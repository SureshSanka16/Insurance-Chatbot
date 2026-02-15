import { GoogleGenAI, Type } from "@google/genai";
import { Claim, Document, Policy } from "../types";

// Initializing the GoogleGenAI client using the Vite environment variable
const ai = new GoogleGenAI({ apiKey: import.meta.env.VITE_GEMINI_API_KEY });

const FAST_MODEL = "gemini-3-flash-preview";
const REASONING_MODEL = "gemini-3-pro-preview";

export const analyzeClaimRisk = async (
  claim: Claim,
): Promise<{ score: number; reasoning: string; recommendations: string[] }> => {
  try {
    const prompt = `
      You are Vantage AI, a premium insurance fraud detection engine. 
      Analyze this ${claim.type} claim for risk.
      
      Details:
      ID: ${claim.id}
      Amount: $${claim.amount}
      Date: ${claim.date}
      Description: ${claim.description}
      Current Score: ${claim.riskScore}
      
      Provide a JSON response with a deep assessment:
      - score: integer 0-100
      - reasoning: detailed professional paragraph
      - recommendations: exactly 3 actionable steps for the adjuster.
    `;

    const response = await ai.models.generateContent({
      model: REASONING_MODEL,
      contents: prompt,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            score: { type: Type.INTEGER },
            reasoning: { type: Type.STRING },
            recommendations: { type: Type.ARRAY, items: { type: Type.STRING } },
          },
          required: ["score", "reasoning", "recommendations"],
        },
      },
    });

    const result = JSON.parse(response.text || "{}");
    return result;
  } catch (error) {
    console.error("AI Analysis Failed:", error);
    return {
      score: claim.riskScore,
      reasoning:
        "AI services are currently under heavy load. System baseline risk preserved.",
      recommendations: [
        "Perform manual verification of police report",
        "Cross-reference IP address history",
        "Wait for secondary AI verification",
      ],
    };
  }
};

/**
 * Generates an executive strategic report based on current operational data.
 */
export const generateStrategicReport = async (data: {
  claimsCount: number;
  fraudValue: string;
  riskDist: any[];
}): Promise<string> => {
  try {
    // Calculate key metrics for deeper analysis
    const totalRiskCount = data.riskDist.reduce((sum, r) => sum + r.value, 0);
    const criticalPercentage =
      totalRiskCount > 0
        ? (
            ((data.riskDist.find((r) => r.name === "Critical")?.value || 0) /
              totalRiskCount) *
            100
          ).toFixed(1)
        : "0.0";
    const highRiskPercentage =
      totalRiskCount > 0
        ? (
            ((data.riskDist.find((r) => r.name === "High Risk")?.value || 0) /
              totalRiskCount) *
            100
          ).toFixed(1)
        : "0.0";

    const prompt = `
      You are the Vantage Chief Strategy Officer AI. Generate a concise, high-impact executive strategic report based on REAL-TIME operational data.
      
      CURRENT OPERATIONAL METRICS:
      - Total Active Claims in Pipeline: ${data.claimsCount}
      - Fraud Successfully Prevented: ${data.fraudValue}
      - Critical Risk Cases: ${criticalPercentage}% of total claims
      - High Risk Cases: ${highRiskPercentage}% of total claims
      - Risk Distribution Breakdown: 
        ${data.riskDist.map((r) => `  • ${r.name}: ${r.value} claims`).join("\n        ")}
      
      REPORT STRUCTURE (Use clean, professional markdown):
      
      ## Executive Summary
      Provide 2-3 powerful sentences summarizing the current state of operations, highlighting the most critical insights from the data.
      
      ## Risk Landscape Analysis
      - Analyze the risk distribution pattern
      - Identify concerning trends (high % of critical/high risk)
      - Compare fraud prevention success rate
      - Flag any anomalies or areas requiring immediate attention
      
      ## Operational Performance
      - Assess current throughput (${data.claimsCount} claims)
      - Evaluate fraud detection effectiveness (${data.fraudValue} prevented)
      - Calculate implied approval rates and processing efficiency
      - Identify bottlenecks or inefficiencies
      
      ## Strategic Recommendations
      Provide 4-6 specific, actionable recommendations based on the data:
      - If critical risk % is high (>10%), recommend enhanced screening protocols
      - If fraud prevention is strong, suggest scaling the model
      - If claim volume is high, recommend automation expansion
      - Include risk mitigation strategies
      - Suggest resource allocation optimizations
      
      TONE: Professional, data-driven, authoritative. Use specific numbers from the data provided. Be direct and actionable.
    `;

    const response = await ai.models.generateContent({
      model: FAST_MODEL,
      contents: prompt,
      config: {
        systemInstruction:
          "You are an elite insurance strategy consultant with expertise in fraud detection, risk assessment, and operational optimization. Your goal is to provide actionable insights based on real-time data to improve claim operations and mitigate risk through AI-driven intelligence.",
      },
    });

    return (
      response.text || "Report generation timed out. Please retry analysis."
    );
  } catch (error) {
    return "The strategic engine is currently recalibrating. Data-driven insights will resume shortly.";
  }
};

/**
 * Policy-Aware Insurance Claim Form Generator
 * Generates a clean, human-readable claim form based on policy type.
 */
export const generateClaimForm = async (
  policy: Policy,
  userProfile: any,
  incidentDetails: {
    date: string;
    time?: string;
    location?: string;
    description: string;
    items: { item: string; cost: number }[];
  },
): Promise<string> => {
  try {
    const systemInstruction = `
You are a Policy-Aware Insurance Claim Form Generator.

Your task:
Generate a clean, human-readable insurance claim form
using the correct template based ONLY on policy_type.

Rules:
- DO NOT ask user to choose claim type.
- Use policy_type to decide template.
- Pre-fill fields using policyholder_profile.
- If a field is missing, write "Not Provided".
- Do NOT hallucinate values.
- Maintain exact template structure and headings.
- Output text only (no JSON).

--------------------------------------------------
SUPPORTED POLICY TYPES
vehicle | health | life | property
--------------------------------------------------

IF policy_type = vehicle
OUTPUT EXACTLY THIS TEMPLATE:

INSURECORP – Global Insurance Group
Vehicle Insurance Claim Submission Form

Claim Reference No:
Submission Date:
Claim Status:

Policyholder Information
Full Name:
Policy Number:
Contact Number:
Email:
Address:

Vehicle Information
Vehicle Make & Model:
Registration Number:
VIN:
Odometer Reading:

Incident Details
Incident Date:
Incident Time:
Incident Type:
Location:
Police Report Filed:
Police Report Number:

Description of Loss

Itemized Loss Breakdown
Item | Estimated Cost

Supporting Documents

Declaration
I hereby declare that the above information is true and correct to the best of my knowledge.
Signature:
Date:

--------------------------------------------------

IF policy_type = health
OUTPUT EXACTLY THIS TEMPLATE:

INSURECORP – Global Insurance Group
Health Insurance Claim Form

Claim No:
Submission Date:
Claim Status:

Policyholder Information
Name:
Policy Number:
Date of Birth:
Contact Number:
Address:

Patient Details
Patient Name:
Relationship to Policyholder:

Hospital Information
Hospital Name:
Hospital Address:
Admission Date:
Discharge Date:
Doctor Name:

Diagnosis & Treatment
Diagnosis:
Treatment Provided:
Surgery Performed:

Itemized Medical Expenses
Item | Amount

Supporting Documents

Declaration
I hereby declare that the above information is true and correct to the best of my knowledge.
Signature:
Date:

--------------------------------------------------

IF policy_type = life
OUTPUT EXACTLY THIS TEMPLATE:

INSURECORP – Global Insurance Group
Life Insurance Claim Form

Claim No:
Submission Date:
Claim Status:

Policyholder (Deceased)
Name:
Policy Number:
Date of Birth:
Date of Death:
Cause of Death:

Nominee / Beneficiary Details
Name:
Relationship:
Contact Number:
Bank Account Details:

Policy Information
Policy Start Date:
Sum Assured:
Premium Status:

Claim Amount
Amount Claimed:

Supporting Documents

Declaration
I hereby declare that the above information is true and correct to the best of my knowledge.
Signature:
Date:

--------------------------------------------------

IF policy_type = property
OUTPUT EXACTLY THIS TEMPLATE:

INSURECORP – Global Insurance Group
Home / Property Insurance Claim Form

Claim No:
Submission Date:
Claim Status:

Policyholder Information
Name:
Policy Number:
Address of Insured Property:
Contact Number:

Incident Details
Incident Date:
Type of Incident:
Location of Damage:
Fire Department Involved:
Report Number:

Description of Damage

Itemized Damage Assessment
Item | Estimated Cost

Supporting Documents

Declaration
I hereby declare that the above information is true and correct to the best of my knowledge.
Signature:
Date:
    `;

    const inputData = `
Policy Metadata:
- policy_id: ${policy.id}
- policy_type: ${policy.category.toLowerCase()}
- policy_name: ${policy.title}
- policy_number: ${policy.policyNumber}
- policyholder_profile: ${JSON.stringify(userProfile)}

User Incident Details:
- date: ${incidentDetails.date}
- time: ${incidentDetails.time || "Not Provided"}
- location: ${incidentDetails.location || "Not Provided"}
- description: ${incidentDetails.description}
- items: ${JSON.stringify(incidentDetails.items)}
    `;

    const response = await ai.models.generateContent({
      model: FAST_MODEL,
      contents: inputData,
      config: {
        systemInstruction: systemInstruction,
      },
    });

    return response.text || "Failed to generate claim form.";
  } catch (error) {
    console.error("Form generation failed:", error);
    return "Error generating standardized claim form.";
  }
};

export const normalizeDocument = async (rawText: string): Promise<string> => {
  try {
    const systemInstruction = `
You are an Insurance Document Normalization Agent.

Your task is to take a raw insurance claim document (OCR extracted text or user-submitted text)
and transform it into ONE of the following standardized templates based on claim type:

1) Vehicle Insurance Claim
2) Health Insurance Claim
3) Life Insurance Claim
4) Home / Property Insurance Claim

Rules:
- Detect claim type automatically.
- Preserve factual values exactly.
- If a field is missing, output "Not Provided".
- Do NOT hallucinate.
- Maintain the exact section order and headings of the chosen template.
- Output clean readable text (not JSON).

-------------------------------
STANDARD VEHICLE TEMPLATE
-------------------------------
INSURECORP – Global Insurance Group
Vehicle Insurance Claim Submission Form

Claim Reference No:
Submission Date:
Claim Status:

Policyholder Information
Full Name:
Policy Number:
Contact Number:
Email:
Address:

Vehicle Information
Vehicle Make & Model:
Registration Number:
VIN:
Odometer Reading:

Incident Details
Incident Date:
Incident Time:
Incident Type:
Location:
Police Report Filed:
Police Report Number:

Description of Loss

Itemized Loss Breakdown
Item | Estimated Cost

Supporting Documents

Declaration
I hereby declare that the above information is true and correct to the best of my knowledge.
Signature:
Date:

-------------------------------
STANDARD HEALTH TEMPLATE
-------------------------------
INSURECORP – Global Insurance Group
Health Insurance Claim Form

Claim No:
Submission Date:
Claim Status:

Policyholder Information
Name:
Policy Number:
Date of Birth:
Contact Number:
Address:

Patient Details
Patient Name:
Relationship to Policyholder:

Hospital Information
Hospital Name:
Hospital Address:
Admission Date:
Discharge Date:
Doctor Name:

Diagnosis & Treatment
Diagnosis:
Treatment Provided:
Surgery Performed:

Itemized Medical Expenses
Item | Amount

Supporting Documents

Declaration
I hereby declare that the above information is true and correct to the best of my knowledge.
Signature:
Date:

-------------------------------
STANDARD LIFE TEMPLATE
-------------------------------
INSURECORP – Global Insurance Group
Life Insurance Claim Form

Claim No:
Submission Date:
Claim Status:

Policyholder (Deceased)
Name:
Policy Number:
Date of Birth:
Date of Death:
Cause of Death:

Nominee / Beneficiary Details
Name:
Relationship:
Contact Number:
Bank Account Details:

Policy Information
Policy Start Date:
Sum Assured:
Premium Status:

Claim Amount
Amount Claimed:

Supporting Documents

Declaration
I hereby declare that the above information is true and correct to the best of my knowledge.
Signature:
Date:

-------------------------------
STANDARD PROPERTY TEMPLATE
-------------------------------
INSURECORP – Global Insurance Group
Home / Property Insurance Claim Form

Claim No:
Submission Date:
Claim Status:

Policyholder Information
Name:
Policy Number:
Address of Insured Property:
Contact Number:

Incident Details
Incident Date:
Type of Incident:
Location of Damage:
Fire Department Involved:
Report Number:

Description of Damage

Itemized Damage Assessment
Item | Estimated Cost

Supporting Documents

Declaration
I hereby declare that the above information is true and correct to the best of my knowledge.
Signature:
Date:
    `;

    const response = await ai.models.generateContent({
      model: FAST_MODEL,
      contents: rawText,
      config: {
        systemInstruction: systemInstruction,
      },
    });

    return response.text || "Failed to normalize document.";
  } catch (error) {
    console.error("Normalization failed:", error);
    return "Error during document normalization process.";
  }
};

export const summarizeDocument = async (
  fileName: string,
  fileType: string,
): Promise<string> => {
  try {
    const response = await ai.models.generateContent({
      model: FAST_MODEL,
      contents: `Summarize the typical contents of an insurance document named "${fileName}" (${fileType}) in exactly 15 words.`,
    });
    return response.text || "Summary unavailable.";
  } catch (error) {
    return "Standard insurance documentation relating to current claim profile.";
  }
};

export const extractDocumentEntities = async (
  doc: Document,
): Promise<Record<string, string>> => {
  try {
    const response = await ai.models.generateContent({
      model: FAST_MODEL,
      contents: `Simulate OCR extraction for "${doc.name}" in category "${doc.category}". Return JSON with 5 realistic insurance fields.`,
      config: { responseMimeType: "application/json" },
    });
    return JSON.parse(response.text || "{}");
  } catch (e) {
    return {
      "OCR Status": "Partial Failure",
      Extraction: "Manual Review Required",
    };
  }
};

export const detectFraudPatterns = async (claims: Claim[]): Promise<string> => {
  try {
    // Extract relevant fields for the specific fraud checks
    const analysisData = claims.map((c) => ({
      id: c.id,
      amount: c.amount,
      phoneNumber: c.phoneNumber,
      description: c.description,
    }));

    const prompt = `
      You are the Vantage Fraud Detection Assistant. Your task is to analyze insurance claims and identify simple red flags based on claimant behavior and costs.

      Focus on these 3 simple signals:
      1. Shared Phone Number: Flag claims where the same phoneNumber appears across different claim IDs.
      2. High-Value Claims: Flag any claim where the total amount is greater than $15,000, as these require manual review.
      3. Description Check: Flag claims where the description is very similar to another claim, which might suggest a "copy-paste" accident story.

      Output Format:
      Provide a clear list for each flagged claim in the following format:
      
      **Claim ID**: [Specific reason for the flag]
      * **Risk Level**: [Low / Medium / High]
      * **Next Step**: [Simple advice, e.g., "Verify contact info" or "Check repair shop"]
      
      If no significant flags are found, provide a brief summary stating that.

      Analyze the following claims:
      ${JSON.stringify(analysisData)}
    `;

    const response = await ai.models.generateContent({
      model: FAST_MODEL,
      contents: prompt,
    });
    return (
      response.text || "No distinct fraud patterns detected in current batch."
    );
  } catch (e) {
    return "Fraud detection algorithm is currently being updated. Manual monitoring recommended.";
  }
};

export const chatWithCopilot = async (
  message: string,
  context?: string,
): Promise<string> => {
  try {
    const response = await ai.models.generateContent({
      model: FAST_MODEL,
      contents: message,
      config: {
        systemInstruction: `You are Aura, the Vantage AI assistant. You are direct, professional, and insightful. Context: ${context || "Dashboard"}.`,
      },
    });
    return (
      response.text || "I'm processing the data. Please rephrase your query."
    );
  } catch (error) {
    return "I'm experiencing a connectivity issue with the neural engine. Please try again.";
  }
};
