import React, { useState, useEffect } from "react";
import { Card, Button, Badge, cn, Skeleton } from "../components/UIComponents";
import { MOCK_ALERTS, RISK_DISTRIBUTION } from "../constants";
import {
  ShieldAlert,
  Zap,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Activity,
  FileText,
  Share2,
  Search,
  Filter,
} from "lucide-react";
import { detectFraudPatterns } from "../services/geminiService";
import { fetchClaims } from "../src/api/endpoints";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
  PieChart,
  Pie,
  Legend,
} from "recharts";
import { motion, AnimatePresence } from "framer-motion";

// Mock Data for Charts
const FRAUD_TRENDS = [
  { month: "Jun", detected: 12, prevented: 10 },
  { month: "Jul", detected: 19, prevented: 18 },
  { month: "Aug", detected: 15, prevented: 12 },
  { month: "Sep", detected: 25, prevented: 24 },
  { month: "Oct", detected: 32, prevented: 30 },
  { month: "Nov", detected: 28, prevented: 27 },
];

const ALERT_TYPES = [
  { name: "Identity Theft", count: 12, color: "#EF4444" },
  { name: "Doc Fabrication", count: 8, color: "#F59E0B" },
  { name: "Velocity Check", count: 15, color: "#8B5CF6" },
  { name: "IP Mismatch", count: 5, color: "#3B82F6" },
];

const StatCard = ({ title, value, change, icon: Icon, colorClass }: any) => (
  <Card className="p-6 flex items-center justify-between border border-gray-100 dark:border-white/10 bg-white/60 dark:bg-[#1C1C1E]/60 backdrop-blur-md shadow-sm hover:shadow-md transition-all">
    <div>
      <p className="text-[10px] font-black uppercase tracking-widest text-gray-400 mb-1">
        {title}
      </p>
      <h3 className="text-3xl font-black text-gray-900 dark:text-white tracking-tighter">
        {value}
      </h3>
      {change && (
        <div className="flex items-center gap-1 mt-1 text-[10px] font-bold text-emerald-600">
          <TrendingUp size={10} /> {change}
        </div>
      )}
    </div>
    <div className={cn("p-3 rounded-2xl", colorClass)}>
      <Icon size={24} />
    </div>
  </Card>
);

export const FraudDetection = () => {
  const [aiAnalysis, setAiAnalysis] = useState<string>("");
  const [analyzing, setAnalyzing] = useState(false);
  const [claims, setClaims] = useState<any[]>([]);
  const [fraudTrends, setFraudTrends] = useState<any[]>([
    { month: "Sep", detected: 12, prevented: 10 },
    { month: "Oct", detected: 19, prevented: 18 },
    { month: "Nov", detected: 15, prevented: 12 },
    { month: "Dec", detected: 25, prevented: 24 },
    { month: "Jan", detected: 32, prevented: 30 },
    { month: "Feb", detected: 28, prevented: 27 },
  ]);
  const [alertTypes, setAlertTypes] = useState<any[]>([
    { name: "Duplicate Claims", count: 12, color: "#EF4444" },
    { name: "New Policy Claims", count: 8, color: "#F59E0B" },
    { name: "High Value", count: 15, color: "#8B5CF6" },
    { name: "IP Anomalies", count: 5, color: "#3B82F6" },
  ]);
  const [recentAlerts, setRecentAlerts] = useState<any[]>([]);

  const calculateFraudTrends = (claimsData: any[]) => {
    const monthNames = [
      "Jan",
      "Feb",
      "Mar",
      "Apr",
      "May",
      "Jun",
      "Jul",
      "Aug",
      "Sep",
      "Oct",
      "Nov",
      "Dec",
    ];
    const currentMonth = new Date().getMonth();

    const trends = [];
    const currentDate = new Date();
    const currentYear = currentDate.getFullYear();

    for (let i = -5; i <= 0; i++) {
      const targetDate = new Date(currentYear, currentMonth + i, 1);
      const monthIndex = targetDate.getMonth();
      const yearIndex = targetDate.getFullYear();
      const monthName = monthNames[monthIndex];

      const monthClaims = claimsData.filter((c) => {
        if (!c.date && !c.submissionDate) return false;
        const claimDate = new Date(c.date || c.submissionDate);
        return (
          claimDate.getMonth() === monthIndex &&
          claimDate.getFullYear() === yearIndex
        );
      });

      const detected = monthClaims.filter(
        (c) => (Number(c.riskScore) || 0) >= 70,
      ).length;
      const prevented = monthClaims.filter(
        (c) => c.status === "Rejected",
      ).length;

      trends.push({
        month: monthName,
        detected: detected,
        prevented: prevented,
      });
    }

    // Always use calculated trends when we have claims data
    setFraudTrends(trends);
  };

  const calculateAlertTypes = (claimsData: any[]) => {
    // Categorize claims by risk patterns
    const highRiskClaims = claimsData.filter(
      (c) => (Number(c.riskScore) || 0) >= 70,
    );

    // Count different fraud indicators
    const duplicateClaims = claimsData.filter(
      (c) =>
        claimsData.filter(
          (other) => other.claimantName === c.claimantName && other.id !== c.id,
        ).length > 0,
    ).length;

    const recentPolicyClaims = claimsData.filter((c) => {
      // Claims filed within 7 days of policy
      if (c.policyCreatedDate) {
        const policyDate = new Date(c.policyCreatedDate);
        const claimDate = new Date(c.date || c.submissionDate);
        const daysDiff =
          (claimDate.getTime() - policyDate.getTime()) / (1000 * 60 * 60 * 24);
        return daysDiff <= 7;
      }
      return false;
    }).length;

    const highAmountClaims = claimsData.filter(
      (c) => (Number(c.amount) || 0) > 50000,
    ).length;
    const suspiciousIpClaims = claimsData.filter(
      (c) => c.ipAddress && c.ipAddress.includes("127"),
    ).length;

    // Always show calculated data even if counts are 0
    const calculatedAlerts = [
      {
        name: "Duplicate Claims",
        count: duplicateClaims,
        color: "#EF4444",
      },
      {
        name: "New Policy Claims",
        count: recentPolicyClaims,
        color: "#F59E0B",
      },
      {
        name: "High Value",
        count: highAmountClaims,
        color: "#8B5CF6",
      },
      {
        name: "IP Anomalies",
        count: suspiciousIpClaims,
        color: "#3B82F6",
      },
    ];
    setAlertTypes(calculatedAlerts);
  };

  const generateRecentAlerts = (claimsData: any[]) => {
    // Get high-risk claims (70+) and convert to alerts
    const highRiskClaims = claimsData
      .filter((c) => (Number(c.riskScore) || 0) >= 70)
      .sort((a, b) => {
        const dateA = new Date(a.date || a.submissionDate);
        const dateB = new Date(b.date || b.submissionDate);
        return dateB.getTime() - dateA.getTime();
      })
      .slice(0, 10); // Top 10 most recent high-risk

    const alerts = highRiskClaims.map((claim, idx) => {
      const riskScore = Number(claim.riskScore) || 0;

      // Determine severity based on risk score
      const severity =
        riskScore >= 80 ? "High" : riskScore >= 60 ? "Medium" : "Low";

      // Determine alert type based on claim characteristics
      let type = "High Risk Claim";
      let description = `Claim flagged with risk score of ${riskScore}/100.`;

      // Check for specific patterns
      if (claim.policyCreatedDate) {
        const policyDate = new Date(claim.policyCreatedDate);
        const claimDate = new Date(claim.date || claim.submissionDate);
        const daysDiff =
          (claimDate.getTime() - policyDate.getTime()) / (1000 * 60 * 60 * 24);

        if (daysDiff <= 7) {
          type = "New Policy Risk";
          description = `Claim filed ${Math.floor(daysDiff)} days after policy creation. Risk score: ${riskScore}/100.`;
        }
      }

      if ((Number(claim.amount) || 0) > 50000) {
        type = "High Value Alert";
        description = `High value claim ($${Number(claim.amount).toLocaleString()}) with risk score ${riskScore}/100.`;
      }

      // Check for duplicates
      const duplicates = claimsData.filter(
        (c) => c.claimantName === claim.claimantName && c.id !== claim.id,
      );
      if (duplicates.length > 0) {
        type = "Duplicate Detection";
        description = `Multiple claims detected from ${claim.claimantName}. Risk score: ${riskScore}/100.`;
      }

      return {
        id: `ALT-${String(idx + 1).padStart(3, "0")}`,
        severity: severity,
        type: type,
        description: description,
        relatedClaims: [claim.id],
        date: new Date(claim.date || claim.submissionDate)
          .toISOString()
          .split("T")[0],
      };
    });

    setRecentAlerts(alerts.length > 0 ? alerts : MOCK_ALERTS);
  };

  useEffect(() => {
    const loadClaims = async () => {
      try {
        const data = await fetchClaims();
        setClaims(data || []);

        if (data && data.length > 0) {
          // Calculate fraud trends from real data
          calculateFraudTrends(data);
          // Calculate alert types from real data
          calculateAlertTypes(data);
          // Generate real alerts from high-risk claims
          generateRecentAlerts(data);
        }
      } catch (err) {
        // Failed to load claims for fraud detection
        setClaims([]);
      }
    };
    loadClaims();
  }, []);

  // Compute live stats from claims
  // Count critical risk claims (70+) as flagged if no explicit flagged status
  const flaggedCount = claims.filter(
    (c) => c.status === "Flagged" || (Number(c.riskScore) || 0) >= 70,
  ).length;

  const rejectedTotal = claims
    .filter((c) => c.status === "Rejected")
    .reduce((acc, c) => acc + (Number(c.amount) || 0), 0);
  const avgRiskScore =
    claims.length > 0
      ? Math.round(
          claims.reduce((acc, c) => acc + (Number(c.riskScore) || 0), 0) /
            claims.length,
        )
      : 0;
  const highRiskCount = claims.filter(
    (c) => (Number(c.riskScore) || 0) >= 50,
  ).length;

  const runAnalysis = async () => {
    setAnalyzing(true);
    // Use live claims data from backend for AI analysis
    const result = await detectFraudPatterns(claims.length > 0 ? claims : []);
    setAiAnalysis(result);
    setAnalyzing(false);
  };

  return (
    <div className="p-8 h-full flex flex-col gap-8 overflow-y-auto custom-scrollbar bg-transparent">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 shrink-0">
        <div>
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2 tracking-tight">
            Fraud Monitor
          </h1>
          <p className="text-gray-500 font-medium">
            Real-time threat detection and anomaly analytics.
          </p>
        </div>
        <Button
          onClick={runAnalysis}
          className="bg-gradient-to-r from-rose-600 to-orange-600 hover:from-rose-500 hover:to-orange-500 border-0 shadow-lg shadow-rose-500/20 px-8 h-12 rounded-2xl"
        >
          <Zap size={18} className={cn(analyzing && "animate-pulse")} />
          {analyzing ? "Scanning Protocols..." : "Run AI Threat Scan"}
        </Button>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 shrink-0">
        <StatCard
          title="High Risk Claims"
          value={highRiskCount.toString()}
          change={claims.length > 0 ? `of ${claims.length} total` : undefined}
          icon={ShieldAlert}
          colorClass="bg-rose-100 text-rose-600 dark:bg-rose-900/20 dark:text-rose-400"
        />
        <StatCard
          title="Fraud Prevented"
          value={rejectedTotal.toLocaleString("en-US", {
            style: "currency",
            currency: "USD",
            maximumFractionDigits: 0,
          })}
          change={
            claims.filter((c) => c.status === "Rejected").length > 0
              ? `${claims.filter((c) => c.status === "Rejected").length} rejected`
              : undefined
          }
          icon={CheckCircle}
          colorClass="bg-emerald-100 text-emerald-600 dark:bg-emerald-900/20 dark:text-emerald-400"
        />
        <StatCard
          title="Risk Score Avg"
          value={`${avgRiskScore}/100`}
          icon={Activity}
          colorClass="bg-blue-100 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400"
        />
        <StatCard
          title="Flagged Claims"
          value={flaggedCount.toString()}
          icon={AlertTriangle}
          colorClass="bg-amber-100 text-amber-600 dark:bg-amber-900/20 dark:text-amber-400"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 min-h-[400px]">
        {/* Trends Chart */}
        <Card className="flex flex-col p-6 bg-white/80 dark:bg-[#1C1C1E]/80 backdrop-blur-2xl border border-gray-100 dark:border-white/10 shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                Threat Mitigation Trends
              </h3>
              <p className="text-xs text-gray-500">
                Detected vs Prevented incidents over 6 months
              </p>
            </div>
            <Badge variant="success">98.5% Efficacy</Badge>
          </div>
          <div className="w-full h-[350px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={fraudTrends}
                margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
              >
                <defs>
                  <linearGradient
                    id="colorDetected"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop offset="5%" stopColor="#F43F5E" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#F43F5E" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient
                    id="colorPrevented"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                  stroke="#E5E7EB"
                  opacity={0.3}
                />
                <XAxis
                  dataKey="month"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: "#9CA3AF", fontSize: 10, fontWeight: 700 }}
                  dy={10}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: "#9CA3AF", fontSize: 10, fontWeight: 700 }}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: "12px",
                    border: "none",
                    boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
                    backgroundColor: "#1F2937",
                    color: "#fff",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="detected"
                  stroke="#F43F5E"
                  strokeWidth={3}
                  fillOpacity={1}
                  fill="url(#colorDetected)"
                  name="Threats Detected"
                />
                <Area
                  type="monotone"
                  dataKey="prevented"
                  stroke="#10B981"
                  strokeWidth={3}
                  fillOpacity={1}
                  fill="url(#colorPrevented)"
                  name="Fraud Prevented"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Alert Types */}
        <Card className="flex flex-col p-6 bg-white/80 dark:bg-[#1C1C1E]/80 backdrop-blur-2xl border border-gray-100 dark:border-white/10 shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                Alert Categories
              </h3>
              <p className="text-xs text-gray-500">
                Distribution of flagged anomalies
              </p>
            </div>
          </div>
          <div className="w-full h-[350px]">
            <ResponsiveContainer width="100%" height="100%">
              {/* Adjusted margins: increased top/bottom to compress chart area and reduce gap, added bottom margin for edge spacing */}
              <BarChart
                data={alertTypes}
                layout="vertical"
                margin={{ left: 0, right: 30, top: 20, bottom: 40 }}
              >
                <XAxis type="number" hide />
                <YAxis
                  dataKey="name"
                  type="category"
                  width={100}
                  tick={{ fill: "#6B7280", fontSize: 11, fontWeight: 600 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  cursor={{ fill: "transparent" }}
                  contentStyle={{
                    borderRadius: "12px",
                    border: "none",
                    backgroundColor: "#1F2937",
                    color: "#fff",
                  }}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]} barSize={36}>
                  {alertTypes.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Bottom Section: Alerts & AI */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recent Alerts List */}
        <div className="lg:col-span-2">
          <Card className="p-0 overflow-hidden bg-white/80 dark:bg-[#1C1C1E]/80 backdrop-blur-2xl border border-gray-100 dark:border-white/10 shadow-sm">
            <div className="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                Recent Alerts
              </h3>
              <Button variant="ghost" size="sm">
                View All
              </Button>
            </div>
            <div className="divide-y divide-gray-100 dark:divide-white/5">
              {recentAlerts.map((alert) => (
                <div
                  key={alert.id}
                  className="p-4 flex items-start gap-4 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer group"
                >
                  <div
                    className={cn(
                      "w-10 h-10 rounded-xl flex items-center justify-center shrink-0",
                      alert.severity === "High"
                        ? "bg-rose-100 text-rose-600 dark:bg-rose-900/20 dark:text-rose-400"
                        : alert.severity === "Medium"
                          ? "bg-amber-100 text-amber-600 dark:bg-amber-900/20 dark:text-amber-400"
                          : "bg-blue-100 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400",
                    )}
                  >
                    <AlertTriangle size={20} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-start mb-1">
                      <h4 className="text-sm font-bold text-gray-900 dark:text-white truncate">
                        {alert.type}
                      </h4>
                      <span className="text-[10px] text-gray-400 font-mono">
                        {alert.date}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 line-clamp-2">
                      {alert.description}
                    </p>
                    <div className="flex gap-2 mt-2">
                      {alert.relatedClaims.map((id) => (
                        <span
                          key={id}
                          className="text-[10px] px-1.5 py-0.5 bg-gray-100 dark:bg-white/10 rounded text-gray-500 font-mono"
                        >
                          {id}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="self-center opacity-0 group-hover:opacity-100 transition-opacity">
                    <Button
                      variant="secondary"
                      size="sm"
                      className="h-8 w-8 p-0 rounded-full"
                    >
                      <Share2 size={14} />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* AI Insight Panel */}
        <div className="flex flex-col gap-6">
          <Card className="flex-1 p-6 bg-gradient-to-br from-indigo-900 to-slate-900 text-white border-0 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-10">
              <Zap size={120} />
            </div>
            <div className="relative z-10 h-full flex flex-col">
              <div className="flex items-center gap-2 mb-4">
                <div className="p-2 bg-white/10 rounded-lg backdrop-blur-md">
                  <Zap size={20} className="text-yellow-400" />
                </div>
                <h3 className="text-lg font-bold">AI Threat Analysis</h3>
              </div>

              <div className="flex-1 bg-white/10 rounded-2xl p-4 backdrop-blur-md border border-white/10 text-sm leading-relaxed text-indigo-100 overflow-y-auto custom-scrollbar max-h-[250px] mb-4 whitespace-pre-wrap">
                {analyzing ? (
                  <div className="flex flex-col items-center justify-center h-full gap-3 opacity-70">
                    <div className="w-8 h-8 border-4 border-white/30 border-t-white rounded-full animate-spin" />
                    <span className="text-xs font-bold uppercase tracking-widest">
                      Processing Data...
                    </span>
                  </div>
                ) : (
                  aiAnalysis ||
                  "Run a scan to generate a detailed threat assessment report based on current claim vectors."
                )}
              </div>

              <Button
                onClick={runAnalysis}
                className="w-full bg-white text-indigo-900 hover:bg-indigo-50 border-0 font-bold shadow-lg"
              >
                {analyzing ? "Scanning..." : "Refresh Analysis"}
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
