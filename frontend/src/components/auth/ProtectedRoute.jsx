import React from "react";
import { Navigate, Outlet } from "react-router-dom";
import { Loader2, Shield } from "lucide-react";
import { useAuthStore } from "../../store/authStore";

export function ProtectedRoute({ children }) {
  const { isAuthenticated, isInitializing } = useAuthStore();

  if (isInitializing) {
    return (
      <div className="flex h-screen w-screen flex-col items-center justify-center bg-slate-900 text-slate-100 p-4">
        <div className="flex flex-col items-center space-y-4 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600 font-bold shadow-md">
            <Shield className="h-6 w-6 text-white" />
          </div>
          <div className="flex items-center space-x-2 text-sm text-slate-300">
            <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
            <span className="font-medium">Checking session authentication...</span>
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children ? children : <Outlet />;
}
