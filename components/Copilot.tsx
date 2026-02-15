import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  Send,
  Sparkles,
  X,
  Car,
  Heart,
  Activity,
  Home,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  AlertCircle,
  FileText,
  Download,
  MapPin,
  ArrowRight,
  UploadCloud,
  Layers,
  BookOpen,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { VantageLogo } from "./Branding";
import { cn, Button, Badge } from "./UIComponents";
import type { Policy, Claim } from "../types";

type Category = "Vehicle" | "Health" | "Life" | "Home";

/**
 * Simple markdown renderer for chatbot responses.
 * Supports: **bold**, *italic*, bullet lists, line breaks, and (Source: ...) styling.
 */
const renderMarkdown = (text: string): React.ReactNode => {
  if (!text) return null;

  // Split by double line breaks to get paragraphs
  const paragraphs = text.split(/\n\n+/);

  return paragraphs.map((paragraph, pIdx) => {
    // Check if it's a bullet list
    const lines = paragraph.split("\n");
    const isList = lines.every(
      (line) =>
        line.trim().startsWith("- ") ||
        line.trim().startsWith("* ") ||
        line.trim() === "",
    );

    if (
      isList &&
      lines.some(
        (line) => line.trim().startsWith("- ") || line.trim().startsWith("* "),
      )
    ) {
      return (
        <ul key={pIdx} className="list-disc list-inside space-y-1 my-2">
          {lines
            .filter((line) => line.trim())
            .map((line, lIdx) => (
              <li key={lIdx} className="text-sm">
                {renderInlineMarkdown(line.replace(/^[\-\*]\s*/, ""))}
              </li>
            ))}
        </ul>
      );
    }

    // Regular paragraph with line breaks
    return (
      <p key={pIdx} className={pIdx > 0 ? "mt-3" : ""}>
        {lines.map((line, lIdx) => (
          <React.Fragment key={lIdx}>
            {renderInlineMarkdown(line)}
            {lIdx < lines.length - 1 && <br />}
          </React.Fragment>
        ))}
      </p>
    );
  });
};

/**
 * Render inline markdown elements: bold, italic, source citations.
 */
const renderInlineMarkdown = (text: string): React.ReactNode => {
  if (!text) return null;

  const parts: React.ReactNode[] = [];
  let remaining = text;
  let keyIdx = 0;

  // Pattern for **bold**, *italic*, and (Source: ...)
  const patterns = [
    {
      regex: /\*\*(.+?)\*\*/g,
      render: (match: string) => (
        <strong
          key={keyIdx++}
          className="font-semibold text-slate-900 dark:text-white"
        >
          {match}
        </strong>
      ),
    },
    {
      regex: /\*(.+?)\*/g,
      render: (match: string) => (
        <em key={keyIdx++} className="italic">
          {match}
        </em>
      ),
    },
    {
      regex: /\(Source:\s*([^)]+)\)/g,
      render: (match: string) => (
        <span
          key={keyIdx++}
          className="text-xs text-emerald-600 dark:text-emerald-400 font-medium block mt-1"
        >
          (Source: {match})
        </span>
      ),
    },
  ];

  // Process bold text
  const boldRegex = /\*\*(.+?)\*\*/g;
  let lastIndex = 0;
  let match;

  while ((match = boldRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(
        processItalicsAndSources(text.slice(lastIndex, match.index), keyIdx),
      );
      keyIdx++;
    }
    parts.push(
      <strong
        key={`bold-${keyIdx++}`}
        className="font-semibold text-slate-900 dark:text-white"
      >
        {match[1]}
      </strong>,
    );
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    parts.push(processItalicsAndSources(text.slice(lastIndex), keyIdx));
  }

  return parts.length > 0 ? parts : text;
};

/**
 * Process italic and source patterns in text.
 */
const processItalicsAndSources = (
  text: string,
  baseKey: number,
): React.ReactNode => {
  if (!text) return null;

  // Handle (Source: ...) pattern - make it a nice badge-style display
  const sourceRegex = /\(Source:\s*([^)]+)\)/g;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match;
  let keyIdx = baseKey;

  while ((match = sourceRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(
        <span key={`text-${keyIdx++}`}>
          {text.slice(lastIndex, match.index)}
        </span>,
      );
    }
    parts.push(
      <span
        key={`source-${keyIdx++}`}
        className="inline-flex items-center gap-1 text-[10px] bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 px-2 py-0.5 rounded-full font-medium ml-1"
      >
        <BookOpen size={10} />
        {match[1]}
      </span>,
    );
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    parts.push(<span key={`text-end-${keyIdx}`}>{text.slice(lastIndex)}</span>);
  }

  return parts.length > 0 ? <>{parts}</> : text;
};

interface Message {
  id: string;
  sender: "user" | "ai" | "system";
  text?: string;
  type?: "text" | "summary" | "wizard" | "upload" | "status" | "alert";
  category?: Category;
  data?: any;
  sources?: Array<{ source: string; section: string; policy_number: string }>;
  ragUsed?: boolean;
}

const CATEGORIES: { id: Category; label: string; icon: any }[] = [
  { id: "Vehicle", label: "Vehicle", icon: Car },
  { id: "Health", label: "Health", icon: Heart },
  { id: "Life", label: "Life", icon: Activity },
  { id: "Home", label: "Home", icon: Home },
];

/** Map frontend category names to backend PolicyCategory values. */
const CATEGORY_TO_POLICY_TYPE: Record<Category, string> = {
  Vehicle: "Vehicle",
  Health: "Health",
  Life: "Life",
  Home: "Property",
};

const SUGGESTIONS: Record<Category, string[]> = {
  Vehicle: [
    "What does my policy cover?",
    "Start Accident Claim",
    "What's my deductible?",
    "Am I covered for theft?",
  ],
  Health: [
    "What's covered under my plan?",
    "Check Deductible",
    "Submit Invoice",
    "Is surgery covered?",
  ],
  Life: [
    "Who are my beneficiaries?",
    "Coverage Limit",
    "What's the payout process?",
    "Update Address",
  ],
  Home: [
    "What damage is covered?",
    "Report Damage",
    "Is flooding covered?",
    "What's my premium?",
  ],
};

export const Copilot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeCategory, setActiveCategory] = useState<Category>("Vehicle");
  const [isTyping, setIsTyping] = useState(false);

  // Context state: policies and claims fetched from the API
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [contextLoaded, setContextLoaded] = useState(false);

  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      sender: "ai",
      text: "Welcome to Vantage Copilot! Select a policy category (Vehicle, Health, Life, or Home) to get started. I'll show you your claims in that category and help you with specific questions about coverage, documents, and policy details.",
      type: "text",
    },
  ]);

  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages, isTyping]);

  // Fetch user's policies and claims when the copilot opens
  const loadContext = useCallback(async () => {
    if (contextLoaded) return;
    try {
      const [{ fetchPolicies }, { fetchClaims }] = await Promise.all([
        import("../src/api/endpoints"),
        import("../src/api/endpoints"),
      ]);
      const [policiesResult, claimsResult] = await Promise.allSettled([
        fetchPolicies(),
        fetchClaims(),
      ]);
      if (policiesResult.status === "fulfilled")
        setPolicies(policiesResult.value);
      if (claimsResult.status === "fulfilled") setClaims(claimsResult.value);
      setContextLoaded(true);
    } catch (err) {
      // Failed to load copilot context
    }
  }, [contextLoaded]);

  useEffect(() => {
    if (isOpen) loadContext();
  }, [isOpen, loadContext]);

  /**
   * Derive the active policy and claim based on the selected category.
   * The backend uses `policy_number` as the canonical key stored in ChromaDB.
   */
  const getActiveContext = useCallback(() => {
    const backendCategory = CATEGORY_TO_POLICY_TYPE[activeCategory];

    // Find the first policy matching this category
    const matchedPolicy =
      policies.find(
        (p) => p.category === backendCategory && p.status === "Active",
      ) || policies.find((p) => p.category === backendCategory);

    // Find the most recent claim for this policy
    const matchedClaim = matchedPolicy
      ? claims.find((c) => c.policyNumber === matchedPolicy.policyNumber)
      : undefined;

    return {
      policyNumber: matchedPolicy?.policyNumber,
      policyTitle: matchedPolicy?.title,
      claimId: matchedClaim?.id,
    };
  }, [activeCategory, policies, claims]);

  const handleSend = async (text: string = input) => {
    if (!text.trim()) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      sender: "user",
      text: text || "Action selected",
      type: "text",
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    try {
      const { chatWithCopilot } = await import("../src/api/endpoints");

      // Only send category - let the chatbot ask which claim to discuss
      // Don't auto-select policy/claim
      const result = await chatWithCopilot(text, {
        activeCategory,
        // Don't send policyNumber or claimId - let user select
      });

      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: "ai",
        text: result.response,
        type: "text",
        sources: result.sources,
        ragUsed: result.rag_context_used,
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (error: any) {
      // Copilot API Error

      // Determine a helpful error message based on the error type
      let errorText =
        "I'm having trouble connecting to the server. Please try again later.";
      const status = error?.response?.status;
      const detail = error?.response?.data?.detail;

      if (status === 429) {
        errorText =
          "The AI service is temporarily busy due to high demand. Please wait a moment and try again.";
      } else if (status === 503) {
        errorText =
          "The AI service is currently unavailable. Please check that the API key is configured.";
      } else if (status === 401) {
        errorText =
          "Your session has expired. Please sign out and sign back in.";
      } else if (status === 500 && detail) {
        errorText = `Something went wrong: ${typeof detail === "string" ? detail.slice(0, 200) : "Internal server error"}`;
      }

      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: "ai",
        text: errorText,
        type: "alert",
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  // --- Specialized Bubble Components ---

  const SmartSummary = ({
    data,
    category,
  }: {
    data: any;
    category?: Category;
  }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    return (
      <div className="bg-white dark:bg-slate-800 rounded-2xl p-4 shadow-sm border border-slate-100 dark:border-white/5 space-y-3">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Layers size={16} className="text-orange-500" />
            <span className="font-bold text-sm">{data.title}</span>
          </div>
          <Badge variant="info" className="text-[9px]">
            {category}
          </Badge>
        </div>
        <p className="text-xs text-slate-500">
          Coverage Limit:{" "}
          <span className="font-bold text-slate-900 dark:text-white">
            {data.limit}
          </span>
        </p>

        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-1 text-[10px] font-black uppercase text-orange-500 hover:text-orange-600 transition-colors"
        >
          {isExpanded ? (
            <>
              <ChevronUp size={12} /> Hide Benefits
            </>
          ) : (
            <>
              <ChevronDown size={12} /> View Benefits
            </>
          )}
        </button>

        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <ul className="space-y-1.5 mt-2 border-t pt-2 border-slate-50 dark:border-white/5">
                {data.benefits.map((b: string, i: number) => (
                  <li
                    key={i}
                    className="text-[11px] flex items-start gap-2 text-slate-600 dark:text-slate-400"
                  >
                    <CheckCircle2
                      size={12}
                      className="text-emerald-500 mt-0.5 shrink-0"
                    />{" "}
                    {b}
                  </li>
                ))}
              </ul>
              <div className="flex gap-2 mt-4">
                <Button
                  variant="secondary"
                  size="sm"
                  className="flex-1 text-[10px] h-8"
                >
                  Compare Policies
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  className="flex-1 text-[10px] h-8"
                >
                  <Download size={10} className="mr-1" /> PDF
                </Button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  };

  const ClaimWizard = ({
    data,
    category,
  }: {
    data: any;
    category?: Category;
  }) => {
    const [step, setStep] = useState(data.step);
    const [ocrProgress, setOcrProgress] = useState(0);

    const nextStep = () => {
      if (step === 1) {
        setStep(2);
        // Trigger OCR simulation
        let p = 0;
        const interval = setInterval(() => {
          p += 10;
          setOcrProgress(p);
          if (p >= 100) clearInterval(interval);
        }, 200);
      } else if (step === 2) {
        setStep(3);
      }
    };

    return (
      <div className="bg-slate-50 dark:bg-white/5 rounded-2xl p-5 border border-slate-200 dark:border-white/10 space-y-4">
        <div className="flex justify-between items-center">
          <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">
            Claim Wizard • Step {step}/3
          </span>
          <div className="flex gap-1">
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                className={cn(
                  "w-1.5 h-1.5 rounded-full transition-colors",
                  s <= step ? "bg-orange-500" : "bg-slate-200",
                )}
              />
            ))}
          </div>
        </div>

        {step === 1 && (
          <div className="space-y-3">
            <h4 className="font-bold text-sm">Tell us what happened?</h4>
            <div className="space-y-2">
              <div className="flex items-center gap-2 p-3 bg-white dark:bg-slate-800 rounded-xl border border-slate-100 dark:border-white/5">
                <MapPin size={14} className="text-slate-400" />
                <input
                  type="text"
                  placeholder="Location..."
                  className="bg-transparent text-xs w-full outline-none"
                />
                <CheckCircle2 size={14} className="text-emerald-500" />
              </div>
              <div className="flex items-center gap-2 p-3 bg-white dark:bg-slate-800 rounded-xl border border-slate-100 dark:border-white/5">
                <FileText size={14} className="text-slate-400" />
                <input
                  type="text"
                  placeholder="Incident type..."
                  className="bg-transparent text-xs w-full outline-none"
                />
                <AlertCircle size={14} className="text-rose-500" />
              </div>
            </div>
            <Button onClick={nextStep} className="w-full h-10 text-xs">
              Next <ArrowRight size={14} />
            </Button>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <h4 className="font-bold text-sm">Evidence & Verification</h4>
            <div className="p-6 border-2 border-dashed border-slate-200 dark:border-white/10 rounded-2xl flex flex-col items-center justify-center gap-2 hover:border-orange-500/50 transition-colors cursor-pointer bg-white dark:bg-white/5">
              <UploadCloud size={24} className="text-slate-300" />
              <span className="text-[10px] font-bold text-slate-400 uppercase">
                Upload Photos / Report
              </span>
            </div>

            {ocrProgress > 0 && ocrProgress < 100 && (
              <div className="space-y-1.5">
                <div className="flex justify-between text-[10px] font-bold uppercase text-slate-400">
                  <span>AI OCR Scanning...</span>
                  <span>{ocrProgress}%</span>
                </div>
                <div className="h-1 bg-slate-200 dark:bg-white/10 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${ocrProgress}%` }}
                    className="h-full bg-orange-500"
                  />
                </div>
              </div>
            )}

            <div className="space-y-1.5">
              <div className="flex items-center gap-2 text-[11px] text-slate-500">
                <CheckCircle2 size={12} className="text-emerald-500" /> Photo of
                Damage
              </div>
              <div className="flex items-center gap-2 text-[11px] text-slate-500">
                <div className="w-3 h-3 rounded-full border border-slate-300" />{" "}
                Police Report
              </div>
            </div>
            <Button
              onClick={nextStep}
              disabled={ocrProgress < 100}
              className="w-full h-10 text-xs"
            >
              Validate Documents
            </Button>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-4 animate-in fade-in zoom-in-95 duration-500">
            <div className="text-center pb-2">
              <div className="w-12 h-12 bg-emerald-500/10 text-emerald-500 rounded-full flex items-center justify-center mx-auto mb-2">
                <Sparkles size={24} />
              </div>
              <h4 className="font-bold text-sm">Settlement Estimate</h4>
              <p className="text-xs text-slate-500">
                Based on initial evidence scan
              </p>
            </div>

            <div className="p-4 bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-100 dark:border-white/5">
              <div className="flex justify-between items-end mb-1">
                <span className="text-[10px] font-bold uppercase text-slate-400">
                  Estimated Range
                </span>
                <span className="text-lg font-black text-emerald-600">
                  $1,200 - $1,500
                </span>
              </div>
              <div className="h-2 bg-slate-100 dark:bg-white/10 rounded-full overflow-hidden">
                <div className="h-full bg-emerald-500 w-3/4 ml-[10%]" />
              </div>
              <div className="grid grid-cols-2 gap-2 mt-4 text-[10px]">
                <div className="p-2 bg-slate-50 dark:bg-white/5 rounded-lg">
                  <span className="block font-bold text-slate-400 uppercase">
                    Payable
                  </span>
                  <span className="text-emerald-600 font-bold">$1,350</span>
                </div>
                <div className="p-2 bg-slate-50 dark:bg-white/5 rounded-lg">
                  <span className="block font-bold text-slate-400 uppercase">
                    Deductible
                  </span>
                  <span className="text-rose-600 font-bold">$250</span>
                </div>
              </div>
            </div>
            <Button className="w-full h-12 bg-orange-500 text-white rounded-2xl border-0 shadow-lg shadow-orange-500/20">
              Finalize Submission
            </Button>
          </div>
        )}
      </div>
    );
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className={`fixed bottom-6 right-6 p-4 rounded-full shadow-2xl z-50 transition-all duration-300 ${
          isOpen ? "scale-0 opacity-0" : "scale-100 opacity-100"
        } bg-gradient-to-r from-orange-500 to-red-500 text-white hover:scale-110 active:scale-95 group overflow-hidden`}
      >
        <Sparkles
          size={24}
          className="group-hover:rotate-12 transition-transform"
        />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 50, scale: 0.9, x: 20 }}
            animate={{ opacity: 1, y: 0, scale: 1, x: 0 }}
            exit={{ opacity: 0, y: 50, scale: 0.9, x: 20 }}
            className="fixed bottom-6 right-6 w-[420px] h-[700px] bg-white dark:bg-slate-900 rounded-[32px] shadow-2xl border border-slate-200 dark:border-white/10 flex flex-col overflow-hidden z-50 backdrop-blur-3xl bg-opacity-95 dark:bg-opacity-95"
          >
            {/* Contextual Category Selector Header */}
            <div className="p-5 border-b border-slate-100 dark:border-white/5 bg-slate-50/50 dark:bg-white/5">
              <div className="flex justify-between items-center mb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-orange-500 rounded-xl text-white shadow-lg shadow-orange-500/30">
                    <VantageLogo size={20} className="text-white" />
                  </div>
                  <div>
                    <h3 className="font-black text-sm text-slate-800 dark:text-white uppercase tracking-wider">
                      Vantage Copilot
                    </h3>
                    <span className="text-[10px] text-emerald-500 font-bold uppercase flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                      AI Engine Active
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-2 hover:bg-white dark:hover:bg-slate-800 rounded-full transition-colors border border-transparent hover:border-slate-100 shadow-sm"
                >
                  <X size={18} className="text-slate-400" />
                </button>
              </div>

              <div className="flex gap-2 p-1 bg-white/60 dark:bg-slate-800/60 rounded-2xl border border-slate-100 dark:border-white/5 shadow-sm overflow-x-auto no-scrollbar">
                {CATEGORIES.map((cat) => {
                  const Icon = cat.icon;
                  const isSelected = activeCategory === cat.id;
                  return (
                    <button
                      key={cat.id}
                      onClick={() => setActiveCategory(cat.id)}
                      className={cn(
                        "flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap",
                        isSelected
                          ? "bg-orange-500 text-white shadow-md scale-105"
                          : "text-slate-500 hover:bg-white dark:hover:bg-white/10",
                      )}
                    >
                      <Icon size={14} />
                      {cat.label}
                    </button>
                  );
                })}
              </div>

              {/* Active policy context badge */}
              {(() => {
                const ctx = getActiveContext();
                if (!ctx.policyNumber) return null;
                return (
                  <div className="mt-2 flex items-center gap-2 px-3 py-1.5 bg-emerald-50 dark:bg-emerald-900/20 rounded-xl border border-emerald-100 dark:border-emerald-800/30">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-[10px] font-bold text-emerald-700 dark:text-emerald-400 truncate">
                      Context: {ctx.policyTitle || ctx.policyNumber}
                    </span>
                    <span className="text-[9px] text-emerald-500/60 font-mono ml-auto shrink-0">
                      {ctx.policyNumber}
                    </span>
                  </div>
                );
              })()}
            </div>

            {/* Chat Body */}
            <div className="flex-1 overflow-y-auto p-5 space-y-5 custom-scrollbar bg-white dark:bg-[#0F172A]/50">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={cn(
                    "flex flex-col",
                    msg.sender === "user" ? "items-end" : "items-start",
                  )}
                >
                  <div
                    className={cn(
                      "max-w-[90%] space-y-1 group",
                      msg.sender === "user" ? "items-end" : "items-start",
                    )}
                  >
                    <div
                      className={cn(
                        "p-4 rounded-[24px] text-sm leading-relaxed shadow-sm",
                        msg.sender === "user"
                          ? "bg-orange-500 text-white rounded-br-none"
                          : "bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 rounded-bl-none border border-slate-200 dark:border-white/5",
                      )}
                    >
                      {msg.type === "summary" ? (
                        <SmartSummary data={msg.data} category={msg.category} />
                      ) : msg.type === "wizard" ? (
                        <ClaimWizard data={msg.data} category={msg.category} />
                      ) : (
                        renderMarkdown(msg.text || "")
                      )}
                    </div>
                    {/* RAG source indicator */}
                    {msg.sender === "ai" &&
                      msg.ragUsed &&
                      msg.sources &&
                      msg.sources.length > 0 && (
                        <div className="flex items-center gap-1.5 px-2 py-1">
                          <BookOpen size={10} className="text-emerald-500" />
                          <span className="text-[9px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">
                            Based on {msg.sources.length} document section
                            {msg.sources.length !== 1 ? "s" : ""}
                          </span>
                        </div>
                      )}
                    <span className="text-[10px] text-slate-400 font-bold uppercase opacity-0 group-hover:opacity-100 transition-opacity px-2">
                      {msg.sender === "user" ? "You" : "Vantage Assistant"}
                    </span>
                  </div>
                </div>
              ))}

              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-slate-100 dark:bg-slate-800 p-4 rounded-[24px] rounded-bl-none flex gap-1 shadow-sm border border-slate-200 dark:border-white/5">
                    <span className="w-2 h-2 bg-orange-500 rounded-full animate-bounce" />
                    <span className="w-2 h-2 bg-orange-500 rounded-full animate-bounce delay-75" />
                    <span className="w-2 h-2 bg-orange-500 rounded-full animate-bounce delay-150" />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Suggestions Row */}
            <div className="px-5 py-3 border-t border-slate-100 dark:border-white/5 bg-slate-50/30 dark:bg-white/5 overflow-x-auto no-scrollbar">
              <div className="flex gap-2">
                {SUGGESTIONS[activeCategory].map((s) => (
                  <button
                    key={s}
                    onClick={() => handleSend(s)}
                    className="text-[10px] font-black uppercase tracking-widest bg-white dark:bg-slate-800 hover:bg-orange-50 dark:hover:bg-orange-900/20 text-slate-500 dark:text-slate-400 hover:text-orange-600 px-4 py-2 rounded-xl transition-all border border-slate-100 dark:border-white/5 shadow-sm whitespace-nowrap active:scale-95"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {/* Input Footer */}
            <div className="p-5 border-t border-slate-100 dark:border-white/5 bg-white dark:bg-slate-900 shadow-lg relative z-20">
              <div className="relative">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSend()}
                  placeholder="Ask Vantage about your claim..."
                  className="w-full pl-5 pr-14 py-4 bg-slate-100 dark:bg-slate-800 rounded-[24px] focus:outline-none focus:ring-4 focus:ring-orange-500/10 text-sm transition-all border border-transparent focus:border-orange-500/20 shadow-inner"
                />
                <button
                  onClick={() => handleSend()}
                  disabled={!input.trim()}
                  className="absolute right-2 top-2 p-2.5 bg-orange-500 text-white rounded-2xl hover:bg-orange-600 transition-all shadow-lg shadow-orange-500/30 disabled:opacity-50 disabled:shadow-none"
                >
                  <Send size={18} />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};
