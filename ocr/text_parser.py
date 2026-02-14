"""
Text Parser Module
Converts OCR-extracted text into structured claim JSON

Uses:
- Regex patterns for field extraction
- NLP for entity recognition
- Rule-based parsing for claim forms
"""

import re
from datetime import datetime
from typing import Dict, Optional, List
import json


class ClaimTextParser:
    """
    Parse OCR-extracted text into structured claim JSON
    
    Handles various claim form formats and extracts:
    - Patient information
    - Hospital details
    - Diagnosis and treatment
    - Financial information
    - Dates
    """
    
    def __init__(self):
        """Initialize parser with regex patterns"""
        
        # Compile regex patterns for common fields
        self.patterns = {
            'patient_name': [
                r'PATIENT\s*NAME\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
                r'NAME\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
                r'Name\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            ],
            'policy_number': [
                r'POLICY\s*(?:NUMBER|NO|#)\s*:?\s*([A-Z0-9-]+)',
                r'Policy\s*(?:Number|No)\s*:?\s*([A-Z0-9-]+)',
                r'IL-(?:778|[0-9]{3})-(?:[0-9]+)',
            ],
            'hospital_name': [
                r'HOSPITAL\s*NAME\s*:?\s*([A-Z][\w\s]+(?:Hospital|Medical Center|Healthcare|Clinic))',
                r'(?:Hospital|Medical Center|Healthcare|Clinic)\s*:?\s*([A-Z][\w\s]+)',
            ],
            'diagnosis': [
                r'DIAGNOSIS\s*:?\s*(.+?)(?:\n|TREATMENT|Treatment)',
                r'Diagnosis\s*:?\s*(.+?)(?:\n|$)',
            ],
            'treatment': [
                r'TREATMENT\s*(?:PROVIDED)?\s*:?\s*(.+?)(?:\n|Surgery)',
                r'Treatment\s*:?\s*(.+?)(?:\n|$)',
                r'(?:Surgery|Procedure)\s*:?\s*(.+?)(?:\n|$)',
            ],
            'claim_amount': [
                r'TOTAL\s*CLAIMED?\s*:?\s*\$?₹?\s*([0-9,]+)',
                r'Total\s*(?:Claimed|Amount)\s*:?\s*\$?₹?\s*([0-9,]+)',
                r'ESTIMATED\s*COST\s*:?\s*\$?₹?\s*([0-9,]+)',
            ],
            'room_rent': [
                r'(?:Hospital\s*)?Room\s*\(([0-9]+)\s*Days?\)',
                r'Room\s*Rent\s*(?:per\s*day)?\s*:?\s*\$?₹?\s*([0-9,]+)',
            ],
            'admission_date': [
                r'ADMISSION\s*DATE\s*:?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})',
                r'Admission\s*Date\s*:?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})',
                r'ADMITTED\s*:?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})',
            ],
            'discharge_date': [
                r'DISCHARGE\s*DATE\s*:?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})',
                r'Discharge\s*Date\s*:?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})',
            ],
            'doctor_name': [
                r'DOCTOR\s*NAME\s*:?\s*Dr\.\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
                r'Dr\.\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            ],
            'invoice_number': [
                r'INVOICE\s*(?:NO|NUMBER|#)\s*:?\s*([A-Z0-9-]+)',
                r'Bill\s*No\s*:?\s*([A-Z0-9-]+)',
            ],
        }
    
    def parse_text_to_claim(self, text: str, policy_id: str = None) -> Dict:
        """
        Main parsing function: Convert OCR text to structured claim JSON
        
        Args:
            text: OCR-extracted text
            policy_id: Policy ID to use (if not found in text)
            
        Returns:
            Structured claim dictionary
        """
        
        # Handle None or empty text
        if text is None:
            text = ""
        
        print("\n" + "="*60)
        print("PARSING OCR TEXT TO STRUCTURED CLAIM")
        print("="*60)
        
        claim = {
            "claim_id": self._generate_claim_id(),
            "policy_id": policy_id or self._extract_field(text, 'policy_number'),
            "patient_name": self._extract_field(text, 'patient_name'),
            "hospital_name": self._extract_field(text, 'hospital_name'),
            "diagnosis": self._extract_field(text, 'diagnosis'),
            "treatment": self._extract_field(text, 'treatment'),
            "claim_amount": self._extract_amount(text, 'claim_amount'),
            "room_rent_per_day": self._extract_amount(text, 'room_rent'),
            "admission_date": self._extract_field(text, 'admission_date'),
            "discharge_date": self._extract_field(text, 'discharge_date'),
            "doctor_name": self._extract_field(text, 'doctor_name'),
            "invoice_number": self._extract_field(text, 'invoice_number'),
            "claim_submission_date": datetime.now().strftime('%Y-%m-%d'),
        }
        
        # Calculate derived fields
        claim = self._add_derived_fields(claim)
        
        # Add default values for missing fields
        claim = self._add_defaults(claim)
        
        print("\n✓ Claim parsed successfully")
        return claim
    
    def _extract_field(self, text: str, field_name: str) -> Optional[str]:
        """
        Extract a field using regex patterns
        
        Args:
            text: Text to search
            field_name: Name of field to extract
            
        Returns:
            Extracted value or None
        """
        if not text or field_name not in self.patterns:
            return None
        
        for pattern in self.patterns[field_name]:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                print(f"  ✓ Extracted {field_name}: {value}")
                return value
        
        print(f"  ✗ Could not extract {field_name}")
        return None
    
    def _extract_amount(self, text: str, field_name: str) -> float:
        """
        Extract monetary amount and convert to float
        
        Args:
            text: Text to search
            field_name: Name of amount field
            
        Returns:
            Extracted amount as float
        """
        value = self._extract_field(text, field_name)
        if value:
            # Remove commas and convert to float
            try:
                amount = float(value.replace(',', ''))
                return amount
            except:
                pass
        
        return 0.0
    
    def _generate_claim_id(self) -> str:
        """Generate unique claim ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"CLM-OCR-{timestamp}"
    
    def _add_derived_fields(self, claim: Dict) -> Dict:
        """
        Add derived fields based on extracted data
        
        Args:
            claim: Partial claim dictionary
            
        Returns:
            Claim with derived fields added
        """
        
        # Calculate policy start date (estimate)
        if claim.get('admission_date'):
            try:
                admission = datetime.strptime(claim['admission_date'], '%Y-%m-%d')
                # Assume policy started 1 year before admission
                policy_start = admission.replace(year=admission.year - 1)
                claim['policy_start_date'] = policy_start.strftime('%Y-%m-%d')
            except:
                pass
        
        # Calculate claim date (use discharge date or current date)
        if claim.get('discharge_date'):
            claim['claim_date'] = claim['discharge_date']
        else:
            claim['claim_date'] = datetime.now().strftime('%Y-%m-%d')
        
        return claim
    
    def _add_defaults(self, claim: Dict) -> Dict:
        """
        Add default values for fields required by ML models
        
        Args:
            claim: Partial claim dictionary
            
        Returns:
            Claim with defaults added
        """
        
        defaults = {
            "num_previous_claims": 0,
            "days_since_last_claim": 365,
            "pre_existing_condition": False,
            "duplicate_invoice": False,
            "is_accident": False,
            "policy_start_date": "2023-01-01",  # Default if not extracted
            "diagnosis": "Unknown",  # Ensure diagnosis is never None
            "treatment": "Unknown",  # Ensure treatment is never None
            "hospital_name": "Unknown Hospital",  # Ensure hospital_name is never None
            "patient_name": "Unknown Patient",  # Ensure patient_name is never None
        }
        
        for key, default_value in defaults.items():
            if key not in claim or claim[key] is None or claim[key] == '':
                claim[key] = default_value
        
        return claim
    
    def parse_itemized_expenses(self, text: str) -> List[Dict]:
        """
        Extract itemized medical expenses from bill
        
        Args:
            text: OCR text from hospital bill
            
        Returns:
            List of expense items
        """
        
        expenses = []
        
        # Common expense categories
        categories = [
            'Consultation', 'Surgery', 'Room', 'Medication', 
            'Diagnostic', 'Laboratory', 'ICU', 'Ambulance'
        ]
        
        for category in categories:
            # Look for pattern: Category ... $amount
            pattern = rf'{category}\s+(?:Charges?|Fee)?\s*:?\s*\$?₹?\s*([0-9,]+)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = float(match.group(1).replace(',', ''))
                expenses.append({
                    "item": category,
                    "amount": amount
                })
        
        return expenses
    
    def validate_extracted_claim(self, claim: Dict) -> tuple[bool, List[str]]:
        """
        Validate extracted claim has required fields
        
        Args:
            claim: Parsed claim dictionary
            
        Returns:
            (is_valid, list_of_missing_fields)
        """
        
        required_fields = [
            'claim_amount',
            'hospital_name',
            'diagnosis',
            'treatment',
        ]
        
        missing = []
        for field in required_fields:
            if not claim.get(field) or claim[field] == 0:
                missing.append(field)
        
        is_valid = len(missing) == 0
        
        if is_valid:
            print("\n✓ All required fields extracted")
        else:
            print(f"\n⚠ Missing required fields: {', '.join(missing)}")
        
        return is_valid, missing


# Enhanced parser using NLP (optional, requires spacy)
class NLPClaimParser:
    """
    Advanced claim parser using Natural Language Processing
    
    Uses spaCy for entity recognition and extraction
    """
    
    def __init__(self):
        """Initialize NLP parser"""
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            print("✓ NLP parser loaded")
        except:
            print("⚠ spaCy not available, using basic parser")
            self.nlp = None
    
    def extract_entities(self, text: str) -> Dict:
        """
        Extract named entities from text
        
        Args:
            text: OCR text
            
        Returns:
            Dictionary of extracted entities
        """
        if not self.nlp:
            return {}
        
        doc = self.nlp(text)
        
        entities = {
            'persons': [],
            'organizations': [],
            'dates': [],
            'money': [],
        }
        
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                entities['persons'].append(ent.text)
            elif ent.label_ == 'ORG':
                entities['organizations'].append(ent.text)
            elif ent.label_ == 'DATE':
                entities['dates'].append(ent.text)
            elif ent.label_ == 'MONEY':
                entities['money'].append(ent.text)
        
        return entities


if __name__ == "__main__":
    # Test parser
    sample_ocr_text = """
    HEALTH INSURANCE CLAIM FORM
    
    PATIENT NAME: Sarah Williams
    POLICY NUMBER: IL-778-21
    HOSPITAL NAME: CityCare Medical Center
    
    ADMISSION DATE: 2024-10-28
    DISCHARGE DATE: 2024-10-31
    DOCTOR NAME: Dr. Emily Carter
    
    DIAGNOSIS: Acute Appendicitis
    TREATMENT PROVIDED: Laparoscopic Appendectomy
    
    ITEMIZED MEDICAL EXPENSES:
    Consultation Charges: $500
    Surgery Charges: $6,000
    Hospital Room (3 Days): $1,500
    Medication: $800
    Diagnostic Tests: $700
    
    TOTAL CLAIMED: $9,500
    """
    
    print("="*60)
    print("TESTING CLAIM TEXT PARSER")
    print("="*60)
    
    parser = ClaimTextParser()
    claim = parser.parse_text_to_claim(sample_ocr_text)
    
    print("\n" + "="*60)
    print("PARSED CLAIM JSON")
    print("="*60)
    print(json.dumps(claim, indent=2))
    
    # Validate
    is_valid, missing = parser.validate_extracted_claim(claim)
    print(f"\nValidation: {'✓ PASS' if is_valid else '✗ FAIL'}")
