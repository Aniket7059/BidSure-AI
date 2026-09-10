import React, { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Shield, Lock, Mail, AlertCircle, ArrowRight, CheckCircle2, Eye, EyeOff, Loader2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { loginSchema } from "../features/auth/schemas";
import { authApi } from "../features/auth/api";
import { useAuthStore } from "../store/authStore";

export function LoginPage() {
  const navigate = useNavigate();
  const { setAuth, isAuthenticated } = useAuthStore();
  const [serverError, setServerError] = useState(null);
  const [showPassword, setShowPassword] = useState(false);

  // Auto-redirect if already logged in
  useEffect(() => {
    if (isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = async (data) => {
    setServerError(null);

    try {
      // Step 1: Login request to POST /auth/login
      const tokenData = await authApi.login({
        email: data.email,
        password: data.password,
      });

      if (!tokenData || !tokenData.access_token) {
        throw new Error("Invalid response format from server");
      }

      // Temporarily store token for Authorization header
      localStorage.setItem("bidsure_auth_token", tokenData.access_token);

      // Step 2: Retrieve authenticated user profile from GET /auth/me
      const userData = await authApi.getCurrentUser();

      // Step 3: Commit state to auth store & navigate
      setAuth(userData, tokenData.access_token);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      console.error("Login authentication error:", err);

      if (!err.response) {
        setServerError("Unable to connect to the server. Please verify backend server is running.");
      } else if (err.response.status === 401) {
        setServerError("Invalid email or password.");
      } else if (err.response.data?.detail) {
        const detail = err.response.data.detail;
        setServerError(typeof detail === "string" ? detail : "Authentication request failed.");
      } else {
        setServerError("An error occurred during authentication. Please try again.");
      }

      localStorage.removeItem("bidsure_auth_token");
    }
  };

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-slate-900 p-4 sm:p-6 lg:p-8">
      <div className="w-full max-w-md space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600 text-white font-bold shadow-md mb-2">
            <Shield className="h-6 w-6" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            BidSure AI
          </h1>
          <p className="text-xs text-slate-400 font-medium">
            AI-Powered Integrated Bid Compliance Verification Platform
          </p>
          <div className="pt-1">
            <Badge variant="outline" className="bg-slate-800/80 text-slate-300 border-slate-700 text-[10px]">
              Chennai Petroleum Corporation Limited (CPCL)
            </Badge>
          </div>
        </div>

        {/* Form Card */}
        <Card className="border-slate-800 bg-white shadow-xl">
          <CardHeader className="space-y-1 pb-4 text-center">
            <CardTitle className="text-lg font-semibold text-slate-900">
              Procurement Officer Authentication
            </CardTitle>
            <CardDescription className="text-xs text-slate-500">
              Enter your credentials to access the compliance portal
            </CardDescription>
          </CardHeader>
          <CardContent>
            {serverError && (
              <div className="mb-4 flex items-start gap-2.5 rounded-md border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
                <AlertCircle className="h-4 w-4 shrink-0 text-rose-600 mt-0.5" />
                <div className="flex-1">{serverError}</div>
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-700">
                  Officer Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
                  <Input
                    type="email"
                    placeholder="officer@cpcl.gov.in"
                    className="pl-9 text-xs"
                    autoComplete="email"
                    {...register("email")}
                  />
                </div>
                {errors.email && (
                  <p className="text-[11px] text-rose-600">{errors.email.message}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-700">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
                  <Input
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    className="pl-9 pr-9 text-xs"
                    autoComplete="current-password"
                    {...register("password")}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600 transition-colors"
                    title={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
                {errors.password && (
                  <p className="text-[11px] text-rose-600">{errors.password.message}</p>
                )}
              </div>

              <Button
                type="submit"
                className="w-full text-xs font-semibold h-9 bg-blue-600 hover:bg-blue-700"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    Signing in...
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    Sign In to Compliance Dashboard
                    <ArrowRight className="h-3.5 w-3.5" />
                  </span>
                )}
              </Button>
            </form>

            <div className="mt-6 pt-4 border-t border-slate-100 text-center">
              <div className="flex items-center justify-center gap-1.5 text-[11px] text-slate-500">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                <span>GeM Statutory Verification Engine Active</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Footer Security Notice */}
        <p className="text-center text-[11px] text-slate-400 max-w-xs mx-auto leading-relaxed">
          Authorized personnel only. All access, statutory lookups, and evaluation decisions are logged in an auditable trail.
        </p>
      </div>
    </div>
  );
}
