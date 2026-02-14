
import React from 'react';

export enum Status {
  New = 'New',
  Analyzing = 'Analyzing',
  InReview = 'In Review',
  Approved = 'Approved',
  Rejected = 'Rejected',
  Flagged = 'Flagged',
  Paid = 'Paid'
}

export enum RiskLevel {
  Low = 'Low',
  Medium = 'Medium',
  High = 'High',
  Critical = 'Critical'
}

export type PolicyCategory = 'Life' | 'Health' | 'Vehicle' | 'Property' | 'Travel';

export interface Policy {
  id: string;
  category: PolicyCategory;
  policyNumber: string;
  title: string;
  coverageAmount: number;
  premium: number;
  expiryDate: string;
  status: 'Active' | 'Expired' | 'Pending';
  features: string[];
  icon?: any;
}

export interface Document {
  id: string;
  name: string;
  type: 'PDF' | 'DOCX' | 'JPG' | 'PNG';
  size: string;
  date: string;
  summary?: string;
  category?: 'Legal' | 'Evidence' | 'Medical' | 'Financial' | 'Other';
  extractedEntities?: Record<string, string>;
  userEmail?: string;
  userId?: string;
  policyNumber?: string;
}

export interface AiAnalysis {
  score: number;
  reasoning: string;
  recommendations: string[];
  rulesChecked?: Array<{
    rule: string;
    result: string;
    impact: string;
    detail: string;
  }>;
}

export interface Claim {
  id: string;
  policyNumber: string;
  claimant: string;
  type: PolicyCategory | string;
  amount: number;
  status: Status;
  riskScore: number | null;  // Nullable during fraud analysis
  riskLevel: RiskLevel;
  date: string;
  description: string;
  documents?: Document[];
  assigneeId?: string;
  assignmentNote?: string;
  aiAnalysis?: AiAnalysis;
  ipAddress?: string;
  phoneNumber?: string;
  deviceFingerprint?: string;

  // Fraud detection fields
  fraudStatus?: 'PENDING' | 'ANALYZING' | 'COMPLETED' | 'FAILED';
  fraudScore?: number;
  fraudRiskLevel?: string;
  fraudDecision?: string;
  fraudIndicators?: string[];
  fraudReasoning?: string;
  vehicleInfo?: {
    makeModel: string;
    regNumber: string;
    vin: string;
    odometer: string;
    policeReportFiled: boolean;
    policeReportNo?: string;
    location?: string;
    time?: string;
    incidentType?: string;
  };
  healthInfo?: {
    dob: string;
    patientName: string;
    relationship: string;
    hospitalName: string;
    hospitalAddress: string;
    admissionDate: string;
    dischargeDate: string;
    doctorName: string;
    diagnosis: string;
    treatment: string;
    surgeryPerformed: boolean;
  };
  lifeInfo?: {
    deceasedName: string;
    deceasedDob: string;
    dateOfDeath: string;
    causeOfDeath: string;
    nomineeName: string;
    nomineeRelationship: string;
    nomineeContact: string;
    bankDetails: string;
    sumAssured: number;
    policyStartDate: string;
  };
  propertyInfo?: {
    address: string;
    incidentType: string;
    locationOfDamage: string;
    fireDeptInvolved: boolean;
    reportNumber?: string;
  };
  itemizedLoss?: { item: string; cost: number }[];
}

export interface ChartData {
  name: string;
  value: number;
  [key: string]: any;
}

export type UserRole = 'Admin' | 'User' | null;

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  avatar: string;
  notificationsEnabled?: boolean;
}

export interface NavItem {
  id: string;
  label: string;
  icon: React.ReactNode;
}

export interface FraudAlert {
  id: string;
  severity: 'High' | 'Medium' | 'Low';
  type: string;
  description: string;
  relatedClaims: string[];
  date: string;
}

export interface SystemSettings {
  notifications: boolean;
  autoApproveThreshold: number;
  fraudSensitivity: number;
  theme: 'system' | 'light' | 'dark';
}