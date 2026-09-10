import React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "../ui/button";
import { cn } from "../../lib/utils";

/**
 * Reusable error state component.
 *
 * @param {object} props
 * @param {string} [props.title="Unable to Load Data"]
 * @param {string} [props.message="An error occurred while fetching system records."]
 * @param {Function} [props.onRetry]
 * @param {string} [props.className]
 */
export function ErrorState({
  title = "Unable to Load System Data",
  message = "An error occurred while fetching requirements or verification data from the backend service.",
  onRetry,
  className,
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-lg border border-rose-200 bg-rose-50/40 p-8 text-center min-h-[220px]",
        className
      )}
    >
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-rose-100 text-rose-600 mb-3 border border-rose-200">
        <AlertTriangle className="h-5 w-5" />
      </div>
      <h4 className="text-sm font-semibold text-rose-900 mb-1">{title}</h4>
      <p className="text-xs text-rose-700 max-w-md mb-4 leading-relaxed">
        {message}
      </p>
      {onRetry && (
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          className="border-rose-300 text-rose-800 hover:bg-rose-100"
        >
          <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
          Retry Request
        </Button>
      )}
    </div>
  );
}
