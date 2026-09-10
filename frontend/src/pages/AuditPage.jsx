import React, { useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  History,
  ArrowLeft,
  Activity,
  FileText,
  ShieldCheck,
  BadgeCheck,
  ChevronDown,
  ChevronRight,
  Filter,
  User,
  Cpu,
  Clock,
  Database,
  Search,
  RefreshCw,
  AlertCircle,
} from "lucide-react";
import { PageContainer } from "../components/layout/PageContainer";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { LoadingState } from "../components/shared/LoadingState";
import { ErrorState } from "../components/shared/ErrorState";
import { useBidEvaluationDashboardQuery } from "../features/dashboard/useDashboard";
import {
  useBidSubmissionAuditLogsQuery,
  useAuditLogsQuery,
} from "../features/audit/useAudit";

export function AuditPage() {
  const { bidSubmissionId } = useParams();

  // Pagination state
  const [page, setPage] = useState(0);
  const limit = 20;
  const offset = page * limit;

  // Filter state
  const [actionFilter, setActionFilter] = useState("ALL");
  const [entityFilter, setEntityFilter] = useState("ALL");

  // Expandable JSON viewer state
  const [expandedItems, setExpandedItems] = useState({});

  const toggleExpand = (id) => {
    setExpandedItems((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  // Fetch optional bid dashboard context if bidSubmissionId exists
  const { data: dashboardData, isLoading: isDashboardLoading } =
    useBidEvaluationDashboardQuery(bidSubmissionId);

  // Fetch audit logs (either bid-specific or global)
  const isBidScope = !!bidSubmissionId;

  const bidAuditQuery = useBidSubmissionAuditLogsQuery(bidSubmissionId, {
    limit,
    offset,
  });

  const globalParams = {
    limit,
    offset,
    ...(actionFilter !== "ALL" ? { action: actionFilter } : {}),
    ...(entityFilter !== "ALL" ? { entityType: entityFilter } : {}),
  };

  const globalAuditQuery = useAuditLogsQuery(globalParams);

  const activeQuery = isBidScope ? bidAuditQuery : globalAuditQuery;
  const { data: auditData, isLoading, isError, error, refetch } = activeQuery;

  if (isLoading || (isBidScope && isDashboardLoading)) {
    return (
      <PageContainer
        title={
          isBidScope
            ? `Audit Trail Workspace (#${bidSubmissionId})`
            : "System Audit Logs"
        }
        description="Loading immutable system audit logs and change history..."
      >
        <LoadingState message="Fetching chronological audit log records..." />
      </PageContainer>
    );
  }

  if (isError) {
    return (
      <PageContainer
        title={
          isBidScope
            ? `Audit Trail Workspace (#${bidSubmissionId})`
            : "System Audit Logs"
        }
        description="Immutable System Audit Trail"
        actions={
          isBidScope ? (
            <Link to={`/bids/${bidSubmissionId}`}>
              <Button size="sm" variant="outline">
                <ArrowLeft className="mr-1.5 h-3.5 w-3.5" /> Back to Bid Evaluation
              </Button>
            </Link>
          ) : null
        }
      >
        <ErrorState
          title="Failed to Load Audit Trail"
          message={
            error?.response?.data?.detail ||
            error?.message ||
            "Could not retrieve audit logs."
          }
          onRetry={refetch}
        />
      </PageContainer>
    );
  }

  const bidderName = dashboardData?.bidder?.company_name || "Bidder";
  const tenderRef = dashboardData?.tender?.reference_number || "Tender";
  const documents = dashboardData?.documents || [];
  const verifications = dashboardData?.verification || [];

  const rawLogs = auditData?.items || [];
  const totalCount = auditData?.total || 0;
  const totalPages = Math.ceil(totalCount / limit) || 1;

  // Filter logs locally if in bid scope
  const filteredLogs = rawLogs.filter((log) => {
    if (actionFilter !== "ALL" && log.action !== actionFilter) return false;
    if (entityFilter !== "ALL" && log.entity_type !== entityFilter) return false;
    return true;
  });

  const getActionBadge = (actionStr) => {
    const act = (actionStr || "").toUpperCase();
    if (act.includes("DECISION") || act.includes("QUALIFIED") || act.includes("DISQUALIFIED")) {
      return <Badge className="bg-purple-700 text-white font-bold text-[10px]">{actionStr}</Badge>;
    }
    if (act.includes("RECOMMENDATION") || act.includes("AI")) {
      return <Badge className="bg-indigo-600 text-white font-bold text-[10px]">{actionStr}</Badge>;
    }
    if (act.includes("COMPLIANCE") || act.includes("ASSESS")) {
      return <Badge className="bg-blue-600 text-white font-bold text-[10px]">{actionStr}</Badge>;
    }
    if (act.includes("VERIF") || act.includes("PORTAL")) {
      return <Badge className="bg-emerald-600 text-white font-bold text-[10px]">{actionStr}</Badge>;
    }
    if (act.includes("DISCREPANCY") || act.includes("RESOLV") || act.includes("WAIV")) {
      return <Badge className="bg-amber-600 text-white font-bold text-[10px]">{actionStr}</Badge>;
    }
    if (act.includes("DOCUMENT") || act.includes("UPLOAD") || act.includes("EXTRACT")) {
      return <Badge className="bg-slate-700 text-white font-bold text-[10px]">{actionStr}</Badge>;
    }
    return <Badge variant="outline" className="bg-slate-100 text-slate-700 border-slate-300 text-[10px]">{actionStr}</Badge>;
  };

  return (
    <PageContainer
      title={
        isBidScope
          ? `Audit Trail Workspace (#${bidSubmissionId})`
          : "System Audit Logs"
      }
      description={
        isBidScope
          ? `Authoritative, immutable event log trail for ${bidderName} (Tender ${tenderRef})`
          : "System-wide activity audit records logged by BidSure AI backend"
      }
      badge={
        <Badge variant="outline" className="bg-slate-100 text-slate-700 border-slate-300 text-xs font-semibold">
          Total Logged Events: {totalCount}
        </Badge>
      }
      actions={
        isBidScope ? (
          <div className="flex items-center gap-2 flex-wrap">
            <Link to={`/bids/${bidSubmissionId}`}>
              <Button size="sm" variant="outline" className="text-xs">
                <ArrowLeft className="mr-1.5 h-3.5 w-3.5" /> Back to Bid Evaluation
              </Button>
            </Link>
            <Button size="sm" variant="ghost" onClick={() => refetch()} className="text-xs">
              <RefreshCw className="mr-1.5 h-3.5 w-3.5" /> Refresh Trail
            </Button>
          </div>
        ) : null
      }
    >
      {/* Bid Workspace Sub-Navigation (if within bid scope) */}
      {isBidScope && (
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
          <Link to={`/bids/${bidSubmissionId}/compliance`}>
            <Button size="sm" variant="outline" className="text-xs text-slate-700 hover:bg-slate-100">
              <BadgeCheck className="mr-1.5 h-3.5 w-3.5 text-purple-600" /> Compliance & Decision
            </Button>
          </Link>
          <Button size="sm" variant="default" className="bg-slate-900 text-white text-xs font-semibold">
            <History className="mr-1.5 h-3.5 w-3.5 text-slate-300" /> Audit Trail
          </Button>
        </div>
      )}

      {/* Filter & Controls Bar */}
      <Card className="shadow-subtle border-slate-200 bg-white">
        <CardContent className="p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-2 flex-wrap text-xs">
            <Filter className="h-4 w-4 text-slate-500" />
            <span className="font-semibold text-slate-700">Filter Trail:</span>

            {/* Filter by Action */}
            <div className="flex items-center gap-1.5">
              <label className="text-[11px] text-slate-500">Action:</label>
              <select
                value={actionFilter}
                onChange={(e) => {
                  setActionFilter(e.target.value);
                  setPage(0);
                }}
                className="bg-slate-50 border border-slate-300 rounded px-2.5 py-1 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-400"
              >
                <option value="ALL">All Actions</option>
                <option value="PROCUREMENT_DECISION_RECORDED">Procurement Decision Recorded</option>
                <option value="AI_RECOMMENDATION_GENERATED">AI Recommendation Generated</option>
                <option value="COMPLIANCE_ASSESSMENT_EXECUTED">Compliance Assessment Executed</option>
                <option value="STATUTORY_VERIFICATION_EXECUTED">Statutory Verification Executed</option>
                <option value="DISCREPANCY_STATUS_UPDATED">Discrepancy Status Updated</option>
              </select>
            </div>

            {/* Filter by Entity */}
            <div className="flex items-center gap-1.5 ml-2">
              <label className="text-[11px] text-slate-500">Entity:</label>
              <select
                value={entityFilter}
                onChange={(e) => {
                  setEntityFilter(e.target.value);
                  setPage(0);
                }}
                className="bg-slate-50 border border-slate-300 rounded px-2.5 py-1 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-400"
              >
                <option value="ALL">All Entities</option>
                <option value="BID_SUBMISSION">Bid Submission</option>
                <option value="PROCUREMENT_DECISION">Procurement Decision</option>
                <option value="COMPLIANCE_ASSESSMENT">Compliance Assessment</option>
                <option value="DISCREPANCY">Discrepancy</option>
                <option value="DOCUMENT">Document</option>
              </select>
            </div>
          </div>

          <div className="text-xs text-slate-500 font-mono">
            Showing {filteredLogs.length} of {totalCount} records
          </div>
        </CardContent>
      </Card>

      {/* Chronological Audit Timeline */}
      <Card className="shadow-subtle border-slate-200 bg-white">
        <CardHeader className="pb-3 border-b border-slate-100">
          <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <History className="h-4 w-4 text-slate-800" />
            Immutable Audit Trail Events ({filteredLogs.length})
          </CardTitle>
          <CardDescription className="text-xs text-slate-500">
            Backend-controlled audit records logged in compliance with public procurement accountability standards.
          </CardDescription>
        </CardHeader>

        <CardContent className="p-0 divide-y divide-slate-100 text-xs">
          {filteredLogs.length === 0 ? (
            <div className="p-8 text-center text-slate-500 space-y-2">
              <AlertCircle className="h-8 w-8 text-slate-400 mx-auto" />
              <p className="font-semibold text-slate-800">No audit log entries recorded for this filter selection.</p>
              <p className="text-[11px] text-slate-500">Audit logs are automatically generated as procurement evaluation events occur.</p>
            </div>
          ) : (
            filteredLogs.map((log) => {
              const isExpanded = !!expandedItems[log.id];
              const actorText = log.user_id ? `User #${log.user_id}` : "System / Rule Engine";
              const formattedTime = log.created_at
                ? new Date(log.created_at).toLocaleString("en-IN", {
                    dateStyle: "medium",
                    timeStyle: "medium",
                  })
                : "N/A";

              const hasSnapshots = !!(log.old_value || log.new_value || log.details);

              return (
                <div key={log.id} className="p-4 hover:bg-slate-50/60 transition-colors space-y-3">
                  <div className="flex items-start justify-between gap-4 flex-wrap sm:flex-nowrap">
                    <div className="space-y-1.5 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        {getActionBadge(log.action)}
                        <Badge variant="outline" className="bg-slate-50 text-slate-600 border-slate-200 text-[10px] font-mono">
                          {log.entity_type} {log.entity_id ? `#${log.entity_id}` : ""}
                        </Badge>
                      </div>

                      <div className="flex items-center gap-4 text-[11px] text-slate-500 flex-wrap pt-0.5">
                        <span className="flex items-center gap-1">
                          <User className="h-3 w-3 text-slate-400" />
                          Actor: <strong className="text-slate-800">{actorText}</strong>
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3 text-slate-400" />
                          Timestamp: <strong className="text-slate-800">{formattedTime}</strong>
                        </span>
                        {log.ip_address && (
                          <span className="flex items-center gap-1 font-mono text-[10px] text-slate-400">
                            IP: {log.ip_address}
                          </span>
                        )}
                      </div>
                    </div>

                    {hasSnapshots && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => toggleExpand(log.id)}
                        className="text-[11px] border-slate-200 text-slate-700 hover:bg-slate-100 h-7 shrink-0"
                      >
                        {isExpanded ? (
                          <>
                            <ChevronDown className="mr-1 h-3 w-3" /> Hide Snapshots
                          </>
                        ) : (
                          <>
                            <ChevronRight className="mr-1 h-3 w-3" /> View Snapshots
                          </>
                        )}
                      </Button>
                    )}
                  </div>

                  {/* Expandable Old / New State & Context Details */}
                  {isExpanded && hasSnapshots && (
                    <div className="mt-3 p-3.5 rounded-lg bg-slate-900 text-slate-100 font-mono text-[11px] space-y-3 border border-slate-700">
                      {log.details && (
                        <div>
                          <span className="text-purple-300 font-bold text-[10px] uppercase block tracking-wider mb-1">
                            Event Description & Details:
                          </span>
                          <pre className="whitespace-pre-wrap text-slate-300 font-sans text-xs bg-slate-800/80 p-2.5 rounded border border-slate-700">
                            {typeof log.details === "object" ? JSON.stringify(log.details, null, 2) : log.details}
                          </pre>
                        </div>
                      )}

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                        {log.old_value && (
                          <div className="bg-slate-800/90 p-2.5 rounded border border-slate-700 space-y-1">
                            <span className="text-amber-400 font-bold text-[10px] uppercase block tracking-wider">
                              Previous State (Before):
                            </span>
                            <pre className="whitespace-pre-wrap text-slate-300 text-[10px] overflow-x-auto max-h-48">
                              {JSON.stringify(log.old_value, null, 2)}
                            </pre>
                          </div>
                        )}

                        {log.new_value && (
                          <div className="bg-slate-800/90 p-2.5 rounded border border-slate-700 space-y-1">
                            <span className="text-emerald-400 font-bold text-[10px] uppercase block tracking-wider">
                              New State (After):
                            </span>
                            <pre className="whitespace-pre-wrap text-slate-300 text-[10px] overflow-x-auto max-h-48">
                              {JSON.stringify(log.new_value, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </CardContent>
      </Card>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-2 text-xs">
          <Button
            size="sm"
            variant="outline"
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="text-xs"
          >
            Previous Page
          </Button>

          <span className="text-slate-600 font-medium">
            Page {page + 1} of {totalPages}
          </span>

          <Button
            size="sm"
            variant="outline"
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            className="text-xs"
          >
            Next Page
          </Button>
        </div>
      )}
    </PageContainer>
  );
}
