import React from "react";
import { FolderOpen } from "lucide-react";
import { cn } from "../../lib/utils";

/**
 * Reusable empty state component (No fake data).
 *
 * @param {object} props
 * @param {string} [props.title="No Records Available"]
 * @param {string} [props.description="There are currently no records to display."]
 * @param {React.ReactNode} [props.icon]
 * @param {React.ReactNode} [props.action]
 * @param {string} [props.className]
 */
export function EmptyState({
  title = "No Records Available",
  description = "There are currently no records to display for this section.",
  icon: Icon = FolderOpen,
  action,
  className,
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-slate-50/50 p-8 text-center min-h-[220px]",
        className
      )}
    >
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-slate-500 mb-3 border border-slate-200">
        <Icon className="h-5 w-5" />
      </div>
      <h4 className="text-sm font-semibold text-slate-800 mb-1">{title}</h4>
      <p className="text-xs text-muted-foreground max-w-sm mb-4 leading-relaxed">
        {description}
      </p>
      {action && <div>{action}</div>}
    </div>
  );
}
