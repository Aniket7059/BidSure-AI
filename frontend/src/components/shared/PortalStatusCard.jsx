import React from "react";
import { CheckCircle2, XCircle, Clock, AlertCircle } from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";

export function PortalStatusCard({ title, subtitle, status = "VERIFIED", identifier, onVerify, isLoading }) {
  const getStatusDisplay = () => {
    switch (status) {
      case "VERIFIED":
      case "PASSED":
        return {
          icon: <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />,
          badgeBg: "bg-emerald-50 text-emerald-700 border-emerald-200",
          text: "Verified",
        };
      case "FAILED":
      case "NON_COMPLIANT":
        return {
          icon: <XCircle className="h-4 w-4 text-red-600 shrink-0" />,
          badgeBg: "bg-red-50 text-red-700 border-red-200",
          text: "Failed",
        };
      case "FLAGGED":
        return {
          icon: <AlertCircle className="h-4 w-4 text-amber-600 shrink-0" />,
          badgeBg: "bg-amber-50 text-amber-700 border-amber-200",
          text: "Flagged",
        };
      default:
        return {
          icon: <Clock className="h-4 w-4 text-slate-400 shrink-0" />,
          badgeBg: "bg-slate-100 text-slate-600 border-slate-200",
          text: "Pending",
        };
    }
  };

  const current = getStatusDisplay();

  return (
    <Card className="shadow-subtle border-slate-200 hover:border-slate-300 transition-all">
      <CardContent className="p-4 flex items-center justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0">
          <div className="p-2 rounded-lg bg-slate-100 text-slate-700 shrink-0 mt-0.5">
            {current.icon}
          </div>
          <div className="min-w-0">
            <h4 className="text-sm font-semibold text-slate-900 truncate">{title}</h4>
            <p className="text-xs text-slate-500 truncate mt-0.5">{subtitle}</p>
            {identifier && (
              <p className="text-[11px] font-mono text-slate-600 mt-1 truncate bg-slate-50 px-1.5 py-0.5 rounded border border-slate-100 inline-block">
                ID: {identifier}
              </p>
            )}
          </div>
        </div>
        <div className="flex flex-col items-end gap-2 shrink-0">
          <Badge variant="outline" className={`text-[11px] font-medium ${current.badgeBg}`}>
            {current.text}
          </Badge>
          {onVerify && (
            <button
              onClick={onVerify}
              disabled={isLoading}
              className="text-[11px] font-medium text-blue-600 hover:text-blue-700 underline cursor-pointer disabled:opacity-50"
            >
              {isLoading ? "Checking..." : "Re-Verify"}
            </button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
