
import React, { useState, useMemo, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, Button, Badge, Modal, cn, Input, TextArea, Select, Toast } from '../components/UIComponents';
import { MOCK_POLICIES, MOCK_CLAIMS, CURRENT_USER } from '../constants';
import { Policy, PolicyCategory, Status, Claim } from '../types';
import { fetchPolicies, fetchClaims, createClaim, createPolicy, uploadDocument, finalizeClaim, getCurrentUser } from '../src/api/endpoints';
import {
    Heart,
    Car,
    Home,
    Activity,
    ArrowRight,
    CheckCircle,
    Clock,
    Loader2,
    XCircle,
    Shield,
    FileText,
    Plus,
    Zap,
    Sparkles,
    ClipboardCheck,
    Calendar,
    MapPin,
    FileBadge,
    Eye,
    ChevronRight,
    Trash2,
    Stethoscope,
    Building2,
    User as UserIcon,
    Phone,
    Hash,
    AlertTriangle,
    Signature,
    Upload,
    FileCheck,
    AlertCircle,
    FileUp,
    X,
    ChevronLeft,
    ZoomIn,
    ZoomOut,
    Printer
} from 'lucide-react';
import { generateClaimForm } from '../services/geminiService';
import { ThreeScene } from '../components/ThreeScene';

// --- Shared Document Template Components ---

const OFFERED_POLICIES = [
    { category: 'Life', title: 'Platinum Life L-100', coverage_amount: 10000000, premium: 2000, features: ['Term Life', 'Critical Illness', 'Total Disability'] },
    { category: 'Health', title: 'Health Shield H-500', coverage_amount: 500000, premium: 500, features: ['Cashless', 'OPD Cover', 'No Claim Bonus'] },
    { category: 'Vehicle', title: 'Drive Secure V-15', coverage_amount: 1500000, premium: 800, features: ['Zero Dep', 'Roadside Assist', 'Engine Protect'] },
    { category: 'Property', title: 'Home Protect P-50', coverage_amount: 5000000, premium: 1200, features: ['Fire & Burglary', 'Content Cover', 'Natural Calamity'] }
];

const DocHeader = ({ title, claimNo, date, status, icon: Icon, emoji }: any) => (
    <div className="flex justify-between items-start border-b-2 border-gray-900 pb-6 mb-6">
        <div className="flex items-center gap-3">
            <div className="p-2 bg-gray-900 rounded-lg text-white">
                <Icon size={24} />
            </div>
            <div>
                <h1 className="text-xl font-black tracking-tighter text-gray-900 uppercase leading-tight">
                    {emoji} INSURECORP
                </h1>
                <p className="text-[8px] text-gray-500 font-bold uppercase tracking-[0.2em]">Global Insurance Group</p>
            </div>
        </div>
        <div className="text-right">
            <h2 className="text-xs font-bold uppercase tracking-widest text-gray-800">{title}</h2>
            <div className="flex flex-col gap-0.5 mt-1 font-mono text-[9px]">
                <p><span className="text-gray-400">Ref No:</span> <span className="text-gray-900 font-bold">{claimNo}</span></p>
                <p><span className="text-gray-400">Date:</span> <span className="text-gray-900">{date}</span></p>
                <p><span className="text-gray-400">Status:</span> <span className="text-orange-600 font-bold uppercase">{status}</span></p>
            </div>
        </div>
    </div>
);

const DocSection = ({ title, emoji, children }: any) => (
    <div className="mb-6">
        <h3 className="text-[10px] font-black uppercase text-gray-400 tracking-widest border-b border-gray-100 pb-1 mb-3">{emoji} {title}</h3>
        {children}
    </div>
);

const DocGrid = ({ items }: { items: { label: string; value: any }[] }) => (
    <div className="grid grid-cols-2 gap-x-8 gap-y-3 text-[11px]">
        {items.map((item, i) => (
            <div key={i} className="flex flex-col">
                <span className="text-[9px] font-bold text-gray-400 uppercase tracking-wider mb-0.5">{item.label}</span>
                <span className="font-semibold text-gray-900">{item.value || 'Not Provided'}</span>
            </div>
        ))}
    </div>
);

// --- Claim Tracker Component ---
const ClaimTracker = ({ claim }: { claim: any }) => {
    // Simplified steps for user portal (removed "Paid")
    const steps = [
        { label: 'Submitted', status: Status.New },
        { label: 'In Review', status: Status.InReview },
        { label: claim.status === Status.Rejected ? 'Rejected' : 'Approved', status: claim.status === Status.Rejected ? Status.Rejected : Status.Approved }
    ];

    let currentStep = 0;
    let isRejected = claim.status === Status.Rejected;

    // Map "Analyzing" to "In Review" for user-friendly display
    const displayStatus = claim.status === Status.Analyzing ? Status.InReview : claim.status;

    if (displayStatus === Status.InReview || displayStatus === Status.Flagged) currentStep = 1;
    else if (displayStatus === Status.Approved) currentStep = 2;
    else if (displayStatus === Status.Rejected) currentStep = 2;

    const progressColor = isRejected ? 'bg-rose-500' : 'bg-[#2563EB]';

    return (
        <div className="w-full">
            <div className="flex justify-between items-center mb-4">
                <div>
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
                        Claim #{claim.id}
                        <Badge variant={displayStatus === Status.Approved ? 'info' : displayStatus === Status.Rejected ? 'danger' : 'warning'}>{displayStatus}</Badge>
                    </h3>
                    <p className="text-sm text-gray-500 mt-0.5">{claim.type} • Filed on {claim.date}</p>
                </div>
                <div className="text-right">
                    <p className="text-[10px] text-gray-400 uppercase tracking-wider font-bold">Claim Amount</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">₹{claim.amount.toLocaleString()}</p>
                </div>
            </div>

            <div className="relative mb-6 px-4">
                <div className="absolute top-1/2 left-0 w-full h-1.5 bg-gray-100 dark:bg-white/10 -translate-y-1/2 rounded-full" />
                <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(currentStep / (steps.length - 1)) * 100}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className={cn("absolute top-1/2 left-0 h-1.5 -translate-y-1/2 rounded-full transition-colors duration-500", progressColor)}
                />
                <div className="relative flex justify-between z-10 w-full">
                    {steps.map((step, index) => {
                        const isCompleted = index <= currentStep;
                        const isCurrent = index === currentStep;
                        let StepIcon = CheckCircle;

                        // Determine icon based on status
                        if (index === 2 && isRejected) StepIcon = XCircle;
                        else if (index === currentStep && displayStatus !== Status.Approved && displayStatus !== Status.Rejected) StepIcon = Loader2;

                        // Determine color
                        const stepColor = isRejected && index === 2 ? '#F43F5E' :
                            isCompleted ? '#2563EB' : '#F1F5F9';

                        return (
                            <div key={index} className="flex flex-col items-center -ml-4 first:ml-0 last:mr-0">
                                <motion.div
                                    animate={{
                                        scale: isCurrent ? 1.1 : 1,
                                        backgroundColor: stepColor,
                                        borderColor: isCurrent ? '#FFF' : 'transparent'
                                    }}
                                    className={cn(
                                        "w-10 h-10 rounded-full flex items-center justify-center border-4 transition-colors duration-500 shadow-lg",
                                        isCompleted ? "text-white" : "bg-gray-100 dark:bg-white/5 text-gray-300 dark:text-gray-600"
                                    )}
                                >
                                    {isCompleted ? (
                                        <StepIcon size={16} strokeWidth={3} className={cn(isCurrent && displayStatus !== Status.Approved && displayStatus !== Status.Rejected && "animate-spin")} />
                                    ) : (
                                        <div className="w-2.5 h-2.5 rounded-full bg-current" />
                                    )}
                                </motion.div>
                                <span className={cn(
                                    "absolute top-12 text-xs font-bold transition-colors duration-300 w-24 text-center",
                                    isCurrent ? (isRejected ? "text-rose-600" : "text-blue-600") : "text-gray-400"
                                )}>
                                    {step.label}
                                </span>
                            </div>
                        );
                    })}
                </div>
            </div>

            <div className={cn(
                "p-4 rounded-2xl border flex items-start gap-4 shadow-sm",
                isRejected ? "bg-rose-50 dark:bg-rose-900/10 border-rose-100 dark:border-rose-500/20" :
                    "bg-blue-50/50 dark:bg-blue-900/10 border-blue-100 dark:border-blue-500/20"
            )}>
                <div className={cn("p-2 rounded-xl shrink-0",
                    isRejected ? "bg-rose-100 text-rose-600" :
                        "bg-blue-100 text-blue-600"
                )}>
                    {isRejected ? <XCircle size={18} /> : displayStatus === Status.Approved ? <CheckCircle size={18} /> : <Activity size={18} />}
                </div>
                <div>
                    <p className={cn("text-sm font-bold mb-0.5",
                        isRejected ? "text-rose-900 dark:text-rose-100" :
                            "text-gray-900 dark:text-white"
                    )}>
                        {displayStatus === Status.New && "Claim Submitted Successfully"}
                        {displayStatus === Status.InReview && "Adjuster Review in Progress"}
                        {displayStatus === Status.Flagged && "Additional Assessment Required"}
                        {displayStatus === Status.Approved && "Claim Approved for Settlement"}
                        {displayStatus === Status.Rejected && "Claim Request Rejected"}
                    </p>
                    <p className={cn("text-xs",
                        isRejected ? "text-rose-700 dark:text-rose-300" :
                            "text-gray-600 dark:text-gray-400"
                    )}>
                        {displayStatus === Status.New && "Your claim has been received and queued for assignment."}
                        {displayStatus === Status.InReview && "Our intelligent systems are analyzing the evidence."}
                        {displayStatus === Status.Flagged && "We need a few more details to process your claim."}
                        {displayStatus === Status.Approved && "Great news! Your claim has been approved."}
                        {displayStatus === Status.Rejected && "Unfortunately, your claim does not meet criteria."}
                    </p>
                </div>
            </div>
        </div>
    );
};

// --- Standardized Policy Card ---
const PolicyCard: React.FC<{ policy: Policy; activeClaim?: Claim; onViewPolicy: () => void; onNewClaim: (e: React.MouseEvent) => void }> = ({ policy, activeClaim, onViewPolicy, onNewClaim }) => {
    const getIcon = (cat: PolicyCategory) => {
        switch (cat) {
            case 'Life': return <Activity size={24} />;
            case 'Health': return <Heart size={24} />;
            case 'Vehicle': return <Car size={24} />;
            case 'Property': return <Home size={24} />;
        }
    };

    const getTheme = (cat: PolicyCategory) => {
        switch (cat) {
            case 'Life': return { bg: 'bg-cyan-50/50 dark:bg-cyan-900/20', border: 'border-cyan-100 dark:border-cyan-500/20', iconColor: 'text-cyan-600', button: 'bg-cyan-600 text-white hover:bg-cyan-700' };
            case 'Health': return { bg: 'bg-emerald-50/50 dark:bg-emerald-900/20', border: 'border-emerald-100 dark:border-emerald-500/20', iconColor: 'text-emerald-600', button: 'bg-emerald-600 text-white hover:bg-emerald-700' };
            case 'Vehicle': return { bg: 'bg-violet-50/50 dark:bg-violet-900/20', border: 'border-violet-100 dark:border-violet-500/20', iconColor: 'text-violet-600', button: 'bg-violet-600 text-white hover:bg-violet-700' };
            case 'Property': return { bg: 'bg-amber-50/50 dark:bg-amber-900/20', border: 'border-amber-100 dark:border-amber-500/20', iconColor: 'text-amber-600', button: 'bg-amber-600 text-white hover:bg-amber-700' };
        }
    };

    const theme = getTheme(policy.category);

    // Helper to highlight the category word in the standardized title
    const renderStyledTitle = (title: string) => {
        const parts = title.split(' ');
        // Format is "Tier Category Code" e.g. "Platinum Life L-100"
        // We want the 2nd word to be emphasized
        return (
            <span className="flex flex-wrap items-baseline gap-x-1.5">
                <span className="text-gray-500 dark:text-gray-400 text-sm font-medium">{parts[0]}</span>
                <span className="text-xl font-black text-gray-900 dark:text-white uppercase tracking-tight">{parts[1]}</span>
                <span className="text-gray-500 dark:text-gray-400 text-sm font-bold">{parts[2]}</span>
            </span>
        );
    };

    return (
        <motion.div whileHover={{ y: -5 }} className="h-full">
            <Card className={cn("h-full flex flex-col justify-between p-0 overflow-hidden", theme.bg, theme.border)}>
                <div className="p-6 flex-1">
                    <div className="flex justify-between items-start mb-6">
                        <div className={cn("p-4 rounded-2xl bg-white dark:bg-white/10 shadow-md border border-white/20", theme.iconColor)}>
                            {getIcon(policy.category)}
                        </div>
                        <Badge variant="success" className="font-black">{policy.status}</Badge>
                    </div>
                    <div className="mb-4">
                        {renderStyledTitle(policy.title)}
                        <p className="text-[10px] font-mono text-gray-400 mt-1.5 font-bold tracking-widest uppercase">{policy.policyNumber}</p>
                    </div>
                    <div className="pt-4 border-t border-black/5 dark:border-white/5">
                        <p className="text-[9px] uppercase font-black text-gray-400 tracking-widest mb-1">Total Coverage Limit</p>
                        <p className="text-xl font-black text-gray-900 dark:text-white">₹{policy.coverageAmount.toLocaleString()}</p>
                    </div>
                </div>
                <div className="p-4 pt-0 grid grid-cols-2 gap-2">
                    <Button variant="secondary" size="sm" onClick={onViewPolicy} className="rounded-xl h-10 font-bold"><Eye size={14} /> Details</Button>
                    <Button
                        size="sm"
                        onClick={onNewClaim}
                        disabled={!!activeClaim}
                        className={cn("rounded-xl h-10 border-0 shadow-lg font-bold transition-all", theme.button, !!activeClaim && "opacity-70 grayscale")}
                    >
                        {activeClaim ? <><FileBadge size={14} /> {activeClaim.status}</> : <><Plus size={14} /> File Claim</>}
                    </Button>
                </div>
            </Card>
        </motion.div>
    );
};

// --- Form Wizard Helpers ---

const FormLabel = ({ children, icon: Icon }: any) => (
    <label className="text-[10px] font-black uppercase tracking-widest text-gray-400 flex items-center gap-2 mb-1.5">
        {Icon && <Icon size={12} />} {children}
    </label>
);

const MANDATORY_DOCS: Record<PolicyCategory, string[]> = {
    Health: ['Hospital Bills', 'Discharge Summary', 'Doctor Prescription', 'Government ID Proof', 'Policy Document'],
    Vehicle: ['Vehicle Registration Certificate (RC)', 'Photos of Vehicle Damage', 'Repair Estimate / Quotation', 'Driving License', 'FIR / Police Report (for accidents)'],
    Property: ['Damage Photographs', 'Repair Estimate / Contractor Quotation', 'Ownership Proof / Property Deed', 'Incident Report (Fire / Police / Society)'],
    Life: ['Death Certificate', 'Claimant (Nominee) ID Proof', 'Policy Document', 'Medical Records (if death due to illness)', 'Cancelled Cheque / Bank Proof'],
    Travel: ['Passport Copy', 'Visa Copy', 'Ticket Details', 'Boarding Pass', 'Incident Report (Police/Airline)'],
};

const UploadSlot: React.FC<{
    label: string;
    onFileSelect: (file: File | null) => void;
    uploadedFile?: File | null;
}> = ({ label, onFileSelect, uploadedFile }) => {
    const fileInputRef = React.useRef<HTMLInputElement>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            // Validate file type
            if (file.type !== 'application/pdf') {
                alert('Only PDF files are allowed');
                return;
            }
            // Validate file size (max 10MB)
            if (file.size > 10 * 1024 * 1024) {
                alert('File size must be less than 10MB');
                return;
            }
            onFileSelect(file);
        }
    };

    const handleClick = () => {
        if (!uploadedFile) {
            fileInputRef.current?.click();
        }
    };

    const handleRemove = (e: React.MouseEvent) => {
        e.stopPropagation();
        onFileSelect(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    return (
        <div
            onClick={handleClick}
            className={cn(
                "w-full flex items-center justify-between p-4 rounded-2xl border-2 transition-all cursor-pointer group",
                uploadedFile
                    ? "bg-emerald-50 border-emerald-100 text-emerald-700 cursor-default"
                    : "bg-white dark:bg-white/5 border-gray-100 dark:border-white/5 text-gray-700 dark:text-gray-300 hover:border-blue-400 dark:hover:border-blue-500/50 hover:bg-blue-50/30"
            )}
        >
            <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,application/pdf"
                onChange={handleFileChange}
                className="hidden"
            />
            <div className="flex items-center gap-4 overflow-hidden">
                <div className={cn(
                    "w-10 h-10 rounded-xl flex items-center justify-center transition-colors shrink-0",
                    uploadedFile ? "bg-emerald-100 text-emerald-600" : "bg-gray-100 dark:bg-white/10 text-gray-400 group-hover:bg-blue-100 group-hover:text-blue-600"
                )}>
                    {uploadedFile ? <FileCheck size={20} /> : <FileUp size={20} />}
                </div>
                <div className="flex flex-col overflow-hidden">
                    <span className="text-sm font-bold truncate">{label}</span>
                    {uploadedFile ? (
                        <span className="text-[10px] font-mono text-emerald-600 opacity-80 truncate">{uploadedFile.name}</span>
                    ) : (
                        <span className="text-[10px] text-gray-400 uppercase font-black tracking-widest">Click to upload PDF</span>
                    )}
                </div>
            </div>
            {uploadedFile && (
                <div className="flex items-center gap-2">
                    <Badge variant="success" className="bg-emerald-100 border-0 text-emerald-700">Ready</Badge>
                    <button
                        onClick={handleRemove}
                        className="p-1.5 hover:bg-emerald-200/50 rounded-full transition-colors text-emerald-800"
                    >
                        <X size={14} />
                    </button>
                </div>
            )}
        </div>
    );
};



export const UserDashboard = () => {
    const [policies, setPolicies] = useState<Policy[]>([]);
    const [userClaims, setUserClaims] = useState<Claim[]>([]);
    const [selectedPolicy, setSelectedPolicy] = useState<Policy | null>(null);
    const [claimingPolicy, setClaimingPolicy] = useState<Policy | null>(null);
    const [wizardStep, setWizardStep] = useState<'info' | 'details' | 'documents' | 'breakdown' | 'preview'>('info');
    const [toast, setToast] = useState<{ msg: string, type: 'success' | 'error' } | null>(null);
    const [showMarketplace, setShowMarketplace] = useState(false);

    const [formData, setFormData] = useState<any>({
        incidentDate: new Date().toISOString().split('T')[0],
        incidentTime: '12:00',
        location: '',
        description: '',
        uploadedDocs: {} as Record<string, File | null>,
        items: [{ item: '', cost: 0 }],
        // Vehicle optional fields
        makeModel: '', regNumber: '', vin: '', odometer: '',
        vehicleIncidentType: 'Collision', policeReportFiled: false, policeReportNo: '',
        // Health optional fields
        dob: '', patientName: '', relationship: 'Self',
        hospitalName: '', hospitalAddress: '', admissionDate: '', dischargeDate: '',
        doctorName: '', diagnosis: '', treatment: '', surgeryPerformed: false,
        // Life optional fields
        deceasedName: '', deceasedDob: '', dateOfDeath: '', causeOfDeath: '',
        nomineeName: '', nomineeRelationship: 'Spouse', nomineeContact: '', bankDetails: '',
        policyStartDate: '',
        // Property optional fields
        propertyAddress: '', propertyIncidentType: 'Fire',
        locationOfDamage: '', fireDeptInvolved: false, reportNumber: '',
    });

    const [isSubmitting, setIsSubmitting] = useState(false);
    const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({});
    const [notificationsEnabled, setNotificationsEnabled] = useState(true);

    // Document viewer state for policy details
    const [zoom, setZoom] = useState(1);
    const documentRef = useRef<HTMLDivElement>(null);



    // Load initial data
    useEffect(() => {
        const loadData = async () => {
            try {
                const [policiesData, claimsData, userData] = await Promise.all([
                    fetchPolicies(),
                    fetchClaims(),
                    getCurrentUser()
                ]);
                setPolicies(policiesData.filter((p: Policy) => p.title !== 'Global Health Shield'));
                setUserClaims(claimsData);
                if (userData.notificationsEnabled !== undefined) {
                    setNotificationsEnabled(userData.notificationsEnabled);
                }
            } catch (error) {
                console.error("Failed to load dashboard data:", error);
                setToast({ msg: "Failed to load dashboard data", type: "error" });
            }
        };
        loadData();
    }, []);

    // Get the most recent active claim or first claim
    const activeClaim = userClaims.length > 0 ? userClaims[0] : null;

    const handleBuyPolicy = async (plan: any) => {
        setIsSubmitting(true);
        try {
            await createPolicy({
                category: plan.category,
                title: plan.title,
                coverage_amount: plan.coverage_amount,
                premium: plan.premium,
                features: plan.features,
                status: 'Active'
            });

            const [policiesData] = await Promise.all([
                fetchPolicies()
            ]);
            setPolicies(policiesData.filter((p: Policy) => p.title !== 'Global Health Shield'));
            setToast({ msg: `Successfully registered for ${plan.title}!`, type: "success" });
        } catch (error: any) {
            console.error("Failed to buy policy:", error);
            setToast({ msg: "Failed to register policy", type: "error" });
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleNewClaimClick = (e: React.MouseEvent, policy: Policy) => {
        e.stopPropagation();
        setClaimingPolicy(policy);
        setWizardStep('info');
        setFormData({
            incidentDate: new Date().toISOString().split('T')[0],
            incidentTime: '12:00',
            location: '',
            description: '',
            uploadedDocs: {},
            items: [{ item: '', cost: 0 }],
            makeModel: '', regNumber: '', vin: '', odometer: '',
            vehicleIncidentType: 'Collision', policeReportFiled: false, policeReportNo: '',
            dob: '', patientName: '', relationship: 'Self',
            hospitalName: '', hospitalAddress: '', admissionDate: '', dischargeDate: '',
            doctorName: '', diagnosis: '', treatment: '', surgeryPerformed: false,
            deceasedName: '', deceasedDob: '', dateOfDeath: '', causeOfDeath: '',
            nomineeName: '', nomineeRelationship: 'Spouse', nomineeContact: '', bankDetails: '',
            policyStartDate: '',
            propertyAddress: '', propertyIncidentType: 'Fire',
            locationOfDamage: '', fireDeptInvolved: false, reportNumber: '',
        });
    };

    const addItem = () => setFormData({ ...formData, items: [...formData.items, { item: '', cost: 0 }] });
    const removeItem = (index: number) => setFormData({ ...formData, items: formData.items.filter((_: any, i: number) => i !== index) });
    const updateItem = (index: number, field: string, value: any) => {
        const newItems = [...formData.items];
        newItems[index] = { ...newItems[index], [field]: value };
        setFormData({ ...formData, items: newItems });
    };

    const setDocumentFile = (docName: string, file: File | null) => {
        setFormData({
            ...formData,
            uploadedDocs: { ...formData.uploadedDocs, [docName]: file }
        });
    };

    const isDocsComplete = useMemo(() => {
        if (!claimingPolicy) return false;
        const required = MANDATORY_DOCS[claimingPolicy.category];
        return required.every(doc => !!formData.uploadedDocs[doc]);
    }, [claimingPolicy, formData.uploadedDocs]);

    const calculateTotal = useMemo(() => {
        return formData.items.reduce((sum: number, item: any) => sum + (Number(item.cost) || 0), 0);
    }, [formData.items]);

    const handleFinalSubmit = async () => {
        if (!claimingPolicy) return;
        setIsSubmitting(true);

        try {
            // Prepare claim payload with polymorphic data
            const claimPayload: any = {
                policy_number: claimingPolicy.policyNumber,
                claimant_name: CURRENT_USER.name,
                type: claimingPolicy.category,
                amount: calculateTotal,
                description: formData.description,
            };

            // Add itemized loss breakdown
            if (formData.items && formData.items.length > 0 && formData.items.some((i: any) => i.item)) {
                claimPayload.itemized_loss = formData.items
                    .filter((i: any) => i.item)
                    .map((i: any) => ({ item: i.item, cost: Number(i.cost) || 0 }));
            }

            // Map form data into category-specific polymorphic fields
            const cat = claimingPolicy.category;
            if (cat === 'Vehicle') {
                claimPayload.vehicle_info = {
                    makeModel: formData.makeModel || undefined,
                    regNumber: formData.regNumber || undefined,
                    vin: formData.vin || undefined,
                    odometer: formData.odometer || undefined,
                    policeReportFiled: formData.policeReportFiled,
                    policeReportNo: formData.policeReportNo || undefined,
                    location: formData.location || undefined,
                    time: formData.incidentTime || undefined,
                    incidentType: formData.vehicleIncidentType || 'Collision',
                };
            } else if (cat === 'Health') {
                claimPayload.health_info = {
                    dob: formData.dob || undefined,
                    patientName: formData.patientName || CURRENT_USER.name,
                    relationship: formData.relationship || 'Self',
                    hospitalName: formData.hospitalName || undefined,
                    hospitalAddress: formData.hospitalAddress || undefined,
                    admissionDate: formData.admissionDate || formData.incidentDate || undefined,
                    dischargeDate: formData.dischargeDate || undefined,
                    doctorName: formData.doctorName || undefined,
                    diagnosis: formData.diagnosis || undefined,
                    treatment: formData.treatment || undefined,
                    surgeryPerformed: formData.surgeryPerformed,
                };
            } else if (cat === 'Life') {
                claimPayload.life_info = {
                    deceasedName: formData.deceasedName || undefined,
                    deceasedDob: formData.deceasedDob || undefined,
                    dateOfDeath: formData.dateOfDeath || formData.incidentDate || undefined,
                    causeOfDeath: formData.causeOfDeath || undefined,
                    nomineeName: formData.nomineeName || CURRENT_USER.name,
                    nomineeRelationship: formData.nomineeRelationship || 'Spouse',
                    nomineeContact: formData.nomineeContact || undefined,
                    bankDetails: formData.bankDetails || undefined,
                    sumAssured: calculateTotal,
                    policyStartDate: formData.policyStartDate || undefined,
                };
            } else if (cat === 'Property') {
                claimPayload.property_info = {
                    address: formData.propertyAddress || formData.location || undefined,
                    incidentType: formData.propertyIncidentType || 'Fire',
                    locationOfDamage: formData.locationOfDamage || formData.location || undefined,
                    fireDeptInvolved: formData.fireDeptInvolved,
                    reportNumber: formData.reportNumber || undefined,
                };
            }

            console.log('Submitting claim:', claimPayload);
            const newClaim = await createClaim(claimPayload);
            console.log('Claim created successfully:', newClaim);

            // Upload Documents
            if (newClaim && newClaim.id) {
                const uploadPromises = Object.entries(formData.uploadedDocs).map(async ([docType, file]) => {
                    if (file) {
                        try {
                            console.log(`Uploading ${docType}...`);
                            await uploadDocument(newClaim.id, file as File, docType);
                            console.log(`Uploaded ${docType}`);
                        } catch (uploadError) {
                            console.error(`Failed to upload ${docType}:`, uploadError);
                            throw uploadError; // Will be caught by outer catch
                        }
                    }
                });

                if (uploadPromises.length > 0) {
                    await Promise.all(uploadPromises);
                    console.log('All documents uploaded successfully');
                }

                // Always finalize claim to trigger fraud detection (with or without documents)
                try {
                    console.log('Finalizing claim and triggering fraud detection...');
                    await finalizeClaim(newClaim.id);
                    console.log('Claim finalized, fraud detection started');
                } catch (finalizeError) {
                    console.warn('Failed to finalize claim:', finalizeError);
                    // Don't fail the whole process if finalization fails
                }
            }

            // Close the modal and show success message first
            setClaimingPolicy(null);
            setWizardStep('info');
            setToast({ msg: "Claim submitted successfully with documents!", type: "success" });

            // Try to refresh claims list, but don't let it break the success flow
            try {
                const updatedClaims = await fetchClaims();
                setUserClaims(updatedClaims);
            } catch (refreshError) {
                console.warn('Failed to refresh claims list, but claim was created successfully:', refreshError);
                // Optionally add the new claim to the list manually
                if (newClaim) {
                    setUserClaims(prev => [newClaim, ...prev]);
                }
            }
        } catch (error: any) {
            console.error("Submit claim failed:", error);
            console.error("Error details:", error.response?.data);
            const errorMessage = error.response?.data?.detail || error.message || "Failed to submit claim";
            setToast({ msg: errorMessage, type: "error" });
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="relative min-h-screen overflow-x-hidden">
            {/* 3D Component Background - Integrated for premium visual feel */}
            <div className="absolute inset-0 z-0 opacity-20 dark:opacity-40 pointer-events-none">
                <ThreeScene />
            </div>

            <div className="relative z-10 p-8 pb-32 max-w-[1600px] mx-auto">
                {/* Header */}
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex justify-between items-end mb-10">
                    <div>
                        <h1 className="text-4xl font-bold text-gray-900 dark:text-white tracking-tight mb-2">User Portal</h1>
                        <p className="text-gray-500 font-medium">Policy management for {CURRENT_USER.name}</p>
                    </div>
                </motion.div>

                <div className="space-y-6">


                    {/* My Claims Section - Show all claims grouped by category */}
                    {userClaims.length > 0 && (
                        <div className="pt-2">
                            <div className="flex items-center justify-between mb-6">
                                <div className="flex items-center gap-3">
                                    <div className="w-1.5 h-6 bg-[#2563EB] rounded-full" />
                                    <h2 className="text-xl font-bold text-gray-900 dark:text-white">My Claims</h2>
                                </div>
                                <Badge variant="info">{userClaims.length} {userClaims.length === 1 ? 'Claim' : 'Claims'}</Badge>
                            </div>

                            {/* Group claims by category */}
                            {(() => {
                                const claimsByPolicy = userClaims.reduce((acc, claim) => {
                                    const policy = policies.find(p => p.policyNumber === claim.policyNumber);
                                    const groupName = policy ? policy.title : (claim.type ? `${claim.type} Claims` : 'Other Claims');
                                    if (!acc[groupName]) acc[groupName] = [];
                                    acc[groupName].push(claim);
                                    return acc;
                                }, {} as Record<string, any[]>);

                                const categoryIcons: Record<string, any> = {
                                    'Health': Stethoscope,
                                    'Life': Heart,
                                    'Vehicle': Car,
                                    'Property': Home,
                                    'Other': FileText
                                };

                                const categoryColors: Record<string, string> = {
                                    'Health': 'text-red-600 bg-red-100',
                                    'Life': 'text-purple-600 bg-purple-100',
                                    'Vehicle': 'text-blue-600 bg-blue-100',
                                    'Property': 'text-green-600 bg-green-100',
                                    'Other': 'text-gray-600 bg-gray-100'
                                };

                                // Toggle category expansion
                                const toggleCategory = (groupName: string) => {
                                    setExpandedCategories(prev => ({
                                        ...prev,
                                        [groupName]: !prev[groupName]
                                    }));
                                };

                                return Object.entries(claimsByPolicy).map(([groupName, claims]) => {
                                    const firstClaim = claims[0];
                                    const category = firstClaim.type || 'Other';
                                    const Icon = categoryIcons[category] || FileText;
                                    const colorClass = categoryColors[category] || 'text-gray-600 bg-gray-100';
                                    const isExpanded = expandedCategories[groupName] !== false; // Default to expanded

                                    return (
                                        <div key={groupName} className="mb-6">
                                            <div
                                                className="flex items-center gap-2 mb-3 cursor-pointer hover:opacity-80 transition-opacity"
                                                onClick={() => toggleCategory(groupName)}
                                            >
                                                <div className={cn("p-1.5 rounded-lg", colorClass)}>
                                                    <Icon size={16} />
                                                </div>
                                                <h3 className="text-sm font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wider flex-1">
                                                    {groupName}
                                                </h3>
                                                <Badge variant="default" className="text-xs">{claims.length}</Badge>
                                                <motion.div
                                                    animate={{ rotate: isExpanded ? 180 : 0 }}
                                                    transition={{ duration: 0.2 }}
                                                >
                                                    <ChevronRight size={18} className="text-gray-400" />
                                                </motion.div>
                                            </div>
                                            <AnimatePresence>
                                                {isExpanded && (
                                                    <motion.div
                                                        initial={{ height: 0, opacity: 0 }}
                                                        animate={{ height: "auto", opacity: 1 }}
                                                        exit={{ height: 0, opacity: 0 }}
                                                        transition={{ duration: 0.3, ease: "easeInOut" }}
                                                        className="overflow-hidden"
                                                    >
                                                        <div className="grid grid-cols-1 gap-4">
                                                            {claims.map((claim) => (
                                                                <Card key={claim.id} className="relative overflow-hidden p-5 border-gray-200 dark:border-gray-700 shadow-lg bg-white/95 dark:bg-white/5 backdrop-blur-3xl hover:shadow-xl transition-shadow">
                                                                    <ClaimTracker claim={claim} />
                                                                </Card>
                                                            ))}
                                                        </div>
                                                    </motion.div>
                                                )}
                                            </AnimatePresence>
                                        </div>
                                    );
                                });
                            })()}
                        </div>
                    )}


                    <div className="pt-2">
                        <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center gap-3">
                                <div className="w-1.5 h-6 bg-[#2563EB] rounded-full" />
                                <h2 className="text-xl font-bold text-gray-900 dark:text-white">Active Policies</h2>
                            </div>
                        </div>

                        {showMarketplace ? (
                            <div className="space-y-6">
                                <div className="p-6 bg-blue-50/50 dark:bg-blue-900/10 rounded-2xl border border-blue-100 dark:border-blue-500/20 text-center mb-8 relative">
                                    <Button variant="secondary" onClick={() => setShowMarketplace(false)} className="absolute top-6 right-6">Back to Dashboard</Button>
                                    <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">Welcome to Vantage!</h3>
                                    <p className="text-gray-600 dark:text-gray-300">{policies.length === 0 ? "You don't have any active policies yet. Choose a plan below to get started instantly." : "Explore our premium insurance plans tailored for your needs."}</p>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                                    {OFFERED_POLICIES.map((plan, idx) => (
                                        <Card key={idx} className="flex flex-col h-full border-dashed border-2 hover:border-solid hover:border-blue-500 transition-all group">
                                            <div className="p-6 flex-1">
                                                <Badge variant="info" className="mb-4">{plan.category}</Badge>
                                                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">{plan.title}</h3>
                                                <p className="text-3xl font-black text-gray-900 dark:text-white mb-4">₹{plan.premium}<span className="text-sm font-medium text-gray-400">/mo</span></p>
                                                <div className="space-y-2 mb-6">
                                                    <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">Includes</p>
                                                    {plan.features.map(f => (
                                                        <div key={f} className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
                                                            <CheckCircle size={14} className="text-green-500" /> {f}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                            <div className="p-4 pt-0">
                                                <Button
                                                    onClick={() => handleBuyPolicy(plan)}
                                                    disabled={isSubmitting}
                                                    className="w-full bg-gray-900 dark:bg-white text-white dark:text-gray-900 hover:scale-[1.02] active:scale-95 transition-transform"
                                                >
                                                    {isSubmitting ? <Loader2 className="animate-spin" /> : 'Get Covered Now'}
                                                </Button>
                                            </div>
                                        </Card>
                                    ))}
                                </div>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                                {policies.map((policy) => {
                                    // Find any active claim for this policy (not Paid or Rejected)
                                    // Actually, let's show status even if Rejected/Paid?
                                    // The user said "should not allow any other claim".
                                    // If Paid/Rejected, maybe they can file new one?
                                    // For now, let's block only active ones: New, In Review, Flagged, Approved.
                                    // Status.Approved means "Approved for Settlement", not yet Paid.
                                    // If 'Paid', cycle is done. 'Rejected', cycle done.
                                    const activeClaim = userClaims.find(c => c.policyNumber === policy.policyNumber && c.status !== Status.Paid && c.status !== Status.Rejected);

                                    return (
                                        <PolicyCard
                                            key={policy.id}
                                            policy={policy}
                                            activeClaim={activeClaim}
                                            onViewPolicy={() => setSelectedPolicy(policy)}
                                            onNewClaim={(e) => handleNewClaimClick(e, policy)}
                                        />
                                    );
                                })}
                                <Card onClick={() => setShowMarketplace(true)} className="flex flex-col items-center justify-center p-6 border-dashed border-2 cursor-pointer hover:border-blue-500 hover:bg-blue-50/50 transition-all min-h-[300px] group">
                                    <div className="w-16 h-16 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform"><Plus size={32} /></div>
                                    <h3 className="text-xl font-bold text-gray-900 dark:text-gray-200">Add New Policy</h3>
                                    <p className="text-sm text-gray-500 mt-2 text-center">Explore comprehensive plans for Health, Life, Vehicle, and Property.</p>
                                </Card>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {toast && (notificationsEnabled || toast.type === 'error') && (
                <div className="fixed top-24 left-1/2 -translate-x-1/2 z-[100]">
                    <Toast message={toast.msg} type={toast.type} onClose={() => setToast(null)} />
                </div>
            )}
            <AnimatePresence>
                {selectedPolicy && (
                    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
                        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setSelectedPolicy(null)} className="absolute inset-0 bg-black/60 backdrop-blur-md" />
                        <motion.div layoutId={`policy-${selectedPolicy.id}`} className="relative w-full max-w-lg bg-white dark:bg-[#1C1C1E] rounded-[32px] overflow-hidden shadow-2xl">
                            <div className="p-8 border-b border-gray-100 dark:border-white/5 flex justify-between items-start bg-gray-50 dark:bg-white/5">
                                <div>
                                    <Badge variant="default" className="mb-2">{selectedPolicy.category}</Badge>
                                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{selectedPolicy.title}</h2>
                                </div>
                                <button onClick={() => setSelectedPolicy(null)} className="p-2 text-gray-400 hover:text-gray-900"><X size={20} /></button>
                            </div>
                            <div className="p-8 space-y-6">
                                <div className="grid grid-cols-2 gap-6">
                                    <div><p className="text-[10px] uppercase font-bold text-gray-400">Monthly Premium</p><p className="text-lg font-bold">₹{selectedPolicy.premium}</p></div>
                                    <div><p className="text-[10px] uppercase font-bold text-gray-400">Total Coverage</p><p className="text-lg font-bold text-green-600">₹{selectedPolicy.coverageAmount.toLocaleString()}</p></div>
                                </div>
                                <div className="space-y-3">
                                    <p className="text-[10px] uppercase font-bold text-gray-400">Policy Features</p>
                                    <div className="flex flex-wrap gap-2">
                                        {selectedPolicy.features.map(f => <Badge key={f} variant="info" className="lowercase">{f}</Badge>)}
                                    </div>
                                </div>
                                <Button variant="secondary" className="w-full h-12 rounded-2xl" onClick={() => setSelectedPolicy(null)}>Close</Button>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>

            <Modal
                isOpen={!!claimingPolicy}
                onClose={() => setClaimingPolicy(null)}
                title={wizardStep === 'preview' ? 'Claim Document Preview' : `New ${claimingPolicy?.category} Claim`}
                size={wizardStep === 'preview' ? 'lg' : 'md'}
            >
                <div className="flex flex-col gap-6">
                    <div className="flex items-center justify-center gap-3 mb-4">
                        {['info', 'details', 'documents', 'breakdown', 'preview'].map((step) => (
                            <div key={step} className={cn("w-2 h-2 rounded-full transition-all duration-300", wizardStep === step ? "bg-blue-600 scale-125" : "bg-gray-200")} />
                        ))}
                    </div>

                    {wizardStep === 'info' && (
                        <div className="space-y-6 animate-in fade-in duration-300">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-1">
                                    <FormLabel icon={Calendar}>Incident Date</FormLabel>
                                    <Input type="date" value={formData.incidentDate} onChange={(e) => setFormData({ ...formData, incidentDate: e.target.value })} />
                                </div>
                                <div className="space-y-1">
                                    <FormLabel icon={Clock}>Time</FormLabel>
                                    <Input type="time" value={formData.incidentTime} onChange={(e) => setFormData({ ...formData, incidentTime: e.target.value })} />
                                </div>
                            </div>
                            <div className="space-y-1">
                                <FormLabel icon={MapPin}>Location</FormLabel>
                                <Input placeholder="Location details" value={formData.location} onChange={(e) => setFormData({ ...formData, location: e.target.value })} />
                            </div>
                            <div className="space-y-1">
                                <FormLabel icon={FileText}>Loss Description</FormLabel>
                                <TextArea placeholder="Explain the incident..." className="h-24" value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} />
                            </div>
                            <div className="flex justify-end gap-3 pt-4 border-t border-gray-100 dark:border-white/5">
                                <Button variant="secondary" onClick={() => setClaimingPolicy(null)}>Cancel</Button>
                                <Button onClick={() => setWizardStep('details')} className="px-8">{claimingPolicy?.category} Details <ChevronRight size={16} /></Button>
                            </div>
                        </div>
                    )}

                    {wizardStep === 'details' && (
                        <div className="space-y-6 animate-in fade-in duration-300">
                            <div className="flex items-center gap-2 mb-2">
                                <div className="w-1 h-4 bg-blue-500 rounded-full" />
                                <p className="text-[10px] font-black uppercase tracking-widest text-gray-400">
                                    {claimingPolicy?.category} Details <span className="text-gray-300 font-medium normal-case">(All fields optional — fill what you can)</span>
                                </p>
                            </div>

                            {claimingPolicy?.category === 'Vehicle' && (
                                <div className="space-y-4 bg-blue-50/30 dark:bg-blue-900/10 p-4 rounded-2xl border border-blue-100 dark:border-blue-500/10">
                                    <div className="grid grid-cols-2 gap-3">
                                        <div className="space-y-1">
                                            <FormLabel icon={Car}>Make & Model</FormLabel>
                                            <Input placeholder="e.g. Honda City 2024" value={formData.makeModel} onChange={(e) => setFormData({ ...formData, makeModel: e.target.value })} />
                                        </div>
                                        <div className="space-y-1">
                                            <FormLabel icon={Hash}>Registration No.</FormLabel>
                                            <Input placeholder="e.g. MH-01-AB-1234" value={formData.regNumber} onChange={(e) => setFormData({ ...formData, regNumber: e.target.value })} />
                                        </div>
                                        <div className="space-y-1">
                                            <FormLabel icon={Hash}>VIN</FormLabel>
                                            <Input placeholder="Vehicle Identification Number" value={formData.vin} onChange={(e) => setFormData({ ...formData, vin: e.target.value })} />
                                        </div>
                                        <div className="space-y-1">
                                            <FormLabel icon={Activity}>Odometer (km)</FormLabel>
                                            <Input type="number" placeholder="e.g. 45000" value={formData.odometer} onChange={(e) => setFormData({ ...formData, odometer: e.target.value })} />
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-2 gap-3">
                                        <div className="space-y-1">
                                            <FormLabel icon={AlertTriangle}>Incident Type</FormLabel>
                                            <Select value={formData.vehicleIncidentType} onChange={(e) => setFormData({ ...formData, vehicleIncidentType: e.target.value })}>
                                                <option value="Collision">Collision</option>
                                                <option value="Theft">Theft</option>
                                                <option value="Vandalism">Vandalism</option>
                                                <option value="Natural Disaster">Natural Disaster</option>
                                                <option value="Hit and Run">Hit and Run</option>
                                                <option value="Other">Other</option>
                                            </Select>
                                        </div>
                                        <div className="space-y-1">
                                            <FormLabel icon={FileText}>Police Report No.</FormLabel>
                                            <Input placeholder="If filed" value={formData.policeReportNo} onChange={(e) => setFormData({ ...formData, policeReportNo: e.target.value })} />
                                        </div>
                                    </div>
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input type="checkbox" checked={formData.policeReportFiled} onChange={(e) => setFormData({ ...formData, policeReportFiled: e.target.checked })} className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                                        <span className="text-xs text-gray-600 dark:text-gray-400">Police report has been filed</span>
                                    </label>
                                </div>
                            )}

                            {claimingPolicy?.category === 'Health' && (
                                <div className="space-y-4 bg-red-50/30 dark:bg-red-900/10 p-4 rounded-2xl border border-red-100 dark:border-red-500/10">
                                    <div className="grid grid-cols-2 gap-3">
                                        <div className="space-y-1">
                                            <FormLabel icon={UserIcon}>Patient Name</FormLabel>
                                            <Input placeholder="Patient full name" value={formData.patientName} onChange={(e) => setFormData({ ...formData, patientName: e.target.value })} />
                                        </div>
                                        <div className="space-y-1">
                                            <FormLabel icon={UserIcon}>Relationship</FormLabel>
                                            <Select value={formData.relationship} onChange={(e) => setFormData({ ...formData, relationship: e.target.value })}>
                                                <option value="Self">Self</option>
                                                <option value="Spouse">Spouse</option>
                                                <option value="Child">Child</option>
                                                <option value="Parent">Parent</option>
                                                <option value="Sibling">Sibling</option>
                                                <option value="Other">Other</option>
                                            </Select>
                                        </div>
                                        <div className="space-y-1">
                                            <FormLabel icon={Calendar}>Date of Birth</FormLabel>
                                            <Input type="date" value={formData.dob} onChange={(e) => setFormData({ ...formData, dob: e.target.value })} />
                                        </div>
                                        <div className="space-y-1">
                                            <FormLabel icon={Building2}>Hospital Name</FormLabel>
                                            <Input placeholder="Hospital name" value={formData.hospitalName} onChange={(e) => setFormData({ ...formData, hospitalName: e.target.value })} />
                                        </div>
                                    </div>
                                    <div className="space-y-1">
                                        <FormLabel icon={MapPin}>Hospital Address</FormLabel>
                                        <Input placeholder="Hospital address" value={formData.hospitalAddress} onChange={(e) => setFormData({ ...formData, hospitalAddress: e.target.value })} />
                                    </div>
                                    <div className="grid grid-cols-2 gap-3">
                                        <div className="space-y-1">
                                            <FormLabel icon={Calendar}>Admission Date</FormLabel>
                                            <Input type="date" value={formData.admissionDate} onChange={(e) => setFormData({ ...formData, admissionDate: e.target.value })} />
                                        </div>
                                        <div className="space-y-1">
                                            <FormLabel icon={Calendar}>Discharge Date</FormLabel>
                                            <Input type="date" value={formData.dischargeDate} onChange={(e) => setFormData({ ...formData, dischargeDate: e.target.value })} />
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-2 gap-3">
                                        <div className="space-y-1">
                                            <FormLabel icon={UserIcon}>Doctor Name</FormLabel>
                                            <Input placeholder="Attending doctor" value={formData.doctorName} onChange={(e) => setFormData({ ...formData, doctorName: e.target.value })} />
                                        </div>
                                        <div className="space-y-1">
                                            <FormLabel icon={Stethoscope}>Diagnosis</FormLabel>
                                            <Input placeholder="Primary diagnosis" value={formData.diagnosis} onChange={(e) => setFormData({ ...formData, diagnosis: e.target.value })} />
                                        </div>
                                    </div>
                                    <div className="space-y-1">
                                        <FormLabel icon={ClipboardCheck}>Treatment Provided</FormLabel>
                                        <Input placeholder="Treatment details" value={formData.treatment} onChange={(e) => setFormData({ ...formData, treatment: e.target.value })} />
                                    </div>
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input type="checkbox" checked={formData.surgeryPerformed} onChange={(e) => setFormData({ ...formData, surgeryPerformed: e.target.checked })} className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                                        <span className="text-xs text-gray-600 dark:text-gray-400">Surgery was performed</span>
                                    </label>
                                </div>
                            )}

                            {claimingPolicy?.category === 'Life' && (
                                <div className="space-y-4 bg-purple-50/30 dark:bg-purple-900/10 p-4 rounded-2xl border border-purple-100 dark:border-purple-500/10">
                                    <div className="grid grid-cols-2 gap-3">
                                        <div className="space-y-1">
                                            <FormLabel icon={UserIcon}>Deceased Name</FormLabel>
                                            <Input placeholder="Full name" value={formData.deceasedName} onChange={(e) => setFormData({ ...formData, deceasedName: e.target.value })} />
                                        </div>
                                        <div className="space-y-1">
                                            <FormLabel icon={Calendar}>Deceased DOB</FormLabel>
                                            <Input type="date" value={formData.deceasedDob} onChange={(e) => setFormData({ ...formData, deceasedDob: e.target.value })} />
                                        </div>
                                        <div className="space-y-1">
                                            <FormLabel icon={Calendar}>Date of Death</FormLabel>
                                            <Input type="date" value={formData.dateOfDeath} onChange={(e) => setFormData({ ...formData, dateOfDeath: e.target.value })} />
                                        </div>
                                        <div className="space-y-1">
                                            <FormLabel icon={FileText}>Cause of Death</FormLabel>
                                            <Input placeholder="Cause of death" value={formData.causeOfDeath} onChange={(e) => setFormData({ ...formData, causeOfDeath: e.target.value })} />
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-2 gap-3">
                                        <div className="space-y-1">
                                            <FormLabel icon={UserIcon}>Nominee Name</FormLabel>
                                            <Input placeholder="Nominee full name" value={formData.nomineeName} onChange={(e) => setFormData({ ...formData, nomineeName: e.target.value })} />
                                        </div>
                                        <div className="space-y-1">
                                            <FormLabel icon={UserIcon}>Nominee Relationship</FormLabel>
                                            <Select value={formData.nomineeRelationship} onChange={(e) => setFormData({ ...formData, nomineeRelationship: e.target.value })}>
                                                <option value="Spouse">Spouse</option>
                                                <option value="Child">Child</option>
                                                <option value="Parent">Parent</option>
                                                <option value="Sibling">Sibling</option>
                                                <option value="Other">Other</option>
                                            </Select>
                                        </div>
                                        <div className="space-y-1">
                                            <FormLabel icon={Phone}>Nominee Contact</FormLabel>
                                            <Input placeholder="Phone number" value={formData.nomineeContact} onChange={(e) => setFormData({ ...formData, nomineeContact: e.target.value })} />
                                        </div>
                                        <div className="space-y-1">
                                            <FormLabel icon={Hash}>Bank Account Details</FormLabel>
                                            <Input placeholder="Account number / IFSC" value={formData.bankDetails} onChange={(e) => setFormData({ ...formData, bankDetails: e.target.value })} />
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-1 gap-3">
                                        <div className="space-y-1">
                                            <FormLabel icon={Calendar}>Policy Start Date</FormLabel>
                                            <Input type="date" value={formData.policyStartDate} onChange={(e) => setFormData({ ...formData, policyStartDate: e.target.value })} />
                                        </div>
                                    </div>
                                </div>
                            )}

                            {claimingPolicy?.category === 'Property' && (
                                <div className="space-y-4 bg-green-50/30 dark:bg-green-900/10 p-4 rounded-2xl border border-green-100 dark:border-green-500/10">
                                    <div className="space-y-1">
                                        <FormLabel icon={Home}>Property Address</FormLabel>
                                        <Input placeholder="Insured property address" value={formData.propertyAddress} onChange={(e) => setFormData({ ...formData, propertyAddress: e.target.value })} />
                                    </div>
                                    <div className="grid grid-cols-2 gap-3">
                                        <div className="space-y-1">
                                            <FormLabel icon={AlertTriangle}>Incident Type</FormLabel>
                                            <Select value={formData.propertyIncidentType} onChange={(e) => setFormData({ ...formData, propertyIncidentType: e.target.value })}>
                                                <option value="Fire">Fire</option>
                                                <option value="Flood">Flood</option>
                                                <option value="Theft">Theft / Burglary</option>
                                                <option value="Storm">Storm / Wind</option>
                                                <option value="Vandalism">Vandalism</option>
                                                <option value="Earthquake">Earthquake</option>
                                                <option value="Other">Other</option>
                                            </Select>
                                        </div>
                                        <div className="space-y-1">
                                            <FormLabel icon={MapPin}>Location of Damage</FormLabel>
                                            <Input placeholder="e.g. Kitchen, Roof" value={formData.locationOfDamage} onChange={(e) => setFormData({ ...formData, locationOfDamage: e.target.value })} />
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-2 gap-3">
                                        <div className="space-y-1">
                                            <FormLabel icon={FileText}>Report Number</FormLabel>
                                            <Input placeholder="Fire/Police report no." value={formData.reportNumber} onChange={(e) => setFormData({ ...formData, reportNumber: e.target.value })} />
                                        </div>
                                    </div>
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input type="checkbox" checked={formData.fireDeptInvolved} onChange={(e) => setFormData({ ...formData, fireDeptInvolved: e.target.checked })} className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                                        <span className="text-xs text-gray-600 dark:text-gray-400">Fire department was involved</span>
                                    </label>
                                </div>
                            )}

                            <div className="flex justify-between gap-3 pt-4 border-t border-gray-100 dark:border-white/5">
                                <Button variant="secondary" onClick={() => setWizardStep('info')}>Back</Button>
                                <Button onClick={() => setWizardStep('documents')} className="px-8">Documents <ChevronRight size={16} /></Button>
                            </div>
                        </div>
                    )}

                    {wizardStep === 'documents' && (
                        <div className="space-y-6 animate-in fade-in duration-300">
                            <div className="bg-blue-50/50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-500/20 p-4 rounded-2xl flex items-center gap-3">
                                <AlertCircle size={20} className="text-blue-600 shrink-0" />
                                <p className="text-xs text-blue-700 dark:text-blue-300 font-medium">All mandatory documents are required to proceed.</p>
                            </div>
                            <div className="space-y-3">
                                {claimingPolicy && MANDATORY_DOCS[claimingPolicy.category].map((docName) => (
                                    <UploadSlot
                                        key={docName}
                                        label={docName}
                                        uploadedFile={formData.uploadedDocs[docName]}
                                        onFileSelect={(fileName) => setDocumentFile(docName, fileName)}
                                    />
                                ))}
                            </div>
                            <div className="flex justify-between gap-3 pt-4 border-t border-gray-100 dark:border-white/5">
                                <Button variant="secondary" onClick={() => setWizardStep('details')}>Back</Button>
                                <Button disabled={!isDocsComplete} onClick={() => setWizardStep('breakdown')} className="px-8">Next <ChevronRight size={16} /></Button>
                            </div>
                        </div>
                    )}

                    {wizardStep === 'breakdown' && (
                        <div className="space-y-6 animate-in fade-in duration-300">
                            <div className="p-4 bg-gray-50 dark:bg-black/20 rounded-2xl border border-gray-100 dark:border-white/5">
                                <h4 className="text-[10px] font-black uppercase text-gray-400 mb-4">Loss Items</h4>
                                <div className="space-y-3">
                                    {formData.items.map((item: any, idx: number) => (
                                        <div key={idx} className="flex gap-2">
                                            <Input placeholder="Item description" className="flex-1" value={item.item} onChange={(e) => updateItem(idx, 'item', e.target.value)} />
                                            <Input type="number" placeholder="₹0" className="w-24" value={item.cost} onChange={(e) => updateItem(idx, 'cost', e.target.value)} />
                                            <button onClick={() => removeItem(idx)} className="p-2 text-gray-400 hover:text-red-500"><Trash2 size={16} /></button>
                                        </div>
                                    ))}
                                    <Button variant="secondary" size="sm" onClick={addItem} className="w-full border-dashed rounded-xl mt-2"><Plus size={14} /> Add Item</Button>
                                </div>
                            </div>
                            <div className="flex justify-between items-center px-4 py-4 bg-gray-900 text-white rounded-2xl">
                                <span className="text-[10px] font-black uppercase text-gray-400">Total Claim</span>
                                <span className="text-2xl font-black">₹{calculateTotal.toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between gap-3 pt-4 border-t border-gray-100 dark:border-white/5">
                                <Button variant="secondary" onClick={() => setWizardStep('documents')}>Back</Button>
                                <Button onClick={() => setWizardStep('preview')} className="px-8 bg-blue-600 text-white border-0">Preview <Sparkles size={16} /></Button>
                            </div>
                        </div>
                    )}

                    {wizardStep === 'preview' && (
                        <div className="space-y-6 animate-in zoom-in-95 duration-500">
                            <div className="bg-white p-8 rounded-[32px] border-4 border-gray-50 shadow-inner max-h-[500px] overflow-y-auto custom-scrollbar">
                                <DocHeader title={`${claimingPolicy?.category} Claim Form`} claimNo="PENDING" date={new Date().toLocaleDateString()} status="DRAFT" icon={claimingPolicy?.category === 'Vehicle' ? Car : Heart} emoji="📁" />
                                <DocSection title="Policyholder Details" emoji="👤"><DocGrid items={[{ label: 'Full Name', value: CURRENT_USER.name }, { label: 'Policy Number', value: claimingPolicy?.policyNumber }]} /></DocSection>
                                <DocSection title="Incident Summary" emoji="📍"><DocGrid items={[{ label: 'Date', value: formData.incidentDate }, { label: 'Location', value: formData.location }]} /></DocSection>
                                <DocSection title="Description" emoji="📝"><p className="text-[11px] italic text-gray-600 bg-gray-50 p-3 rounded-lg">{formData.description || 'Not Provided'}</p></DocSection>
                                <DocSection title="Uploaded Files" emoji="📎"><div className="grid grid-cols-2 gap-2">{Object.keys(formData.uploadedDocs).map(d => <div key={d} className="p-2 bg-gray-50 rounded-lg text-[10px] flex items-center gap-1"><FileCheck size={12} className="text-emerald-500" /> {d}</div>)}</div></DocSection>
                                <div className="mt-8 border-t border-dashed pt-4 flex justify-between items-end"><div><p className="text-[8px] font-bold text-gray-400 uppercase">Signature</p><p className="text-xl font-serif text-gray-800" style={{ fontFamily: 'Dancing Script, cursive' }}>{CURRENT_USER.name}</p></div><p className="text-[10px] font-bold text-gray-900">{new Date().toLocaleDateString()}</p></div>
                            </div>
                            <div className="flex justify-end gap-3 pt-4 border-t border-gray-100 dark:border-white/5">
                                <Button variant="secondary" onClick={() => setWizardStep('breakdown')}>Edit</Button>
                                <Button isLoading={isSubmitting} onClick={handleFinalSubmit} className="bg-emerald-600 text-white border-0 px-10">Confirm & Submit <FileBadge size={16} /></Button>
                            </div>
                        </div>
                    )}
                </div>
            </Modal>

            {/* Policy Claims Document Viewer Modal */}
            <AnimatePresence>
                {selectedPolicy && (() => {
                    // Get all claims for this policy
                    const policyClaims = userClaims.filter(c => c.policyNumber === selectedPolicy.policyNumber);
                    const selectedClaim = policyClaims[0]; // Show first claim for now

                    if (!selectedClaim) return null;

                    return (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
                            onClick={() => setSelectedPolicy(null)}
                        >
                            <motion.div
                                initial={{ scale: 0.9, y: 20 }}
                                animate={{ scale: 1, y: 0 }}
                                exit={{ scale: 0.9, y: 20 }}
                                onClick={(e) => e.stopPropagation()}
                                className="bg-white dark:bg-gray-900 rounded-3xl shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-hidden flex flex-col"
                            >
                                {/* Header */}
                                <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
                                    <div className="flex items-center gap-4">
                                        <button
                                            onClick={() => setSelectedPolicy(null)}
                                            className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-full transition-colors"
                                        >
                                            <ChevronLeft size={24} className="text-gray-600 dark:text-gray-300" />
                                        </button>
                                        <div>
                                            <h2 className="text-xl font-bold text-gray-900 dark:text-white">Claim #{selectedClaim.id}</h2>
                                            <p className="text-sm text-gray-500">{selectedClaim.type} Insurance Claim</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={() => setZoom(prev => Math.max(prev - 0.1, 0.5))}
                                            className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
                                            title="Zoom Out"
                                        >
                                            <ZoomOut size={18} className="text-gray-600 dark:text-gray-300" />
                                        </button>
                                        <button
                                            onClick={() => setZoom(prev => Math.min(prev + 0.1, 2.0))}
                                            className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
                                            title="Zoom In"
                                        >
                                            <ZoomIn size={18} className="text-gray-600 dark:text-gray-300" />
                                        </button>
                                    </div>
                                </div>

                                {/* Document Content */}
                                <div className="flex-1 overflow-auto bg-gray-100 dark:bg-gray-950 p-8">
                                    <div
                                        ref={documentRef}
                                        className="bg-white rounded-2xl shadow-xl p-8 mx-auto max-w-4xl transition-transform origin-top"
                                        style={{ transform: `scale(${zoom})` }}
                                    >
                                        <DocHeader
                                            title={`${selectedClaim.type} Insurance Claim Form`}
                                            claimNo={selectedClaim.id}
                                            date={selectedClaim.date}
                                            status={selectedClaim.status}
                                            icon={selectedClaim.type === 'Vehicle' ? Car : selectedClaim.type === 'Health' ? Heart : selectedClaim.type === 'Life' ? Heart : Home}
                                            emoji={selectedClaim.type === 'Vehicle' ? '🚗' : selectedClaim.type === 'Health' ? '🏥' : selectedClaim.type === 'Life' ? '🧬' : '🏠'}
                                        />

                                        <DocSection title="Policyholder Information" emoji="👤">
                                            <DocGrid items={[
                                                { label: 'Full Name', value: selectedClaim.claimant },
                                                { label: 'Policy Number', value: selectedClaim.policyNumber },
                                                { label: 'Contact', value: selectedClaim.phoneNumber || 'Not Provided' },
                                                { label: 'Email', value: CURRENT_USER.email }
                                            ]} />
                                        </DocSection>

                                        <DocSection title="Claim Details" emoji="📋">
                                            <DocGrid items={[
                                                { label: 'Claim Amount', value: `$${selectedClaim.amount.toLocaleString()}` },
                                                { label: 'Submission Date', value: selectedClaim.date },
                                                { label: 'Status', value: selectedClaim.status },
                                                { label: 'Risk Level', value: selectedClaim.riskLevel }
                                            ]} />
                                        </DocSection>

                                        <DocSection title="Description" emoji="📝">
                                            <p className="text-sm text-gray-700 leading-relaxed italic bg-gray-50 p-4 rounded-xl border border-gray-100">
                                                {selectedClaim.description || 'No description provided'}
                                            </p>
                                        </DocSection>

                                        {selectedClaim.documents && selectedClaim.documents.length > 0 && (
                                            <DocSection title="Supporting Documents" emoji="📎">
                                                <div className="grid grid-cols-2 gap-2">
                                                    {selectedClaim.documents.map((doc, i) => (
                                                        <div key={i} className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg text-xs">
                                                            <FileCheck size={14} className="text-emerald-500" />
                                                            {doc.name}
                                                        </div>
                                                    ))}
                                                </div>
                                            </DocSection>
                                        )}

                                        <div className="mt-8 pt-6 border-t border-dashed border-gray-200 flex justify-between items-end">
                                            <div>
                                                <p className="text-xs font-bold text-gray-400 uppercase mb-1">Signature</p>
                                                <p className="text-2xl font-serif text-gray-800" style={{ fontFamily: 'Dancing Script, cursive' }}>
                                                    {selectedClaim.claimant}
                                                </p>
                                            </div>
                                            <div className="text-right">
                                                <p className="text-xs font-bold text-gray-400 uppercase mb-1">Date</p>
                                                <p className="text-sm font-bold text-gray-900">{selectedClaim.date}</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </motion.div>
                        </motion.div>
                    );
                })()}
            </AnimatePresence>
        </div>
    );
};
