
import React, { useRef, useState } from 'react';
import { Canvas, useFrame, ThreeElements } from '@react-three/fiber';
import { OrbitControls, Html, Sphere, Line } from '@react-three/drei';
import * as THREE from 'three';
import { Claim, RiskLevel } from '../types';

// Standard JSX elements are already provided by @types/react.
// React Three Fiber elements are handled by the library's internal type extensions.

interface ClaimRiskVisualizerProps {
  claims: Claim[];
  selectedClaimId: string;
  onSelectClaim?: (id: string) => void;
}

interface RiskPointProps {
  claim: Claim;
  isSelected: boolean;
  onClick: () => void;
}

const RiskPoint: React.FC<RiskPointProps> = ({ claim, isSelected, onClick }) => {
  const meshRef = useRef<THREE.Mesh>(null!);
  const [hovered, setHovered] = useState(false);

  // Normalize data for position
  // X: Risk Score (0-100) mapped to (-4, 4)
  const x = (claim.riskScore / 100) * 8 - 4;
  
  // Y: Amount (Log scale 1k to 2M) mapped to (-3, 3)
  // min log(1000) = 3, max log(2000000) = 6.3
  const logAmount = Math.log10(Math.max(claim.amount, 1000));
  const y = ((logAmount - 3) / (6.3 - 3)) * 6 - 3;
  
  // Z: Pseudo-random based on ID char code to spread them out in depth (-3, 3)
  const z = ((claim.id.charCodeAt(claim.id.length - 1) % 10) / 10) * 6 - 3;

  const color = claim.riskLevel === RiskLevel.Critical || claim.riskLevel === RiskLevel.High 
    ? '#EA4335' 
    : claim.riskLevel === RiskLevel.Medium 
      ? '#FBBC04' 
      : '#34A853';

  useFrame((state) => {
    if (isSelected && meshRef.current) {
      // Pulse effect for selected
      const scale = 1.5 + Math.sin(state.clock.elapsedTime * 4) * 0.3;
      meshRef.current.scale.setScalar(scale);
    } else if (meshRef.current) {
        // Hover effect
        const targetScale = hovered ? 1.5 : 1;
        meshRef.current.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.1);
    }
  });

  return (
    <group position={[x, y, z]}>
      <Sphere 
        ref={meshRef} 
        args={[0.15, 32, 32]} 
        onClick={(e) => { e.stopPropagation(); onClick(); }}
        onPointerOver={(e) => { e.stopPropagation(); setHovered(true); }}
        onPointerOut={() => setHovered(false)}
      >
        <meshStandardMaterial 
            color={isSelected ? '#ffffff' : color} 
            emissive={isSelected ? color : '#000000'}
            emissiveIntensity={isSelected ? 0.8 : 0.2}
            roughness={0.1}
            metalness={0.5}
        />
      </Sphere>
      
      {/* Tooltip */}
      {(hovered || isSelected) && (
        <Html distanceFactor={12} zIndexRange={[100, 0]}>
          <div className={`
            px-3 py-2 rounded-lg text-xs whitespace-nowrap shadow-xl border backdrop-blur-md transition-opacity duration-200
            ${isSelected 
              ? 'bg-white/90 text-gray-900 border-orange-500' 
              : 'bg-black/80 text-white border-white/20'
            }
          `}>
            <p className="font-bold">{claim.id}</p>
            <p>Risk: {claim.riskScore}</p>
            <p>${claim.amount.toLocaleString()}</p>
          </div>
        </Html>
      )}

      {/* Reference Line to 'floor' for spatial context when selected */}
      {isSelected && (
         <Line 
            points={[[0, 0, 0], [0, -y - 3.5, 0]]} 
            color={color} 
            lineWidth={1} 
            transparent 
            opacity={0.4} 
         />
      )}
    </group>
  );
};

export const ClaimRiskVisualizer = ({ claims, selectedClaimId, onSelectClaim }: ClaimRiskVisualizerProps) => {
  return (
    <div className="w-full h-[350px] rounded-2xl overflow-hidden bg-gradient-to-b from-gray-900 via-[#0a0a0a] to-black relative border border-gray-800 shadow-inner group">
      {/* Axis Labels */}
      <div className="absolute top-4 left-4 z-10 text-[10px] text-gray-400 font-mono space-y-1 pointer-events-none">
        <div className="flex items-center gap-2">
           <div className="w-2 h-0.5 bg-red-500"></div>
           <span>X: Risk Score (Low → High)</span>
        </div>
        <div className="flex items-center gap-2">
           <div className="w-2 h-0.5 bg-green-500"></div>
           <span>Y: Amount ($)</span>
        </div>
      </div>
      
      {/* Interaction Hint */}
      <div className="absolute bottom-4 right-4 z-10 text-[10px] text-gray-600 bg-black/50 px-2 py-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
        Rotate & Zoom to Explore
      </div>

      <Canvas camera={{ position: [0, 0, 10], fov: 45 }}>
        <fog attach="fog" args={['#050505', 8, 25]} />
        <ambientLight intensity={0.4} />
        <pointLight position={[10, 10, 10]} intensity={1} color="#ffffff" />
        <pointLight position={[-5, -5, -5]} intensity={0.5} color="#F97316" />
        
        <group>
            {claims.map(claim => (
            <RiskPoint 
                key={claim.id} 
                claim={claim} 
                isSelected={claim.id === selectedClaimId}
                onClick={() => onSelectClaim && onSelectClaim(claim.id)}
            />
            ))}
        </group>

        {/* Floor Grid */}
        <gridHelper args={[10, 10, 0x333333, 0x111111]} position={[0, -3.5, 0]} />
        
        {/* Animated Orbit Controls */}
        <OrbitControls 
            enableZoom={true} 
            enablePan={false} 
            autoRotate={true}
            autoRotateSpeed={0.5}
            minDistance={5}
            maxDistance={15}
        />
      </Canvas>
    </div>
  );
};