import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { documentsApi } from "./api";

/**
 * Hook to fetch all bid documents submitted for a specific bid submission.
 */
export function useBidDocumentsQuery(bidSubmissionId) {
  return useQuery({
    queryKey: ["documents", "submission", bidSubmissionId],
    queryFn: () => documentsApi.getSubmissionDocuments(bidSubmissionId),
    enabled: !!bidSubmissionId,
  });
}

/**
 * Hook to fetch latest Document Intelligence extraction result for a document.
 */
export function useDocumentExtractionQuery(bidDocumentId) {
  return useQuery({
    queryKey: ["documents", "extraction", bidDocumentId],
    queryFn: () => documentsApi.getDocumentExtractions(bidDocumentId),
    enabled: !!bidDocumentId,
    retry: false, // Don't retry indefinitely if extraction hasn't been run yet
  });
}

/**
 * Mutation hook to upload a new document via multipart/form-data.
 */
export function useUploadDocumentMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ bidSubmissionId, formData }) =>
      documentsApi.uploadDocument(bidSubmissionId, formData),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["documents", "submission", variables.bidSubmissionId],
      });
      queryClient.invalidateQueries({
        queryKey: ["dashboard", "bid", variables.bidSubmissionId],
      });
    },
  });
}

/**
 * Mutation hook to execute or re-run Document Intelligence process on a document.
 */
export function useProcessDocumentMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (bidDocumentId) => documentsApi.processDocument(bidDocumentId),
    onSuccess: (data, bidDocumentId) => {
      queryClient.invalidateQueries({
        queryKey: ["documents", "extraction", bidDocumentId],
      });
      if (data && data.bid_submission_id) {
        queryClient.invalidateQueries({
          queryKey: ["documents", "submission", data.bid_submission_id],
        });
        queryClient.invalidateQueries({
          queryKey: ["dashboard", "bid", data.bid_submission_id],
        });
      }
    },
  });
}

/**
 * Helper utility to extract structured fields from backend extraction payload.
 * Supports both standardized `{ document_type, fields: {...} }` and flat `{ gstin: "..." }` schemas.
 */
export function parseExtractedFields(extraction) {
  if (!extraction || !extraction.extracted_data) return {};
  const data = extraction.extracted_data;

  if (data.fields && typeof data.fields === "object") {
    return data.fields;
  }

  // Filter out internal metadata keys if flat payload
  const metadataKeys = new Set([
    "document_type",
    "classification_confidence",
    "extraction_method",
    "total_pages",
    "total_characters",
  ]);

  const fields = {};
  Object.entries(data).forEach(([k, v]) => {
    if (!metadataKeys.has(k)) {
      fields[k] = v;
    }
  });

  return fields;
}
