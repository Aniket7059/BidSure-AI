import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { complianceApi } from "./api";

/**
 * Hook to fetch compliance summary assessment for a submission.
 */
export function useComplianceAssessmentQuery(bidSubmissionId) {
  return useQuery({
    queryKey: ["compliance", "assessment", bidSubmissionId],
    queryFn: () => complianceApi.getSubmissionAssessment(bidSubmissionId),
    enabled: !!bidSubmissionId,
    retry: 1,
  });
}

/**
 * Hook to fetch rule-level compliance checks for a submission.
 */
export function useComplianceChecksQuery(bidSubmissionId) {
  return useQuery({
    queryKey: ["compliance", "checks", bidSubmissionId],
    queryFn: () => complianceApi.getSubmissionChecks(bidSubmissionId),
    enabled: !!bidSubmissionId,
  });
}

/**
 * Hook to fetch multi-document cross-verification results for a submission.
 */
export function useCrossVerificationQuery(bidSubmissionId) {
  return useQuery({
    queryKey: ["compliance", "crossVerify", bidSubmissionId],
    queryFn: () => complianceApi.crossVerifySubmission(bidSubmissionId),
    enabled: !!bidSubmissionId,
  });
}

/**
 * Hook to fetch stored AI recommendation detail for a submission.
 */
export function useRecommendationDetailQuery(bidSubmissionId) {
  return useQuery({
    queryKey: ["compliance", "recommendation", bidSubmissionId],
    queryFn: () => complianceApi.getRecommendationDetail(bidSubmissionId),
    enabled: !!bidSubmissionId,
    retry: false,
  });
}

/**
 * Hook to fetch persisted discrepancies for a submission.
 */
export function useDiscrepanciesQuery(bidSubmissionId) {
  return useQuery({
    queryKey: ["compliance", "discrepancies", bidSubmissionId],
    queryFn: () => complianceApi.getDiscrepancies(bidSubmissionId),
    enabled: !!bidSubmissionId,
  });
}

/**
 * Hook to fetch recorded procurement officer decision if available.
 */
export function useProcurementDecisionQuery(bidSubmissionId) {
  return useQuery({
    queryKey: ["compliance", "decision", bidSubmissionId],
    queryFn: () => complianceApi.getProcurementDecision(bidSubmissionId),
    enabled: !!bidSubmissionId,
    retry: false, // Don't retry indefinitely if no decision recorded yet
  });
}

/**
 * Mutation hook to re-run compliance assessment engine.
 */
export function useAssessSubmissionMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (bidSubmissionId) => complianceApi.getSubmissionAssessment(bidSubmissionId),
    onSuccess: (data, bidSubmissionId) => {
      queryClient.invalidateQueries({ queryKey: ["compliance", "assessment", bidSubmissionId] });
      queryClient.invalidateQueries({ queryKey: ["compliance", "checks", bidSubmissionId] });
      queryClient.invalidateQueries({ queryKey: ["compliance", "recommendation", bidSubmissionId] });
      queryClient.invalidateQueries({ queryKey: ["compliance", "discrepancies", bidSubmissionId] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "bid", bidSubmissionId] });
    },
  });
}

/**
 * Mutation hook to generate / refresh AI recommendation.
 */
export function useGenerateRecommendationMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (bidSubmissionId) => complianceApi.generateAiRecommendation(bidSubmissionId),
    onSuccess: (data, bidSubmissionId) => {
      queryClient.invalidateQueries({ queryKey: ["compliance", "recommendation", bidSubmissionId] });
      queryClient.invalidateQueries({ queryKey: ["compliance", "assessment", bidSubmissionId] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "bid", bidSubmissionId] });
    },
  });
}

/**
 * Mutation hook to update discrepancy status (RESOLVED / WAIVED) with officer justification.
 */
export function useUpdateDiscrepancyMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ bidSubmissionId, discrepancyId, status, resolutionNote }) =>
      complianceApi.updateDiscrepancyStatus(bidSubmissionId, discrepancyId, status, resolutionNote),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["compliance", "discrepancies", variables.bidSubmissionId],
      });
      queryClient.invalidateQueries({
        queryKey: ["compliance", "assessment", variables.bidSubmissionId],
      });
      queryClient.invalidateQueries({
        queryKey: ["dashboard", "bid", variables.bidSubmissionId],
      });
    },
  });
}

/**
 * Mutation hook to record official Procurement Officer decision.
 */
export function useRecordProcurementDecisionMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ bidSubmissionId, decisionData }) =>
      complianceApi.recordProcurementDecision(bidSubmissionId, decisionData),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["compliance", "decision", variables.bidSubmissionId],
      });
      queryClient.invalidateQueries({
        queryKey: ["dashboard", "bid", variables.bidSubmissionId],
      });
      queryClient.invalidateQueries({
        queryKey: ["compliance", "assessment", variables.bidSubmissionId],
      });
    },
  });
}
