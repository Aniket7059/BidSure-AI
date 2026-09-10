/**
 * Formats a file size in bytes to a human-readable string (KB, MB, GB).
 *
 * @param {number} bytes
 * @param {number} [decimals=2]
 * @returns {string}
 */
export function formatFileSize(bytes, decimals = 2) {
  if (bytes === 0) return "0 Bytes";
  if (!bytes || isNaN(bytes)) return "N/A";

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ["Bytes", "KB", "MB", "GB", "TB"];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
}
