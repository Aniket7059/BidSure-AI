import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  FileText,
  Plus,
  Search,
  Filter,
  Building2,
  ArrowRight,
  Loader2,
  AlertCircle,
  FolderOpen,
  Calendar,
  ShieldCheck,
  Users
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
import { useTendersQuery, useCreateTenderMutation } from "../features/tenders/useTenders";

export function TendersPage() {
  const { data: tenders = [], isLoading, isError, error, refetch } = useTendersQuery();
  const createTenderMutation = useCreateTenderMutation();

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [openModal, setOpenModal] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  const [formData, setFormData] = useState({
    reference_number: "",
    title: "",
    department: "Chennai Petroleum Corporation Limited (CPCL)",
    category: "Industrial Equipment",
    minimum_turnover: 50000000,
    min_local_content: 50,
    closing_date: "2026-10-31T18:00:00Z",
  });

  const handleCreateTender = async (e) => {
    e.preventDefault();
    setSubmitError(null);
    try {
      await createTenderMutation.mutateAsync(formData);
      setOpenModal(false);
      setFormData({
        reference_number: "",
        title: "",
        department: "Chennai Petroleum Corporation Limited (CPCL)",
        category: "Industrial Equipment",
        minimum_turnover: 50000000,
        min_local_content: 50,
        closing_date: "2026-10-31T18:00:00Z",
      });
    } catch (err) {
      setSubmitError(err?.response?.data?.detail || "Failed to create tender on server.");
    }
  };

  const filteredTenders = tenders.filter((t) => {
    const titleMatch = (t.title || "").toLowerCase().includes(search.toLowerCase());
    const refMatch = (t.reference_number || t.reference_no || "").toLowerCase().includes(search.toLowerCase());
    const deptMatch = (t.department || t.issuing_organization || "").toLowerCase().includes(search.toLowerCase());
    const matchesSearch = titleMatch || refMatch || deptMatch;

    if (statusFilter === "ALL") return matchesSearch;
    const itemStatus = (t.status || "ACTIVE").toUpperCase();
    return matchesSearch && itemStatus === statusFilter;
  });

  return (
    <PageContainer
      title="GeM Procurement Tenders"
      description="Manage active CPCL tender notices, review statutory compliance parameters, and navigate bid evaluations."
      badge={
        <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 text-xs">
          CPCL Procurement Portal
        </Badge>
      }
      actions={
        <Dialog open={openModal} onOpenChange={setOpenModal}>
          <DialogTrigger asChild>
            <Button size="sm" className="bg-blue-600 hover:bg-blue-700 text-xs shadow-sm">
              <Plus className="mr-1.5 h-3.5 w-3.5" />
              Create New Tender
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-lg bg-white border-slate-200 p-6">
            <DialogHeader>
              <DialogTitle className="text-lg font-bold text-slate-900">
                Register New Procurement Tender
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreateTender} className="space-y-4 py-2">
              {submitError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded text-xs text-red-700 flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 shrink-0 text-red-600" />
                  <span>{submitError}</span>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label className="text-xs font-semibold text-slate-700">Tender Reference No.</Label>
                  <Input
                    required
                    placeholder="GEM/2026/B/998877"
                    value={formData.reference_number}
                    onChange={(e) => setFormData({ ...formData, reference_number: e.target.value })}
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs font-semibold text-slate-700">Category</Label>
                  <Input
                    required
                    placeholder="Industrial Equipment"
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  />
                </div>
              </div>

              <div className="space-y-1">
                <Label className="text-xs font-semibold text-slate-700">Tender Title</Label>
                <Input
                  required
                  placeholder="Supply & Commissioning of High Pressure Valves"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                />
              </div>

              <div className="space-y-1">
                <Label className="text-xs font-semibold text-slate-700">Department / Division</Label>
                <Input
                  required
                  value={formData.department}
                  onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label className="text-xs font-semibold text-slate-700">Min Annual Turnover (₹)</Label>
                  <Input
                    type="number"
                    required
                    value={formData.minimum_turnover}
                    onChange={(e) => setFormData({ ...formData, minimum_turnover: Number(e.target.value) })}
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs font-semibold text-slate-700">Min Local Content %</Label>
                  <Input
                    type="number"
                    required
                    min="0"
                    max="100"
                    value={formData.min_local_content}
                    onChange={(e) => setFormData({ ...formData, min_local_content: Number(e.target.value) })}
                  />
                </div>
              </div>

              <DialogFooter className="pt-3">
                <Button type="button" variant="outline" onClick={() => setOpenModal(false)}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={createTenderMutation.isPending}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {createTenderMutation.isPending ? "Saving..." : "Save & Register Tender"}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      }
    >
      {/* Search & Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-white p-3 rounded-lg border border-slate-200 shadow-subtle">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Search tenders by GeM ID, Title, or Dept..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 text-xs"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="h-3.5 w-3.5 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs border border-slate-200 rounded px-2.5 py-1 bg-white text-slate-700 focus:ring-1 focus:ring-blue-500 focus:outline-none"
          >
            <option value="ALL">All Statuses</option>
            <option value="ACTIVE">Active / Published</option>
            <option value="DRAFT">Draft</option>
            <option value="CLOSED">Closed</option>
          </select>
          <Badge variant="outline" className="bg-slate-50 text-slate-700 text-xs px-2.5 py-1 shrink-0">
            Total: {filteredTenders.length}
          </Badge>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="p-12 text-center bg-white rounded-lg border border-slate-200">
          <Loader2 className="h-7 w-7 text-blue-600 animate-spin mx-auto mb-2" />
          <p className="text-xs font-semibold text-slate-700">Loading tenders from server...</p>
        </div>
      )}

      {/* Error State */}
      {isError && (
        <div className="p-6 bg-red-50 rounded-lg border border-red-200 text-center space-y-3">
          <AlertCircle className="h-8 w-8 text-red-600 mx-auto" />
          <div>
            <h3 className="text-sm font-bold text-red-900">Failed to Load Tenders</h3>
            <p className="text-xs text-red-700 mt-1">
              {error?.response?.data?.detail || error?.message || "An error occurred while connecting to the backend server."}
            </p>
          </div>
          <Button size="sm" variant="outline" onClick={() => refetch()} className="text-xs border-red-300 text-red-800">
            Try Again
          </Button>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !isError && filteredTenders.length === 0 && (
        <div className="p-12 text-center bg-white rounded-lg border border-slate-200 space-y-3">
          <FolderOpen className="h-10 w-10 text-slate-300 mx-auto" />
          <h3 className="text-sm font-bold text-slate-800">No Tenders Found</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            {search ? `No tenders match search query "${search}".` : "No tender records currently exist in the database."}
          </p>
        </div>
      )}

      {/* Tender List Cards */}
      {!isLoading && !isError && filteredTenders.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredTenders.map((tender) => (
            <Card
              key={tender.id}
              className="shadow-subtle border-slate-200 hover:border-blue-300 transition-all flex flex-col justify-between"
            >
              <CardHeader className="pb-3 border-b border-slate-100 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-100">
                    {tender.reference_number || tender.reference_no || `TENDER-#${tender.id}`}
                  </span>
                  <Badge
                    variant="outline"
                    className={`text-[10px] ${
                      (tender.status || "ACTIVE") === "ACTIVE" || (tender.status || "") === "PUBLISHED"
                        ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                        : "bg-slate-100 text-slate-700 border-slate-200"
                    }`}
                  >
                    {tender.status || "ACTIVE"}
                  </Badge>
                </div>
                <Link to={`/tenders/${tender.id}`} className="hover:underline">
                  <CardTitle className="text-sm font-bold text-slate-900 line-clamp-2 leading-snug">
                    {tender.title}
                  </CardTitle>
                </Link>
              </CardHeader>
              <CardContent className="p-4 text-xs space-y-3 flex-1 flex flex-col justify-between">
                <div className="space-y-1.5 text-slate-600">
                  <div className="flex items-center gap-2">
                    <Building2 className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                    <span className="truncate">
                      {tender.department || tender.issuing_organization || "CPCL Refinery"}
                    </span>
                  </div>
                  {tender.minimum_turnover != null && (
                    <div className="flex items-center justify-between pt-1">
                      <span>Min Turnover:</span>
                      <span className="font-semibold text-slate-900">
                        ₹{(tender.minimum_turnover / 100000).toFixed(0)} Lakhs
                      </span>
                    </div>
                  )}
                  {tender.min_local_content != null && (
                    <div className="flex items-center justify-between">
                      <span>MII Local Content:</span>
                      <span className="font-semibold text-slate-900">≥ {tender.min_local_content}%</span>
                    </div>
                  )}
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-1">
                  <Link to={`/tenders/${tender.id}`}>
                    <Button size="sm" variant="ghost" className="text-xs text-slate-600 px-2">
                      Overview
                    </Button>
                  </Link>
                  <Link to={`/tenders/${tender.id}/requirements`}>
                    <Button size="sm" variant="ghost" className="text-xs text-blue-600 px-2">
                      Rules
                    </Button>
                  </Link>
                  <Link to={`/tenders/${tender.id}/bids`}>
                    <Button size="sm" className="bg-slate-900 hover:bg-slate-800 text-xs px-2.5">
                      Bids <ArrowRight className="ml-1 h-3 w-3" />
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </PageContainer>
  );
}
