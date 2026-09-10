import React from "react";
import { Navigate, createBrowserRouter } from "react-router-dom";
import { AppShell } from "../components/layout/AppShell";
import { ProtectedRoute } from "../components/auth/ProtectedRoute";
import { LoginPage } from "../pages/LoginPage";
import { DashboardPage } from "../pages/DashboardPage";
import { TendersPage } from "../pages/TendersPage";
import { TenderDetailsPage } from "../pages/TenderDetailsPage";
import { TenderRequirementsPage } from "../pages/TenderRequirementsPage";
import { TenderBidsPage } from "../pages/TenderBidsPage";
import { BidDetailsPage } from "../pages/BidDetailsPage";
import { DocumentsPage } from "../pages/DocumentsPage";
import { VerificationPage } from "../pages/VerificationPage";
import { CompliancePage } from "../pages/CompliancePage";
import { AuditPage } from "../pages/AuditPage";

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <AppShell />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: "dashboard",
        element: <DashboardPage />,
      },
      {
        path: "tenders",
        element: <TendersPage />,
      },
      {
        path: "tenders/:tenderId",
        element: <TenderDetailsPage />,
      },
      {
        path: "tenders/:tenderId/requirements",
        element: <TenderRequirementsPage />,
      },
      {
        path: "tenders/:tenderId/bids",
        element: <TenderBidsPage />,
      },
      {
        path: "bids/:bidSubmissionId",
        element: <BidDetailsPage />,
      },
      {
        path: "bids/:bidSubmissionId/documents",
        element: <DocumentsPage />,
      },
      {
        path: "bids/:bidSubmissionId/verification",
        element: <VerificationPage />,
      },
      {
        path: "bids/:bidSubmissionId/compliance",
        element: <CompliancePage />,
      },
      {
        path: "bids/:bidSubmissionId/audit",
        element: <AuditPage />,
      },
      {
        path: "audit-logs",
        element: <AuditPage />,
      },
      {
        path: "settings",
        element: <DashboardPage />,
      },
      {
        path: "*",
        element: <Navigate to="/dashboard" replace />,
      },
    ],
  },
]);
