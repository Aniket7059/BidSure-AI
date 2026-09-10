import React from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import {
  FileText,
  ShieldCheck,
  BadgeCheck,
  ArrowLeft,
  Building2,
  ExternalLink,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  ShieldAlert,
  Cpu,
  History,
  UserCheck,
  RefreshCw,
  FileWarning,
  Sparkles,
  ListChecks,
  Activity,
  FileCheck,
  AlertCircle
} from "lucide-react";
import { PageContainer } from "../components/layout/PageContainer";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { RiskBadge } from "../components/shared/RiskBadge";
import { ScoreGauge } from "../components/shared/ScoreGauge";
import { LoadingState } from "../components/shared/LoadingState";
import { ErrorState } from "../components/shared/ErrorState";
import { useBidEvaluationDashboardQuery } from "../features/dashboard/useDashboard";

export function BidDetailsPage() {
  const { bidSubmissionId } = useParams();
  const navigate = useNavigate();

  const {
    data,
    isLoading,
    isError,
    error,
    refetch
  } = useBidEvaluationDashboardQuery(bidSubmissionId);

  if (isLoading) {
    return (
      <PageContainer title="Bid Evaluation Workspace" description="Loading authoritative evaluation payload from backend services...">
        <LoadingState message="Loading bid evaluation metrics, statutory verifications, and compliance findings..." />
      </PageContainer>
    );
  }

  if (isError || !data || !data.bid_submission) {
    const errorMsg = error?.response?.status === 404
      ? `Bid submission #${bidSubmissionId} was not found.`
      : error?.response?.status === 403
      ? "You do not have permission to view this bid evaluation workspace."
      : "Unable to connect to backend service. Please check your connection and try again.";

    return (
      <PageContainer
        title="Bid Evaluation Workspace"
        description="Authoritative Procurement Officer Evaluation Center"
        actions={
          <Link to="/tenders">
            <Button size="sm" variant="outline">
              <ArrowLeft className="mr-1.5 h-3.5 w-3.5" /> Back to Tenders
            </Button>
          </Link>
        }
      >
        <ErrorState
          title="Bid Evaluation Unavailable"
          message={errorMsg}
          onRetry={refetch}
        />
      </PageContainer>
    );
  }

  const {
    bid_submission: submission,
    tender,
    bidder,
    summary,
    requirements = [],
    documents = [],
    verification = [],
    discrepancies = [],
    compliance,
    recommendation,
    decision,
    audit
  } = data;

  // Helper status badge getters using authoritative backend values
  const getComplianceStatusBadge = (status) => {
    const s = (status || "PENDING").toUpperCase();
    if (s === "PASS") {
      return <Badge className="bg-emerald-600 text-white font-bold text-xs">COMPLIANT (PASS)</Badge>;
    }
    if (s === "FAIL") {
      return <Badge className="bg-red-600 text-white font-bold text-xs">NON-COMPLIANT (FAIL)</Badge>;
    }
    if (s === "REVIEW") {
      return <Badge className="bg-amber-500 text-white font-bold text-xs">REVIEW REQUIRED</Badge>;
    }
    return <Badge variant="outline" className="bg-slate-100 text-slate-700 border-slate-300 text-xs">PENDING EVALUATION</Badge>;
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

  const getDecisionBadge = (dec) => {
    const d = (dec || "").toUpperCase();
    if (d === "QUALIFIED") {
      return <Badge className="bg-emerald-600 text-white font-bold text-xs">QUALIFIED</Badge>;
    }
    if (d === "DISQUALIFIED") {
      return <Badge className="bg-red-600 text-white font-bold text-xs">DISQUALIFIED</Badge>;
    }
    if (d === "CLARIFICATION_REQUIRED") {
      return <Badge className="bg-amber-500 text-white font-bold text-xs font-mono">CLARIFICATION REQUESTED</Badge>;
    }
    return <Badge variant="outline" className="bg-slate-100 text-slate-700 border-slate-300 text-xs">Awaiting Procurement Officer decision</Badge>;
  };

  // Compile "Attention Required" items strictly from real backend payloads
  const attentionItems = [];

  // 1. Open Discrepancies
  discrepancies.filter((d) => d.status === "OPEN").forEach((d) => {
    attentionItems.push({
      id: `disc-${d.id}`,
      severity: d.severity,
      category: `Discrepancy: ${d.type}`,
      title: d.title,
      description: d.description,
      link: `/bids/${bidSubmissionId}/compliance`,
      linkText: "Resolve Discrepancy",
    });
  });

  // 2. Failed / Review Compliance Requirements
  requirements.filter((r) => r.status === "FAIL" || r.status === "REVIEW").forEach((r) => {
    attentionItems.push({
      id: `req-${r.requirement_id}`,
      severity: r.mandatory ? (r.status === "FAIL" ? "CRITICAL" : "HIGH") : "MEDIUM",
      category: `Requirement: ${r.requirement_type}`,
      title: r.requirement_name,
      description: r.reason || `Requirement evaluated with status ${r.status}.`,
      link: `/bids/${bidSubmissionId}/compliance`,
      linkText: "Inspect Requirement",
    });
  });

  // 3. Verification Failures or Mismatches
  verification.filter((v) => v.status === "FAILED" || v.status === "MISMATCH" || v.status === "ERROR").forEach((v) => {
    attentionItems.push({
      id: `verif-${v.id}`,
      severity: "HIGH",
      category: `Statutory Check: ${v.provider}`,
      title: `${v.verification_type} Verification Failure`,
      description: v.message || "Registry check returned unverified or mismatched status.",
      link: `/bids/${bidSubmissionId}/verification`,
      linkText: "View Portal Verification",
    });
  });

  const formattedDate = submission.submitted_at
    ? new Date(submission.submitted_at).toLocaleString("en-IN", {
        dateStyle: "medium",
        timeStyle: "short",
      })
    : "N/A";

  const scoreValue = summary.score !== null && summary.score !== undefined
    ? summary.score
    : (compliance?.score !== null && compliance?.score !== undefined ? compliance.score : null);

  const riskLevel = summary.risk_level || compliance?.risk_level || null;

  return (
    <PageContainer
      title={`Bid Evaluation Workspace (#${submission.id})`}
      description={`Authoritative evaluation for ${bidder.company_name} under Tender ${tender.reference_number}`}
      badge={
        <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 text-xs font-semibold">
          Submission Status: {submission.status}
        </Badge>
      }
      actions={
        <div className="flex items-center gap-2 flex-wrap">
          <Link to={`/tenders/${tender.id}/bids`}>
            <Button size="sm" variant="outline" className="text-xs">
              <ArrowLeft className="mr-1.5 h-3.5 w-3.5" /> Back to Bids List
            </Button>
          </Link>
          <Link to={`/tenders/${tender.id}`}>
            <Button size="sm" variant="outline" className="text-xs">
              <Building2 className="mr-1.5 h-3.5 w-3.5 text-slate-500" /> View Tender Notice
            </Button>
          </Link>
        </div>
      }
    >
      {/* 1. Strong Bid Header Card */}
      <Card className="shadow-subtle border-slate-200 bg-white">
        <CardContent className="p-6 space-y-4">
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 border-b border-slate-100 pb-4">
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <h2 className="text-xl font-bold text-slate-900">{bidder.company_name}</h2>
                {riskLevel ? (
                  <RiskBadge riskLevel={riskLevel} />
                ) : (
                  <Badge variant="outline" className="bg-slate-100 text-slate-600 border-slate-300 text-xs">
                    Risk Pending
                  </Badge>
                )}
                {getDecisionBadge(summary.final_decision || decision?.decision)}
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Tender: <strong className="text-slate-800">{tender.reference_number}</strong> — {tender.title}
              </p>
            </div>

            <div className="text-right text-xs text-slate-500 shrink-0">
              <p>Submitted: <strong className="text-slate-900">{formattedDate}</strong></p>
              <p className="mt-0.5">Tender Requirements: <strong className="text-slate-900">{tender.requirement_count}</strong></p>
            </div>
          </div>

          {/* Bidder Registry Identifiers */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
              <span className="text-slate-400 font-medium block text-[10px] uppercase tracking-wider">GSTIN</span>
              <span className="font-mono font-bold text-slate-900 mt-0.5 block">{bidder.gstin || "N/A"}</span>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
              <span className="text-slate-400 font-medium block text-[10px] uppercase tracking-wider">PAN</span>
              <span className="font-mono font-bold text-slate-900 mt-0.5 block">{bidder.pan || "N/A"}</span>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
              <span className="text-slate-400 font-medium block text-[10px] uppercase tracking-wider">Udyam Registration</span>
              <span className="font-mono font-bold text-slate-900 mt-0.5 block">{bidder.udyam_number || "N/A"}</span>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
              <span className="text-slate-400 font-medium block text-[10px] uppercase tracking-wider">Contact</span>
              <span className="font-semibold text-slate-900 mt-0.5 block truncate">{bidder.contact_email || bidder.contact_phone || "N/A"}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Persistent Bid Sub-Navigation Bar */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-2 overflow-x-auto">
        <Button size="sm" variant="default" className="bg-slate-900 text-white text-xs font-semibold">
          <Activity className="mr-1.5 h-3.5 w-3.5" /> Workspace Overview
        </Button>
        <Link to={`/bids/${bidSubmissionId}/documents`}>
          <Button size="sm" variant="outline" className="text-xs text-slate-700 hover:bg-slate-100">
            <FileText className="mr-1.5 h-3.5 w-3.5 text-blue-600" /> Documents ({documents.length})
          </Button>
        </Link>
        <Link to={`/bids/${bidSubmissionId}/verification`}>
          <Button size="sm" variant="outline" className="text-xs text-slate-700 hover:bg-slate-100">
            <ShieldCheck className="mr-1.5 h-3.5 w-3.5 text-emerald-600" /> Statutory Verifications ({verification.length})
          </Button>
        </Link>
        <Link to={`/bids/${bidSubmissionId}/compliance`}>
          <Button size="sm" variant="outline" className="text-xs text-slate-700 hover:bg-slate-100">
            <BadgeCheck className="mr-1.5 h-3.5 w-3.5 text-purple-600" /> Compliance & Decision
          </Button>
        </Link>
        <Link to={`/bids/${bidSubmissionId}/audit`}>
          <Button size="sm" variant="outline" className="text-xs text-slate-700 hover:bg-slate-100">
            <History className="mr-1.5 h-3.5 w-3.5 text-slate-600" /> Audit Trail
          </Button>
        </Link>
      </div>

      {/* 2. Evaluation Summary: 5 Visually Distinct Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Card 1: Compliance State */}
        <Card className="shadow-subtle border-slate-200 bg-white">
          <CardContent className="p-4 flex flex-col justify-between h-full space-y-2">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Compliance State</span>
            <div className="my-1">
              {getComplianceStatusBadge(summary.overall_status || compliance?.status)}
            </div>
            <span className="text-[11px] text-slate-500 block">
              Mandatory: {summary.mandatory?.pass_count ?? 0} Pass / {summary.mandatory?.fail_count ?? 0} Fail / {summary.mandatory?.review_count ?? 0} Review
            </span>
          </CardContent>
        </Card>

        {/* Card 2: Compliance Score */}
        <Card className="shadow-subtle border-slate-200 bg-white">
          <CardContent className="p-4 flex flex-col justify-between h-full space-y-2">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Evaluation Score</span>
            <div className="my-1">
              {scoreValue !== null ? (
                <div className="flex items-baseline gap-1">
                  <span className="text-2xl font-black text-slate-900">{Number(scoreValue).toFixed(0)}</span>
                  <span className="text-xs font-semibold text-slate-500">/ 100</span>
                </div>
              ) : (
                <span className="text-xs font-bold text-slate-500 italic">Not yet evaluated</span>
              )}
            </div>
            <span className="text-[11px] text-slate-500 block">
              {scoreValue !== null ? `Evaluated by Rule Engine` : "Awaiting Evaluation Run"}
            </span>
          </CardContent>
        </Card>

        {/* Card 3: Risk Level */}
        <Card className="shadow-subtle border-slate-200 bg-white">
          <CardContent className="p-4 flex flex-col justify-between h-full space-y-2">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Risk Classification</span>
            <div className="my-1">
              {riskLevel ? (
                <RiskBadge riskLevel={riskLevel} />
              ) : (
                <Badge variant="outline" className="bg-slate-100 text-slate-600 border-slate-300 text-xs">
                  Pending / Unavailable
                </Badge>
              )}
            </div>
            <span className="text-[11px] text-slate-500 block">
              Discrepancies: {summary.discrepancies?.open ?? 0} Open
            </span>
          </CardContent>
        </Card>

        {/* Card 4: AI Recommendation */}
        <Card className="shadow-subtle border-slate-200 bg-white">
          <CardContent className="p-4 flex flex-col justify-between h-full space-y-2">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">AI Recommendation</span>
            <div className="my-1">
              {getRecommendationBadge(summary.recommendation || recommendation?.recommendation)}
            </div>
            <span className="text-[11px] text-slate-500 block">
              Confidence: {recommendation?.confidence || "N/A"}
            </span>
          </CardContent>
        </Card>

        {/* Card 5: Officer Decision */}
        <Card className="shadow-subtle border-slate-200 bg-white">
          <CardContent className="p-4 flex flex-col justify-between h-full space-y-2">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Officer Decision</span>
            <div className="my-1">
              {getDecisionBadge(summary.final_decision || decision?.decision)}
            </div>
            <span className="text-[11px] text-slate-500 block">
              {decision ? `Decided by ${decision.decided_by?.full_name || "Officer"}` : "Action Required"}
            </span>
          </CardContent>
        </Card>
      </div>

      {/* 3. Attention Required Section */}
      <Card className="shadow-subtle border-amber-200 bg-amber-50/30">
        <CardHeader className="pb-3 border-b border-amber-200/60">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-amber-600" />
              Attention Required ({attentionItems.length})
            </CardTitle>
            {attentionItems.length > 0 && (
              <Badge className="bg-amber-600 text-white font-bold text-[10px]">Action Required</Badge>
            )}
          </div>
          <CardDescription className="text-xs text-slate-600">
            Real-time findings, statutory mismatches, and requirement review flags generated by backend engines.
          </CardDescription>
        </CardHeader>

        <CardContent className="p-4 space-y-3">
          {attentionItems.length === 0 ? (
            <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center gap-3">
              <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" />
              <div>
                <h4 className="text-xs font-bold text-emerald-900">No Attention Items Identified</h4>
                <p className="text-[11px] text-emerald-700">All evaluated statutory checks and tender requirements are compliant without open findings.</p>
              </div>
            </div>
          ) : (
            <div className="space-y-2.5">
              {attentionItems.map((item) => (
                <div key={item.id} className="p-3.5 rounded-lg bg-white border border-slate-200 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      {item.severity === "CRITICAL" && <Badge className="bg-red-600 text-white font-bold text-[10px]">CRITICAL</Badge>}
                      {item.severity === "HIGH" && <Badge className="bg-orange-500 text-white font-bold text-[10px]">HIGH</Badge>}
                      {item.severity === "MEDIUM" && <Badge className="bg-amber-500 text-white font-bold text-[10px]">MEDIUM</Badge>}
                      <span className="font-semibold text-slate-900">{item.title}</span>
                      <span className="text-[10px] text-slate-400 font-mono">({item.category})</span>
                    </div>
                    <p className="text-slate-600 text-[11px] leading-relaxed">{item.description}</p>
                  </div>

                  <Link to={item.link} className="shrink-0">
                    <Button size="sm" variant="outline" className="text-[11px] h-7 border-slate-300">
                      {item.linkText} <ExternalLink className="ml-1 h-3 w-3" />
                    </Button>
                  </Link>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 4. Tender Requirements Matrix Overview */}
      <Card className="shadow-subtle border-slate-200">
        <CardHeader className="pb-3 border-b border-slate-100 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <ListChecks className="h-4 w-4 text-purple-600" />
              Tender Eligibility Requirements Matrix ({requirements.length})
            </CardTitle>
            <CardDescription className="text-xs text-slate-500">
              Evaluated rule states for each statutory & technical requirement defined in the tender.
            </CardDescription>
          </div>
          <Link to={`/bids/${bidSubmissionId}/compliance`}>
            <Button size="sm" variant="outline" className="text-xs">
              Open Full Compliance Matrix <ExternalLink className="ml-1.5 h-3.5 w-3.5" />
            </Button>
          </Link>
        </CardHeader>

        <CardContent className="p-0 overflow-x-auto">
          {requirements.length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-500">No requirement evaluations registered for this tender yet.</div>
          ) : (
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                  <th className="py-2.5 px-4">Requirement</th>
                  <th className="py-2.5 px-[16px]">Mandatory</th>
                  <th className="py-2.5 px-4">Evidence</th>
                  <th className="py-2.5 px-4">Portal Verification</th>
                  <th className="py-2.5 px-4">Compliance Check</th>
                  <th className="py-2.5 px-4">Reason / Notes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                {requirements.map((req) => (
                  <tr key={req.requirement_id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3 px-4 font-semibold text-slate-900">
                      <div>{req.requirement_name}</div>
                      <span className="text-[10px] font-mono text-slate-400">{req.requirement_type}</span>
                    </td>
                    <td className="py-3 px-4">
                      {req.mandatory ? (
                        <Badge className="bg-purple-100 text-purple-800 border-purple-200 text-[10px]">Yes</Badge>
                      ) : (
                        <Badge variant="outline" className="text-slate-500 text-[10px]">Optional</Badge>
                      )}
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-700">
                      {req.evidence_count} Document{req.evidence_count !== 1 ? "s" : ""}
                    </td>
                    <td className="py-3 px-4">
                      <Badge variant="outline" className="bg-slate-50 text-slate-700 border-slate-200 text-[10px] font-mono">
                        {req.verification_status}
                      </Badge>
                    </td>
                    <td className="py-3 px-4">
                      {req.status === "PASS" && <Badge className="bg-emerald-600 text-white text-[10px]">PASS</Badge>}
                      {req.status === "FAIL" && <Badge className="bg-red-600 text-white text-[10px]">FAIL</Badge>}
                      {req.status === "REVIEW" && <Badge className="bg-amber-500 text-white text-[10px]">REVIEW</Badge>}
                      {req.status === "PENDING" && <Badge variant="outline" className="text-slate-500 text-[10px]">PENDING</Badge>}
                    </td>
                    <td className="py-3 px-4 text-[11px] text-slate-600 max-w-xs truncate">
                      {req.reason || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>

      {/* 5. Split Section: Document Summary & Statutory Verification Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Document Summary */}
        <Card className="shadow-subtle border-slate-200">
          <CardHeader className="pb-3 border-b border-slate-100 flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <FileText className="h-4 w-4 text-blue-600" />
                Submitted Bid Documents ({documents.length})
              </CardTitle>
              <CardDescription className="text-xs text-slate-500">
                Uploaded PDFs, OCR intelligence, and extracted data.
              </CardDescription>
            </div>
            <Link to={`/bids/${bidSubmissionId}/documents`}>
              <Button size="sm" variant="outline" className="text-xs">
                View All <ExternalLink className="ml-1 h-3 w-3" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="p-0 divide-y divide-slate-100 text-xs">
            {documents.length === 0 ? (
              <div className="p-6 text-center text-slate-500">No documents uploaded for this bid submission.</div>
            ) : (
              documents.slice(0, 5).map((doc) => (
                <div key={doc.id} className="p-3.5 flex items-center justify-between gap-3">
                  <div className="space-y-0.5 min-w-0">
                    <span className="font-semibold text-slate-900 block truncate">{doc.file_name}</span>
                    <span className="text-[10px] text-slate-500 block font-mono">{doc.document_type}</span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {doc.confidence_score !== null && doc.confidence_score !== undefined && (
                      <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200 text-[10px]">
                        OCR: {(doc.confidence_score * 100).toFixed(0)}%
                      </Badge>
                    )}
                    <Badge variant="outline" className="bg-slate-50 text-slate-700 border-slate-200 text-[10px]">
                      {doc.status}
                    </Badge>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Statutory Verifications Overview */}
        <Card className="shadow-subtle border-slate-200">
          <CardHeader className="pb-3 border-b border-slate-100 flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-emerald-600" />
                Statutory Verifications ({verification.length})
              </CardTitle>
              <CardDescription className="text-xs text-slate-500">
                Government registry & statutory database checks.
              </CardDescription>
            </div>
            <Link to={`/bids/${bidSubmissionId}/verification`}>
              <Button size="sm" variant="outline" className="text-xs">
                View Verifications <ExternalLink className="ml-1 h-3 w-3" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="p-0 divide-y divide-slate-100 text-xs">
            {verification.length === 0 ? (
              <div className="p-6 text-center text-slate-500">No portal verifications executed yet.</div>
            ) : (
              verification.slice(0, 5).map((v) => (
                <div key={v.id} className="p-3.5 flex items-center justify-between gap-3">
                  <div className="space-y-0.5 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="font-semibold text-slate-900">{v.provider}</span>
                      <span className="text-[10px] text-slate-400 font-mono">({v.verification_type})</span>
                    </div>
                    <p className="text-[11px] text-slate-500 truncate">{v.message || `ID: ${v.identifier}`}</p>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {v.status === "VERIFIED" && <Badge className="bg-emerald-600 text-white text-[10px]">VERIFIED</Badge>}
                    {v.status === "FAILED" && <Badge className="bg-red-600 text-white text-[10px]">FAILED</Badge>}
                    {v.status === "REVIEW" && <Badge className="bg-amber-500 text-white text-[10px]">REVIEW</Badge>}
                    {v.status === "PENDING" && <Badge variant="outline" className="text-slate-500 text-[10px]">PENDING</Badge>}
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      {/* 6. Discrepancies Summary */}
      <Card className="shadow-subtle border-slate-200">
        <CardHeader className="pb-3 border-b border-slate-100 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <FileWarning className="h-4 w-4 text-amber-600" />
              Identified Discrepancies & Cross-Source Conflicts ({discrepancies.length})
            </CardTitle>
            <CardDescription className="text-xs text-slate-500">
              Cross-document and registry mismatches detected by compliance engines.
            </CardDescription>
          </div>
          <Link to={`/bids/${bidSubmissionId}/compliance`}>
            <Button size="sm" variant="outline" className="text-xs">
              Resolve Discrepancies <ExternalLink className="ml-1 h-3 w-3" />
            </Button>
          </Link>
        </CardHeader>

        <CardContent className="p-0 divide-y divide-slate-100 text-xs">
          {discrepancies.length === 0 ? (
            <div className="p-6 text-center text-slate-500 flex flex-col items-center gap-2">
              <CheckCircle2 className="h-6 w-6 text-emerald-500" />
              <p className="font-semibold text-slate-700">No discrepancies identified.</p>
              <p className="text-[11px] text-slate-400">Extracted document facts completely match statutory portal records.</p>
            </div>
          ) : (
            discrepancies.map((d) => (
              <div key={d.id} className="p-4 space-y-2">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-bold text-slate-900">{d.title}</span>
                    {d.severity === "CRITICAL" && <Badge className="bg-red-600 text-white font-bold text-[10px]">CRITICAL</Badge>}
                    {d.severity === "HIGH" && <Badge className="bg-orange-500 text-white font-bold text-[10px]">HIGH</Badge>}
                    {d.severity === "MEDIUM" && <Badge className="bg-amber-500 text-white font-bold text-[10px]">MEDIUM</Badge>}
                    <Badge variant="outline" className="bg-slate-50 text-slate-600 border-slate-200 text-[10px]">
                      {d.status}
                    </Badge>
                  </div>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {d.created_at ? new Date(d.created_at).toLocaleDateString() : ""}
                  </span>
                </div>
                <p className="text-slate-600 text-[11px] leading-relaxed">{d.description}</p>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      {/* 7. AI Recommendation Detail & Procurement Officer Decision */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Stored AI Advisory Recommendation */}
        <Card className="shadow-subtle border-slate-200 bg-slate-900 text-white flex flex-col justify-between">
          <CardHeader className="pb-3 border-b border-slate-800 flex flex-row items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-purple-400" />
              <CardTitle className="text-sm font-bold text-white">AI Recommendation Engine</CardTitle>
            </div>
            <Badge variant="outline" className="bg-purple-950 text-purple-300 border-purple-800 text-[10px]">
              ADVISORY ONLY
            </Badge>
          </CardHeader>
          <CardContent className="p-5 space-y-3 text-xs">
            {recommendation ? (
              <>
                <div className="flex items-center justify-between bg-slate-800/80 p-3 rounded-lg border border-slate-700">
                  <span className="font-semibold text-slate-300">Recommendation Status:</span>
                  {getRecommendationBadge(recommendation.recommendation)}
                </div>

                <p className="text-slate-200 leading-relaxed p-3 bg-slate-800/50 rounded-lg border border-slate-700/60 font-sans italic">
                  "{recommendation.summary}"
                </p>

                {recommendation.critical_issues?.length > 0 && (
                  <div className="space-y-1">
                    <span className="font-bold text-red-400 block text-[11px]">Critical Risk Factors:</span>
                    <ul className="list-disc list-inside text-slate-300 space-y-0.5 text-[11px]">
                      {recommendation.critical_issues.map((issue, idx) => (
                        <li key={idx}>{typeof issue === "object" ? issue.description || JSON.stringify(issue) : issue}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            ) : (
              <div className="p-6 text-center text-slate-400 italic">
                AI evaluation recommendation has not been generated for this bid yet.
              </div>
            )}
          </CardContent>
        </Card>

        {/* Right Column: Procurement Officer Decision & Decision-Time Snapshot */}
        <Card className="shadow-subtle border-slate-200 bg-white flex flex-col justify-between">
          <CardHeader className="pb-3 border-b border-slate-100 flex flex-row items-center justify-between">
            <div className="flex items-center gap-2">
              <UserCheck className="h-4 w-4 text-slate-800" />
              <CardTitle className="text-sm font-bold text-slate-900">Procurement Officer Final Decision</CardTitle>
            </div>
            {getDecisionBadge(decision?.decision || summary.final_decision)}
          </CardHeader>

          <CardContent className="p-5 space-y-4 text-xs">
            {decision ? (
              <div className="space-y-3">
                <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
                  <div className="flex items-center justify-between text-slate-700">
                    <span>Decided By: <strong>{decision.decided_by?.full_name} ({decision.decided_by?.role})</strong></span>
                    <span>{decision.decided_at ? new Date(decision.decided_at).toLocaleString() : ""}</span>
                  </div>
                  <div className="text-slate-900">
                    <span className="font-bold text-slate-700 block text-[10px] uppercase tracking-wider">Official Officer Reason:</span>
                    <p className="mt-0.5 leading-relaxed font-sans">{decision.reason}</p>
                  </div>
                </div>

                {/* Decision Context Historical Snapshot */}
                {(decision.score_at_decision !== null || decision.recommendation_at_decision) && (
                  <div className="p-3 rounded-lg bg-purple-50/60 border border-purple-100 space-y-1">
                    <span className="font-bold text-purple-900 text-[11px] flex items-center gap-1.5">
                      <History className="h-3.5 w-3.5 text-purple-600" />
                      Decision Context Snapshot (Historical State at Approval Time):
                    </span>
                    <div className="grid grid-cols-3 gap-2 text-[10px] text-purple-950 font-mono mt-1">
                      <div>Score: {decision.score_at_decision ?? "N/A"}</div>
                      <div>Risk: {decision.risk_at_decision ?? "N/A"}</div>
                      <div>Rec: {decision.recommendation_at_decision ?? "N/A"}</div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-6 text-center text-slate-500 space-y-2">
                <Clock className="h-8 w-8 text-slate-400 mx-auto" />
                <p className="font-semibold text-slate-800">Awaiting Procurement Officer Decision</p>
                <p className="text-[11px] text-slate-500 max-w-xs mx-auto">
                  Review the compliance matrix, statutory verifications, and AI advisory recommendations to record your qualification decision.
                </p>
              </div>
            )}

            <div className="pt-2 border-t border-slate-100">
              <Link to={`/bids/${bidSubmissionId}/compliance`}>
                <Button className="w-full bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold">
                  <UserCheck className="mr-1.5 h-3.5 w-3.5" />
                  {decision ? "Manage Officer Qualification Decision" : "Record Officer Qualification Decision"}
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 8. Recent Audit Timeline */}
      {audit?.events?.length > 0 && (
        <Card className="shadow-subtle border-slate-200">
          <CardHeader className="pb-3 border-b border-slate-100">
            <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Activity className="h-4 w-4 text-slate-700" />
              Recent Evaluation Audit Timeline ({audit.total_events} events)
            </CardTitle>
            <CardDescription className="text-xs text-slate-500">
              Immutable audit history of uploads, verifications, compliance checks, and decision logs.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 space-y-3">
            <div className="space-y-2 border-l-2 border-slate-200 pl-4 text-xs">
              {audit.events.slice(0, 6).map((evt) => (
                <div key={evt.id} className="relative space-y-0.5">
                  <div className="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full bg-slate-400 border-2 border-white" />
                  <div className="flex items-center justify-between text-slate-900">
                    <span className="font-bold font-mono text-slate-800">{evt.action}</span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {evt.created_at ? new Date(evt.created_at).toLocaleString() : ""}
                    </span>
                  </div>
                  <p className="text-slate-600 text-[11px]">{evt.details || `Entity: ${evt.entity_type} (#${evt.entity_id || ""})`}</p>
                  {evt.actor && <span className="text-[10px] text-slate-400 font-semibold">Actor: {evt.actor}</span>}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </PageContainer>
  );
}

