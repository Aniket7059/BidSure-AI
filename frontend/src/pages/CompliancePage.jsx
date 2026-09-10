import React, { useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  BadgeCheck,
  Play,
  ArrowLeft,
  Cpu,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  MessageSquare,
  ThumbsUp,
  ThumbsDown,
  AlertOctagon,
  ShieldAlert,
  Check,
  XCircle,
  FileWarning,
  Filter,
  ExternalLink,
  Activity,
  FileText,
  History,
  UserCheck,
  Sparkles,
  AlertCircle,
  RefreshCw,
  Info,
  Layers,
  Lock
} from "lucide-react";
import { PageContainer } from "../components/layout/PageContainer";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Textarea } from "../components/ui/textarea";
import { Label } from "../components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "../components/ui/dialog";
import { ScoreGauge } from "../components/shared/ScoreGauge";
import { RiskBadge } from "../components/shared/RiskBadge";
import { LoadingState } from "../components/shared/LoadingState";
import { ErrorState } from "../components/shared/ErrorState";
import { useBidEvaluationDashboardQuery } from "../features/dashboard/useDashboard";
import {
  useComplianceAssessmentQuery,
  useComplianceChecksQuery,
  useCrossVerificationQuery,
  useRecommendationDetailQuery,
  useDiscrepanciesQuery,
  useProcurementDecisionQuery,
  useAssessSubmissionMutation,
  useGenerateRecommendationMutation,
  useUpdateDiscrepancyMutation,
  useRecordProcurementDecisionMutation,
} from "../features/compliance/useCompliance";

export function CompliancePage() {
  const { bidSubmissionId } = useParams();

  // Discrepancy filter state
  const [discrepancyFilter, setDiscrepancyFilter] = useState("ALL");

  // Inline discrepancy resolution state
  const [resolvingId, setResolvingId] = useState(null);
  const [resolutionAction, setResolutionAction] = useState("RESOLVED"); // RESOLVED or WAIVED
  const [resolutionNoteInput, setResolutionNoteInput] = useState("");
  const [resolutionError, setResolutionError] = useState(null);

  // Officer qualification decision form state
  const [selectedDecision, setSelectedDecision] = useState("QUALIFIED"); // QUALIFIED or DISQUALIFIED
  const [officerReason, setOfficerReason] = useState("");
  const [openConfirmModal, setOpenConfirmModal] = useState(false);
  const [decisionError, setDecisionError] = useState(null);

  // Fetch bid dashboard payload for context
  const {
    data: dashboardData,
    isLoading: isDashboardLoading,
  } = useBidEvaluationDashboardQuery(bidSubmissionId);

  // Compliance hooks
  const {
    data: assessment,
    isLoading: isAssessmentLoading,
    isError: isAssessmentError,
    error: assessmentError,
    refetch: refetchAssessment,
  } = useComplianceAssessmentQuery(bidSubmissionId);

  const {
    data: checks = [],
    isLoading: isChecksLoading,
  } = useComplianceChecksQuery(bidSubmissionId);

  const {
    data: crossVerify,
    isLoading: isCrossVerifyLoading,
  } = useCrossVerificationQuery(bidSubmissionId);

  const {
    data: recommendationDetail,
    isLoading: isRecLoading,
  } = useRecommendationDetailQuery(bidSubmissionId);

  const {
    data: discrepancies = [],
    isLoading: isDiscrepanciesLoading,
  } = useDiscrepanciesQuery(bidSubmissionId);

  const {
    data: recordedDecision,
    isLoading: isDecisionLoading,
    refetch: refetchDecision,
  } = useProcurementDecisionQuery(bidSubmissionId);

  // Mutations
  const assessMutation = useAssessSubmissionMutation();
  const generateRecMutation = useGenerateRecommendationMutation();
  const updateDiscrepancyMutation = useUpdateDiscrepancyMutation();
  const recordDecisionMutation = useRecordProcurementDecisionMutation();

  // Handlers
  const handleRunComplianceEngine = async () => {
    try {
      await assessMutation.mutateAsync(Number(bidSubmissionId));
    } catch (err) {
      console.error("Compliance engine assessment failed:", err);
    }
  };

  const handleGenerateRecommendation = async () => {
    try {
      await generateRecMutation.mutateAsync(Number(bidSubmissionId));
    } catch (err) {
      console.error("Recommendation generation failed:", err);
    }
  };

  const handleResolveDiscrepancy = async (discrepancyId) => {
    setResolutionError(null);
    if (!resolutionNoteInput.trim()) {
      setResolutionError("Please provide a mandatory officer justification note.");
      return;
    }

    try {
      await updateDiscrepancyMutation.mutateAsync({
        bidSubmissionId: Number(bidSubmissionId),
        discrepancyId,
        status: resolutionAction,
        resolutionNote: resolutionNoteInput.trim(),
      });
      setResolvingId(null);
      setResolutionNoteInput("");
    } catch (err) {
      const msg = err?.response?.data?.detail || "Failed to update discrepancy status.";
      setResolutionError(msg);
    }
  };

  const handleOpenConfirmDialog = () => {
    setDecisionError(null);
    const cleanedReason = officerReason.trim();

    if (!cleanedReason) {
      setDecisionError("Detailed officer explanation is required.");
      return;
    }
    if (cleanedReason.length < 10) {
      setDecisionError("Reason must be at least 10 characters long to provide adequate justification.");
      return;
    }

    setOpenConfirmModal(true);
  };

  const handleConfirmDecisionSubmit = async () => {
    setDecisionError(null);

    try {
      await recordDecisionMutation.mutateAsync({
        bidSubmissionId: Number(bidSubmissionId),
        decisionData: {
          decision: selectedDecision,
          reason: officerReason.trim(),
        },
      });
      setOpenConfirmModal(false);
      setOfficerReason("");
      refetchDecision();
    } catch (err) {
      setOpenConfirmModal(false);
      const msg = err?.response?.data?.detail || "Failed to record procurement decision.";
      setDecisionError(msg);
    }
  };

  if (isAssessmentLoading || isDashboardLoading || isChecksLoading) {
    return (
      <PageContainer
        title={`Compliance & AI Recommendation (#${bidSubmissionId})`}
        description="Loading rule evaluation matrix, AI advisory recommendation, and officer decision controls..."
      >
        <LoadingState message="Fetching compliance assessment, AI recommendation, and decision records..." />
      </PageContainer>
    );
  }

  if (isAssessmentError && !dashboardData) {
    return (
      <PageContainer
        title={`Compliance Assessment (#${bidSubmissionId})`}
        description="Tender Compliance & Risk Matrix"
        actions={
          <Link to={`/bids/${bidSubmissionId}`}>
            <Button size="sm" variant="outline">
              <ArrowLeft className="mr-1.5 h-3.5 w-3.5" /> Back to Bid Evaluation
            </Button>
          </Link>
        }
      >
        <ErrorState
          title="Compliance Evaluation Unavailable"
          message={assessmentError?.response?.data?.detail || "Failed connecting to compliance engine."}
          onRetry={refetchAssessment}
        />
      </PageContainer>
    );
  }

  const bidderName = dashboardData?.bidder?.company_name || "Bidder";
  const tenderRef = dashboardData?.tender?.reference_number || "Tender";
  const documents = dashboardData?.documents || [];
  const verifications = dashboardData?.verification || [];

  // Summary metrics from backend
  const complianceStatus = assessment?.status || dashboardData?.summary?.overall_status || "PENDING";
  const scoreValue = assessment?.score ?? assessment?.overall_compliance_score ?? dashboardData?.summary?.score ?? null;
  const riskLevel = assessment?.risk_level ?? dashboardData?.summary?.risk_level ?? null;

  // AI Recommendation object (prefer detailed recommendation response, fallback to assessment summary)
  const recObj = recommendationDetail || assessment?.assessment_metadata?.recommendation_detail || null;
  const recStatus = recObj?.recommendation || assessment?.recommendation || dashboardData?.summary?.recommendation || null;
  const recSummary = recObj?.summary || assessment?.summary || assessment?.summary_recommendation || dashboardData?.recommendation?.summary || null;
  const recConfidence = recObj?.confidence || "HIGH";

  const requirementsList = dashboardData?.requirements || [];

  // Safe array wrappers
  const safeDiscrepancies = Array.isArray(discrepancies) ? discrepancies : [];
  const safeChecks = Array.isArray(checks) ? checks : [];
  const safeRequirementsList = Array.isArray(requirementsList) ? requirementsList : [];

  // Discrepancies filtering
  const filteredDiscrepancies = safeDiscrepancies.filter((d) => {
    if (discrepancyFilter === "ALL") return true;
    return d?.status === discrepancyFilter;
  });
  const openDiscrepanciesCount = safeDiscrepancies.filter((d) => d?.status === "OPEN").length;

  const getSeverityBadge = (severity) => {
    const s = (severity || "").toUpperCase();
    switch (s) {
      case "CRITICAL":
        return <Badge className="bg-red-600 text-white font-bold text-[10px]">CRITICAL</Badge>;
      case "HIGH":
        return <Badge className="bg-orange-500 text-white font-bold text-[10px]">HIGH</Badge>;
      case "MEDIUM":
        return <Badge className="bg-amber-500 text-white font-bold text-[10px]">MEDIUM</Badge>;
      default:
        return <Badge className="bg-blue-500 text-white font-bold text-[10px]">LOW</Badge>;
    }
  };

  const getRecommendationBadge = (rec) => {
    const r = (rec || "").toUpperCase();
    if (r === "PROCEED") {
      return <Badge className="bg-emerald-600 text-white font-bold text-xs">PROCEED (RECOMMENDED)</Badge>;
    }
    if (r === "REVIEW_REQUIRED") {
      return <Badge className="bg-amber-500 text-white font-bold text-xs">REVIEW REQUIRED</Badge>;
    }
    if (r === "HIGH_RISK_REVIEW") {
      return <Badge className="bg-orange-600 text-white font-bold text-xs">HIGH RISK REVIEW</Badge>;
    }
    if (r === "DO_NOT_RECOMMEND") {
      return <Badge className="bg-red-600 text-white font-bold text-xs">DO NOT RECOMMEND</Badge>;
    }
    return <Badge variant="outline" className="bg-slate-100 text-slate-600 border-slate-300 text-xs">Not generated yet</Badge>;
  };

  const getDecisionBadge = (decisionStr) => {
    const d = (decisionStr || "").toUpperCase();
    if (d === "QUALIFIED") {
      return <Badge className="bg-emerald-600 text-white font-bold text-xs">QUALIFIED</Badge>;
    }
    if (d === "DISQUALIFIED") {
      return <Badge className="bg-red-600 text-white font-bold text-xs">DISQUALIFIED</Badge>;
    }
    return <Badge variant="outline" className="bg-slate-100 text-slate-700 border-slate-300 text-xs">Awaiting Procurement Officer decision</Badge>;
  };

  const activeDecision = recordedDecision || (dashboardData?.decision?.decision ? dashboardData.decision : null);

  return (
    <PageContainer
      title={`Compliance & AI Recommendation Workspace (#${bidSubmissionId})`}
      description={`Authoritative compliance matrix, AI advisory recommendations, and officer decision workflow for ${bidderName}`}
      badge={
        <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200 text-xs font-semibold">
          Compliance State: {complianceStatus}
        </Badge>
      }
      actions={
        <div className="flex items-center gap-2 flex-wrap">
          <Link to={`/bids/${bidSubmissionId}`}>
            <Button size="sm" variant="outline" className="text-xs">
              <ArrowLeft className="mr-1.5 h-3.5 w-3.5" /> Back to Bid Evaluation
            </Button>
          </Link>

          <Button
            size="sm"
            onClick={handleRunComplianceEngine}
            disabled={assessMutation.isPending}
            className="bg-blue-600 hover:bg-blue-700 text-white text-xs shadow-sm"
          >
            <Play className={`mr-1.5 h-3.5 w-3.5 ${assessMutation.isPending ? "animate-spin" : ""}`} />
            {assessMutation.isPending ? "Evaluating Engine..." : "Run Compliance Engine"}
          </Button>
        </div>
      }
    >
      {/* Workspace Sub-Navigation */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-2 overflow-x-auto">
        <Link to={`/bids/${bidSubmissionId}`}>
          <Button size="sm" variant="outline" className="text-xs text-slate-700 hover:bg-slate-100">
            <Activity className="mr-1.5 h-3.5 w-3.5" /> Workspace Overview
          </Button>
        </Link>
        <Link to={`/bids/${bidSubmissionId}/documents`}>
          <Button size="sm" variant="outline" className="text-xs text-slate-700 hover:bg-slate-100">
            <FileText className="mr-1.5 h-3.5 w-3.5 text-blue-600" /> Documents ({documents.length})
          </Button>
        </Link>
        <Link to={`/bids/${bidSubmissionId}/verification`}>
          <Button size="sm" variant="outline" className="text-xs text-slate-700 hover:bg-slate-100">
            <ShieldCheck className="mr-1.5 h-3.5 w-3.5 text-emerald-600" /> Statutory Verifications ({verifications.length})
          </Button>
        </Link>
        <Button size="sm" variant="default" className="bg-slate-900 text-white text-xs font-semibold">
          <BadgeCheck className="mr-1.5 h-3.5 w-3.5 text-purple-400" /> Compliance & Decision
        </Button>
        <Link to={`/bids/${bidSubmissionId}/audit`}>
          <Button size="sm" variant="outline" className="text-xs text-slate-700 hover:bg-slate-100">
            <History className="mr-1.5 h-3.5 w-3.5 text-slate-600" /> Audit Trail
          </Button>
        </Link>
      </div>

      {/* 1. Authoritative Summary Banner: Score Gauge, Risk Badge, and AI Advisory Recommendation */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Authoritative Score & Risk Badge */}
        <Card className="shadow-subtle border-slate-200 bg-white flex flex-col justify-between">
          <CardHeader className="pb-2 border-b border-slate-100 text-center">
            <CardTitle className="text-sm font-bold text-slate-900">Authoritative Compliance Score</CardTitle>
          </CardHeader>
          <CardContent className="p-6 flex flex-col items-center justify-center space-y-4">
            {scoreValue !== null ? (
              <ScoreGauge score={scoreValue} size={130} />
            ) : (
              <div className="p-6 text-center space-y-2">
                <AlertCircle className="h-8 w-8 text-amber-500 mx-auto" />
                <span className="text-xs font-bold text-slate-700 block">Compliance assessment not available yet</span>
                <span className="text-[11px] text-slate-500 block">Click "Run Compliance Engine" to calculate score.</span>
              </div>
            )}

            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-slate-500">Bidder Risk Classification:</span>
              {riskLevel ? (
                <RiskBadge riskLevel={riskLevel} />
              ) : (
                <Badge variant="outline" className="bg-slate-100 text-slate-600 border-slate-300 text-xs">
                  Pending / Unavailable
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Right Columns: AI Advisory Recommendation Panel */}
        <Card className="lg:col-span-2 shadow-subtle border-slate-200 bg-slate-900 text-white flex flex-col justify-between">
          <CardHeader className="pb-2 border-b border-slate-800 flex flex-row items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-purple-400" />
              <div>
                <CardTitle className="text-sm font-bold text-white">AI Recommendation Engine</CardTitle>
                <span className="text-[10px] text-purple-300 font-mono block">ADVISORY ONLY — Does Not Qualify/Disqualify</span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {getRecommendationBadge(recStatus)}
              <Button
                size="sm"
                variant="outline"
                onClick={handleGenerateRecommendation}
                disabled={generateRecMutation.isPending}
                className="text-[11px] bg-slate-800 border-slate-700 text-slate-200 hover:bg-slate-700 h-7"
              >
                <RefreshCw className={`mr-1 h-3 w-3 ${generateRecMutation.isPending ? "animate-spin text-purple-400" : ""}`} />
                {generateRecMutation.isPending ? "Generating..." : "Refresh Recommendation"}
              </Button>
            </div>
          </CardHeader>

          <CardContent className="p-5 space-y-4 text-xs">
            {recSummary ? (
              <>
                <p className="text-slate-200 leading-relaxed font-sans bg-slate-800/80 p-3.5 rounded-lg border border-slate-700 italic">
                  "{recSummary}"
                </p>

                {/* Structured Advisory Lists */}
                {recObj?.critical_issues?.length > 0 && (
                  <div className="space-y-1">
                    <span className="font-bold text-red-400 block text-[11px]">Critical Risk Factors:</span>
                    <ul className="list-disc list-inside text-slate-300 space-y-0.5 text-[11px]">
                      {recObj.critical_issues.map((issue, idx) => (
                        <li key={idx}>{typeof issue === "object" ? issue.reason || issue.description || JSON.stringify(issue) : issue}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {recObj?.review_items?.length > 0 && (
                  <div className="space-y-1">
                    <span className="font-bold text-amber-400 block text-[11px]">Officer Priority Review Items:</span>
                    <ul className="list-disc list-inside text-slate-300 space-y-0.5 text-[11px]">
                      {recObj.review_items.map((item, idx) => (
                        <li key={idx}>
                          Priority #{item.priority || idx + 1}: {item.reason} — <strong className="text-purple-300">Action: {item.suggested_officer_action}</strong>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            ) : (
              <div className="p-6 text-center text-slate-400 italic">
                AI recommendation advisory has not been generated for this bid submission yet. Click "Refresh Recommendation" to generate.
              </div>
            )}

            <div className="p-2.5 rounded bg-slate-800/60 border border-slate-700 text-[11px] text-slate-400 flex items-center justify-between">
              <span>Confidence: <strong>{recConfidence}</strong></span>
              <span>Source Engine: <strong>{recObj?.generated_by || "RULE_ENGINE"}</strong></span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 2. Procurement Officer Qualification Decision Panel */}
      <Card className="shadow-subtle border-slate-200 bg-white">
        <CardHeader className="pb-3 border-b border-slate-100 flex flex-row items-center justify-between">
          <div className="flex items-center gap-2">
            <UserCheck className="h-5 w-5 text-slate-900" />
            <div>
              <CardTitle className="text-sm font-bold text-slate-900">Procurement Officer Final Decision (Authoritative)</CardTitle>
              <CardDescription className="text-xs text-slate-500">
                Official human-in-the-loop qualification decision recorded in system audit logs.
              </CardDescription>
            </div>
          </div>
          {getDecisionBadge(activeDecision?.decision)}
        </CardHeader>

        <CardContent className="p-5 space-y-4 text-xs">
          {decisionError && (
            <div className="p-3 rounded bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-red-600 shrink-0" />
              <span>{decisionError}</span>
            </div>
          )}

          {activeDecision ? (
            /* Post-Decision Recorded / Immutable State */
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3">
                <div className="flex items-center justify-between flex-wrap gap-2 text-slate-700 border-b border-slate-200 pb-2">
                  <div className="flex items-center gap-2">
                    <Lock className="h-4 w-4 text-slate-500" />
                    <span className="font-bold text-slate-900">Final Decision Recorded</span>
                  </div>
                  <span className="text-[11px]">
                    Decided at: <strong>{activeDecision.decided_at || activeDecision.created_at ? new Date(activeDecision.decided_at || activeDecision.created_at).toLocaleString() : "N/A"}</strong>
                  </span>
                </div>

                <div className="text-slate-900 space-y-1">
                  <span className="font-bold text-slate-600 block text-[10px] uppercase tracking-wider">Official Legal / Procurement Reasoning:</span>
                  <p className="p-3 rounded bg-white border border-slate-200 text-slate-900 font-sans leading-relaxed text-xs">
                    "{activeDecision.reason}"
                  </p>
                </div>

                {/* Officer Override Indicator */}
                {(activeDecision.is_override || activeDecision.override) && (
                  <div className="p-3 rounded-md bg-amber-50 border border-amber-200 text-amber-900 text-xs font-semibold flex items-center gap-2">
                    <ShieldAlert className="h-4 w-4 text-amber-600 shrink-0" />
                    <span>Officer Override Notice: Official decision differs from automated AI advisory recommendation.</span>
                  </div>
                )}

                {/* Decision Context Historical Snapshot */}
                {(activeDecision.score_snapshot !== undefined || activeDecision.score_at_decision !== undefined || activeDecision.recommendation_at_decision) && (
                  <div className="p-3 rounded-lg bg-purple-50 border border-purple-100 space-y-1 text-purple-950">
                    <span className="font-bold text-[11px] flex items-center gap-1.5">
                      <History className="h-3.5 w-3.5 text-purple-600" />
                      Decision Context Snapshot (Historical State Captured at Approval Time):
                    </span>
                    <div className="grid grid-cols-3 gap-2 text-[11px] font-mono mt-1">
                      <div>Score Snapshot: <strong>{activeDecision.score_snapshot ?? activeDecision.score_at_decision ?? "N/A"}</strong></div>
                      <div>Risk Snapshot: <strong>{activeDecision.risk_snapshot ?? activeDecision.risk_at_decision ?? "N/A"}</strong></div>
                      <div>Rec Snapshot: <strong>{activeDecision.recommendation_at_decision ?? "N/A"}</strong></div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            /* Pre-Decision Form State */
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <span className="font-bold text-slate-900">Select Qualification Decision:</span>
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    size="sm"
                    onClick={() => setSelectedDecision("QUALIFIED")}
                    variant={selectedDecision === "QUALIFIED" ? "default" : "outline"}
                    className={selectedDecision === "QUALIFIED" ? "bg-emerald-600 text-white hover:bg-emerald-700" : "border-slate-300"}
                  >
                    <ThumbsUp className="mr-1.5 h-3.5 w-3.5" /> QUALIFIED
                  </Button>

                  <Button
                    type="button"
                    size="sm"
                    onClick={() => setSelectedDecision("DISQUALIFIED")}
                    variant={selectedDecision === "DISQUALIFIED" ? "destructive" : "outline"}
                    className={selectedDecision === "DISQUALIFIED" ? "bg-red-600 text-white" : "border-slate-300"}
                  >
                    <ThumbsDown className="mr-1.5 h-3.5 w-3.5" /> DISQUALIFIED
                  </Button>
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <Label className="text-xs font-semibold text-slate-700">Official Officer Reason & Legal Grounds (Min 10 characters required)</Label>
                  <span className={`text-[10px] font-mono font-bold ${officerReason.trim().length < 10 ? "text-amber-600" : "text-emerald-600"}`}>
                    {officerReason.trim().length} chars
                  </span>
                </div>
                <Textarea
                  placeholder="Enter detailed legal and procurement justification for this final decision..."
                  value={officerReason}
                  onChange={(e) => setOfficerReason(e.target.value)}
                  rows={3}
                  className="bg-white border-slate-300 text-xs text-slate-900"
                />
              </div>

              <div className="flex justify-end pt-2">
                <Button
                  type="button"
                  onClick={handleOpenConfirmDialog}
                  className="bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-sm px-6"
                >
                  <UserCheck className="mr-1.5 h-3.5 w-3.5" /> Submit Final Decision
                </Button>
              </div>

              {/* Confirmation Modal Dialog */}
              <Dialog open={openConfirmModal} onOpenChange={setOpenConfirmModal}>
                <DialogContent className="sm:max-w-md bg-white p-6">
                  <DialogHeader>
                    <DialogTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                      <Lock className="h-4 w-4 text-slate-700" />
                      Confirm Final Procurement Decision
                    </DialogTitle>
                    <CardDescription className="text-xs text-slate-500">
                      You are recording an authoritative procurement decision for submission #{bidSubmissionId}.
                    </CardDescription>
                  </DialogHeader>

                  <div className="space-y-3 py-2 text-xs">
                    <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500 font-semibold">Decision Outcome:</span>
                        {getDecisionBadge(selectedDecision)}
                      </div>
                      <div className="mt-2 text-slate-900">
                        <span className="text-slate-500 font-semibold block text-[10px] uppercase">Reason Summary:</span>
                        <p className="italic text-slate-800 font-sans mt-0.5">"{officerReason.trim()}"</p>
                      </div>
                    </div>

                    <div className="p-3 rounded bg-amber-50 border border-amber-200 text-[11px] text-amber-900">
                      <strong>Audit Notice:</strong> Once submitted, this decision is officially recorded in the audit trail and cannot be modified through normal workflows.
                    </div>
                  </div>

                  <DialogFooter className="pt-2 flex items-center justify-end gap-2">
                    <Button type="button" variant="outline" onClick={() => setOpenConfirmModal(false)} className="text-xs">
                      Cancel
                    </Button>
                    <Button
                      type="button"
                      onClick={handleConfirmDecisionSubmit}
                      disabled={recordDecisionMutation.isPending}
                      className="bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold"
                    >
                      {recordDecisionMutation.isPending ? "Recording Decision..." : "Confirm & Record Final Decision"}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 3. Requirement-Level Compliance Matrix Table */}
      <Card className="shadow-subtle border-slate-200 bg-white">
        <CardHeader className="pb-3 border-b border-slate-100">
          <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <BadgeCheck className="h-4 w-4 text-purple-600" />
            Evaluated Requirement Rules Checklist ({safeRequirementsList.length})
          </CardTitle>
          <CardDescription className="text-xs text-slate-500">
            Tender-specific eligibility checks evaluated against submitted document evidence and statutory verifications.
          </CardDescription>
        </CardHeader>

        <CardContent className="p-0 overflow-x-auto">
          {safeRequirementsList.length === 0 && safeChecks.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500 space-y-2">
              <AlertCircle className="h-8 w-8 text-slate-400 mx-auto" />
              <p className="font-semibold text-slate-800">No requirement evaluations registered yet.</p>
            </div>
          ) : (
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                  <th className="py-2.5 px-4">Requirement</th>
                  <th className="py-2.5 px-4">Mandatory</th>
                  <th className="py-2.5 px-4">Compliance Status</th>
                  <th className="py-2.5 px-4">Authoritative Finding / Explanation</th>
                  <th className="py-2.5 px-4">Score</th>
                  <th className="py-2.5 px-4 text-right">Evidence Link</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                {safeRequirementsList.map((req) => {
                  const matchingCheck = safeChecks.find((c) => c?.tender_requirement_id === req?.requirement_id || c?.requirement_code === req?.requirement_type);
                  const status = req.status || matchingCheck?.status || "PENDING";
                  const reason = req.reason || matchingCheck?.finding_details || matchingCheck?.reason || "—";
                  const score = req.score ?? matchingCheck?.score ?? null;

                  return (
                    <tr key={req.requirement_id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-3 px-4 font-semibold text-slate-900">
                        <div>{req.requirement_name}</div>
                        <span className="text-[10px] font-mono text-slate-400">{req.requirement_type}</span>
                      </td>
                      <td className="py-3 px-4">
                        {req.mandatory ? (
                          <Badge className="bg-purple-100 text-purple-800 border-purple-200 text-[10px]">Mandatory</Badge>
                        ) : (
                          <Badge variant="outline" className="text-slate-500 text-[10px]">Optional</Badge>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        {status === "PASS" && <Badge className="bg-emerald-600 text-white text-[10px]">PASS</Badge>}
                        {status === "FAIL" && <Badge className="bg-red-600 text-white text-[10px]">FAIL</Badge>}
                        {status === "REVIEW" && <Badge className="bg-amber-500 text-white text-[10px]">REVIEW</Badge>}
                        {status === "PENDING" && <Badge variant="outline" className="text-slate-500 text-[10px]">PENDING</Badge>}
                      </td>
                      <td className="py-3 px-4 text-[11px] text-slate-600 max-w-md leading-relaxed">
                        {reason}
                      </td>
                      <td className="py-3 px-4 font-mono font-bold text-slate-900">
                        {score !== null ? `${score.toFixed(0)} / 100` : "—"}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <Link to={`/bids/${bidSubmissionId}/documents`}>
                            <Button size="sm" variant="ghost" className="h-6 text-[10px] text-blue-600 hover:text-blue-800 px-2">
                              <FileText className="mr-1 h-3 w-3" /> Docs
                            </Button>
                          </Link>
                          <Link to={`/bids/${bidSubmissionId}/verification`}>
                            <Button size="sm" variant="ghost" className="h-6 text-[10px] text-emerald-600 hover:text-emerald-800 px-2">
                              <ShieldCheck className="mr-1 h-3 w-3" /> Verif
                            </Button>
                          </Link>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>

      {/* 4. Cross-Verification & Discrepancies Log */}
      <Card className="shadow-subtle border-slate-200 bg-white">
        <CardHeader className="pb-3 border-b border-slate-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-amber-600" />
              Persisted Discrepancies & Missing Evidence Log ({discrepancies.length})
            </CardTitle>
            <CardDescription className="text-xs text-slate-500">
              Structured findings tracked across cross-verification, compliance engine checks, and extracted evidence.
            </CardDescription>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="outline" className="bg-slate-100 text-slate-700 border-slate-300 text-xs">
              Total: {discrepancies.length}
            </Badge>
            {openDiscrepanciesCount > 0 ? (
              <Badge variant="outline" className="bg-amber-100 text-amber-800 border-amber-300 text-xs font-bold">
                {openDiscrepanciesCount} Open
              </Badge>
            ) : (
              <Badge variant="outline" className="bg-emerald-100 text-emerald-800 border-emerald-300 text-xs font-bold">
                0 Open Findings
              </Badge>
            )}

            {/* Filter Tabs */}
            <div className="flex items-center bg-slate-100 p-0.5 rounded-lg border border-slate-200 text-xs ml-2">
              {["ALL", "OPEN", "RESOLVED", "WAIVED"].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setDiscrepancyFilter(tab)}
                  className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-all ${
                    discrepancyFilter === tab
                      ? "bg-white text-slate-900 shadow-sm font-bold"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-0 divide-y divide-slate-100 text-xs">
          {filteredDiscrepancies.length === 0 ? (
            <div className="p-6 text-center text-slate-500 space-y-1">
              <CheckCircle2 className="h-8 w-8 text-emerald-500 mx-auto opacity-80" />
              <p className="font-semibold text-slate-700">No {discrepancyFilter.toLowerCase()} discrepancies found.</p>
            </div>
          ) : (
            filteredDiscrepancies.map((disc) => (
              <div key={disc.id} className="p-4 space-y-3 bg-white hover:bg-slate-50/50 transition-colors">
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-1 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-bold text-slate-900 text-xs">{disc.title}</span>
                      {getSeverityBadge(disc.severity)}
                      <Badge variant="outline" className="bg-slate-50 text-slate-600 border-slate-200 text-[10px]">
                        Status: {disc.status}
                      </Badge>
                    </div>
                    <p className="text-slate-600 leading-relaxed text-xs">{disc.description}</p>
                  </div>

                  {disc.status === "OPEN" && resolvingId !== disc.id && (
                    <div className="flex items-center gap-2 shrink-0">
                      <Button
                        size="sm"
                        onClick={() => {
                          setResolvingId(disc.id);
                          setResolutionAction("RESOLVED");
                          setResolutionNoteInput("");
                          setResolutionError(null);
                        }}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white text-[11px] h-7 px-2.5"
                      >
                        <Check className="mr-1 h-3 w-3" /> Resolve
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setResolvingId(disc.id);
                          setResolutionAction("WAIVED");
                          setResolutionNoteInput("");
                          setResolutionError(null);
                        }}
                        className="border-purple-300 text-purple-700 bg-purple-50 hover:bg-purple-100 text-[11px] h-7 px-2.5"
                      >
                        Waive
                      </Button>
                    </div>
                  )}
                </div>

                {resolvingId === disc.id && (
                  <div className="bg-slate-900 text-white p-3.5 rounded-lg border border-slate-700 space-y-3 mt-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                        <FileWarning className="h-4 w-4 text-amber-400" />
                        Set Status to: <span className="text-purple-300 font-mono">{resolutionAction}</span>
                      </span>
                      <button onClick={() => setResolvingId(null)} className="text-slate-400 hover:text-white text-xs">
                        Cancel
                      </button>
                    </div>

                    {resolutionError && (
                      <div className="p-2 rounded bg-red-900/80 border border-red-700 text-red-200 text-[11px]">
                        {resolutionError}
                      </div>
                    )}

                    <Textarea
                      placeholder={`Enter officer justification note for setting status to ${resolutionAction}...`}
                      value={resolutionNoteInput}
                      onChange={(e) => setResolutionNoteInput(e.target.value)}
                      rows={2}
                      className="bg-slate-800 border-slate-700 text-xs text-slate-100 placeholder:text-slate-500"
                    />

                    <div className="flex items-center justify-end gap-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setResolvingId(null)}
                        className="text-slate-300 hover:text-white text-xs"
                      >
                        Cancel
                      </Button>
                      <Button
                        size="sm"
                        onClick={() => handleResolveDiscrepancy(disc.id)}
                        disabled={updateDiscrepancyMutation.isPending}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs"
                      >
                        {updateDiscrepancyMutation.isPending ? "Saving..." : `Confirm ${resolutionAction}`}
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </PageContainer>
  );
}
