import { useQuery } from "@tanstack/react-query";
import { auditApi } from "./api";

/**
 * Hook to fetch chronological audit trail for a specific bid submission.
 */
export function useBidSubmissionAuditLogsQuery(bidSubmissionId, { limit = 50, offset = 0 } = {}) {
  return useQuery({
    queryKey: ["audit", "bidSubmission", bidSubmissionId, limit, offset],
    queryFn: () => auditApi.getBidSubmissionAuditLogs(bidSubmissionId, { limit, offset }),
    enabled: !!bidSubmissionId,
    retry: 1,
  });
}

/**
 * Hook to fetch system-wide paginated audit logs with optional filters.
 */
export function useAuditLogsQuery(params = {}) {
  return useQuery({
    queryKey: ["audit", "list", params],
    queryFn: () => auditApi.listAuditLogs(params),
    retry: 1,
  });
}

/**
 * Hook to fetch a single audit log entry by ID.
 */
export function useAuditLogDetailQuery(auditId) {
  return useQuery({
    queryKey: ["audit", "detail", auditId],
    queryFn: () => auditApi.getAuditLogById(auditId),
    enabled: !!auditId,
  });
}
