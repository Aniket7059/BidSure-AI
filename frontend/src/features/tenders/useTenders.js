import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { tendersApi } from "./api";
import { dashboardApi } from "../dashboard/api";

/**
 * React Query hook to fetch all tenders.
 */
export function useTendersQuery() {
  return useQuery({
    queryKey: ["tenders"],
    queryFn: () => tendersApi.getTenders(),
  });
}

/**
 * React Query hook to fetch a single tender by ID.
 */
export function useTenderQuery(tenderId) {
  return useQuery({
    queryKey: ["tender", tenderId],
    queryFn: () => tendersApi.getTenderById(tenderId),
    enabled: !!tenderId,
  });
}

/**
 * React Query hook to fetch requirements for a tender.
 */
export function useTenderRequirementsQuery(tenderId) {
  return useQuery({
    queryKey: ["tenderRequirements", tenderId],
    queryFn: () => tendersApi.getTenderRequirements(tenderId),
    enabled: !!tenderId,
  });
}

/**
 * React Query hook to fetch bid submissions for a tender.
 */
export function useTenderBidsQuery(tenderId) {
  return useQuery({
    queryKey: ["tenderBids", tenderId],
    queryFn: () => tendersApi.getTenderBids(tenderId),
    enabled: !!tenderId,
  });
}

/**
 * React Query hook to fetch tender dashboard aggregation (overview, metrics, bids).
 */
export function useTenderOverviewQuery(tenderId, params = {}) {
  return useQuery({
    queryKey: ["tenderOverview", tenderId, params],
    queryFn: () => dashboardApi.getTenderDashboard(tenderId, params),
    enabled: !!tenderId,
  });
}

/**
 * Mutation hook to create a new tender.
 */
export function useCreateTenderMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (tenderData) => tendersApi.createTender(tenderData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tenders"] });
    },
  });
}

/**
 * Mutation hook to create a new tender requirement.
 */
export function useCreateRequirementMutation(tenderId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (reqData) => tendersApi.createTenderRequirement(tenderId, reqData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tenderRequirements", tenderId] });
      queryClient.invalidateQueries({ queryKey: ["tender", tenderId] });
    },
  });
}

/**
 * Mutation hook to run RAG requirement extraction from tender text.
 */
export function useExtractRequirementsMutation(tenderId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (extractRequest) => tendersApi.extractTenderRequirements(tenderId, extractRequest),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tenderRequirements", tenderId] });
    },
  });
}
