import React from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  FileText,
  History,
  Settings,
  Shield,
  ChevronLeft,
  ChevronRight,
  X,
} from "lucide-react";
import { useUIStore } from "../../store/uiStore";
import { Button } from "../ui/button";
import { cn } from "../../lib/utils";

const mainNavItems = [
  {
    title: "Overview",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    title: "Tenders & Bids",
    href: "/tenders",
    icon: FileText,
  },
];

const secondaryNavItems = [
  {
    title: "System Audit Trail",
    href: "/audit-logs",
    icon: History,
  },
  {
    title: "Settings",
    href: "/settings",
    icon: Settings,
  },
];

export function Sidebar({ isMobile = false }) {
  const location = useLocation();
  const {
    sidebarCollapsed,
    toggleSidebar,
    setMobileSidebarOpen,
  } = useUIStore();

  const handleNavClick = () => {
    if (isMobile) {
      setMobileSidebarOpen(false);
    }
  };

  return (
    <aside
      className={cn(
        "flex flex-col border-r border-border bg-slate-900 text-slate-100 transition-all duration-200 ease-in-out h-full select-none",
        isMobile ? "w-full" : sidebarCollapsed ? "w-16" : "w-64"
      )}
    >
      {/* Brand Header */}
      <div className="flex h-14 items-center justify-between px-4 border-b border-slate-800">
        <div className="flex items-center gap-2.5 overflow-hidden">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-blue-600 text-white font-bold shadow-xs">
            <Shield className="h-4 w-4" />
          </div>
          {(!sidebarCollapsed || isMobile) && (
            <div className="flex flex-col leading-none">
              <span className="font-bold text-sm tracking-tight text-white">
                BidSure AI
              </span>
              <span className="text-[10px] text-slate-400 font-medium uppercase tracking-wider mt-0.5">
                GeM Procurement
              </span>
            </div>
          )}
        </div>

        {isMobile ? (
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setMobileSidebarOpen(false)}
            className="text-slate-400 hover:text-white hover:bg-slate-800"
          >
            <X className="h-4 w-4" />
          </Button>
        ) : (
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            className="hidden lg:flex h-7 w-7 text-slate-400 hover:text-white hover:bg-slate-800"
            title={sidebarCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
          >
            {sidebarCollapsed ? (
              <ChevronRight className="h-3.5 w-3.5" />
            ) : (
              <ChevronLeft className="h-3.5 w-3.5" />
            )}
          </Button>
        )}
      </div>

      {/* Main Navigation */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        <div className="space-y-1">
          {(!sidebarCollapsed || isMobile) && (
            <div className="px-2 text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Procurement Management
            </div>
          )}
          {mainNavItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              location.pathname === item.href ||
              (item.href !== "/dashboard" &&
                location.pathname.startsWith(item.href));

            return (
              <NavLink
                key={item.href}
                to={item.href}
                onClick={handleNavClick}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2.5 text-xs font-medium transition-all duration-150",
                  isActive
                    ? "bg-blue-600 text-white font-semibold shadow-xs"
                    : "text-slate-300 hover:bg-slate-800/80 hover:text-white"
                )}
                title={sidebarCollapsed && !isMobile ? item.title : undefined}
              >
                <Icon
                  className={cn(
                    "h-4 w-4 shrink-0",
                    isActive ? "text-white" : "text-slate-400"
                  )}
                />
                {(!sidebarCollapsed || isMobile) && <span>{item.title}</span>}
              </NavLink>
            );
          })}
        </div>

        {/* Secondary Section */}
        <div className="space-y-1 pt-4 border-t border-slate-800">
          {(!sidebarCollapsed || isMobile) && (
            <div className="px-2 text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
              System Settings
            </div>
          )}
          {secondaryNavItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname.startsWith(item.href);

            return (
              <NavLink
                key={item.href}
                to={item.href}
                onClick={handleNavClick}
                className={cn(
                  "flex items-center gap-3 rounded-md px-2.5 py-2 text-xs font-medium transition-colors",
                  isActive
                    ? "bg-blue-600/90 text-white font-semibold shadow-xs"
                    : "text-slate-300 hover:bg-slate-800/80 hover:text-white"
                )}
                title={sidebarCollapsed && !isMobile ? item.title : undefined}
              >
                <Icon
                  className={cn(
                    "h-4 w-4 shrink-0",
                    isActive ? "text-white" : "text-slate-400"
                  )}
                />
                {(!sidebarCollapsed || isMobile) && <span>{item.title}</span>}
              </NavLink>
            );
          })}
        </div>
      </div>

      {/* Footer Role Banner */}
      {(!sidebarCollapsed || isMobile) && (
        <div className="p-3 border-t border-slate-800 bg-slate-950/40">
          <div className="rounded-md bg-slate-800/60 p-2.5 border border-slate-700/50">
            <div className="text-[11px] font-semibold text-slate-200">
              CPCL Procurement Unit
            </div>
            <div className="text-[10px] text-slate-400">
              Ministry of Petroleum & Natural Gas
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
