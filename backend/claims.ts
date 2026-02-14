
import { Claim, Status, RiskLevel } from '../types';
import { MOCK_DOCUMENTS } from './documents';

export const MOCK_CLAIMS: Claim[] = [
  {
    id: 'CLM-2024-001',
    policyNumber: 'VH-882-99',
    claimant: 'James Doe',
    type: 'Vehicle',
    amount: 16500,
    status: Status.New,
    riskScore: 25,
    riskLevel: RiskLevel.Low,
    date: '2024-10-25',
    description: 'Head-on collision occurred at an intersection resulting in airbag deployment and severe front-end structural damage. Vehicle was rendered inoperable and towed from scene.',
    documents: [MOCK_DOCUMENTS[0], MOCK_DOCUMENTS[2], MOCK_DOCUMENTS[5]],
    ipAddress: '192.168.1.55',
    phoneNumber: '+1-555-123-4567',
    vehicleInfo: {
      makeModel: 'Toyota Camry 2022',
      regNumber: 'NY-AB-1234',
      vin: '1HGCM82633A123456',
      odometer: '45,000 miles',
      policeReportFiled: true,
      policeReportNo: 'PR-789456',
      location: 'Warehouse B Intersection, NY',
      time: '18:30',
      incidentType: 'Head-on Collision'
    },
    itemizedLoss: [
      { item: 'Structural Repairs', cost: 5000 },
      { item: 'Front Bumper Replacement', cost: 2000 },
      { item: 'Airbag Replacement', cost: 2000 },
      { item: 'Inventory (Electronics)', cost: 7500 }
    ]
  },
  {
    id: 'HLTH-2024-014',
    policyNumber: 'HL-778-21',
    claimant: 'Sarah Williams',
    type: 'Health',
    amount: 9500,
    status: Status.New,
    riskScore: 12,
    riskLevel: RiskLevel.Low,
    date: '2024-11-02',
    description: 'Patient admitted for acute appendicitis symptoms. Laparoscopic appendectomy performed.',
    documents: [MOCK_DOCUMENTS[1]],
    ipAddress: '10.0.0.42',
    phoneNumber: '+1-555-456-7890',
    healthInfo: {
      dob: '1995-04-18',
      patientName: 'Sarah Williams',
      relationship: 'Self',
      hospitalName: 'CityCare Medical Center',
      hospitalAddress: '220 Madison Ave, NY',
      admissionDate: '2024-10-28',
      dischargeDate: '2024-10-31',
      doctorName: 'Dr. Emily Carter',
      diagnosis: 'Acute Appendicitis',
      treatment: 'Laparoscopic Appendectomy',
      surgeryPerformed: true
    },
    itemizedLoss: [
      { item: 'Consultation Charges', cost: 500 },
      { item: 'Surgery Charges', cost: 6000 },
      { item: 'Hospital Room (3 Days)', cost: 1500 },
      { item: 'Medication', cost: 800 },
      { item: 'Diagnostic Tests', cost: 700 }
    ]
  },
  {
    id: 'LIFE-2024-009',
    policyNumber: 'LF-554-11',
    claimant: 'Laura Williams',
    type: 'Life',
    amount: 250000,
    status: Status.InReview,
    riskScore: 60,
    riskLevel: RiskLevel.Medium,
    date: '2024-10-30',
    description: 'Death claim for Robert Williams due to sudden cardiac arrest.',
    documents: [MOCK_DOCUMENTS[4]],
    ipAddress: '192.168.1.112',
    phoneNumber: '+1-555-222-8899',
    lifeInfo: {
      deceasedName: 'Robert Williams',
      deceasedDob: '1970-02-10',
      dateOfDeath: '2024-10-15',
      causeOfDeath: 'Cardiac Arrest',
      nomineeName: 'Laura Williams',
      nomineeRelationship: 'Spouse',
      nomineeContact: '+1-555-222-8899',
      bankDetails: 'XXXX-XXXX-3456',
      sumAssured: 250000,
      policyStartDate: '2015-05-20'
    }
  },
  {
    id: 'HOME-2024-022',
    policyNumber: 'HM-993-45',
    claimant: 'Daniel Harper',
    type: 'Property',
    amount: 11000,
    status: Status.New,
    riskScore: 98,
    riskLevel: RiskLevel.Critical,
    date: '2024-11-01',
    description: 'Short circuit caused fire outbreak in kitchen resulting in cabinet damage, appliance destruction, and smoke damage to adjacent rooms.',
    documents: [MOCK_DOCUMENTS[3]],
    ipAddress: '192.168.1.55',
    phoneNumber: '+1-555-999-1212',
    propertyInfo: {
      address: '78 Sunset Boulevard, NY',
      incidentType: 'Electrical Fire',
      locationOfDamage: 'Kitchen Area',
      fireDeptInvolved: true,
      reportNumber: 'FD-22345'
    },
    itemizedLoss: [
      { item: 'Kitchen Cabinets', cost: 4000 },
      { item: 'Refrigerator', cost: 1800 },
      { item: 'Electrical Wiring Repairs', cost: 2500 },
      { item: 'Wall Repainting', cost: 1200 },
      { item: 'Smoke Cleanup', cost: 1500 }
    ]
  }
];