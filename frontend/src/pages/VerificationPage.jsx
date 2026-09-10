import React, { useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  ShieldCheck,
  Play,
  ArrowLeft,
  RefreshCw,
  Database,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  ShieldAlert,
  FileText,
  BadgeCheck,
  ExternalLink,
  Activity,
  FileWarning,
  AlertCircle,
  UserCheck,
  Search,
  Info,
  Server,
  Layers,
  HelpCircle,
  Building2,
  History
} from "lucide-react";
import { PageContainer } from "../components/layout/PageContainer";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "../components/ui/dialog";
import { Label } from "../components/ui/label";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { LoadingState } from "../components/shared/LoadingState";
import { ErrorState } from "../components/shared/ErrorState";
import { useBidEvaluationDashboardQuery } from "../features/dashboard/useDashboard";
import {
  useSubmissionVerificationsQuery,
  useVerificationProvidersQuery,
  useVerifyIdentifierMutation,
  useManualVerificationMutation,
  useTriggerEndToEndVerificationMutation,
  formatSourceMode,
} from "../features/verification/useVerification";

export function VerificationPage() {
  const { bidSubmissionId } = useParams();

  // Selected verification result for detailed inspection modal/drawer
  const [selectedResult, setSelectedResult] = useState(null);

  // Manual verification modal state
  const [openManualModal, setOpenManualModal] = useState(false);
  const [manualReqType, setManualReqType] = useState("GST");
  const [manualIdentifier, setManualIdentifier] = useState("");
  const [manualStatus, setManualStatus] = useState("VERIFIED");
  const [manualMessage, setManualMessage] = useState("");
  const [manualNotes, setManualNotes] = useState("");
  const [manualError, setManualError] = useState(null);

  // Fetch bid dashboard payload for context (bidder, tender, documents)
  const {
    data: dashboardData,
    isLoading: isDashboardLoading,
  } = useBidEvaluationDashboardQuery(bidSubmissionId);

  // Fetch persisted verification results for this submission
  const {
    data: results = [],
    isLoading: isResultsLoading,
    isError: isResultsError,
    error: resultsError,
    refetch: refetchResults,
  } = useSubmissionVerificationsQuery(bidSubmissionId);

  // Fetch provider capability & provenance metadata
  const {
    data: providers = [],
    isLoading: isProvidersLoading,
  } = useVerificationProvidersQuery();

  // Mutations
  const verifyMutation = useVerifyIdentifierMutation();
  const manualMutation = useManualVerificationMutation();
  const triggerAllMutation = useTriggerEndToEndVerificationMutation();

  // Single identifier check trigger handler
  const handleVerifySingle = async (item) => {
    try {
      await verifyMutation.mutateAsync({
        bid_submission_id: Number(bidSubmissionId),
        verification_type: item.verification_type || item.requirement_type,
        identifier: item.identifier,
        bid_document_id: item.bid_document_id || null,
      });
    } catch (err) {
      console.error("Single verification failed:", err);
    }
  };

  // Run all verifications trigger handler
  const handleRunAllVerifications = async () => {
    try {
      await triggerAllMutation.mutateAsync(Number(bidSubmissionId));
    } catch (err) {
      console.error("End-to-end verification trigger failed:", err);
    }
  };

  // Manual verification submit handler
  const handleManualSubmit = async (e) => {
    e.preventDefault();
    setManualError(null);

    if (!manualIdentifier.trim()) {
      setManualError("Please provide an identifier (e.g. GSTIN, PAN, or Registration No).");
      return;
    }

    try {
      await manualMutation.mutateAsync({
        bid_submission_id: Number(bidSubmissionId),
        requirement_type: manualReqType,
        identifier: manualIdentifier.trim(),
        verification_status: manualStatus,
        message: manualMessage.trim() || null,
        reference_notes: manualNotes.trim() || null,
      });
      setOpenManualModal(false);
      setManualIdentifier("");
      setManualMessage("");
      setManualNotes("");
    } catch (err) {
      const msg = err?.response?.data?.detail || "Failed to record manual verification.";
      setManualError(msg);
    }
  };

  if (isResultsLoading || isDashboardLoading) {
    return (
      <PageContainer
        title={`Statutory Verification Center (#${bidSubmissionId})`}
        description="Loading registry verification results and provider capabilities..."
      >
        <LoadingState message="Fetching statutory database verification records and provider metadata..." />
      </PageContainer>
    );
  }

  if (isResultsError) {
    return (
      <PageContainer
        title={`Statutory Verification Center (#${bidSubmissionId})`}
        description="Government Registry & Statutory Provider Connector"
        actions={
          <Link to={`/bids/${bidSubmissionId}`}>
            <Button size="sm" variant="outline">
              <ArrowLeft className="mr-1.5 h-3.5 w-3.5" /> Back to Bid Evaluation
            </Button>
          </Link>
        }
      >
        <ErrorState
          title="Unable to Load Verification Data"
          message={resultsError?.response?.data?.detail || "Failed connecting to verification service."}
          onRetry={refetchResults}
        />
      </PageContainer>
    );
  }

  const bidderName = dashboardData?.bidder?.company_name || "Bidder";
  const tenderRef = dashboardData?.tender?.reference_number || "Tender";
  const documents = dashboardData?.documents || [];

  // Summary counts using exact backend status values
  const totalCount = results.length;
  const verifiedCount = results.filter((r) => (r.status || r.verification_status) === "VERIFIED").length;
  const mismatchCount = results.filter((r) => (r.status || r.verification_status) === "MISMATCH").length;
  const notFoundCount = results.filter((r) => (r.status || r.verification_status) === "NOT_FOUND").length;
  const pendingCount = results.filter(
    (r) => (r.status || r.verification_status) === "PENDING" || (r.status || r.verification_status) === "NOT_VERIFIED"
  ).length;
  const errorCount = results.filter((r) => (r.status || r.verification_status) === "ERROR").length;

  const getStatusBadge = (statusStr) => {
    const s = (statusStr || "").toUpperCase();
    switch (s) {
      case "VERIFIED":
        return <Badge className="bg-emerald-600 text-white font-bold text-xs">VERIFIED</Badge>;
      case "MISMATCH":
        return <Badge className="bg-red-600 text-white font-bold text-xs">MISMATCH</Badge>;
      case "NOT_FOUND":
        return <Badge className="bg-amber-500 text-white font-bold text-xs">RECORD NOT FOUND</Badge>;
      case "NOT_VERIFIED":
        return <Badge className="bg-amber-500 text-white font-bold text-xs">NOT VERIFIED</Badge>;
      case "ERROR":
        return <Badge className="bg-red-600 text-white font-bold text-xs">PROVIDER ERROR</Badge>;
      case "NOT_APPLICABLE":
        return <Badge variant="outline" className="bg-slate-100 text-slate-600 border-slate-300 text-xs">NOT APPLICABLE</Badge>;
      case "PENDING":
      default:
        return <Badge variant="outline" className="bg-slate-100 text-slate-700 border-slate-300 text-xs font-mono">PENDING</Badge>;
    }
  };

  const getSourceModeBadge = (sourceMode) => {
    const info = formatSourceMode(sourceMode);
    if (info.variant === "official") {
      return <Badge className="bg-emerald-100 text-emerald-800 border-emerald-300 text-[10px] font-bold">Official Government API</Badge>;
    }
    if (info.variant === "authorized") {
      return <Badge className="bg-blue-100 text-blue-800 border-blue-300 text-[10px] font-bold">Authorized GSP Provider</Badge>;
    }
    if (info.variant === "manual") {
      return <Badge className="bg-purple-100 text-purple-800 border-purple-300 text-[10px] font-bold">Officer Manual Verification</Badge>;
    }
    // SYNTHETIC
    return (
      <Badge variant="outline" className="bg-amber-50 text-amber-800 border-amber-300 text-[10px] font-bold flex items-center gap-1">
        <Info className="h-3 w-3 text-amber-600" /> Synthetic / Test Provider
      </Badge>
    );
  };

  return (
    <PageContainer
      title={`Statutory Verification Center (#${bidSubmissionId})`}
      description={`Multi-source database verifications for ${bidderName} (Tender ${tenderRef})`}
      badge={
        <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200 text-xs font-semibold">
          {verifiedCount}/{totalCount} Checks Verified
        </Badge>
      }
      actions={
        <div className="flex items-center gap-2 flex-wrap">
          <Link to={`/bids/${bidSubmissionId}`}>
            <Button size="sm" variant="outline" className="text-xs">
              <ArrowLeft className="mr-1.5 h-3.5 w-3.5" /> Back to Bid Evaluation
            </Button>
          </Link>

          {/* Record Manual Verification Modal Dialog */}
          <Dialog open={openManualModal} onOpenChange={setOpenManualModal}>
            <DialogTrigger asChild>
              <Button size="sm" variant="outline" className="text-xs border-purple-300 text-purple-700 bg-purple-50 hover:bg-purple-100">
                <UserCheck className="mr-1.5 h-3.5 w-3.5" /> Record Manual Verification
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md bg-white p-6">
              <DialogHeader>
                <DialogTitle className="text-lg font-bold text-slate-900">Record Officer Manual Verification</DialogTitle>
                <CardDescription className="text-xs text-slate-500">
                  Record human-in-the-loop verification performed directly on government web portals.
                </CardDescription>
              </DialogHeader>

              <form onSubmit={handleManualSubmit} className="space-y-4 py-2 text-xs">
                {manualError && (
                  <div className="p-3 rounded-md bg-red-50 border border-red-200 text-red-700 flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 shrink-0 text-red-600" />
                    <span>{manualError}</span>
                  </div>
                )}

                <div className="space-y-1">
                  <Label className="text-xs font-semibold text-slate-700">Requirement / Statutory Type</Label>
                  <select
                    className="w-full text-xs p-2 border border-slate-200 rounded-md bg-white text-slate-900 focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    value={manualReqType}
                    onChange={(e) => setManualReqType(e.target.value)}
                  >
                    <option value="GST">GST Registration & Tax Compliance</option>
                    <option value="PAN">PAN & Income Tax Compliance</option>
                    <option value="UDYAM">Udyam / MSME Registration</option>
                    <option value="MCA21">MCA21 Corporate Standing & CIN</option>
                    <option value="DEBARMENT">GeM & CPSE Debarment / Blacklisting</option>
                    <option value="EPFO">EPFO Employee Provident Fund</option>
                    <option value="ESIC">ESIC Employee State Insurance</option>
                    <option value="MAKE_IN_INDIA">Make in India Local Content</option>
                    <option value="OEM_AUTHORIZATION">OEM Authorization Validity</option>
                    <option value="INCOME_TAX">Income Tax ITR Compliance</option>
                    <option value="STARTUP_INDIA">Startup India Recognition</option>
                    <option value="NSIC">NSIC Enlistment Certificate</option>
                    <option value="DIGILOCKER">DigiLocker Document Verification</option>
                    <option value="OTHER">Other Manual Verification</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <Label className="text-xs font-semibold text-slate-700">Verified Identifier (GSTIN / PAN / Registration No)</Label>
                  <Input
                    type="text"
                    required
                    placeholder="e.g. 33AAACA1234A1Z5 or UDYAM-TN-02-0012345"
                    value={manualIdentifier}
                    onChange={(e) => setManualIdentifier(e.target.value)}
                    className="text-xs font-mono"
                  />
                </div>

                <div className="space-y-1">
                  <Label className="text-xs font-semibold text-slate-700">Verification Outcome Status</Label>
                  <select
                    className="w-full text-xs p-2 border border-slate-200 rounded-md bg-white text-slate-900 focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    value={manualStatus}
                    onChange={(e) => setManualStatus(e.target.value)}
                  >
                    <option value="VERIFIED">VERIFIED — Record Confirmed Active & Valid</option>
                    <option value="NOT_VERIFIED">NOT_VERIFIED — Could Not Confirm Record</option>
                    <option value="MISMATCH">MISMATCH — Extracted Data Differs From Portal</option>
                    <option value="NOT_FOUND">NOT_FOUND — No Record Exists on Registry</option>
                    <option value="ERROR">ERROR — Portal Error / System Unavailable</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <Label className="text-xs font-semibold text-slate-700">Officer Verification Remark</Label>
                  <Input
                    type="text"
                    placeholder="e.g. Verified on official GST portal portal.gst.gov.in"
                    value={manualMessage}
                    onChange={(e) => setManualMessage(e.target.value)}
                    className="text-xs"
                  />
                </div>

                <div className="space-y-1">
                  <Label className="text-xs font-semibold text-slate-700">Reference Notes / Portal Reference ID</Label>
                  <Textarea
                    placeholder="Add portal transaction IDs, officer remarks, or reference numbers..."
                    value={manualNotes}
                    onChange={(e) => setManualNotes(e.target.value)}
                    rows={2}
                    className="text-xs"
                  />
                </div>

                <DialogFooter className="pt-3 flex items-center justify-end gap-2">
                  <Button type="button" variant="outline" onClick={() => setOpenManualModal(false)} className="text-xs">
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={manualMutation.isPending}
                    className="bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold"
                  >
                    {manualMutation.isPending ? "Recording..." : "Record Officer Verification"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>

          {/* Trigger All Verifications Pipeline */}
          <Button
            size="sm"
            onClick={handleRunAllVerifications}
            disabled={triggerAllMutation.isPending}
            className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs shadow-sm"
          >
            <Play className={`mr-1.5 h-3.5 w-3.5 ${triggerAllMutation.isPending ? "animate-spin" : ""}`} />
            {triggerAllMutation.isPending ? "Executing Pipeline..." : "Run All Statutory Verifications"}
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
        <Button size="sm" variant="default" className="bg-slate-900 text-white text-xs font-semibold">
          <ShieldCheck className="mr-1.5 h-3.5 w-3.5 text-emerald-400" /> Statutory Verifications ({totalCount})
        </Button>
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

      {/* Real Summary Metrics Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <Card className="shadow-subtle border-slate-200 bg-white">
          <CardContent className="p-3.5">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Total Checks</span>
            <span className="text-xl font-bold text-slate-900 mt-1 block">{totalCount}</span>
          </CardContent>
        </Card>
        <Card className="shadow-subtle border-slate-200 bg-white">
          <CardContent className="p-3.5">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Verified</span>
            <span className="text-xl font-bold text-emerald-600 mt-1 block">{verifiedCount}</span>
          </CardContent>
        </Card>
        <Card className="shadow-subtle border-slate-200 bg-white">
          <CardContent className="p-3.5">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Mismatches</span>
            <span className="text-xl font-bold text-red-600 mt-1 block">{mismatchCount}</span>
          </CardContent>
        </Card>
        <Card className="shadow-subtle border-slate-200 bg-white">
          <CardContent className="p-3.5">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Not Found</span>
            <span className="text-xl font-bold text-amber-600 mt-1 block">{notFoundCount}</span>
          </CardContent>
        </Card>
        <Card className="shadow-subtle border-slate-200 bg-white">
          <CardContent className="p-3.5">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Pending / Review</span>
            <span className="text-xl font-bold text-slate-600 mt-1 block">{pendingCount}</span>
          </CardContent>
        </Card>
        <Card className="shadow-subtle border-slate-200 bg-white">
          <CardContent className="p-3.5">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Provider Errors</span>
            <span className="text-xl font-bold text-red-600 mt-1 block">{errorCount}</span>
          </CardContent>
        </Card>
      </div>

      {/* Provenance Truthfulness & Disclosure Banner */}
      <div className="p-4 rounded-lg bg-amber-50/70 border border-amber-200 text-xs text-amber-950 flex items-start gap-3">
        <ShieldAlert className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <h4 className="font-bold text-amber-900">Statutory Source Provenance & Environment Disclosure</h4>
          <p className="text-[11px] leading-relaxed text-amber-900">
            Registered provider adapters operating in <strong>SYNTHETIC</strong> mode utilize development test fixtures and mock registries for system evaluation.
            They are explicitly tagged as <strong>Synthetic / Test Provider</strong> and do not represent live official government API credentials unless configured with official live access keys.
          </p>
        </div>
      </div>

      {/* Registered Provider Connectors & Source Availability Section */}
      {providers.length > 0 && (
        <Card className="shadow-subtle border-slate-200 bg-white">
          <CardHeader className="pb-3 border-b border-slate-100">
            <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Server className="h-4 w-4 text-blue-600" />
              Registered Verification Connectors & Source Capabilities ({providers.length})
            </CardTitle>
            <CardDescription className="text-xs text-slate-500">
              Operational status and access mode provenance for registered government & statutory database connectors.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 overflow-x-auto">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {providers.map((p, idx) => (
                <div key={idx} className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 space-y-2 text-xs">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-bold text-slate-900">{p.provider_name}</span>
                    {getSourceModeBadge(p.source_mode)}
                  </div>

                  <p className="text-[11px] text-slate-600 line-clamp-2">{p.description || "Registered statutory adapter."}</p>

                  <div className="flex items-center justify-between pt-1 border-t border-slate-200/60 text-[10px] text-slate-500 font-mono">
                    <span>Avail: {p.availability}</span>
                    <span>{p.is_live ? "LIVE ADAPTER" : "TEST ADAPTER"}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Verification Results Matrix Table */}
      <Card className="shadow-subtle border-slate-200 bg-white">
        <CardHeader className="pb-3 border-b border-slate-100 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Database className="h-4 w-4 text-emerald-600" />
              Statutory Verification Matrix ({results.length})
            </CardTitle>
            <CardDescription className="text-xs text-slate-500">
              Persisted results returned by registered verification provider adapters.
            </CardDescription>
          </div>
        </CardHeader>

        <CardContent className="p-0 overflow-x-auto">
          {results.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500 space-y-3">
              <Database className="h-8 w-8 text-slate-400 mx-auto" />
              <div>
                <p className="font-semibold text-slate-800">No Verification Results Available</p>
                <p className="text-[11px] text-slate-500">Statutory verifications have not been executed for this submission yet.</p>
              </div>
              <Button
                size="sm"
                onClick={handleRunAllVerifications}
                disabled={triggerAllMutation.isPending}
                className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold"
              >
                <Play className="mr-1.5 h-3.5 w-3.5" /> Execute Statutory Verifications
              </Button>
            </div>
          ) : (
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                  <th className="py-2.5 px-4">Requirement / Check</th>
                  <th className="py-2.5 px-4">Evidence Identifier</th>
                  <th className="py-2.5 px-4">Provider Source</th>
                  <th className="py-2.5 px-4">Source Mode</th>
                  <th className="py-2.5 px-4">Verification Status</th>
                  <th className="py-2.5 px-4">Checked At</th>
                  <th className="py-2.5 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                {results.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-4 font-semibold text-slate-900">
                      <div>{r.verification_type || r.requirement_type}</div>
                      {r.message && <span className="text-[10px] text-slate-500 block truncate max-w-xs">{r.message}</span>}
                    </td>
                    <td className="py-3 px-4 font-mono font-bold text-slate-900">
                      {r.identifier}
                    </td>
                    <td className="py-3 px-4 font-semibold text-slate-800">
                      {r.source || r.provider}
                    </td>
                    <td className="py-3 px-4">
                      {getSourceModeBadge(r.source_mode)}
                    </td>
                    <td className="py-3 px-4">
                      {getStatusBadge(r.status || r.verification_status)}
                    </td>
                    <td className="py-3 px-4 text-[11px] text-slate-500 font-mono">
                      {r.checked_at ? new Date(r.checked_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }) : "N/A"}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        {r.verified_data && (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => setSelectedResult(r)}
                            className="text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50 h-7 px-2"
                          >
                            <Search className="mr-1 h-3 w-3" /> Inspect Data
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleVerifySingle(r)}
                          disabled={verifyMutation.isPending}
                          className="text-[11px] h-7 px-2 border-slate-300"
                        >
                          <RefreshCw className={`h-3 w-3 ${verifyMutation.isPending ? "animate-spin" : ""}`} />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>

      {/* Modal / Dialog for Detailed Verified Data Inspection */}
      {selectedResult && (
        <Dialog open={!!selectedResult} onOpenChange={() => setSelectedResult(null)}>
          <DialogContent className="sm:max-w-lg bg-white p-6">
            <DialogHeader>
              <div className="flex items-center justify-between pr-4">
                <DialogTitle className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <Database className="h-5 w-5 text-emerald-600" />
                  Verification Record Inspector
                </DialogTitle>
                {getStatusBadge(selectedResult.status || selectedResult.verification_status)}
              </div>
              <CardDescription className="text-xs text-slate-500">
                Data payload returned by {selectedResult.source || selectedResult.provider}
              </CardDescription>
            </DialogHeader>

            <div className="space-y-4 py-2 text-xs">
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
                <div className="flex justify-between">
                  <span className="text-slate-500 font-medium">Check Type:</span>
                  <span className="font-bold text-slate-900 font-mono">{selectedResult.verification_type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-medium">Identifier:</span>
                  <span className="font-bold text-slate-900 font-mono">{selectedResult.identifier}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-medium">Source Mode Provenance:</span>
                  {getSourceModeBadge(selectedResult.source_mode)}
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-medium">Checked Timestamp:</span>
                  <span className="font-mono text-slate-700">{selectedResult.checked_at ? new Date(selectedResult.checked_at).toLocaleString() : "N/A"}</span>
                </div>
              </div>

              {/* Verified Data Fields Grid */}
              <div className="space-y-2">
                <span className="font-bold text-slate-900 block">Registry Returned Attributes:</span>
                {selectedResult.verified_data ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {Object.entries(selectedResult.verified_data).map(([key, val]) => (
                      <div key={key} className="p-2.5 rounded bg-slate-50 border border-slate-200">
                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">{key.replace(/_/g, " ")}</span>
                        <span className="text-xs font-bold text-slate-900 block font-mono truncate">{String(val)}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-500 italic">No structured data payload returned.</p>
                )}
              </div>
            </div>

            <DialogFooter className="pt-2">
              <Button onClick={() => setSelectedResult(null)} className="w-full bg-slate-900 text-white text-xs">
                Close Inspector
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </PageContainer>
  );
}
