import { api } from "../../services/api";

export const complianceApi = {
  /**
   * Run compliance assessment engine for a submission. Returns overall score, risk level, and summary.
   */
  getSubmissionAssessment: async (bidSubmissionId) => {
    try {
      const response = await api.post(`/compliance/assess/${bidSubmissionId}`);
      return response.data;
    } catch (err) {
      if (err.response && err.response.status === 404) {
        return null;
      }
      throw err;
    }
  },

  /**
   * List all requirement-level compliance check records for a submission.
   */
  getSubmissionChecks: async (bidSubmissionId) => {
    try {
      const response = await api.get(`/compliance/checks/${bidSubmissionId}`);
      return Array.isArray(response.data) ? response.data : [];
    } catch (err) {
      if (err.response && err.response.status === 404) {
        return [];
      }
      return [];
    }
  },

  /**
   * Run multi-document cross-verification audit against portal records.
   */
  crossVerifySubmission: async (bidSubmissionId) => {
    try {
      const response = await api.post(`/compliance/cross-verify/${bidSubmissionId}`);
      return response.data;
    } catch (err) {
      if (err.response && err.response.status === 404) {
        return null;
      }
      throw err;
    }
  },

  /**
   * Generate advisory AI qualification recommendation.
   */
  generateAiRecommendation: async (bidSubmissionId) => {
    const response = await api.post(`/compliance/recommend/${bidSubmissionId}`);
    return response.data;
  },

  /**
   * Get stored AI recommendation detail.
   */
  getRecommendationDetail: async (bidSubmissionId) => {
    try {
      const response = await api.get(`/compliance/recommendation/${bidSubmissionId}`);
      return response.data;
    } catch (err) {
      if (err.response && (err.response.status === 404 || err.response.status === 400)) {
        return null;
      }
      return null;
    }
  },

  /**
   * List all persisted discrepancies for a submission.
   */
  getDiscrepancies: async (bidSubmissionId) => {
    try {
      const response = await api.get(`/bid-submissions/${bidSubmissionId}/discrepancies`);
      return Array.isArray(response.data) ? response.data : [];
    } catch (err) {
      if (err.response && err.response.status === 404) {
        return [];
      }
      return [];
    }
  },

  /**
   * List OPEN discrepancies for a submission.
   */
  getOpenDiscrepancies: async (bidSubmissionId) => {
    try {
      const response = await api.get(`/bid-submissions/${bidSubmissionId}/discrepancies/open`);
      return Array.isArray(response.data) ? response.data : [];
    } catch (err) {
      if (err.response && err.response.status === 404) {
        return [];
      }
      return [];
    }
  },

  /**
   * Update discrepancy status (RESOLVED / WAIVED) with mandatory resolution note.
   */
  updateDiscrepancyStatus: async (bidSubmissionId, discrepancyId, status, resolutionNote) => {
    const response = await api.patch(`/bid-submissions/${bidSubmissionId}/discrepancies/${discrepancyId}`, {
      status,
      resolution_note: resolutionNote,
    });
    return response.data;
  },

  /**
   * Record official Procurement Officer qualification decision.
   * `decisionData`: { decision: "QUALIFIED" | "DISQUALIFIED", reason: "Min 10 chars" }
   */
  recordProcurementDecision: async (bidSubmissionId, decisionData) => {
    const response = await api.post(`/bid-submissions/${bidSubmissionId}/decision`, decisionData);
    return response.data;
  },

  /**
   * Get recorded Procurement Officer decision if exists.
   */
  getProcurementDecision: async (bidSubmissionId) => {
    try {
      const response = await api.get(`/bid-submissions/${bidSubmissionId}/decision`);
      return response.data;
    } catch (err) {
      if (err.response && err.response.status === 404) {
        return null;
      }
      return null;
    }
  },
};

