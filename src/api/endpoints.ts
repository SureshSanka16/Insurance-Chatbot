/**
 * API endpoint functions for backend communication
 */

import apiClient, { setAuthToken, clearAuthToken } from "./client";
import type { Claim, Status, User } from "../../types";

// ============================================================================
// Authentication
// ============================================================================

export interface LoginRequest {
  username: string; // email
  password: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
  role?: "User" | "Admin";
  avatar?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

/**
 * Login user and store JWT token
 */
export const login = async (email: string, password: string): Promise<User> => {
  // FastAPI OAuth2 expects form data with 'username' field
  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);

  const response = await apiClient.post<AuthResponse>("/auth/login", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

  // Store token
  setAuthToken(response.data.access_token);

  // Get current user details
  const user = await getCurrentUser();

  // Store user in localStorage
  localStorage.setItem("user", JSON.stringify(user));

  return transformUser(user);
};

/**
 * Register new user
 */
export const register = async (userData: RegisterRequest): Promise<User> => {
  const response = await apiClient.post<User>("/auth/register", userData);
  return transformUser(response.data);
};

/**
 * Get current authenticated user
 */
export const getCurrentUser = async (): Promise<User> => {
  const response = await apiClient.get<User>("/me");
  return transformUser(response.data);
};

/**
 * Logout user
 */
export const logout = () => {
  clearAuthToken();
  window.location.href = "/login";
};

/**
 * Update user profile
 */
export const updateUserProfile = async (data: Partial<User>): Promise<User> => {
  const payload = {
    ...data,
    notifications_enabled: data.notificationsEnabled,
  };
  const response = await apiClient.patch<User>("/me", payload);
  return transformUser(response.data);
};

// ============================================================================
// Data Transformation Helpers (Backend snake_case -> Frontend camelCase)
// ============================================================================

function transformUser(data: any): any {
  return {
    ...data,
    notificationsEnabled: data.notifications_enabled,
  };
}

const transformPolicy = (data: any): any => ({
  ...data,
  policyNumber: data.policy_number,
  expiryDate: data.expiry_date,
  coverageAmount: data.coverage_amount,
  // features is already array of strings
});

const transformDocument = (data: any): any => ({
  ...data,
  userEmail: data.user_email || data.userEmail,
  userId: data.user_id || data.userId,
  policyNumber: data.policy_number || data.policyNumber,
});

const transformClaim = (data: any): any => {
  if (!data) return null;

  // The backend stores type-specific info inside a `polymorphic_data` JSON column.
  // Extract nested fields so the frontend can access them at the top level.
  const poly = data.polymorphic_data || {};

  // Build aiAnalysis with fraud reasoning if available
  const aiAnalysis = data.ai_analysis || data.aiAnalysis || {};
  if (data.fraud_reasoning || data.fraudReasoning) {
    aiAnalysis.reasoning = data.fraud_reasoning || data.fraudReasoning;
  }
  if (data.fraud_indicators || data.fraudIndicators) {
    aiAnalysis.fraudIndicators = data.fraud_indicators || data.fraudIndicators;
  }
  // Include rules_checked if available from backend
  if (data.rules_checked) {
    aiAnalysis.rulesChecked = data.rules_checked;
  }

  return {
    ...data,
    policyNumber: data.policy_number || data.policyNumber,
    claimant: data.claimant_name || data.claimant,
    riskScore: data.risk_score ?? data.riskScore,
    riskLevel: data.risk_level || data.riskLevel,
    date: data.submission_date || data.date,
    vehicleInfo: data.vehicle_info || data.vehicleInfo || poly.vehicleInfo,
    healthInfo: data.health_info || data.healthInfo || poly.healthInfo,
    lifeInfo: data.life_info || data.lifeInfo || poly.lifeInfo,
    propertyInfo: data.property_info || data.propertyInfo || poly.propertyInfo,
    itemizedLoss: data.itemized_loss || data.itemizedLoss || poly.itemizedLoss,
    aiAnalysis: Object.keys(aiAnalysis).length > 0 ? aiAnalysis : undefined,
    documents: (data.documents || []).map(transformDocument),

    // Fraud detection fields
    fraudStatus: data.fraud_status || data.fraudStatus,
    fraudScore: data.fraud_score != null ? data.fraud_score * 100 : null, // Convert 0-1 to 0-100
    fraudRiskLevel: data.fraud_risk_level || data.fraudRiskLevel,
    fraudDecision: data.fraud_decision || data.fraudDecision,
    fraudIndicators: data.fraud_indicators || data.fraudIndicators,
    fraudReasoning: data.fraud_reasoning || data.fraudReasoning,
  };
};

// ============================================================================
// Claims Management
// ============================================================================

export interface ClaimFilters {
  status?: Status;
  min_risk_score?: number;
  skip?: number;
  limit?: number;
}

/**
 * Fetch all claims (Admin) or User claims (Filtered by backend if needed)
 */
export const fetchClaims = async (filters?: {
  status?: string;
  min_risk_score?: number;
  skip?: number;
  limit?: number;
}): Promise<any[]> => {
  const params = new URLSearchParams();

  if (filters?.status) params.append("status", filters.status);
  if (filters?.min_risk_score !== undefined)
    params.append("min_risk_score", filters.min_risk_score.toString());
  if (filters?.skip !== undefined)
    params.append("skip", filters.skip.toString());
  if (filters?.limit !== undefined)
    params.append("limit", filters.limit.toString());

  const response = await apiClient.get<any[]>(`/claims?${params.toString()}`);
  return response.data.map(transformClaim);
};

/**
 * Fetch single claim by ID
 */
export const fetchClaimDetails = async (id: string): Promise<any> => {
  const response = await apiClient.get<any>(`/claims/${id}`);
  return transformClaim(response.data);
};

/**
 * Create new claim
 */
export const createClaim = async (claimData: any): Promise<any> => {
  const response = await apiClient.post<any>("/claims", claimData);
  return transformClaim(response.data);
};

/**
 * Update claim status
 */
export const updateClaimStatus = async (
  id: string,
  status: Status,
): Promise<any> => {
  const response = await apiClient.patch<any>(`/claims/${id}/status`, {
    status,
  });
  return transformClaim(response.data);
};

/**
 * Finalize claim submission - triggers fraud detection
 * Call this after all documents are uploaded
 */
export const finalizeClaim = async (claimId: string): Promise<any> => {
  const response = await apiClient.post<any>(`/claims/${claimId}/finalize`);
  return response.data;
};

// ============================================================================
// AI Features
// ============================================================================

export interface RiskAnalysisResponse {
  claim_id: string;
  risk_score: number;
  risk_level: string;
  reasoning: string;
  fraud_indicators?: string[];
  recommendations?: string;
  rules_checked?: Array<{
    rule: string;
    result: string;
    impact: string;
    detail: string;
  }>;
}

/**
 * Run AI risk analysis on a claim
 */
export const runAiScan = async (
  claimId: string,
): Promise<RiskAnalysisResponse> => {
  const response = await apiClient.post<RiskAnalysisResponse>(
    `/ai/claims/${claimId}/analyze`,
  );
  return response.data;
};

export interface CopilotRequest {
  message: string;
  active_category?: string;
  claim_id?: string;
  policy_id?: string;
  policy_number?: string;
}

export interface CopilotSource {
  source: string;
  section: string;
  policy_number: string;
}

export interface CopilotResponse {
  response: string;
  sources?: CopilotSource[];
  rag_context_used?: boolean;
}

/**
 * Chat with RAG-augmented AI copilot.
 *
 * The backend uses the JWT token to extract user_id (secure, server-side)
 * and the context IDs to scope the RAG retrieval to the user's active
 * policy / claim.
 */
export const chatWithCopilot = async (
  message: string,
  context?: {
    activeCategory?: string;
    claimId?: string;
    policyId?: string;
    policyNumber?: string;
  },
): Promise<CopilotResponse> => {
  const payload: CopilotRequest = {
    message,
    active_category: context?.activeCategory,
    claim_id: context?.claimId,
    policy_id: context?.policyId,
    policy_number: context?.policyNumber,
  };

  const response = await apiClient.post<CopilotResponse>(
    "/ai/copilot/chat",
    payload,
  );
  return response.data;
};

// ============================================================================
// Policies
// ============================================================================

export interface PolicyCreate {
  category: string;
  title: string;
  coverage_amount: number;
  premium: number;
  status?: string;
  features?: string[];
}

/**
 * Fetch all policies for authenticated user
 */
export const fetchPolicies = async (): Promise<any[]> => {
  const response = await apiClient.get<any[]>("/policies");
  return response.data.map(transformPolicy);
};

/**
 * Create new policy
 */
export const createPolicy = async (policyData: PolicyCreate): Promise<any> => {
  const response = await apiClient.post<any>("/policies", policyData);
  return transformPolicy(response.data);
};

/**
 * Get policy by ID
 */
export const fetchPolicyDetails = async (id: string): Promise<any> => {
  const response = await apiClient.get<any>(`/policies/${id}`);
  return transformPolicy(response.data);
};

/**
 * Update policy status (Admin only)
 */
export const updatePolicyStatus = async (
  policyId: string,
  status: string,
): Promise<any> => {
  const response = await apiClient.patch<any>(`/policies/${policyId}`, {
    status,
  });
  return transformPolicy(response.data);
};

/**
 * Upload document to claim
 */
export const uploadDocument = async (
  claimId: string,
  file: File,
  documentType: string,
): Promise<any> => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post(
    `/claims/${claimId}/documents?document_type=${encodeURIComponent(documentType)}`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    },
  );

  return response.data;
};

/**
 * Fetch all documents (Documents Hub). Admin: all; User: own + claim-linked.
 */
export const fetchDocuments = async (): Promise<any[]> => {
  const response = await apiClient.get<any[]>("/documents");
  return response.data;
};

/**
 * Fetch all documents for a claim
 */
export const fetchClaimDocuments = async (claimId: string): Promise<any[]> => {
  const response = await apiClient.get<any[]>(`/claims/${claimId}/documents`);
  return response.data;
};

/**
 * Download/view a specific document
 */
export const downloadDocument = async (documentId: string): Promise<Blob> => {
  const response = await apiClient.get(`/documents/${documentId}`, {
    responseType: "blob",
  });
  return response.data;
};
