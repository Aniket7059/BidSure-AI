import { api } from "../../services/api";

export const authApi = {
  /**
   * Authenticates user against POST /auth/login
   * @param {{ email: string, password: string }} credentials
   * @returns {Promise<{ access_token: string, token_type: string }>}
   */
  login: async (credentials) => {
    const response = await api.post("/auth/login", {
      email: credentials.email,
      password: credentials.password,
    });
    return response.data;
  },

  /**
   * Fetches current authenticated user profile from GET /auth/me
   * @returns {Promise<{ id: number, full_name: string, email: string, role: string }>}
   */
  getCurrentUser: async () => {
    const response = await api.get("/auth/me");
    return response.data;
  },
};
