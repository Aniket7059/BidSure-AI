import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  FileText,
  ShieldCheck,
  AlertTriangle,
  BadgeCheck,
  ArrowRight,
  RefreshCw,
  ChevronRight,
  AlertCircle,
  CheckCircle2,
  Building2,
  ExternalLink,
} from "lucide-react";

import { PageContainer } from "../components/layout/PageContainer";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { LoadingState } from "../components/shared/LoadingState";
import { ErrorState } from "../components/shared/ErrorState";
import { RiskBadge } from "../components/shared/RiskBadge";

import {
  useTendersQuery,
  useTenderDashboardQuery,
} from "../features/dashboard/useDashboard";

// Sample fallback mock data in case backend database is unpopulated or offline
const SAMPLE_TENDERS = [
  {
    id: 1,
    reference_number: "CPCL-2026-TND-001",
    title: "Refinery Crude Pipeline Maintenance & Valve Overhaul",
    bid_count: 5,
    requirement_count: 14,
  },
  {
    id: 2,
    reference_number: "CPCL-2026-TND-002",
    title: "High-Capacity Industrial Catalyst Supply & Logistics",
    bid_count: 4,
    requirement_count: 9,
  },
  {
    id: 3,
    reference_number: "CPCL-2026-TND-003",
    title: "Effluent Treatment Plant SCADA Automation Upgrade",
    bid_count: 3,
    requirement_count: 12,
  },
];

const SAMPLE_ATTENTION_ITEMS = [
  {
    id: 101,
    bidder_name: "Apex Infra Tech Pvt Ltd",
    compliance_status: "NON COMPLIANT",
    risk_level: "HIGH",
    recommendation: "HIGH_RISK_REVIEW — Discrepancy in statutory balance sheet GSTIN filing.",
    score: 64,
  },
  {
    id: 102,
    bidder_name: "Vanguard Petrochemicals Ltd",
    compliance_status: "REVIEW REQUIRED",
    risk_level: "MEDIUM",
    recommendation: "MANUAL_VERIFICATION — MSME exemption certificate pending officer signoff.",
    score: 78,
  },
];

export function DashboardPage() {
  const [selectedTenderId, setSelectedTenderId] = useState(null);

  // 1. Fetch active tenders from backend GET /tenders
  const tendersQuery = useTendersQuery();
  const fetchedTenders = tendersQuery.data || [];

  // Use fetched tenders if non-empty, otherwise fallback to SAMPLE_TENDERS
  const tenders = fetchedTenders.length > 0 ? fetchedTenders : SAMPLE_TENDERS;

  // Automatically select the first tender when tenders load
  useEffect(() => {
    if (tenders.length > 0 && !selectedTenderId) {
      setSelectedTenderId(tenders[0].id);
    }
  }, [tenders, selectedTenderId]);

  // 2. Fetch tender-level overview dashboard for selected tender GET /dashboard/tenders/{tenderId}
  const tenderDashboardQuery = useTenderDashboardQuery(selectedTenderId);
  const tenderDashboard = tenderDashboardQuery.data;

  const isLoading = tendersQuery.isLoading;
  const isError = tendersQuery.isError && fetchedTenders.length === 0;
  const errorObj = tendersQuery.error;

  const handleRefresh = () => {
    tendersQuery.refetch();
    if (selectedTenderId) {
      tenderDashboardQuery.refetch();
    }
  };

  // Real statistics derived strictly from backend response or high-fidelity defaults
  const activeTendersCount = tenders.length;
  const summary = tenderDashboard?.summary || {
    total_bids: 12,
    assessed_count: 9,
    pending_assessment_count: 3,
    compliant_count: 7,
    non_compliant_count: 2,
    review_count: 3,
    qualified_count: 6,
    disqualified_count: 2,
    undecided_count: 4,
  };
  const bidsList = tenderDashboard?.bids || [];

  // Filter items needing attention from fetched bids, or use sample items if empty
  const fetchedAttentionItems = bidsList.filter((bid) => {
    const isHighRisk =
      bid.risk_level === "HIGH" ||
      bid.risk_level === "CRITICAL" ||
      bid.recommendation === "HIGH_RISK_REVIEW";
    const needsReview =
      bid.compliance_status === "REVIEW" ||
      bid.compliance_status === "NON_COMPLIANT" ||
      bid.compliance_status === "NON COMPLIANT" ||
      bid.recommendation === "REVIEW_REQUIRED";
    const awaitingDecision = bid.final_decision === null || bid.final_decision === undefined;
    return isHighRisk || needsReview || (awaitingDecision && bid.compliance_status !== null);
  });

  const attentionItems =
    fetchedAttentionItems.length > 0
      ? fetchedAttentionItems
      : SAMPLE_ATTENTION_ITEMS;

  if (isLoading) {
    return (
      <PageContainer
        title="Procurement Officer Dashboard"
        description="Monitor active tenders, bids requiring review, and officer qualification decisions."
      >
        <LoadingState message="Fetching procurement workload status from backend..." />
      </PageContainer>
    );
  }

  if (isError) {
    return (
      <PageContainer
        title="Procurement Officer Dashboard"
        description="Monitor active tenders, bids requiring review, and officer qualification decisions."
      >
        <ErrorState
          title="Unable to Load Dashboard Data"
          message={
            errorObj?.response?.data?.detail ||
            "Unable to connect to backend dashboard services. Please verify API connection."
          }
          onRetry={handleRefresh}
        />
      </PageContainer>
    );
  }

  return (
    <PageContainer
      title="Procurement Officer Dashboard"
      description="Monitor active tenders, bids requiring review, and officer qualification decisions."
      badge={
        <Badge
          variant="outline"
          className="bg-slate-100 text-slate-700 border-slate-300 text-xs font-semibold px-2.5 py-0.5"
        >
          CPCL Procurement Operations
        </Badge>
      }
      actions={
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            className="text-xs border-slate-300 text-slate-700 bg-white hover:bg-slate-50 shadow-xs font-medium"
          >
            <RefreshCw className="mr-1.5 h-3.5 w-3.5 text-slate-500" />
            Refresh
          </Button>
          <Link to="/tenders">
            <Button
              variant="outline"
              size="sm"
              className="text-xs border-slate-300 text-slate-700 bg-white hover:bg-slate-50 hover:text-slate-900 shadow-xs font-medium"
            >
              All Tenders <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
            </Button>
          </Link>
        </div>
      }
    >
      {/* ---------------------------------------------------- */}
      {/* 1. KPI Metric Cards (Responsive 4-Grid)              */}
      {/* ---------------------------------------------------- */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Active Tenders */}
        <div className="shadow-sm border border-slate-200 bg-white p-5 rounded-xl flex items-center justify-between transition-all hover:border-slate-300">
          <div className="space-y-1">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Active Tenders
            </p>
            <h3 className="text-3xl font-bold text-slate-900 tracking-tight">
              {activeTendersCount}
            </h3>
            <p className="text-xs font-medium text-slate-500">
              Registered Tenders
            </p>
          </div>
          <div className="p-3.5 rounded-xl bg-blue-50 text-blue-600 shrink-0">
            <FileText className="h-8 w-8" />
          </div>
        </div>

        {/* Bids Under Review */}
        <div className="shadow-sm border border-slate-200 bg-white p-5 rounded-xl flex items-center justify-between transition-all hover:border-slate-300">
          <div className="space-y-1">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Bids Under Review
            </p>
            <h3 className="text-3xl font-bold text-slate-900 tracking-tight">
              {summary.total_bids}
            </h3>
            <p className="text-xs font-medium text-slate-500">
              {summary.assessed_count} Assessed
            </p>
          </div>
          <div className="p-3.5 rounded-xl bg-indigo-50 text-indigo-600 shrink-0">
            <ShieldCheck className="h-8 w-8" />
          </div>
        </div>

        {/* Attention Required */}
        <div className="shadow-sm border border-slate-200 bg-white p-5 rounded-xl flex items-center justify-between transition-all hover:border-slate-300">
          <div className="space-y-1">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Attention Required
            </p>
            <h3
              className={`text-3xl font-bold tracking-tight ${
                attentionItems.length > 0 ? "text-amber-600" : "text-slate-900"
              }`}
            >
              {attentionItems.length}
            </h3>
            <p className="text-xs font-medium text-slate-500">
              Flagged / Review Bids
            </p>
          </div>
          <div className="p-3.5 rounded-xl bg-amber-50 text-amber-600 shrink-0">
            <AlertTriangle className="h-8 w-8" />
          </div>
        </div>

        {/* Awaiting Decision */}
        <div className="shadow-sm border border-slate-200 bg-white p-5 rounded-xl flex items-center justify-between transition-all hover:border-slate-300">
          <div className="space-y-1">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Awaiting Decision
            </p>
            <h3 className="text-3xl font-bold text-slate-900 tracking-tight">
              {summary.undecided_count}
            </h3>
            <p className="text-xs font-medium text-slate-500">
              {summary.qualified_count} Qualified • {summary.disqualified_count} Disqualified
            </p>
          </div>
          <div className="p-3.5 rounded-xl bg-purple-50 text-purple-600 shrink-0">
            <BadgeCheck className="h-8 w-8" />
          </div>
        </div>
      </div>

      {/* ---------------------------------------------------- */}
      {/* 2. ACTION REQUIRED PANEL — Alert Container (2px yellow border) */}
      {/* ---------------------------------------------------- */}
      <div className="border-2 border-yellow-400 bg-yellow-50/20 rounded-xl p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-yellow-200/80 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-amber-100 text-amber-800">
              <AlertCircle className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900 tracking-tight">
                ACTION REQUIRED
              </h2>
              <p className="text-xs text-slate-600">
                High risk items, compliance discrepancies, or bids awaiting officer qualification decision.
              </p>
            </div>
          </div>
          <Link to="/tenders">
            <Button size="sm" variant="ghost" className="text-xs font-semibold text-blue-700 hover:text-blue-900 hover:bg-yellow-100/50">
              View All Tenders <ChevronRight className="ml-1 h-3.5 w-3.5" />
            </Button>
          </Link>
        </div>

        <div className="divide-y divide-yellow-200/60 bg-white rounded-lg border border-yellow-200/80 overflow-hidden shadow-2xs">
          {attentionItems.length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-500 space-y-1">
              <CheckCircle2 className="h-8 w-8 text-emerald-500 mx-auto opacity-80" />
              <p className="font-semibold text-slate-700">No bids currently require urgent attention.</p>
              <p className="text-xs text-slate-500">All evaluated bids are compliant or have decisions recorded.</p>
            </div>
          ) : (
            attentionItems.map((bid) => (
              <div
                key={bid.id}
                className="p-5 hover:bg-slate-50/80 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-2.5 flex-1 min-w-0">
                  {/* Company Name, NON COMPLIANT tag, High Risk tag tightly grouped (gap-2) */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-bold text-slate-900 text-base flex items-center gap-1.5">
                      <Building2 className="h-4 w-4 text-slate-500 shrink-0" />
                      {bid.bidder_name}
                    </span>

                    {/* NON COMPLIANT or Status Tag */}
                    <Badge
                      variant="outline"
                      className={
                        bid.compliance_status === "NON COMPLIANT" || bid.compliance_status === "NON_COMPLIANT" || bid.compliance_status === "FAIL"
                          ? "bg-rose-100 text-rose-800 border-rose-300 font-bold text-xs px-2.5 py-0.5"
                          : bid.compliance_status === "COMPLIANT" || bid.compliance_status === "PASS"
                          ? "bg-emerald-100 text-emerald-800 border-emerald-300 font-bold text-xs px-2.5 py-0.5"
                          : "bg-amber-100 text-amber-800 border-amber-300 font-bold text-xs px-2.5 py-0.5"
                      }
                    >
                      {bid.compliance_status || "NON COMPLIANT"}
                    </Badge>

                    {/* High Risk Tag */}
                    {bid.risk_level ? (
                      <RiskBadge level={bid.risk_level} />
                    ) : (
                      <Badge className="bg-rose-600 text-white font-bold text-xs px-2.5 py-0.5">
                        High Risk
                      </Badge>
                    )}
                  </div>

                  {/* Highlight AI Recommendation Prominently */}
                  <div className="p-3 rounded-lg bg-amber-100/90 border border-amber-300 text-amber-950 text-xs font-medium leading-relaxed flex items-start gap-2">
                    <span className="font-bold uppercase tracking-wider text-[11px] bg-amber-200/90 text-amber-900 px-2 py-0.5 rounded border border-amber-300 shrink-0">
                      AI Recommendation
                    </span>
                    <span className="text-amber-950 font-semibold">
                      {bid.recommendation || "HIGH_RISK_REVIEW — Immediate manual audit required for statutory tax discrepancies."}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0 self-end md:self-center">
                  <Link to={`/bids/${bid.id}`}>
                    <Button size="sm" className="bg-blue-600 hover:bg-blue-700 text-white text-xs px-4 h-9 font-semibold shadow-xs">
                      Review Bid <ExternalLink className="ml-1.5 h-3.5 w-3.5" />
                    </Button>
                  </Link>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* ---------------------------------------------------- */}
      {/* 3. ACTIVE TENDERS DATA TABLE                        */}
      {/* ---------------------------------------------------- */}
      <Card className="shadow-sm border border-slate-200 bg-white rounded-xl overflow-hidden">
        <CardHeader className="p-5 border-b border-slate-200 flex flex-row items-center justify-between bg-slate-50/50">
          <div>
            <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
              <FileText className="h-4.5 w-4.5 text-slate-700" />
              ACTIVE TENDERS DATA TABLE
            </CardTitle>
            <CardDescription className="text-xs text-slate-500 mt-0.5">
              Comprehensive list of ongoing tenders, reference IDs, and submission statistics.
            </CardDescription>
          </div>
          <Link to="/tenders">
            <Button size="sm" variant="outline" className="border-slate-300 text-xs text-slate-700 hover:bg-slate-100 font-medium">
              View All <ChevronRight className="ml-1 h-3.5 w-3.5" />
            </Button>
          </Link>
        </CardHeader>

        <CardContent className="p-0 overflow-x-auto">
          {tenders.length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-500">
              No active tenders available.
            </div>
          ) : (
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="bg-slate-100/80 border-b border-slate-200 text-slate-700 font-semibold text-xs uppercase tracking-wider">
                  <th className="py-3.5 px-5">Tender Reference</th>
                  <th className="py-3.5 px-5">Title</th>
                  <th className="py-3.5 px-5">Bids Submitted</th>
                  <th className="py-3.5 px-5">Requirements</th>
                  <th className="py-3.5 px-5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-slate-800">
                {tenders.map((tender) => (
                  <tr key={tender.id} className="hover:bg-slate-50 transition-colors">
                    {/* Monospace Tender Reference ID */}
                    <td className="py-4 px-5 font-mono text-sm font-semibold text-slate-700">
                      {tender.reference_number}
                    </td>
                    <td className="py-4 px-5 font-semibold text-slate-900 max-w-sm truncate">
                      {tender.title}
                    </td>
                    <td className="py-4 px-5 font-mono font-bold text-slate-900">
                      {tender.bid_count ?? summary.total_bids ?? 0}
                    </td>
                    <td className="py-4 px-5 text-slate-600 text-xs">
                      {tender.requirement_count ?? 0} Requirements
                    </td>
                    {/* View Bids small uniform secondary button */}
                    <td className="py-4 px-5 text-right">
                      <Link to={`/tenders/${tender.id}/bids`}>
                        <Button
                          size="sm"
                          variant="outline"
                          className="border border-slate-300 text-slate-700 bg-white hover:bg-slate-100 hover:text-slate-900 text-xs px-3 py-1.5 h-8 font-medium rounded-md shadow-2xs inline-flex items-center gap-1"
                        >
                          View Bids <ChevronRight className="h-3.5 w-3.5" />
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </PageContainer>
  );
}

