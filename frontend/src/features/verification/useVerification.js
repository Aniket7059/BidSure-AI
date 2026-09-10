import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { verificationApi } from "./api";

/**
 * Hook to fetch persisted verification results for a bid submission.
 */
export function useSubmissionVerificationsQuery(bidSubmissionId) {
  return useQuery({
    queryKey: ["verification", "submission", bidSubmissionId],
    queryFn: () => verificationApi.getSubmissionVerifications(bidSubmissionId),
    enabled: !!bidSubmissionId,
  });
}

/**
 * Hook to fetch registered verification connector capabilities and source mode provenance metadata.
 */
export function useVerificationProvidersQuery() {
  return useQuery({
    queryKey: ["verification", "providers"],
    queryFn: () => verificationApi.getVerificationProviders(),
  });
}

/**
 * Mutation hook to run a single provider verification check.
 */
export function useVerifyIdentifierMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (requestData) => verificationApi.verifyIdentifier(requestData),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["verification", "submission", variables.bid_submission_id],
      });
      queryClient.invalidateQueries({
        queryKey: ["dashboard", "bid", variables.bid_submission_id],
      });
    },
  });
}

/**
 * Mutation hook to record a manual human-in-the-loop verification by an officer.
 */
export function useManualVerificationMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (manualData) => verificationApi.recordManualVerification(manualData),
    onSuccess: (data) => {
      if (data && data.bid_submission_id) {
        queryClient.invalidateQueries({
          queryKey: ["verification", "submission", data.bid_submission_id],
        });
        queryClient.invalidateQueries({
          queryKey: ["dashboard", "bid", data.bid_submission_id],
        });
      }
    },
  });
}

/**
 * Mutation hook to trigger master end-to-end verification pipeline.
 */
export function useTriggerEndToEndVerificationMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (bidSubmissionId) => verificationApi.triggerEndToEndVerification(bidSubmissionId),
    onSuccess: (data, bidSubmissionId) => {
      queryClient.invalidateQueries({
        queryKey: ["verification", "submission", bidSubmissionId],
      });
      queryClient.invalidateQueries({
        queryKey: ["dashboard", "bid", bidSubmissionId],
      });
      queryClient.invalidateQueries({
        queryKey: ["documents", "submission", bidSubmissionId],
      });
      queryClient.invalidateQueries({
        queryKey: ["compliance", "assessment", bidSubmissionId],
      });
    },
  });
}

/**
 * Utility helper to format source mode into a human-readable, truthful badge label.
 */
export function formatSourceMode(sourceMode) {
  const mode = (sourceMode || "SYNTHETIC").toUpperCase();
  switch (mode) {
    case "OFFICIAL_API":
      return { label: "Official Government API", isLive: true, variant: "official" };
    case "AUTHORIZED_PROVIDER":
      return { label: "Authorized Provider (GSP/ASP)", isLive: true, variant: "authorized" };
    case "MANUAL":
      return { label: "Officer Manual Verification", isLive: false, variant: "manual" };
    case "SYNTHETIC":
    default:
      return { label: "Synthetic / Test Provider", isLive: false, variant: "synthetic" };
  }
}
