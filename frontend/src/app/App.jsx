import React, { useEffect } from "react";
import { RouterProvider } from "react-router-dom";
import { router } from "./routes";
import { AppProviders } from "./providers";
import { useAuthStore } from "../store/authStore";

export default function App() {
  useEffect(() => {
    // Restore authentication state on initial page load / refresh
    useAuthStore.getState().initializeAuth();
  }, []);

  return (
    <AppProviders>
      <RouterProvider router={router} />
    </AppProviders>
  );
}
