"""
OCR Claim Processor - Complete Pipeline
Orchestrates: OCR → Parsing → Feature Engineering → ML Prediction → Agent Workflow

This is the main entry point for processing claims from images
"""

from typing import Dict, List, Union
import json
from pathlib import Path

from ocr.trocr_extractor import TrOCRExtractor, get_ocr_extractor
from ocr.text_parser import ClaimTextParser
from src.agent import ClaimsAgent


class OCRClaimProcessor:
    """
    Complete end-to-end OCR claim processing pipeline
    
    Workflow:
    1. OCR Extraction - Extract text from images
    2. Text Parsing - Convert text to structured JSON
    3. Feature Engineering - Generate ML features
    4. ML Prediction - Fraud + Anomaly detection
    5. Agent Workflow - Policy validation + Risk assessment
    6. Decision - Final claim decision with explanation
    """
    
    def __init__(self, 
                 ocr_method: str = "trocr",
                 policy_path: str = 'config/policy.json',
                 fraud_model_path: str = 'models/fraud_model.pkl',
                 anomaly_model_path: str = 'models/anomaly_model.pkl',
                 policy_doc_path: str = 'config/policy_clauses.txt'):
        """
        Initialize OCR Claim Processor
        
        Args:
            ocr_method: "trocr" or "easyocr"
            policy_path: Path to policy configuration
            fraud_model_path: Path to fraud detection model
            anomaly_model_path: Path to anomaly detection model
            policy_doc_path: Path to policy documentation
        """
        
        print("="*70)
        print("INITIALIZING OCR CLAIM PROCESSOR")
        print("="*70)
        
        # Initialize components
        print("\n1. Loading OCR Engine...")
        try:
            self.ocr_extractor = get_ocr_extractor(ocr_method)
        except Exception as e:
            print(f"   ⚠ OCR initialization failed: {e}")
            print("   Continuing without OCR (manual JSON input required)")
            self.ocr_extractor = None
        
        print("\n2. Loading Text Parser...")
        self.text_parser = ClaimTextParser()
        print("   ✓ Text parser ready")
        
        print("\n3. Loading Claims Agent...")
        try:
            self.agent = ClaimsAgent(
                policy_path=policy_path,
                model_path=fraud_model_path,
                anomaly_model_path=anomaly_model_path,
                policy_doc_path=policy_doc_path
            )
        except Exception as e:
            print(f"   ✗ Agent initialization failed: {e}")
            self.agent = None
        
        print("\n" + "="*70)
        print("✓ OCR CLAIM PROCESSOR READY")
        print("="*70)
    
    def process_claim_from_images(self, 
                                   claim_image_path: str,
                                   invoice_image_path: str = None,
                                   policy_id: str = None) -> Dict:
        """
        Process claim from images (main entry point)
        
        Args:
            claim_image_path: Path to claim form image
            invoice_image_path: Path to hospital invoice image (optional)
            policy_id: Policy ID to use
            
        Returns:
            Complete claim processing result
        """
        
        print("\n" + "="*70)
        print("PROCESSING CLAIM FROM IMAGES")
        print("="*70)
        
        # Step 1: OCR Extraction
        print("\n📷 STEP 1: OCR TEXT EXTRACTION")
        print("-" * 70)
        
        all_text = ""
        
        if self.ocr_extractor:
            # Extract from claim form
            print(f"Extracting text from: {claim_image_path}")
            claim_text = self.ocr_extractor.extract_text_from_image(claim_image_path)
            all_text += claim_text
            
            # Extract from invoice if provided
            if invoice_image_path:
                print(f"Extracting text from: {invoice_image_path}")
                invoice_text = self.ocr_extractor.extract_text_from_image(invoice_image_path)
                all_text += "\n\n" + invoice_text
            
            print(f"\n✓ Extracted {len(all_text)} characters")
        else:
            print("⚠ OCR not available")
            return {"error": "OCR not initialized"}
        
        # Step 2: Parse to Structured JSON
        print("\n📋 STEP 2: TEXT PARSING")
        print("-" * 70)
        claim_json = self.text_parser.parse_text_to_claim(all_text, policy_id=policy_id)
        
        # Validate extraction
        is_valid, missing_fields = self.text_parser.validate_extracted_claim(claim_json)
        
        if not is_valid:
            print(f"\n⚠ Warning: Missing fields: {', '.join(missing_fields)}")
            print("Proceeding with available data...")
        
        # Step 3: Agent Processing
        print("\n🤖 STEP 3: AGENT PROCESSING")
        print("-" * 70)
        
        if self.agent:
            result = self.agent.process_claim(claim_json)
        else:
            print("⚠ Agent not available")
            result = {
                "error": "Agent not initialized",
                "extracted_claim": claim_json
            }
        
        # Add OCR metadata
        result['ocr_metadata'] = {
            'extraction_method': 'trocr',
            'text_length': len(all_text),
            'fields_extracted': list(claim_json.keys()),
            'validation_passed': is_valid,
            'missing_fields': missing_fields
        }
        
        return result
    
    def process_claim_from_bytes(self,
                                  claim_image_bytes: bytes,
                                  invoice_image_bytes: bytes = None,
                                  policy_id: str = None) -> Dict:
        """
        Process claim from image bytes (for API uploads)
        
        Args:
            claim_image_bytes: Claim form image as bytes
            invoice_image_bytes: Invoice image as bytes (optional)
            policy_id: Policy ID
            
        Returns:
            Complete claim processing result
        """
        
        print("\n" + "="*70)
        print("PROCESSING CLAIM FROM UPLOADED IMAGES")
        print("="*70)
        
        # Step 1: OCR Extraction from bytes
        print("\n📷 STEP 1: OCR TEXT EXTRACTION")
        print("-" * 70)
        
        all_text = ""
        
        if self.ocr_extractor:
            # Extract from claim form
            print("Extracting text from uploaded claim form...")
            claim_text = self.ocr_extractor.extract_text_from_bytes(claim_image_bytes)
            all_text += claim_text
            
            # Extract from invoice if provided
            if invoice_image_bytes:
                print("Extracting text from uploaded invoice...")
                invoice_text = self.ocr_extractor.extract_text_from_bytes(invoice_image_bytes)
                all_text += "\n\n" + invoice_text
            
            print(f"\n✓ Extracted {len(all_text)} characters")
        else:
            print("⚠ OCR not available")
            return {"error": "OCR not initialized"}
        
        # Step 2: Parse to JSON
        print("\n📋 STEP 2: TEXT PARSING")
        print("-" * 70)
        claim_json = self.text_parser.parse_text_to_claim(all_text, policy_id=policy_id)
        
        # Validate
        is_valid, missing_fields = self.text_parser.validate_extracted_claim(claim_json)
        
        # Step 3: Agent Processing
        print("\n🤖 STEP 3: AGENT PROCESSING")
        print("-" * 70)
        
        if self.agent:
            result = self.agent.process_claim(claim_json)
        else:
            result = {
                "error": "Agent not initialized",
                "extracted_claim": claim_json
            }
        
        # Add metadata
        result['ocr_metadata'] = {
            'extraction_method': 'trocr',
            'text_length': len(all_text),
            'validation_passed': is_valid,
            'missing_fields': missing_fields
        }
        
        return result
    
    def process_claim_from_json(self, claim_json: Dict) -> Dict:
        """
        Process claim from pre-structured JSON (skip OCR)
        
        Args:
            claim_json: Structured claim dictionary
            
        Returns:
            Claim processing result
        """
        
        print("\n" + "="*70)
        print("PROCESSING CLAIM FROM JSON")
        print("="*70)
        
        if self.agent:
            result = self.agent.process_claim(claim_json)
        else:
            result = {"error": "Agent not initialized"}
        
        return result
    
    def batch_process_claims(self, claim_images: List[str], policy_ids: List[str] = None) -> List[Dict]:
        """
        Process multiple claims in batch
        
        Args:
            claim_images: List of claim image paths
            policy_ids: List of policy IDs (optional)
            
        Returns:
            List of processing results
        """
        
        print("\n" + "="*70)
        print(f"BATCH PROCESSING {len(claim_images)} CLAIMS")
        print("="*70)
        
        results = []
        
        for i, image_path in enumerate(claim_images, 1):
            print(f"\n>>> Processing claim {i}/{len(claim_images)}")
            
            policy_id = policy_ids[i-1] if policy_ids and i <= len(policy_ids) else None
            
            try:
                result = self.process_claim_from_images(image_path, policy_id=policy_id)
                results.append(result)
            except Exception as e:
                print(f"✗ Error processing {image_path}: {e}")
                results.append({
                    "error": str(e),
                    "image_path": image_path
                })
        
        print("\n" + "="*70)
        print(f"✓ BATCH PROCESSING COMPLETE: {len(results)} claims processed")
        print("="*70)
        
        return results
    
    def get_processing_summary(self, result: Dict) -> str:
        """
        Generate human-readable summary of processing result
        
        Args:
            result: Processing result dictionary
            
        Returns:
            Formatted summary string
        """
        
        summary = []
        summary.append("="*70)
        summary.append("CLAIM PROCESSING SUMMARY")
        summary.append("="*70)
        
        if 'error' in result:
            summary.append(f"\n✗ ERROR: {result['error']}")
            return "\n".join(summary)
        
        summary.append(f"\nClaim ID: {result.get('claim_id', 'N/A')}")
        summary.append(f"Decision: {result.get('decision', 'N/A')}")
        summary.append(f"Payable Amount: ₹{result.get('payable_amount', 0):,.2f}")
        summary.append(f"Fraud Score: {result.get('fraud_score', 0):.4f}")
        summary.append(f"Anomaly Flag: {result.get('anomaly_flag', 0)}")
        summary.append(f"Risk Level: {result.get('risk_level', 'Unknown')}")
        
        if result.get('fraud_indicators'):
            summary.append(f"\n⚠ Risk Indicators:")
            for indicator in result['fraud_indicators']:
                summary.append(f"  • {indicator}")
        
        if result.get('coverage_issues'):
            summary.append(f"\n✗ Coverage Issues:")
            for issue in result['coverage_issues']:
                summary.append(f"  • {issue}")
        
        if result.get('ocr_metadata'):
            meta = result['ocr_metadata']
            summary.append(f"\n📷 OCR Metadata:")
            summary.append(f"  • Validation: {'✓ PASS' if meta.get('validation_passed') else '✗ FAIL'}")
            if meta.get('missing_fields'):
                summary.append(f"  • Missing: {', '.join(meta['missing_fields'])}")
        
        summary.append("="*70)
        
        return "\n".join(summary)


def test_ocr_pipeline():
    """
    Test function for OCR claim processing pipeline
    """
    
    print("="*70)
    print("TESTING OCR CLAIM PROCESSING PIPELINE")
    print("="*70)
    
    # Initialize processor
    processor = OCRClaimProcessor()
    
    # Test with sample
    print("\nThis test requires:")
    print("1. Sample claim form image")
    print("2. Hospital invoice image")
    print("\nPlace test images in: data/test_images/")
    
    # Example usage
    sample_claim_path = "data/test_images/claim_form.jpg"
    sample_invoice_path = "data/test_images/invoice.jpg"
    
    if Path(sample_claim_path).exists():
        result = processor.process_claim_from_images(
            sample_claim_path,
            sample_invoice_path if Path(sample_invoice_path).exists() else None,
            policy_id="IL-778-21"
        )
        
        print(processor.get_processing_summary(result))
    else:
        print(f"\n⚠ Test images not found")
        print("To test, place images at:")
        print(f"  - {sample_claim_path}")
        print(f"  - {sample_invoice_path}")


if __name__ == "__main__":
    test_ocr_pipeline()
