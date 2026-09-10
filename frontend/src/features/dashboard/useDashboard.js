import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "./api";

/**
 * Hook to fetch all tenders from backend.
 */
export function useTendersQuery() {
  return useQuery({
    queryKey: ["tenders"],
    queryFn: () => dashboardApi.getTenders(),
  });
}

/**
 * Hook to fetch tender dashboard aggregation for a specific tender.
 */
export function useTenderDashboardQuery(tenderId, params = {}) {
  return useQuery({
    queryKey: ["dashboard", "tender", tenderId, params],
    queryFn: () => dashboardApi.getTenderDashboard(tenderId, params),
    enabled: !!tenderId,
  });
}

/**
 * Hook to fetch single bid evaluation dashboard payload.
 */
export function useBidEvaluationDashboardQuery(bidSubmissionId) {
  return useQuery({
    queryKey: ["dashboard", "bid", bidSubmissionId],
    queryFn: () => dashboardApi.getBidEvaluationDashboard(bidSubmissionId),
    enabled: !!bidSubmissionId,
  });
}

/**
 * Hook to fetch verification provider metadata & operational status.
 */
export function useVerificationProvidersQuery() {
  return useQuery({
    queryKey: ["verification", "providers"],
    queryFn: () => dashboardApi.getVerificationProviders(),
  });
}
