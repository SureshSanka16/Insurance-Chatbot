"""
Rule-Based Fraud Detection Service
===================================
Uses ONLY structured claim form data to calculate fraud risk.
NO OCR or document processing - just business rules and policy validation.

This service checks:
1. Policy coverage limits
2. Claim history patterns
3. Claim amount anomalies
4. Timing patterns (claim date vs policy start)
5. Frequency of claims
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from models import Claim, Policy, User, ClaimStatus

logger = logging.getLogger("rule_based_fraud_detection")


async def analyze_claim_with_rules(
    claim_data: Dict[str, Any],
    user_id: str,
    policy_number: str,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Analyze claim for fraud using rule-based approach.
    Uses ONLY structured form data - no OCR or document processing.
    
    Args:
        claim_data: Structured claim fields (from form submission)
        user_id: User ID who filed the claim
        policy_number: Policy number
        db: Database session
        
    Returns:
        Fraud analysis results with score, indicators, and decision
    """
    
    logger.info(f"[RULE-FRAUD] Starting rule-based fraud analysis for policy {policy_number}")
    
    fraud_indicators = []
    rules_checked = []  # Track all rules that were evaluated
    risk_score = 0  # Start at 0, add points for each red flag
    
    # Get policy information
    policy = await _get_policy(policy_number, db)
    if not policy:
        logger.error(f"Policy {policy_number} not found")
        return _generate_result(50, fraud_indicators, "MANUAL_REVIEW", "Policy not found")
    
    # Get claim history
    claim_history = await _get_user_claim_history(user_id, db)
    
    # Rule 1: Check claim amount vs policy coverage
    claim_amount = float(claim_data.get("claim_amount", 0))
    coverage_amount = float(policy.coverage_amount)
    
    rule_name = "📊 Coverage Limit Check"
    if claim_amount > coverage_amount:
        risk_score += 30
        fraud_indicators.append(f"Claim amount (${claim_amount:,.0f}) exceeds policy coverage (${coverage_amount:,.0f})")
        rules_checked.append({"rule": rule_name, "result": "⚠️ ALERT", "impact": "+30 points", "detail": f"Claim exceeds coverage by ${claim_amount - coverage_amount:,.0f}"})
    elif claim_amount > coverage_amount * 0.9:  # 90% of coverage
        risk_score += 15
        fraud_indicators.append(f"Claim amount (${claim_amount:,.0f}) is very high (>90% of coverage)")
        rules_checked.append({"rule": rule_name, "result": "⚠️ WARNING", "impact": "+15 points", "detail": f"Claim is {(claim_amount/coverage_amount*100):.1f}% of coverage"})
    elif claim_amount > coverage_amount * 0.7:  # 70% of coverage
        risk_score += 8
        fraud_indicators.append(f"Claim amount is high relative to coverage")
        rules_checked.append({"rule": rule_name, "result": "⚠️ CAUTION", "impact": "+8 points", "detail": f"Claim is {(claim_amount/coverage_amount*100):.1f}% of coverage"})
    else:
        rules_checked.append({"rule": rule_name, "result": "✅ PASS", "impact": "0 points", "detail": f"Claim (${claim_amount:,.0f}) is within normal range ({(claim_amount/coverage_amount*100):.1f}% of coverage)"})
    
    # Rule 2: Check policy age (new policies are higher risk)
    policy_age_days = (datetime.utcnow().date() - policy.created_at.date()).days
    rule_name = "📅 Policy Age Check"
    if policy_age_days < 30:
        risk_score += 20
        fraud_indicators.append(f"Policy is very new (activated {policy_age_days} days ago)")
        rules_checked.append({"rule": rule_name, "result": "⚠️ WARNING", "impact": "+20 points", "detail": f"Policy activated only {policy_age_days} days ago (high risk period)"})
    elif policy_age_days < 90:
        risk_score += 10
        fraud_indicators.append(f"Policy is relatively new ({policy_age_days} days old)")
        rules_checked.append({"rule": rule_name, "result": "⚠️ CAUTION", "impact": "+10 points", "detail": f"Policy is {policy_age_days} days old (still in early risk period)"})
    else:
        rules_checked.append({"rule": rule_name, "result": "✅ PASS", "impact": "0 points", "detail": f"Policy is {policy_age_days} days old (established policy)"})
    
    # Rule 3: Check claim frequency
    recent_claims = [c for c in claim_history if (datetime.utcnow() - c.submission_date).days < 180]
    rule_name = "📈 Claim Frequency Analysis"
    if len(recent_claims) >= 3:
        risk_score += 25
        fraud_indicators.append(f"High claim frequency: {len(recent_claims)} claims in last 6 months")
        rules_checked.append({"rule": rule_name, "result": "⚠️ ALERT", "impact": "+25 points", "detail": f"{len(recent_claims)} claims filed in last 6 months (unusual pattern)"})
    elif len(recent_claims) >= 2:
        risk_score += 12
        fraud_indicators.append(f"Multiple recent claims: {len(recent_claims)} in last 6 months")
        rules_checked.append({"rule": rule_name, "result": "⚠️ CAUTION", "impact": "+12 points", "detail": f"{len(recent_claims)} claims in last 6 months (monitor pattern)"})
    else:
        rules_checked.append({"rule": rule_name, "result": "✅ PASS", "impact": "0 points", "detail": f"{len(recent_claims)} claim(s) in last 6 months (normal frequency)"})
    
    # Rule 4: Check for round numbers (often fake)
    rule_name = "🔢 Round Number Detection"
    if claim_amount % 1000 == 0 and claim_amount >= 10000:
        risk_score += 8
        fraud_indicators.append(f"Claim amount is a round number (${claim_amount:,.0f})")
        rules_checked.append({"rule": rule_name, "result": "⚠️ SUSPICIOUS", "impact": "+8 points", "detail": f"Perfect round number (${claim_amount:,.0f}) - may indicate estimation"})
    else:
        rules_checked.append({"rule": rule_name, "result": "✅ PASS", "impact": "0 points", "detail": f"Claim amount (${claim_amount:,.0f}) appears genuine"})
    
    # Rule 5: Check claim type patterns
    claim_type = claim_data.get("claim_type", "")
    rule_name = f"🏥 {claim_type}-Specific Rules"
    type_score_before = risk_score
    
    if claim_type == "Health":
        risk_score += _check_health_claim_rules(claim_data, fraud_indicators)
    elif claim_type == "Vehicle":
        risk_score += _check_vehicle_claim_rules(claim_data, fraud_indicators)
    elif claim_type == "Life":
        risk_score += _check_life_claim_rules(claim_data, policy, fraud_indicators)
    elif claim_type == "Property":
        risk_score += _check_property_claim_rules(claim_data, fraud_indicators)
    
    type_score_added = risk_score - type_score_before
    if type_score_added > 0:
        rules_checked.append({"rule": rule_name, "result": "⚠️ FLAG", "impact": f"+{type_score_added} points", "detail": f"Type-specific analysis identified concerns"})
    else:
        rules_checked.append({"rule": rule_name, "result": "✅ PASS", "impact": "0 points", "detail": f"Type-specific checks passed"})
    
    # Rule 6: Check historical claim amounts (anomaly detection)
    rule_name = "📊 Historical Pattern Analysis"
    if claim_history:
        avg_claim_amount = sum(float(c.amount) for c in claim_history) / len(claim_history)
        if claim_amount > avg_claim_amount * 3:
            risk_score += 15
            fraud_indicators.append(f"Claim amount is 3x higher than user's average claim (${avg_claim_amount:,.0f})")
            rules_checked.append({"rule": rule_name, "result": "⚠️ ANOMALY", "impact": "+15 points", "detail": f"Claim is 3x higher than average (${avg_claim_amount:,.0f})"})
        elif claim_amount > avg_claim_amount * 2:
            risk_score += 8
            fraud_indicators.append(f"Claim amount is 2x higher than user's average")
            rules_checked.append({"rule": rule_name, "result": "⚠️ CAUTION", "impact": "+8 points", "detail": f"Claim is 2x higher than average (${avg_claim_amount:,.0f})"})
        else:
            rules_checked.append({"rule": rule_name, "result": "✅ PASS", "impact": "0 points", "detail": f"Claim amount consistent with history (avg: ${avg_claim_amount:,.0f})"})
    else:
        rules_checked.append({"rule": rule_name, "result": "ℹ️ N/A", "impact": "0 points", "detail": "No claim history available for comparison"})
    
    # Rule 7: Check for duplicate/similar claims
    rule_name = "🔍 Duplicate Detection"
    similar_claims = _find_similar_claims(claim_data, claim_history)
    if similar_claims:
        risk_score += 20
        fraud_indicators.append(f"Similar claim found: filed {similar_claims[0].submission_date.strftime('%Y-%m-%d')}")
        rules_checked.append({"rule": rule_name, "result": "⚠️ ALERT", "impact": "+20 points", "detail": f"Similar claim filed on {similar_claims[0].submission_date.strftime('%Y-%m-%d')}"})
    else:
        rules_checked.append({"rule": rule_name, "result": "✅ PASS", "impact": "0 points", "detail": "No duplicate or similar claims found"})
    
    # Cap risk score at 100
    risk_score = min(risk_score, 100)
    
    # Determine risk level and decision
    if risk_score >= 75:
        risk_level = "HIGH"
        decision = "FRAUD_ALERT"
    elif risk_score >= 50:
        risk_level = "MEDIUM"
        decision = "MANUAL_REVIEW"
    elif risk_score >= 30:
        risk_level = "MEDIUM"
        decision = "MANUAL_REVIEW"
    else:
        risk_level = "LOW"
        decision = "AUTO_APPROVE"
    
    # Generate reasoning
    reasoning = _generate_reasoning(risk_score, risk_level, fraud_indicators, claim_data, rules_checked)
    
    logger.info(f"[RULE-FRAUD] Analysis complete - Score: {risk_score}, Level: {risk_level}, Decision: {decision}")
    
    return _generate_result(risk_score, fraud_indicators, decision, reasoning, risk_level, rules_checked)


async def _get_policy(policy_number: str, db: AsyncSession) -> Policy:
    """Get policy from database."""
    result = await db.execute(
        select(Policy).where(Policy.policy_number == policy_number)
    )
    return result.scalar_one_or_none()


async def _get_user_claim_history(user_id: str, db: AsyncSession) -> List[Claim]:
    """Get user's claim history."""
    result = await db.execute(
        select(Claim)
        .join(Policy, Claim.policy_number == Policy.policy_number)
        .where(Policy.user_id == user_id)
        .order_by(Claim.submission_date.desc())
    )
    return result.scalars().all()


def _check_health_claim_rules(claim_data: Dict[str, Any], indicators: List[str]) -> int:
    """Check health-specific fraud rules."""
    score = 0
    
    # Check for expensive procedures
    diagnosis = str(claim_data.get("diagnosis", "")).lower()
    if any(word in diagnosis for word in ["surgery", "transplant", "cancer", "cardiac"]):
        # High-cost procedures - verify carefully
        amount = float(claim_data.get("claim_amount", 0))
        if amount > 100000:
            score += 10
            indicators.append("High-cost procedure with large claim amount")
    
    # Check admission/discharge dates
    admission = claim_data.get("admission_date")
    discharge = claim_data.get("discharge_date")
    if admission and discharge:
        try:
            adm_date = datetime.fromisoformat(admission.replace('Z', '+00:00'))
            dis_date = datetime.fromisoformat(discharge.replace('Z', '+00:00'))
            stay_days = (dis_date - adm_date).days
            
            if stay_days < 0:
                score += 25
                indicators.append("Discharge date before admission date")
            elif stay_days > 30:
                score += 8
                indicators.append(f"Very long hospital stay ({stay_days} days)")
        except:
            pass
    
    return score


def _check_vehicle_claim_rules(claim_data: Dict[str, Any], indicators: List[str]) -> int:
    """Check vehicle-specific fraud rules."""
    score = 0
    
    # Check if police report was filed for high-value claims
    amount = float(claim_data.get("claim_amount", 0))
    police_filed = claim_data.get("police_report_filed", False)
    
    if amount > 20000 and not police_filed:
        score += 15
        indicators.append("High-value vehicle damage without police report")
    
    # Check incident type
    incident_type = str(claim_data.get("incident_type", "")).lower()
    if "theft" in incident_type or "total" in incident_type:
        if amount > 50000:
            score += 12
            indicators.append("High-value total loss or theft claim")
    
    return score


def _check_life_claim_rules(claim_data: Dict[str, Any], policy: Policy, indicators: List[str]) -> int:
    """Check life insurance-specific fraud rules."""
    score = 0
    
    # Check policy age for life claims (suspicious if very new)
    policy_age_days = (datetime.utcnow().date() - policy.created_at.date()).days
    if policy_age_days < 180:  # Less than 6 months
        score += 25
        indicators.append(f"Life claim filed shortly after policy activation ({policy_age_days} days)")
    elif policy_age_days < 365:  # Less than 1 year
        score += 15
        indicators.append("Life claim within first year of policy")
    
    # Check cause of death if provided
    cause = str(claim_data.get("cause_of_death", "")).lower()
    if any(word in cause for word in ["accident", "unnatural", "suspicious"]):
        score += 10
        indicators.append("Unnatural cause of death - requires investigation")
    
    return score


def _check_property_claim_rules(claim_data: Dict[str, Any], indicators: List[str]) -> int:
    """Check property-specific fraud rules."""
    score = 0
    
    incident_type = str(claim_data.get("incident_type", "")).lower()
    fire_dept = claim_data.get("fire_dept_involved", False)
    
    if "fire" in incident_type and not fire_dept:
        score += 20
        indicators.append("Fire damage claim without fire department involvement")
    
    return score


def _find_similar_claims(current_claim: Dict[str, Any], history: List[Claim]) -> List[Claim]:
    """Find similar claims in history (potential duplicates)."""
    similar = []
    current_amount = float(current_claim.get("claim_amount", 0))
    current_type = current_claim.get("claim_type", "")
    
    for claim in history:
        # Check if same type and similar amount (within 10%)
        if claim.type == current_type:
            amount_diff = abs(float(claim.amount) - current_amount) / current_amount
            if amount_diff < 0.1:  # Within 10%
                # Check if filed within same year
                days_diff = (datetime.utcnow() - claim.submission_date).days
                if days_diff < 365:
                    similar.append(claim)
    
    return similar


def _generate_reasoning(score: int, level: str, indicators: List[str], claim_data: Dict[str, Any], rules_checked: List[Dict]) -> str:
    """Generate human-readable fraud analysis reasoning."""
    claim_type = claim_data.get("claim_type", "Unknown")
    claim_amount = float(claim_data.get("claim_amount", 0))
    
    reasoning = f"✅ Rule-based fraud analysis for {claim_type} claim (${claim_amount:,.0f}):\n\n"
    
    # Summary
    if score >= 75:
        reasoning += "⚠️ HIGH RISK - Multiple fraud indicators detected:\n"
    elif score >= 50:
        reasoning += "⚡ MEDIUM RISK - Some concerning patterns identified:\n"
    elif score >= 30:
        reasoning += "⚠️ MODERATE RISK - Minor concerns noted:\n"
    else:
        reasoning += "✅ LOW RISK - Claim appears legitimate:\n"
    
    reasoning += "\n📋 ALL FRAUD DETECTION RULES EVALUATED:\n"
    reasoning += "─" * 60 + "\n"
    
    # Show all rules that were checked
    for i, rule_check in enumerate(rules_checked, 1):
        reasoning += f"{i}. {rule_check['rule']}\n"
        reasoning += f"   Result: {rule_check['result']} | Impact: {rule_check['impact']}\n"
        reasoning += f"   Detail: {rule_check['detail']}\n\n"
    
    reasoning += "\n🚩 FRAUD INDICATORS FLAGGED:\n"
    reasoning += "─" * 60 + "\n"
    
    if indicators:
        for i, indicator in enumerate(indicators, 1):
            reasoning += f"{i}. {indicator}\n"
    else:
        reasoning += "✅ No significant fraud indicators found\n"
        reasoning += "✅ Claim amount within normal range\n"
        reasoning += "✅ Policy is established with good history\n"
    
    reasoning += f"\n📊 FINAL ANALYSIS:\n"
    reasoning += "─" * 60 + "\n"
    reasoning += f"Risk Score: {score}/100 ({level} Risk)\n"
    reasoning += f"Red Flags: {len(indicators)}\n"
    reasoning += f"Rules Checked: {len(rules_checked)}\n\n"
    
    reasoning += f"💡 RECOMMENDATION: "
    if score >= 75:
        reasoning += "Requires immediate fraud investigation"
    elif score >= 50:
        reasoning += "Manual review recommended before approval"
    else:
        reasoning += "Standard approval process can proceed"
    
    return reasoning


def _generate_result(score: int, indicators: List[str], decision: str, reasoning: str, risk_level: str = "MEDIUM", rules_checked: List[Dict] = None) -> Dict[str, Any]:
    """Generate standardized fraud analysis result."""
    return {
        "fraud_score": score,
        "risk_level": risk_level,
        "decision": decision,
        "fraud_indicators": indicators,
        "reasoning": reasoning,
        "red_flags_count": len(indicators),
        "confidence": "HIGH" if len(indicators) >= 3 else "MEDIUM" if len(indicators) >= 1 else "LOW",
        "analysis_method": "rule_based",
        "rules_checked": rules_checked or [],
        "total_rules_evaluated": len(rules_checked) if rules_checked else 0
    }
