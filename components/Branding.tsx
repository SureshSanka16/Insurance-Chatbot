import React from 'react';
import { cn } from './UIComponents';

export const VantageLogo = ({ className, size = 32, variant = 'orange' }: { className?: string; size?: number; variant?: 'orange' | 'blue' }) => {
  const isBlue = variant === 'blue';
  
  // Color definitions based on variant
  const colors = {
    mainStart: isBlue ? '#2563EB' : '#F97316', // Blue 600 : Orange 500
    mainEnd: isBlue ? '#1D4ED8' : '#DC2626',   // Blue 700 : Red 600
    accentStart: isBlue ? '#60A5FA' : '#FB923C', // Blue 400 : Orange 400
    accentEnd: isBlue ? '#2563EB' : '#F97316'    // Blue 600 : Orange 500
  };

  const idSuffix = isBlue ? '_blue' : '_orange';

  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 100 100" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={cn("overflow-visible", className)}
    >
      <defs>
        <linearGradient id={`vantage_main${idSuffix}`} x1="0" y1="0" x2="100" y2="100" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor={colors.mainStart}/>
          <stop offset="100%" stopColor={colors.mainEnd}/>
        </linearGradient>
        <linearGradient id={`vantage_accent${idSuffix}`} x1="100" y1="0" x2="0" y2="100" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor={colors.accentStart}/>
          <stop offset="100%" stopColor={colors.accentEnd}/>
        </linearGradient>
        <filter id={`glow${idSuffix}`} x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>
      
      {/* Geometric Abstract 'V' Shape */}
      <g filter={`url(#glow${idSuffix})`}>
          {/* Left Wing */}
          <path 
            d="M20 20 L50 85 L35 85 L5 20 Z" 
            fill={`url(#vantage_main${idSuffix})`} 
            opacity="0.9"
          />
          {/* Right Wing */}
          <path 
            d="M80 20 L50 85 L65 85 L95 20 Z" 
            fill={`url(#vantage_main${idSuffix})`} 
            opacity="0.9"
          />
          {/* Center Diamond/Prism */}
          <path 
            d="M50 35 L65 15 L50 5 L35 15 Z" 
            fill={`url(#vantage_accent${idSuffix})`}
          />
          {/* Connecting line (Circuit hint) */}
          <circle cx="50" cy="50" r="3" fill="white" fillOpacity="0.8" />
      </g>
    </svg>
  );
};