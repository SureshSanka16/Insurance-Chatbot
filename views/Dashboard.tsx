import React, { useState, useEffect } from "react";
import {
  Card,
  Skeleton,
  Button,
  Badge,
  Modal,
} from "../components/UIComponents";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import {
  ArrowUpRight,
  ArrowDownRight,
  ShieldAlert,
  Activity,
  Zap,
  Sparkles,
  Download,
  Share2,
  FileText,
  ChevronRight,
} from "lucide-react";
import { cn } from "../components/UIComponents";
import { motion } from "framer-motion";
import { generateStrategicReport } from "../services/geminiService";

const StatCard = ({
  title,
  value,
  change,
  icon: Icon,
  trend,
  isLoading,
}: any) => {
  const isPositive = trend === "up";

  if (isLoading) {
    return (
      <div className="h-[160px] bg-white/40 dark:bg-white/5 backdrop-blur-xl border border-white/40 dark:border-white/10 rounded-[24px] p-6 shadow-2xl">
        <Skeleton className="w-10 h-10 rounded-lg mb-4" />
        <Skeleton className="w-24 h-8 mb-2" />
        <Skeleton className="w-16 h-4" />
      </div>
    );
  }

  return (
    <motion.div
      whileHover={{ y: -4, scale: 1.02 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
      className="group relative h-[160px] bg-white/60 dark:bg-[#1C1C1E]/40 backdrop-blur-2xl border border-white/60 dark:border-white/10 rounded-[24px] p-6 shadow-[0_20px_50px_rgba(0,0,0,0.04)] dark:shadow-none flex flex-col justify-between hover:shadow-[0_0_30px_rgba(249,115,22,0.4)] hover:border-orange-500/30 transition-all duration-300"
    >
      <div className="flex justify-between items-start">
        <div className="p-2.5 rounded-xl bg-orange-500/10 text-orange-600 dark:text-orange-400 group-hover:scale-110 transition-transform duration-300">
          <Icon size={20} strokeWidth={2.5} />
        </div>
        <div
          className={cn(
            "flex items-center gap-1 px-2 py-1 rounded-full text-[10px] font-black tracking-tighter uppercase transition-colors duration-300",
            isPositive
              ? "bg-emerald-500/10 text-emerald-600 border border-emerald-500/20"
              : "bg-rose-500/10 text-rose-600 border border-rose-500/20",
          )}
        >
          {isPositive ? (
            <ArrowUpRight size={10} />
          ) : (
            <ArrowDownRight size={10} />
          )}
          {change}
        </div>
      </div>

      <div>
        <h3 className="text-3xl font-black text-gray-900 dark:text-white tracking-tighter leading-none mb-1.5">
          {value}
        </h3>
        <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">
          {title}
        </p>
      </div>
    </motion.div>
  );
};

const CustomTooltip = ({ active, payload, label, chartMode }: any) => {
  if (active && payload && payload.length) {
    const value = payload[0].value;
    const isVolume = chartMode === "volume";
    return (
      <div className="bg-gray-900/95 dark:bg-black/90 backdrop-blur-md border border-white/10 p-4 rounded-2xl shadow-2xl min-w-[180px]">
        <p className="text-[10px] font-black text-orange-500 uppercase tracking-widest mb-2">
          {label} 2026
        </p>
        <div className="flex flex-col gap-2">
          <div>
            <p className="text-xs text-gray-400 font-medium mb-0.5">
              {isVolume ? "Claims Processed" : "Total Claim Value"}
            </p>
            <p className="text-2xl font-black text-white">
              {isVolume
                ? value.toLocaleString()
                : `$${value.toLocaleString()}K`}
            </p>
          </div>
          <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden mt-1">
            <div
              className="h-full bg-gradient-to-r from-orange-500 to-orange-400 rounded-full"
              style={{
                width: `${Math.min((value / (isVolume ? 350 : 10000)) * 100, 100)}%`,
              }}
            />
          </div>
        </div>
      </div>
    );
  }
  return null;
};

export const Dashboard = ({
  onNavigate,
}: {
  onNavigate: (tab: string) => void;
}) => {
  const [chartMode, setChartMode] = useState<"volume" | "value">("volume");
  const [isLoading, setIsLoading] = useState(true);
  const [isReportOpen, setIsReportOpen] = useState(false);
  const [reportText, setReportText] = useState("");
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [claims, setClaims] = useState<any[]>([]); // Use any[] or Claim[] depending on available types

  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoadError(null);
        const data = await import("../src/api/endpoints").then((mod) =>
          mod.fetchClaims(),
        );
        setClaims(data || []);
      } catch (err: any) {
        // Failed to load claims for dashboard
        setLoadError(
          err?.response?.data?.detail ||
            "Failed to connect to backend. Is the server running on port 8000?",
        );
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleOpenReport = async () => {
    setIsReportOpen(true);
    setIsGeneratingReport(true);
    try {
      // Validate we have claims data
      if (claims.length === 0) {
        setReportText(
          "## No Data Available\n\nInsufficient claims data to generate strategic report. Please ensure claims are loaded and try again.",
        );
        setIsGeneratingReport(false);
        return;
      }

      // Calculate real-time statistics from actual claims data
      const actualClaimsCount = claims.length;

      // Calculate fraud prevented: sum of rejected claims
      const fraudPreventedAmount = claims
        .filter((c) => c.status === "Rejected")
        .reduce((acc, curr) => acc + (Number(curr.amount) || 0), 0);
      const fraudValue = `$${(fraudPreventedAmount / 1000000).toFixed(1)}M`;

      // Calculate actual risk distribution based on risk scores
      const riskCounts = {
        low: claims.filter((c) => c.riskScore < 30).length,
        medium: claims.filter((c) => c.riskScore >= 30 && c.riskScore < 50)
          .length,
        high: claims.filter((c) => c.riskScore >= 50 && c.riskScore < 70)
          .length,
        critical: claims.filter((c) => c.riskScore >= 70).length,
      };

      const actualRiskDist = [
        { name: "Low Risk", value: riskCounts.low, fill: "#34A853" },
        { name: "Medium Risk", value: riskCounts.medium, fill: "#FBBC04" },
        { name: "High Risk", value: riskCounts.high, fill: "#EA4335" },
        { name: "Critical", value: riskCounts.critical, fill: "#000000" },
      ];

      const report = await generateStrategicReport({
        claimsCount: actualClaimsCount,
        fraudValue: fraudValue,
        riskDist: actualRiskDist,
      });
      setReportText(report);
    } finally {
      setIsGeneratingReport(false);
    }
  };

  // Calculate real chart data from actual claims
  const calculateMonthlyData = () => {
    if (!claims || claims.length === 0) {
      // Return fallback data if no claims
      return [
        { name: "Jan", value: 245, risk: 2400 },
        { name: "Feb", value: 198, risk: 1398 },
        { name: "Mar", value: 287, risk: 9800 },
        { name: "Apr", value: 312, risk: 3908 },
        { name: "May", value: 276, risk: 4800 },
        { name: "Jun", value: 294, risk: 3800 },
        { name: "Jul", value: 318, risk: 4300 },
        { name: "Aug", value: 302, risk: 4100 },
        { name: "Sep", value: 265, risk: 3600 },
        { name: "Oct", value: 289, risk: 4200 },
        { name: "Nov", value: 256, risk: 3400 },
        { name: "Dec", value: 223, risk: 2800 },
      ];
    }

    // Group claims by month
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
    const monthlyStats: {
      [key: string]: { count: number; totalAmount: number; totalRisk: number };
    } = {};

    // Initialize all months
    monthNames.forEach((month) => {
      monthlyStats[month] = { count: 0, totalAmount: 0, totalRisk: 0 };
    });

    // Process each claim
    claims.forEach((claim) => {
      try {
        const claimDate = new Date(claim.date);
        if (!isNaN(claimDate.getTime())) {
          const monthName = monthNames[claimDate.getMonth()];
          monthlyStats[monthName].count += 1;
          monthlyStats[monthName].totalAmount += Number(claim.amount) || 0;
          monthlyStats[monthName].totalRisk += Number(claim.riskScore) || 0;
        }
      } catch (e) {
        // Skip invalid dates
      }
    });

    // Convert to chart data format
    return monthNames.map((month) => ({
      name: month,
      value: monthlyStats[month].count,
      risk: Math.round(monthlyStats[month].totalAmount / 1000), // Convert to thousands
    }));
  };

  const chartData = calculateMonthlyData().map((d) => ({
    name: d.name,
    primary: chartMode === "volume" ? d.value : d.risk, // Volume: claims count, Value: total claim amount in $K
  }));

  console.log("Real-time chartData:", chartData);

  const HIGH_CONTRAST_COLORS = ["#34A853", "#FBBC04", "#EA4335", "#64748B"];

  return (
    <div className="p-8 space-y-8 max-w-[1600px] mx-auto h-full flex flex-col overflow-y-auto custom-scrollbar">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 shrink-0">
        <div>
          <h1 className="text-5xl font-black text-gray-900 dark:text-white tracking-tighter mb-2">
            Operations Center
          </h1>
          <p className="text-lg text-gray-500 font-medium max-w-xl">
            Intelligent hub for real-time risk assessment and operational
            throughput monitoring.
          </p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="secondary"
            onClick={handleOpenReport}
            className="h-12 px-6 border-gray-200 dark:border-white/10 shadow-sm gap-2 rounded-xl"
          >
            <Sparkles size={18} className="text-orange-500" />
            <span className="font-bold">AI Strategy</span>
          </Button>
          <div className="h-12 flex items-center gap-3 px-5 py-2 bg-emerald-500/10 rounded-xl border border-emerald-500/20">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
            </span>
            <span className="text-[10px] font-black text-emerald-600 dark:text-emerald-400 uppercase tracking-[0.15em]">
              Live Network
            </span>
          </div>
        </div>
      </div>

      {/* Metrics Row - Strict 4 Column Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-[24px] shrink-0">
        <StatCard
          title="Total Claims"
          value={claims.length.toLocaleString()}
          change="12.5% UP"
          icon={Activity}
          trend="up"
          isLoading={isLoading}
        />
        <StatCard
          title="Fraud Prevented"
          value={claims
            .filter((c) => c.status === "Rejected")
            .reduce((acc, curr) => acc + (Number(curr.amount) || 0), 0)
            .toLocaleString("en-US", {
              style: "currency",
              currency: "USD",
              maximumFractionDigits: 0,
            })}
          change="8.2% UP"
          icon={ShieldAlert}
          trend="up"
          isLoading={isLoading}
        />
        <StatCard
          title="Processing Time"
          value="2.4d"
          change="1.2% DOWN"
          icon={Zap}
          trend="down"
          isLoading={isLoading}
        />
        <StatCard
          title="Auto-Approval"
          value="28.4%"
          change="0.5% UP"
          icon={Sparkles}
          trend="up"
          isLoading={isLoading}
        />
      </div>

      {/* Error Banner */}
      {loadError && !isLoading && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-900/40 rounded-2xl p-6 text-center">
          <p className="text-red-600 dark:text-red-400 font-bold mb-1">
            Unable to load live data
          </p>
          <p className="text-red-400 dark:text-red-500 text-sm">{loadError}</p>
        </div>
      )}

      {/* Main Charts & Queue Grid */}
      <div className="flex-1 min-h-[500px]">
        {/* Claims Volume Area Chart */}
        <div className="flex flex-col h-full">
          <Card className="flex-1 flex flex-col p-8 bg-white/60 dark:bg-[#1C1C1E]/40 backdrop-blur-2xl border border-white/60 dark:border-white/10 shadow-[0_20px_50px_rgba(0,0,0,0.04)]">
            <div className="flex justify-between items-center mb-16">
              <div>
                <h3 className="text-xl font-black text-gray-900 dark:text-white tracking-tight">
                  System Throughput
                </h3>
                <p className="text-xs text-gray-500 font-medium mt-1 uppercase tracking-widest">
                  Active Claims Cycle Volume
                </p>
              </div>
              <div className="flex bg-gray-100 dark:bg-black/20 p-1 rounded-xl border border-gray-200 dark:border-white/10">
                {[
                  { key: "volume", label: "Claims Count" },
                  { key: "value", label: "Amount ($K)" },
                ].map((mode) => (
                  <button
                    key={mode.key}
                    onClick={() => setChartMode(mode.key as any)}
                    className={cn(
                      "px-4 py-1.5 text-[10px] font-black uppercase tracking-widest rounded-lg transition-all",
                      chartMode === mode.key
                        ? "bg-white dark:bg-gray-800 shadow-md text-gray-900 dark:text-white"
                        : "text-gray-400 hover:text-gray-600 dark:hover:text-gray-300",
                    )}
                  >
                    {mode.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="w-full h-[400px] pb-2">
              {!chartData || chartData.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <Activity className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-400 dark:text-gray-500 font-medium">
                      No data available
                    </p>
                    <p className="text-xs text-gray-400 dark:text-gray-600 mt-2">
                      Chart data: {chartData?.length || 0} items
                    </p>
                  </div>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart
                    data={chartData}
                    margin={{ top: 10, right: 0, left: 0, bottom: 5 }}
                  >
                    <defs>
                      <linearGradient
                        id="colorPrimary"
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="5%"
                          stopColor="#F97316"
                          stopOpacity={0.3}
                        />
                        <stop
                          offset="95%"
                          stopColor="#F97316"
                          stopOpacity={0}
                        />
                      </linearGradient>
                    </defs>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      vertical={false}
                      stroke="#E2E8F0"
                      opacity={0.3}
                    />
                    <XAxis
                      dataKey="name"
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: "#94A3B8", fontSize: 10, fontWeight: 800 }}
                      dy={10}
                    />
                    <YAxis
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: "#94A3B8", fontSize: 10, fontWeight: 800 }}
                      tickFormatter={(value) =>
                        chartMode === "volume" ? `${value}` : `$${value}K`
                      }
                    />
                    <Tooltip
                      content={<CustomTooltip chartMode={chartMode} />}
                      cursor={{
                        stroke: "#F97316",
                        strokeWidth: 2,
                        strokeDasharray: "5 5",
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="primary"
                      stroke="#F97316"
                      strokeWidth={4}
                      fillOpacity={1}
                      fill="url(#colorPrimary)"
                      animationDuration={1500}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>
          </Card>
        </div>
      </div>

      {/* Strategic Report Modal - Preservation of functional logic with improved styling */}
      <Modal
        isOpen={isReportOpen}
        onClose={() => setIsReportOpen(false)}
        title="Executive Strategic Intelligence"
        size="lg"
      >
        <div className="flex flex-col gap-6 h-full min-h-[500px]">
          {isGeneratingReport ? (
            <div className="flex flex-col items-center justify-center flex-1 space-y-6 py-20">
              <div className="relative">
                <div className="w-20 h-20 rounded-full border-4 border-orange-100 dark:border-orange-900/30 animate-pulse" />
                <Sparkles
                  size={32}
                  className="absolute inset-0 m-auto text-orange-500 animate-bounce"
                />
              </div>
              <div className="text-center">
                <h4 className="text-xl font-black text-gray-900 dark:text-white mb-2">
                  Synthesizing Network Signals
                </h4>
                <p className="text-sm text-gray-500 font-medium">
                  Calibrating operational models for Q4 projections...
                </p>
              </div>
              <div className="w-full max-w-xs space-y-2">
                <Skeleton className="h-1.5 w-full rounded-full" />
                <Skeleton className="h-1.5 w-3/4 mx-auto rounded-full" />
                <Skeleton className="h-1.5 w-1/2 mx-auto rounded-full" />
              </div>
            </div>
          ) : (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex-1 space-y-8"
            >
              <div className="flex justify-between items-start border-b border-gray-100 dark:border-white/5 pb-6">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-orange-600 rounded-2xl text-white shadow-xl shadow-orange-500/20">
                    <FileText size={24} />
                  </div>
                  <div>
                    <h3 className="text-xl font-black text-gray-900 dark:text-white uppercase tracking-tight">
                      Operational Audit
                    </h3>
                    <p className="text-[10px] text-gray-400 font-mono font-black uppercase tracking-widest">
                      ID: V-STRAT-8812
                    </p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    className="h-10 px-4 rounded-xl border-gray-200 dark:border-white/10"
                  >
                    <Share2 size={14} />
                  </Button>
                  <Button
                    size="sm"
                    className="h-10 px-4 rounded-xl bg-orange-600 hover:bg-orange-500 text-white border-0 shadow-lg"
                  >
                    <Download size={14} className="mr-2" /> Export
                  </Button>
                </div>
              </div>

              <div className="bg-gray-50/50 dark:bg-white/5 p-8 rounded-[32px] border border-gray-100 dark:border-white/10 shadow-inner max-h-[400px] overflow-y-auto custom-scrollbar">
                <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap font-sans text-sm leading-relaxed text-gray-700 dark:text-gray-300">
                  {reportText}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-5 rounded-2xl bg-emerald-500/5 border border-emerald-500/20">
                  <p className="text-[10px] font-black text-emerald-600 uppercase tracking-widest mb-1.5">
                    Current Throughput
                  </p>
                  <p className="text-xs font-bold text-gray-800 dark:text-emerald-100">
                    {claims.length > 0 ? (
                      <>
                        Processing {claims.length} active claims with{" "}
                        {claims.filter((c) => c.status === "Approved").length}{" "}
                        approved (
                        {(
                          (claims.filter((c) => c.status === "Approved")
                            .length /
                            claims.length) *
                          100
                        ).toFixed(1)}
                        % approval rate)
                      </>
                    ) : (
                      "No claims data available"
                    )}
                  </p>
                </div>
                <div className="p-5 rounded-2xl bg-blue-500/5 border border-blue-500/20">
                  <p className="text-[10px] font-black text-blue-600 uppercase tracking-widest mb-1.5">
                    Fraud Detection Impact
                  </p>
                  <p className="text-xs font-bold text-gray-800 dark:text-blue-100">
                    {claims.length > 0 ? (
                      <>
                        {claims.filter((c) => c.riskScore >= 70).length}{" "}
                        critical risk cases identified, preventing{" "}
                        {claims.filter((c) => c.status === "Rejected").length}{" "}
                        fraudulent claims
                      </>
                    ) : (
                      "No fraud data available"
                    )}
                  </p>
                </div>
              </div>

              <Button
                variant="secondary"
                className="w-full h-12 rounded-2xl border-gray-200 dark:border-white/10 font-bold"
                onClick={() => setIsReportOpen(false)}
              >
                Close Report
              </Button>
            </motion.div>
          )}
        </div>
      </Modal>
    </div>
  );
};
