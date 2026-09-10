import React from "react";
import { Loader2 } from "lucide-react";
import { cn } from "../../lib/utils";

/**
 * Reusable loading state component.
 *
 * @param {object} props
 * @param {string} [props.message="Loading parameters and data..."]
 * @param {string} [props.className]
 */
export function LoadingState({
  message = "Loading operational data...",
  className,
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-8 text-center min-h-[200px]",
        className
      )}
    >
      <Loader2 className="h-6 w-6 animate-spin text-primary mb-3" />
      <p className="text-xs text-muted-foreground font-medium">{message}</p>
    </div>
  );
}
