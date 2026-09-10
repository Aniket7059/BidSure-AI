import { api } from "../../services/api";

export const documentsApi = {
  /**
   * List all submitted documents for a specific bid submission.
   */
  getSubmissionDocuments: async (bidSubmissionId) => {
    const response = await api.get(`/bid-submissions/${bidSubmissionId}/documents`);
    return response.data;
  },

  /**
   * Upload a new document via multipart/form-data for a bid submission.
   * Accepts FormData containing `file` and `document_type`.
   */
  uploadDocument: async (bidSubmissionId, formData) => {
    const response = await api.post(`/bid-submissions/${bidSubmissionId}/documents`, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },

  /**
   * Execute or re-run Document Intelligence OCR & entity extraction on a document.
   */
  processDocument: async (bidDocumentId) => {
    const response = await api.post(`/bid-submissions/documents/${bidDocumentId}/process`);
    return response.data;
  },

  /**
   * Get the latest Document Intelligence extraction result for a document.
   */
  getDocumentExtractions: async (bidDocumentId) => {
    const response = await api.get(`/bid-submissions/documents/${bidDocumentId}/extraction`);
    return response.data;
  },
};
