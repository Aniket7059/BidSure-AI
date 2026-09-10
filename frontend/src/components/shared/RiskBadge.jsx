import React from "react";
import { AlertTriangle, CheckCircle2, ShieldAlert } from "lucide-react";
import { Badge } from "../ui/badge";

export function RiskBadge({ riskLevel, className = "" }) {
  const level = (riskLevel || "").toUpperCase();

  if (level === "LOW_RISK" || level === "LOW") {
    return (
      <Badge
        variant="outline"
        className={`bg-emerald-50 text-emerald-700 border-emerald-200 gap-1.5 font-medium px-2.5 py-0.5 ${className}`}
      >
        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
        Low Risk
      </Badge>
    );
  }

  if (level === "MEDIUM_RISK" || level === "MEDIUM") {
    return (
      <Badge
        variant="outline"
        className={`bg-amber-50 text-amber-700 border-amber-200 gap-1.5 font-medium px-2.5 py-0.5 ${className}`}
      >
        <AlertTriangle className="h-3.5 w-3.5 text-amber-600" />
        Medium Risk
      </Badge>
    );
  }

  return (
    <Badge
      variant="outline"
      className={`bg-red-50 text-red-700 border-red-200 gap-1.5 font-medium px-2.5 py-0.5 ${className}`}
    >
      <ShieldAlert className="h-3.5 w-3.5 text-red-600" />
      High Risk
    </Badge>
  );
}
