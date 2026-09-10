import { api } from "../../services/api";

export const dashboardApi = {
  /**
   * Fetch all tenders (used for selector and active tender count)
   */
  getTenders: async () => {
    const response = await api.get("/tenders");
    return response.data;
  },

  /**
   * Fetch tender-level overview dashboard, summarizing bid counts,
   * compliance distribution, risk distribution, decision counts, and paginated bids list.
   */
  getTenderDashboard: async (tenderId, params = {}) => {
    const response = await api.get(`/dashboard/tenders/${tenderId}`, { params });
    return response.data;
  },

  /**
   * Fetch single bid submission evaluation dashboard payload.
   */
  getBidEvaluationDashboard: async (bidSubmissionId) => {
    const response = await api.get(`/dashboard/bid-submissions/${bidSubmissionId}`);
    return response.data;
  },

  /**
   * Fetch government & statutory verification provider metadata & capabilities.
   */
  getVerificationProviders: async () => {
    const response = await api.get("/verification/providers");
    return response.data;
  },
};
