import { api } from "../../services/api";

export const auditApi = {
  /**
   * Retrieve complete chronological audit trail for a specific bid submission.
   */
  getBidSubmissionAuditLogs: async (bidSubmissionId, { limit = 50, offset = 0 } = {}) => {
    try {
      const response = await api.get(`/bid-submissions/${bidSubmissionId}/audit-logs`, {
        params: { limit, offset },
      });
      return response.data;
    } catch (err) {
      if (err.response && err.response.status === 404) {
        return { items: [], total: 0, limit, offset };
      }
      throw err;
    }
  },

  /**
   * Retrieve paginated audit logs with optional filtering by entity, action, user, or date range.
   */
  listAuditLogs: async ({
    entityType = null,
    entityId = null,
    bidSubmissionId = null,
    userId = null,
    action = null,
    startDate = null,
    endDate = null,
    limit = 50,
    offset = 0,
  } = {}) => {
    try {
      const params = { limit, offset };
      if (entityType) params.entity_type = entityType;
      if (entityId) params.entity_id = entityId;
      if (bidSubmissionId) params.bid_submission_id = bidSubmissionId;
      if (userId) params.user_id = userId;
      if (action) params.action = action;
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const response = await api.get("/audit-logs", { params });
      return response.data;
    } catch (err) {
      if (err.response && err.response.status === 404) {
        return { items: [], total: 0, limit, offset };
      }
      throw err;
    }
  },

  /**
   * Retrieve a single audit log entry by ID.
   */
  getAuditLogById: async (auditId) => {
    const response = await api.get(`/audit-logs/${auditId}`);
    return response.data;
  },
};
