import React from "react";
import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { Sheet, SheetContent } from "../ui/sheet";
import { useUIStore } from "../../store/uiStore";

export function AppShell() {
  const { mobileSidebarOpen, setMobileSidebarOpen } = useUIStore();

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground antialiased">
      {/* Desktop Navigation Sidebar */}
      <div className="hidden lg:block shrink-0 h-full">
        <Sidebar isMobile={false} />
      </div>

      {/* Mobile Drawer Sheet */}
      <Sheet open={mobileSidebarOpen} onOpenChange={setMobileSidebarOpen}>
        <SheetContent side="left" className="p-0 w-72 bg-slate-900 border-slate-800">
          <Sidebar isMobile={true} />
        </SheetContent>
      </Sheet>

      {/* Main View Area */}
      <div className="flex flex-col flex-1 h-full min-w-0 overflow-hidden bg-white">
        <Topbar />
        <div className="flex-1 overflow-y-auto bg-white">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
