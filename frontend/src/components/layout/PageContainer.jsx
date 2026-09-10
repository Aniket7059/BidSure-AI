import React from "react";
import { cn } from "../../lib/utils";

/**
 * Standard container layout for all operational pages.
 *
 * @param {object} props
 * @param {string} [props.title]
 * @param {string} [props.description]
 * @param {React.ReactNode} [props.badge]
 * @param {React.ReactNode} [props.actions]
 * @param {React.ReactNode} props.children
 * @param {string} [props.className]
 */
export function PageContainer({
  title,
  description,
  badge,
  actions,
  children,
  className,
}) {
  return (
    <div
      className={cn(
        "flex-1 p-6 sm:p-8 lg:p-10 max-w-7xl w-full mx-auto space-y-8 bg-white text-slate-900",
        className
      )}
    >
      {/* Optional Page Header */}
      {(title || description || actions) && (
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 pb-6">
          <div className="space-y-1.5">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
                {title}
              </h1>
              {badge}
            </div>
            {description && (
              <p className="text-xs sm:text-sm text-slate-500 leading-relaxed">
                {description}
              </p>
            )}
          </div>
          {actions && <div className="flex items-center gap-3 shrink-0">{actions}</div>}
        </div>
      )}

      {/* Main Content Body */}
      <main className="space-y-6">{children}</main>
    </div>
  );
}
