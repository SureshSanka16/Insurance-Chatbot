
import React, { useRef, useMemo, useState, useEffect } from 'react';
import { Canvas, useFrame, ThreeElements } from '@react-three/fiber';
import { OrbitControls, Html, Sphere } from '@react-three/drei';
import * as THREE from 'three';
import { MOCK_CLAIMS } from '../constants';
import { Claim } from '../types';

// Standard JSX elements are already provided by @types/react.
// React Three Fiber elements are handled by the library's internal type extensions.

// Types for the graph
export interface GraphNode {
  id: string;
  type: 'claim' | 'ip' | 'phone';
  data?: any;
  x: number;
  y: number;
  z: number;
  vx: number;
  vy: number;
  vz: number;
}

interface GraphLink {
  source: string;
  target: string;
  color: string;
  sourceObj?: GraphNode;
  targetObj?: GraphNode;
}

// Prepare graph data structure
const generateGraphData = (claims: Claim[]) => {
  const nodes: GraphNode[] = [];
  const links: GraphLink[] = [];
  const nodeMap = new Set<string>();

  const addNode = (id: string, type: 'claim' | 'ip' | 'phone', data?: any) => {
    if (!nodeMap.has(id)) {
      nodes.push({
        id,
        type,
        data,
        // Initialize with random positions to prevent stacking
        x: (Math.random() - 0.5) * 10,
        y: (Math.random() - 0.5) * 10,
        z: (Math.random() - 0.5) * 10,
        vx: 0,
        vy: 0,
        vz: 0
      });
      nodeMap.add(id);
    }
  };

  claims.forEach((c) => {
    addNode(c.id, 'claim', c);

    if (c.ipAddress) {
      addNode(c.ipAddress, 'ip');
      links.push({ source: c.id, target: c.ipAddress, color: '#EF4444' }); // Red for IP risk
    }

    if (c.phoneNumber) {
      addNode(c.phoneNumber, 'phone');
      links.push({ source: c.id, target: c.phoneNumber, color: '#F59E0B' }); // Amber for Phone risk
    }
  });

  return { nodes, links };
};

const NodeObject: React.FC<{ node: GraphNode; isSelected: boolean; onSelect: (n: GraphNode) => void }> = ({ node, isSelected, onSelect }) => {
  const ref = useRef<THREE.Group>(null);
  const [hovered, setHovered] = useState(false);

  // Sync ref position with simulation node position every frame
  useFrame(() => {
    if (ref.current) {
      // Lerp for smoother visual updates
      ref.current.position.lerp(new THREE.Vector3(node.x, node.y, node.z), 0.1);
    }
  });

  const color = node.type === 'claim' ? '#F97316' : node.type === 'ip' ? '#EF4444' : '#F59E0B';
  const size = node.type === 'claim' ? 0.35 : 0.25;

  return (
    <group ref={ref}>
      <Sphere
        args={[size, 32, 32]}
        onClick={(e) => { e.stopPropagation(); onSelect(node); }}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <meshStandardMaterial
          color={isSelected ? '#ffffff' : color}
          emissive={isSelected || hovered ? color : '#000000'}
          emissiveIntensity={isSelected || hovered ? 0.8 : 0.2}
          roughness={0.4}
          metalness={0.6}
        />
      </Sphere>
      {(hovered || isSelected) && (
        <Html distanceFactor={10} zIndexRange={[100, 0]}>
          <div className="bg-black/90 text-white p-3 rounded-xl text-xs whitespace-nowrap border border-white/20 backdrop-blur-md shadow-xl select-none pointer-events-none">
            <div className="flex items-center gap-2 mb-1">
               <div className={`w-2 h-2 rounded-full ${node.type === 'claim' ? 'bg-orange-500' : node.type === 'ip' ? 'bg-red-500' : 'bg-amber-500'}`} />
               <span className="font-bold uppercase tracking-wider text-[10px] text-gray-400">{node.type}</span>
            </div>
            <div className="font-mono text-sm font-semibold">{node.id}</div>
            {node.data && (
                <div className="mt-1 pt-1 border-t border-white/10 text-gray-400">
                    ${node.data.amount?.toLocaleString()} • {node.data.status}
                </div>
            )}
          </div>
        </Html>
      )}
    </group>
  );
};

const LinkObject: React.FC<{ link: GraphLink; sourceNode?: GraphNode; targetNode?: GraphNode }> = ({ link, sourceNode, targetNode }) => {
  const ref = useRef<any>(null);

  useFrame(() => {
    if (ref.current && sourceNode && targetNode) {
      const positions = new Float32Array([
        sourceNode.x, sourceNode.y, sourceNode.z,
        targetNode.x, targetNode.y, targetNode.z
      ]);
      ref.current.geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      ref.current.geometry.attributes.position.needsUpdate = true;
    }
  });

  if (!sourceNode || !targetNode) return null;

  return (
    <line ref={ref}>
      <bufferGeometry />
      <lineBasicMaterial color={link.color} transparent opacity={0.3} linewidth={1} />
    </line>
  );
};

const ForceGraphSimulation = ({ 
  data, 
  onNodeSelect, 
  selectedNode 
}: { 
  data: { nodes: GraphNode[], links: GraphLink[] }, 
  onNodeSelect: (n: GraphNode) => void,
  selectedNode: GraphNode | null
}) => {
  // Use a stable reference for simulation nodes to allow mutation without re-renders
  // We clone initial data once
  const simulationNodes = useMemo(() => data.nodes.map(n => ({ ...n })), [data]);

  // Pre-calculate links with object references for speed
  const simulationLinks = useMemo(() => {
    return data.links.map(l => ({
      ...l,
      sourceObj: simulationNodes.find(n => n.id === l.source),
      targetObj: simulationNodes.find(n => n.id === l.target)
    })).filter(l => l.sourceObj && l.targetObj);
  }, [data, simulationNodes]);

  useFrame(() => {
    // 1. Apply Forces
    const REPULSION = 0.5;
    const CENTER_GRAVITY = 0.01;
    const SPRING_LEN = 2.5;
    const SPRING_STRENGTH = 0.05;

    // Repulsion (All nodes repel)
    for (let i = 0; i < simulationNodes.length; i++) {
      const nodeA = simulationNodes[i];
      
      // Center Gravity
      nodeA.vx -= nodeA.x * CENTER_GRAVITY;
      nodeA.vy -= nodeA.y * CENTER_GRAVITY;
      nodeA.vz -= nodeA.z * CENTER_GRAVITY;

      for (let j = i + 1; j < simulationNodes.length; j++) {
        const nodeB = simulationNodes[j];
        const dx = nodeA.x - nodeB.x;
        const dy = nodeA.y - nodeB.y;
        const dz = nodeA.z - nodeB.z;
        const distSq = dx * dx + dy * dy + dz * dz + 0.1; // +0.1 to avoid div/0
        const force = REPULSION / distSq;
        
        const dist = Math.sqrt(distSq);
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        const fz = (dz / dist) * force;

        nodeA.vx += fx;
        nodeA.vy += fy;
        nodeA.vz += fz;
        nodeB.vx -= fx;
        nodeB.vy -= fy;
        nodeB.vz -= fz;
      }
    }

    // Spring (Links attract)
    simulationLinks.forEach(link => {
      const s = link.sourceObj!;
      const t = link.targetObj!;
      
      const dx = t.x - s.x;
      const dy = t.y - s.y;
      const dz = t.z - s.z;
      const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
      
      const force = (dist - SPRING_LEN) * SPRING_STRENGTH;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      const fz = (dz / dist) * force;

      s.vx += fx;
      s.vy += fy;
      s.vz += fz;
      t.vx -= fx;
      t.vy -= fy;
      t.vz -= fz;
    });

    // 2. Update Positions with Velocity & Damping
    simulationNodes.forEach(node => {
      node.vx *= 0.91; // Damping
      node.vy *= 0.91;
      node.vz *= 0.91;
      node.x += node.vx;
      node.y += node.vy;
      node.z += node.vz;
    });
  });

  return (
    <group>
      {simulationNodes.map((node) => (
        <NodeObject 
            key={node.id} 
            node={node} 
            isSelected={selectedNode?.id === node.id}
            onSelect={onNodeSelect} 
        />
      ))}
      {simulationLinks.map((link, i) => (
        <LinkObject 
            key={i} 
            link={link} 
            sourceNode={link.sourceObj} 
            targetNode={link.targetObj} 
        />
      ))}
    </group>
  );
};

interface FraudGraphProps {
    selectedNodeId?: string | null;
    onNodeSelect?: (node: GraphNode) => void;
}

export const FraudGraph = ({ selectedNodeId, onNodeSelect }: FraudGraphProps) => {
  const data = useMemo(() => generateGraphData(MOCK_CLAIMS), []);
  const [internalSelected, setInternalSelected] = useState<GraphNode | null>(null);
  
  const activeNode = useMemo(() => {
      if (selectedNodeId !== undefined) {
          return data.nodes.find(n => n.id === selectedNodeId) || null;
      }
      return internalSelected;
  }, [selectedNodeId, internalSelected, data.nodes]);

  const handleSelect = (node: GraphNode) => {
      if (onNodeSelect) {
          onNodeSelect(node);
      } else {
          setInternalSelected(node);
      }
  };

  return (
    <div className="w-full h-full relative bg-gradient-to-br from-[#0F172A] via-[#020617] to-black rounded-3xl overflow-hidden border border-white/10 shadow-2xl">
      {/* Legend */}
      <div className="absolute top-4 left-4 z-10 space-y-2 pointer-events-none">
        <div className="flex items-center gap-2 text-xs text-white/70">
          <div className="w-2 h-2 rounded-full bg-[#F97316] shadow-[0_0_8px_#F97316]"></div> Claim
        </div>
        <div className="flex items-center gap-2 text-xs text-white/70">
          <div className="w-2 h-2 rounded-full bg-[#EF4444] shadow-[0_0_8px_#EF4444]"></div> Shared IP
        </div>
        <div className="flex items-center gap-2 text-xs text-white/70">
          <div className="w-2 h-2 rounded-full bg-[#F59E0B] shadow-[0_0_8px_#F59E0B]"></div> Shared Phone
        </div>
      </div>

      <Canvas camera={{ position: [0, 0, 18], fov: 45 }}>
        <ambientLight intensity={0.6} />
        <pointLight position={[10, 10, 10]} intensity={1} color="#ffffff" />
        <pointLight position={[-10, -10, -5]} intensity={0.5} color="#F97316" />
        
        <ForceGraphSimulation 
            data={data} 
            onNodeSelect={handleSelect} 
            selectedNode={activeNode}
        />

        <OrbitControls autoRotate={!activeNode} autoRotateSpeed={0.5} enableDamping dampingFactor={0.1} />
      </Canvas>
    </div>
  );
};