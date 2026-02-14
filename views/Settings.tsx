import React, { useState } from 'react';
import { Card, Button, Modal, Badge, cn, Input, Toast } from '../components/UIComponents';
import { CURRENT_USER, MOCK_CLAIMS } from '../constants';
import { Status, User as UserType } from '../types';
import { getCurrentUser, updateUserProfile } from '../src/api/endpoints';
import {
    Bell,
    Shield,
    Moon,
    User,
    LogOut,
    ChevronRight,
    ToggleRight,
    ToggleLeft,
    History,
    FileText,
    ArrowLeft,
    AlertCircle,
    CheckCircle,
    XCircle,
    Clock,
    ShieldAlert,
    Smartphone,
    Mail,
    Phone,
    MapPin,
    QrCode,
    Lock
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Generate a consistent color based on the name string
const getAvatarColor = (name: string): string => {
    const colors = [
        'bg-gradient-to-br from-rose-500 to-pink-600',
        'bg-gradient-to-br from-orange-500 to-amber-600',
        'bg-gradient-to-br from-emerald-500 to-teal-600',
        'bg-gradient-to-br from-blue-500 to-indigo-600',
        'bg-gradient-to-br from-violet-500 to-purple-600',
        'bg-gradient-to-br from-cyan-500 to-sky-600',
        'bg-gradient-to-br from-fuchsia-500 to-pink-600',
        'bg-gradient-to-br from-lime-500 to-green-600',
    ];
    // Use character codes sum to pick a consistent color
    const charSum = name.split('').reduce((sum, char) => sum + char.charCodeAt(0), 0);
    return colors[charSum % colors.length];
};

const InitialAvatar = ({ name, size = 'lg' }: { name: string; size?: 'sm' | 'md' | 'lg' }) => {
    const initial = name?.charAt(0)?.toUpperCase() || '?';
    const bgColor = getAvatarColor(name || 'User');
    const sizeClasses = {
        sm: 'w-8 h-8 text-sm',
        md: 'w-12 h-12 text-lg',
        lg: 'w-24 h-24 text-4xl'
    };
    
    return (
        <div className={cn(
            sizeClasses[size],
            bgColor,
            'rounded-full flex items-center justify-center font-bold text-white shadow-2xl border-2 border-orange-500 p-1'
        )}>
            <span className="drop-shadow-md">{initial}</span>
        </div>
    );
};

const SettingRow = ({ icon: Icon, label, value, type = 'arrow', active = false, onClick }: any) => (
    <div className="flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer first:rounded-t-2xl last:rounded-b-2xl bg-white dark:bg-white/5 border-b border-gray-100 dark:border-white/5 last:border-0" onClick={onClick}>
        <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-gray-300">
                <Icon size={18} />
            </div>
            <span className="font-medium text-gray-900 dark:text-white">{label}</span>
        </div>
        <div className="flex items-center gap-2">
            {value && <span className="text-sm text-gray-500">{value}</span>}
            {type === 'arrow' && <ChevronRight size={16} className="text-gray-400" />}
            {type === 'toggle' && (
                <div className={cn("text-2xl transition-colors", active ? "text-[#34A853]" : "text-gray-300")}>
                    {active ? <ToggleRight size={32} /> : <ToggleLeft size={32} />}
                </div>
            )}
        </div>
    </div>
);

// --- New Activity List Component ---
const ActivityHistory = ({ onBack }: { onBack: () => void }) => {
    // Filter claims for the current logged-in user to show their specific history
    const userClaims = MOCK_CLAIMS.filter(c => c.claimant === CURRENT_USER.name);

    const isUser = CURRENT_USER.role === 'User';
    const accentColor = isUser ? 'text-[#2563EB]' : 'text-[#F97316]';
    const accentBg = isUser ? 'bg-blue-100 dark:bg-blue-900/20' : 'bg-orange-100 dark:bg-orange-900/20';

    return (
        <div className="space-y-6">
            <button onClick={onBack} className={cn("flex items-center gap-2 text-sm font-bold text-gray-500 hover:text-opacity-80 transition-colors mb-4", isUser ? "hover:text-blue-600" : "hover:text-orange-500")}>
                <ArrowLeft size={16} /> Back to Settings
            </button>

            <div className="flex items-center gap-3 mb-6">
                <div className={cn("p-3 rounded-2xl", accentBg, accentColor)}>
                    <History size={24} />
                </div>
                <div>
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Claim History</h2>
                    <p className="text-sm text-gray-500">Recent activity and claim decisions.</p>
                </div>
            </div>

            <div className="space-y-4">
                {userClaims.length === 0 ? (
                    <div className="text-center py-12 bg-gray-50 dark:bg-white/5 rounded-3xl border border-gray-100 dark:border-white/5 border-dashed">
                        <FileText size={48} className="mx-auto text-gray-300 mb-4" />
                        <p className="text-gray-500 font-medium">No activity history found.</p>
                    </div>
                ) : (
                    userClaims.map((claim) => (
                        <Card key={claim.id} className="p-5 flex items-center justify-between hover:shadow-lg transition-all border border-gray-100 dark:border-white/5">
                            <div className="flex items-center gap-4">
                                <div className={cn(
                                    "w-12 h-12 rounded-full flex items-center justify-center shrink-0",
                                    claim.status === Status.Approved ? "bg-emerald-100 text-emerald-600" :
                                        claim.status === Status.Rejected ? "bg-rose-100 text-rose-600" :
                                            claim.status === Status.Flagged ? "bg-amber-100 text-amber-600" :
                                                "bg-blue-100 text-blue-600"
                                )}>
                                    {claim.status === Status.Approved ? <CheckCircle size={20} /> :
                                        claim.status === Status.Rejected ? <XCircle size={20} /> :
                                            claim.status === Status.Flagged ? <AlertCircle size={20} /> :
                                                <Clock size={20} />}
                                </div>
                                <div>
                                    <div className="flex items-center gap-2">
                                        <h4 className="font-bold text-gray-900 dark:text-white">{claim.type} Claim</h4>
                                        <span className="text-xs font-mono text-gray-400">#{claim.id}</span>
                                    </div>
                                    <p className="text-xs text-gray-500 mt-0.5 line-clamp-1 max-w-[200px] md:max-w-md">{claim.description}</p>
                                    <p className="text-[10px] text-gray-400 mt-1">{claim.date}</p>
                                </div>
                            </div>
                            <div className="text-right">
                                <p className="font-bold text-gray-900 dark:text-white mb-1">₹{claim.amount.toLocaleString()}</p>
                                <Badge variant={
                                    claim.status === Status.Approved ? 'success' :
                                        claim.status === Status.Rejected ? 'danger' :
                                            claim.status === Status.Flagged ? 'warning' : 'info'
                                }>
                                    {claim.status}
                                </Badge>
                            </div>
                        </Card>
                    ))
                )}
            </div>
        </div>
    );
};

interface SettingsProps {
    onLogout?: () => void;
}

export const Settings = ({ onLogout }: SettingsProps) => {
    const [view, setView] = useState<'main' | 'history'>('main');
    const [notifications, setNotifications] = useState(true);
    const [currentUser, setCurrentUser] = useState<UserType | null>(null);

    // Fetch current user settings on mount
    React.useEffect(() => {
        const loadUser = async () => {
            try {
                const user = await getCurrentUser();
                setCurrentUser(user);
                setUserName(user.name);
                setUserRole(user.role);
                setPersonalInfo(prev => ({ ...prev, email: user.email }));
                if (user.notificationsEnabled !== undefined) {
                    setNotifications(user.notificationsEnabled);
                }
            } catch (error) {
                console.error("Failed to load user settings:", error);
            }
        };
        loadUser();
    }, []);

    const handleNotificationToggle = async () => {
        const newState = !notifications;
        setNotifications(newState); // Optimistic update
        try {
            await updateUserProfile({ notificationsEnabled: newState });
            setToast(newState ? "Notifications enabled" : "Notifications disabled");
        } catch (error) {
            console.error("Failed to update notification settings:", error);
            setNotifications(!newState); // Revert on error
            setToast("Failed to update settings");
        }
    };

    // Modals
    const [isProfileOpen, setIsProfileOpen] = useState(false);
    const [isPersonalDetailsOpen, setIsPersonalDetailsOpen] = useState(false);
    const [is2FAOpen, setIs2FAOpen] = useState(false);

    // Personal Details State
    const [personalInfo, setPersonalInfo] = useState({
        email: CURRENT_USER.email || (CURRENT_USER.role === 'Admin' ? 'alex.chen@vantage.ai' : 'james.doe@gmail.com'),
        phone: '+91 98765-43210',
        address: 'Sector 44, Gurgaon, Haryana, India'
    });

    // 2FA State
    const [is2FAEnabled, setIs2FAEnabled] = useState(false);
    const [show2FAQR, setShow2FAQR] = useState(false);

    const [userName, setUserName] = useState(CURRENT_USER.name);
    const [userRole, setUserRole] = useState(CURRENT_USER.role);
    const [fraudMode, setFraudMode] = useState<'Aggressive' | 'Balanced' | 'Conservative'>('Balanced');
    const [toast, setToast] = useState<string | null>(null);

    const isUser = CURRENT_USER.role === 'User';
    const accentColor = isUser ? 'text-[#2563EB]' : 'text-[#F97316]';
    const focusRing = isUser ? 'focus:ring-[#2563EB]' : 'focus:ring-[#F97316]';

    const handleSaveProfile = () => {
        CURRENT_USER.name = userName;
        CURRENT_USER.role = userRole;
        setIsProfileOpen(false);
        setToast("Profile display updated");
    };

    const handleSavePersonalDetails = () => {
        setIsPersonalDetailsOpen(false);
        setToast("Personal details saved successfully");
    };

    const handleEnable2FA = () => {
        setIs2FAEnabled(true);
        setShow2FAQR(false);
        setIs2FAOpen(false);
        setToast("Two-Factor Authentication Enabled");
    };

    if (view === 'history') {
        return (
            <div className="p-8 max-w-3xl mx-auto animate-in slide-in-from-right-8 duration-500">
                <ActivityHistory onBack={() => setView('main')} />
            </div>
        );
    }

    return (
        <div className="p-8 max-w-3xl mx-auto relative">
            <AnimatePresence>
                {toast && (
                    <div className="fixed top-24 left-1/2 -translate-x-1/2 z-[100]">
                        <Toast message={toast} onClose={() => setToast(null)} />
                    </div>
                )}
            </AnimatePresence>

            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-8">Settings</h1>

            <div className="space-y-6">
                {/* Enhanced Profile Section */}
                <div className="flex items-center gap-6 mb-10">
                    <InitialAvatar name={userName} size="lg" />
                    <div>
                        <div className="flex items-center gap-2">
                            <h2 className="text-2xl font-black text-gray-900 dark:text-white tracking-tight">{userName}</h2>
                            <CheckCircle size={22} className="text-blue-500 fill-blue-500/10" />
                        </div>
                        <div className="flex flex-col gap-0.5 mt-1">
                            <p className="text-sm font-bold text-gray-500">{userRole}</p>
                            <p className="text-[10px] font-black uppercase tracking-[0.15em] text-gray-400">Verified {userRole === 'Admin' ? 'Administrator' : 'Policyholder'}</p>
                        </div>
                        <button
                            onClick={() => setIsProfileOpen(true)}
                            className={cn("text-xs font-bold mt-4 px-4 py-1.5 rounded-full bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 transition-all", accentColor)}
                        >
                            Edit Display Info
                        </button>
                    </div>
                </div>

                {/* Account Actions */}
                <div>
                    <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 px-2">Account</h3>
                    <div className="rounded-2xl border border-gray-200 dark:border-white/10 overflow-hidden shadow-sm">
                        <SettingRow
                            icon={History}
                            label="Claim History & Activity"
                            value="View All"
                            onClick={() => setView('history')}
                        />
                        <SettingRow
                            icon={User}
                            label="Personal Details"
                            value="Manage"
                            onClick={() => setIsPersonalDetailsOpen(true)}
                        />
                    </div>
                </div>

                {/* Preferences */}
                <div>
                    <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 px-2">Preferences</h3>
                    <div className="rounded-2xl border border-gray-200 dark:border-white/10 overflow-hidden shadow-sm">
                        <SettingRow
                            icon={Bell}
                            label="Notifications"
                            type="toggle"
                            active={notifications}
                            onClick={handleNotificationToggle}
                        />
                    </div>
                </div>

                <div>
                    <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 px-2">Security & Privacy</h3>
                    <div className="rounded-2xl border border-gray-200 dark:border-white/10 overflow-hidden shadow-sm">
                        {CURRENT_USER.role === 'Admin' && (
                            <div className="bg-white dark:bg-white/5 border-b border-gray-100 dark:border-white/5 p-4 flex flex-col gap-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-gray-300">
                                        <ShieldAlert size={18} />
                                    </div>
                                    <span className="font-medium text-gray-900 dark:text-white">Fraud Detection Sensitivity</span>
                                </div>
                                <div className="grid grid-cols-3 gap-2">
                                    {(['Aggressive', 'Balanced', 'Conservative'] as const).map(mode => (
                                        <button
                                            key={mode}
                                            onClick={() => setFraudMode(mode)}
                                            className={cn(
                                                "py-2.5 px-2 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all border",
                                                fraudMode === mode
                                                    ? "bg-orange-500 text-white border-orange-500 shadow-md scale-[1.02]"
                                                    : "bg-gray-50 dark:bg-white/5 text-gray-500 border-gray-100 dark:border-white/10 hover:bg-gray-100 dark:hover:bg-white/10"
                                            )}
                                        >
                                            {mode}
                                        </button>
                                    ))}
                                </div>
                                <p className="text-[10px] text-gray-400 italic">
                                    {fraudMode === 'Aggressive' && "Higher sensitivity: Catches more potential fraud but may increase false positives."}
                                    {fraudMode === 'Balanced' && "Standard sensitivity: Recommended for optimal operations."}
                                    {fraudMode === 'Conservative' && "Lower sensitivity: Focuses on clearly identified risk patterns only."}
                                </p>
                            </div>
                        )}
                        <SettingRow
                            icon={Shield}
                            label="Two-Factor Authentication"
                            value={is2FAEnabled ? "Enabled" : "Disabled"}
                            onClick={() => setIs2FAOpen(true)}
                        />
                    </div>
                </div>

                <div className="pt-4">
                    <Button variant="danger" className="w-full h-12" onClick={onLogout}>
                        <LogOut size={18} /> Sign Out
                    </Button>
                </div>
            </div>

            {/* Display Info Modal */}
            <Modal isOpen={isProfileOpen} onClose={() => setIsProfileOpen(false)} title="Edit Display Profile">
                <div className="space-y-4">
                    <div>
                        <label className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1 block">Display Name</label>
                        <Input
                            type="text"
                            value={userName}
                            onChange={(e) => setUserName(e.target.value)}
                            className={cn("w-full h-12 focus:ring-2", focusRing)}
                        />
                    </div>
                    {CURRENT_USER.role === 'Admin' && (
                        <div>
                            <label className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1 block">Role (Admin Overwrite)</label>
                            <select
                                value={userRole || ''}
                                onChange={(e) => setUserRole(e.target.value as any)}
                                className={cn("w-full h-12 p-3 bg-gray-50 dark:bg-white/5 rounded-2xl border border-gray-200 dark:border-white/10 focus:ring-2 outline-none", focusRing)}
                            >
                                <option value="Admin">Admin</option>
                                <option value="Manager">Manager</option>
                                <option value="Adjuster">Adjuster</option>
                                <option value="User">User</option>
                            </select>
                        </div>
                    )}
                    <div className="flex gap-3 pt-4">
                        <Button variant="secondary" onClick={() => setIsProfileOpen(false)} className="flex-1">Cancel</Button>
                        <Button onClick={handleSaveProfile} className="flex-1">Save</Button>
                    </div>
                </div>
            </Modal>

            {/* Personal Details Modal */}
            <Modal isOpen={isPersonalDetailsOpen} onClose={() => setIsPersonalDetailsOpen(false)} title="Personal Details">
                <div className="space-y-6">
                    <p className="text-xs text-gray-500 font-medium">Update your verified contact and address information for policy accuracy.</p>
                    <div className="space-y-4">
                        <div className="space-y-1">
                            <label className="text-[10px] font-black uppercase text-gray-400 flex items-center gap-2 ml-1">
                                <Mail size={12} /> Email Address
                            </label>
                            <Input
                                type="email"
                                value={personalInfo.email}
                                onChange={(e) => setPersonalInfo({ ...personalInfo, email: e.target.value })}
                                placeholder="Email"
                            />
                        </div>
                        <div className="space-y-1">
                            <label className="text-[10px] font-black uppercase text-gray-400 flex items-center gap-2 ml-1">
                                <Phone size={12} /> Phone Number
                            </label>
                            <Input
                                type="tel"
                                value={personalInfo.phone}
                                onChange={(e) => setPersonalInfo({ ...personalInfo, phone: e.target.value })}
                                placeholder="Phone"
                            />
                        </div>
                        <div className="space-y-1">
                            <label className="text-[10px] font-black uppercase text-gray-400 flex items-center gap-2 ml-1">
                                <MapPin size={12} /> Primary Address
                            </label>
                            <Input
                                type="text"
                                value={personalInfo.address}
                                onChange={(e) => setPersonalInfo({ ...personalInfo, address: e.target.value })}
                                placeholder="Address"
                            />
                        </div>
                    </div>
                    <div className="flex gap-3 pt-4 border-t border-gray-100 dark:border-white/5">
                        <Button variant="secondary" onClick={() => setIsPersonalDetailsOpen(false)} className="flex-1">Discard</Button>
                        <Button onClick={handleSavePersonalDetails} className="flex-1">Update Details</Button>
                    </div>
                </div>
            </Modal>

            {/* 2FA Modal */}
            <Modal isOpen={is2FAOpen} onClose={() => setIs2FAOpen(false)} title="Security Center">
                <div className="space-y-6">
                    {!is2FAEnabled && !show2FAQR ? (
                        <div className="flex flex-col items-center text-center py-4">
                            <div className="w-16 h-16 bg-orange-50 dark:bg-orange-900/20 rounded-3xl flex items-center justify-center text-orange-600 mb-4">
                                <Lock size={32} />
                            </div>
                            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Secure Your Account</h3>
                            <p className="text-sm text-gray-500 max-w-xs mb-8">Two-Factor Authentication adds an extra layer of security to your Vantage account by requiring a code from your phone.</p>
                            <Button className="w-full h-14 rounded-2xl bg-orange-600 text-white border-0 shadow-lg shadow-orange-500/20" onClick={() => setShow2FAQR(true)}>
                                Set Up Authenticator
                            </Button>
                        </div>
                    ) : show2FAQR ? (
                        <div className="space-y-6 animate-in zoom-in-95 duration-300">
                            <div className="flex flex-col items-center p-8 bg-gray-50 dark:bg-white/5 rounded-3xl border border-gray-200 dark:border-white/10">
                                <div className="p-4 bg-white rounded-2xl shadow-inner mb-6">
                                    <QrCode size={160} className="text-gray-900" />
                                </div>
                                <div className="text-center">
                                    <p className="font-bold text-gray-900 dark:text-white text-lg">Scan QR Code</p>
                                    <p className="text-xs text-gray-500 mt-1 uppercase tracking-widest font-black">Use Google Authenticator or Authy</p>
                                </div>
                            </div>
                            <div className="space-y-3">
                                <p className="text-xs font-bold text-gray-400 uppercase tracking-widest ml-1">Enter Verification Code</p>
                                <div className="grid grid-cols-6 gap-2">
                                    {[1, 2, 3, 4, 5, 6].map(i => (
                                        <input key={i} type="text" maxLength={1} className="w-full h-12 text-center text-xl font-bold bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500 outline-none" placeholder="0" />
                                    ))}
                                </div>
                            </div>
                            <div className="flex gap-3 pt-4">
                                <Button variant="secondary" onClick={() => setShow2FAQR(false)} className="flex-1">Back</Button>
                                <Button onClick={handleEnable2FA} className="flex-1 bg-orange-600 text-white border-0">Verify & Activate</Button>
                            </div>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center text-center py-6">
                            <div className="w-16 h-16 bg-emerald-50 dark:bg-emerald-900/20 rounded-3xl flex items-center justify-center text-emerald-600 mb-4">
                                <CheckCircle size={32} />
                            </div>
                            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">2FA is Active</h3>
                            <p className="text-sm text-gray-500 max-w-xs mb-8">Your account is protected by an additional security layer. You will be prompted for a code on new sign-ins.</p>
                            <Button variant="danger" className="w-full h-12 rounded-2xl" onClick={() => setIs2FAEnabled(false)}>
                                Disable Two-Factor
                            </Button>
                        </div>
                    )}
                </div>
            </Modal>
        </div>
    );
};