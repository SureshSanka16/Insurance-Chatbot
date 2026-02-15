/**
 * Axios client configuration for API requests
 */

import axios, {
  AxiosInstance,
  InternalAxiosRequestConfig,
  AxiosResponse,
} from "axios";

// API base URL - match CORS configuration
const BASE_URL = "http://localhost:8000";

// Create Axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor - attach JWT token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Get token from localStorage
    const token = localStorage.getItem("access_token");

    // Attach token to Authorization header if it exists
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// Response interceptor - handle errors
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Return response data directly
    return response;
  },
  (error) => {
    // Handle 401 Unauthorized - redirect to login
    if (error.response?.status === 401) {
      // Clear token
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");

      // Redirect to login (you can customize this based on your routing)
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }

    // Handle 403 Forbidden
    if (error.response?.status === 403) {
      console.error("Permission denied:", error.response.data);
    }

    // Handle 500 Internal Server Error
    if (error.response?.status === 500) {
      console.error("Server error:", error.response.data);
    }

    return Promise.reject(error);
  },
);

// Helper function to set token
export const setAuthToken = (token: string) => {
  localStorage.setItem("access_token", token);
};

// Helper function to clear token
export const clearAuthToken = () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("user");
};

// Helper function to get token
export const getAuthToken = (): string | null => {
  return localStorage.getItem("access_token");
};

export default apiClient;
