import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  FileText,
  Upload,
  Cpu,
  CheckCircle2,
  ArrowLeft,
  Eye,
  RefreshCw,
  AlertTriangle,
  FileWarning,
  ShieldCheck,
  BadgeCheck,
  History,
  ExternalLink,
  Activity,
  Clock,
  Sparkles,
  Database,
  AlertCircle
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
import { LoadingState } from "../components/shared/LoadingState";
import { ErrorState } from "../components/shared/ErrorState";
import { useBidEvaluationDashboardQuery } from "../features/dashboard/useDashboard";
import {
  useBidDocumentsQuery,
  useDocumentExtractionQuery,
  useUploadDocumentMutation,
  useProcessDocumentMutation,
  parseExtractedFields,
} from "../features/documents/useDocuments";

export function DocumentsPage() {
  const { bidSubmissionId } = useParams();

  // Selected document state for detailed extraction inspection
  const [selectedDocId, setSelectedDocId] = useState(null);

  // Upload modal state
  const [openUploadModal, setOpenUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [documentType, setDocumentType] = useState("GST_CERTIFICATE");
  const [uploadError, setUploadError] = useState(null);

  // Fetch bid dashboard payload for context (tender, bidder, discrepancies)
  const {
    data: dashboardData,
    isLoading: isDashboardLoading,
  } = useBidEvaluationDashboardQuery(bidSubmissionId);

  // Fetch list of documents submitted for this bid
  const {
    data: documents = [],
    isLoading: isDocsLoading,
    isError: isDocsError,
    error: docsError,
    refetch: refetchDocs,
  } = useBidDocumentsQuery(bidSubmissionId);

  // Auto-select first document when list loads if none selected
  useEffect(() => {
    if (documents.length > 0 && !selectedDocId) {
      setSelectedDocId(documents[0].id);
    }
  }, [documents, selectedDocId]);

  // Selected document object
  const selectedDoc = documents.find((d) => d.id === selectedDocId) || documents[0] || null;

  // Fetch latest extraction for the selected document
  const {
    data: extraction,
    isLoading: isExtractionLoading,
    isError: isExtractionError,
    refetch: refetchExtraction,
  } = useDocumentExtractionQuery(selectedDoc?.id);

  // Mutations
  const uploadMutation = useUploadDocumentMutation();
  const processMutation = useProcessDocumentMutation();

  // Handlers
  const handleSelectDoc = (doc) => {
    setSelectedDocId(doc.id);
  };

  const handleRunProcess = async (docId) => {
    try {
      await processMutation.mutateAsync(docId);
    } catch (err) {
      console.error("Document processing error:", err);
    }
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    setUploadError(null);

    if (!uploadFile) {
      setUploadError("Please select a file to upload.");
      return;
    }

    // Client-side file size check (10MB limit)
    const MAX_SIZE = 10 * 1024 * 1024;
    if (uploadFile.size > MAX_SIZE) {
      setUploadError("File size exceeds maximum limit of 10MB.");
      return;
    }

    const formData = new FormData();
    formData.append("file", uploadFile);
    formData.append("document_type", documentType);

    try {
      const uploadedDoc = await uploadMutation.mutateAsync({
        bidSubmissionId,
        formData,
      });
      setOpenUploadModal(false);
      setUploadFile(null);
      if (uploadedDoc && uploadedDoc.id) {
        setSelectedDocId(uploadedDoc.id);
      }
    } catch (err) {
      const msg = err?.response?.data?.detail || "Upload failed. Please check backend validation and file type.";
      setUploadError(msg);
    }
  };

  if (isDocsLoading || isDashboardLoading) {
    return (
      <PageContainer
        title={`Document Vault (#${bidSubmissionId})`}
        description="Loading submitted bid documents and OCR extraction records..."
      >
        <LoadingState message="Fetching document vault data and AI extraction outputs..." />
      </PageContainer>
    );
  }

  if (isDocsError) {
    return (
      <PageContainer
        title={`Document Vault (#${bidSubmissionId})`}
        description="Submitted Document Intelligence Repository"
        actions={
          <Link to={`/bids/${bidSubmissionId}`}>
            <Button size="sm" variant="outline">
              <ArrowLeft className="mr-1.5 h-3.5 w-3.5" /> Back to Bid Evaluation
            </Button>
          </Link>
        }
      >
        <ErrorState
          title="Unable to Load Document Vault"
          message={docsError?.response?.data?.detail || "Failed connecting to document service."}
          onRetry={refetchDocs}
        />
      </PageContainer>
    );
  }

  const bidderName = dashboardData?.bidder?.company_name || "Bidder";
  const tenderRef = dashboardData?.tender?.reference_number || "Tender";
  const allDiscrepancies = dashboardData?.discrepancies || [];

  // Summary counts
  const totalCount = documents.length;
  const processedCount = documents.filter((d) => d.status === "PROCESSED" || d.status === "SUCCESS").length;
  const pendingCount = documents.filter((d) => d.status === "UPLOADED" || d.status === "PROCESSING" || d.status === "PENDING").length;
  const failedCount = documents.filter((d) => d.status === "FAILED").length;

  const extractedFields = parseExtractedFields(extraction);
  const selectedDocDiscrepancies = selectedDoc
    ? allDiscrepancies.filter((disc) => disc.bid_document_id === selectedDoc.id)
    : [];

  return (
    <PageContainer
      title={`Document Vault & AI Intelligence (#${bidSubmissionId})`}
      description={`Evidence documents and OCR extractions for ${bidderName} (Tender ${tenderRef})`}
      badge={
        <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 text-xs font-semibold">
          {totalCount} Documents Uploaded
        </Badge>
      }
      actions={
        <div className="flex items-center gap-2 flex-wrap">
          <Link to={`/bids/${bidSubmissionId}`}>
            <Button size="sm" variant="outline" className="text-xs">
              <ArrowLeft className="mr-1.5 h-3.5 w-3.5" /> Back to Bid Evaluation
            </Button>
          </Link>

          {/* Upload Modal Dialog */}
          <Dialog open={openUploadModal} onOpenChange={setOpenUploadModal}>
            <DialogTrigger asChild>
              <Button size="sm" className="bg-blue-600 hover:bg-blue-700 text-white text-xs shadow-sm">
                <Upload className="mr-1.5 h-3.5 w-3.5" /> Upload Document
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md bg-white p-6">
              <DialogHeader>
                <DialogTitle className="text-lg font-bold text-slate-900">Upload Bid Document</DialogTitle>
                <CardDescription className="text-xs text-slate-500">
                  Upload PDF or image evidence documents to execute backend Document Intelligence OCR.
                </CardDescription>
              </DialogHeader>

              <form onSubmit={handleUploadSubmit} className="space-y-4 py-2 text-xs">
                {uploadError && (
                  <div className="p-3 rounded-md bg-red-50 border border-red-200 text-red-700 flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 shrink-0 text-red-600" />
                    <span>{uploadError}</span>
                  </div>
                )}

                <div className="space-y-1">
                  <Label className="text-xs font-semibold text-slate-700">Document Type</Label>
                  <select
                    className="w-full text-xs p-2 border border-slate-200 rounded-md bg-white text-slate-900 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                    value={documentType}
                    onChange={(e) => setDocumentType(e.target.value)}
                  >
                    <option value="GST_CERTIFICATE">GST Registration Certificate</option>
                    <option value="UDYAM_CERTIFICATE">Udyam / MSME Certificate</option>
                    <option value="MAKE_IN_INDIA_DECLARATION">Make in India Self-Declaration</option>
                    <option value="OEM_AUTHORIZATION">OEM Authorization Letter</option>
                    <option value="INCOME_TAX_RETURN">Income Tax Returns (ITR)</option>
                    <option value="PAN_CARD">Permanent Account Number (PAN) Card</option>
                    <option value="DEBARMENT_UNDERTAKING">Non-Blacklisting Undertaking</option>
                    <option value="EPFO_CHALLAN">EPFO / ESIC Employee Return</option>
                    <option value="MCA_ANNUAL_RETURN">MCA21 Corporate Incorporation</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <Label className="text-xs font-semibold text-slate-700">File Attachment (PDF / PNG / JPG)</Label>
                  <Input
                    type="file"
                    required
                    accept=".pdf,.png,.jpg,.jpeg"
                    onChange={(e) => setUploadFile(e.target.files[0])}
                    className="text-xs"
                  />
                  <span className="text-[10px] text-slate-400 block mt-1">Maximum file size: 10MB</span>
                </div>

                <DialogFooter className="pt-3 flex items-center justify-end gap-2">
                  <Button type="button" variant="outline" onClick={() => setOpenUploadModal(false)} className="text-xs">
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={uploadMutation.isPending}
                    className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold"
                  >
                    {uploadMutation.isPending ? "Uploading & Extracting..." : "Upload & Run Extraction"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
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
        <Button size="sm" variant="default" className="bg-slate-900 text-white text-xs font-semibold">
          <FileText className="mr-1.5 h-3.5 w-3.5 text-blue-400" /> Documents Vault ({totalCount})
        </Button>
        <Link to={`/bids/${bidSubmissionId}/verification`}>
          <Button size="sm" variant="outline" className="text-xs text-slate-700 hover:bg-slate-100">
            <ShieldCheck className="mr-1.5 h-3.5 w-3.5 text-emerald-600" /> Statutory Verifications
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

      {/* Real Summary Metrics Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card className="shadow-subtle border-slate-200 bg-white">
          <CardContent className="p-3.5">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Submitted Documents</span>
            <span className="text-xl font-bold text-slate-900 mt-1 block">{totalCount}</span>
          </CardContent>
        </Card>
        <Card className="shadow-subtle border-slate-200 bg-white">
          <CardContent className="p-3.5">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">OCR Processed</span>
            <span className="text-xl font-bold text-emerald-600 mt-1 block">{processedCount}</span>
          </CardContent>
        </Card>
        <Card className="shadow-subtle border-slate-200 bg-white">
          <CardContent className="p-3.5">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Processing / Pending</span>
            <span className="text-xl font-bold text-amber-600 mt-1 block">{pendingCount}</span>
          </CardContent>
        </Card>
        <Card className="shadow-subtle border-slate-200 bg-white">
          <CardContent className="p-3.5">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Extraction Failures</span>
            <span className="text-xl font-bold text-red-600 mt-1 block">{failedCount}</span>
          </CardContent>
        </Card>
      </div>

      {/* Main Grid: Document List (Left 1 col) & Extraction Intelligence (Right 2 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Submitted Files List */}
        <div className="space-y-3">
          <Card className="shadow-subtle border-slate-200 bg-white">
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <FileText className="h-4 w-4 text-blue-600" />
                Submitted Files ({documents.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="p-2 space-y-2">
              {documents.length === 0 ? (
                <div className="p-6 text-center text-xs text-slate-500 space-y-2">
                  <FileWarning className="h-6 w-6 text-slate-400 mx-auto" />
                  <p>No documents uploaded for this bid yet.</p>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setOpenUploadModal(true)}
                    className="text-xs"
                  >
                    <Upload className="mr-1.5 h-3.5 w-3.5" /> Upload First Document
                  </Button>
                </div>
              ) : (
                documents.map((doc) => {
                  const isSelected = selectedDoc?.id === doc.id;
                  const docStatus = doc.status || "PROCESSED";

                  return (
                    <div
                      key={doc.id}
                      onClick={() => handleSelectDoc(doc)}
                      className={`p-3 rounded-lg border text-xs cursor-pointer transition-all ${
                        isSelected
                          ? "border-blue-500 bg-blue-50/70 shadow-sm"
                          : "border-slate-200/80 bg-slate-50/40 hover:bg-slate-100/80"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-bold text-slate-900 truncate">
                          {doc.file_name || doc.original_filename || `Document #${doc.id}`}
                        </span>
                        <Badge variant="outline" className="bg-white text-slate-700 text-[10px] shrink-0 font-mono">
                          {doc.document_type}
                        </Badge>
                      </div>

                      <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-200/60 text-[11px] text-slate-500">
                        <span className="flex items-center gap-1 font-medium">
                          Status:
                          {docStatus === "PROCESSED" && <span className="text-emerald-700 font-bold">PROCESSED</span>}
                          {docStatus === "FAILED" && <span className="text-red-700 font-bold">FAILED</span>}
                          {docStatus !== "PROCESSED" && docStatus !== "FAILED" && (
                            <span className="text-amber-700 font-bold">{docStatus}</span>
                          )}
                        </span>

                        <span className="text-blue-600 font-semibold hover:underline flex items-center gap-1">
                          <Eye className="h-3 w-3" /> Inspect Data
                        </span>
                      </div>
                    </div>
                  );
                })
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column: AI Document Intelligence Detail Inspector */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="shadow-subtle border-slate-200 bg-white">
            <CardHeader className="pb-3 border-b border-slate-100 flex flex-row items-center justify-between gap-4">
              <div>
                <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Cpu className="h-4 w-4 text-purple-600" />
                  AI Document Intelligence Inspector
                </CardTitle>
                <CardDescription className="text-xs text-slate-500">
                  {selectedDoc
                    ? `Parsed OCR entities for ${selectedDoc.file_name || selectedDoc.original_filename}`
                    : "Select a document to inspect extractions"}
                </CardDescription>
              </div>

              {selectedDoc && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleRunProcess(selectedDoc.id)}
                  disabled={processMutation.isPending}
                  className="text-xs shrink-0"
                >
                  <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${processMutation.isPending ? "animate-spin text-purple-600" : ""}`} />
                  {processMutation.isPending ? "Processing OCR..." : "Re-Run OCR"}
                </Button>
              )}
            </CardHeader>

            <CardContent className="p-5 space-y-4">
              {!selectedDoc ? (
                <div className="p-12 text-center text-slate-400 text-xs">
                  Select a document from the left vault list to inspect OCR extractions.
                </div>
              ) : isExtractionLoading ? (
                <LoadingState message="Fetching OCR extraction data from Document Intelligence service..." />
              ) : extraction ? (
                <>
                  {/* Status & Confidence Banner */}
                  <div className="flex items-center justify-between p-3.5 rounded-lg bg-purple-50 border border-purple-100 text-xs flex-wrap gap-2">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-purple-600 shrink-0" />
                      <div>
                        <span className="font-bold text-purple-950">OCR Extraction Completed</span>
                        {extraction.extractor_name && (
                          <span className="text-[10px] text-purple-700 block font-mono">
                            Engine: {extraction.extractor_name} ({extraction.extractor_version || "v1.0"})
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {extraction.confidence_score !== null && extraction.confidence_score !== undefined && (
                        <Badge variant="outline" className="bg-purple-100 text-purple-800 border-purple-300 font-bold text-xs">
                          Confidence: {(extraction.confidence_score * 100).toFixed(0)}%
                        </Badge>
                      )}
                      <Badge variant="outline" className="bg-white text-purple-900 border-purple-200 text-xs font-mono">
                        {extraction.extraction_status}
                      </Badge>
                    </div>
                  </div>

                  {/* Mandated Disclaimer Banner */}
                  <div className="p-3 rounded-md bg-blue-50/70 border border-blue-200 text-[11px] text-blue-900 flex items-start gap-2">
                    <AlertCircle className="h-4 w-4 text-blue-600 shrink-0 mt-0.5" />
                    <div>
                      <strong className="block font-semibold">Document Intelligence Distinction:</strong>
                      Extracted fields are parsed directly from the uploaded PDF document by AI/OCR tools. Verification against official government portals (GSTN, MCA21, EPFO) is performed and recorded separately in the Statutory Verification Center.
                    </div>
                  </div>

                  {/* Extraction Errors if any */}
                  {extraction.error_message && (
                    <div className="p-3.5 rounded-lg bg-red-50 border border-red-200 text-xs text-red-800 space-y-1">
                      <div className="flex items-center gap-2 font-bold text-red-900">
                        <AlertTriangle className="h-4 w-4 text-red-600" />
                        Extraction Exception Flagged
                      </div>
                      <p className="text-[11px] leading-relaxed">{extraction.error_message}</p>
                    </div>
                  )}

                  {/* Parsed Extracted Fields Grid */}
                  <div className="space-y-2 pt-1">
                    <span className="text-xs font-bold text-slate-900 block">Extracted Entities & Metadata:</span>

                    {Object.keys(extractedFields).length === 0 ? (
                      <div className="p-6 text-center text-xs text-slate-500 bg-slate-50 rounded-lg border border-slate-100">
                        No structured fields extracted from this document text payload yet. Click "Re-Run OCR" to execute text parsing.
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {Object.entries(extractedFields).map(([key, val]) => (
                          <div key={key} className="p-3 rounded-lg bg-slate-50 border border-slate-200/70 space-y-0.5">
                            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                              {key.replace(/_/g, " ")}
                            </span>
                            <span className="text-xs font-bold text-slate-900 block break-all font-mono">
                              {typeof val === "object" ? JSON.stringify(val) : String(val)}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Associated Document Discrepancies */}
                  {selectedDocDiscrepancies.length > 0 && (
                    <div className="p-4 rounded-lg bg-amber-50/60 border border-amber-200 space-y-2 text-xs mt-4">
                      <span className="font-bold text-amber-900 flex items-center gap-1.5">
                        <FileWarning className="h-4 w-4 text-amber-600" />
                        Document Discrepancies ({selectedDocDiscrepancies.length})
                      </span>
                      {selectedDocDiscrepancies.map((disc) => (
                        <div key={disc.id} className="p-2.5 bg-white rounded border border-amber-200 space-y-1">
                          <div className="flex items-center justify-between font-bold text-slate-900">
                            <span>{disc.title}</span>
                            <Badge className="bg-amber-600 text-white text-[10px]">{disc.severity}</Badge>
                          </div>
                          <p className="text-slate-600 text-[11px]">{disc.description}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <div className="p-8 text-center text-xs text-slate-500 space-y-3">
                  <AlertCircle className="h-8 w-8 text-slate-400 mx-auto" />
                  <div>
                    <p className="font-semibold text-slate-800">No Document Extraction Record Found</p>
                    <p className="text-[11px] text-slate-500">Document Intelligence has not parsed text from this file yet.</p>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => handleRunProcess(selectedDoc.id)}
                    disabled={processMutation.isPending}
                    className="bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold shadow-sm"
                  >
                    <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${processMutation.isPending ? "animate-spin" : ""}`} />
                    {processMutation.isPending ? "Processing..." : "Run Document Intelligence OCR"}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </PageContainer>
  );
}
