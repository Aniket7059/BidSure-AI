import hashlib
import os
import re
import uuid
from typing import BinaryIO

from app.core.config import settings


def sanitize_filename(filename: str | None) -> str:
    """
    Sanitizes a client-provided filename for safe display and metadata recording.
    Strips directory separators, null bytes, drive letters, and traversal sequences.
    """
    if not filename or not isinstance(filename, str):
        return "unnamed_document.bin"

    # Remove path components (Windows/Unix separators)
    cleaned = os.path.basename(filename.replace("\\", "/"))

    # Remove non-printable, null, or path characters
    cleaned = re.sub(r"[^\w\s\.\-]", "_", cleaned)
    cleaned = re.sub(r"\.\.+", ".", cleaned).strip()

    if not cleaned or cleaned == ".":
        return "unnamed_document.bin"

    return cleaned[:255]


def get_file_extension(filename: str) -> str:
    """Returns normalized lowercase extension including dot (e.g. '.pdf')."""
    _, ext = os.path.splitext(filename)
    return ext.lower()


class DocumentStorageService:
    """
    Handles secure server-side file storage, path traversal protection,
    streaming chunked writes, SHA-256 hashing, and magic-byte header validation.
    """

    def __init__(self, storage_root: str | None = None) -> None:
        self.storage_root = os.path.abspath(storage_root or settings.DOCUMENT_STORAGE_ROOT)
        os.makedirs(self.storage_root, exist_ok=True)

    def validate_file_metadata(self, original_filename: str, content_type: str | None) -> str:
        """
        Validates file extension and content type against configured allowed lists.
        Returns the normalized file extension.
        """
        ext = get_file_extension(original_filename)
        if ext not in settings.ALLOWED_DOCUMENT_EXTENSIONS:
            raise ValueError(
                f"Unsupported file extension: '{ext}'. Allowed extensions: {sorted(list(settings.ALLOWED_DOCUMENT_EXTENSIONS))}"
            )

        if content_type:
            ct_clean = content_type.split(";")[0].strip().lower()
            if ct_clean not in settings.ALLOWED_DOCUMENT_MIME_TYPES:
                raise ValueError(
                    f"Unsupported content type: '{content_type}'. Allowed types: {sorted(list(settings.ALLOWED_DOCUMENT_MIME_TYPES))}"
                )

        return ext

    def validate_magic_bytes(self, header: bytes, ext: str) -> None:
        """
        Inspects raw file header magic bytes to verify file signature match.
        """
        if not header:
            raise ValueError("File content is empty.")

        if ext == ".pdf":
            if not header.startswith(b"%PDF"):
                raise ValueError("File content header does not match valid PDF format (%PDF signature missing).")
        elif ext == ".png":
            if not header.startswith(b"\x89PNG"):
                raise ValueError("File content header does not match valid PNG image format.")
        elif ext in (".jpg", ".jpeg"):
            if not header.startswith(b"\xff\xd8\xff"):
                raise ValueError("File content header does not match valid JPEG image format.")

    def save_upload(
        self,
        file_obj: BinaryIO,
        bid_submission_id: int,
        original_filename: str,
        content_type: str | None = None,
    ) -> tuple[str, str, int, str, str, str]:
        """
        Streams uploaded binary file to secure server storage.

        Returns:
            relative_storage_path: Trusted server-side path (e.g. 'storage/documents/1/uuid.pdf')
            server_filename: Safe server-generated filename
            file_size: Exact byte count written
            file_hash: SHA-256 hex digest of file contents
            display_name: Sanitized original filename
            detected_mime_type: Validated MIME type
        """
        ext = self.validate_file_metadata(original_filename, content_type)
        display_name = sanitize_filename(original_filename)

        # Build secure submission storage directory
        submission_dir = os.path.abspath(os.path.join(self.storage_root, str(bid_submission_id)))
        if not submission_dir.startswith(self.storage_root):
            raise ValueError("Path traversal attempt detected in submission path.")
        os.makedirs(submission_dir, exist_ok=True)

        # Generate safe server-side storage filename
        server_filename = f"{uuid.uuid4().hex}{ext}"
        target_path = os.path.abspath(os.path.join(submission_dir, server_filename))

        # Path traversal guard
        if not target_path.startswith(submission_dir):
            raise ValueError("Path traversal attempt detected in target file path.")

        max_bytes = settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024
        sha256 = hashlib.sha256()
        total_bytes = 0
        header_bytes = b""

        try:
            with open(target_path, "wb") as out_file:
                while True:
                    chunk = file_obj.read(64 * 1024)
                    if not chunk:
                        break

                    total_bytes += len(chunk)
                    if total_bytes > max_bytes:
                        raise ValueError(
                            f"File size ({total_bytes} bytes) exceeds maximum allowed limit of {settings.MAX_DOCUMENT_SIZE_MB}MB."
                        )

                    if len(header_bytes) < 16:
                        header_bytes += chunk[: 16 - len(header_bytes)]

                    sha256.update(chunk)
                    out_file.write(chunk)

            if total_bytes == 0:
                raise ValueError("Empty file (0 bytes) cannot be uploaded.")

            # Validate magic bytes against header
            self.validate_magic_bytes(header_bytes, ext)

        except Exception as exc:
            # Clean up partial/orphaned file on error
            if os.path.exists(target_path):
                try:
                    os.remove(target_path)
                except OSError:
                    pass
            raise exc

        file_hash = sha256.hexdigest()

        # Compute relative storage path using forward slashes for cross-platform safety
        try:
            rel_path = os.path.normpath(os.path.relpath(target_path, start=os.getcwd())).replace("\\", "/")
        except ValueError:
            rel_path = os.path.normpath(target_path).replace("\\", "/")

        mime_map = {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
        }
        detected_mime = mime_map.get(ext, content_type or "application/octet-stream")

        return rel_path, server_filename, total_bytes, file_hash, display_name, detected_mime

    def delete_file(self, storage_path: str) -> bool:
        """Deletes stored document file from disk if present."""
        if not storage_path:
            return False

        abs_path = self.get_absolute_path(storage_path)
        if abs_path and os.path.exists(abs_path):
            try:
                os.remove(abs_path)
                return True
            except OSError:
                return False
        return False

    def exists(self, storage_path: str) -> bool:
        """Returns True if the file exists at storage_path."""
        abs_path = self.get_absolute_path(storage_path)
        return bool(abs_path and os.path.exists(abs_path))

    def get_absolute_path(self, storage_path: str) -> str | None:
        """
        Resolves a relative storage_path to an absolute OS path,
        ensuring it resides within the configured storage root or working directory.
        """
        if not storage_path:
            return None

        # Check if already absolute or relative
        if os.path.isabs(storage_path):
            abs_p = os.path.abspath(storage_path)
        else:
            abs_p = os.path.abspath(os.path.join(os.getcwd(), storage_path))

        abs_root = os.path.abspath(self.storage_root)
        abs_cwd = os.path.abspath(os.getcwd())

        # Security check: must not escape storage_root or cwd
        if not abs_p.startswith(abs_root) and not abs_p.startswith(abs_cwd):
            return None

        return abs_p


document_storage_service = DocumentStorageService()
