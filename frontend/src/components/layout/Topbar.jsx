import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Bell,
  Search,
  Menu,
  UserCheck,
  LogOut,
  ChevronRight,
  ShieldAlert,
} from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import { Avatar, AvatarFallback } from "../ui/avatar";
import { Badge } from "../ui/badge";
import { useUIStore } from "../../store/uiStore";
import { useAuthStore } from "../../store/authStore";

const routeTitleMap = {
  "/dashboard": "System Overview",
  "/tenders": "Procurement Tenders",
  "/settings": "System Configuration",
};

export function Topbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { toggleMobileSidebar } = useUIStore();
  const { logout, user } = useAuthStore();

  const getBreadcrumbs = () => {
    const path = location.pathname;

    if (path.includes("/tenders/") && path.includes("/requirements")) {
      return ["Tenders", "Tender Requirements"];
    }
    if (path.includes("/tenders/") && path.includes("/bids")) {
      return ["Tenders", "Submitted Bids"];
    }
    if (path.includes("/tenders/")) {
      return ["Tenders", "Tender Specification"];
    }
    if (path.includes("/bids/") && path.includes("/documents")) {
      return ["Bids", "Bid Documents"];
    }
    if (path.includes("/bids/") && path.includes("/verification")) {
      return ["Bids", "Statutory Verification"];
    }
    if (path.includes("/bids/") && path.includes("/compliance")) {
      return ["Bids", "Compliance & Risk Evaluation"];
    }
    if (path.includes("/bids/")) {
      return ["Bids", "Bid Details"];
    }

    const title = routeTitleMap[path] || "Procurement Intelligence";
    return [title];
  };

  const breadcrumbs = getBreadcrumbs();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  // Helper to format role string nicely
  const formatRole = (role) => {
    if (!role) return "Procurement Officer";
    return role
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(" ");
  };

  // Helper to get initials
  const getInitials = (name) => {
    if (!name) return "PO";
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .substring(0, 2)
      .toUpperCase();
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-200 bg-white px-4 lg:px-8 shadow-2xs">
      {/* 1. Left: Mobile Menu + Breadcrumb Context */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleMobileSidebar}
          className="lg:hidden h-8 w-8 text-slate-600 hover:bg-slate-100"
          title="Toggle Navigation Menu"
        >
          <Menu className="h-5 w-5" />
        </Button>

        <nav aria-label="Breadcrumb" className="flex items-center text-xs font-medium text-slate-500">
          <span className="text-slate-600 font-semibold hover:text-slate-900 transition-colors">
            BidSure Platform
          </span>
          {breadcrumbs.map((crumb, idx) => (
            <React.Fragment key={idx}>
              <ChevronRight className="h-3.5 w-3.5 mx-2 text-slate-400 shrink-0" />
              <span
                className={
                  idx === breadcrumbs.length - 1
                    ? "text-slate-900 font-semibold"
                    : "text-slate-500"
                }
              >
                {crumb}
              </span>
            </React.Fragment>
          ))}
        </nav>
      </div>

      {/* 2. Middle: Search Field */}
      <div className="relative hidden md:flex items-center w-64 lg:w-80 mx-4">
        <Search className="absolute left-3 h-3.5 w-3.5 text-slate-400 pointer-events-none" />
        <Input
          type="search"
          placeholder="Search tenders, bids, or GSTIN..."
          className="h-9 pl-9 pr-3 text-xs bg-slate-50/80 border-slate-200 focus:bg-white focus:border-blue-500 transition-all rounded-md"
        />
      </div>

      {/* 3. Right: Environment, Notifications, User Profile */}
      <div className="flex items-center gap-3">
        {/* System Environment Badge */}
        <Badge variant="outline" className="hidden sm:inline-flex bg-slate-100 text-slate-700 text-[10px] font-mono border-slate-200 px-2 py-0.5">
          CPCL ONLINE
        </Badge>

        {/* Notifications Button */}
        <Button
          variant="ghost"
          size="icon"
          className="relative h-8 w-8 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-full"
          title="System Audit Notifications"
        >
          <Bell className="h-4 w-4" />
          <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-blue-600 ring-2 ring-white" />
        </Button>

        <div className="h-4 w-[1px] bg-slate-200 mx-0.5" />

        {/* Profile Menu (No Duplicate Text) */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="flex items-center gap-2.5 px-2 py-1 h-9 hover:bg-slate-100 rounded-lg transition-colors">
              <Avatar className="h-7 w-7 border border-slate-300">
                <AvatarFallback className="bg-slate-800 text-slate-100 text-xs font-semibold">
                  {getInitials(user?.full_name)}
                </AvatarFallback>
              </Avatar>
              <div className="flex flex-col text-left leading-tight hidden sm:block">
                <span className="text-xs font-semibold text-slate-900">
                  {user?.full_name || "Procurement Officer"}
                </span>
                <span className="text-[10px] text-slate-500 font-medium">
                  {user?.role && user.role !== "PROCUREMENT_OFFICER"
                    ? formatRole(user.role)
                    : "Officer ID: PO-4092"}
                </span>
              </div>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-60">
            <DropdownMenuLabel className="font-normal p-3">
              <div className="flex flex-col space-y-1">
                <p className="text-xs font-semibold leading-none text-slate-900">
                  {user?.full_name || "Procurement Officer"}
                </p>
                <p className="text-[11px] leading-none text-slate-500">
                  {user?.email || "officer@cpcl.gov.in"}
                </p>
                <div className="pt-1.5">
                  <Badge variant="outline" className="text-[9px] font-mono uppercase bg-slate-50 text-slate-700 border-slate-200">
                    {user?.role || "PROCUREMENT_OFFICER"}
                  </Badge>
                </div>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="cursor-pointer text-xs">
              <UserCheck className="mr-2 h-3.5 w-3.5 text-slate-500" />
              Role & Permissions
            </DropdownMenuItem>
            <DropdownMenuItem className="cursor-pointer text-xs">
              <ShieldAlert className="mr-2 h-3.5 w-3.5 text-slate-500" />
              Audit Log History
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={handleLogout}
              className="cursor-pointer text-xs text-rose-600 focus:text-rose-600 focus:bg-rose-50"
            >
              <LogOut className="mr-2 h-3.5 w-3.5" />
              Sign Out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
