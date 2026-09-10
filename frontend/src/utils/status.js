/**
 * Status design configuration and badge variants mapping.
 */

export const STATUS_CONFIG = {
  // Verification Statuses
  VERIFIED: {
    label: "Verified",
    variant: "success",
    className: "bg-emerald-50 text-emerald-700 border-emerald-200",
  },
  NOT_VERIFIED: {
    label: "Not Verified",
    variant: "warning",
    className: "bg-amber-50 text-amber-700 border-amber-200",
  },
  NOT_FOUND: {
    label: "Not Found",
    variant: "destructive",
    className: "bg-rose-50 text-rose-700 border-rose-200",
  },
  MISMATCH: {
    label: "Mismatch Flagged",
    variant: "destructive",
    className: "bg-rose-50 text-rose-700 border-rose-200 font-medium",
  },
  PENDING: {
    label: "Pending Review",
    variant: "outline",
    className: "bg-slate-50 text-slate-700 border-slate-200",
  },
  ERROR: {
    label: "Verification Error",
    variant: "destructive",
    className: "bg-rose-50 text-rose-700 border-rose-200",
  },
  NOT_APPLICABLE: {
    label: "N/A",
    variant: "secondary",
    className: "bg-slate-100 text-slate-600 border-slate-200",
  },

  // Compliance Check Statuses
  PASS: {
    label: "Pass",
    variant: "success",
    className: "bg-emerald-50 text-emerald-700 border-emerald-200 font-medium",
  },
  FAIL: {
    label: "Fail",
    variant: "destructive",
    className: "bg-rose-50 text-rose-700 border-rose-200 font-medium",
  },
  REVIEW: {
    label: "Review Required",
    variant: "warning",
    className: "bg-amber-50 text-amber-700 border-amber-200 font-medium",
  },

  // Risk Classification Levels
  LOW: {
    label: "Low Risk",
    variant: "success",
    className: "bg-emerald-50 text-emerald-700 border-emerald-200 font-semibold",
  },
  MEDIUM: {
    label: "Medium Risk",
    variant: "warning",
    className: "bg-amber-50 text-amber-700 border-amber-200 font-semibold",
  },
  HIGH: {
    label: "High Risk",
    variant: "destructive",
    className: "bg-rose-50 text-rose-700 border-rose-200 font-semibold",
  },
  CRITICAL: {
    label: "Critical Risk",
    variant: "destructive",
    className: "bg-red-100 text-red-800 border-red-300 font-bold",
  },
};

/**
 * Retrieves the status configuration object for a status key.
 * @param {string} statusKey
 * @returns {object}
 */
export function getStatusMeta(statusKey) {
  if (!statusKey) return STATUS_CONFIG.PENDING;
  const key = String(statusKey).toUpperCase();
  return STATUS_CONFIG[key] || {
    label: statusKey,
    variant: "secondary",
    className: "bg-slate-100 text-slate-700 border-slate-200",
  };
}
