import React from "react";
import { useParams, Link } from "react-router-dom";
import {
  Users,
  FileText,
  ShieldCheck,
  ArrowRight,
  ArrowLeft,
  Loader2,
  AlertCircle,
  FolderOpen
} from "lucide-react";
import { PageContainer } from "../components/layout/PageContainer";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { RiskBadge } from "../components/shared/RiskBadge";
import { useTenderQuery, useTenderBidsQuery, useTenderOverviewQuery } from "../features/tenders/useTenders";

export function TenderBidsPage() {
  const { tenderId } = useParams();

  const { data: tender } = useTenderQuery(tenderId);
  const { data: bids = [], isLoading: loadingBids, isError: bidsError, error: bidsErr, refetch: refetchBids } = useTenderBidsQuery(tenderId);
  const { data: overviewData } = useTenderOverviewQuery(tenderId);

  const overviewBids = overviewData?.bids || [];
  const displayBids = bids.length > 0 ? bids : overviewBids;

  return (
    <PageContainer
      title={
        tender
          ? `Bid Submissions: ${tender.reference_number || tender.reference_no || `Tender #${tenderId}`}`
          : `Bid Submissions (Tender #${tenderId})`
      }
      description="Review submitted bidder proposals, authoritative compliance scores, risk levels, and decision audits."
      badge={
        <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 text-xs">
          {displayBids.length} Submissions Received
        </Badge>
      }
      actions={
        <Link to={`/tenders/${tenderId}`}>
          <Button size="sm" variant="outline" className="text-xs">
            <ArrowLeft className="mr-1.5 h-3.5 w-3.5" /> Back to Tender
          </Button>
        </Link>
      }
    >
      {/* Loading State */}
      {loadingBids && (
        <div className="p-12 text-center bg-white rounded-lg border border-slate-200">
          <Loader2 className="h-7 w-7 text-blue-600 animate-spin mx-auto mb-2" />
          <p className="text-xs font-semibold text-slate-700">Loading bid submissions from server...</p>
        </div>
      )}

      {/* Error State */}
      {bidsError && (
        <div className="p-6 bg-red-50 rounded-lg border border-red-200 text-center space-y-3">
          <AlertCircle className="h-8 w-8 text-red-600 mx-auto" />
          <div>
            <h3 className="text-sm font-bold text-red-900">Failed to Load Submissions</h3>
            <p className="text-xs text-red-700 mt-1">
              {bidsErr?.response?.data?.detail || bidsErr?.message || "Could not retrieve bid submissions."}
            </p>
          </div>
          <Button size="sm" variant="outline" onClick={() => refetchBids()} className="text-xs border-red-300 text-red-800">
            Retry Loading
          </Button>
        </div>
      )}

      {/* Empty State */}
      {!loadingBids && !bidsError && displayBids.length === 0 && (
        <div className="p-12 text-center bg-white rounded-lg border border-slate-200 space-y-3">
          <FolderOpen className="h-10 w-10 text-slate-300 mx-auto" />
          <h3 className="text-sm font-bold text-slate-800">No Submissions Received</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            No bidder submissions have been recorded for this tender yet.
          </p>
        </div>
      )}

      {/* Bid Submissions List */}
      {!loadingBids && !bidsError && displayBids.length > 0 && (
        <div className="space-y-4">
          {displayBids.map((bidItem) => {
            const bid = bidItem.bid_submission || bidItem;
            const bidderObj = bidItem.bidder || bid.bidder || {};
            const assessment = bidItem.compliance_assessment || bid.compliance_assessment || {};
            const decision = bidItem.procurement_decision || bid.procurement_decision || {};

            const bidderName = bidderObj.company_name || bidderObj.legal_name || bid.bidder_name || "Bidder Entity";
            const gstin = bidderObj.gstin || bid.gstin;
            const pan = bidderObj.pan || bid.pan;

            const score = assessment.score !== undefined ? assessment.score : bid.compliance_score;
            const riskLevel = assessment.risk_level || bid.risk_level || "MEDIUM";
            const statusStr = decision.decision || assessment.status || bid.status || "SUBMITTED";

            return (
              <Card key={bid.id} className="shadow-subtle border-slate-200 hover:border-slate-300 transition-all">
                <CardContent className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-2 min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="text-base font-bold text-slate-900 truncate">{bidderName}</h3>
                      <RiskBadge riskLevel={riskLevel} />
                      <Badge variant="outline" className="bg-slate-100 text-slate-700 text-[10px]">
                        {statusStr}
                      </Badge>
                    </div>

                    <div className="flex items-center gap-4 text-xs text-slate-600 flex-wrap">
                      {gstin && (
                        <span>
                          GSTIN: <strong className="font-mono text-slate-900">{gstin}</strong>
                        </span>
                      )}
                      {pan && (
                        <span>
                          PAN: <strong className="font-mono text-slate-900">{pan}</strong>
                        </span>
                      )}
                      <span>
                        Submission ID: <strong className="font-mono text-slate-900">#{bid.id}</strong>
                      </span>
                      {bid.submitted_at && (
                        <span>Submitted: {new Date(bid.submitted_at).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>

                  {/* Compliance Score & Action Links */}
                  <div className="flex items-center gap-4 shrink-0 border-t md:border-t-0 md:border-l border-slate-100 pt-3 md:pt-0 md:pl-4 justify-between md:justify-end">
                    {score != null && (
                      <div className="text-right">
                        <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                          Compliance Score
                        </span>
                        <span className="text-xl font-black text-emerald-600">
                          {Number(score).toFixed(1)}%
                        </span>
                      </div>
                    )}

                    <div className="flex items-center gap-2">
                      <Link to={`/bids/${bid.id}/documents`}>
                        <Button size="sm" variant="outline" className="text-xs">
                          <FileText className="mr-1 h-3.5 w-3.5" /> Docs
                        </Button>
                      </Link>
                      <Link to={`/bids/${bid.id}/verification`}>
                        <Button size="sm" variant="outline" className="text-xs">
                          <ShieldCheck className="mr-1 h-3.5 w-3.5 text-blue-600" /> Portals
                        </Button>
                      </Link>
                      <Link to={`/bids/${bid.id}/compliance`}>
                        <Button size="sm" className="bg-slate-900 hover:bg-slate-800 text-xs px-3">
                          Review & Audit <ArrowRight className="ml-1 h-3.5 w-3.5" />
                        </Button>
                      </Link>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </PageContainer>
  );
}
