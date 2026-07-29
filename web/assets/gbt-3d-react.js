/**
 * ═══════════════════════════════════════════
 *  GBT 3D React v1 — R3F + Framer Motion + Shadcn/ui
 *  
 *  开源替代栈:
 *    Three.js (MIT) + React Three Fiber (MIT) → 替代 Spline
 *    Framer Motion (MIT) → 替代 GSAP
 *    Shadcn/ui (MIT) → 替代 V0.dev
 *    CSS Scroll-Driven Animations → 零JS动画
 *  
 *  用法:
 *    import { ParticleRing, DataGlobe, BeamLine, ScrollReveal, ParallaxCard } from './gbt-3d-react'
 * ═══════════════════════════════════════════
 */

import React, { useRef, useMemo, useEffect, useState, useCallback } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, useGLTF, Environment, Float } from '@react-three/drei';
import { motion, useScroll, useTransform, useSpring, AnimatePresence } from 'framer-motion';
import * as THREE from 'three';

/* ═══════════════════════════════════════════
   设计 Token (与 Shadcn CSS 变量对齐)
   ═══════════════════════════════════════════ */
export const TOKENS = {
  colors: {
    techBlue:   '#00d4ff',
    gold:       '#ffd700',
    purple:     '#a855f7',
    green:      '#22c55e',
    red:        '#ff4444',
    bg:         '#0a0a0f',
    cardBg:     'rgba(255,255,255,0.04)',
    border:     'rgba(255,255,255,0.08)',
  },
  glass: {
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: '16px',
    backdropFilter: 'blur(16px)',
  }
};

/* ═══════════════════════════════════════════
   1. 粒子光环 — Three.js Points + useFrame
   ═══════════════════════════════════════════ */
function ParticleField({ count = 2000, color = '#00d4ff', rings = 3, speed = 0.0005 }) {
  const pointsRef = useRef();
  const isMobile = /Mobi|Android/i.test(navigator.userAgent);
  const finalCount = isMobile ? Math.min(count, 600) : count;
  const finalRings = isMobile ? Math.min(rings, 2) : rings;

  const { positions, colors } = useMemo(() => {
    const pos = new Float32Array(finalCount * 3);
    const col = new Float32Array(finalCount * 3);
    const c = new THREE.Color(color);
    for (let i = 0; i < finalCount; i++) {
      const ri = i % finalRings;
      const r = 3 + ri * 0.3;
      const angle = (i / finalCount) * Math.PI * 2 * (ri + 1);
      const y = (Math.random() - 0.5) * 0.5 * (ri + 1);
      pos[i * 3] = Math.cos(angle) * r;
      pos[i * 3 + 1] = y;
      pos[i * 3 + 2] = Math.sin(angle) * r;
      const pc = new THREE.Color(color);
      pc.offsetHSL(ri * 0.05, 0, Math.random() * 0.3);
      col[i * 3] = pc.r;
      col[i * 3 + 1] = pc.g;
      col[i * 3 + 2] = pc.b;
    }
    return { positions: pos, colors: col };
  }, [finalCount, color, finalRings]);

  useFrame(() => {
    if (pointsRef.current) {
      pointsRef.current.rotation.x += speed * 0.3;
      pointsRef.current.rotation.y += speed;
    }
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={finalCount} array={positions} itemSize={3} />
        <bufferAttribute attach="attributes-color" count={finalCount} array={colors} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial size={isMobile ? 0.04 : 0.02} vertexColors blending={THREE.AdditiveBlending} depthWrite={false} />
    </points>
  );
}

export function ParticleRing({ count, color, rings, speed, className = '' }) {
  return (
    <div className={`fixed inset-0 -z-10 pointer-events-none ${className}`} style={{ opacity: 0.6 }}>
      <Canvas camera={{ position: [0, 0, 5], fov: 60 }} dpr={[1, 2]}>
        <ParticleField count={count} color={color} rings={rings} speed={speed} />
      </Canvas>
    </div>
  );
}

/* ═══════════════════════════════════════════
   2. 3D 地球 — 支持GLB模型 + 动态数据标记
   ═══════════════════════════════════════════ */
function GlobeMarkers({ markers, radius = 1.5 }) {
  const groupRef = useRef();
  const t = useRef(0);

  useFrame((_, delta) => {
    t.current += delta;
    if (groupRef.current) {
      groupRef.current.children.forEach((child, i) => {
        if (child.isMesh) {
          const pulse = 1 + Math.sin(t.current * 3 + i) * 0.05;
          child.scale.setScalar(pulse);
          child.material.opacity = 0.5 + Math.sin(t.current * 3 + i) * 0.5;
        }
      });
    }
  });

  const dots = useMemo(() => {
    return (markers || []).map((m, i) => {
      const phi = (90 - m.lat) * Math.PI / 180;
      const theta = m.lng * Math.PI / 180;
      return {
        position: [
          radius * 1.02 * Math.sin(phi) * Math.cos(theta),
          radius * 1.02 * Math.cos(phi),
          radius * 1.02 * Math.sin(phi) * Math.sin(theta),
        ],
        color: m.color || '#ff4444',
        key: i
      };
    });
  }, [markers, radius]);

  return (
    <group ref={groupRef}>
      {dots.map((d) => (
        <mesh key={d.key} position={d.position}>
          <sphereGeometry args={[0.03, 8, 8]} />
          <meshBasicMaterial color={d.color} transparent opacity={0.8} />
        </mesh>
      ))}
    </group>
  );
}

function GlobeScene({ color = '#00d4ff', markers, speed = 0.002, modelUrl = null }) {
  const globeRef = useRef();
  const [modelError, setModelError] = useState(false);

  useFrame(() => {
    if (globeRef.current) globeRef.current.rotation.y += speed;
  });

  return (
    <group ref={globeRef}>
      {/* 线框地球 */}
      <mesh>
        <sphereGeometry args={[1.5, 64, 48]} />
        <meshPhongMaterial color={color} wireframe transparent opacity={0.6} emissive={new THREE.Color(color).multiplyScalar(0.2)} />
      </mesh>
      {/* 外发光 */}
      <mesh>
        <sphereGeometry args={[1.58, 64, 48]} />
        <shaderMaterial
          uniforms={{ uColor: { value: new THREE.Color(color) } }}
          vertexShader="varying vec3 vNormal; void main(){vNormal=normalize(normalMatrix*normal);gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}"
          fragmentShader="varying vec3 vNormal; uniform vec3 uColor; void main(){float intensity=pow(0.7-dot(vNormal,vec3(0,0,1.0)),2.0);gl_FragColor=vec4(uColor,intensity*0.3);}"
          transparent blending={THREE.AdditiveBlending} depthWrite={false}
        />
      </mesh>
      {/* 数据标记 */}
      {markers && markers.length > 0 && <GlobeMarkers markers={markers} />}
      {/* 环绕粒子 */}
      <OrbitParticles color={color} count={500} radius={1.5} />
    </group>
  );
}

function OrbitParticles({ color, count = 500, radius = 1.5 }) {
  const { positions } = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const angle = (i / count) * Math.PI * 2;
      const r = radius * 1.2 + Math.random() * 0.5;
      pos[i * 3] = Math.cos(angle) * r;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 1.5;
      pos[i * 3 + 2] = Math.sin(angle) * r;
    }
    return { positions: pos };
  }, [count, radius]);

  return (
    <points>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial size={0.02} color={color} blending={THREE.AdditiveBlending} depthWrite={false} />
    </points>
  );
}

export function DataGlobe({ color, markers, speed, markerFetchUrl, markerInterval = 3000, className = '' }) {
  const [dynamicMarkers, setDynamicMarkers] = useState(markers || [
    { label: '北京', lng: 116.4, lat: 39.9, color: 0x00ff88 },
    { label: '纽约', lng: -74, lat: 40.7, color: 0xff6644 },
    { label: '伦敦', lng: -0.1, lat: 51.5, color: 0x4488ff },
    { label: '新加坡', lng: 103.8, lat: 1.3, color: 0xffdd44 },
  ]);

  useEffect(() => {
    if (!markerFetchUrl) return;
    const fetchMarkers = () => {
      fetch(markerFetchUrl)
        .then(r => r.json())
        .then(data => {
          const m = Array.isArray(data) ? data : (data.markers || data.nodes || []);
          setDynamicMarkers(m);
        })
        .catch(() => {});
    };
    fetchMarkers();
    const timer = setInterval(fetchMarkers, markerInterval);
    return () => clearInterval(timer);
  }, [markerFetchUrl, markerInterval]);

  return (
    <div className={`${className}`} style={{ width: 400, height: 400 }}>
      <Canvas camera={{ position: [0, 0, 4], fov: 45 }} dpr={[1, 2]}>
        <ambientLight intensity={0.3} color="#222244" />
        <pointLight position={[3, 3, 3]} intensity={1} />
        <GlobeScene color={color} markers={dynamicMarkers} speed={speed} />
        <OrbitControls enableZoom={false} enablePan={false} />
      </Canvas>
    </div>
  );
}

/* ═══════════════════════════════════════════
   3. 滚动入场 — Framer Motion (替代IntersectionObserver)
   ═══════════════════════════════════════════ */
export function ScrollReveal({ children, stagger = 0.1, className = '' }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 30, scale: 0.96 }}
      whileInView={{ opacity: 1, y: 0, scale: 1 }}
      viewport={{ once: true, margin: '-50px' }}
      transition={{ duration: 0.6, ease: [0.22, 0.61, 0.36, 1], delay: stagger }}
    >
      {children}
    </motion.div>
  );
}

export function StaggerReveal({ children, baseStagger = 0.1 }) {
  const childrenArray = React.Children.toArray(children);
  return childrenArray.map((child, i) => (
    <ScrollReveal key={i} stagger={i * baseStagger}>
      {child}
    </ScrollReveal>
  ));
}

/* ═══════════════════════════════════════════
   4. 鼠标视差 — Framer Motion (移动端自动禁用)
   ═══════════════════════════════════════════ */
export function ParallaxCard({ children, depth = 2, className = '' }) {
  const isMobile = /Mobi|Android/i.test(navigator.userAgent);
  const x = useSpring(0, { stiffness: 100, damping: 30 });
  const y = useSpring(0, { stiffness: 100, damping: 30 });

  const handleMouseMove = useCallback((e) => {
    if (isMobile) return;
    const rect = e.currentTarget.getBoundingClientRect();
    x.set(((e.clientX - rect.left) / rect.width - 0.5) * depth * 30);
    y.set(((e.clientY - rect.top) / rect.height - 0.5) * depth * 30);
  }, [isMobile, depth, x, y]);

  if (isMobile) return <div className={className}>{children}</div>;

  return (
    <motion.div
      className={className}
      onMouseMove={handleMouseMove}
      style={{ x, y }}
      transition={{ type: 'spring', stiffness: 100, damping: 30 }}
    >
      {children}
    </motion.div>
  );
}

/* ═══════════════════════════════════════════
   5. Shadcn/ui 卡片模板
   ═══════════════════════════════════════════ */
export function GlassCard({ children, className = '', hover = true }) {
  return (
    <motion.div
      className={`rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-xl p-6 ${className}`}
      whileHover={hover ? { scale: 1.02, borderColor: 'rgba(0,212,255,0.3)' } : {}}
      transition={{ duration: 0.3 }}
    >
      {children}
    </motion.div>
  );
}

/* ═══════════════════════════════════════════
   6. 数字跳动 — Framer Motion
   ═══════════════════════════════════════════ */
export function CountUp({ from = 0, to, duration = 1.5, className = '' }) {
  const ref = useRef(null);
  const spring = useSpring(from, { stiffness: 50, damping: 20 });

  useEffect(() => {
    spring.set(to);
  }, [to, spring]);

  useEffect(() => {
    return spring.on('change', (v) => {
      if (ref.current) ref.current.textContent = Math.round(v).toLocaleString();
    });
  }, [spring]);

  return <span ref={ref} className={className}>{from}</span>;
}

/* ═══════════════════════════════════════════
   Export all
   ═══════════════════════════════════════════ */
export default {
  ParticleRing, DataGlobe, ScrollReveal, StaggerReveal,
  ParallaxCard, GlassCard, CountUp, TOKENS
};
