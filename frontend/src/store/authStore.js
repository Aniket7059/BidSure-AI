import { create } from "zustand";
import { authApi } from "../features/auth/api";
import { queryClient } from "../lib/queryClient";

const TOKEN_KEY = "bidsure_auth_token";

export const useAuthStore = create((set, get) => ({
  user: null,
  accessToken: localStorage.getItem(TOKEN_KEY) || null,
  isAuthenticated: false,
  isInitializing: true,

  setAuth: (user, token) => {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
    }
    set({
      user,
      accessToken: token,
      isAuthenticated: true,
      isInitializing: false,
    });
  },

  setUser: (user) => {
    set({ user });
  },

  logout: () => {
    localStorage.removeItem(TOKEN_KEY);
    // Clear query cache to prevent user data leaks between sessions
    queryClient.clear();
    set({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isInitializing: false,
    });
  },

  initializeAuth: async () => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      set({
        user: null,
        accessToken: null,
        isAuthenticated: false,
        isInitializing: false,
      });
      return;
    }

    try {
      const user = await authApi.getCurrentUser();
      set({
        user,
        accessToken: token,
        isAuthenticated: true,
        isInitializing: false,
      });
    } catch (error) {
      // Token is expired or invalid
      localStorage.removeItem(TOKEN_KEY);
      set({
        user: null,
        accessToken: null,
        isAuthenticated: false,
        isInitializing: false,
      });
    }
  },
}));
