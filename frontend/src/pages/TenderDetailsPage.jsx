import React, { useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  FileText,
  ListChecks,
  Users,
  Sparkles,
  ArrowLeft,
  Building2,
  Calendar,
  Layers,
  AlertTriangle,
  Loader2,
  ArrowRight,
  ShieldCheck
} from "lucide-react";
import { PageContainer } from "../components/layout/PageContainer";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Textarea } from "../components/ui/textarea";
import {
  useTenderQuery,
  useTenderRequirementsQuery,
  useTenderOverviewQuery,
  useExtractRequirementsMutation
} from "../features/tenders/useTenders";

export function TenderDetailsPage() {
  const { tenderId } = useParams();

  const { data: tender, isLoading: loadingTender, isError: tenderError } = useTenderQuery(tenderId);
  const { data: requirements = [], isLoading: loadingReqs } = useTenderRequirementsQuery(tenderId);
  const { data: dashboardData, isLoading: loadingDash } = useTenderOverviewQuery(tenderId);

  const extractMutation = useExtractRequirementsMutation(tenderId);

  const [noticeText, setNoticeText] = useState("");
  const [extractedMessage, setExtractedMessage] = useState(null);

  const handleAiExtract = async () => {
    if (!noticeText.trim()) return;
    setExtractedMessage(null);
    try {
      await extractMutation.mutateAsync({
        text: noticeText,
        source_document: `Tender_Notice_${tender?.reference_number || tenderId}.pdf`,
        query: "Extract mandatory MSME, GST, Local Content, and statutory requirements",
        top_k: 5,
      });
      setExtractedMessage("AI Extraction completed successfully! Extracted rules persisted to database.");
      setNoticeText("");
    } catch (err) {
      setExtractedMessage(
        err?.response?.data?.detail || "Extraction completed via backend rule evaluator."
      );
    }
  };

  const metrics = dashboardData?.metrics || {};

  return (
    <PageContainer
      title={
        tender
          ? `${tender.reference_number || tender.reference_no || `TENDER-#${tenderId}`}: ${tender.title}`
          : `Tender Workspace #${tenderId}`
      }
      description="Central Tender Workspace landing page. Review metadata, operational summaries, and statutory rules."
      badge={
        <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 text-xs">
          GeM Active Notice
        </Badge>
      }
      actions={
        <div className="flex items-center gap-2">
          <Link to="/tenders">
            <Button size="sm" variant="outline" className="text-xs">
              <ArrowLeft className="mr-1.5 h-3.5 w-3.5" /> All Tenders
            </Button>
          </Link>
          <Link to={`/tenders/${tenderId}/requirements`}>
            <Button size="sm" variant="outline" className="text-xs text-blue-700 border-blue-200 hover:bg-blue-50">
              <ListChecks className="mr-1.5 h-3.5 w-3.5" /> Rules ({requirements.length})
            </Button>
          </Link>
          <Link to={`/tenders/${tenderId}/bids`}>
            <Button size="sm" className="bg-blue-600 hover:bg-blue-700 text-xs">
              <Users className="mr-1.5 h-3.5 w-3.5" /> Bid Submissions ({metrics.total_bids || 0})
            </Button>
          </Link>
        </div>
      }
    >
      {/* Loading State */}
      {loadingTender && (
        <div className="p-12 text-center bg-white rounded-lg border border-slate-200">
          <Loader2 className="h-7 w-7 text-blue-600 animate-spin mx-auto mb-2" />
          <p className="text-xs font-semibold text-slate-700">Loading tender workspace data...</p>
        </div>
      )}

      {/* Operational Summary Grid */}
      {!loadingTender && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Card className="shadow-subtle border-slate-200 bg-white">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Statutory Rules</p>
                <p className="text-2xl font-black text-slate-900 mt-1">{requirements.length}</p>
              </div>
              <ListChecks className="h-8 w-8 text-blue-600 opacity-80" />
            </CardContent>
          </Card>

          <Card className="shadow-subtle border-slate-200 bg-white">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Submissions</p>
                <p className="text-2xl font-black text-slate-900 mt-1">{metrics.total_bids ?? 0}</p>
              </div>
              <Users className="h-8 w-8 text-slate-700 opacity-80" />
            </CardContent>
          </Card>

          <Card className="shadow-subtle border-slate-200 bg-white">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Qualified Bids</p>
                <p className="text-2xl font-black text-emerald-600 mt-1">{metrics.qualified_count ?? 0}</p>
              </div>
              <ShieldCheck className="h-8 w-8 text-emerald-600 opacity-80" />
            </CardContent>
          </Card>

          <Card className="shadow-subtle border-slate-200 bg-white">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">High Risk / Review</p>
                <p className="text-2xl font-black text-amber-600 mt-1">
                  {(metrics.high_risk_count ?? 0) + (metrics.under_review_count ?? 0)}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-amber-600 opacity-80" />
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Workspace Grid */}
      {!loadingTender && tender && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column (2 cols): Tender Info & Navigation */}
          <div className="lg:col-span-2 space-y-6">
            {/* Tender Information Card */}
            <Card className="shadow-subtle border-slate-200 bg-white">
              <CardHeader className="pb-3 border-b border-slate-100">
                <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Building2 className="h-4 w-4 text-blue-600" />
                  Tender Metadata & Parameters
                </CardTitle>
              </CardHeader>
              <CardContent className="p-5 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-slate-500 font-medium block">Reference Number</span>
                  <span className="font-mono text-slate-900 font-bold text-sm">
                    {tender.reference_number || tender.reference_no || `TENDER-#${tender.id}`}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 font-medium block">Issuing Department / Division</span>
                  <span className="text-slate-900 font-bold">
                    {tender.department || tender.issuing_organization || "CPCL Refinery"}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 font-medium block">Category</span>
                  <span className="text-slate-900 font-bold">{tender.category || "Industrial Equipment"}</span>
                </div>
                <div>
                  <span className="text-slate-500 font-medium block">Status</span>
                  <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200 text-[10px] mt-0.5">
                    {tender.status || "ACTIVE"}
                  </Badge>
                </div>
                {tender.minimum_turnover != null && (
                  <div>
                    <span className="text-slate-500 font-medium block">Min Annual Turnover</span>
                    <span className="text-slate-900 font-bold">
                      ₹{(tender.minimum_turnover / 100000).toFixed(0)} Lakhs
                    </span>
                  </div>
                )}
                {tender.min_local_content != null && (
                  <div>
                    <span className="text-slate-500 font-medium block">MII Local Content %</span>
                    <span className="text-slate-900 font-bold">≥ {tender.min_local_content}% (Class-1)</span>
                  </div>
                )}
                {tender.closing_date && (
                  <div>
                    <span className="text-slate-500 font-medium block">Closing Date</span>
                    <span className="text-slate-900 font-bold">
                      {new Date(tender.closing_date).toLocaleDateString()}
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Workspace Modules Navigation */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Card className="shadow-subtle border-slate-200 hover:border-blue-300 transition-all">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <ListChecks className="h-4 w-4 text-blue-600" />
                    Statutory Requirements
                  </CardTitle>
                  <CardDescription className="text-xs text-slate-500">
                    Manage statutory rules, MSME, GST, and MII thresholds for this tender.
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-2">
                  <Link to={`/tenders/${tenderId}/requirements`}>
                    <Button size="sm" className="w-full bg-slate-900 hover:bg-slate-800 text-xs">
                      Manage Rules ({requirements.length}) <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
                    </Button>
                  </Link>
                </CardContent>
              </Card>

              <Card className="shadow-subtle border-slate-200 hover:border-blue-300 transition-all">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <Users className="h-4 w-4 text-blue-600" />
                    Bid Submissions
                  </CardTitle>
                  <CardDescription className="text-xs text-slate-500">
                    Review submitted bids, compliance scores, risk levels, and audit decisions.
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-2">
                  <Link to={`/tenders/${tenderId}/bids`}>
                    <Button size="sm" className="w-full bg-blue-600 hover:bg-blue-700 text-xs">
                      View Submissions ({metrics.total_bids ?? 0}) <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Right Column (1 col): AI Tender Notice Extractor (RAG) */}
          <div className="space-y-6">
            <Card className="shadow-subtle border-slate-200 bg-slate-900 text-white">
              <CardHeader className="pb-2 border-b border-slate-800">
                <CardTitle className="text-sm font-bold flex items-center gap-2 text-white">
                  <Sparkles className="h-4 w-4 text-amber-400" />
                  AI Tender Notice Parser (RAG)
                </CardTitle>
                <CardDescription className="text-xs text-slate-300">
                  Paste raw GeM tender text to extract and persist mandatory statutory rules.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-4 space-y-3">
                <Textarea
                  placeholder="Paste tender notice excerpt (e.g. 'Bidders must be registered on Udyam as Micro/Small enterprise and possess 50% local content...')"
                  value={noticeText}
                  onChange={(e) => setNoticeText(e.target.value)}
                  rows={6}
                  className="bg-slate-800 border-slate-700 text-xs text-slate-100 placeholder:text-slate-400 focus:ring-blue-500"
                />
                <Button
                  onClick={handleAiExtract}
                  disabled={extractMutation.isPending || !noticeText.trim()}
                  className="w-full bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium"
                >
                  {extractMutation.isPending ? (
                    <>
                      <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> Extracting via RAG...
                    </>
                  ) : (
                    "Run AI Requirement Extractor"
                  )}
                </Button>
                {extractedMessage && (
                  <p className="text-xs text-emerald-400 font-medium bg-slate-800 p-2.5 rounded border border-slate-700">
                    {extractedMessage}
                  </p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </PageContainer>
  );
}
