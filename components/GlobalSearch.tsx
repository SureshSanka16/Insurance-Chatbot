import React, { useState, useEffect, useRef } from 'react';
import { Search, FileText, User as UserIcon, File, Command, X } from 'lucide-react';
import { cn } from './UIComponents';
import { motion, AnimatePresence } from 'framer-motion';

interface GlobalSearchProps {
  onNavigate: (type: 'claim' | 'document' | 'user', id: string) => void;
}

export const GlobalSearch = ({ onNavigate }: GlobalSearchProps) => {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Live data from API
  const [claims, setClaims] = useState<any[]>([]);
  const [documents, setDocuments] = useState<any[]>([]);

  useEffect(() => {
    const loadData = async () => {
      try {
        const { fetchClaims } = await import('../src/api/endpoints');
        const claimsData = await fetchClaims();
        setClaims(claimsData || []);

        // Extract documents from claims
        const allDocs: any[] = [];
        (claimsData || []).forEach((claim: any) => {
          if (claim.documents) {
            claim.documents.forEach((doc: any) => {
              allDocs.push({ ...doc, claimId: claim.id, claimant: claim.claimant });
            });
          }
        });
        setDocuments(allDocs);
      } catch (err) {
        console.error('GlobalSearch: Failed to load data', err);
      }
    };
    loadData();
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
        setIsOpen(true);
      }
      if (e.key === 'Escape') {
        setIsOpen(false);
        inputRef.current?.blur();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  const filteredClaims = claims.filter(c => 
    (c.id || '').toLowerCase().includes(query.toLowerCase()) || 
    (c.claimant || '').toLowerCase().includes(query.toLowerCase()) ||
    (c.policyNumber || '').toLowerCase().includes(query.toLowerCase())
  ).slice(0, 3);

  const filteredDocs = documents.filter(d => 
    (d.name || '').toLowerCase().includes(query.toLowerCase())
  ).slice(0, 3);

  const hasResults = filteredClaims.length > 0 || filteredDocs.length > 0;

  const handleSelect = (type: 'claim' | 'document' | 'user', id: string) => {
    onNavigate(type, id);
    setIsOpen(false);
    setQuery('');
  };

  return (
    <div ref={wrapperRef} className="relative w-full max-w-xl mx-auto z-[200]">
      <div className="relative group">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-orange-500 transition-colors" size={18} />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => { setQuery(e.target.value); setIsOpen(true); }}
          onFocus={() => setIsOpen(true)}
          placeholder="Search claims, documents, users..."
          className="w-full pl-10 pr-12 py-2.5 bg-gray-100/50 dark:bg-gray-800/50 border border-transparent focus:border-orange-500/30 focus:bg-white dark:focus:bg-gray-900 rounded-xl text-sm focus:ring-4 focus:ring-orange-500/10 outline-none transition-all text-gray-900 dark:text-gray-100 placeholder-gray-500"
        />
        <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
            {query ? (
                 <button onClick={() => {setQuery(''); inputRef.current?.focus()}} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"><X size={14}/></button>
            ) : (
                <span className="text-xs text-gray-400 bg-gray-200/50 dark:bg-gray-700/50 px-1.5 py-0.5 rounded border border-gray-200 dark:border-gray-700 font-mono">⌘K</span>
            )}
        </div>
      </div>

      <AnimatePresence>
        {isOpen && query && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="absolute top-full left-0 right-0 mt-3 bg-white/95 dark:bg-gray-900/95 backdrop-blur-xl border border-gray-200 dark:border-gray-800 rounded-2xl shadow-2xl overflow-hidden max-h-[600px] overflow-y-auto z-[210]"
          >
            {hasResults ? (
              <div className="p-2 space-y-2">
                {filteredClaims.length > 0 && (
                  <div>
                    <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-wider px-3 py-2">Claims</h4>
                    {filteredClaims.map(claim => (
                      <button
                        key={claim.id}
                        onClick={() => handleSelect('claim', claim.id)}
                        className="w-full flex items-center gap-3 p-2.5 rounded-xl hover:bg-orange-50 dark:hover:bg-orange-900/20 transition-colors group text-left"
                      >
                        <div className="p-2 bg-orange-100 dark:bg-orange-900/30 text-orange-600 rounded-lg">
                          <FileText size={18} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex justify-between items-center">
                              <p className="text-sm font-medium text-gray-900 dark:text-white group-hover:text-orange-600 transition-colors truncate">{claim.id}</p>
                              <span className="text-[10px] bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded text-gray-500">{claim.status}</span>
                          </div>
                          <p className="text-xs text-gray-500 truncate">{claim.claimant} • {claim.type}</p>
                        </div>
                      </button>
                    ))}
                  </div>
                )}

                {filteredDocs.length > 0 && (
                  <div>
                    <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-wider px-3 py-2">Documents</h4>
                    {filteredDocs.map(doc => (
                      <button
                        key={doc.id}
                        onClick={() => handleSelect('document', doc.id)}
                        className="w-full flex items-center gap-3 p-2.5 rounded-xl hover:bg-orange-50 dark:hover:bg-orange-900/20 transition-colors group text-left"
                      >
                        <div className="p-2 bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 rounded-lg">
                          <File size={18} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-white group-hover:text-orange-600 transition-colors truncate">{doc.name}</p>
                          <p className="text-xs text-gray-500">{doc.type} • {doc.size}</p>
                        </div>
                      </button>
                    ))}
                  </div>
                )}

                
              </div>
            ) : (
              <div className="p-8 text-center text-gray-500">
                <Command size={32} className="mx-auto mb-2 opacity-20" />
                <p>No results found for "{query}"</p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};