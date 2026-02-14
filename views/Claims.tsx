import React, { useState, useEffect, useRef } from "react";
import { Card, Button, Badge, cn } from "../components/UIComponents";
import { Status, RiskLevel, Claim } from "../types";
import {
  Search,
  FileText,
  CheckCircle,
  Activity,
  Clock,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  Filter,
  Printer,
  ZoomIn,
  ZoomOut,
  User,
  Shield,
  Stethoscope,
  Car,
  Home,
  Heart,
  AlertTriangle,
  Mail,
  Phone,
  MapPin,
  ClipboardList,
  Paperclip,
  Navigation,
  FileBadge,
  RefreshCw,
  X,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { ThreeScene } from "../components/ThreeScene";
import {
  fetchClaims,
  updateClaimStatus,
  runAiScan,
} from "../src/api/endpoints";

// --- Date/Time Formatting Helpers ---
const formatDate = (raw?: string | null): string => {
  if (!raw) return "Not Provided";
  try {
    const d = new Date(raw);
    return d.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  } catch {
    return raw;
  }
};

const formatTime = (raw?: string | null): string => {
  if (!raw) return "Not Provided";
  try {
    const d = new Date(raw);
    if (!isNaN(d.getTime()) && raw.includes("T")) {
      return d.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
      });
    }
    return raw;
  } catch {
    return raw;
  }
};

const formatDateTime = (raw?: string | null): string => {
  if (!raw) return "Not Provided";
  try {
    const d = new Date(raw);
    return (
      d.toLocaleDateString("en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
      }) +
      " at " +
      d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })
    );
  } catch {
    return raw;
  }
};

// --- Specialized Document Templates ---

const DocumentHeader = ({
  title,
  claimNo,
  date,
  status,
  icon: Icon,
  emoji,
}: any) => (
  <div className="flex justify-between items-start border-b-2 border-gray-900 pb-8 mb-8">
    <div className="flex items-center gap-4">
      <div className="p-3 bg-gray-900 rounded-xl text-white">
        <Icon size={32} />
      </div>
      <div>
        <h1 className="text-2xl font-black tracking-tighter text-gray-900 font-sans uppercase">
          {emoji} INSURECORP
        </h1>
        <p className="text-[10px] text-gray-500 font-bold uppercase tracking-[0.2em] font-sans">
          Global Insurance Group
        </p>
      </div>
    </div>
    <div className="text-right">
      <h2 className="text-lg font-bold uppercase tracking-widest text-gray-800">
        {title}
      </h2>
      <div className="flex flex-col gap-1 mt-2 font-mono text-xs">
        <p>
          <span className="text-gray-400">Claim Reference No:</span>{" "}
          <span className="text-gray-900 font-bold">{claimNo}</span>
        </p>
        <p>
          <span className="text-gray-400">Submission Date:</span>{" "}
          <span className="text-gray-900">{formatDate(date)}</span>
        </p>
        <p>
          <span className="text-gray-400">Claim Status:</span>{" "}
          <span className="text-orange-600 font-bold uppercase">{status}</span>
        </p>
      </div>
    </div>
  </div>
);

const SectionTitle = ({ icon: Icon, title, emoji }: any) => (
  <div className="flex items-center gap-2 border-b border-gray-200 pb-2 mb-4 mt-8">
    <Icon size={16} className="text-gray-400" />
    <h3 className="text-[11px] font-black uppercase text-gray-500 tracking-[0.15em]">
      {emoji} {title}
    </h3>
  </div>
);

const InfoGrid = ({
  items,
}: {
  items: {
    label: string;
    value: string | number | undefined | null;
    mono?: boolean;
  }[];
}) => (
  <div className="grid grid-cols-2 gap-x-12 gap-y-4 text-sm">
    {items.map((item, i) => (
      <div key={i} className="flex flex-col">
        <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">
          {item.label}
        </span>
        <span
          className={cn(
            "font-semibold text-gray-900",
            item.mono && "font-mono",
          )}
        >
          {item.value || "Not Provided"}
        </span>
      </div>
    ))}
  </div>
);

const ItemizedTable = ({
  data,
  totalLabel = "Total Claimed Amount",
}: {
  data?: { item: string; cost: number }[];
  totalLabel?: string;
}) => {
  if (!data)
    return (
      <div className="text-sm text-gray-400 italic">No breakdown provided.</div>
    );
  const total = data.reduce((acc, curr) => acc + curr.cost, 0);
  return (
    <div className="mt-4 border rounded-xl overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-gray-500">
          <tr>
            <th className="px-4 py-2 text-left font-bold uppercase text-[10px]">
              Item
            </th>
            <th className="px-4 py-2 text-right font-bold uppercase text-[10px]">
              Estimated Cost
            </th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {data.map((row, i) => (
            <tr key={i}>
              <td className="px-4 py-3 text-gray-700">{row.item}</td>
              <td className="px-4 py-3 text-right font-mono font-bold text-gray-900">
                ${row.cost.toLocaleString()}
              </td>
            </tr>
          ))}
          <tr className="bg-gray-100 text-gray-900 font-bold">
            <td className="px-4 py-4">{totalLabel}</td>
            <td className="px-4 py-4 text-right font-mono text-lg">
              ${total.toLocaleString()}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
};

const SupportingDocsList = ({ docs }: { docs: string[] }) => (
  <div className="mt-4 grid grid-cols-2 gap-2">
    {docs.length > 0 ? (
      docs.map((doc, i) => (
        <div
          key={i}
          className="flex items-center gap-2 p-2.5 rounded-lg bg-gray-50 border border-gray-100 text-xs text-gray-700 font-medium shadow-sm"
        >
          <Paperclip size={14} className="text-orange-500" />
          {doc}
        </div>
      ))
    ) : (
      <p className="text-xs text-gray-400 italic">
        No supporting documents listed.
      </p>
    )}
  </div>
);

const Declaration = ({ name, date }: { name: string; date: string }) => (
  <div className="mt-12 pt-8 border-t border-dashed border-gray-200">
    <h3 className="text-[10px] font-black uppercase text-gray-400 tracking-widest mb-4">
      ✍ Declaration
    </h3>
    <p className="text-xs text-gray-500 leading-relaxed italic mb-8">
      I hereby declare that the above information is true and correct to the
      best of my knowledge.
    </p>
    <div className="flex justify-between items-end">
      <div className="space-y-1">
        <p className="text-xs font-bold text-gray-400 uppercase">Signature</p>
        <p
          className="text-2xl font-serif text-gray-800 tracking-tighter"
          style={{ fontFamily: "Dancing Script, cursive" }}
        >
          {name}
        </p>
      </div>
      <div className="text-right">
        <p className="text-xs font-bold text-gray-400 uppercase">Date</p>
        <p className="text-sm font-bold text-gray-900">{date}</p>
      </div>
    </div>
  </div>
);

// Specific View: Vehicle
const VehicleDocument = ({ claim }: { claim: Claim }) => {
  const docNames = claim.documents?.map((d) => d.name) || [
    "Vehicle Photographs",
    "Repair Estimate Invoice",
    "Police Report",
    "Driver’s License",
    "Vehicle Registration",
    "Insurance Policy Copy",
  ];

  return (
    <div className="p-12 font-sans bg-white min-h-screen">
      <DocumentHeader
        emoji="🚗"
        title="Vehicle Insurance Claim Submission Form"
        claimNo={claim.id}
        date={formatDate(claim.date)}
        status={claim.status === Status.New ? "Submitted" : claim.status}
        icon={Car}
      />
      <div className="space-y-10">
        <div>
          <SectionTitle
            emoji="🧍"
            icon={User}
            title="Policyholder Information"
          />
          <InfoGrid
            items={[
              { label: "Full Name", value: claim.claimant },
              { label: "Policy Number", value: claim.policyNumber, mono: true },
              { label: "Contact Number", value: claim.phoneNumber },
              {
                label: "Email",
                value: `${claim.claimant.toLowerCase().replace(" ", ".")} @email.com`,
              },
              { label: "Address", value: "123 Business Park, New York, NY" },
            ]}
          />
        </div>
        <div>
          <SectionTitle emoji="🚘" icon={Car} title="Vehicle Information" />
          <InfoGrid
            items={[
              {
                label: "Vehicle Make & Model",
                value: claim.vehicleInfo?.makeModel,
              },
              {
                label: "Registration Number",
                value: claim.vehicleInfo?.regNumber,
                mono: true,
              },
              { label: "VIN", value: claim.vehicleInfo?.vin, mono: true },
              { label: "Odometer Reading", value: claim.vehicleInfo?.odometer },
            ]}
          />
        </div>
        <div>
          <SectionTitle emoji="📍" icon={MapPin} title="Incident Details" />
          <InfoGrid
            items={[
              { label: "Incident Date", value: formatDate(claim.date) },
              { label: "Incident Time", value: formatTime(claim.date) },
              {
                label: "Incident Type",
                value: claim.vehicleInfo?.incidentType,
              },
              { label: "Location", value: claim.vehicleInfo?.location },
              {
                label: "Police Report Filed",
                value: claim.vehicleInfo?.policeReportFiled ? "Yes" : "No",
              },
              {
                label: "Police Report Number",
                value: claim.vehicleInfo?.policeReportNo,
                mono: true,
              },
            ]}
          />
        </div>
        <div>
          <SectionTitle
            emoji="📝"
            icon={FileText}
            title="Description of Loss"
          />
          <div className="bg-gray-50/50 p-6 rounded-2xl border border-gray-100 italic text-gray-700 leading-relaxed text-sm shadow-inner">
            {claim.description || "Not Provided"}
          </div>
        </div>
        <div>
          <SectionTitle
            emoji="📦"
            icon={ClipboardList}
            title="Itemized Loss Breakdown"
          />
          <ItemizedTable data={claim.itemizedLoss} />
        </div>
        <div>
          <SectionTitle
            emoji="📎"
            icon={Paperclip}
            title="Supporting Documents"
          />
          <SupportingDocsList docs={docNames} />
        </div>
        <Declaration name={claim.claimant} date={formatDate(claim.date)} />
      </div>
    </div>
  );
};

// Generic Template Components for other types
const HealthDocument = ({ claim }: { claim: Claim }) => (
  <div className="p-12">
    <DocumentHeader
      emoji="🏥"
      title="Health Insurance Claim Form"
      claimNo={claim.id}
      date={formatDate(claim.date)}
      status={claim.status}
      icon={Heart}
    />
    <SectionTitle emoji="🧍" icon={User} title="Policyholder Information" />
    <InfoGrid
      items={[
        { label: "Name", value: claim.claimant },
        { label: "Policy Number", value: claim.policyNumber, mono: true },
        { label: "Date of Birth", value: claim.healthInfo?.dob },
        { label: "Contact Number", value: claim.phoneNumber },
        { label: "Address", value: "45 Maple Street, New York, NY" },
      ]}
    />
    <SectionTitle emoji="🏥" icon={Heart} title="Patient Details" />
    <InfoGrid
      items={[
        { label: "Patient Name", value: claim.healthInfo?.patientName },
        {
          label: "Relationship to Policyholder",
          value: claim.healthInfo?.relationship,
        },
      ]}
    />
    <SectionTitle emoji="🏨" icon={Home} title="Hospital Information" />
    <InfoGrid
      items={[
        { label: "Hospital Name", value: claim.healthInfo?.hospitalName },
        { label: "Hospital Address", value: claim.healthInfo?.hospitalAddress },
        { label: "Admission Date", value: claim.healthInfo?.admissionDate },
        { label: "Discharge Date", value: claim.healthInfo?.dischargeDate },
        { label: "Doctor Name", value: claim.healthInfo?.doctorName },
      ]}
    />
    <SectionTitle emoji="📋" icon={Stethoscope} title="Diagnosis & Treatment" />
    <InfoGrid
      items={[
        { label: "Diagnosis", value: claim.healthInfo?.diagnosis },
        { label: "Treatment Provided", value: claim.healthInfo?.treatment },
        {
          label: "Surgery Performed",
          value: claim.healthInfo?.surgeryPerformed ? "Yes" : "No",
        },
      ]}
    />
    <SectionTitle
      emoji="💰"
      icon={ClipboardList}
      title="Itemized Medical Expenses"
    />
    <ItemizedTable data={claim.itemizedLoss} totalLabel="Total Claimed" />
    <Declaration name={claim.claimant} date={formatDate(claim.date)} />
  </div>
);

const LifeDocument = ({ claim }: { claim: Claim }) => (
  <div className="p-12">
    <DocumentHeader
      emoji="🧬"
      title="Life Insurance Claim Form"
      claimNo={claim.id}
      date={formatDate(claim.date)}
      status={claim.status}
      icon={Heart}
    />
    <SectionTitle emoji="👤" icon={User} title="Policyholder (Deceased)" />
    <InfoGrid
      items={[
        { label: "Name", value: claim.lifeInfo?.deceasedName },
        { label: "Policy Number", value: claim.policyNumber, mono: true },
        { label: "Date of Birth", value: claim.lifeInfo?.deceasedDob },
        { label: "Date of Death", value: claim.lifeInfo?.dateOfDeath },
        { label: "Cause of Death", value: claim.lifeInfo?.causeOfDeath },
      ]}
    />
    <SectionTitle
      emoji="👨‍👩‍👧"
      icon={Heart}
      title="Nominee / Beneficiary Details"
    />
    <InfoGrid
      items={[
        { label: "Name", value: claim.lifeInfo?.nomineeName },
        { label: "Relationship", value: claim.lifeInfo?.nomineeRelationship },
        { label: "Contact Number", value: claim.lifeInfo?.nomineeContact },
        {
          label: "Bank Account Details",
          value: claim.lifeInfo?.bankDetails,
          mono: true,
        },
      ]}
    />
    <SectionTitle emoji="📄" icon={FileText} title="Policy Information" />
    <InfoGrid
      items={[
        { label: "Policy Start Date", value: claim.lifeInfo?.policyStartDate },
        {
          label: "Sum Assured",
          value: `$${claim.lifeInfo?.sumAssured.toLocaleString()} `,
        },
        { label: "Premium Status", value: "Active" },
      ]}
    />
    <SectionTitle emoji="💰" icon={ClipboardList} title="Claim Amount" />
    <div className="p-6 bg-gray-900 text-white rounded-2xl flex justify-between items-center mt-4 shadow-xl">
      <span className="font-bold uppercase tracking-widest text-[10px]">
        Amount Claimed
      </span>
      <span className="text-3xl font-black font-mono">
        ${claim.lifeInfo?.sumAssured.toLocaleString()}
      </span>
    </div>
    <Declaration name={claim.claimant} date={formatDate(claim.date)} />
  </div>
);

const PropertyDocument = ({ claim }: { claim: Claim }) => (
  <div className="p-12">
    <DocumentHeader
      emoji="🏠"
      title="Home / Property Insurance Claim Form"
      claimNo={claim.id}
      date={formatDate(claim.date)}
      status={claim.status}
      icon={Home}
    />
    <SectionTitle emoji="🧍" icon={User} title="Policyholder Information" />
    <InfoGrid
      items={[
        { label: "Name", value: claim.claimant },
        { label: "Policy Number", value: claim.policyNumber, mono: true },
        {
          label: "Address of Insured Property",
          value: claim.propertyInfo?.address,
        },
        { label: "Contact Number", value: claim.phoneNumber },
      ]}
    />
    <SectionTitle emoji="🔥" icon={AlertTriangle} title="Incident Details" />
    <InfoGrid
      items={[
        { label: "Incident Date", value: formatDate(claim.date) },
        { label: "Type of Incident", value: claim.propertyInfo?.incidentType },
        {
          label: "Location of Damage",
          value: claim.propertyInfo?.locationOfDamage,
        },
        {
          label: "Fire Department Involved",
          value: claim.propertyInfo?.fireDeptInvolved ? "Yes" : "No",
        },
        {
          label: "Report Number",
          value: claim.propertyInfo?.reportNumber,
          mono: true,
        },
      ]}
    />
    <SectionTitle emoji="📝" icon={FileText} title="Description of Damage" />
    <p className="text-sm text-gray-700 leading-7 italic bg-gray-50 p-4 rounded-xl border border-gray-100">
      {claim.description}
    </p>
    <SectionTitle
      emoji="💰"
      icon={ClipboardList}
      title="Itemized Damage Assessment"
    />
    <ItemizedTable data={claim.itemizedLoss} totalLabel="Total Claimed" />
    <Declaration name={claim.claimant} date={formatDate(claim.date)} />
  </div>
);

// --- Component Logic ---

const RadialScore = ({ score }: { score: number }) => {
  const size = 160;
  const strokeWidth = 12;
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (score / 100) * circumference;

  let color = "#34A853";
  let label = "Low Risk";
  if (score > 80) {
    color = "#EF4444";
    label = "Critical";
  } else if (score > 50) {
    color = "#F59E0B";
    label = "Medium";
  }

  return (
    <div
      className="relative flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg className="transform -rotate-90 w-full h-full">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="transparent"
          className="text-gray-100 dark:text-white/10"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span
          className={cn(
            "text-5xl font-bold tracking-tighter text-gray-900 dark:text-white",
          )}
        >
          {score}
        </span>
        <span
          className={cn(
            "text-xs font-bold uppercase tracking-wider mt-1",
            score > 80
              ? "text-rose-500"
              : score > 50
                ? "text-amber-500"
                : "text-emerald-500",
          )}
        >
          {label}
        </span>
      </div>
    </div>
  );
};

const DocumentViewer = ({
  claim,
  zoom,
  documentRef,
}: {
  claim: Claim;
  zoom: number;
  documentRef: React.RefObject<HTMLDivElement>;
}) => {
  const renderTemplate = () => {
    switch (claim.type) {
      case "Vehicle":
        return <VehicleDocument claim={claim} />;
      case "Health":
        return <HealthDocument claim={claim} />;
      case "Life":
        return <LifeDocument claim={claim} />;
      case "Property":
        return <PropertyDocument claim={claim} />;
      default:
        return (
          <div className="p-12 text-center text-gray-400">
            Template for {claim.type} in development
          </div>
        );
    }
  };

  return (
    <div
      ref={documentRef}
      className="bg-white text-gray-900 rounded-[32px] shadow-2xl overflow-hidden min-h-[1100px] font-sans relative border-8 border-gray-50 dark:border-white/5 transition-all duration-300 origin-top transform"
      style={{ transform: `scale(${zoom})` }}
    >
      <div className="absolute top-0 right-0 p-8 flex items-center gap-2 text-gray-300 pointer-events-none opacity-20">
        <Shield size={120} />
      </div>
      {renderTemplate()}
    </div>
  );
};

// --- Main Page Component ---

// --- Main Page Component ---

export const Claims = ({
  initialClaimId,
  onAddNotification,
}: {
  initialClaimId?: string;
  onAddNotification?: (msg: string) => void;
}) => {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [policies, setPolicies] = useState<any[]>([]); // Using any[] for now to avoid strict type issues, or import Policy
  const [selectedClaim, setSelectedClaim] = useState<Claim | null>(null);
  const [filterQuery, setFilterQuery] = useState("");
  const [riskThreshold, setRiskThreshold] = useState(0);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New: Document Viewer controls state
  const [zoom, setZoom] = useState(1);
  const documentRef = useRef<HTMLDivElement>(null);
  // Track expanded groups
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>(
    {},
  );

  // Load claims and policies from API on mount
  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Fetch claims and policies independently so one failure doesn't block the other
        const [claimsResult, policiesResult] = await Promise.allSettled([
          fetchClaims(),
          import("../src/api/endpoints").then((m) => m.fetchPolicies()),
        ]);

        if (claimsResult.status === "fulfilled") {
          setClaims(claimsResult.value);
        } else {
          console.error("Failed to load claims:", claimsResult.reason);
          setError(
            claimsResult.reason?.response?.data?.detail ||
              "Failed to load claims. Is the backend running?",
          );
        }

        if (policiesResult.status === "fulfilled") {
          setPolicies(policiesResult.value);
        } else {
          console.error("Failed to load policies:", policiesResult.reason);
          // Non-critical: claims still work without policy titles
        }
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, []);

  // Auto-refresh claims when there are claims with PENDING or ANALYZING fraud status
  useEffect(() => {
    const hasAnalyzingClaims = claims.some(
      (c) => c.fraudStatus === 'PENDING' || c.fraudStatus === 'ANALYZING'
    );

    if (!hasAnalyzingClaims) return;

    console.log('[AUTO-REFRESH] Claims in progress detected, polling every 5 seconds...');

    const refreshInterval = setInterval(async () => {
      try {
        const updatedClaims = await fetchClaims();
        setClaims(updatedClaims);
        
        // Update selected claim if it exists
        if (selectedClaim) {
          const updated = updatedClaims.find((c) => c.id === selectedClaim.id);
          if (updated) {
            setSelectedClaim(updated);
          }
        }

        // Check if any claims are still analyzing
        const stillAnalyzing = updatedClaims.some(
          (c) => c.fraudStatus === 'PENDING' || c.fraudStatus === 'ANALYZING'
        );

        if (!stillAnalyzing) {
          console.log('[AUTO-REFRESH] All claims completed analysis, stopping polling.');
        }
      } catch (err) {
        console.error('Failed to refresh claims:', err);
      }
    }, 5000); // Poll every 5 seconds

    return () => {
      console.log('[AUTO-REFRESH] Cleanup: stopping polling interval');
      clearInterval(refreshInterval);
    };
  }, [claims, selectedClaim]);

  useEffect(() => {
    if (initialClaimId) {
      const claim = claims.find((c) => c.id === initialClaimId);
      if (claim) setSelectedClaim(claim);
    }
  }, [initialClaimId, claims]);

  const handleStatusUpdate = async (status: Status) => {
    if (!selectedClaim) return;
    try {
      const updated = await updateClaimStatus(selectedClaim.id, status);
      setSelectedClaim(updated);
      setClaims((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
      if (onAddNotification)
        onAddNotification(`Claim ${selectedClaim.id} updated to ${status} `);
    } catch (err: any) {
      console.error("Failed to update claim status:", err);
      if (onAddNotification)
        onAddNotification(
          `Failed to update claim: ${err.response?.data?.detail || "Unknown error"} `,
        );
    }
  };

  const handleAiDeepScan = async () => {
    if (!selectedClaim) return;
    setIsAnalyzing(true);
    try {
      const result = await runAiScan(selectedClaim.id);
      const updated = {
        ...selectedClaim,
        aiAnalysis: {
          score: result.risk_score,
          reasoning: result.reasoning,
          recommendations: result.fraud_indicators
            ? result.fraud_indicators.map((i: string) => `• ${i}`)
            : [],
          fraudIndicators: result.fraud_indicators,
          rulesChecked: result.rules_checked || [],
        },
        riskScore: result.risk_score,
      };
      setSelectedClaim(updated);
      setClaims((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
      if (onAddNotification)
        onAddNotification(`AI Scan Complete for ${selectedClaim.id}`);
    } catch (err: any) {
      console.error("AI scan failed:", err);
      if (onAddNotification)
        onAddNotification(
          `AI Scan failed: ${err.response?.data?.detail || "Unknown error"} `,
        );
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handlePrint = () => {
    if (!documentRef.current) return;
    const content = documentRef.current.innerHTML;
    const printWindow = window.open("", "_blank");
    if (printWindow) {
      printWindow.document.write(`
    <html>
                <head>
                    <title>Vantage Document - ${selectedClaim?.id}</title>
                    <script src="https://cdn.tailwindcss.com"></script>
                    <link href="https://fonts.googleapis.com/css2?family=Dancing+Script:wght@400;700&display=swap" rel="stylesheet">
                    <style>
                        body { background: white; -webkit-print-color-adjust: exact; }
                        @page { margin: 20mm; }
                    </style>
                </head>
                <body class="p-0">
                    <div class="max-w-4xl mx-auto border-0">
                        ${content}
                    </div>
                </body>
            </html>
    `);
      printWindow.document.close();
      printWindow.focus();
      setTimeout(() => {
        printWindow.print();
        printWindow.close();
      }, 500);
    }
  };

  const filteredClaims = claims.filter((c) => {
    const matchesText =
      c.id.toLowerCase().includes(filterQuery.toLowerCase()) ||
      c.claimant.toLowerCase().includes(filterQuery.toLowerCase());
    const matchesRisk = c.riskScore >= riskThreshold;
    return matchesText && matchesRisk;
  });

  const resetFilters = () => {
    setFilterQuery("");
    setRiskThreshold(0);
  };

  // Toggle group expansion
  const toggleGroup = (groupName: string) => {
    setExpandedGroups((prev) => ({
      ...prev,
      [groupName]: !prev[groupName],
    }));
  };

  // Grouping Logic
  const claimsByPolicy = filteredClaims.reduce(
    (acc, claim) => {
      const policy = policies.find(
        (p) => p.policyNumber === claim.policyNumber,
      );
      const groupName = policy
        ? policy.title
        : claim.type
          ? `${claim.type} Claims`
          : "Other Claims";
      if (!acc[groupName]) acc[groupName] = [];
      acc[groupName].push(claim);
      return acc;
    },
    {} as Record<string, Claim[]>,
  );

  return (
    <div className="relative min-h-screen flex flex-col overflow-x-hidden bg-transparent text-gray-900 dark:text-white transition-colors duration-500">
      {/* 3D Background effect */}
      <div className="absolute inset-0 z-0 opacity-5 pointer-events-none fixed">
        <ThreeScene />
      </div>

      <AnimatePresence mode="wait">
        {!selectedClaim ? (
          <motion.div
            key="list"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="relative z-10 flex-1 flex flex-col p-8"
          >
            <div className="flex flex-col md:flex-row justify-between items-end mb-8 shrink-0">
              <div>
                <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2 tracking-tight">
                  Claims Queue
                </h1>
                <p className="text-gray-500">
                  Review and adjudicate incoming claims.
                </p>
              </div>
              <div className="flex flex-col md:flex-row gap-6 items-center">
                {/* Refresh Button */}
                <button
                  onClick={async () => {
                    try {
                      const updatedClaims = await fetchClaims();
                      setClaims(updatedClaims);
                      if (onAddNotification) {
                        onAddNotification('Claims refreshed successfully');
                      }
                    } catch (err) {
                      console.error('Failed to refresh claims:', err);
                      if (onAddNotification) {
                        onAddNotification('Failed to refresh claims');
                      }
                    }
                  }}
                  className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors shadow-sm"
                  title="Refresh claims queue"
                >
                  <RefreshCw size={16} />
                  <span className="text-sm font-medium">Refresh</span>
                </button>
                
                {/* Risk Threshold Slider */}
                <div className="bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-2xl p-3 px-6 shadow-sm flex items-center gap-6 min-w-[300px]">
                  <div className="flex flex-col">
                    <span className="text-[10px] font-black uppercase tracking-widest text-gray-400">
                      Min Risk Score
                    </span>
                    <span className="text-lg font-black text-orange-500">
                      {riskThreshold}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={riskThreshold}
                    onChange={(e) => setRiskThreshold(parseInt(e.target.value))}
                    className="flex-1 h-1.5 bg-gray-100 dark:bg-white/10 rounded-lg appearance-none cursor-pointer accent-orange-500"
                  />
                </div>

                <div className="flex gap-3">
                  <div className="relative group">
                    <Search
                      className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-[var(--primary)] transition-colors"
                      size={18}
                    />
                    <input
                      type="text"
                      value={filterQuery}
                      onChange={(e) => setFilterQuery(e.target.value)}
                      placeholder="Search holders..."
                      className="pl-10 pr-6 py-2.5 rounded-xl bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 focus:ring-2 focus:ring-[var(--primary)]/50 outline-none text-sm w-48 shadow-sm transition-all"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Auto-Refresh Status Indicator */}
            {claims.some((c) => c.fraudStatus === 'PENDING' || c.fraudStatus === 'ANALYZING') && (
              <div className="mb-4 flex items-center gap-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl px-4 py-3 text-sm">
                <RefreshCw className="animate-spin text-blue-600 dark:text-blue-400" size={16} />
                <span className="text-blue-700 dark:text-blue-300 font-medium">
                  Auto-refreshing claims with analysis in progress (every 5 seconds)
                </span>
              </div>
            )}

            {/* Uniform List View with Grouping */}
            <div className="space-y-6 pb-20">
              {error ? (
                <div className="flex flex-col items-center justify-center py-20 text-red-500 bg-red-50/50 dark:bg-red-900/10 rounded-3xl border border-dashed border-red-200 dark:border-red-900/30">
                  <AlertTriangle size={48} className="opacity-50 mb-4" />
                  <p className="font-bold text-lg mb-1">
                    Failed to load claims
                  </p>
                  <p className="text-sm text-red-400 mb-4 max-w-md text-center">
                    {error}
                  </p>
                  <button
                    onClick={() => window.location.reload()}
                    className="px-6 py-2 bg-orange-500 text-white rounded-xl font-bold hover:bg-orange-600 transition-colors"
                  >
                    Reload Page
                  </button>
                </div>
              ) : isLoading ? (
                <div className="flex flex-col items-center justify-center py-20 text-gray-400">
                  <RefreshCw
                    size={32}
                    className="animate-spin mb-4 opacity-50"
                  />
                  <p className="font-medium">Loading claims...</p>
                </div>
              ) : filteredClaims.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 text-gray-400 bg-white/50 dark:bg-white/5 rounded-3xl border border-dashed border-gray-200 dark:border-white/10">
                  <Activity size={48} className="opacity-20 mb-4" />
                  <p className="font-medium">
                    No claims match the selected filters.
                  </p>
                  <button
                    onClick={resetFilters}
                    className="px-6 py-2 mt-4 bg-orange-500 text-white rounded-xl font-bold hover:bg-orange-600 transition-colors"
                  >
                    Clear Filters
                  </button>
                </div>
              ) : (
                Object.entries(claimsByPolicy).map(
                  ([groupName, groupClaims]) => {
                    const isExpanded = expandedGroups[groupName] !== false; // Default to expanded

                    return (
                      <div key={groupName} className="space-y-4">
                        {/* Group Header */}
                        <div
                          className="flex items-center gap-3 cursor-pointer hover:opacity-80 transition-opacity select-none"
                          onClick={() => toggleGroup(groupName)}
                        >
                          <div className="p-2 bg-white dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5 shadow-sm">
                            <FileText
                              size={16}
                              className="text-[var(--primary)]"
                            />
                          </div>
                          <h3 className="text-lg font-bold text-gray-800 dark:text-gray-200">
                            {groupName}
                          </h3>
                          <Badge variant="info" className="text-xs">
                            {groupClaims.length}
                          </Badge>
                          <div className="flex-1 h-px bg-gray-200 dark:bg-white/10 ml-4" />
                          <motion.div
                            animate={{ rotate: isExpanded ? 0 : -90 }}
                            transition={{ duration: 0.2 }}
                          >
                            <ChevronRight size={18} className="text-gray-400" />
                          </motion.div>
                        </div>

                        {/* Group Content */}
                        <AnimatePresence>
                          {isExpanded && (
                            <motion.div
                              initial={{ height: 0, opacity: 0 }}
                              animate={{ height: "auto", opacity: 1 }}
                              exit={{ height: 0, opacity: 0 }}
                              transition={{ duration: 0.3 }}
                              className="overflow-hidden"
                            >
                              <Card className="flex flex-col p-0 border border-gray-200 dark:border-white/10 shadow-lg bg-white/90 dark:bg-white/5 backdrop-blur-xl overflow-hidden rounded-2xl">
                                <div className="grid grid-cols-[1.2fr_1.8fr_1fr_1.2fr_1.5fr_1.2fr_auto] gap-4 px-6 py-4 border-b border-gray-200 dark:border-white/10 bg-gradient-to-r from-gray-50 to-gray-100/50 dark:from-white/5 dark:to-white/10 text-[10px] font-black text-gray-500 dark:text-gray-400 uppercase tracking-[0.15em]">
                                  <div>Claim ID</div>
                                  <div>Policy Holder</div>
                                  <div>Amount</div>
                                  <div>Date</div>
                                  <div>Risk Score</div>
                                  <div>Status</div>
                                  <div></div>
                                </div>

                                <div className="divide-y divide-gray-100 dark:divide-white/5">
                                  {groupClaims.map((claim) => (
                                    <motion.div
                                      key={claim.id}
                                      onClick={() => {
                                        setSelectedClaim(claim);
                                        setZoom(1);
                                      }}
                                      whileHover={{ x: 4 }}
                                      className="grid grid-cols-[1.2fr_1.8fr_1fr_1.2fr_1.5fr_1.2fr_auto] gap-4 px-6 py-5 hover:bg-orange-50/50 dark:hover:bg-orange-900/10 transition-all cursor-pointer group items-center"
                                    >
                                      <div className="font-bold text-gray-900 dark:text-white group-hover:text-orange-600 dark:group-hover:text-orange-400 transition-colors">
                                        {claim.id}
                                      </div>
                                      <div className="font-semibold text-gray-700 dark:text-gray-300">
                                        {claim.claimant}
                                      </div>
                                      <div className="font-mono text-gray-900 dark:text-gray-100 font-bold">
                                        ${claim.amount.toLocaleString()}
                                      </div>
                                      <div className="text-xs text-gray-500 font-medium">
                                        {formatDate(claim.date)}
                                      </div>
                                      <div className="flex flex-col gap-1.5 pr-4">
                                        {claim.fraudStatus === "PENDING" ||
                                        claim.fraudStatus === "ANALYZING" ? (
                                          <div className="flex items-center gap-2">
                                            <span className="px-3 py-1 rounded-full text-[10px] font-bold text-blue-700 bg-blue-100 dark:text-blue-400 dark:bg-blue-900/30 animate-pulse">
                                              🔄 IN PROGRESS
                                            </span>
                                          </div>
                                        ) : claim.riskScore != null ? (
                                          <>
                                            <div className="flex justify-between items-center text-[10px] font-bold">
                                              <span
                                                className={cn(
                                                  "px-2 py-0.5 rounded-full",
                                                  claim.riskScore >= 80
                                                    ? "text-red-700 bg-red-100 dark:text-red-400 dark:bg-red-900/30"
                                                    : claim.riskScore >= 50
                                                      ? "text-amber-700 bg-amber-100 dark:text-amber-400 dark:bg-amber-900/30"
                                                      : "text-emerald-700 bg-emerald-100 dark:text-emerald-400 dark:bg-emerald-900/30",
                                                )}
                                              >
                                                {claim.riskScore}%
                                              </span>
                                            </div>
                                            <div className="h-2 w-full bg-gray-100 dark:bg-white/10 rounded-full overflow-hidden">
                                              <motion.div
                                                initial={{ width: 0 }}
                                                animate={{
                                                  width: `${claim.riskScore}%`,
                                                }}
                                                transition={{
                                                  duration: 0.5,
                                                  ease: "easeOut",
                                                }}
                                                className={cn(
                                                  "h-full rounded-full",
                                                  claim.riskScore >= 80
                                                    ? "bg-red-500"
                                                    : claim.riskScore >= 50
                                                      ? "bg-amber-500"
                                                      : "bg-emerald-500",
                                                )}
                                              />
                                            </div>
                                          </>
                                        ) : (
                                          <span className="text-xs text-gray-400 italic">
                                            Pending
                                          </span>
                                        )}
                                      </div>
                                      <div>
                                        <Badge
                                          className={cn(
                                            "rounded-full px-4 py-1.5 font-black text-[9px] tracking-widest border-0",
                                            claim.status === Status.Approved
                                              ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400"
                                              : claim.status === Status.Rejected
                                                ? "bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-400"
                                                : claim.status ===
                                                    Status.Flagged
                                                  ? "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400"
                                                  : claim.status ===
                                                      Status.InReview
                                                    ? "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400"
                                                    : "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400",
                                          )}
                                        >
                                          {claim.status}
                                        </Badge>
                                      </div>
                                      <div className="text-gray-300 group-hover:text-orange-500 transition-all flex justify-end">
                                        <ChevronRight
                                          size={20}
                                          className="group-hover:translate-x-1 transition-transform"
                                        />
                                      </div>
                                    </motion.div>
                                  ))}
                                </div>
                              </Card>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    );
                  },
                )
              )}
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="detail"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="relative z-10 flex-1 flex flex-col h-full overflow-hidden"
          >
            {/* Uniform Header Bar */}
            <div className="h-24 px-8 flex items-center justify-between border-b border-gray-200 dark:border-white/10 bg-white/80 dark:bg-[#0F172A]/80 backdrop-blur-xl shrink-0 z-20 shadow-sm">
              <div className="flex items-center gap-6">
                <button
                  onClick={() => setSelectedClaim(null)}
                  className="p-2.5 rounded-xl text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/10 transition-all"
                  title="Back to Claims List"
                >
                  <ChevronLeft size={24} />
                </button>
                <div className="h-12 w-px bg-gray-200 dark:bg-white/10" />
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <h2 className="text-2xl font-black text-gray-900 dark:text-white tracking-tight">
                      Claim #{selectedClaim.id}
                    </h2>
                    <Badge
                      className={cn(
                        "px-3 py-1 text-xs font-bold uppercase tracking-wider",
                        selectedClaim.riskScore > 80
                          ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                          : selectedClaim.riskScore > 50
                            ? "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
                            : "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400",
                      )}
                    >
                      {selectedClaim.riskLevel} Risk
                    </Badge>
                    <Badge className="bg-gray-100 text-gray-700 dark:bg-white/10 dark:text-gray-300 px-3 py-1 text-xs font-bold uppercase">
                      {selectedClaim.status}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-500 font-medium">
                    {selectedClaim.claimant} • Policy #
                    {selectedClaim.policyNumber} • {selectedClaim.type}{" "}
                    Insurance • ${selectedClaim.amount.toLocaleString()}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex bg-gray-100 dark:bg-white/10 rounded-xl p-1 border border-gray-200 dark:border-white/5">
                  <button
                    onClick={() => setZoom((prev) => Math.max(prev - 0.1, 0.5))}
                    className="p-2 text-gray-500 hover:text-gray-900 dark:hover:text-white hover:bg-white dark:hover:bg-white/10 rounded-lg transition-all"
                    title="Zoom Out"
                  >
                    <ZoomOut size={16} />
                  </button>
                  <button
                    onClick={() => setZoom((prev) => Math.min(prev + 0.1, 2.0))}
                    className="p-2 text-gray-500 hover:text-gray-900 dark:hover:text-white hover:bg-white dark:hover:bg-white/10 rounded-lg transition-all"
                    title="Zoom In"
                  >
                    <ZoomIn size={16} />
                  </button>
                  <button
                    onClick={handlePrint}
                    className="p-2 text-gray-500 hover:text-gray-900 dark:hover:text-white hover:bg-white dark:hover:bg-white/10 rounded-lg transition-all"
                    title="Print Document"
                  >
                    <Printer size={16} />
                  </button>
                </div>
              </div>
            </div>

            <div className="flex-1 flex overflow-hidden">
              <div className="flex-1 bg-gray-200/50 dark:bg-[#0a0a0a] overflow-auto p-12 flex justify-center custom-scrollbar">
                <div className="w-full max-w-4xl shadow-2xl rounded-[32px]">
                  <DocumentViewer
                    claim={selectedClaim}
                    zoom={zoom}
                    documentRef={documentRef}
                  />
                </div>
              </div>
              <div className="w-[420px] border-l border-gray-200 dark:border-white/10 bg-white dark:bg-[#0F172A] flex flex-col overflow-hidden shadow-2xl z-10 transition-all">
                <div className="flex-1 overflow-y-auto custom-scrollbar p-8 space-y-10">
                  <section>
                    <h3 className="text-[10px] font-black uppercase text-gray-400 tracking-[0.2em] mb-8">
                      AI Risk Assessment
                    </h3>
                    <div className="flex flex-col items-center">
                      <div className="mb-8 relative group">
                        <RadialScore score={selectedClaim.riskScore} />
                        <div className="absolute inset-0 bg-orange-500/10 blur-3xl rounded-full -z-10 transition-all duration-1000 group-hover:bg-orange-500/20" />
                      </div>
                      <div className="w-full bg-gray-50 dark:bg-white/5 rounded-2xl p-6 border border-gray-100 dark:border-white/10 shadow-sm">
                        <p className="text-[10px] text-gray-400 uppercase font-black tracking-widest mb-3">
                          AI Reasoning
                        </p>
                        <p className="text-xs text-gray-500 leading-relaxed italic">
                          {selectedClaim.aiAnalysis?.reasoning ||
                            "Standard claim profile. Perform AI Deep Scan for detailed pattern recognition."}
                        </p>
                      </div>
                    </div>
                  </section>
                  <section>
                    <h3 className="text-[10px] font-black uppercase text-gray-400 tracking-[0.2em] mb-4">
                      Fraud Indicators
                    </h3>
                    <div className="space-y-3">
                      {selectedClaim.riskScore > 50 ? (
                        <div className="p-4 rounded-xl border border-rose-200 bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:border-rose-900/50 dark:text-rose-400 flex gap-3">
                          <Shield size={18} className="shrink-0" />
                          <div>
                            <h4 className="font-bold text-sm">
                              Potential Risk Pattern
                            </h4>
                            <p className="text-xs mt-1">
                              Identifiers match known high-risk history.
                            </p>
                          </div>
                        </div>
                      ) : (
                        <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:border-emerald-900/50 dark:text-emerald-400 flex gap-3">
                          <CheckCircle size={18} className="shrink-0" />
                          <div>
                            <h4 className="font-bold text-sm">
                              Integrity Verified
                            </h4>
                            <p className="text-xs mt-1">
                              No anomalies detected in submission metadata.
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  </section>
                  
                  {/* Detailed Rules Analysis Section */}
                  {selectedClaim.aiAnalysis?.rulesChecked && selectedClaim.aiAnalysis.rulesChecked.length > 0 && (
                    <section>
                      <h3 className="text-[10px] font-black uppercase text-gray-400 tracking-[0.2em] mb-4">
                        🔍 Fraud Detection Rules Evaluated
                      </h3>
                      <div className="space-y-2">
                        {selectedClaim.aiAnalysis.rulesChecked.map((rule, idx) => {
                          const isPassed = rule.result.includes('PASS') || rule.result.includes('N/A');
                          const isWarning = rule.result.includes('CAUTION') || rule.result.includes('WARNING');
                          const isAlert = rule.result.includes('ALERT') || rule.result.includes('SUSPICIOUS') || rule.result.includes('ANOMALY');
                          
                          return (
                            <div
                              key={idx}
                              className={`p-3 rounded-lg border text-xs ${
                                isPassed
                                  ? 'border-emerald-200 bg-emerald-50/50 dark:bg-emerald-500/5 dark:border-emerald-900/30'
                                  : isWarning
                                  ? 'border-yellow-200 bg-yellow-50/50 dark:bg-yellow-500/5 dark:border-yellow-900/30'
                                  : 'border-rose-200 bg-rose-50/50 dark:bg-rose-500/5 dark:border-rose-900/30'
                              }`}
                            >
                              <div className="flex items-start justify-between mb-1">
                                <span className="font-semibold text-gray-700 dark:text-gray-300">
                                  {rule.rule}
                                </span>
                                <span
                                  className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                                    isPassed
                                      ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
                                      : isWarning
                                      ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                                      : 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400'
                                  }`}
                                >
                                  {rule.impact}
                                </span>
                              </div>
                              <div className="text-gray-600 dark:text-gray-400 text-[11px] flex items-center gap-1">
                                <span className="font-medium">{rule.result}</span>
                                <span className="text-gray-400">•</span>
                                <span>{rule.detail}</span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                      <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-500/5 border border-blue-200 dark:border-blue-900/30 rounded-lg">
                        <p className="text-[11px] text-blue-700 dark:text-blue-400">
                          ℹ️ <strong>{selectedClaim.aiAnalysis.rulesChecked.length} fraud detection rules</strong> were evaluated to calculate the final risk score of <strong>{selectedClaim.riskScore}%</strong>
                        </p>
                      </div>
                    </section>
                  )}
                </div>

                {/* Uniform Action Panel */}
                <div className="p-6 border-t border-gray-200 dark:border-white/10 bg-gray-50/50 dark:bg-white/5 space-y-3">
                  <h3 className="text-[10px] font-black uppercase text-gray-400 tracking-[0.2em] mb-4">
                    Claim Actions
                  </h3>

                  {/* Primary Actions */}
                  <div className="space-y-2">
                    <Button
                      onClick={() => handleStatusUpdate(Status.Approved)}
                      disabled={selectedClaim.status === Status.Approved}
                      className={cn(
                        "w-full h-12 rounded-xl font-bold text-sm uppercase tracking-wider transition-all border-0 shadow-lg",
                        selectedClaim.status === Status.Approved
                          ? "bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-not-allowed"
                          : "bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white shadow-emerald-500/20 hover:shadow-emerald-500/40 hover:scale-[1.02]",
                      )}
                    >
                      <CheckCircle size={18} className="mr-2" />
                      {selectedClaim.status === Status.Approved
                        ? "Approved"
                        : "Approve Claim"}
                    </Button>

                    <Button
                      onClick={() => handleStatusUpdate(Status.InReview)}
                      disabled={selectedClaim.status === Status.InReview}
                      className={cn(
                        "w-full h-12 rounded-xl font-bold text-sm uppercase tracking-wider transition-all border-0 shadow-lg",
                        selectedClaim.status === Status.InReview
                          ? "bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-not-allowed"
                          : "bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white shadow-blue-500/20 hover:shadow-blue-500/40 hover:scale-[1.02]",
                      )}
                    >
                      <Activity size={18} className="mr-2" />
                      {selectedClaim.status === Status.InReview
                        ? "In Review"
                        : "Review Claim"}
                    </Button>

                    <Button
                      onClick={() => handleStatusUpdate(Status.Rejected)}
                      disabled={selectedClaim.status === Status.Rejected}
                      className={cn(
                        "w-full h-12 rounded-xl font-bold text-sm uppercase tracking-wider transition-all border-0 shadow-lg",
                        selectedClaim.status === Status.Rejected
                          ? "bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-not-allowed"
                          : "bg-gradient-to-r from-rose-500 to-rose-600 hover:from-rose-600 hover:to-rose-700 text-white shadow-rose-500/20 hover:shadow-rose-500/40 hover:scale-[1.02]",
                      )}
                    >
                      <X size={18} className="mr-2" />
                      {selectedClaim.status === Status.Rejected
                        ? "Rejected"
                        : "Reject Claim"}
                    </Button>
                  </div>

                  {/* AI Scan Button */}
                  <div className="pt-3 border-t border-gray-200 dark:border-white/10">
                    <Button
                      isLoading={isAnalyzing}
                      onClick={handleAiDeepScan}
                      className="w-full h-12 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 rounded-xl text-white font-bold shadow-lg shadow-orange-500/20 hover:shadow-orange-500/40 flex items-center justify-center gap-2 transition-all hover:scale-[1.02] border-0 uppercase tracking-wider text-sm"
                    >
                      <Sparkles size={18} />
                      {isAnalyzing ? "Scanning..." : "AI Deep Scan"}
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
