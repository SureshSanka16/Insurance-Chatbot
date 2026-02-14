import React, { useState } from 'react';
import { Card, Button, cn, Skeleton, Modal, Badge, Toast } from '../components/UIComponents';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Legend, Cell, LabelList } from 'recharts';
import { TrendingUp, Clock, CheckCircle, AlertTriangle, Zap, FileText, Share2, Download, Sparkles, Target, ArrowRight, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { generateStrategicReport } from '../services/geminiService';
import { ThreeScene } from '../components/ThreeScene';

const FORECAST_DATA = [
  { month: 'Jul', actual: 4000, forecast: 4200 },
  { month: 'Aug', actual: 3000, forecast: 3500 },
  { month: 'Sep', actual: 2000, forecast: 2900 },
  { month: 'Oct', actual: 2780, forecast: 3100 },
  { month: 'Nov', actual: 1890, forecast: 2600 },
  { month: 'Dec', actual: 2390, forecast: 2800 },
  { month: 'Jan', actual: null, forecast: 4100 },
  { month: 'Feb', actual: null, forecast: 4500 },
  { month: 'Mar', actual: null, forecast: 4800 },
];

const PROCESSING_TIME_DATA = [
  { name: 'Vehicle', time: 4.2, color: '#F97316' },
  { name: 'Life', time: 5.8, color: '#8B5CF6' },
  { name: 'Health', time: 2.1, color: '#10B981' },
  { name: 'Property', time: 6.5, color: '#F43F5E' },
];

const MetricCard = ({ title, value, subtext, icon: Icon, colorClass, trendClass }: any) => (
  <Card className="h-[160px] p-6 flex flex-col justify-between shadow-lg border border-gray-200 dark:border-white/10 bg-white/70 dark:bg-[#1C1C1E]/40 backdrop-blur-2xl transition-all duration-300 hover:scale-[1.02]">
    <div className="flex justify-between items-start">
      <div className={cn("p-2.5 rounded-xl shadow-sm", colorClass)}>
        <Icon size={20} />
      </div>
      <div className={cn("text-[10px] font-black flex items-center gap-1 uppercase tracking-wider", trendClass)}>
        {subtext}
      </div>
    </div>
    <div>
      <span className="font-black text-[10px] uppercase tracking-[0.2em] text-gray-400 block mb-1">{title}</span>
      <div className="text-3xl font-black text-slate-900 dark:text-white tracking-tighter leading-none">{value}</div>
    </div>
  </Card>
);

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900/95 dark:bg-black/90 backdrop-blur-md border border-white/10 p-4 rounded-2xl shadow-2xl">
        <p className="text-[10px] font-black text-orange-500 uppercase tracking-widest mb-2">{label} Report</p>
        <div className="space-y-2">
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center justify-between gap-8">
              <span className="text-[10px] text-gray-400 font-bold uppercase">{entry.name}:</span>
              <span className="text-sm font-black text-white">{entry.value ? entry.value.toLocaleString() : 'N/A'}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }
  return null;
};

export const Analytics = () => {
  const [isReportOpen, setIsReportOpen] = useState(false);
  const [reportText, setReportText] = useState('');
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const handleGenerateReport = async () => {
    setIsReportOpen(true);
    setIsGeneratingReport(true);
    try {
      const report = await generateStrategicReport({
        claimsCount: 1248,
        fraudValue: "$4.2M",
        riskDist: [
          { name: 'Low Risk', value: 400 },
          { name: 'Medium Risk', value: 300 },
          { name: 'High Risk', value: 300 },
          { name: 'Critical', value: 100 },
        ]
      });
      setReportText(report);
    } finally {
      setIsGeneratingReport(false);
    }
  };

  const handleExport = () => {
    setToast("Analytics report exported as PDF");
  };

  return (
    <div className="relative p-8 h-full flex flex-col gap-8 animate-in fade-in duration-700 max-w-full overflow-y-auto custom-scrollbar bg-transparent">
      {/* 3D Background effect for Analytics */}
      <div className="absolute inset-0 z-0 opacity-5 pointer-events-none">
          <ThreeScene />
      </div>

      <AnimatePresence>
        {toast && (
          <div className="fixed top-24 left-1/2 -translate-x-1/2 z-[100]">
            <Toast message={toast} onClose={() => setToast(null)} />
          </div>
        )}
      </AnimatePresence>

      <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-end gap-4 shrink-0 pl-1">
        <div className="space-y-1">
          <h1 className="text-5xl font-black text-slate-900 dark:text-white tracking-tighter">Predictive Analytics</h1>
          <p className="text-lg text-slate-500 font-medium">Enterprise-grade forecasting and operational throughput monitoring.</p>
        </div>
        <div className="flex gap-4">
          <Button variant="secondary" onClick={handleExport} className="h-12 px-6 border-gray-200 dark:border-white/10 rounded-xl gap-2 shadow-sm bg-white dark:bg-white/5">
            <Download size={16} /> 
            <span className="font-bold">Export PDF</span>
          </Button>
          <Button onClick={handleGenerateReport} className="h-12 px-6 shadow-xl bg-orange-600 hover:bg-orange-500 text-white border-0 rounded-xl gap-2 transition-transform active:scale-95">
            <Sparkles size={16} className="text-white fill-white" /> 
            <span className="font-bold uppercase tracking-widest text-xs">Generate Report</span>
          </Button>
        </div>
      </div>

      {/* Top Metrics Grid - Unified 24px Gap */}
      <div className="relative z-10 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 w-full shrink-0">
        <MetricCard 
          title="Avg Settlement" 
          value="4.2 Days" 
          subtext={<span><TrendingUp size={12} className="inline" /> -12%</span>}
          icon={Clock}
          colorClass="bg-orange-50 text-orange-600 dark:bg-orange-500/10 dark:text-orange-400"
          trendClass="text-emerald-600 dark:text-emerald-400"
        />
        <MetricCard 
          title="AI Accuracy" 
          value="94.8%" 
          subtext={<span><TrendingUp size={12} className="inline" /> +2.4%</span>}
          icon={Zap}
          colorClass="bg-purple-50 text-purple-600 dark:bg-purple-500/10 dark:text-purple-400"
          trendClass="text-emerald-600 dark:text-emerald-400"
        />
        <MetricCard 
          title="Auto-Approval" 
          value="28.4%" 
          subtext="Target: 30%"
          icon={CheckCircle}
          colorClass="bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400"
          trendClass="text-slate-400 dark:text-slate-500"
        />
        <MetricCard 
          title="Risk Exposure" 
          value="$12.4M" 
          subtext={<span><TrendingUp size={12} className="inline" /> +5%</span>}
          icon={AlertTriangle}
          colorClass="bg-rose-50 text-rose-600 dark:bg-rose-500/10 dark:text-rose-400"
          trendClass="text-rose-600 dark:text-rose-400"
        />
      </div>

      {/* Charts Layout - Flexible Grid */}
      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-[550px]">
        {/* Main Forecast Area Chart - Dominant Box */}
        <Card className="lg:col-span-8 flex flex-col p-8 bg-white/80 dark:bg-[#1C1C1E]/40 backdrop-blur-2xl shadow-lg border border-gray-200 dark:border-white/10">
          <div className="mb-8 flex justify-between items-start">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-slate-100 dark:bg-white/5 rounded-2xl text-orange-500">
                <Target size={24} />
              </div>
              <div>
                <h3 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight uppercase">Claims Volume Forecast</h3>
                <p className="text-[10px] text-slate-400 uppercase tracking-[0.2em] font-black mt-0.5">Predictive AI Projections • Fiscal Q4</p>
              </div>
            </div>
            <Badge variant="info" className="px-4 py-1.5 rounded-full font-black text-[9px] tracking-widest bg-blue-500/10 text-blue-600 border-blue-500/20">LIVE DATA</Badge>
          </div>
          
          <div className="flex-1 w-full min-h-[350px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={FORECAST_DATA} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#F97316" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#F97316" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" opacity={0.3} />
                <XAxis 
                  dataKey="month" 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fill: '#94A3B8', fontSize: 10, fontWeight: 900, textTransform: 'uppercase' }} 
                  dy={15} 
                />
                <YAxis 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fill: '#94A3B8', fontSize: 10, fontWeight: 900 }} 
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend 
                  iconType="circle" 
                  verticalAlign="top" 
                  align="right" 
                  wrapperStyle={{ paddingBottom: '30px', fontSize: '10px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.1em' }} 
                />
                <Area 
                  type="monotone" 
                  dataKey="actual" 
                  stroke="#F97316" 
                  strokeWidth={4} 
                  fill="url(#colorActual)" 
                  name="Recorded Volume" 
                  animationDuration={1500}
                />
                <Area 
                  type="monotone" 
                  dataKey="forecast" 
                  stroke="#8B5CF6" 
                  strokeWidth={3} 
                  strokeDasharray="6 6" 
                  fill="url(#colorForecast)" 
                  name="AI Baseline" 
                  animationDuration={2000}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Efficiency Audit - Compact and Appealing Side Box */}
        <Card className="lg:col-span-4 flex flex-col p-8 bg-white/80 dark:bg-[#1C1C1E]/40 backdrop-blur-2xl shadow-lg border border-gray-200 dark:border-white/10 overflow-hidden">
          <div className="mb-6">
            <h3 className="text-xl font-black text-slate-900 dark:text-white tracking-tight uppercase">Efficiency Audit</h3>
            <p className="text-[10px] text-slate-400 mt-1 uppercase tracking-[0.2em] font-black">Settlement Latency (Avg Days)</p>
          </div>

          <div className="w-full h-[220px] mb-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart 
                data={PROCESSING_TIME_DATA} 
                layout="vertical" 
                margin={{ left: -30, right: 30, top: 0, bottom: 0 }}
                barSize={24}
              >
                <XAxis type="number" hide domain={[0, 10]} />
                <YAxis 
                  dataKey="name" 
                  type="category" 
                  width={90} 
                  tick={{ fill: '#64748B', fontSize: 11, fontWeight: 800, textTransform: 'uppercase' }} 
                  axisLine={false} 
                  tickLine={false}
                />
                <Tooltip 
                  cursor={{ fill: 'transparent' }} 
                  contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 10px 30px rgba(0,0,0,0.1)', backgroundColor: '#0F172A' }} 
                  itemStyle={{ color: '#fff', fontSize: '11px', fontWeight: 'bold' }}
                  formatter={(value: number) => [`${value} Days`, 'Latency']}
                />
                <Bar 
                  dataKey="time" 
                  radius={[6, 6, 6, 6]} 
                  background={{ fill: 'rgba(148, 163, 184, 0.1)', radius: 6 }} 
                  animationDuration={1500}
                >
                  {PROCESSING_TIME_DATA.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                  <LabelList 
                    dataKey="time" 
                    position="right" 
                    fill="#94A3B8" 
                    fontSize={11} 
                    fontWeight={800} 
                    formatter={(val: any) => `${val}d`} 
                    offset={8}
                  />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Efficiency Visualization Placeholder */}
          <div className="mt-auto h-[120px] w-full rounded-2xl overflow-hidden relative group shadow-inner">
             <img 
                src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=800&q=80" 
                alt="Efficiency Visualization" 
                className="w-full h-full object-cover opacity-80 group-hover:scale-105 transition-transform duration-700 ease-out grayscale group-hover:grayscale-0"
             />
             <div className="absolute inset-0 bg-gradient-to-t from-slate-900/90 via-slate-900/40 to-transparent flex items-end p-4">
                 <div className="flex items-center gap-2 text-white/90">
                     <div className="p-1.5 bg-emerald-500/20 rounded-lg backdrop-blur-md">
                        <Activity size={14} className="text-emerald-400" />
                     </div>
                     <span className="text-[10px] font-black uppercase tracking-widest text-emerald-100">Workflow Optimized</span>
                 </div>
             </div>
          </div>
        </Card>
      </div>

      {/* Strategic Report Modal */}
      <Modal 
        isOpen={isReportOpen} 
        onClose={() => setIsReportOpen(false)} 
        title="Predictive Strategic Intelligence"
        size="lg"
      >
        <div className="flex flex-col gap-6 h-full min-h-[550px]">
          {isGeneratingReport ? (
            <div className="flex flex-col items-center justify-center flex-1 space-y-6 py-20">
              <div className="relative">
                <div className="w-24 h-24 rounded-full border-4 border-slate-100 dark:border-white/5 animate-pulse" />
                <Sparkles size={40} className="absolute inset-0 m-auto text-orange-500 animate-bounce" />
              </div>
              <div className="text-center">
                <h4 className="text-2xl font-black text-slate-900 dark:text-white mb-2 tracking-tighter">Analyzing Market Signals</h4>
                <p className="text-sm text-slate-500 font-bold uppercase tracking-widest">Compiling probabilistic data models...</p>
              </div>
              <div className="w-full max-w-xs space-y-3">
                <Skeleton className="h-1.5 w-full rounded-full" />
                <Skeleton className="h-1.5 w-3/4 mx-auto rounded-full" />
                <Skeleton className="h-1.5 w-1/2 mx-auto rounded-full" />
              </div>
            </div>
          ) : (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex-1 space-y-8 pb-4">
              <div className="flex justify-between items-start border-b border-gray-100 dark:border-white/5 pb-8">
                <div className="flex items-center gap-4">
                  <div className="p-4 bg-orange-600 rounded-2xl text-white shadow-xl shadow-orange-500/30">
                    <FileText size={28} />
                  </div>
                  <div>
                    <h3 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight uppercase leading-none">Strategic Audit</h3>
                    <p className="text-[10px] text-slate-400 font-mono font-black uppercase tracking-widest mt-2">REFERENCE: V-PRDX-8890</p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <Button variant="secondary" size="sm" className="h-10 px-4 rounded-xl border-gray-200 dark:border-white/10 bg-white dark:bg-white/5"><Share2 size={14} /></Button>
                  <Button size="sm" onClick={handleExport} className="h-10 px-5 rounded-xl bg-orange-600 hover:bg-orange-500 text-white border-0 shadow-lg font-black text-[10px] tracking-widest uppercase">Export PDF</Button>
                </div>
              </div>

              <div className="bg-slate-50 dark:bg-white/5 p-8 rounded-[32px] border border-gray-100 dark:border-white/10 shadow-inner max-h-[450px] overflow-y-auto custom-scrollbar">
                <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap font-sans text-sm leading-relaxed text-slate-700 dark:text-slate-300 font-medium">
                  {reportText}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-6 rounded-3xl bg-emerald-500/5 border border-emerald-500/10">
                  <p className="text-[10px] font-black text-emerald-600 dark:text-emerald-400 uppercase tracking-widest mb-2">Model Reliability</p>
                  <p className="text-xs font-bold text-slate-800 dark:text-slate-200">AI confidence levels remain high at 92.4% for predicted Q4 volume spikes.</p>
                </div>
                <div className="p-6 rounded-3xl bg-blue-500/5 border border-blue-500/10">
                  <p className="text-[10px] font-black text-blue-600 dark:text-blue-400 uppercase tracking-widest mb-2">Operational Node</p>
                  <p className="text-xs font-bold text-slate-800 dark:text-slate-200">Expansion of auto-approval logic for low-risk vehicle claims is highly recommended.</p>
                </div>
              </div>

              <Button variant="secondary" className="w-full h-14 rounded-2xl border-gray-200 dark:border-white/10 font-black tracking-widest uppercase text-xs bg-white dark:bg-white/5" onClick={() => setIsReportOpen(false)}>Dismiss Insight Intelligence</Button>
            </motion.div>
          )}
        </div>
      </Modal>
    </div>
  );
};