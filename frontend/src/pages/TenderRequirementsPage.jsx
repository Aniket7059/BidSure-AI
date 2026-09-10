import React, { useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  ListChecks,
  Plus,
  ArrowLeft,
  ShieldCheck,
  FileText,
  Layers,
  Loader2,
  AlertCircle,
  FolderOpen
} from "lucide-react";
import { PageContainer } from "../components/layout/PageContainer";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter
} from "../components/ui/dialog";
import { Label } from "../components/ui/label";
import {
  useTenderQuery,
  useTenderRequirementsQuery,
  useCreateRequirementMutation
} from "../features/tenders/useTenders";

export function TenderRequirementsPage() {
  const { tenderId } = useParams();

  const { data: tender } = useTenderQuery(tenderId);
  const {
    data: requirements = [],
    isLoading,
    isError,
    error,
    refetch
  } = useTenderRequirementsQuery(tenderId);

  const createRequirementMutation = useCreateRequirementMutation(tenderId);

  const [openModal, setOpenModal] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  const [formData, setFormData] = useState({
    requirement_type: "MSME_REGISTRATION",
    requirement_name: "",
    description: "",
    is_required: true,
    validation_config: '{"required": true}',
    source_document: "",
  });

  const handleAddRequirement = async (e) => {
    e.preventDefault();
    setSubmitError(null);
    try {
      await createRequirementMutation.mutateAsync({
        requirement_type: formData.requirement_type,
        requirement_name: formData.requirement_name,
        description: formData.description,
        is_required: formData.is_required,
        validation_config: formData.validation_config,
        source_document: formData.source_document || undefined,
      });
      setOpenModal(false);
      setFormData({
        requirement_type: "MSME_REGISTRATION",
        requirement_name: "",
        description: "",
        is_required: true,
        validation_config: '{"required": true}',
        source_document: "",
      });
    } catch (err) {
      setSubmitError(err?.response?.data?.detail || "Failed to create requirement rule.");
    }
  };

  return (
    <PageContainer
      title={
        tender
          ? `Statutory Requirements: ${tender.reference_number || tender.reference_no || `Tender #${tenderId}`}`
          : `Statutory Requirements (Tender #${tenderId})`
      }
      description="Configure statutory evaluation rules, statutory criteria thresholds, and requirement provenance."
      badge={
        <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 text-xs">
          {requirements.length} Configured Rules
        </Badge>
      }
      actions={
        <div className="flex items-center gap-2">
          <Link to={`/tenders/${tenderId}`}>
            <Button size="sm" variant="outline" className="text-xs">
              <ArrowLeft className="mr-1.5 h-3.5 w-3.5" /> Back to Tender
            </Button>
          </Link>

          <Dialog open={openModal} onOpenChange={setOpenModal}>
            <DialogTrigger asChild>
              <Button size="sm" className="bg-blue-600 hover:bg-blue-700 text-xs shadow-sm">
                <Plus className="mr-1.5 h-3.5 w-3.5" /> Add Statutory Rule
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-lg bg-white p-6">
              <DialogHeader>
                <DialogTitle className="text-lg font-bold text-slate-900">
                  Add Compliance Requirement Rule
                </DialogTitle>
              </DialogHeader>

              <form onSubmit={handleAddRequirement} className="space-y-4 py-2">
                {submitError && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded text-xs text-red-700 flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 shrink-0 text-red-600" />
                    <span>{submitError}</span>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs font-semibold text-slate-700">Requirement Type</Label>
                    <select
                      value={formData.requirement_type}
                      onChange={(e) => setFormData({ ...formData, requirement_type: e.target.value })}
                      className="w-full text-xs border border-slate-200 rounded px-2.5 py-1.5 bg-white text-slate-900 focus:ring-1 focus:ring-blue-500"
                    >
                      <option value="MSME_REGISTRATION">MSME / Udyam Registration</option>
                      <option value="GST_REGISTRATION">GST Registration & Return</option>
                      <option value="FINANCIAL_TURNOVER">Financial Turnover Threshold</option>
                      <option value="MAKE_IN_INDIA">Make In India (MII Local Content)</option>
                      <option value="EPFO_ESIC_COMPLIANCE">EPFO / ESIC Compliance</option>
                      <option value="STARTUP_DPIIT_RECOGNITION">Startup India / DPIIT Waiver</option>
                      <option value="OEM_AUTHORIZATION">OEM Authorization Letter</option>
                      <option value="DEBARMENT_CLEARANCE">Debarment / Blacklisting Clearance</option>
                    </select>
                  </div>

                  <div className="space-y-1">
                    <Label className="text-xs font-semibold text-slate-700">Rule Level</Label>
                    <select
                      value={formData.is_required ? "MANDATORY" : "OPTIONAL"}
                      onChange={(e) => setFormData({ ...formData, is_required: e.target.value === "MANDATORY" })}
                      className="w-full text-xs border border-slate-200 rounded px-2.5 py-1.5 bg-white text-slate-900 focus:ring-1 focus:ring-blue-500"
                    >
                      <option value="MANDATORY">Mandatory</option>
                      <option value="OPTIONAL">Optional / Exemption</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-1">
                  <Label className="text-xs font-semibold text-slate-700">Requirement Name</Label>
                  <Input
                    required
                    placeholder="e.g. Active Udyam MSME Certificate Registration"
                    value={formData.requirement_name}
                    onChange={(e) => setFormData({ ...formData, requirement_name: e.target.value })}
                  />
                </div>

                <div className="space-y-1">
                  <Label className="text-xs font-semibold text-slate-700">Description & Evaluation Logic</Label>
                  <Input
                    required
                    placeholder="Bidder must possess active Udyam registration matching PAN."
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  />
                </div>

                <div className="space-y-1">
                  <Label className="text-xs font-semibold text-slate-700">Source Document Citation (Optional)</Label>
                  <Input
                    placeholder="e.g. GeM_Tender_Notice_Section_4.2.pdf"
                    value={formData.source_document}
                    onChange={(e) => setFormData({ ...formData, source_document: e.target.value })}
                  />
                </div>

                <DialogFooter className="pt-3">
                  <Button type="button" variant="outline" onClick={() => setOpenModal(false)}>
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={createRequirementMutation.isPending}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    {createRequirementMutation.isPending ? "Saving..." : "Save Requirement Rule"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      }
    >
      {/* Loading State */}
      {isLoading && (
        <div className="p-12 text-center bg-white rounded-lg border border-slate-200">
          <Loader2 className="h-7 w-7 text-blue-600 animate-spin mx-auto mb-2" />
          <p className="text-xs font-semibold text-slate-700">Loading statutory requirements...</p>
        </div>
      )}

      {/* Error State */}
      {isError && (
        <div className="p-6 bg-red-50 rounded-lg border border-red-200 text-center space-y-3">
          <AlertCircle className="h-8 w-8 text-red-600 mx-auto" />
          <div>
            <h3 className="text-sm font-bold text-red-900">Failed to Load Requirements</h3>
            <p className="text-xs text-red-700 mt-1">
              {error?.response?.data?.detail || error?.message || "Could not retrieve requirement records."}
            </p>
          </div>
          <Button size="sm" variant="outline" onClick={() => refetch()} className="text-xs border-red-300 text-red-800">
            Retry Loading
          </Button>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !isError && requirements.length === 0 && (
        <div className="p-12 text-center bg-white rounded-lg border border-slate-200 space-y-3">
          <FolderOpen className="h-10 w-10 text-slate-300 mx-auto" />
          <h3 className="text-sm font-bold text-slate-800">No Requirements Configured</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            No statutory or technical requirements have been added to this tender yet. Click "Add Statutory Rule" or run the AI Notice Parser on the tender overview page.
          </p>
        </div>
      )}

      {/* Requirements List */}
      {!isLoading && !isError && requirements.length > 0 && (
        <Card className="shadow-subtle border-slate-200 bg-white">
          <CardHeader className="pb-3 border-b border-slate-100">
            <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-emerald-600" />
              Statutory Evaluation Rules
            </CardTitle>
            <CardDescription className="text-xs text-slate-500">
              Rules automatically executed by the Compliance Evaluation Engine during verification.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0 divide-y divide-slate-100">
            {requirements.map((req) => {
              const name = req.requirement_name || req.title || req.requirement_code;
              const type = req.requirement_type || req.category || "STATUTORY";
              const isMandatory = req.is_required !== undefined ? req.is_required : (req.is_mandatory ?? true);

              return (
                <div key={req.id} className="p-5 hover:bg-slate-50 transition-colors space-y-2">
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                        {type}
                      </span>
                      {isMandatory ? (
                        <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200 text-[10px] font-bold">
                          MANDATORY
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="bg-slate-100 text-slate-600 border-slate-200 text-[10px]">
                          OPTIONAL / EXEMPTION
                        </Badge>
                      )}
                    </div>

                    {req.evaluator_name && (
                      <span className="text-[11px] font-mono text-slate-500">
                        Evaluator: <span className="text-blue-600 font-semibold">{req.evaluator_name}</span>
                      </span>
                    )}
                  </div>

                  <div>
                    <h4 className="text-sm font-bold text-slate-900">{name}</h4>
                    {req.description && (
                      <p className="text-xs text-slate-600 mt-0.5 leading-relaxed">{req.description}</p>
                    )}
                  </div>

                  {/* Source Provenance Section (if present) */}
                  {(req.source_document || (req.source_chunk_ids && req.source_chunk_ids.length > 0)) && (
                    <div className="mt-2 pt-2 border-t border-slate-100 flex items-center gap-3 text-[11px] text-slate-500">
                      <FileText className="h-3.5 w-3.5 text-blue-500 shrink-0" />
                      <span>
                        Source Provenance: <strong className="text-slate-700">{req.source_document || "Tender Notice Document"}</strong>
                      </span>
                      {req.source_chunk_ids && (
                        <span className="font-mono text-slate-400">
                          (Chunks: {Array.isArray(req.source_chunk_ids) ? req.source_chunk_ids.join(", ") : req.source_chunk_ids})
                        </span>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}
    </PageContainer>
  );
}
