import { Policy } from '../types';

export const MOCK_POLICIES: Policy[] = [
  {
    id: 'POL-LIFE-001',
    category: 'Life',
    policyNumber: 'LF-992-11',
    title: 'Platinum Life L-100',
    coverageAmount: 1000000,
    premium: 120,
    expiryDate: '2030-12-31',
    status: 'Active',
    features: ['Critical Illness', 'Disability Rider']
  },
  {
    id: 'POL-HEALTH-002',
    category: 'Health',
    policyNumber: 'HL-221-44',
    title: 'Select Health H-200',
    coverageAmount: 500000,
    premium: 350,
    expiryDate: '2025-06-15',
    status: 'Active',
    features: ['Dental', 'Vision', 'Maternity']
  },
  {
    id: 'POL-VEHICLE-003',
    category: 'Vehicle',
    policyNumber: 'VH-882-99',
    title: 'Elite Vehicle V-300',
    coverageAmount: 65000,
    premium: 180,
    expiryDate: '2024-11-20',
    status: 'Active',
    features: ['Zero Depreciation', 'Roadside Assist']
  },
  {
    id: 'POL-PROP-004',
    category: 'Property',
    policyNumber: 'PR-112-33',
    title: 'Premier Housing P-400',
    coverageAmount: 850000,
    premium: 1200,
    expiryDate: '2025-01-01',
    status: 'Active',
    features: ['Fire', 'Theft', 'Natural Disaster']
  }
];