import React, { useState, useMemo, useEffect } from 'react';
import { Card, Button, Badge, cn, Modal, TextArea } from '../components/UIComponents';
import { Document } from '../types';
import { FileText, Search, LayoutGrid, List as ListIcon, ScanLine, ArrowRight, Download, User as UserIcon, FolderOpen, Sparkles, ClipboardCheck, AlertTriangle, RefreshCw } from 'lucide-react';
import { extractDocumentEntities } from '../services/geminiService';
import { motion, AnimatePresence } from 'framer-motion';
import { ThreeScene } from '../components/ThreeScene';

// Extend Document type locally to include claimant and claim type info
type ExtendedDocument = Document & { claimant?: string; claimId?: string; claimType?: string; userEmail?: string };

export const Documents = () => {
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
    const [selectedCategory, setSelectedCategory] = useState<string>('All');
    const [searchQuery, setSearchQuery] = useState('');
    const [processingId, setProcessingId] = useState<string | null>(null);

    // Initialize documents derived from Claims to link them to Policy Holders and Types
    const [documents, setDocuments] = useState<ExtendedDocument[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [loadError, setLoadError] = useState<string | null>(null);

    useEffect(() => {
        const loadDocs = async () => {
            try {
                setIsLoading(true);
                setLoadError(null);
                const { fetchDocuments, fetchClaims } = await import('../src/api/endpoints');
                // Load from both: GET /documents (all DB docs) + claims (same claim context as before)
                const [list, claims] = await Promise.all([fetchDocuments(), fetchClaims()]);

                const formatDate = (dateVal: string | undefined) => {
                    if (!dateVal) return dateVal;
                    try {
                        const d = new Date(dateVal);
                        return !isNaN(d.getTime()) ? d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : dateVal;
                    } catch { return dateVal; }
                };

                const byId = new Map<string, ExtendedDocument>();
                list.forEach((doc: any) => {
                    byId.set(doc.id, {
                        ...doc,
                        date: formatDate(doc.date),
                        id: doc.id,
                        originalId: doc.id,
                        claimant: doc.claimant,
                        claimId: doc.claimId,
                        claimType: doc.claimType,
                        userEmail: doc.user_email,
                    });
                });

                // Overlay claim-linked docs from claims API so claimant/claimType match previous behavior
                claims.forEach((claim: any) => {
                    const claimant = claim.claimant ?? claim.claimant_name;
                    (claim.documents || []).forEach((doc: any) => {
                        const existing = byId.get(doc.id);
                        const extended: ExtendedDocument = {
                            ...(existing ?? doc),
                            date: formatDate((existing ?? doc).date),
                            id: doc.id,
                            originalId: doc.id,
                            claimant: claimant,
                            claimId: claim.id,
                            claimType: claim.type,
                            userEmail: (existing ?? doc).user_email ?? (doc as any).user_email,
                        };
                        byId.set(doc.id, extended);
                    });
                });

                const allDocs = Array.from(byId.values()).sort((a, b) => (a.claimant || '').localeCompare(b.claimant || ''));
                setDocuments(allDocs);
            } catch (error: any) {
                console.error("Failed to load documents:", error);
                setLoadError(error?.response?.data?.detail || 'Failed to load documents. Is the backend running?');
            } finally {
                setIsLoading(false);
            }
        };
        loadDocs();
    }, []);

    const handleSmartExtract = async (docId: string) => {
        setProcessingId(docId);
        const doc = documents.find(d => d.id === docId);
        if (doc) {
            const entities = await extractDocumentEntities(doc);
            setDocuments(prev => prev.map(d => d.id === docId ? { ...d, extractedEntities: entities } : d));
        }
        setProcessingId(null);
    };

    const handleDownload = (docName: string) => {
        // Mock download
        const element = document.createElement("a");
        const file = new Blob(["Mock content"], { type: 'text/plain' });
        element.href = URL.createObjectURL(file);
        element.download = docName;
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
    };

    const categories = ['All', 'Legal', 'Medical', 'Financial', 'Evidence'];

    const filteredDocs = documents.filter(doc => {
        const matchesCategory = selectedCategory === 'All' || doc.category === selectedCategory;
        const lowerQuery = searchQuery.toLowerCase();

        // Enhanced Search Logic including Claimant Name and Policy Type
        const matchesSearch =
            doc.name.toLowerCase().includes(lowerQuery) ||
            (doc.claimant?.toLowerCase().includes(lowerQuery) ?? false) ||
            (doc.claimType?.toLowerCase().includes(lowerQuery) ?? false) ||
            (doc.summary?.toLowerCase().includes(lowerQuery) ?? false) ||
            (doc.extractedEntities && Object.values(doc.extractedEntities).some((v: any) => (v as string).toLowerCase().includes(lowerQuery)));

        return matchesCategory && matchesSearch;
    });

    // Group filtered documents by Claimant -> Claim Type
    const groupedDocs = useMemo(() => {
        const groups: Record<string, Record<string, ExtendedDocument[]>> = {};

        filteredDocs.forEach(doc => {
            const holder = doc.claimant || 'Unassigned';
            const type = doc.claimType || 'General';

            if (!groups[holder]) groups[holder] = {};
            if (!groups[holder][type]) groups[holder][type] = [];

            groups[holder][type].push(doc);
        });

        return groups;
    }, [filteredDocs]);

    return (
        <div className="relative p-8 h-full flex flex-col gap-8 bg-transparent transition-colors duration-500">
            {/* 3D Background effect */}
            <div className="absolute inset-0 z-0 opacity-5 pointer-events-none">
                <ThreeScene />
            </div>

            <div className="relative z-10 flex flex-col md:flex-row justify-between items-end shrink-0">
                <div>
                    <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2 tracking-tight">Documents Hub</h1>
                    <p className="text-gray-500">Centralized intelligent file management.</p>
                </div>

                <div className="flex items-center gap-3">
                    <div className="bg-white/40 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl p-1 flex backdrop-blur-md">
                        <button
                            onClick={() => setViewMode('grid')}
                            className={cn("p-2 rounded-lg transition-all", viewMode === 'grid' ? "bg-white/80 dark:bg-white/10 text-gray-900 dark:text-white shadow-sm" : "text-gray-400")}
                        >
                            <LayoutGrid size={18} />
                        </button>
                        <button
                            onClick={() => setViewMode('list')}
                            className={cn("p-2 rounded-lg transition-all", viewMode === 'list' ? "bg-white/80 dark:bg-white/10 text-gray-900 dark:text-white shadow-sm" : "text-gray-400")}
                        >
                            <ListIcon size={18} />
                        </button>
                    </div>
                </div>
            </div>

            <div className="relative z-10 flex flex-col lg:flex-row gap-8 flex-1 min-h-0">
                {/* Sidebar / Filters */}
                <div className="w-full lg:w-64 shrink-0 space-y-2 h-full overflow-y-auto custom-scrollbar pr-2">
                    <div className="relative mb-6">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search files..."
                            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white/40 dark:bg-white/5 border border-gray-200 dark:border-white/10 focus:ring-2 focus:ring-[#F97316]/50 outline-none text-sm backdrop-blur-md transition-all"
                        />
                    </div>

                    <div className="space-y-1">
                        {categories.map(cat => (
                            <button
                                key={cat}
                                onClick={() => setSelectedCategory(cat)}
                                className={cn(
                                    "w-full text-left px-4 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center justify-between group backdrop-blur-sm",
                                    selectedCategory === cat
                                        ? "bg-[#F97316]/10 text-[#F97316] border border-[#F97316]/20"
                                        : "text-gray-600 dark:text-gray-400 hover:bg-white/40 dark:hover:bg-white/5 border border-transparent"
                                )}
                            >
                                {cat}
                                {selectedCategory === cat && <ArrowRight size={14} className="opacity-0 group-hover:opacity-100 transition-opacity" />}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Main Content Area */}
                <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar pb-10 space-y-8">
                    {loadError ? (
                        <div className="flex flex-col items-center justify-center h-64 text-red-500">
                            <AlertTriangle size={48} className="mb-4 opacity-50" />
                            <p className="font-bold mb-1">Failed to load documents</p>
                            <p className="text-sm text-red-400 max-w-md text-center">{loadError}</p>
                        </div>
                    ) : isLoading ? (
                        <div className="flex flex-col items-center justify-center h-64 text-gray-400">
                            <RefreshCw size={32} className="animate-spin mb-4 opacity-50" />
                            <p className="font-medium">Loading documents...</p>
                        </div>
                    ) : Object.keys(groupedDocs).length === 0 && (
                        <div className="flex flex-col items-center justify-center h-64 text-gray-400">
                            <FileText size={48} className="mb-4 opacity-50" />
                            <p>No documents found matching your criteria.</p>
                        </div>
                    )}

                    {Object.entries(groupedDocs).map(([claimant, typeGroups]: [string, Record<string, ExtendedDocument[]>]) => (
                        <div key={claimant} className="animate-in fade-in slide-in-from-bottom-4 duration-500 mb-8">
                            {/* Policy Holder Header - REPLACED BACKGROUND WITH TRANSPARENT/GLASS STYLE */}
                            <div className="flex items-center gap-3 mb-6 sticky top-0 z-20 py-3 bg-white/10 dark:bg-black/10 backdrop-blur-lg border border-white/20 dark:border-white/5 shadow-sm transition-all rounded-2xl px-4">
                                <div className="p-2 bg-orange-500/10 dark:bg-orange-900/20 rounded-lg text-orange-600 dark:text-orange-400 shadow-sm backdrop-blur-md">
                                    <UserIcon size={18} />
                                </div>
                                <h2 className="text-xl font-bold text-gray-900 dark:text-white tracking-tight">{claimant}</h2>
                                <Badge variant="default" className="bg-white/50 dark:bg-white/10 backdrop-blur-md border-white/20">
                                    {Object.values(typeGroups).reduce((acc, curr) => acc + curr.length, 0)} Files
                                </Badge>
                            </div>

                            {/* Iterate over Policy Types within this Holder */}
                            <div className="space-y-8 pl-2">
                                {Object.entries(typeGroups).map(([type, groupDocs]) => (
                                    <div key={type} className="relative">
                                        {/* Policy Type Sub-header */}
                                        <div className="flex items-center gap-2 mb-3 pl-2 border-l-2 border-orange-200 dark:border-orange-800 ml-1">
                                            <FolderOpen size={16} className="text-gray-400" />
                                            <h3 className="text-sm font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                                                {type} Claim
                                            </h3>
                                            <span className="text-xs text-gray-400 font-medium bg-gray-100 dark:bg-white/5 px-1.5 py-0.5 rounded-full">{groupDocs.length}</span>
                                        </div>

                                        {viewMode === 'grid' ? (
                                            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                                                <AnimatePresence>
                                                    {groupDocs.map((doc) => (
                                                        <motion.div
                                                            layout
                                                            key={doc.id}
                                                            initial={{ opacity: 0, scale: 0.9 }}
                                                            animate={{ opacity: 1, scale: 1 }}
                                                            exit={{ opacity: 0, scale: 0.9 }}
                                                        >
                                                            <Card className="h-full flex flex-col p-5 hover:shadow-lg transition-all group border border-gray-100 dark:border-white/5 bg-white/40 dark:bg-[#1C1C1E]/40 backdrop-blur-md">
                                                                <div className="flex justify-between items-start mb-4">
                                                                    <div className={cn("p-3 rounded-2xl",
                                                                        doc.type === 'PDF' ? 'bg-red-50 text-red-500' :
                                                                            doc.type === 'DOCX' ? 'bg-blue-50 text-blue-500' : 'bg-green-50 text-green-50'
                                                                    )}>
                                                                        <FileText size={24} />
                                                                    </div>
                                                                    <button
                                                                        onClick={() => handleDownload(doc.name)}
                                                                        className="text-gray-300 hover:text-[#F97316] transition-colors"
                                                                    >
                                                                        <Download size={18} />
                                                                    </button>
                                                                </div>

                                                                <h3 className="font-semibold text-gray-900 dark:text-white truncate mb-1" title={doc.name}>
                                                                    {doc.name.toLowerCase().includes(searchQuery.toLowerCase()) ? (
                                                                        <span className="text-orange-600 dark:text-orange-400">{doc.name}</span>
                                                                    ) : doc.name}
                                                                </h3>

                                                                <div className="flex gap-2 text-xs text-gray-500 mb-4 mt-2">
                                                                    <span className="bg-gray-100 dark:bg-white/10 px-2 py-0.5 rounded">{doc.type}</span>
                                                                    <span>{doc.size}</span>
                                                                    <span>• {doc.date}</span>
                                                                </div>

                                                                {doc.extractedEntities ? (
                                                                    <div className="mt-auto bg-[#F97316]/5 border border-[#F97316]/10 rounded-xl p-3 text-xs space-y-1">
                                                                        <p className="font-bold text-[#F97316] flex items-center gap-1 mb-2">
                                                                            <ScanLine size={12} /> Data Extracted
                                                                        </p>
                                                                        {Object.entries(doc.extractedEntities).map(([k, v]) => (
                                                                            <div key={k} className="flex justify-between border-b border-[#F97316]/5 pb-1 last:border-0">
                                                                                <span className="text-gray-500">{k}:</span>
                                                                                <span className={cn("font-medium truncate max-w-[100px]",
                                                                                    searchQuery && (v as string).toLowerCase().includes(searchQuery.toLowerCase()) ? "text-[#EA4335] bg-yellow-100 dark:bg-yellow-900/30 px-1 rounded" : "text-gray-700 dark:text-gray-300"
                                                                                )}>{v}</span>
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                ) : (
                                                                    <Button
                                                                        variant="secondary"
                                                                        size="sm"
                                                                        className="mt-auto w-full group-hover:bg-[#F97316] group-hover:text-white border-dashed border-gray-300 group-hover:border-transparent bg-white/50 dark:bg-white/5"
                                                                        onClick={() => handleSmartExtract(doc.id)}
                                                                    >
                                                                        {processingId === doc.id ? (
                                                                            <span className="flex items-center gap-2"><div className="w-3 h-3 rounded-full border-2 border-white/50 border-t-white animate-spin" /> Processing...</span>
                                                                        ) : (
                                                                            <><ScanLine size={14} /> Smart Extract</>
                                                                        )}
                                                                    </Button>
                                                                )}
                                                            </Card>
                                                        </motion.div>
                                                    ))}
                                                </AnimatePresence>
                                            </div>
                                        ) : (
                                            <Card className="flex flex-col p-0 ml-2 bg-white/40 dark:bg-[#1C1C1E]/40 backdrop-blur-md border border-white/20">
                                                <div className="grid grid-cols-12 p-4 border-b border-gray-100 dark:border-white/5 text-xs font-bold text-gray-400 uppercase bg-gray-50/30 dark:bg-white/5">
                                                    <div className="col-span-3">Name</div>
                                                    <div className="col-span-3">User Email</div>
                                                    <div className="col-span-2">Type</div>
                                                    <div className="col-span-2">Category</div>
                                                    <div className="col-span-2 text-right">Date</div>
                                                </div>
                                                {groupDocs.map(doc => (
                                                    <motion.div
                                                        initial={{ opacity: 0, y: 10 }}
                                                        animate={{ opacity: 1, y: 0 }}
                                                        key={doc.id}
                                                        className="grid grid-cols-12 p-4 items-center hover:bg-white/40 dark:hover:bg-white/5 border-b border-gray-50 dark:border-white/5 last:border-0 transition-colors"
                                                    >
                                                        <div className="col-span-3 flex items-center gap-3 overflow-hidden">
                                                            <FileText size={18} className="text-gray-400 shrink-0" />
                                                            <div className="min-w-0">
                                                                <span className="font-medium text-gray-900 dark:text-white truncate block">{doc.name}</span>
                                                                {searchQuery && doc.extractedEntities && Object.values(doc.extractedEntities).some((v: any) => (v as string).toLowerCase().includes(searchQuery.toLowerCase())) && (
                                                                    <span className="text-[10px] text-green-600 bg-green-50 px-1.5 py-0.5 rounded flex items-center gap-1 w-fit mt-1">
                                                                        <ScanLine size={10} /> Content Match
                                                                    </span>
                                                                )}
                                                            </div>
                                                        </div>
                                                        <div className="col-span-3 text-sm text-gray-600 dark:text-gray-400 truncate pr-2" title={doc.userEmail}>
                                                            {doc.userEmail || 'N/A'}
                                                        </div>
                                                        <div className="col-span-2 text-sm text-gray-500">{doc.type}</div>
                                                        <div className="col-span-2">
                                                            <Badge variant="default" className="bg-white/50 dark:bg-white/10 backdrop-blur-sm">{doc.category || 'General'}</Badge>
                                                        </div>
                                                        <div className="col-span-2 text-sm text-gray-500 text-right flex items-center justify-end gap-3">
                                                            <span>{doc.date}</span>
                                                            <button
                                                                onClick={() => handleDownload(doc.name)}
                                                                className="p-1.5 hover:bg-gray-200 dark:hover:bg-white/10 rounded-full text-gray-400 transition-colors"
                                                                title="Download"
                                                            >
                                                                <Download size={14} />
                                                            </button>
                                                        </div>
                                                    </motion.div>
                                                ))}
                                            </Card>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};