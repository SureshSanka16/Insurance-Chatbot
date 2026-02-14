import { FraudAlert } from '../types';

export const MOCK_ALERTS: FraudAlert[] = [
  {
    id: 'ALT-001',
    severity: 'High',
    type: 'Shared IP Address',
    description: 'Multiple claims originated from the same IP address (192.168.1.55) within 48 hours.',
    relatedClaims: ['CLM-2024-001', 'CLM-2024-002', 'CLM-2024-005'],
    date: '2024-10-25'
  },
  {
    id: 'ALT-002',
    severity: 'Medium',
    type: 'Recycled Phone Number',
    description: 'Claimant contact number matches a previous high-risk claim.',
    relatedClaims: ['CLM-2024-001', 'CLM-2024-003'],
    date: '2024-10-24'
  }
];