import { api } from "../../services/api";

export const verificationApi = {
  /**
   * Fetch persisted provider verification results for a single bid submission.
   */
  getSubmissionVerifications: async (bidSubmissionId) => {
    const response = await api.get(`/verification/submissions/${bidSubmissionId}/results`);
    return response.data;
  },

  /**
   * Run a single registered provider verification check.
   */
  verifyIdentifier: async (requestData) => {
    const response = await api.post(`/verification/verify`, requestData);
    return response.data;
  },

  /**
   * Fetch provider capability & provenance metadata for all registered connectors.
   */
  getVerificationProviders: async () => {
    const response = await api.get(`/verification/providers`);
    return response.data;
  },

  /**
   * Record a human-in-the-loop manual verification result by a Procurement Officer.
   */
  recordManualVerification: async (manualData) => {
    const response = await api.post(`/verification/manual`, manualData);
    return response.data;
  },

  /**
   * Trigger master end-to-end verification pipeline for a bid submission.
   */
  triggerEndToEndVerification: async (bidSubmissionId) => {
    const response = await api.post(`/bid-submissions/${bidSubmissionId}/verify`);
    return response.data;
  },
};
