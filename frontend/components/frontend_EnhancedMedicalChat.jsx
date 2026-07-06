"use client";
import React, { useState, useEffect, useRef, useCallback, useMemo, memo } from "react";
import {
  Send, Mic, MicOff, Image as ImageIcon, Loader2, Square,
  FileText, Activity, Clock, ChevronRight, Plus, X, Trash2,
  Upload, Heart, AlertTriangle, Shield, Brain, BookOpen,
  Pill, Download, Globe, Zap, Eye, Stethoscope,
  Check, Moon, Sun, Search, Settings,
  Calendar, ClipboardList, Users, Sparkles, TrendingUp, Target,
  Play, Pause, Volume2, VolumeX, RotateCcw,
  RefreshCw,
  MessageSquare, BarChart3, ChevronLeft, Cpu, Waves,
  FlaskConical, Dna, Microscope, Syringe, Wind, Droplets,
  Thermometer, LayoutDashboard, ListChecks, ChevronDown,
  ExternalLink, Phone, BookMarked, Share2, Clipboard, MapPin,
} from "lucide-react";

/* ═══════════════════════════════════════════════════════════
   API
═══════════════════════════════════════════════════════════ */

const apiFetch = async (url, options = {}) => {
  const token = localStorage.getItem("ai_doctor_token");
  const headers = { ...options.headers };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  
  const res = await window.fetch(url, { ...options, headers });
  if (res.status === 401 || res.status === 403) {
    window.dispatchEvent(new Event("auth_error"));
  }
  return res;
};

const API = process.env.NEXT_PUBLIC_API_URL || (typeof window !== "undefined" ? window.location.origin : "");

/* ═══════════════════════════════════════════════════════════
   CONSTANTS
═══════════════════════════════════════════════════════════ */
const BODY_REGIONS = [
  { id: "head", label: "Head", cx: 150, cy: 30, desc: "Headache, migraine, dizziness" },
  { id: "eyes", label: "Eyes", cx: 150, cy: 52, desc: "Vision problems, eye pain" },
  { id: "chest", label: "Chest", cx: 150, cy: 145, desc: "Chest pain, breathing" },
  { id: "abdomen", label: "Abdomen", cx: 150, cy: 200, desc: "Stomach pain, digestion" },
  { id: "left_arm", label: "Left Arm", cx: 85, cy: 175, desc: "Arm pain, numbness" },
  { id: "right_arm", label: "Right Arm", cx: 215, cy: 175, desc: "Arm pain, numbness" },
  { id: "lower_back", label: "Lower Back", cx: 200, cy: 210, desc: "Lower back pain" },
  { id: "left_leg", label: "Left Leg", cx: 130, cy: 320, desc: "Leg pain, swelling" },
  { id: "right_leg", label: "Right Leg", cx: 170, cy: 320, desc: "Leg pain, swelling" },
  { id: "skin", label: "Skin", cx: 240, cy: 260, desc: "Rashes, lesions" },
];

const VOICE_LANGUAGES = [
  { code: null, label: "Auto Detect", abbr: "AUTO" },
  { code: "en", label: "English", abbr: "EN" },
  { code: "hi", label: "Hindi", abbr: "HI" },
  { code: "pa", label: "Punjabi", abbr: "PA" },
];

const NAV_ITEMS = [
  { id: "chat", icon: MessageSquare, label: "Consult", short: "Chat" },
  { id: "dashboard", icon: LayoutDashboard, label: "Overview", short: "Dash" },
  { id: "tools", icon: FlaskConical, label: "Tools", short: "Tools" },
  { id: "reports", label: "Records", icon: Microscope, short: "Labs" },
];

const SPECIALIST_ICON_MAP = {
  general: Stethoscope, cardiologist: Heart, dermatologist: Eye,
  endocrinologist: Activity, neurologist: Brain, gastroenterologist: Shield,
  nephrologist: Droplets, psychiatrist: Brain, nutritionist: Sparkles,
  orthopedist: Activity, pulmonologist: Wind, radiologist: Search,
};

const ACCENT_PRESETS = {
  cyan: { a: "#00d4ff", a2: "#7c3aed", a3: "#00e5a0", name: "Cyan" },
  rose: { a: "#ff6b9d", a2: "#f59e0b", a3: "#34d399", name: "Rose" },
  lime: { a: "#a3e635", a2: "#06b6d4", a3: "#f472b6", name: "Lime" },
};

/* ═══════════════════════════════════════════════════════════
   THEME ENGINE
═══════════════════════════════════════════════════════════ */
function buildTheme(isDark, accentKey) {
  const acc = ACCENT_PRESETS[accentKey] || ACCENT_PRESETS.cyan;
  return isDark ? {
    bg: "#03050a",
    bgMesh: `radial-gradient(ellipse 80% 60% at 20% 10%, ${acc.a}0a 0%, transparent 60%),radial-gradient(ellipse 60% 80% at 80% 90%, ${acc.a2}08 0%, transparent 60%),radial-gradient(ellipse 50% 40% at 50% 50%, #00000000 0%, #03050a 100%)`,
    surface: "rgba(8,12,22,0.92)",
    surface2: "rgba(12,18,32,0.85)",
    surface3: "rgba(16,24,42,0.8)",
    surfaceHov: "rgba(20,30,52,0.9)",
    border: "rgba(255,255,255,0.06)",
    borderBright: "rgba(255,255,255,0.12)",
    borderAccent: `${acc.a}28`,
    text: "#f0f4ff",
    textSub: "#8899bb",
    textMuted: "#4a5878",
    accent: acc.a,
    accent2: acc.a2,
    accent3: acc.a3,
    danger: "#ff4d6d",
    warn: "#ffbb33",
    shadow: "0 2px 8px rgba(0,0,0,0.6), 0 16px 48px rgba(0,0,0,0.4)",
    shadowLg: "0 4px 16px rgba(0,0,0,0.7), 0 32px 80px rgba(0,0,0,0.5)",
    inputBg: "rgba(8,14,28,0.9)",
    msgUser: `linear-gradient(135deg, ${acc.a}18, ${acc.a2}12)`,
    msgUserBorder: `${acc.a}25`,
    msgBot: "rgba(10,16,30,0.9)",
    msgBotBorder: "rgba(255,255,255,0.07)",
    scrollbar: "rgba(255,255,255,0.08)",
    robotSkin: "#0a1628",
    robotGlow: `${acc.a}30`,
    glowA: `${acc.a}40`,
    glowA2: `${acc.a2}30`,
    isDark: true,
    accentKey,
  } : {
    bg: "#f1f5ff",
    bgMesh: `radial-gradient(ellipse 80% 60% at 20% 10%, ${acc.a}12 0%, transparent 60%),radial-gradient(ellipse 60% 80% at 80% 90%, ${acc.a2}0a 0%, transparent 60%)`,
    surface: "rgba(255,255,255,0.95)",
    surface2: "rgba(245,248,255,0.92)",
    surface3: "rgba(238,243,255,0.9)",
    surfaceHov: "rgba(230,238,255,0.95)",
    border: "rgba(0,0,0,0.07)",
    borderBright: "rgba(0,0,0,0.14)",
    borderAccent: `${acc.a}30`,
    text: "#0a0f1e",
    textSub: "#3a4868",
    textMuted: "#7a8aaa",
    accent: acc.a === "#00d4ff" ? "#0099cc" : acc.a,
    accent2: acc.a2,
    accent3: acc.a3 === "#00e5a0" ? "#009966" : acc.a3,
    danger: "#e0294a",
    warn: "#d97706",
    shadow: "0 2px 8px rgba(0,0,0,0.08), 0 8px 32px rgba(0,0,0,0.06)",
    shadowLg: "0 4px 16px rgba(0,0,0,0.1), 0 16px 48px rgba(0,0,0,0.08)",
    inputBg: "rgba(245,248,255,0.95)",
    msgUser: `linear-gradient(135deg, ${acc.a}14, ${acc.a2}0e)`,
    msgUserBorder: `${acc.a}28`,
    msgBot: "rgba(255,255,255,0.98)",
    msgBotBorder: "rgba(0,0,0,0.07)",
    scrollbar: "rgba(0,0,0,0.1)",
    robotSkin: "#dbeafe",
    robotGlow: `${acc.a}20`,
    glowA: `${acc.a}35`,
    glowA2: `${acc.a2}25`,
    isDark: false,
    accentKey,
  };
}

/* ═══════════════════════════════════════════════════════════
   GLOBAL CSS INJECTION
═══════════════════════════════════════════════════════════ */
function injectGlobalStyles(T) {
  let el = document.getElementById("ma-ultimate-styles");
  if (!el) { el = document.createElement("style"); el.id = "ma-ultimate-styles"; document.head.appendChild(el); }
  el.textContent = `
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;0,9..40,800;1,9..40,400&family=Instrument+Serif:ital@0;1&family=Fira+Code:wght@400;500;600&display=swap');

:root {
  --sat: env(safe-area-inset-top,0px);
  --sab: env(safe-area-inset-bottom,0px);
}
*, *::before, *::after { box-sizing:border-box; margin:0; padding:0; }
html {
  height: 100%;
  height: -webkit-fill-available;
  background-color: var(--ma-bg, #03050a);
}
body {
  height: 100%;
  font-family: 'DM Sans', sans-serif;
  -webkit-font-smoothing: antialiased;
  background-color: var(--ma-bg, #03050a);
  overscroll-behavior-y: contain;
}

::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:${T.scrollbar}; border-radius:99px; }

/* ═══ KEYFRAMES ═══ */
@keyframes fadeUp    { from{opacity:0;transform:translateY(18px)} to{opacity:1;transform:translateY(0)} }
@keyframes fadeIn    { from{opacity:0} to{opacity:1} }
@keyframes spin      { to{transform:rotate(360deg)} }
@keyframes blink     { 0%,100%{opacity:1} 50%{opacity:0} }
@keyframes bounce    { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-7px)} }
@keyframes float     { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-9px)} }
@keyframes shimmer   { from{transform:translateX(-120%)} to{transform:translateX(220%)} }
@keyframes ringGrow  { from{stroke-dashoffset:var(--circ)} to{stroke-dashoffset:var(--offset)} }
@keyframes scanLine  { from{top:-2px} to{top:102%} }
@keyframes thinkDot  { 0%{transform:scale(0.4);opacity:0} 50%{transform:scale(1.1);opacity:1} 100%{transform:scale(0.4);opacity:0} }
@keyframes popIn     { 0%{transform:scale(0.85) translateY(6px);opacity:0} 65%{transform:scale(1.03);opacity:1} 100%{transform:scale(1);opacity:1} }
@keyframes glowPulse { 0%,100%{opacity:0.6} 50%{opacity:1} }
@keyframes orbitDot  { from{transform:rotate(0deg) translateX(56px) rotate(0deg)} to{transform:rotate(360deg) translateX(56px) rotate(-360deg)} }
@keyframes progressFill { from{width:0%} to{width:var(--tw)} }
@keyframes antennaPulse { 0%,100%{r:2} 50%{r:3.5} }
@keyframes slideInLeft { from{opacity:0;transform:translateX(-8px)} to{opacity:1;transform:translateX(0)} }
@keyframes disclaimerSlideIn { from{opacity:0;transform:translateX(120%)} to{opacity:1;transform:translateX(0)} }
@keyframes riskAlertSlideIn { from{opacity:0;transform:translateX(120%) scale(0.95)} to{opacity:1;transform:translateX(0) scale(1)} }

/* ═══ UTILITY ═══ */
.fade-up   { animation:fadeUp  0.4s cubic-bezier(0.16,1,0.3,1) both; }
.fade-in   { animation:fadeIn  0.2s ease both; }
.pop-in    { animation:popIn   0.38s cubic-bezier(0.16,1,0.3,1) both; }
.slide-in  { animation:slideInLeft 0.3s cubic-bezier(0.16,1,0.3,1) both; }

.stagger > * { opacity:0; animation:fadeUp 0.44s cubic-bezier(0.16,1,0.3,1) both; }
.stagger > *:nth-child(1){animation-delay:.00s}
.stagger > *:nth-child(2){animation-delay:.07s}
.stagger > *:nth-child(3){animation-delay:.14s}
.stagger > *:nth-child(4){animation-delay:.21s}
.stagger > *:nth-child(5){animation-delay:.28s}
.stagger > *:nth-child(6){animation-delay:.35s}
.stagger > *:nth-child(7){animation-delay:.42s}
.stagger > *:nth-child(8){animation-delay:.49s}
.stagger > *:nth-child(9){animation-delay:.56s}

/* ═══ SKELETON ═══ */
.ma-skeleton {
  position: relative;
  overflow: hidden;
  background: ${T.surface2};
  border-radius: 8px;
}
.ma-skeleton::after {
  content: "";
  position: absolute; top: 0; right: 0; bottom: 0; left: 0;
  transform: translateX(-100%);
  background-image: linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.06) 20%, rgba(255,255,255,0.12) 50%, rgba(255,255,255,0.06) 80%, rgba(255,255,255,0) 100%);
  animation: shimmer 2s infinite;
}

/* ═══ CURSOR ═══ */
.ma-cursor {
  display:inline-block; width:2px; height:1.2em;
  background:${T.accent}; border-radius:1px;
  animation:blink 1.05s steps(2, start) infinite;
  vertical-align:-0.15em; margin-left:1px;
}

/* ═══ LOADING DOTS ═══ */
.dot1{animation:bounce 1.2s ease-in-out infinite}
.dot2{animation:bounce 1.2s ease-in-out .14s infinite}
.dot3{animation:bounce 1.2s ease-in-out .28s infinite}

/* ═══ WAVE BARS ═══ */

/* ═══ ROBOT ═══ */
.robot-float{ animation:float 3.8s ease-in-out infinite; }
.robot-think .think-dot-1{animation:thinkDot 1.6s ease-in-out infinite}
.robot-think .think-dot-2{animation:thinkDot 1.6s ease-in-out .22s infinite}
.robot-think .think-dot-3{animation:thinkDot 1.6s ease-in-out .44s infinite}
.robot-think .ant-ball{animation:antennaPulse 0.7s ease-in-out infinite}
.robot-think .scan-line{display:block;animation:scanLine 1s linear infinite}

/* ═══ RING ═══ */
.ma-ring-path {
  stroke-dasharray: var(--circ);
  stroke-dashoffset: var(--circ);
  animation: ringGrow 1.5s cubic-bezier(0.4,0,0.2,1) forwards 0.15s;
}

/* ═══════════════════════════════════════════
   SIDEBAR
═══════════════════════════════════════════ */
.ma-sidebar {
  border-right:1px solid ${T.border};
  background:${T.isDark ? "rgba(5,7,15,0.98)" : "rgba(255,255,255,0.99)"};
}

@media (max-width:768px) {
  .ma-sidebar {
    position:fixed !important;
    top:0 !important; left:0 !important; bottom:0 !important;
    width:272px !important; min-width:272px !important;
    z-index:40 !important;
    transform:translateX(-272px);
    transition:transform 0.3s cubic-bezier(0.4,0,0.2,1) !important;
    box-shadow:12px 0 60px rgba(0,0,0,0.4) !important;
  }
  .ma-sidebar.open { transform:translateX(0) !important; }
  .ma-sidebar .ma-sidebar-inner { transform:translateX(0) !important; }
  .ma-mobile-backdrop { display:block !important; }
}

/* ═══════════════════════════════════════════
   NAV
═══════════════════════════════════════════ */
.ma-nav-item {
  display:flex; align-items:center; gap:12px;
  padding:9px 14px; border-radius:8px;
  font-size:13.5px; font-weight:500; color:${T.textSub};
  cursor:pointer; transition:all 0.15s ease;
  border:1px solid transparent; width:100%; text-align:left;
  font-family:'DM Sans',sans-serif; background:transparent;
  letter-spacing:-0.01em; position:relative;
}
.ma-nav-item:hover { background:${T.surface2}; color:${T.text}; }
.ma-nav-item.active {
  background:${T.isDark ? `${T.accent}0d` : `${T.accent}08`};
  color:${T.accent}; border-color:${T.accent}20; font-weight:600;
}
.ma-nav-item.active::before {
  content:''; position:absolute; left:0; top:25%; bottom:25%;
  width:2.5px; border-radius:99px; background:${T.accent};
}

/* ═══════════════════════════════════════════
   BUTTONS
═══════════════════════════════════════════ */
.ma-btn {
  display:inline-flex; align-items:center; justify-content:center; gap:6px;
  font-family:'DM Sans',sans-serif; font-weight:600; font-size:13.5px;
  border-radius:8px; padding:8px 16px; cursor:pointer; border:none;
  transition:all 0.15s ease; white-space:nowrap; letter-spacing:-0.01em;
}
.ma-btn:active { transform:scale(0.96); }
.ma-btn:disabled { opacity:0.35; pointer-events:none; }

.ma-btn-primary {
  background:${T.accent}; color:${T.isDark ? "#000" : "#fff"};
  box-shadow:0 1px 0 rgba(255,255,255,0.1) inset;
}
.ma-btn-primary:hover { filter:brightness(1.1); box-shadow:0 4px 20px ${T.accent}40; transform:translateY(-1px); }

.ma-btn-ghost {
  background:transparent; color:${T.textSub};
  border:1px solid ${T.border};
}
.ma-btn-ghost:hover { background:${T.surface2}; color:${T.text}; border-color:${T.borderBright}; }

.ma-btn-danger  { background:${T.danger}15; color:${T.danger}; border:1px solid ${T.danger}28; }
.ma-btn-danger:hover  { background:${T.danger}25; }
.ma-btn-success { background:${T.accent3}12; color:${T.accent3}; border:1px solid ${T.accent3}28; }
.ma-btn-success:hover { background:${T.accent3}22; }
.ma-btn-accent2 { background:${T.accent2}12; color:${T.accent2}; border:1px solid ${T.accent2}28; }

.ma-btn-sm   { padding:5px 12px; font-size:12px; border-radius:7px; }
.ma-btn-icon { padding:8px; border-radius:7px; }
.ma-btn-xs   { padding:3px 9px; font-size:11.5px; border-radius:6px; }

/* ═══════════════════════════════════════════
   INPUT
═══════════════════════════════════════════ */
.ma-input {
  width:100%;
  background:${T.inputBg};
  border:1px solid ${T.border};
  border-radius:8px;
  padding:9px 14px;
  font-family:'DM Sans',sans-serif;
  font-size:13.5px;
  color:${T.text};
  outline:none;
  transition:border-color 0.12s, box-shadow 0.12s;
  letter-spacing:-0.005em;
}
.ma-input::placeholder { color:${T.textMuted}; }
.ma-input:focus {
  border-color:${T.accent}60;
  box-shadow:0 0 0 3px ${T.accent}12;
}
textarea.ma-input { resize:none; min-height:46px; max-height:140px; line-height:1.6; }
select.ma-input { cursor:pointer; }

/* ═══════════════════════════════════════════
   CARD  — surgical, not rounded everywhere
═══════════════════════════════════════════ */
.ma-card {
  background:${T.surface};
  border:1px solid ${T.border};
  border-radius:12px;
  box-shadow:${T.shadow};
}
/* Strong accent variant */
.ma-card-accent {
  border-color:${T.borderAccent};
  box-shadow:${T.shadow}, 0 0 0 1px ${T.accent}10;
}

/* ═══════════════════════════════════════════
   TOOL CARD
═══════════════════════════════════════════ */
.ma-tool-card {
  background:${T.surface};
  border:1px solid ${T.border};
  border-radius:12px;
  padding:22px 20px;
  cursor:pointer;
  transition:border-color 0.15s, box-shadow 0.15s, transform 0.15s;
  text-align:left; position:relative; overflow:hidden;
}
.ma-tool-card::after {
  content:'';
  position:absolute; top:0; left:-100%; width:60%; height:100%;
  background:linear-gradient(90deg,transparent,${T.isDark ? "rgba(255,255,255,0.03)" : "rgba(255,255,255,0.5)"},transparent);
  transition:left 0.5s;
}
.ma-tool-card:hover { border-color:${T.accent}35; box-shadow:0 4px 24px rgba(0,0,0,0.12); transform:translateY(-2px); }
.ma-tool-card:hover::after { left:200%; }

/* ═══════════════════════════════════════════
   SESSION
═══════════════════════════════════════════ */
.ma-session {
  transition:background 0.12s; border-radius:7px;
  border:1px solid transparent; cursor:pointer;
}
.ma-session:hover { background:${T.surface2}; }
.ma-session.active { background:${T.accent}0a; border-color:${T.accent}22; }

/* ═══════════════════════════════════════════
   TAGS
═══════════════════════════════════════════ */
.ma-tag {
  display:inline-flex; align-items:center; gap:5px;
  background:${T.accent}12; border:1px solid ${T.accent}25;
  color:${T.accent}; padding:3px 10px; border-radius:6px;
  font-size:12px; font-weight:600;
}
.ma-tag-green  { background:${T.accent3}10; border-color:${T.accent3}22; color:${T.accent3}; }
.ma-tag-purple { background:${T.accent2}10; border-color:${T.accent2}22; color:${T.accent2}; }

/* ═══════════════════════════════════════════
   TRIAGE
═══════════════════════════════════════════ */
.ma-triage {
  display:inline-flex; align-items:center; gap:6px;
  padding:4px 12px; border-radius:6px;
  font-size:11px; font-weight:800;
  letter-spacing:0.07em; text-transform:uppercase; border:1px solid;
}

/* ═══════════════════════════════════════════
   MODE PILLS
═══════════════════════════════════════════ */
.ma-mode-pill {
  padding:4px 11px; border-radius:6px; font-size:12px; font-weight:600;
  cursor:pointer; transition:all 0.12s; border:1px solid transparent;
  color:${T.textMuted}; font-family:'DM Sans',sans-serif;
}
.ma-mode-pill.active { background:${T.accent}15; color:${T.accent}; border-color:${T.accent}30; }
.ma-mode-pill:not(.active):hover { color:${T.text}; background:${T.surface2}; }

/* ═══════════════════════════════════════════
   DROPDOWN
═══════════════════════════════════════════ */
.ma-dropdown {
  background:${T.surface};
  border:1px solid ${T.borderBright};
  border-radius:10px;
  box-shadow:0 16px 48px rgba(0,0,0,0.3), 0 1px 0 ${T.border};
  overflow:hidden;
}
.ma-dropdown-item {
  display:flex; align-items:center; gap:9px;
  padding:9px 14px; font-size:13.5px; cursor:pointer;
  color:${T.text}; transition:background 0.1s; font-family:'DM Sans',sans-serif;
}
.ma-dropdown-item:hover { background:${T.surface2}; }
.ma-suggest {
  padding:9px 14px; font-size:13.5px; cursor:pointer;
  transition:background 0.1s;
  display:flex; align-items:center; justify-content:space-between;
  border-bottom:1px solid ${T.border}; font-family:'DM Sans',sans-serif; color:${T.text};
}
.ma-suggest:last-child { border-bottom:none; }
.ma-suggest:hover { background:${T.surface2}; }

/* ═══════════════════════════════════════════
   METRIC CARD
═══════════════════════════════════════════ */
.ma-metric {
  padding:18px 20px;
  background:${T.surface};
  border:1px solid ${T.border};
  border-radius:12px;
  transition:border-color 0.15s, transform 0.15s;
  position:relative; overflow:hidden;
}
.ma-metric::after {
  content:''; position:absolute; inset:0;
  background:linear-gradient(135deg, ${T.isDark ? "rgba(255,255,255,0.01)" : "rgba(255,255,255,0.5)"} 0%, transparent 60%);
  pointer-events:none;
}
.ma-metric:hover { border-color:${T.accent}30; transform:translateY(-1px); }

/* ═══════════════════════════════════════════
   RISK BAR
═══════════════════════════════════════════ */
.ma-risk-bg  { height:4px; background:${T.surface3}; border-radius:2px; overflow:hidden; margin-top:5px; }
.ma-risk-fill { height:100%; border-radius:2px; animation:progressFill 1s cubic-bezier(0.4,0,0.2,1) forwards; }

/* ═══════════════════════════════════════════
   ORGAN SCORE
═══════════════════════════════════════════ */
.ma-organ {
  border-radius:8px; padding:12px 8px; text-align:center;
  border:1px solid ${T.border}; background:${T.surface2};
  transition:border-color 0.15s, transform 0.15s;
}
.ma-organ:hover { border-color:${T.accent}28; transform:scale(1.03); }

/* ═══════════════════════════════════════════
   FEATURE CARD (empty state)
═══════════════════════════════════════════ */
.ma-feature {
  background:${T.surface};
  border:1px solid ${T.border};
  border-radius:10px; padding:20px 16px; text-align:center;
  transition:border-color 0.15s, transform 0.15s; cursor:pointer;
}
.ma-feature:hover { border-color:${T.accent}30; transform:translateY(-2px); }

/* ═══════════════════════════════════════════
   SPECIALIST CARD
═══════════════════════════════════════════ */
.ma-spec {
  border:1px solid ${T.border}; border-radius:10px; padding:16px;
  cursor:pointer; transition:border-color 0.15s, transform 0.15s; background:${T.surface};
}
.ma-spec:hover { border-color:${T.accent}30; transform:translateY(-1px); }

/* ═══════════════════════════════════════════
   TABLE — theme-aware, overrides globals.css
═══════════════════════════════════════════ */
.ma-table {
  width:100%; border-collapse:separate; border-spacing:0;
  overflow:hidden;
}
.ma-table thead tr {
  background:${T.surface2};
}
.ma-table th {
  font-size:11px; font-weight:700; letter-spacing:0.08em;
  text-transform:uppercase; color:${T.textMuted};
  padding:11px 18px; text-align:left;
  background:${T.surface2};
  border-bottom:1px solid ${T.border};
}
.ma-table td {
  padding:11px 18px; font-size:13.5px;
  border-top:1px solid ${T.border};
  color:${T.text};
  background:${T.surface};
}
.ma-table tbody tr:nth-child(even) td {
  background:${T.surface2};
}
.ma-table tbody tr:hover td {
  background:${T.accent}08 !important;
}
/* Status badge inside table */
.ma-table .lab-status-normal  { color:${T.accent3}; background:${T.accent3}12; border:1px solid ${T.accent3}25; }
.ma-table .lab-status-high    { color:${T.danger};  background:${T.danger}12;  border:1px solid ${T.danger}25; }
.ma-table .lab-status-low     { color:${T.warn};   background:${T.warn}12;   border:1px solid ${T.warn}25; }
.ma-table .lab-status-abnormal{ color:${T.danger};  background:${T.danger}12;  border:1px solid ${T.danger}25; }
.ma-table .lab-status-noted   { color:${T.accent2}; background:${T.accent2}12; border:1px solid ${T.accent2}25; }

/* ═══════════════════════════════════════════
   MH OPTION
═══════════════════════════════════════════ */
.ma-mh-opt {
  padding:8px 14px; border-radius:7px; font-size:12.5px; font-weight:600;
  cursor:pointer; border:1px solid ${T.border};
  background:${T.surface2}; color:${T.textMuted}; transition:all 0.12s;
}
.ma-mh-opt.active { background:${T.accent2}15; border-color:${T.accent2}40; color:${T.accent2}; }

/* ═══════════════════════════════════════════
   TIMELINE
═══════════════════════════════════════════ */
.ma-timeline-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; margin-top:6px; }

/* ═══════════════════════════════════════════
   RECORDING
═══════════════════════════════════════════ */
@keyframes recPulse { 0%,100%{box-shadow:0 0 0 0 ${T.danger}45} 50%{box-shadow:0 0 0 8px transparent} }
.ma-recording-btn { animation:recPulse 1.3s ease-in-out infinite; }

/* ═══════════════════════════════════════════
   SCROLL
═══════════════════════════════════════════ */
.ma-scroll { overflow-y:auto; overflow-x:hidden; scroll-behavior: smooth; overscroll-behavior-y: contain; }

/* ═══════════════════════════════════════════
   THEME TOGGLE
═══════════════════════════════════════════ */
.ma-theme-track {
  width:34px; height:19px; border-radius:99px;
  position:relative; cursor:pointer; transition:background 0.25s; flex-shrink:0;
}
.ma-theme-thumb {
  position:absolute; top:2.5px; width:14px; height:14px;
  border-radius:50%; background:white;
  transition:left 0.25s cubic-bezier(0.4,0,0.2,1);
  box-shadow:0 1px 5px rgba(0,0,0,0.3);
}

/* ═══════════════════════════════════════════
   TOPBAR / CHATINPUT SAFE AREA
═══════════════════════════════════════════ */
@media (max-width:768px) {
  .ma-topbar { height:calc(52px + var(--sat)) !important; padding-top:calc(8px + var(--sat)) !important; }
  .ma-chatinput { padding-bottom:calc(14px + var(--sab)) !important; }
}

/* ═══════════════════════════════════════════
   RESPONSIVE GRIDS
═══════════════════════════════════════════ */
@media (max-width:640px) {
  .ma-stats-grid    { grid-template-columns:repeat(2,1fr) !important; }
  .ma-score-grid    { grid-template-columns:1fr !important; }
  .ma-tools-grid    { grid-template-columns:repeat(2,1fr) !important; }
  .ma-bodymap-grid  { grid-template-columns:1fr !important; }
  .ma-organ-grid    { grid-template-columns:repeat(2,1fr) !important; }
  .ma-feature-grid  { grid-template-columns:repeat(2,1fr) !important; }
  .ma-metric-num    { font-size:22px !important; }
  .ma-score-wrap    { flex-direction:column !important; align-items:center !important; }
}
@media (max-width:400px) {
  .ma-tools-grid  { grid-template-columns:1fr !important; }
  .ma-feature-grid{ grid-template-columns:1fr !important; }
}

/* ═══════════════════════════════════════════════════════════
   NEW PRODUCTION FEATURES
═══════════════════════════════════════════════════════════ */

/* ── Message actions (copy, etc.) ── */
.ma-msg-actions {
  display:flex; gap:5px; margin-top:8px;
  opacity:0; transition:opacity 0.15s;
}
.ma-msg-wrap:hover .ma-msg-actions { opacity:1; }

/* ── Citations panel ── */
@keyframes citationSlideIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
.ma-citations {
  animation: citationSlideIn 0.3s cubic-bezier(0.16,1,0.3,1) both;
  border-left: 3px solid ${T.accent};
}

/* ── Quick symptom chips ── */
.ma-symptom-chip {
  padding:5px 12px; border-radius:99px; font-size:12px; font-weight:600;
  cursor:pointer; transition:all 0.15s; white-space:nowrap;
  border:1px solid transparent; font-family:'DM Sans',sans-serif;
}

/* ── Vitals quick log ── */
.ma-vitals-grid { display:grid; grid-template-columns:1fr 1fr; gap:9px; }
@media(max-width:480px){ .ma-vitals-grid { grid-template-columns:1fr; } }

/* ── Emergency card ── */
@keyframes emergencyPulse { 0%,100%{box-shadow:0 0 0 0 rgba(255,77,109,0.4)} 50%{box-shadow:0 0 0 6px transparent} }
.ma-emergency-card { animation: emergencyPulse 2.5s ease-in-out infinite; }

/* ── Export menu ── */
.ma-export-menu {
  position:absolute; right:0; bottom:calc(100% + 6px);
  min-width:180px; z-index:200;
}

/* ═══════════════════════════════════════════════════════════
   SENIOR MODE — larger fonts, bigger taps, high contrast
═══════════════════════════════════════════════════════════ */
.senior-mode {
  font-size: 18px !important;
}
.senior-mode .ma-btn {
  padding: 14px 24px !important;
  font-size: 17px !important;
  border-radius: 14px !important;
  min-height: 54px !important;
  font-weight: 700 !important;
}
.senior-mode .ma-btn-icon {
  padding: 14px !important;
  min-height: 54px !important;
  min-width: 54px !important;
}
.senior-mode .ma-btn-sm {
  padding: 10px 18px !important;
  font-size: 15px !important;
  min-height: 46px !important;
}
.senior-mode .ma-input {
  padding: 14px 18px !important;
  font-size: 17px !important;
  border-radius: 12px !important;
  border-width: 2px !important;
  min-height: 54px !important;
}
.senior-mode textarea.ma-input {
  min-height: 60px !important;
  font-size: 17px !important;
}
.senior-mode .ma-nav-item {
  padding: 14px 16px !important;
  font-size: 17px !important;
  min-height: 54px !important;
  gap: 14px !important;
}
.senior-mode .ma-session {
  padding: 14px 16px !important;
}
.senior-mode .ma-card {
  border-radius: 16px !important;
}
.senior-mode .ma-topbar {
  height: 68px !important;
}
@keyframes seniorPulse {
  0%,100%{box-shadow: 0 0 0 0 var(--senior-glow,rgba(0,212,255,0.4))}
  50%{box-shadow: 0 0 0 8px transparent}
}
.senior-mic-btn {
  animation: seniorPulse 2s ease-in-out infinite;
}

/* ═══════════════════════════════════════════
   PREMIUM UI UPGRADES
═══════════════════════════════════════════ */
.ma-card {
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}
.ma-topbar {
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}
.ma-chatinput {
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
}
.ma-msg-wrap {
  transition: transform 0.15s ease;
}
.ma-msg-wrap:hover {
  transform: translateY(-1px);
}
.ma-input:focus {
  border-color: ${T.accent}70 !important;
  box-shadow: 0 0 0 3px ${T.accent}14, 0 2px 8px ${T.accent}10 !important;
}
.ma-avatar {
  width: 34px; height: 34px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 800;
  background: ${T.accent}18; color: ${T.accent};
  border: 1px solid ${T.accent}28; flex-shrink: 0;
}
@keyframes scaleIn {
  from{ opacity:0; transform:scale(0.94) translateY(-4px); }
  to  { opacity:1; transform:scale(1)    translateY(0); }
}
.scale-in { animation: scaleIn 0.18s cubic-bezier(0.16,1,0.3,1) both; }
.ma-pill-tab {
  padding: 6px 14px; border-radius: 8px; font-size: 12.5px; font-weight: 600;
  cursor: pointer; transition: all 0.15s; border: 1px solid transparent;
  color: ${T.textMuted}; font-family: 'DM Sans', sans-serif; background: transparent;
}
.ma-pill-tab.active { background: ${T.accent}14; color: ${T.accent}; border-color: ${T.accent}28; }
.ma-pill-tab:not(.active):hover { background: ${T.surface2}; color: ${T.text}; }
.lab-val-high { color: ${T.danger} !important; }
.lab-val-low  { color: ${T.warn}  !important; }
.lab-val-norm { color: ${T.accent3} !important; }
`;
}

/* ═══════════════════════════════════════════════════════════
   ROBOT DOCTOR COMPONENT
═══════════════════════════════════════════════════════════ */
const RobotDoc = memo(function RobotDoc({ isThinking, T, size = 54 }) {
  return (
    <div style={{ position: "relative", display: "inline-flex", alignItems: "center", justifyContent: "center", width: size, height: size * 1.18 }}>
      <svg width={size} height={size * 1.18} viewBox="0 0 54 64" fill="none" xmlns="http://www.w3.org/2000/svg"
        className={isThinking ? "robot-float robot-think robot-glow" : ""}
        style={{ filter: `drop-shadow(0 6px 20px ${T.robotGlow})`, display: "block" }}>
        {/* Legs */}
        <rect x="20" y="55" width="6" height="7" rx="3" fill={T.robotSkin} opacity="0.8" />
        <rect x="28" y="55" width="6" height="7" rx="3" fill={T.robotSkin} opacity="0.8" />
        {/* Body — white doctor coat */}
        <rect x="12" y="40" width="30" height="17" rx="7" fill={T.isDark ? "#e8edf5" : "#ffffff"} stroke={T.accent} strokeWidth="0.7" strokeOpacity="0.4" />
        {/* Coat shadow/depth */}
        <rect x="12" y="40" width="30" height="17" rx="7" fill="url(#coatGrad)" opacity="0.15" />
        <defs>
          <linearGradient id="coatGrad" x1="12" y1="40" x2="12" y2="57" gradientUnits="userSpaceOnUse">
            <stop offset="0" stopColor={T.accent} stopOpacity="0.1" />
            <stop offset="1" stopColor="#000" stopOpacity="0.08" />
          </linearGradient>
        </defs>
        {/* Doctor coat lapel lines */}
        <line x1="27" y1="40" x2="27" y2="53" stroke={T.accent} strokeWidth="0.5" strokeOpacity="0.25" />
        <line x1="22" y1="40" x2="24" y2="45" stroke={T.accent} strokeWidth="0.4" strokeOpacity="0.2" />
        <line x1="32" y1="40" x2="30" y2="45" stroke={T.accent} strokeWidth="0.4" strokeOpacity="0.2" />
        {/* Medical cross on chest */}
        <rect x="25" y="44" width="4" height="8" rx="1" fill={T.accent3} opacity="0.7" />
        <rect x="23" y="46" width="8" height="4" rx="1" fill={T.accent3} opacity="0.7" />
        {/* Stethoscope */}
        <path d="M14 44 Q8 44 8 50 Q8 56 14 56 Q16 56 17 54"
          stroke={T.accent} strokeWidth="1.2" strokeLinecap="round" fill="none" opacity="0.7" />
        <circle cx="14" cy="56" r="2" fill={T.accent} opacity="0.6">
          {isThinking && <animate attributeName="opacity" values="0.3;0.9;0.3" dur="1.5s" repeatCount="indefinite" />}
        </circle>
        <path d="M40 44 Q46 44 46 50 Q46 56 40 56 Q38 56 37 54"
          stroke={T.accent} strokeWidth="1.2" strokeLinecap="round" fill="none" opacity="0.7" />
        <circle cx="40" cy="56" r="2" fill={T.accent} opacity="0.6" />
        {/* Arms — white coat sleeves */}
        <rect x="3" y="43" width="10" height="5" rx="2.5" fill={T.isDark ? "#dce3ef" : "#f0f3f9"} stroke={T.accent} strokeWidth="0.4" strokeOpacity="0.35" />
        <rect x="41" y="43" width="10" height="5" rx="2.5" fill={T.isDark ? "#dce3ef" : "#f0f3f9"} stroke={T.accent} strokeWidth="0.4" strokeOpacity="0.35" />
        {/* Neck */}
        <rect x="22" y="36" width="10" height="5" rx="3" fill={T.robotSkin} />
        {/* Head */}
        <rect x="9" y="7" width="36" height="31" rx="11" fill={T.robotSkin} stroke={T.accent} strokeWidth="0.9" strokeOpacity="0.55" />
        {/* Head mirror (doctor forehead reflector) */}
        <circle cx="27" cy="5" r="4" fill={T.accent} opacity="0.15" />
        <circle cx="27" cy="5" r="2.5" fill={T.accent} opacity="0.35">
          {isThinking && <animate attributeName="opacity" values="0.2;0.55;0.2" dur="1.8s" repeatCount="indefinite" />}
        </circle>
        <line x1="24" y1="3" x2="30" y2="3" stroke={T.accent} strokeWidth="1" strokeLinecap="round" opacity="0.4" />
        {/* Scan line (thinking) */}
        <rect x="9" y="-2" width="36" height="2" rx="1" fill={T.accent} opacity="0.3" className="scan-line" style={{ display: "none" }} />
        {/* Ear sensors */}
        <circle cx="9" cy="22" r="2" fill={T.accent} opacity="0.4" />
        <circle cx="45" cy="22" r="2" fill={T.accent} opacity="0.4" />
        {/* Eyes */}
        <rect x="15" y="16" width="10" height="8" rx="4" fill={isThinking ? T.accent : T.accent2} opacity="0.9" className="eye-rect">
          {isThinking && <animate attributeName="width" values="10;7;10" dur="0.7s" repeatCount="indefinite" />}
        </rect>
        <rect x="29" y="16" width="10" height="8" rx="4" fill={isThinking ? T.accent : T.accent2} opacity="0.9" className="eye-rect">
          {isThinking && <animate attributeName="width" values="10;7;10" dur="0.7s" repeatCount="indefinite" />}
        </rect>
        {/* Eye shine */}
        {isThinking && <>
          <rect x="14" y="15" width="12" height="10" rx="5" fill={T.accent} opacity="0.15" />
          <rect x="28" y="15" width="12" height="10" rx="5" fill={T.accent} opacity="0.15" />
        </>}
        {/* Pupils */}
        <circle cx="20" cy="20" r="2" fill="white" opacity="0.95" />
        <circle cx="34" cy="20" r="2" fill="white" opacity="0.95" />
        {/* Highlight on pupils */}
        <circle cx="21" cy="19" r="0.7" fill="white" opacity="0.7" />
        <circle cx="35" cy="19" r="0.7" fill="white" opacity="0.7" />
        {/* Friendly smile */}
        <path d={isThinking ? "M19 30 Q27 34 35 30" : "M19 30 Q27 26 35 30"}
          stroke={T.accent} strokeWidth="1.8" strokeLinecap="round" fill="none"
          style={{ transition: "d 0.45s" }} />
        {/* Cheek dots */}
        <circle cx="15" cy="27" r="1.5" fill={T.danger} opacity="0.35" />
        <circle cx="39" cy="27" r="1.5" fill={T.danger} opacity="0.35" />
        {/* Brain circuit overlay when thinking */}
        {isThinking && (
          <g opacity="0.45">
            <path d="M16 12 Q18 8 22 9 Q23 7 27 8 Q31 7 32 9 Q36 8 38 12 Q39 16 37 18 Q38 22 35 22 Q34 24 31 23 Q29 25 27 24 Q25 25 23 24 Q20 22 21 22 Q19 18 15 18 Q15 16 16 12Z"
              fill="none" stroke={T.accent} strokeWidth="0.7" />
            <circle cx="27" cy="16" r="1.5" fill={T.accent} opacity="0.6">
              <animate attributeName="opacity" values="0.3;1;0.3" dur="1.2s" repeatCount="indefinite" />
            </circle>
          </g>
        )}
      </svg>
      {/* Thinking bubbles */}
      {isThinking && (
        <div style={{ position: "absolute", top: -10, right: -14, display: "flex", gap: 3, alignItems: "flex-end" }}>
          <div className="think-dot-1" style={{ width: 7, height: 7, borderRadius: "50%", background: T.accent, opacity: 0.75 }} />
          <div className="think-dot-2" style={{ width: 9, height: 9, borderRadius: "50%", background: T.accent, opacity: 0.75 }} />
          <div className="think-dot-3" style={{ width: 11, height: 11, borderRadius: "50%", background: T.accent, opacity: 0.75 }} />
        </div>
      )}
    </div>
  );
});

/* ═══════════════════════════════════════════════════════════
   SCORE RING COMPONENT
═══════════════════════════════════════════════════════════ */
const ScoreRing = memo(function ScoreRing({ score, size = 100, T }) {
  const r = (size - 14) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 80 ? T.accent3 : score >= 60 ? T.warn : T.danger;
  return (
    <svg width={size} height={size} style={{ transform: "rotate(-90deg)", flexShrink: 0 }}
      viewBox={`0 0 ${size} ${size}`}>
      <style>{`
        .sr-path-${size}{
          --circ:${circ};
          --ring-full:${circ};
          stroke-dasharray:${circ};
          stroke-dashoffset:${circ};
          animation:ringGrow 1.6s cubic-bezier(0.4,0,0.2,1) forwards 0.2s;
          --ring-offset:${offset};
        }
        @keyframes ringGrow${size}{from{stroke-dashoffset:${circ}}to{stroke-dashoffset:${offset}}}
      `}</style>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none"
        stroke={T.isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.07)"} strokeWidth="10" />
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth="10"
        strokeLinecap="round"
        style={{ strokeDasharray: circ, strokeDashoffset: circ, animation: `ringGrow${size} 1.6s cubic-bezier(0.4,0,0.2,1) forwards 0.2s`, filter: `drop-shadow(0 0 12px ${color}80)` }} />
      <text x={size / 2} y={size / 2} textAnchor="middle" dominantBaseline="central"
        fill={color} fontSize={size > 90 ? "20" : "16"} fontWeight="800"
        fontFamily="'Fira Code',monospace"
        style={{ transform: `rotate(90deg)`, transformOrigin: `${size / 2}px ${size / 2}px` }}>
        {score}
      </text>
    </svg>
  );
});

/* ═══════════════════════════════════════════════════════════
   STATUS DOT
═══════════════════════════════════════════════════════════ */
const StatusDot = memo(function StatusDot({ status, T }) {
  const colors = { normal: T.accent3, high: T.danger, abnormal: T.danger, low: T.warn, noted: T.accent2 };
  return (
    <span style={{
      display: "inline-block", width: 8, height: 8, borderRadius: "50%",
      background: colors[status] || T.textMuted, flexShrink: 0,
      boxShadow: `0 0 6px ${colors[status] || T.textMuted}80`
    }} />
  );
});

/* ═══════════════════════════════════════════════════════════
   REAL VOICE VISUALIZER
   Driven purely by live audioLevel (0–1) from the analyser node.
   No CSS animation, no Math.sin fake flow — every bar height is
   computed from the real frequency spectrum.
═══════════════════════════════════════════════════════════ */
const NUM_BARS = 40;

// Per-bar multiplier — taller in centre, shorter at edges (natural voice shape)
const BAR_ENVELOPE = Array.from({ length: NUM_BARS }, (_, i) => {
  const x = (i / (NUM_BARS - 1)) * 2 - 1; // -1 to +1
  return 0.35 + 0.65 * Math.exp(-x * x * 2.2);
});

const VoiceVisualizer = memo(function VoiceVisualizer({ analyserRef, isRecording, T }) {
  const canvasRef = useRef(null);
  const rafRef = useRef(null);

  useEffect(() => {
    if (!isRecording) {
      cancelAnimationFrame(rafRef.current);
      // Draw flat idle state
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const w = canvas.width, h = canvas.height;
      const barW = Math.floor(w / NUM_BARS) - 1;
      for (let i = 0; i < NUM_BARS; i++) {
        const x = i * (barW + 1);
        const barH = 3;
        ctx.fillStyle = T.isDark ? "rgba(255,255,255,0.12)" : "rgba(0,0,0,0.1)";
        ctx.beginPath();
        ctx.roundRect(x, (h - barH) / 2, barW, barH, 2);
        ctx.fill();
      }
      return;
    }

    const draw = () => {
      const canvas = canvasRef.current;
      const analyser = analyserRef.current;
      if (!canvas || !analyser) return;

      const ctx = canvas.getContext("2d");
      const w = canvas.width, h = canvas.height;
      const bufLen = analyser.frequencyBinCount;
      const data = new Uint8Array(bufLen);
      analyser.getByteFrequencyData(data);

      ctx.clearRect(0, 0, w, h);

      const barW = Math.floor(w / NUM_BARS) - 1;
      const step = Math.floor(bufLen / NUM_BARS);
      const accent = T.accent;

      for (let i = 0; i < NUM_BARS; i++) {
        // Average a small band of frequency bins for this bar
        let sum = 0;
        for (let j = 0; j < step; j++) sum += data[i * step + j] || 0;
        const raw = (sum / step) / 255;          // 0–1 raw level
        const level = Math.min(1, raw * 1.6);      // boost quiet voices
        const env = BAR_ENVELOPE[i];             // centre-weighted envelope
        const barH = Math.max(3, level * env * (h - 6));

        const x = i * (barW + 1);
        const y = (h - barH) / 2;

        // Gradient: accent colour at peak, muted at base
        const grad = ctx.createLinearGradient(0, y, 0, y + barH);
        grad.addColorStop(0, accent + "ff");
        grad.addColorStop(0.5, accent + "cc");
        grad.addColorStop(1, accent + "44");
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.roundRect(x, y, barW, barH, 2);
        ctx.fill();
      }
      rafRef.current = requestAnimationFrame(draw);
    };
    draw();
    return () => cancelAnimationFrame(rafRef.current);
  }, [isRecording, analyserRef, T]);

  return (
    <canvas
      ref={canvasRef}
      width={320}
      height={56}
      style={{ width: "100%", height: 56, display: "block" }}
    />
  );
});

/* ═══════════════════════════════════════════════════════════
   TOOL HEADER
═══════════════════════════════════════════════════════════ */
/* ═══════════════════════════════════════════════════════════
   AUDIO PLAYER — for TTS responses
   Play / Pause / Stop / Replay + live progress bar
═══════════════════════════════════════════════════════════ */
const AudioPlayer = memo(function AudioPlayer({ audioUrl, T }) {
  const audioRef = useRef(null);
  const [state, setState] = useState("idle");   // idle | playing | paused | ended
  const [progress, setProgress] = useState(0);        // 0–100
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentT] = useState(0);

  useEffect(() => {
    const a = new Audio(audioUrl);
    audioRef.current = a;
    a.onloadedmetadata = () => setDuration(a.duration);
    a.ontimeupdate = () => {
      setCurrentT(a.currentTime);
      setProgress(a.duration ? (a.currentTime / a.duration) * 100 : 0);
    };
    a.onended = () => { setState("ended"); setProgress(100); };
    return () => { a.pause(); a.src = ""; };
  }, [audioUrl]);

  const play = () => { audioRef.current?.play(); setState("playing"); };
  const pause = () => { audioRef.current?.pause(); setState("paused"); };
  const stop = () => { const a = audioRef.current; if (!a) return; a.pause(); a.currentTime = 0; setState("idle"); setProgress(0); };
  const replay = () => { const a = audioRef.current; if (!a) return; a.currentTime = 0; a.play(); setState("playing"); };
  const seek = (e) => {
    const a = audioRef.current; if (!a || !duration) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const pct = (e.clientX - rect.left) / rect.width;
    a.currentTime = pct * duration;
    setProgress(pct * 100);
  };

  const fmt = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;

  const isPlaying = state === "playing";

  return (
    <div style={{
      marginTop: 10,
      padding: "10px 14px",
      borderRadius: 11,
      background: `${T.accent}0d`,
      border: `1px solid ${T.accent}22`,
      display: "flex", flexDirection: "column", gap: 8,
    }}>
      {/* Controls row */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <Volume2 size={14} style={{ color: T.accent, flexShrink: 0 }} />
        <span style={{ fontSize: 11.5, fontWeight: 700, color: T.accent, letterSpacing: "0.05em", textTransform: "uppercase" }}>
          AI Voice Response
        </span>
        <div style={{ marginLeft: "auto", display: "flex", gap: 5 }}>
          {/* Play / Pause */}
          <button
            onClick={isPlaying ? pause : play}
            style={{
              width: 30, height: 30, borderRadius: 8,
              background: T.accent, border: "none", cursor: "pointer",
              display: "flex", alignItems: "center", justifyContent: "center",
              boxShadow: `0 2px 10px ${T.accent}40`,
              transition: "transform 0.12s",
            }}
            onMouseEnter={e => e.currentTarget.style.transform = "scale(1.1)"}
            onMouseLeave={e => e.currentTarget.style.transform = "scale(1)"}>
            {isPlaying
              ? <Pause size={13} color={T.isDark ? "#000" : "#fff"} />
              : <Play size={13} color={T.isDark ? "#000" : "#fff"} style={{ marginLeft: 1 }} />}
          </button>
          {/* Stop */}
          <button
            onClick={stop}
            disabled={state === "idle"}
            style={{
              width: 30, height: 30, borderRadius: 8,
              background: `${T.danger}18`, border: `1px solid ${T.danger}30`,
              cursor: state === "idle" ? "default" : "pointer",
              display: "flex", alignItems: "center", justifyContent: "center",
              opacity: state === "idle" ? 0.4 : 1, transition: "all 0.12s",
            }}>
            <Square size={11} style={{ color: T.danger }} />
          </button>
          {/* Replay */}
          <button
            onClick={replay}
            style={{
              width: 30, height: 30, borderRadius: 8,
              background: T.surface2, border: `1px solid ${T.border}`,
              cursor: "pointer",
              display: "flex", alignItems: "center", justifyContent: "center",
              transition: "all 0.12s",
            }}
            onMouseEnter={e => e.currentTarget.style.borderColor = T.accent}
            onMouseLeave={e => e.currentTarget.style.borderColor = T.border}>
            <RotateCcw size={12} style={{ color: T.textSub }} />
          </button>
        </div>
      </div>

      {/* Progress bar */}
      <div
        onClick={seek}
        style={{
          height: 4, borderRadius: 99, background: T.surface3,
          cursor: "pointer", position: "relative", overflow: "hidden",
        }}>
        <div style={{
          height: "100%", borderRadius: 99,
          width: `${progress}%`,
          background: `linear-gradient(90deg, ${T.accent}, ${T.accent2})`,
          transition: "width 0.1s linear",
        }} />
      </div>

      {/* Time */}
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10.5, color: T.textMuted, fontFamily: "'Fira Code',monospace" }}>
        <span>{fmt(currentTime)}</span>
        <span>{duration ? fmt(duration) : "--:--"}</span>
      </div>
    </div>
  );
});

const ToolHeader = memo(function ToolHeader({ title, icon: Icon, accent, T, onClose }) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 13 }}>
        <div style={{
          width: 44, height: 44, borderRadius: 13,
          background: `linear-gradient(135deg,${accent}28,${accent}12)`,
          border: `1.5px solid ${accent}35`,
          display: "flex", alignItems: "center", justifyContent: "center",
          boxShadow: `0 4px 16px ${accent}25`,
        }}>
          <Icon size={20} style={{ color: accent }} />
        </div>
        <div>
          <div style={{ fontSize: 17, fontWeight: 800, color: T.text, fontFamily: "'DM Sans',sans-serif", letterSpacing: "-0.02em" }}>{title}</div>
        </div>
      </div>
      <button onClick={onClose} className="ma-btn ma-btn-ghost ma-btn-icon">
        <X size={15} />
      </button>
    </div>
  );
});

/* ═══════════════════════════════════════════════════════════
   GLASS CARD
═══════════════════════════════════════════════════════════ */
const GCard = ({ children, style = {}, className = "", glow = false }) => (
  <div className={`ma-card ${glow ? "ma-card-accent" : ""} fade-up ${className}`} style={{ padding: 22, ...style }}>
    {children}
  </div>
);

/* ═══════════════════════════════════════════════════════════
   FORMAT TEXT
═══════════════════════════════════════════════════════════ */
/* ═══════════════════════════════════════════════════════════
   ADVANCED LLM TEXT FORMATTER (Markdown Simulation)
═══════════════════════════════════════════════════════════ */
function formatText(text, accentColor) {
  if (!text) return null;

  // Split into paragraphs first
  const blocks = text.split(/\n\n+/).filter(Boolean);

  return blocks.map((block, bIdx) => {
    // Check if it's a list
    if (block.match(/^[-*]\s/m)) {
      const items = block.split(/\n/).filter(line => line.trim().length > 0);
      return (
        <ul key={`b-${bIdx}`} style={{ margin: "12px 0", paddingLeft: 24, listStyleType: "none" }}>
          {items.map((item, iOffset) => {
            let lineText = item.replace(/^[-*]\s+/, "");
            return (
              <li key={iOffset} style={{ marginBottom: 6, position: "relative" }}>
                <span style={{ position: "absolute", left: -16, color: accentColor }}>•</span>
                {formatInline(lineText, accentColor)}
              </li>
            );
          })}
        </ul>
      );
    }

    // Check if header
    if (block.match(/^###\s/)) {
      return <h3 key={`b-${bIdx}`} style={{ marginTop: 24, marginBottom: 12, fontSize: 16, fontWeight: 700, color: "inherit" }}>{formatInline(block.replace(/^###\s+/, ""), accentColor)}</h3>;
    }
    if (block.match(/^##\s/)) {
      return <h2 key={`b-${bIdx}`} style={{ marginTop: 28, marginBottom: 14, fontSize: 18, fontWeight: 800, color: "inherit" }}>{formatInline(block.replace(/^##\s+/, ""), accentColor)}</h2>;
    }

    // Fallback paragraph
    return (
      <p key={`b-${bIdx}`} style={{ margin: "0 0 14px 0", lineHeight: 1.7 }}>
        {formatInline(block, accentColor)}
      </p>
    );
  });
}

function formatInline(str, accentColor) {
  // Bold parser
  const parts = str.split(/(\*\*[^*]+\*\*)/);
  let elements = parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i} style={{ color: accentColor, fontWeight: 600 }}>{part.slice(2, -2)}</strong>;
    }
    return part;
  });

  // Single newlines
  let finalElements = [];
  elements.forEach((el, index) => {
    if (typeof el === "string") {
      const subParts = el.split("\n");
      subParts.forEach((sp, spi) => {
        finalElements.push(sp);
        if (spi < subParts.length - 1) finalElements.push(<br key={`br-${index}-${spi}`} />);
      });
    } else {
      finalElements.push(el);
    }
  });

  return finalElements;
}

/* ═══════════════════════════════════════════════════════════
   PARTICLE FIELD (background decoration)
═══════════════════════════════════════════════════════════ */
/* Deterministic pseudo-random — same on server and client, no hydration mismatch */
function seededRand(seed) {
  let s = seed;
  return () => { s = (s * 16807 + 0) % 2147483647; return (s - 1) / 2147483646; };
}

const PARTICLES = (() => {
  const r = seededRand(42);
  return Array.from({ length: 22 }, (_, i) => ({
    id: i,
    x: r() * 100, y: r() * 100,
    size: 1 + r() * 2.5,
    dur: 6 + r() * 10,
    delay: r() * 8,
    opacity: 0.12 + r() * 0.2,
  }));
})();

const ParticleField = memo(function ParticleField({ T }) {
  const particles = PARTICLES;
  return (
    <div style={{ position: "fixed", inset: 0, pointerEvents: "none", zIndex: 0, overflow: "hidden" }}>
      {particles.map(p => (
        <div key={p.id} style={{
          position: "absolute",
          left: `${p.x}%`, top: `${p.y}%`,
          width: p.size, height: p.size,
          borderRadius: "50%",
          background: T.accent,
          opacity: p.opacity,
          animation: `float ${p.dur}s ease-in-out ${p.delay}s infinite`,
        }} />
      ))}
      {/* Floating DNA strands */}
      <svg style={{ position: "absolute", top: "10%", right: "5%", opacity: T.isDark ? 0.04 : 0.06, pointerEvents: "none" }} width="120" height="300" viewBox="0 0 120 300">
        {Array.from({ length: 15 }, (_, i) => {
          const y = i * 20; const x1 = 20 + Math.sin(i * 0.7) * 40; const x2 = 100 - Math.sin(i * 0.7) * 40;
          return (
            <g key={i}>
              <line x1={x1} y1={y} x2={x2} y2={y} stroke={T.accent} strokeWidth="1" />
              <circle cx={x1} cy={y} r="3" fill={T.accent} />
              <circle cx={x2} cy={y} r="3" fill={T.accent2} />
            </g>
          );
        })}
        <path d={Array.from({ length: 30 }, (_, i) => `${i === 0 ? "M" : "L"} ${20 + Math.sin(i * 0.7) * 40} ${i * 10}`).join(" ")}
          fill="none" stroke={T.accent} strokeWidth="1.5" strokeOpacity="0.7" />
        <path d={Array.from({ length: 30 }, (_, i) => `${i === 0 ? "M" : "L"} ${100 - Math.sin(i * 0.7) * 40} ${i * 10}`).join(" ")}
          fill="none" stroke={T.accent2} strokeWidth="1.5" strokeOpacity="0.7" />
      </svg>
      {/* Corner hex pattern */}
      <svg style={{ position: "absolute", bottom: "8%", left: "2%", opacity: T.isDark ? 0.03 : 0.05, pointerEvents: "none" }} width="200" height="200" viewBox="0 0 200 200">
        {Array.from({ length: 7 }, (_, row) => Array.from({ length: 7 }, (_, col) => {
          const x = col * 28 + (row % 2) * 14; const y = row * 24;
          const hex = `M${x + 14},${y} L${x + 28},${y + 8} L${x + 28},${y + 24} L${x + 14},${y + 32} L${x},${y + 24} L${x},${y + 8} Z`;
          return <path key={`${row}-${col}`} d={hex} fill="none" stroke={T.accent} strokeWidth="0.8" />;
        })).flat()}
      </svg>
    </div>
  );
});

/* ═══════════════════════════════════════════════════════════
   MAIN COMPONENT
═══════════════════════════════════════════════════════════ */
export default function EnhancedMedicalChat() {

  /* ── Theme ── */
  const [isDark, setIsDark] = useState(true);
  const [accentKey, setAccentKey] = useState("cyan");
  const [seniorMode, setSeniorMode] = useState(false);
  const T = useMemo(() => buildTheme(isDark, accentKey), [isDark, accentKey]);

  /* ── Core ── */
  const [tab, setTab] = useState("chat");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [patientId, setPatientId] = useState("");
  const [sessionId, setSessionId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [triageInfo, setTriageInfo] = useState(null);
  const [audioLevel, setAudioLevel] = useState(0);

  /* ── Patient ── */
  const [showPatientForm, setShowPatientForm] = useState(false);
  const [showPatientList, setShowPatientList] = useState(false);
  const [tempPatientId, setTempPatientId] = useState("");
  const [patientInfo, setPatientInfo] = useState({
    name: "", age: "", gender: "", blood_group: "",
    allergies: "", chronic_conditions: "", ethnicity: "", family_history: ""
  });

  /* ── Dashboard ── */
  const [labResults, setLabResults] = useState([]);
  const [medImages, setMedImages] = useState([]);
  const [bodyMapData, setBodyMapData] = useState({});
  const [selectedRegion, setSelectedRegion] = useState(null);
  const [regionImages, setRegionImages] = useState({});
  const [regionImageHistory, setRegionImageHistory] = useState({});
  const [uploadDate, setUploadDate] = useState("");

  /* ── Voice ── */
  const [voiceLang, setVoiceLang] = useState(null);
  const [showLangPicker, setShowLangPicker] = useState(false);

  /* ── Health Score ── */
  const [healthScore, setHealthScore] = useState(null);
  const [hsLoading, setHsLoading] = useState(false);

  /* ── Symptom Checker ── */
  const [showSymptomChecker, setShowSymptomChecker] = useState(false);
  const [symptomInput, setSymptomInput] = useState("");
  const [symptomTags, setSymptomTags] = useState([]);
  const [symptomResult, setSymptomResult] = useState(null);
  const [symptomLoading, setSymptomLoading] = useState(false);

  /* ── Drug Interactions ── */
  const [showDrugChecker, setShowDrugChecker] = useState(false);
  const [drugInput, setDrugInput] = useState("");
  const [drugTags, setDrugTags] = useState([]);
  const [drugResult, setDrugResult] = useState(null);
  const [drugLoading, setDrugLoading] = useState(false);
  const [drugSuggestions, setDrugSuggestions] = useState([]);
  const [medSuggestions, setMedSuggestions] = useState([]);

  /* ── Mental Health ── */
  const [showMentalHealth, setShowMentalHealth] = useState(false);
  const [mentalType, setMentalType] = useState("phq9");
  const [mentalAnswers, setMentalAnswers] = useState([]);
  const [mentalResult, setMentalResult] = useState(null);

  /* ── Report ── */
  const [reportData, setReportData] = useState(null);
  const [reportLoading, setReportLoading] = useState(false);

  /* ── Settings ── */
  const [showSettingsMenu, setShowSettingsMenu] = useState(false);

  /* ── Lab Entry ── */
  const [showLabEntry, setShowLabEntry] = useState(false);
  const [labCatalog, setLabCatalog] = useState([]);
  const [labSearch, setLabSearch] = useState("");
  const [labSuggestions, setLabSuggestions] = useState([]);
  const [selectedLabTest, setSelectedLabTest] = useState(null);
  const [labValue, setLabValue] = useState("");
  const [labDate, setLabDate] = useState("");

  /* ── Analytics ── */
  const [riskData, setRiskData] = useState(null);
  const [riskLoading, setRiskLoading] = useState(false);
  const [organData, setOrganData] = useState(null);
  const [organLoading, setOrganLoading] = useState(false);
  const [trendsData, setTrendsData] = useState(null);
  const [trendsLoading, setTrendsLoading] = useState(false);
  const [labIntel, setLabIntel] = useState(null);
  const [labIntelLoading, setLabIntelLoading] = useState(false);

  /* ── Health Trajectory (Predictive) ── */
  const [trajectory, setTrajectory] = useState(null);
  const [trajectoryLoading, setTrajectoryLoading] = useState(false);

  /* ── Medications ── */
  const [medications, setMedications] = useState([]);
  const [showMedForm, setShowMedForm] = useState(false);
  const [showMedTracker, setShowMedTracker] = useState(false);
  const [medForm, setMedForm] = useState({ name: "", dosage: "", frequency: "Once daily" });

  /* ── Specialists ── */
  const [specialists, setSpecialists] = useState([]);
  const [selectedSpecialist, setSelectedSpecialist] = useState(null);
  const [showSpecialistPanel, setShowSpecialistPanel] = useState(false);

  /* ── Health Coach ── */
  const [coachBriefing, setCoachBriefing] = useState(null);
  const [coachLoading, setCoachLoading] = useState(false);
  const [showCoachPanel, setShowCoachPanel] = useState(false);
  const [lifestyleForm, setLifestyleForm] = useState({ steps: "", distance_km: "", sleep_hours: "", calories: "", water_ml: "" });
  const [showLifestyleForm, setShowLifestyleForm] = useState(false);

  /* ── Screening ── */
  const [screeningPlan, setScreeningPlan] = useState(null);
  const [screeningLoading, setScreeningLoading] = useState(false);
  const [showScreeningPanel, setShowScreeningPanel] = useState(false);
  const [screeningInputs, setScreeningInputs] = useState({ smoker: "", alcohol: "", family_history: "", notes: "" });
  const [showScreeningInputs, setShowScreeningInputs] = useState(false);

  /* ── Treatment Plan ── */
  const [showTreatmentPlan, setShowTreatmentPlan] = useState(false);
  const [treatmentCondition, setTreatmentCondition] = useState("");
  const [treatmentResult, setTreatmentResult] = useState(null);
  const [treatmentLoading, setTreatmentLoading] = useState(false);

  /* ── Symptom Flow ── */
  const [showSymptomFlow, setShowSymptomFlow] = useState(false);
  const [flowSymptom, setFlowSymptom] = useState("");
  const [flowAnswers, setFlowAnswers] = useState({});
  const [flowQuestion, setFlowQuestion] = useState(null);
  const [flowDiagnosis, setFlowDiagnosis] = useState(null);
  const [flowLoading, setFlowLoading] = useState(false);
  const [flowSessionId, setFlowSessionId] = useState(null);

  /* ── UI ── */
  const [genMode, setGenMode] = useState("balanced");
  const [patientList, setPatientList] = useState([]);
  const [canStop, setCanStop] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showAccentPicker, setShowAccentPicker] = useState(false);
  /* ── New production features ── */
  const [citations, setCitations] = useState([]);
  const [showCitations, setShowCitations] = useState(false);
  const [showEmergency, setShowEmergency] = useState(false);
  const [copiedMsgId, setCopiedMsgId] = useState(null);
  const [showVitalsLog, setShowVitalsLog] = useState(false);
  const [vitalsForm, setVitalsForm] = useState({ bp_systolic: "", bp_diastolic: "", heart_rate: "", weight_kg: "", temperature: "", spo2: "" });
  const [vitalsSubmitting, setVitalsSubmitting] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [isAudioPlaying, setIsAudioPlaying] = useState(false); // true while auto-play TTS is running
  const [quickSymptoms] = useState(["Fever", "Headache", "Chest pain", "Cough", "Fatigue", "Nausea", "Dizziness", "Shortness of breath", "Back pain", "Stomach ache"]);
  const [showDisclaimer, setShowDisclaimer] = useState(true);
  /* ── Model Selector ── */
  const [selectedModel, setSelectedModel] = useState("core");
  const [showModelMenu, setShowModelMenu] = useState(false);
  const [modelProviders, setModelProviders] = useState([]);
  /* ── Risk Notification ── */
  const [riskNotification, setRiskNotification] = useState(null);
  const lastRiskLevelRef = useRef("green");
  /* ── Microorganism Tool ── */
  const [showMicroorgTool, setShowMicroorgTool] = useState(false);
  const [microInput, setMicroInput] = useState("");
  const [microType, setMicroType] = useState("bacteria");
  const [microResult, setMicroResult] = useState(null);
  const [microLoading, setMicroLoading] = useState(false);
  /* ── Nearby Doctor Search ── */
  const [showNearbyDoctor, setShowNearbyDoctor] = useState(false);
  const [doctorCity, setDoctorCity] = useState("");
  const [doctorSpecialty, setDoctorSpecialty] = useState("");
  const [doctorResults, setDoctorResults] = useState([]);
  const [doctorLoading, setDoctorLoading] = useState(false);
  /* ── Image Staging ── */
  const [stagedImages, setStagedImages] = useState([]);
  const [showImageStage, setShowImageStage] = useState(false);
  const [imageCaption, setImageCaption] = useState("");
  /* ── Toasts ── */
  const [toasts, setToasts] = useState([]);
  const addToast = useCallback((msg, type = "info") => {
    const id = Date.now() + Math.random();
    setToasts(prev => [...prev, { id, msg, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 2500);
  }, []);

  const abortRef = useRef(null);
  const endRef = useRef(null);
  const recorderRef = useRef(null);
  const chunksRef = useRef([]);
  const audioCtxRef = useRef(null);
  const analyserRef = useRef(null);
  const animRef = useRef(null);
  const autoPlayRef = useRef(null); // holds currently auto-playing Audio so Stop can kill it

  /* ── Sidebar: open on desktop, closed on mobile (client-only check) ── */
  useEffect(() => {
    const isMobile = window.innerWidth <= 768;
    if (isMobile) setSidebarOpen(false);
    const handleResize = () => setSidebarOpen(window.innerWidth > 768);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  /* ── Inject styles on theme change ── */
  useEffect(() => {
    injectGlobalStyles(T);

    const themeColor = isDark ? "#03050a" : "#f1f5ff";

    // Viewport
    let vm = document.querySelector('meta[name="viewport"]');
    if (!vm) { vm = document.createElement("meta"); vm.name = "viewport"; document.head.appendChild(vm); }
    vm.content = "width=device-width,initial-scale=1,viewport-fit=cover";

    // theme-color — controls Safari top bar AND bottom bar chrome
    const setMeta = (name, content, extra = {}) => {
      // Remove existing ones first to avoid duplicates
      document.querySelectorAll(`meta[name="${name}"]`).forEach(el => el.remove());
      const el = document.createElement("meta");
      el.name = name;
      el.setAttribute("content", content);
      Object.entries(extra).forEach(([k, v]) => el.setAttribute(k, v));
      document.head.appendChild(el);
    };

    // Set theme-color for both light and dark media — Safari uses these
    setMeta("theme-color", themeColor);

    // Force html + body background — this fills the bounce/overscroll zone
    // which is what causes the black strip at top/bottom in Safari
    const style = `
      html, body {
        background-color: ${themeColor} !important;
        background: ${themeColor} !important;
      }
    `;
    let bgStyle = document.getElementById("ma-bg-style");
    if (!bgStyle) {
      bgStyle = document.createElement("style");
      bgStyle.id = "ma-bg-style";
      document.head.appendChild(bgStyle);
    }
    bgStyle.textContent = style;

    // Also set inline for instant paint
    document.documentElement.style.backgroundColor = themeColor;
    document.body.style.backgroundColor = themeColor;
    document.documentElement.style.setProperty("--ma-bg", themeColor);
  }, [isDark, accentKey]);

  /* ── INIT ── */
  useEffect(() => {
    const stored = localStorage.getItem("ma_patient_id");
    if (stored) setPatientId(stored);
    else { const id = "patient_" + Date.now(); localStorage.setItem("ma_patient_id", id); setPatientId(id); }
    const th = localStorage.getItem("ma_theme");
    if (th === "light") setIsDark(false);
    const ac = localStorage.getItem("ma_accent");
    if (ac && ACCENT_PRESETS[ac]) setAccentKey(ac);
  }, []);

  useEffect(() => { if (patientId) { loadSessions(); loadDashboard(); loadPatientList(); loadTrajectory(); } }, [patientId]);

  /* ── Load model providers on mount ── */
  useEffect(() => {
    (async () => {
      try {
        const r = await apiFetch(`${API}/api/model-providers`);
        if (r.ok) {
          const d = await r.json();
          setModelProviders(d.providers || []);
          const available = (d.providers || []).filter(p => p.available);
          if (available.length) {
            const preferred = available.find(p => p.id !== "core") || available[0];
            setSelectedModel(prev => (prev === "core" || !available.some(p => p.id === prev)) ? preferred.id : prev);
          }
        }
      } catch { }
    })();
  }, []);

  /* ── Auto risk prediction polling (every 5 min) ── */
  useEffect(() => {
    if (!patientId) return;
    const checkRisk = async () => {
      try {
        const r = await apiFetch(`${API}/api/patient/${patientId}/health-trajectory`);
        if (r.ok) {
          const d = await r.json();
          setTrajectory(d);
          const level = d.alert_level || "green";
          if (["yellow", "orange", "red"].includes(level) && level !== lastRiskLevelRef.current) {
            setRiskNotification({ level, message: d.alert_message || "Health risk detected", time: new Date() });
          }
          lastRiskLevelRef.current = level;
        }
      } catch { }
    };
    const iv = setInterval(checkRisk, 5 * 60 * 1000);
    return () => clearInterval(iv);
  }, [patientId]);
  const prevMsgCount = useRef(0);
  useEffect(() => { if (messages.length > 0 && messages.length > prevMsgCount.current) { endRef.current?.scrollIntoView({ behavior: "smooth" }); } prevMsgCount.current = messages.length; }, [messages]);

  /* ── THEME PERSISTENCE ── */
  const toggleTheme = useCallback(() => {
    setIsDark(d => {
      localStorage.setItem("ma_theme", !d ? "dark" : "light");
      addToast(!d ? "Dark mode enabled" : "Light mode enabled", "success");
      return !d;
    });
  }, [addToast]);
  const setAccent = useCallback((key) => {
    setAccentKey(key);
    localStorage.setItem("ma_accent", key);
    addToast(`${ACCENT_PRESETS[key]?.name || key} theme selected`, "success");
    setShowAccentPicker(false);
  }, [addToast]);

  /* ════════════════════════════════════════
     DATA LOADERS
  ════════════════════════════════════════ */
  const loadSessions = async () => {
    try {
      const r = await apiFetch(`${API}/api/patient/${patientId}/sessions`);
      if (r.ok) setSessions((await r.json()).sessions || []);
    } catch { }
  };
  const loadPatientList = async () => {
    try {
      const r = await apiFetch(`${API}/api/patients`);
      if (r.ok) setPatientList((await r.json()).patients || []);
    } catch { }
  };
  const deleteSession = async (sid) => {
    try {
      const r = await apiFetch(`${API}/api/patient/${patientId}/session/${sid}`, { method: "DELETE" });
      if (r.ok) { if (sessionId === sid) { setMessages([]); setSessionId(null); } loadSessions(); }
    } catch { }
  };
  const loadDashboard = async () => {
    try {
      const r = await apiFetch(`${API}/api/patient/${patientId}/dashboard`);
      if (r.ok) {
        const d = await r.json();
        setDashboard(d); setLabResults(d.recent_labs || []); setMedImages(d.recent_images || []); setBodyMapData(d.body_map || {});
        const imgMap = {}, imgHist = {};
        for (const img of (d.recent_images || [])) {
          if (img.body_region && img.image_path) {
            const entry = { url: `${API}/${img.image_path}`, imageId: img.id, date: img.date };
            if (!imgMap[img.body_region]) imgMap[img.body_region] = entry;
            if (!imgHist[img.body_region]) imgHist[img.body_region] = [];
            imgHist[img.body_region].push(entry);
          }
        }
        setRegionImages(prev => ({ ...imgMap, ...Object.fromEntries(Object.entries(prev).filter(([_, v]) => v && !v.imageId)) }));
        setRegionImageHistory(imgHist);
        if (d.patient) setPatientInfo(p => ({ ...p, ...d.patient }));
      }
    } catch { }
  };
  const loadHealthScore = async () => {
    setHsLoading(true);
    try { const r = await apiFetch(`${API}/api/patient/${patientId}/health-score`); if (r.ok) setHealthScore(await r.json()); } catch { }
    finally { setHsLoading(false); }
  };
  const loadSessionMessages = async (sid) => {
    try {
      const r = await apiFetch(`${API}/api/patient/${patientId}/history?session_id=${sid}&limit=100`);
      if (r.ok) {
        const d = await r.json();
        setMessages((d.messages || []).map((m, i) => ({ id: Date.now() + i, role: m.role, text: m.content, language: m.language, timestamp: new Date(m.timestamp) })));
        setSessionId(sid); setTab("chat");
      }
    } catch { }
  };
  const switchPatient = (id) => {
    const newId = (typeof id === "string" ? id : tempPatientId).trim(); if (!newId) return;
    localStorage.setItem("ma_patient_id", newId); setPatientId(newId);
    setMessages([]); setSessionId(null); setSessions([]); setDashboard(null);
    setHealthScore(null); setLabResults([]); setMedImages([]);
    setShowPatientList(false); setTempPatientId("");
  };
  const savePatient = async () => {
    try {
      const body = {};
      Object.entries(patientInfo).forEach(([k, v]) => { if (v) body[k] = k === "age" ? (parseInt(v) || undefined) : v; });
      await apiFetch(`${API}/api/patient/${patientId}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      setShowPatientForm(false); loadDashboard();
    } catch { }
  };

  const addMsg = useCallback((role, text, extra = {}) => {
    const m = { id: Date.now() + Math.random(), role, text, timestamp: new Date(), ...extra };
    setMessages(prev => [...prev, m]);
    return m.id;
  }, []);
  const appendStreamChunk = useCallback((currentText, chunkText) => {
    return (currentText || "") + (chunkText || "");
  }, []);

  /* ════════════════════════════════════════
     STREAMING CHAT
  ════════════════════════════════════════ */
  const sendMessage = useCallback(async () => {
    if (!input.trim() || isLoading) return;
    const msg = input; setInput("");
    addMsg("user", msg);
    setIsLoading(true); setCanStop(true); setTriageInfo(null);
    const aid = addMsg("assistant", "", { isStreaming: true });
    const controller = new AbortController(); abortRef.current = controller;
    const specKey = selectedSpecialist?.name?.toLowerCase?.() || "general";
    const endpoint = selectedSpecialist
      ? `${API}/api/chat/specialist/stream?specialist=${encodeURIComponent(specKey)}`
      : `${API}/api/chat/stream`;
    const payload = { patient_id: patientId, message: msg, language: "auto", session_id: sessionId, generation_mode: genMode, model_provider: selectedModel };
    try {
      const res = await apiFetch(endpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload), signal: controller.signal });
      if (!res.ok) throw new Error("Request failed");
      const reader = res.body.getReader(); const dec = new TextDecoder(); let buf = "";
      while (true) {
        const { done, value } = await reader.read(); if (done) break;
        buf += dec.decode(value, { stream: true });
        const lines = buf.split("\n"); buf = lines.pop();
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const raw = line.slice(6); if (raw.trim() === "[DONE]") continue;
          try {
            const p = JSON.parse(raw);
            if (p.type === "triage") setTriageInfo(p);
            else if (p.type === "chunk") setMessages(prev => prev.map(m => m.id === aid ? { ...m, text: appendStreamChunk(m.text, p.content) } : m));
            else if (p.type === "done") {
              setSessionId(p.session_id);
              setMessages(prev => prev.map(m => m.id === aid ? { ...m, isStreaming: false, language: p.language } : m));
              if (p.triage) setTriageInfo(p.triage);
            }
            else if (p.type === "error") throw new Error(p.content);
          } catch (e) { if (e.name !== "AbortError" && !e.message?.includes("JSON")) throw e; }
        }
      }
    } catch (e) {
      if (e.name === "AbortError") setMessages(prev => prev.map(m => m.id === aid ? { ...m, isStreaming: false, text: m.text + "\n\n[Generation stopped]" } : m));
      else setMessages(prev => prev.map(m => m.id === aid ? { ...m, text: e.message || "An error occurred.", isStreaming: false, error: true } : m));
    } finally { setIsLoading(false); setCanStop(false); abortRef.current = null; loadSessions(); }
  }, [input, isLoading, patientId, sessionId, genMode, selectedSpecialist, addMsg, appendStreamChunk]);

  const stopGenerating = useCallback(() => {
    // Stop LLM stream
    if (abortRef.current) abortRef.current.abort();
    // Stop any auto-playing TTS audio immediately
    if (autoPlayRef.current) {
      autoPlayRef.current.pause();
      autoPlayRef.current.src = "";
      autoPlayRef.current = null;
    }
    setIsAudioPlaying(false);
  }, []);

  // Dedicated audio-only stop — called by the "Stop Audio" button
  const stopAudio = useCallback(() => {
    if (autoPlayRef.current) {
      autoPlayRef.current.pause();
      autoPlayRef.current.src = "";
      autoPlayRef.current = null;
    }
    setIsAudioPlaying(false);
  }, []);

  /* ════════════════════════════════════════
     VOICE
  ════════════════════════════════════════ */
  const startRecording = async () => {
    setShowLangPicker(false);

    try {
      let stream;
      try {
        // Try raw audio with no processing/suppression first for better STT
        stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            noiseSuppression: false,
            echoCancellation: false,
            autoGainControl: false
          }
        });
      } catch (err) {
        console.warn("Raw audio constraints failed, trying basic audio", err);
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      }
      audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)();
      const src = audioCtxRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioCtxRef.current.createAnalyser(); analyserRef.current.fftSize = 256;
      src.connect(analyserRef.current);
      const vis = () => {
        const buf = new Uint8Array(analyserRef.current.frequencyBinCount);
        analyserRef.current.getByteFrequencyData(buf);
        setAudioLevel(buf.reduce((a, b) => a + b, 0) / buf.length / 255);
        animRef.current = requestAnimationFrame(vis);
      }; vis();

      // Safari iOS fix: Safari doesn't support webm, it prefers mp4/aac
      let mime = "";
      if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) mime = "audio/webm;codecs=opus";
      else if (MediaRecorder.isTypeSupported("audio/webm")) mime = "audio/webm";
      else if (MediaRecorder.isTypeSupported("audio/mp4")) mime = "audio/mp4";
      else if (MediaRecorder.isTypeSupported("audio/aac")) mime = "audio/aac";

      const rec = new MediaRecorder(stream, mime ? { mimeType: mime } : {});
      chunksRef.current = [];
      rec.ondataavailable = e => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      rec.onstop = async () => {
        // Safari fallback: if mime is empty, assume mp4 wrapper for iOS compat
        const finalMime = rec.mimeType || mime || "audio/mp4";
        // Convert webm to expected extension or mp4 for Safari
        const ext = finalMime.includes("webm") ? "webm" : "mp4";
        const blob = new Blob(chunksRef.current, { type: finalMime });
        stream.getTracks().forEach(t => t.stop());
        audioCtxRef.current?.close(); cancelAnimationFrame(animRef.current); setAudioLevel(0);
        await sendVoice(blob, ext);
      };
      rec.start(); recorderRef.current = rec; setIsRecording(true);
    } catch (err) {
      console.error("Microphone Access Error:", err);
      addToast("Microphone access denied. Please check permissions.", "error");
    }
  };
  const stopRecording = () => { if (recorderRef.current && isRecording) { recorderRef.current.stop(); setIsRecording(false); } };
  const sendVoice = async (blob, ext = "webm") => {
    setIsLoading(true);
    const ph = addMsg("user", "Processing voice…");
    try {
      const fd = new FormData();
      fd.append("audio", blob, `recording.${ext}`);
      fd.append("patient_id", patientId);
      if (sessionId) fd.append("session_id", sessionId);
      // Always send language — "auto" means whisper detects it.
      // This ensures a language change mid-chat is always honoured.
      fd.append("language", voiceLang || "auto");
      const r = await apiFetch(`${API}/api/voice/chat`, { method: "POST", body: fd });
      const data = await r.json(); if (!r.ok) throw new Error(data.detail || "Voice failed");
      setMessages(prev => prev.filter(m => m.id !== ph));
      addMsg("user", data.transcription.text, { language: data.transcription.language, isVoice: true });
      const resp = data.response;
      addMsg("assistant", resp.response_text, { language: resp.original_language, audio_url: resp.audio_url, triage: resp.triage });
      setSessionId(resp.session_id); if (resp.triage) setTriageInfo(resp.triage);
      if (resp.citations?.length) { setCitations(resp.citations); setShowCitations(true); }
      if (resp.audio_url) {
        try {
          // Stop any currently playing auto-play audio first
          if (autoPlayRef.current) {
            autoPlayRef.current.pause();
            autoPlayRef.current.src = "";
            autoPlayRef.current = null;
          }
          const a = new Audio(`${API}${resp.audio_url}`);
          autoPlayRef.current = a;
          setIsAudioPlaying(true);
          a.onended = () => { autoPlayRef.current = null; setIsAudioPlaying(false); };
          a.onpause = () => { if (!a.src) setIsAudioPlaying(false); };
          a.play().catch(e => { console.log("Audio autoplay blocked:", e); setIsAudioPlaying(false); });
        } catch (e) { console.error("Audio play error:", e); }
      }
    } catch {
      setMessages(prev => prev.filter(m => m.id !== ph));
      addMsg("assistant", "Could not process voice. Try again or select correct language.", { error: true });
    } finally { setIsLoading(false); loadSessions(); }
  };

  /* ════════════════════════════════════════
     IMAGE UPLOAD
  ════════════════════════════════════════ */
  const handleImageUpload = async (e, region = null, caption = "") => {
    const file = e.target.files?.[0]; if (!file) return;
    if (e.target && e.target.value !== undefined) try { e.target.value = ""; } catch { }
    // FIX: Only use body_region if explicitly passed via the body map — never fall back to selectedRegion
    // This was causing every image to be labeled as "eyes" when selectedRegion was left set
    const uploadRegion = region || null;
    setIsLoading(true); setCanStop(true);
    const imgUrl = URL.createObjectURL(file);
    const userLabel = caption
      ? `${caption}${uploadRegion ? ` (${uploadRegion.replace(/_/g, " ")})` : ""}`
      : `Image uploaded${uploadRegion ? ` — ${uploadRegion.replace(/_/g, " ")}` : ""}`;
    addMsg("user", userLabel, { imageUrl: imgUrl });
    const aid = addMsg("assistant", "", { isStreaming: true });
    if (uploadRegion) setRegionImages(prev => ({ ...prev, [uploadRegion]: { url: imgUrl, imageId: null } }));
    const controller = new AbortController(); abortRef.current = controller;
    try {
      const fd = new FormData();
      fd.append("image", file); fd.append("patient_id", patientId);
      if (sessionId) fd.append("session_id", sessionId);
      if (uploadRegion) fd.append("body_region", uploadRegion);
      if (caption) fd.append("description", caption);
      if (uploadDate) fd.append("date", uploadDate);
      const res = await apiFetch(`${API}/api/image/analyze/stream`, { method: "POST", body: fd, signal: controller.signal });
      if (!res.ok) throw new Error("Image upload failed");
      const reader = res.body.getReader(); const dec = new TextDecoder(); let buf = "";
      while (true) {
        const { done, value } = await reader.read(); if (done) break;
        buf += dec.decode(value, { stream: true });
        const lines = buf.split("\n"); buf = lines.pop();
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const raw = line.slice(6); if (raw.trim() === "[DONE]") continue;
          try {
            const p = JSON.parse(raw);
            if (p.type === "vision") setMessages(prev => prev.map(m => m.id === aid ? { ...m, visionDesc: p.description } : m));
            else if (p.type === "chunk") setMessages(prev => prev.map(m => m.id === aid ? { ...m, text: appendStreamChunk(m.text, p.content) } : m));
            else if (p.type === "done") {
              setSessionId(p.session_id);
              setMessages(prev => prev.map(m => m.id === aid ? { ...m, isStreaming: false } : m));
              if (uploadRegion && p.image_id) setRegionImages(prev => ({ ...prev, [uploadRegion]: { url: prev[uploadRegion]?.url || imgUrl, imageId: p.image_id } }));
              if (p.lab_count > 0) { addMsg("assistant", `${p.lab_count} lab values extracted and saved.`); loadDashboard(); }
            }
          } catch { }
        }
      }
    } catch (e) {
      if (e.name === "AbortError") setMessages(prev => prev.map(m => m.id === aid ? { ...m, isStreaming: false, text: m.text + "\n\n[Stopped]" } : m));
      else setMessages(prev => prev.map(m => m.id === aid ? { ...m, text: "Image analysis failed.", isStreaming: false, error: true } : m));
    } finally { setIsLoading(false); setCanStop(false); abortRef.current = null; loadDashboard(); }
  };
  const handleDeleteImage = async (region, specificImageId) => {
    const imgId = specificImageId || regionImages[region]?.imageId; if (!imgId) return;
    try {
      const r = await apiFetch(`${API}/api/patient/${patientId}/image/${imgId}`, { method: "DELETE" });
      if (r.ok) { setRegionImages(prev => { const n = { ...prev }; if (!specificImageId) delete n[region]; return n; }); loadDashboard(); }
    } catch { }
  };

  /* ════════════════════════════════════════
     MICROORGANISM ANALYSIS TOOL
  ════════════════════════════════════════ */
  const runMicroorgAnalysis = useCallback(async () => {
    if (!microInput.trim()) return;
    setMicroLoading(true); setMicroResult(null);
    try {
      const prompt = `You are a clinical microbiologist. Analyse the following ${microType} and provide:\n\n1. **Identification** — Full classification (Kingdom→Species).\n2. **Morphology** — Shape, gram stain (if bacteria), spore formation, motility.\n3. **Biochemical Tests** — List 6-8 key tests with expected results:\n   - Test name | Expected result | Why it matters\n4. **Pathogenicity** — Diseases caused, virulence factors, affected organs.\n5. **Antibiotic/Antifungal Sensitivity** — First-line treatments.\n6. **Diagnostic Methods** — Culture media, staining, molecular tests.\n7. **Prevention & Control** — Key measures.\n\nOrganism/Query: "${microInput}"\nBe precise, use clinical terminology, format clearly with markdown.`;
      const res = await apiFetch(`${API}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ patient_id: patientId, message: prompt, language: "en", generation_mode: "detailed" }),
      });
      const reader = res.body.getReader(); const dec = new TextDecoder(); let buf = ""; let full = "";
      while (true) {
        const { done, value } = await reader.read(); if (done) break;
        buf += dec.decode(value, { stream: true });
        const lines = buf.split("\n"); buf = lines.pop();
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const raw = line.slice(6); if (raw.trim() === "[DONE]") continue;
          try { const p = JSON.parse(raw); if (p.type === "chunk") { full += p.content; setMicroResult(full); } } catch { }
        }
      }
      if (!full) {
        setMicroResult("No result returned. Please try a different query.");
      } else {
        apiFetch(`${API}/api/patient/${patientId}/event`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ event_type: "lab_test", title: `Microorganism ID: ${microInput}`, description: full, date: new Date().toISOString() })
        }).catch(err => console.error(err));
        addToast("Analysis saved to history", "success");
      }
    } catch { setMicroResult("Analysis failed. Please try again."); }
    finally { setMicroLoading(false); }
  }, [microInput, microType, patientId]);

  /* ════════════════════════════════════════
     NEARBY DOCTOR SEARCH — Hospital Database
  ════════════════════════════════════════ */


  const searchNearbyDoctors = useCallback(async () => {
    if (!doctorCity.trim()) return;
    setDoctorLoading(true); setDoctorResults([]);
    try {
      const qs = new URLSearchParams({ city: doctorCity, specialty: doctorSpecialty || "" });
      const r = await apiFetch(`${API}/api/medical-facilities?${qs}`);
      if (r.ok) {
        const d = await r.json();
        setDoctorResults(d.facilities || []);
      }
    } catch {
      addToast("Failed to fetch medical facilities", "error");
    } finally {
      setDoctorLoading(false);
    }
  }, [doctorCity, doctorSpecialty, addToast]);

  /* ════════════════════════════════════════
     IMAGE STAGING (select multiple → preview → send)
  ════════════════════════════════════════ */
  const handleImageStage = (e) => {
    const files = Array.from(e.target.files || []);
    if (e.target) e.target.value = "";
    const newStaged = files.map(file => ({ file, url: URL.createObjectURL(file), id: Date.now() + Math.random() }));
    setStagedImages(prev => [...prev, ...newStaged]);
    setShowImageStage(true);
  };
  const removeStagedImage = (id) => {
    setStagedImages(prev => { const next = prev.filter(s => s.id !== id); if (next.length === 0) setShowImageStage(false); return next; });
  };
  const sendStagedImages = async () => {
    if (!stagedImages.length) return;
    const cap = imageCaption.trim();
    for (const staged of stagedImages) {
      await handleImageUpload({ target: { files: [staged.file], value: "" } }, selectedRegion || null, cap);
    }
    setStagedImages([]); setShowImageStage(false); setImageCaption("");
  };


  /* ════════════════════════════════════════
     LAB REPORT
  ════════════════════════════════════════ */
  const handleReportUpload = async (e) => {
    const file = e.target.files?.[0]; if (!file) return; e.target.value = "";
    setIsLoading(true);
    const isPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
    addMsg("user", `${isPdf ? "PDF" : "Image"} lab report uploaded`);
    try {
      const fd = new FormData(); fd.append("image", file); fd.append("patient_id", patientId);
      if (sessionId) fd.append("session_id", sessionId);
      const r = await apiFetch(`${API}/api/report/parse`, { method: "POST", body: fd });
      const data = await r.json(); if (!r.ok) throw new Error(data.detail || "Report parsing failed");
      let txt = `Lab Report — ${data.count} values extracted\n\n`;
      for (const lr of data.lab_results) {
        const tag = lr.status === "normal" ? "✓" : lr.status === "high" || lr.status === "abnormal" ? "↑" : lr.status === "low" ? "↓" : "•";
        txt += `${tag} ${lr.test_name.replace(/_/g, " ").toUpperCase()}: ${lr.value} ${lr.unit || ""} (Normal: ${lr.normal_range || "N/A"})\n`;
      }
      if (data.count === 0) txt += "No lab values could be extracted. Try a clearer photo.";
      addMsg("assistant", txt); loadDashboard();
    } catch { addMsg("assistant", "Could not parse the report. Try uploading photos of individual pages.", { error: true }); }
    finally { setIsLoading(false); }
  };

  /* ════════════════════════════════════════
     TOOLS
  ════════════════════════════════════════ */
  const addSymptom = () => { const v = symptomInput.trim(); if (v && !symptomTags.includes(v)) { setSymptomTags(p => [...p, v]); setSymptomInput(""); } };
  const runSymptomCheck = async () => {
    if (!symptomTags.length) return;
    setSymptomLoading(true); setSymptomResult(null);
    try {
      const r = await apiFetch(`${API}/api/symptom-check`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ patient_id: patientId, symptoms: symptomTags, age: patientInfo.age ? parseInt(patientInfo.age) : undefined, gender: patientInfo.gender || undefined }) });
      if (r.ok) setSymptomResult(await r.json());
    } catch { } finally { setSymptomLoading(false); }
  };
  const searchMedicines = async (q) => {
    if (!q || q.length < 1) return [];
    try { const r = await apiFetch(`${API}/api/medicine-catalog?q=${encodeURIComponent(q)}`); if (r.ok) { const d = await r.json(); return d.medicines || []; } } catch { }
    return [];
  };
  const handleDrugInput = async (val) => {
    setDrugInput(val);
    if (val.trim().length >= 1) setDrugSuggestions(await searchMedicines(val.trim()));
    else setDrugSuggestions([]);
  };
  const selectDrugSuggestion = (med) => { if (!drugTags.includes(med.display)) setDrugTags(p => [...p, med.display]); setDrugInput(""); setDrugSuggestions([]); };
  const addDrug = () => { const v = drugInput.trim(); if (v && !drugTags.includes(v)) { setDrugTags(p => [...p, v]); setDrugInput(""); setDrugSuggestions([]); } };
  const runDrugCheck = async () => {
    if (drugTags.length < 2) return;
    setDrugLoading(true); setDrugResult(null);
    try { const r = await apiFetch(`${API}/api/drug-interactions`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ patient_id: patientId, medications: drugTags }) }); if (r.ok) setDrugResult(await r.json()); } catch { }
    finally { setDrugLoading(false); }
  };
  const mentalQuestions = useMemo(() => mentalType === "phq9"
    ? ["Little interest or pleasure in doing things", "Feeling down, depressed, or hopeless", "Trouble falling or staying asleep", "Feeling tired or having little energy", "Poor appetite or overeating", "Feeling bad about yourself", "Trouble concentrating on things", "Moving or speaking slowly / being fidgety", "Thoughts of self-harm or suicide"]
    : ["Feeling nervous, anxious or on edge", "Not being able to stop or control worrying", "Worrying too much about different things", "Trouble relaxing", "Being so restless it's hard to sit still", "Becoming easily annoyed or irritable", "Feeling afraid as if something awful might happen"], [mentalType]);
  const submitMentalHealth = async () => {
    try { const r = await apiFetch(`${API}/api/mental-health/assess`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ patient_id: patientId, assessment_type: mentalType, responses: mentalAnswers }) }); if (r.ok) setMentalResult(await r.json()); } catch { }
  };
  const generateReport = async () => { setReportLoading(true); try { const r = await apiFetch(`${API}/api/patient/${patientId}/report`); if (r.ok) setReportData(await r.json()); } catch { } finally { setReportLoading(false); } };
  const loadLabCatalog = async () => { try { const r = await apiFetch(`${API}/api/lab-catalog`); if (r.ok) { const d = await r.json(); setLabCatalog(d.tests || []); } } catch { } };
  useEffect(() => { loadLabCatalog(); }, []);
  const handleLabSearch = useCallback((q) => {
    setLabSearch(q); setSelectedLabTest(null);
    if (!q.trim()) { setLabSuggestions([]); return; }
    const low = q.toLowerCase();
    setLabSuggestions(labCatalog.filter(t => t.display.toLowerCase().includes(low) || t.name.toLowerCase().includes(low) || t.category.toLowerCase().includes(low)).slice(0, 8));
  }, [labCatalog]);
  const selectLabTest = (test) => { setSelectedLabTest(test); setLabSearch(test.display); setLabSuggestions([]); };
  const submitLabEntry = async () => {
    if (!selectedLabTest || !labValue.trim()) return;
    try {
      const r = await apiFetch(`${API}/api/patient/${patientId}/lab-result/manual`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ test_name: selectedLabTest.name, value: labValue.trim(), unit: selectedLabTest.unit, normal_range: selectedLabTest.normal_range, date: labDate || undefined }) });
      if (r.ok) { setLabSearch(""); setLabValue(""); setLabDate(""); setSelectedLabTest(null); loadDashboard(); }
    } catch { }
  };
  const deleteLabResult = async (resultId) => { try { const r = await apiFetch(`${API}/api/patient/${patientId}/lab-result/${resultId}`, { method: "DELETE" }); if (r.ok) loadDashboard(); } catch { } };
  const loadRiskPredictions = async () => { setRiskLoading(true); try { const r = await apiFetch(`${API}/api/patient/${patientId}/risk-predictions`); if (r.ok) setRiskData(await r.json()); } catch { } finally { setRiskLoading(false); } };
  const loadOrganHealth = async () => { setOrganLoading(true); try { const r = await apiFetch(`${API}/api/patient/${patientId}/organ-health`); if (r.ok) setOrganData(await r.json()); } catch { } finally { setOrganLoading(false); } };
  const loadTrends = async () => { setTrendsLoading(true); try { const r = await apiFetch(`${API}/api/patient/${patientId}/trends`); if (r.ok) setTrendsData(await r.json()); } catch { } finally { setTrendsLoading(false); } };
  const loadLabIntelligence = async () => { setLabIntelLoading(true); try { const r = await apiFetch(`${API}/api/patient/${patientId}/lab-intelligence`); if (r.ok) setLabIntel(await r.json()); } catch { } finally { setLabIntelLoading(false); } };
  const loadMedications = async () => { try { const r = await apiFetch(`${API}/api/patient/${patientId}/medications?active_only=false`); if (r.ok) setMedications((await r.json()).medications || []); } catch { } };
  const handleMedNameInput = async (val) => { setMedForm(p => ({ ...p, name: val })); if (val.trim().length >= 1) setMedSuggestions(await searchMedicines(val.trim())); else setMedSuggestions([]); };
  const selectMedSuggestion = (med) => { setMedForm(p => ({ ...p, name: med.display, dosage: med.dosage })); setMedSuggestions([]); };
  const addMedication = async () => { if (!medForm.name.trim()) return; try { await apiFetch(`${API}/api/patient/${patientId}/medication`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(medForm) }); setMedForm({ name: "", dosage: "", frequency: "Once daily" }); setShowMedForm(false); loadMedications(); } catch { } };
  const logMedTaken = async (medId) => { try { await apiFetch(`${API}/api/patient/${patientId}/medication/${medId}/log`, { method: "POST" }); loadMedications(); } catch { } };
  const deleteMed = async (medId) => { try { await apiFetch(`${API}/api/patient/${patientId}/medication/${medId}`, { method: "DELETE" }); loadMedications(); } catch { } };
  const toggleMedActive = async (medId) => { try { await apiFetch(`${API}/api/patient/${patientId}/medication/${medId}/toggle`, { method: "PUT" }); loadMedications(); } catch { } };
  const updateMedReminder = async (medId, field, value) => {
    const med = medications.find(m => m.id === medId); if (!med) return;
    const body = { reminder_morning: med.reminder_morning || "08:00", reminder_evening: med.reminder_evening || "21:00", reminder_enabled: med.reminder_enabled ?? 0 };
    body[field] = value;
    try { await apiFetch(`${API}/api/patient/${patientId}/medication/${medId}/reminder`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }); loadMedications(); } catch { }
  };
  const checkMedInteractions = () => {
    const tags = medications.filter(m => m.active).map(m => `${m.name}${m.dosage ? " " + m.dosage : ""}`);
    setDrugTags(tags); setDrugResult(null); closeTool(); setShowDrugChecker(true); setTab("tools");
    setTimeout(() => runDrugCheck(), 300);
  };
  const logLifestyle = async () => {
    const body = { patient_id: patientId };
    if (lifestyleForm.steps) body.steps = parseInt(lifestyleForm.steps) || undefined;
    if (lifestyleForm.distance_km) body.distance_km = parseFloat(lifestyleForm.distance_km) || undefined;
    if (lifestyleForm.sleep_hours) body.sleep_hours = parseFloat(lifestyleForm.sleep_hours) || undefined;
    if (lifestyleForm.calories) body.calories = parseInt(lifestyleForm.calories) || undefined;
    if (lifestyleForm.water_ml) body.water_ml = parseInt(lifestyleForm.water_ml) || undefined;
    try { await apiFetch(`${API}/api/patient/${patientId}/lifestyle`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }); setLifestyleForm({ steps: "", distance_km: "", sleep_hours: "", calories: "", water_ml: "" }); setShowLifestyleForm(false); } catch { }
  };
  const loadSpecialists = async () => { try { const r = await apiFetch(`${API}/api/specialists`); if (r.ok) setSpecialists((await r.json()).specialists || []); } catch { } };
  useEffect(() => { loadSpecialists(); loadMedications(); }, [patientId]);
  const loadTrajectory = async () => { setTrajectoryLoading(true); try { const r = await apiFetch(`${API}/api/patient/${patientId}/health-trajectory`); if (r.ok) setTrajectory(await r.json()); } catch { } finally { setTrajectoryLoading(false); } };
  const [coachBriefingData, setCoachBriefingData] = [coachBriefing, setCoachBriefing];
  const loadCoachBriefing = async () => { setCoachLoading(true); try { const r = await apiFetch(`${API}/api/patient/${patientId}/health-coach`); if (r.ok) setCoachBriefing(await r.json()); } catch { } finally { setCoachLoading(false); } };
  const loadScreeningWithInputs = async () => {
    setScreeningLoading(true);
    const hasInputs = Object.values(screeningInputs).some(v => v);
    try {
      const r = hasInputs
        ? await apiFetch(`${API}/api/patient/${patientId}/screening-plan`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ patient_id: patientId, ...screeningInputs }) })
        : await apiFetch(`${API}/api/patient/${patientId}/screening-plan`);
      if (r.ok) setScreeningPlan(await r.json());
    } catch { } finally { setScreeningLoading(false); }
  };
  const generateTreatmentPlan = async () => {
    if (!treatmentCondition.trim()) return;
    setTreatmentLoading(true); setTreatmentResult(null);
    try { const r = await apiFetch(`${API}/api/treatment-plan`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ patient_id: patientId, condition: treatmentCondition }) }); if (r.ok) setTreatmentResult(await r.json()); } catch { }
    finally { setTreatmentLoading(false); }
  };
  const startSymptomFlow = async () => {
    if (!flowSymptom.trim()) return;
    setFlowLoading(true); setFlowDiagnosis(null); setFlowQuestion(null); setFlowAnswers({});
    try { const r = await apiFetch(`${API}/api/symptom-flow`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ patient_id: patientId, symptom: flowSymptom }) }); if (r.ok) { const d = await r.json(); if (d.type === "question") setFlowQuestion(d); if (d.session_id) setFlowSessionId(d.session_id); } } catch { }
    finally { setFlowLoading(false); }
  };
  const answerSymptomFlow = async (answer) => {
    if (!flowQuestion) return;
    const newAnswers = { ...flowAnswers, [flowQuestion.question]: answer };
    setFlowAnswers(newAnswers); setFlowLoading(true);
    try { const r = await apiFetch(`${API}/api/symptom-flow`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ patient_id: patientId, symptom: flowSymptom, answers: newAnswers, session_id: flowSessionId }) }); if (r.ok) { const d = await r.json(); if (d.type === "question") setFlowQuestion(d); else if (d.type === "diagnosis") { setFlowDiagnosis(d); setFlowQuestion(null); } } } catch { }
    finally { setFlowLoading(false); }
  };

  /* ── Medication reminders ── */
  useEffect(() => {
    if (!medications.length) return;
    const check = () => {
      const now = new Date();
      const timeStr = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
      medications.filter(m => m.active && m.reminder_enabled).forEach(m => {
        if (timeStr === m.reminder_morning || timeStr === m.reminder_evening)
          if ("Notification" in window && Notification.permission === "granted")
            new Notification("Medication Reminder", { body: `Time to take ${m.name}${m.dosage ? " " + m.dosage : ""}` });
      });
    };
    if ("Notification" in window && Notification.permission === "default") Notification.requestPermission();
    const iv = setInterval(check, 60000);
    return () => clearInterval(iv);
  }, [medications]);

  const newSession = useCallback(() => { setMessages([]); setSessionId(null); setTriageInfo(null); loadSessions(); }, []);

  /* ── Vitals Quick-Log ── */
  const submitVitals = async () => {
    setVitalsSubmitting(true);
    try {
      const tests = [
        { key: "bp_systolic", name: "bp_systolic", unit: "mmHg", range: "90-120" },
        { key: "bp_diastolic", name: "bp_diastolic", unit: "mmHg", range: "60-80" },
        { key: "heart_rate", name: "heart_rate", unit: "bpm", range: "60-100" },
        { key: "weight_kg", name: "weight", unit: "kg", range: "" },
        { key: "temperature", name: "body_temperature", unit: "°C", range: "36.1-37.2" },
        { key: "spo2", name: "oxygen_saturation", unit: "%", range: "95-100" },
      ];
      for (const t of tests) {
        const val = vitalsForm[t.key];
        if (!val.trim()) continue;
        await apiFetch(`${API}/api/patient/${patientId}/lab-result/manual`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ test_name: t.name, value: val.trim(), unit: t.unit, normal_range: t.range }),
        });
      }
      setVitalsForm({ bp_systolic: "", bp_diastolic: "", heart_rate: "", weight_kg: "", temperature: "", spo2: "" });
      setShowVitalsLog(false);
      loadDashboard();
    } catch (e) { console.error("Vitals submit error:", e); }
    finally { setVitalsSubmitting(false); }
  };

  /* ── Copy message to clipboard ── */
  const copyMessage = useCallback((msgId, text) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedMsgId(msgId);
      setTimeout(() => setCopiedMsgId(null), 2000);
      addToast("Copied to clipboard!", "success");
    });
  }, [addToast]);

  /* ── Export session as .txt ── */
  const exportSession = useCallback(() => {
    if (!messages.length) return;
    const lines = [
      `MedAssist AI — Session Export`,
      `Patient: ${patientInfo.name || patientId}`,
      `Date: ${new Date().toLocaleString()}`,
      `Session: ${sessionId || "unsaved"}`,
      "─".repeat(60),
      "",
    ];
    for (const m of messages) {
      const who = m.role === "user" ? "YOU" : "MEDASSIST AI";
      const time = m.timestamp?.toLocaleTimeString?.([], { hour: "2-digit", minute: "2-digit" }) || "";
      lines.push(`[${who}  ${time}]`);
      lines.push(m.text || "");
      lines.push("");
    }
    lines.push("─".repeat(60));
    lines.push("⚠️  This is an AI-generated record. Always consult a qualified healthcare provider.");
    const blob = new Blob([lines.join("\n")], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `medassist_${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    setShowExportMenu(false);
  }, [messages, patientId, patientInfo, sessionId]);
  const activeTool = showSymptomChecker ? "symptom" : showDrugChecker ? "drugs" : showMentalHealth ? "mental" : showMedTracker ? "meds" : showSpecialistPanel ? "specialist" : showSymptomFlow ? "flow" : showTreatmentPlan ? "treatment" : showCoachPanel ? "coach" : showScreeningPanel ? "screening" : showMicroorgTool ? "microorg" : showNearbyDoctor ? "doctor" : null;
  const closeTool = useCallback(() => {
    setShowSymptomChecker(false); setShowDrugChecker(false); setShowMentalHealth(false);
    setShowMedTracker(false); setShowSpecialistPanel(false); setShowSymptomFlow(false);
    setShowTreatmentPlan(false); setShowCoachPanel(false); setShowScreeningPanel(false);
    setShowMicroorgTool(false); setShowNearbyDoctor(false);
  }, []);

  /* ════════════════════════════════════════
     TRIAGE CONFIG
  ════════════════════════════════════════ */
  const TRIAGE = {
    emergency: { bg: `${T.danger}12`, border: `${T.danger}40`, color: T.danger },
    urgent: { bg: `${T.warn}12`, border: `${T.warn}40`, color: T.warn },
    moderate: { bg: `rgba(251,191,36,0.1)`, border: `rgba(251,191,36,0.35)`, color: "#fbbf24" },
    general: { bg: `${T.accent3}10`, border: `${T.accent3}30`, color: T.accent3 },
  };

  /* ════════════════════════════════════════
     RENDER
  ════════════════════════════════════════ */
  return (
    <div suppressHydrationWarning className={seniorMode ? "senior-mode" : ""} style={{
      display: "flex", height: "100dvh", minHeight: "-webkit-fill-available",
      background: T.bg, color: T.text, fontFamily: "'DM Sans',sans-serif",
      overflow: "hidden", position: "relative",
      fontSize: seniorMode ? 18 : undefined,
    }}>
      {/* ── Solid bg fill — covers Safari top/bottom overscroll areas ── */}
      <div style={{ position: "fixed", inset: 0, background: T.bg, zIndex: -1 }} />
      {/* ── Background mesh ── */}
      <div style={{ position: "fixed", inset: 0, backgroundImage: T.bgMesh, pointerEvents: "none", zIndex: 0 }} />
      <ParticleField T={T} />

      {/* ── Mobile-only backdrop (hidden on desktop via CSS) ── */}
      {sidebarOpen && (
        <div onClick={() => setSidebarOpen(false)} className="ma-mobile-backdrop" style={{
          display: "none", /* shown via CSS on mobile only */
          position: "fixed", inset: 0,
          background: T.isDark ? "rgba(0,0,0,0.6)" : "rgba(0,0,0,0.3)",
          zIndex: 39,
          backdropFilter: "blur(6px)", WebkitBackdropFilter: "blur(6px)",
          animation: "fadeIn 0.2s ease both",
        }} />
      )}

      {/* ════════════════════════════════════════
          SIDEBAR
          Desktop: in-flow, width transition, no overlay
          Mobile:  fixed overlay with blur backdrop
      ════════════════════════════════════════ */}
      <aside className={`ma-sidebar${sidebarOpen ? " open" : ""}`} style={{
        /* Desktop defaults — in layout flow */
        position: "relative",
        width: sidebarOpen ? 272 : 0,
        minWidth: sidebarOpen ? 272 : 0,
        flexShrink: 0,
        zIndex: 10,
        overflow: "hidden",
        display: "flex", flexDirection: "column",
        background: T.isDark ? "rgba(4,8,18,0.97)" : "rgba(252,254,255,0.98)",
        borderRight: `1px solid ${T.border}`,
        transition: "width 0.32s cubic-bezier(0.4,0,0.2,1), min-width 0.32s cubic-bezier(0.4,0,0.2,1)",
      }}>
        {/* Inner wrapper — fixed 272px so content never reflows during animation */}
        <div className="ma-sidebar-inner" style={{
          width: 272,
          height: "100%",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          transform: sidebarOpen ? "translateX(0)" : "translateX(-272px)",
          transition: "transform 0.32s cubic-bezier(0.4,0,0.2,1)",
          willChange: "transform",
        }}>
          {/* Logo + close */}
          <div style={{ padding: "16px 18px 14px", borderBottom: `1px solid ${T.border}`, flexShrink: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 11, marginBottom: 16 }}>
              {/* Logo mark - sharp, not round */}
              <div style={{
                width: 34, height: 34, borderRadius: 8,
                background: `linear-gradient(135deg,${T.accent},${T.accent2})`,
                display: "flex", alignItems: "center", justifyContent: "center",
                flexShrink: 0,
              }}>
                <Dna size={17} color="#fff" strokeWidth={2.5} />
              </div>
              <div>
                <div style={{
                  fontSize: 16, fontWeight: 800, letterSpacing: "-0.04em",
                  color: T.text, fontFamily: "'DM Sans',sans-serif",
                }}>MedAssist</div>
                <div style={{ fontSize: 10, color: T.textMuted, letterSpacing: "0.06em", textTransform: "uppercase", fontWeight: 600 }}>AI · Clinical</div>
              </div>
              <button onClick={() => setSidebarOpen(false)} className="ma-btn ma-btn-ghost ma-btn-icon" style={{ marginLeft: "auto", padding: 6 }}>
                <ChevronLeft size={13} />
              </button>
            </div>

            {/* Patient card — flat, no fake grid texture */}
            <div style={{
              background: T.surface2,
              borderRadius: 9, padding: "11px 13px",
              border: `1px solid ${T.border}`,
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{
                  width: 34, height: 34, borderRadius: 7,
                  background: `${T.accent}18`,
                  border: `1px solid ${T.accent}25`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  flexShrink: 0, fontSize: 14, fontWeight: 800, color: T.accent,
                }}>
                  {(patientInfo.name || patientId || "P").charAt(0).toUpperCase()}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13, fontWeight: 700, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", color: T.text }}>
                    {patientInfo.name || patientId?.slice(0, 16)}
                  </div>
                  {patientInfo.age && <div style={{ fontSize: 11, color: T.textMuted }}>{patientInfo.age}y{patientInfo.gender ? ` · ${patientInfo.gender}` : ""}{patientInfo.blood_group ? ` · ${patientInfo.blood_group}` : ""}</div>}
                </div>
                <div style={{ display: "flex", gap: 3 }}>
                  <button onClick={() => { setShowPatientList(!showPatientList); if (!showPatientList) loadPatientList(); }} className="ma-btn ma-btn-ghost ma-btn-icon" style={{ padding: 5 }}><Users size={12} /></button>
                  <button onClick={() => setShowPatientForm(!showPatientForm)} className="ma-btn ma-btn-ghost ma-btn-icon" style={{ padding: 5 }}><Settings size={12} /></button>
                </div>
              </div>{/* end flex row */}
            </div>{/* end patient card */}
          </div>{/* end logo+close section */}

          {/* Patient switcher */}
          {showPatientList && (
            <div style={{ padding: "10px 16px", borderBottom: `1px solid ${T.border}`, flexShrink: 0 }} className="fade-up">
              <div style={{ fontSize: 10, fontWeight: 800, letterSpacing: "0.12em", textTransform: "uppercase", color: T.textMuted, marginBottom: 8 }}>Switch Patient</div>
              <div style={{ maxHeight: 150, overflowY: "auto", marginBottom: 8 }}>
                {patientList.filter(p => p.patient_id !== patientId).map(p => (
                  <button key={p.patient_id} onClick={() => switchPatient(p.patient_id)} style={{ display: "flex", alignItems: "center", gap: 9, width: "100%", padding: "8px 10px", borderRadius: 10, border: `1px solid ${T.border}`, background: T.surface2, marginBottom: 4, cursor: "pointer", textAlign: "left", transition: "all 0.15s" }}
                    onMouseEnter={e => { e.currentTarget.style.borderColor = T.borderAccent; e.currentTarget.style.background = T.surfaceHov; }}
                    onMouseLeave={e => { e.currentTarget.style.borderColor = T.border; e.currentTarget.style.background = T.surface2; }}>
                    <div style={{ width: 28, height: 28, borderRadius: "50%", background: `${T.accent2}20`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11.5, fontWeight: 800, color: T.accent2, flexShrink: 0 }}>
                      {(p.name || p.patient_id || "P").charAt(0).toUpperCase()}
                    </div>
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div style={{ fontSize: 12.5, fontWeight: 600, color: T.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{p.name || p.patient_id}</div>
                      {p.age && <div style={{ fontSize: 10, color: T.textMuted }}>{p.age}y {p.gender || ""}</div>}
                    </div>
                  </button>
                ))}
                {patientList.filter(p => p.patient_id !== patientId).length === 0 && <div style={{ fontSize: 12, color: T.textMuted, padding: "4px 2px" }}>No other patients</div>}
              </div>
              <div style={{ display: "flex", gap: 6 }}>
                <input value={tempPatientId} onChange={e => setTempPatientId(e.target.value)} onKeyDown={e => { if (e.key === "Enter") switchPatient(); }} placeholder="New patient ID…" className="ma-input" style={{ fontSize: 12, padding: "7px 11px" }} />
                <button onClick={() => switchPatient()} className="ma-btn ma-btn-primary ma-btn-sm">Add</button>
              </div>
            </div>
          )}

          {/* Patient profile form */}
          {showPatientForm && (
            <div style={{ padding: "10px 16px", borderBottom: `1px solid ${T.border}`, flexShrink: 0 }} className="fade-up">
              <div style={{ fontSize: 10, fontWeight: 800, letterSpacing: "0.12em", textTransform: "uppercase", color: T.textMuted, marginBottom: 8 }}>Patient Profile</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                {[["name", "Full Name"], ["age", "Age"], ["gender", "Gender"], ["blood_group", "Blood Group"], ["allergies", "Allergies"], ["chronic_conditions", "Chronic Conditions"], ["ethnicity", "Ethnicity"], ["family_history", "Family History"]].map(([f, l]) => (
                  <input key={f} placeholder={l} value={patientInfo[f] || ""} onChange={e => setPatientInfo(p => ({ ...p, [f]: e.target.value }))} className="ma-input" style={{ fontSize: 12.5, padding: "7px 11px" }} />
                ))}
              </div>
              <button onClick={savePatient} className="ma-btn ma-btn-primary" style={{ marginTop: 10, width: "100%", fontSize: 13 }}>Save Profile</button>
            </div>
          )}

          {/* Navigation */}
          <nav style={{ padding: "10px 10px 8px", borderBottom: `1px solid ${T.border}`, flexShrink: 0 }}>
            {NAV_ITEMS.map(n => (
              <button key={n.id} onClick={() => setTab(n.id)} className={`ma-nav-item ${tab === n.id ? "active" : ""}`} style={{ marginBottom: 3 }}>
                <n.icon size={16} />
                {n.label}
                {tab === n.id && <div style={{ marginLeft: "auto", width: 6, height: 6, borderRadius: "50%", background: T.accent, boxShadow: `0 0 8px ${T.accent}` }} />}
              </button>
            ))}
          </nav>

          {/* Quick actions */}
          <div style={{ padding: "10px 10px 8px", borderBottom: `1px solid ${T.border}`, flexShrink: 0 }}>
            <div style={{ fontSize: 9.5, fontWeight: 800, letterSpacing: "0.12em", textTransform: "uppercase", color: T.textMuted, marginBottom: 7, paddingLeft: 4 }}>Quick Actions</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4 }}>
              {[
                { icon: Search, label: "Symptoms", fn: () => { setTab("tools"); setShowSymptomChecker(true); } },
                { icon: Pill, label: "Drug Check", fn: () => { setTab("tools"); setShowDrugChecker(true); } },
                { icon: Upload, label: "Lab Report", fn: () => document.getElementById("sb-report-upload")?.click() },
                { icon: Heart, label: "Health Score", fn: () => { setTab("dashboard"); loadHealthScore(); } },
              ].map((a, i) => (
                <button key={i} onClick={a.fn} style={{
                  display: "flex", alignItems: "center", gap: 7, padding: "8px 10px",
                  borderRadius: 10, background: "transparent", border: `1px solid transparent`,
                  color: T.textMuted, fontSize: 12, fontWeight: 600, cursor: "pointer",
                  transition: "all 0.15s", fontFamily: "'DM Sans',sans-serif",
                }}
                  onMouseEnter={e => { e.currentTarget.style.background = T.surface2; e.currentTarget.style.borderColor = T.border; e.currentTarget.style.color = T.text; }}
                  onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.borderColor = "transparent"; e.currentTarget.style.color = T.textMuted; }}>
                  <a.icon size={13} />{a.label}
                </button>
              ))}
            </div>
            <input id="sb-report-upload" type="file" accept="image/*,.pdf" onChange={handleReportUpload} style={{ display: "none" }} />
          </div>

          {/* ── Emergency Contacts card ── */}
          <div style={{ padding: "8px 10px", borderBottom: `1px solid ${T.border}`, flexShrink: 0 }}>
            <button onClick={() => setShowEmergency(e => !e)} style={{
              width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between",
              padding: "9px 12px", borderRadius: 10, cursor: "pointer",
              background: showEmergency ? `${T.danger}12` : `${T.danger}08`,
              border: `1px solid ${showEmergency ? T.danger + "35" : T.danger + "20"}`,
              fontFamily: "'DM Sans',sans-serif", transition: "all 0.15s",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Phone size={13} style={{ color: T.danger }} />
                <span style={{ fontSize: 12.5, fontWeight: 700, color: T.danger }}>Emergency Contacts</span>
              </div>
              <ChevronDown size={13} style={{ color: T.danger, transform: showEmergency ? "rotate(180deg)" : "rotate(0)", transition: "transform 0.2s" }} />
            </button>
            {showEmergency && (
              <div className="fade-up" style={{ marginTop: 8, display: "flex", flexDirection: "column", gap: 5 }}>
                {[
                  { label: "Ambulance (India)", number: "102", color: T.danger },
                  { label: "Police", number: "100", color: T.accent2 },
                  { label: "Women Helpline", number: "1091", color: T.accent },
                  { label: "Disaster Mgmt", number: "108", color: T.warn },
                ].map((c, i) => (
                  <a key={i} href={`tel:${c.number}`} style={{
                    display: "flex", alignItems: "center", justifyContent: "space-between",
                    padding: "8px 12px", borderRadius: 9,
                    background: T.surface2, border: `1px solid ${T.border}`,
                    textDecoration: "none", transition: "border-color 0.12s",
                  }}
                    onMouseEnter={e => e.currentTarget.style.borderColor = c.color + "50"}
                    onMouseLeave={e => e.currentTarget.style.borderColor = T.border}>
                    <span style={{ fontSize: 12.5, fontWeight: 600, color: T.text }}>{c.label}</span>
                    <span style={{ fontSize: 14, fontWeight: 900, fontFamily: "'Fira Code',monospace", color: c.color }}>{c.number}</span>
                  </a>
                ))}
              </div>
            )}
          </div>

          {/* Sessions list */}
          <div className="ma-scroll" style={{ flex: 1, minHeight: 0, padding: "10px" }}>
            <button onClick={newSession} style={{
              display: "flex", alignItems: "center", gap: 9, width: "100%",
              padding: "10px 13px", borderRadius: 12,
              background: `linear-gradient(135deg,${T.accent}10,${T.accent2}08)`,
              border: `1px solid ${T.accent}25`,
              color: T.accent, fontSize: 13.5, fontWeight: 700, cursor: "pointer",
              marginBottom: 6, transition: "all 0.15s", fontFamily: "'DM Sans',sans-serif",
            }}
              onMouseEnter={e => e.currentTarget.style.background = `linear-gradient(135deg,${T.accent}18,${T.accent2}12)`}
              onMouseLeave={e => e.currentTarget.style.background = `linear-gradient(135deg,${T.accent}10,${T.accent2}08)`}>
              <Plus size={15} />New Consultation
            </button>
            {sessions.map(ss => (
              <div key={ss.session_id} className={`ma-session ${sessionId === ss.session_id ? "active" : ""}`}
                style={{ padding: "9px 12px", marginBottom: 3, display: "flex", alignItems: "center", gap: 7 }}>
                <div style={{ flex: 1, minWidth: 0 }} onClick={() => loadSessionMessages(ss.session_id)}>
                  <div style={{ fontSize: 13, fontWeight: 500, color: T.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {ss.summary || `Session ${ss.session_id?.slice(0, 8)}`}
                  </div>
                  {ss.started_at && <div style={{ fontSize: 11, color: T.textMuted, marginTop: 1 }}>
                    {new Date(ss.started_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                  </div>}
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 4, flexShrink: 0 }}>
                  <span style={{ fontSize: 10.5, color: T.textMuted, fontFamily: "'Fira Code',monospace" }}>{ss.message_count}</span>
                  <button onClick={e => { e.stopPropagation(); deleteSession(ss.session_id); }} className="ma-btn ma-btn-ghost ma-btn-icon" style={{ padding: 4, opacity: 0.45 }}
                    onMouseEnter={e => { e.currentTarget.style.color = T.danger; e.currentTarget.style.opacity = 1; }}
                    onMouseLeave={e => { e.currentTarget.style.color = ""; e.currentTarget.style.opacity = 0.45; }}>
                    <Trash2 size={11} />
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Bottom — theme + accent controls */}
          <div style={{ padding: "12px 14px", borderTop: `1px solid ${T.border}`, flexShrink: 0 }}>
            {/* Accent color picker */}
            {showAccentPicker && (
              <div className="fade-up" style={{ marginBottom: 10, padding: "10px 12px", borderRadius: 12, background: T.surface2, border: `1px solid ${T.border}` }}>
                <div style={{ fontSize: 10, fontWeight: 800, letterSpacing: "0.1em", textTransform: "uppercase", color: T.textMuted, marginBottom: 8 }}>Accent Color</div>
                <div style={{ display: "flex", gap: 8 }}>
                  {Object.entries(ACCENT_PRESETS).map(([key, val]) => (
                    <button key={key} onClick={() => setAccent(key)} style={{
                      width: 28, height: 28, borderRadius: "50%",
                      background: `linear-gradient(135deg,${val.a},${val.a2})`,
                      border: `2px solid ${accentKey === key ? val.a : "transparent"}`,
                      cursor: "pointer", transition: "all 0.2s",
                      boxShadow: accentKey === key ? `0 0 12px ${val.a}60` : "none",
                      transform: accentKey === key ? "scale(1.15)" : "scale(1)",
                    }} title={val.name} />
                  ))}
                </div>
              </div>
            )}
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              {/* Settings Dropdown Button */}
              <div style={{ position: "relative", flex: 1 }}>
                <button onClick={() => setShowSettingsMenu(!showSettingsMenu)} style={{
                  width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between",
                  padding: "9px 14px", borderRadius: 11, background: T.surface2,
                  border: `1px solid ${T.border}`, cursor: "pointer", transition: "all 0.2s",
                  fontFamily: "'DM Sans',sans-serif",
                }}
                  onMouseEnter={e => e.currentTarget.style.borderColor = T.borderAccent}
                  onMouseLeave={e => e.currentTarget.style.borderColor = T.border}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <Settings size={15} style={{ color: T.textMuted }} />
                    <div style={{ textAlign: "left", flex: 1 }}>
                      <div style={{ fontSize: 13, fontWeight: 700, color: T.text }}>Preferences</div>
                    </div>
                  </div>
                  <ChevronDown size={14} style={{ color: T.textMuted, transform: showSettingsMenu ? "rotate(180deg)" : "rotate(0)", transition: "transform 0.2s" }} />
                </button>
                {/* Internal Dropdown Popover */}
                {showSettingsMenu && (
                  <div className="ma-dropdown fade-up" style={{
                    position: "absolute", bottom: 50, left: 0, width: "100%", zIndex: 110,
                    padding: 8, background: T.surface, border: `1px solid ${T.border}`,
                    borderRadius: 12, boxShadow: T.shadowLg
                  }}>
                    <button onClick={toggleTheme} className="ma-dropdown-item" style={{ width: "100%", display: "flex", justifyContent: "space-between" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        {isDark ? <Sun size={14} style={{ color: T.warn }} /> : <Moon size={14} style={{ color: T.accent2 }} />}
                        <span style={{ fontSize: 13, fontWeight: 600 }}>{isDark ? "Light Mode" : "Dark Mode"}</span>
                      </div>
                      <div className="ma-theme-track" style={{ background: isDark ? T.accent : T.accent2, transform: "scale(0.8)", margin: 0 }}>
                        <div className="ma-theme-thumb" style={{ left: isDark ? 19 : 3 }} />
                      </div>
                    </button>
                    {/* Senior Mode inside Settings */}
                    <button onClick={() => setSeniorMode(s => !s)} className="ma-dropdown-item" style={{ width: "100%", display: "flex", justifyContent: "space-between", marginTop: 4 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <span style={{ fontSize: 14 }}>👴</span>
                        <span style={{ fontSize: 13, fontWeight: 600, color: seniorMode ? T.accent3 : T.text }}>Senior Mode</span>
                      </div>
                      {seniorMode && <Check size={14} style={{ color: T.accent3 }} />}
                    </button>
                  </div>
                )}
              </div>

              {/* Accent picker toggle (Keeping it small on the side) */}
              <button onClick={() => setShowAccentPicker(p => !p)} className="ma-btn ma-btn-ghost ma-btn-icon" title="Choose accent color" style={{ flexShrink: 0 }}>
                <div style={{ width: 16, height: 16, borderRadius: "50%", background: `linear-gradient(135deg,${T.accent},${T.accent2})` }} />
              </button>
            </div>
          </div>
        </div>{/* end inner wrapper */}
      </aside>

      {/* ════════════════════════════════════════
          MAIN CONTENT
          Desktop: naturally fills remaining flex space
          Mobile:  full width (sidebar overlays above)
      ════════════════════════════════════════ */}
      <div style={{
        flex: 1, display: "flex", flexDirection: "column",
        minWidth: 0, overflow: "hidden",
        position: "relative", zIndex: 1,
      }}>
        {/* ── TOP BAR ── */}
        <header className="ma-topbar" style={{
          height: 56, display: "flex", alignItems: "center",
          gap: 12, padding: "0 20px",
          borderBottom: `1px solid ${T.border}`,
          background: T.isDark ? "rgba(3,5,12,0.94)" : "rgba(255,255,255,0.95)",
          backdropFilter: "blur(24px)", WebkitBackdropFilter: "blur(24px)",
          flexShrink: 0, zIndex: 5,
          boxShadow: T.isDark ? "0 1px 0 rgba(255,255,255,0.04)" : "0 1px 0 rgba(0,0,0,0.06)",
        }}>
          {/* Menu toggle */}
          <button onClick={() => setSidebarOpen(v => !v)} style={{
            display: "flex", flexDirection: "column", gap: 4.5,
            background: "none", border: "none", cursor: "pointer",
            padding: "7px 5px", borderRadius: 8, transition: "background 0.15s",
          }}
            onMouseEnter={e => e.currentTarget.style.background = T.surface2}
            onMouseLeave={e => e.currentTarget.style.background = "none"}>
            {[20, 13, 20].map((w, i) => (
              <div key={i} style={{ height: 1.5, width: w, borderRadius: 99, background: T.textSub, transition: "width 0.2s" }} />
            ))}
          </button>

          {/* Logo — always visible */}
          <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
            <div style={{
              width: 32, height: 32, borderRadius: 9,
              background: `linear-gradient(135deg, ${T.accent}, ${T.accent2})`,
              display: "flex", alignItems: "center", justifyContent: "center",
              boxShadow: `0 4px 16px ${T.accent}40`,
              flexShrink: 0,
            }}>
              <Dna size={16} color="#fff" strokeWidth={2.5} />
            </div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 800, color: T.text, letterSpacing: "-0.03em", lineHeight: 1 }}>
                MedAssist
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 4, marginTop: 2 }}>
                <div style={{ width: 6, height: 6, borderRadius: "50%", background: T.accent3, boxShadow: `0 0 6px ${T.accent3}` }} />
                <span style={{ fontSize: 9.5, fontWeight: 600, color: T.textMuted, letterSpacing: "0.04em" }}>AI ONLINE</span>
              </div>
            </div>
          </div>

          <div style={{ width: 1, height: 20, background: T.border, flexShrink: 0 }} />

          {/* Page label */}
          <span style={{ fontSize: 13, fontWeight: 600, color: T.textSub, letterSpacing: "-0.01em" }}>
            {NAV_ITEMS.find(n => n.id === tab)?.label}
          </span>

          {/* Specialist pill */}
          {selectedSpecialist && (
            <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "3px 10px", borderRadius: 8, background: `${T.accent}10`, border: `1px solid ${T.accent}22`, fontSize: 12, fontWeight: 700, color: T.accent }}>
              <Stethoscope size={11} />{selectedSpecialist.name}
              <button onClick={() => setSelectedSpecialist(null)} style={{ border: "none", background: "none", color: T.textMuted, cursor: "pointer", padding: 0, display: "flex", marginLeft: 2, lineHeight: 1 }}><X size={10} /></button>
            </div>
          )}

          {/* Trajectory Alert */}
          {trajectory && trajectory.has_sufficient_data && trajectory.alert_level !== "green" && (
            <div className="pop-in" style={{
              display: "flex", alignItems: "center", gap: 7, padding: "4px 12px", borderRadius: 8, fontSize: 12, fontWeight: 600, cursor: "pointer",
              background: trajectory.alert_level === "red" ? `${T.danger}15` : trajectory.alert_level === "orange" ? `${T.warn}15` : `${T.accent}10`,
              border: `1px solid ${trajectory.alert_level === "red" ? `${T.danger}35` : trajectory.alert_level === "orange" ? `${T.warn}35` : `${T.accent}20`}`,
              color: trajectory.alert_level === "red" ? T.danger : trajectory.alert_level === "orange" ? T.warn : T.accent,
            }} onClick={() => setTab("dashboard")}>
              <Activity size={12} />
              <span style={{ maxWidth: 260, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{trajectory.alert_message}</span>
            </div>
          )}

          <div style={{ flex: 1 }} />

          {/* Triage badge */}
          {triageInfo && triageInfo.level !== "general" && (
            <div className="ma-triage pop-in" style={{ background: TRIAGE[triageInfo.level]?.bg, border: `1.5px solid ${TRIAGE[triageInfo.level]?.border}`, color: TRIAGE[triageInfo.level]?.color }}>
              <AlertTriangle size={11} />{triageInfo.level.toUpperCase()} — {triageInfo.reason}
            </div>
          )}

          {/* Stop stream */}
          {canStop && (
            <button onClick={stopGenerating} className="ma-btn ma-btn-danger ma-btn-sm" style={{ gap: 5 }}>
              <Square size={11} />Stop
            </button>
          )}
          {/* Stop audio */}
          {isAudioPlaying && !canStop && (
            <button onClick={stopAudio} className="ma-btn ma-btn-danger ma-btn-sm" style={{ gap: 5 }}>
              <VolumeX size={11} />Stop Audio
            </button>
          )}

          {/* Settings Menu */}
          <div style={{ position: "relative" }}>
            <button onClick={() => setShowSettingsMenu(!showSettingsMenu)} className="ma-btn ma-btn-ghost ma-btn-icon" title="Settings" style={{ borderRadius: 10 }}>
              <Settings size={15} style={{ color: T.textMuted }} />
            </button>
            {showSettingsMenu && (
              <div className="ma-dropdown scale-in" style={{ position: "absolute", top: 46, right: 0, minWidth: 160, zIndex: 100 }}>
                <div onClick={() => { toggleTheme(); setShowSettingsMenu(false); }} className="ma-dropdown-item">
                  {isDark ? <Sun size={14} style={{ color: T.warn }} /> : <Moon size={14} style={{ color: T.accent2 }} />}
                  <span style={{ fontSize: 13, fontWeight: 600 }}>{isDark ? "Light Mode" : "Dark Mode"}</span>
                </div>
              </div>
            )}
          </div>
          {/* Senior Mode quick toggle */}
          <button onClick={() => setSeniorMode(s => !s)} title="Senior Mode" style={{
            display: "flex", alignItems: "center", gap: 6,
            padding: "6px 11px", borderRadius: 8, cursor: "pointer",
            background: seniorMode ? `${T.accent3}18` : "transparent",
            border: `1px solid ${seniorMode ? T.accent3 + "45" : T.border}`,
            color: seniorMode ? T.accent3 : T.textMuted,
            fontSize: 12, fontWeight: 700, transition: "all 0.15s",
            fontFamily: "'DM Sans',sans-serif",
          }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = T.accent3; e.currentTarget.style.color = T.accent3; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = seniorMode ? T.accent3 + "45" : T.border; e.currentTarget.style.color = seniorMode ? T.accent3 : T.textMuted; }}>
            <span style={{ fontSize: 15 }}>👴🏼</span>
            <span style={{ display: seniorMode ? "inline" : "none" }}>Senior</span>
          </button>
        </header>

        {/* ════════════════════════════════════════
            SENIOR MODE UI — full screen override
        ════════════════════════════════════════ */}
        {seniorMode && (
          <div style={{
            flex: 1, display: "flex", flexDirection: "column",
            overflow: "hidden", background: T.bg,
          }}>
            {/* ── Senior Chat Area ── */}
            <div className="ma-scroll" style={{ flex: 1, padding: "20px 18px 0" }}>
              <div style={{ maxWidth: 680, margin: "0 auto", paddingBottom: 20 }}>

                {/* Disclaimer */}
                <div style={{
                  display: "flex", alignItems: "flex-start", gap: 12,
                  padding: "14px 18px", borderRadius: 14,
                  background: `${T.warn}10`, border: `2px solid ${T.warn}30`,
                  marginBottom: 24, fontSize: 15, color: T.warn, lineHeight: 1.6,
                }}>
                  <span style={{ fontSize: 20, flexShrink: 0 }}>⚠️</span>
                  <span>This AI is not a replacement for your doctor. Always consult a qualified healthcare provider for medical advice.</span>
                </div>

                {/* Empty state for seniors */}
                {messages.length === 0 && (
                  <div className="fade-up" style={{ textAlign: "center", padding: "30px 0 40px" }}>
                    {/* Big robot */}
                    <div style={{
                      width: 140, height: 140, borderRadius: "50%",
                      background: `radial-gradient(circle at 35% 35%, ${T.accent}18, transparent 70%)`,
                      border: `2px solid ${T.border}`,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      margin: "0 auto 28px",
                    }}>
                      <RobotDoc isThinking={false} T={T} size={90} />
                    </div>

                    <h1 style={{
                      fontFamily: "'DM Sans', sans-serif",
                      fontSize: 34, fontWeight: 800, letterSpacing: "-0.03em",
                      color: T.text, marginBottom: 14,
                    }}>Your Health Assistant</h1>
                    <p style={{
                      fontSize: 20, color: T.textSub, lineHeight: 1.65,
                      maxWidth: 460, margin: "0 auto 40px",
                    }}>
                      Tell me how you are feeling.<br />
                      I can help with your health questions.
                    </p>

                    {/* Big action buttons */}
                    <div style={{
                      display: "grid", gridTemplateColumns: "1fr 1fr",
                      gap: 14, maxWidth: 480, margin: "0 auto",
                    }}>
                      {[
                        { emoji: "🎤", label: "Speak to Me", sub: "Tell me your symptoms by voice", color: T.accent, fn: () => { if (!isRecording) { setTab("chat"); startRecording(); } else stopRecording(); } },
                        { emoji: "⌨️", label: "Type a Question", sub: "Write what is bothering you", color: T.accent2, fn: () => { setTab("chat"); setTimeout(() => document.querySelector(".senior-chat-input")?.focus(), 100); } },
                        { emoji: "🔬", label: "Upload Lab Report", sub: "Photo or PDF of your tests", color: T.accent3, fn: () => document.getElementById("senior-report-upload")?.click() },
                        { emoji: "💊", label: "Check Medicines", sub: "See if your medicines are safe together", color: T.warn, fn: () => { setSeniorMode(false); setTab("tools"); setShowDrugChecker(true); } },
                      ].map((a, i) => (
                        <button key={i} onClick={a.fn} style={{
                          padding: "22px 18px", borderRadius: 18,
                          background: T.surface,
                          border: `2px solid ${T.border}`,
                          cursor: "pointer", textAlign: "left",
                          transition: "all 0.18s", fontFamily: "'DM Sans',sans-serif",
                          display: "flex", flexDirection: "column", gap: 8,
                        }}
                          onMouseEnter={e => { e.currentTarget.style.borderColor = a.color; e.currentTarget.style.background = T.surface2; e.currentTarget.style.transform = "translateY(-2px)"; }}
                          onMouseLeave={e => { e.currentTarget.style.borderColor = T.border; e.currentTarget.style.background = T.surface; e.currentTarget.style.transform = "translateY(0)"; }}>
                          <div style={{ fontSize: 36 }}>{a.emoji}</div>
                          <div style={{ fontSize: 18, fontWeight: 800, color: T.text }}>{a.label}</div>
                          <div style={{ fontSize: 14, color: T.textMuted, lineHeight: 1.4, fontWeight: 400 }}>{a.sub}</div>
                        </button>
                      ))}
                    </div>
                    <input id="senior-report-upload" type="file" accept="image/*,.pdf" style={{ display: "none" }} onChange={handleReportUpload} />
                  </div>
                )}

                {/* Messages */}
                <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                  {messages.map(m => (
                    <div key={m.id} className="fade-up" style={{
                      display: "flex",
                      justifyContent: m.role === "user" ? "flex-end" : "flex-start",
                      alignItems: "flex-end", gap: 14,
                    }}>
                      {m.role === "assistant" && (
                        <div style={{ flexShrink: 0, marginBottom: 4 }}>
                          <RobotDoc isThinking={!!m.isStreaming} T={T} size={48} />
                        </div>
                      )}
                      <div style={{
                        maxWidth: "82%",
                        padding: "18px 22px",
                        fontSize: 18,
                        lineHeight: 1.75,
                        borderRadius: m.role === "user" ? "18px 18px 5px 18px" : "5px 18px 18px 18px",
                        background: m.role === "user" ? T.msgUser : T.msgBot,
                        border: `1.5px solid ${m.role === "user" ? T.msgUserBorder : T.msgBotBorder}`,
                        color: T.text,
                        boxShadow: T.isDark ? "0 4px 20px rgba(0,0,0,0.25)" : "0 4px 16px rgba(0,0,0,0.07)",
                      }}>
                        {m.imageUrl && <img src={m.imageUrl} alt="Upload" style={{ borderRadius: 10, marginBottom: 12, maxHeight: 180, objectFit: "cover", display: "block" }} />}
                        <div style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                          {formatText(m.text, T.accent)}
                          {m.isStreaming && <span className="ma-cursor" />}
                        </div>
                        {/* Large timestamp */}
                        <div style={{ fontSize: 13, color: T.textMuted, marginTop: 10, opacity: 0.55, fontFamily: "'Fira Code',monospace" }}>
                          {m.timestamp?.toLocaleTimeString?.([], { hour: "2-digit", minute: "2-digit" })}
                        </div>
                      </div>
                    </div>
                  ))}
                  {isLoading && messages.length > 0 && !messages[messages.length - 1]?.isStreaming && (
                    <div style={{ display: "flex", alignItems: "flex-end", gap: 14 }} className="fade-in">
                      <RobotDoc isThinking={true} T={T} size={48} />
                      <div style={{ padding: "18px 22px", borderRadius: "5px 18px 18px 18px", background: T.msgBot, border: `1.5px solid ${T.msgBotBorder}`, display: "inline-flex", gap: 8 }}>
                        <div className="dot1" style={{ width: 10, height: 10, borderRadius: "50%", background: T.accent }} />
                        <div className="dot2" style={{ width: 10, height: 10, borderRadius: "50%", background: T.accent, opacity: 0.65 }} />
                        <div className="dot3" style={{ width: 10, height: 10, borderRadius: "50%", background: T.accent, opacity: 0.4 }} />
                      </div>
                    </div>
                  )}
                </div>
                <div ref={endRef} />
              </div>
            </div>

            {/* ── Senior Chat Input ── */}
            <div style={{
              borderTop: `2px solid ${T.border}`,
              background: T.isDark ? "rgba(5,7,15,0.95)" : "rgba(255,255,255,0.97)",
              backdropFilter: "blur(20px)", WebkitBackdropFilter: "blur(20px)",
              padding: "16px 18px 20px", flexShrink: 0,
            }}>
              <div style={{ maxWidth: 680, margin: "0 auto" }}>
                {/* Recording wave */}
                {isRecording && (
                  <div className="fade-up" style={{
                    marginBottom: 14, borderRadius: 14, padding: "12px 18px",
                    background: `${T.danger}08`, border: `2px solid ${T.danger}22`,
                  }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                      <div style={{ width: 11, height: 11, borderRadius: "50%", background: T.danger, animation: "pulse 1.2s infinite" }} />
                      <span style={{ fontSize: 16, fontWeight: 800, color: T.danger }}>Listening… speak clearly</span>
                    </div>
                    <VoiceVisualizer analyserRef={analyserRef} isRecording={isRecording} T={T} />
                  </div>
                )}

                {/* Input row */}
                <div style={{ display: "flex", gap: 10, alignItems: "flex-end" }}>
                  {/* Image upload */}
                  <label style={{ cursor: "pointer", flexShrink: 0 }}>
                    <input type="file" accept="image/*,.pdf" style={{ display: "none" }} onChange={handleReportUpload} disabled={isLoading || isRecording} />
                    <div style={{
                      width: 56, height: 56, borderRadius: 14, flexShrink: 0,
                      background: T.surface2, border: `2px solid ${T.border}`,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      cursor: "pointer", transition: "all 0.15s",
                    }}
                      onMouseEnter={e => { e.currentTarget.style.borderColor = T.accent; }}
                      onMouseLeave={e => { e.currentTarget.style.borderColor = T.border; }}>
                      <FileText size={22} style={{ color: T.textSub }} />
                    </div>
                  </label>

                  {/* Big textarea */}
                  <textarea
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
                    placeholder="Type your health question here…"
                    className="ma-input senior-chat-input"
                    rows={2}
                    disabled={isLoading || isRecording}
                    style={{
                      flex: 1, fontSize: 18, fontFamily: "'DM Sans',sans-serif",
                      minHeight: 60, padding: "14px 18px", borderWidth: 2,
                      borderRadius: 14,
                    }}
                  />

                  {/* Big mic / send button */}
                  {input.trim() ? (
                    <button onClick={sendMessage} disabled={isLoading} style={{
                      width: 60, height: 60, borderRadius: 16, flexShrink: 0,
                      background: T.accent, border: "none", cursor: "pointer",
                      display: "flex", alignItems: "center", justifyContent: "center",
                      boxShadow: `0 4px 20px ${T.accent}50`,
                      transition: "all 0.15s",
                    }}>
                      {isLoading ? <Loader2 size={22} color={T.isDark ? "#000" : "#fff"} style={{ animation: "spin 1s linear infinite" }} /> : <Send size={22} color={T.isDark ? "#000" : "#fff"} />}
                    </button>
                  ) : (
                    <button onClick={isRecording ? stopRecording : startRecording} disabled={isLoading} className={isRecording ? "senior-mic-btn" : ""} style={{
                      width: 60, height: 60, borderRadius: 16, flexShrink: 0,
                      background: isRecording ? T.danger : T.accent,
                      border: "none", cursor: "pointer",
                      display: "flex", alignItems: "center", justifyContent: "center",
                      boxShadow: `0 4px 20px ${isRecording ? T.danger : T.accent}55`,
                      transition: "all 0.15s",
                      "--senior-glow": isRecording ? `${T.danger}50` : `${T.accent}50`,
                    }}>
                      {isRecording ? <MicOff size={24} color="white" /> : <Mic size={24} color={T.isDark ? "#000" : "#fff"} />}
                    </button>
                  )}
                </div>

                {/* Stop button */}
                {canStop && (
                  <button onClick={stopGenerating} style={{
                    marginTop: 10, width: "100%",
                    padding: "13px", borderRadius: 12,
                    background: `${T.danger}12`, border: `2px solid ${T.danger}30`,
                    color: T.danger, fontSize: 16, fontWeight: 700,
                    cursor: "pointer", fontFamily: "'DM Sans',sans-serif",
                    display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
                  }}>
                    <Square size={16} /> Stop Generating
                  </button>
                )}

                {/* Big "Exit Senior Mode" button */}
                <button onClick={() => setSeniorMode(false)} style={{
                  marginTop: 10, width: "100%",
                  padding: "11px", borderRadius: 12,
                  background: "transparent", border: `1.5px solid ${T.border}`,
                  color: T.textMuted, fontSize: 14, fontWeight: 600,
                  cursor: "pointer", fontFamily: "'DM Sans',sans-serif",
                  display: "flex", alignItems: "center", justifyContent: "center", gap: 7,
                }}
                  onMouseEnter={e => { e.currentTarget.style.color = T.text; e.currentTarget.style.borderColor = T.borderBright; }}
                  onMouseLeave={e => { e.currentTarget.style.color = T.textMuted; e.currentTarget.style.borderColor = T.border; }}>
                  ← Switch to Normal Mode
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ════════════════════════════════════════
            CHAT TAB
        ════════════════════════════════════════ */}
        {!seniorMode && tab === "chat" && (
          <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
            {/* Messages area */}
            <div className="ma-scroll" style={{ flex: 1, padding: "24px 22px 0" }}>
              <div style={{ maxWidth: 780, margin: "0 auto", paddingBottom: 24 }}>

                {/* Disclaimer popup — slides in from right */}
                {showDisclaimer && (
                  <div className="ma-disclaimer-popup" style={{
                    position: "fixed", top: 20, right: 20,
                    maxWidth: 360, width: "calc(100% - 40px)",
                    zIndex: 999,
                    display: "flex", alignItems: "flex-start", gap: 10,
                    padding: "14px 16px", borderRadius: 14,
                    background: T.isDark ? "rgba(50,40,10,0.92)" : "rgba(255,248,230,0.98)",
                    border: `1px solid ${T.warn}35`,
                    backdropFilter: "blur(16px)", WebkitBackdropFilter: "blur(16px)",
                    boxShadow: `0 8px 32px rgba(0,0,0,0.25), 0 0 0 1px ${T.warn}15`,
                    fontSize: 12.5, color: T.warn, lineHeight: 1.5,
                    animation: "disclaimerSlideIn 0.45s cubic-bezier(0.16,1,0.3,1) both",
                  }}>
                    <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 1 }} />
                    <span style={{ flex: 1 }}>AI assistant only — not a substitute for professional medical advice. Always consult a qualified healthcare provider.</span>
                    <button
                      onClick={() => setShowDisclaimer(false)}
                      style={{
                        background: "none", border: "none", cursor: "pointer",
                        color: T.warn, opacity: 0.7, padding: 2, display: "flex",
                        flexShrink: 0, borderRadius: 6, transition: "opacity 0.15s",
                      }}
                      onMouseEnter={e => e.currentTarget.style.opacity = "1"}
                      onMouseLeave={e => e.currentTarget.style.opacity = "0.7"}
                      aria-label="Dismiss disclaimer"
                    >
                      <X size={16} />
                    </button>
                  </div>
                )}

                {/* Risk Prediction Notification */}
                {riskNotification && (
                  <div style={{
                    position: "fixed", top: showDisclaimer ? 90 : 20, right: 20,
                    maxWidth: 380, width: "calc(100% - 40px)",
                    zIndex: 998,
                    display: "flex", alignItems: "flex-start", gap: 10,
                    padding: "14px 16px", borderRadius: 14,
                    background: T.isDark
                      ? (riskNotification.level === "red" ? "rgba(80,20,20,0.95)" : riskNotification.level === "orange" ? "rgba(80,50,10,0.95)" : "rgba(70,60,10,0.95)")
                      : (riskNotification.level === "red" ? "rgba(255,235,235,0.98)" : riskNotification.level === "orange" ? "rgba(255,245,230,0.98)" : "rgba(255,250,230,0.98)"),
                    border: `1px solid ${riskNotification.level === "red" ? "#ef444435" : riskNotification.level === "orange" ? "#f9731635" : T.warn + "35"}`,
                    backdropFilter: "blur(16px)", WebkitBackdropFilter: "blur(16px)",
                    boxShadow: "0 8px 32px rgba(0,0,0,0.25)",
                    fontSize: 12.5, lineHeight: 1.5,
                    color: riskNotification.level === "red" ? "#ef4444" : riskNotification.level === "orange" ? "#f97316" : T.warn,
                    animation: "riskAlertSlideIn 0.5s cubic-bezier(0.16,1,0.3,1) both",
                  }}>
                    <Activity size={16} style={{ flexShrink: 0, marginTop: 1 }} />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 2 }}>⚠️ Health Risk Alert</div>
                      <span>{riskNotification.message}</span>
                    </div>
                    <button
                      onClick={() => setRiskNotification(null)}
                      style={{
                        background: "none", border: "none", cursor: "pointer",
                        color: "inherit", opacity: 0.7, padding: 2, display: "flex",
                        flexShrink: 0, borderRadius: 6, transition: "opacity 0.15s",
                      }}
                      onMouseEnter={e => e.currentTarget.style.opacity = "1"}
                      onMouseLeave={e => e.currentTarget.style.opacity = "0.7"}
                      aria-label="Dismiss risk alert"
                    >
                      <X size={16} />
                    </button>
                  </div>
                )}

                {/* ── CITATIONS PANEL ── */}
                {showCitations && citations.length > 0 && (
                  <div className="fade-up" style={{
                    marginBottom: 16, padding: "14px 16px", borderRadius: 12,
                    background: T.surface2, border: `1px solid ${T.border}`,
                    borderLeft: `3px solid ${T.accent}`,
                  }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 7, fontSize: 12, fontWeight: 800, color: T.accent, letterSpacing: "0.06em", textTransform: "uppercase" }}>
                        <BookMarked size={13} /> Trusted Sources
                      </div>
                      <button onClick={() => setShowCitations(false)} style={{ background: "none", border: "none", cursor: "pointer", color: T.textMuted, display: "flex" }}>
                        <X size={13} />
                      </button>
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                      {citations.map((c, i) => (
                        <a key={i} href={c.url} target="_blank" rel="noopener noreferrer" style={{
                          display: "flex", alignItems: "flex-start", gap: 10,
                          padding: "8px 10px", borderRadius: 9,
                          background: T.surface, border: `1px solid ${T.border}`,
                          textDecoration: "none", transition: "border-color 0.15s",
                        }}
                          onMouseEnter={e => e.currentTarget.style.borderColor = T.accent + "50"}
                          onMouseLeave={e => e.currentTarget.style.borderColor = T.border}>
                          <div style={{
                            fontSize: 10, fontWeight: 800, letterSpacing: "0.06em",
                            padding: "2px 7px", borderRadius: 5,
                            background: c.publisher === "WHO" ? `${T.danger}18` : c.publisher === "CDC" ? `${T.accent3}15` : c.publisher === "NICE" ? `${T.accent2}15` : `${T.accent}12`,
                            color: c.publisher === "WHO" ? T.danger : c.publisher === "CDC" ? T.accent3 : c.publisher === "NICE" ? T.accent2 : T.accent,
                            flexShrink: 0, marginTop: 1, textTransform: "uppercase",
                          }}>{c.publisher}</div>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ fontSize: 12.5, fontWeight: 600, color: T.text, lineHeight: 1.4, marginBottom: 2 }}>{c.title}</div>
                            {c.section && <div style={{ fontSize: 11, color: T.textMuted }}>{c.section}</div>}
                            {c.last_reviewed && <div style={{ fontSize: 10.5, color: T.textMuted, fontFamily: "'Fira Code',monospace" }}>Reviewed: {c.last_reviewed}</div>}
                          </div>
                          <ExternalLink size={12} style={{ color: T.textMuted, flexShrink: 0, marginTop: 2 }} />
                        </a>
                      ))}
                    </div>
                  </div>
                )}

                {/* ── QUICK SYMPTOM CHIPS ── */}
                {messages.length > 0 && !isLoading && (
                  <div style={{ marginBottom: 14 }}>
                    <div style={{ fontSize: 10.5, fontWeight: 700, color: T.textMuted, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 7 }}>Quick add symptom:</div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                      {quickSymptoms.slice(0, 6).map((s, i) => (
                        <button key={i} onClick={() => setInput(p => p ? `${p}, ${s.toLowerCase()}` : s.toLowerCase())}
                          className="ma-symptom-chip"
                          style={{
                            background: T.surface2, border: `1px solid ${T.border}`,
                            color: T.textSub, fontSize: 12, fontWeight: 600,
                          }}
                          onMouseEnter={e => { e.currentTarget.style.background = T.surfaceHov; e.currentTarget.style.borderColor = T.accent + "50"; e.currentTarget.style.color = T.text; }}
                          onMouseLeave={e => { e.currentTarget.style.background = T.surface2; e.currentTarget.style.borderColor = T.border; e.currentTarget.style.color = T.textSub; }}>
                          + {s}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* ── EMPTY STATE ── */}
                {messages.length === 0 && (
                  <div className="fade-up" style={{ paddingTop: 16, paddingBottom: 40 }}>

                    {/* ── HERO: split layout ── */}
                    <div style={{
                      display: "flex", alignItems: "center", gap: 48,
                      marginBottom: 56, flexWrap: "wrap",
                    }}>
                      {/* Left: text */}
                      <div style={{ flex: "1 1 300px", minWidth: 0 }}>
                        <div style={{
                          display: "inline-flex", alignItems: "center", gap: 8,
                          padding: "4px 12px", borderRadius: 6,
                          background: `${T.accent}12`, border: `1px solid ${T.accent}25`,
                          fontSize: 11, fontWeight: 700, color: T.accent,
                          letterSpacing: "0.1em", textTransform: "uppercase",
                          marginBottom: 20,
                        }}>
                          <div style={{ width: 5, height: 5, borderRadius: "50%", background: T.accent3, animation: "glowPulse 2s infinite" }} />
                          Online · Ready to Help
                        </div>

                        <h1 style={{
                          fontFamily: "'Instrument Serif', serif",
                          fontSize: "clamp(32px,4vw,52px)",
                          fontWeight: 400,
                          fontStyle: "italic",
                          lineHeight: 1.1,
                          letterSpacing: "-0.02em",
                          color: T.text,
                          marginBottom: 8,
                        }}>
                          Clinical AI,
                        </h1>
                        <h1 style={{
                          fontFamily: "'DM Sans', sans-serif",
                          fontSize: "clamp(32px,4vw,52px)",
                          fontWeight: 800,
                          lineHeight: 1.1,
                          letterSpacing: "-0.04em",
                          color: T.accent,
                          marginBottom: 24,
                        }}>
                          Human Understanding.
                        </h1>
                        <p style={{
                          fontSize: 15, color: T.textSub, lineHeight: 1.65,
                          maxWidth: 380, marginBottom: 32, fontWeight: 400,
                        }}>
                          Describe symptoms in English, Hindi, or Punjabi.
                          Upload scans, parse labs, get instant expert-level AI analysis.
                        </p>

                        {/* Suggested prompts — chip style */}
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 7 }}>
                          {[
                            "I have chest pain",
                            "Interpret my blood report",
                            "My blood pressure is high",
                            "Feeling tired all the time",
                          ].map((prompt, i) => (
                            <button key={i} onClick={() => setInput(prompt)} style={{
                              padding: "7px 14px",
                              borderRadius: 7,
                              background: T.surface2,
                              border: `1px solid ${T.border}`,
                              color: T.textSub, fontSize: 13, fontWeight: 500,
                              cursor: "pointer", transition: "all 0.15s",
                              fontFamily: "'DM Sans',sans-serif",
                              letterSpacing: "-0.01em",
                            }}
                              onMouseEnter={e => { e.currentTarget.style.borderColor = T.accent + "50"; e.currentTarget.style.color = T.text; e.currentTarget.style.background = T.surfaceHov; }}
                              onMouseLeave={e => { e.currentTarget.style.borderColor = T.border; e.currentTarget.style.color = T.textSub; e.currentTarget.style.background = T.surface2; }}>
                              {prompt}
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Right: robot with rings */}
                      <div style={{ flex: "0 0 auto", display: "flex", justifyContent: "center", position: "relative", width: 200, height: 200 }}>
                        {/* Orbit */}
                        <div style={{
                          position: "absolute", inset: -24, borderRadius: "50%",
                          border: `1px solid ${T.accent}18`,
                          animation: "float 7s ease-in-out infinite",
                        }} />
                        <div style={{
                          position: "absolute", inset: -6, borderRadius: "50%",
                          border: `1px solid ${T.accent}12`,
                          animation: "float 5s ease-in-out 1s infinite",
                        }} />
                        {/* Orbiting dot */}
                        <div style={{
                          position: "absolute", top: "50%", left: "50%",
                          width: 7, height: 7, borderRadius: "50%",
                          background: T.accent,
                          boxShadow: `0 0 10px ${T.accent}`,
                          transformOrigin: "-88px -3.5px",
                          animation: "orbitDot 5s linear infinite",
                        }} />
                        {/* Main avatar */}
                        <div style={{
                          width: 200, height: 200, borderRadius: "50%",
                          background: T.isDark
                            ? `radial-gradient(circle at 35% 35%, ${T.accent}18 0%, rgba(0,0,0,0) 70%)`
                            : `radial-gradient(circle at 35% 35%, ${T.accent}10 0%, rgba(255,255,255,0) 70%)`,
                          border: `1px solid ${T.border}`,
                          display: "flex", alignItems: "center", justifyContent: "center",
                          position: "relative",
                        }}>
                          <RobotDoc isThinking={false} T={T} size={110} />
                          {/* Online dot */}
                          <div style={{
                            position: "absolute", bottom: 16, right: 16,
                            width: 14, height: 14, borderRadius: "50%",
                            background: T.accent3,
                            border: `2px solid ${T.isDark ? "#03050a" : "#f1f5ff"}`,
                          }} />
                        </div>
                      </div>
                    </div>

                    {/* ── CAPABILITIES ROW — horizontal, editorial ── */}
                    <div style={{
                      borderTop: `1px solid ${T.border}`,
                      paddingTop: 28,
                    }}>
                      <div style={{
                        fontSize: 11, fontWeight: 700, letterSpacing: "0.1em",
                        textTransform: "uppercase", color: T.textMuted,
                        marginBottom: 18,
                      }}>What I can do</div>
                      <div className="ma-feature-grid stagger" style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(4,1fr)",
                        gap: 1,
                      }}>
                        {[
                          {
                            icon: Mic,
                            title: "Voice Input",
                            desc: "Speak in any language and get a response in kind",
                            color: T.accent,
                            action: () => { if (!isRecording) startRecording(); else stopRecording(); },
                            hint: "Tap to speak",
                          },
                          {
                            icon: ImageIcon,
                            title: "Scan Analysis",
                            desc: "Upload X-rays, MRIs, ultrasounds for AI reading",
                            color: T.accent2,
                            action: () => document.getElementById("feat-image-upload")?.click(),
                            hint: "Upload a scan",
                          },
                          {
                            icon: Microscope,
                            title: "Lab Reports",
                            desc: "Upload PDFs or photos, values extracted instantly",
                            color: T.accent3,
                            action: () => document.getElementById("feat-report-upload")?.click(),
                            hint: "Upload a report",
                          },
                          {
                            icon: FlaskConical,
                            title: "Clinical Tools",
                            desc: "Drug checks, symptom flows, mental health screening",
                            color: T.warn,
                            action: () => setTab("tools"),
                            hint: "Open tools",
                          },
                        ].map((f, i) => (
                          <div key={i} onClick={f.action} style={{
                            padding: "20px 18px",
                            borderRight: i < 3 ? `1px solid ${T.border}` : "none",
                            transition: "background 0.15s, transform 0.15s",
                            cursor: "pointer",
                            position: "relative",
                          }}
                            onMouseEnter={e => { e.currentTarget.style.background = T.surface2; e.currentTarget.style.transform = "translateY(-2px)"; }}
                            onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.transform = "translateY(0)"; }}>
                            <div style={{
                              width: 36, height: 36,
                              display: "flex", alignItems: "center", justifyContent: "center",
                              marginBottom: 14,
                            }}>
                              <f.icon size={22} style={{ color: f.color }} />
                            </div>
                            <div style={{
                              fontSize: 13.5, fontWeight: 700, color: T.text,
                              marginBottom: 6, letterSpacing: "-0.02em",
                            }}>{f.title}</div>
                            <div style={{
                              fontSize: 12.5, color: T.textMuted, lineHeight: 1.55, fontWeight: 400,
                            }}>{f.desc}</div>
                            {/* Hint badge */}
                            <div style={{
                              position: "absolute", bottom: 10, right: 12,
                              fontSize: 10, fontWeight: 700, color: f.color,
                              opacity: 0.65, letterSpacing: "0.04em", textTransform: "uppercase",
                            }}>{f.hint} →</div>
                          </div>
                        ))}
                      </div>
                      {/* Hidden file inputs for feature cards */}
                      <input id="feat-image-upload" type="file" accept="image/*" multiple style={{ display: "none" }} onChange={e => handleImageStage(e)} />
                      <input id="feat-report-upload" type="file" accept="image/*,.pdf" style={{ display: "none" }} onChange={handleReportUpload} />
                    </div>
                  </div>
                )}

                {/* ── MESSAGES ── */}
                <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                  {messages.map((m) => (
                    <div key={m.id} className="fade-up ma-msg-wrap" style={{
                      display: "flex",
                      justifyContent: m.role === "user" ? "flex-end" : "flex-start",
                      alignItems: "flex-end", gap: 10,
                    }}>
                      {/* Bot avatar */}
                      {m.role === "assistant" && (
                        <div style={{ flexShrink: 0, marginBottom: 4 }}>
                          <RobotDoc isThinking={!!m.isStreaming} T={T} size={38} />
                        </div>
                      )}

                      <div style={{
                        maxWidth: "76%",
                        position: "relative",
                      }}>
                        {/* Triage badge above bot messages */}
                        {m.role === "assistant" && m.triage && m.triage.level !== "low" && (
                          <div style={{
                            marginBottom: 6, display: "inline-flex", alignItems: "center", gap: 5,
                            padding: "3px 10px", borderRadius: 99, fontSize: 10.5, fontWeight: 800,
                            letterSpacing: "0.05em", textTransform: "uppercase",
                            background: m.triage.level === "emergency" ? `${T.danger}18`
                              : m.triage.level === "urgent" ? `${T.warn}18`
                              : `${T.accent2}14`,
                            border: `1px solid ${m.triage.level === "emergency" ? `${T.danger}35`
                              : m.triage.level === "urgent" ? `${T.warn}35`
                              : `${T.accent2}28`}`,
                            color: m.triage.level === "emergency" ? T.danger
                              : m.triage.level === "urgent" ? T.warn : T.accent2,
                          }}>
                            <AlertTriangle size={9} />
                            {m.triage.level}
                          </div>
                        )}

                        {/* Bubble */}
                        <div style={{
                          padding: "14px 18px", fontSize: 14, lineHeight: 1.75,
                          borderRadius: m.role === "user" ? "16px 16px 4px 16px" : "4px 16px 16px 16px",
                          background: m.role === "user"
                            ? m.error ? `${T.danger}10` : T.msgUser
                            : m.error ? `${T.danger}08` : T.msgBot,
                          border: `1px solid ${m.role === "user"
                            ? m.error ? `${T.danger}25` : T.msgUserBorder
                            : m.error ? `${T.danger}20` : T.msgBotBorder}`,
                          boxShadow: m.role === "user"
                            ? T.isDark ? `0 4px 24px rgba(0,0,0,0.3), 0 0 0 1px ${T.accent}10` : `0 4px 16px rgba(0,0,0,0.08)`
                            : T.isDark ? "0 4px 24px rgba(0,0,0,0.3)" : "0 4px 16px rgba(0,0,0,0.06)",
                          color: T.text,
                          position: "relative", overflow: "hidden",
                        }}>
                          {/* Top shimmer line on user bubbles */}
                          {m.role === "user" && !m.error && (
                            <div style={{
                              position: "absolute", top: 0, left: 0, right: 0, height: 1,
                              background: `linear-gradient(90deg, transparent, ${T.accent}60, transparent)`,
                            }} />
                          )}

                          {/* Image preview */}
                          {m.imageUrl && (
                            <img src={m.imageUrl} alt="Upload" style={{
                              borderRadius: 10, marginBottom: 10,
                              maxHeight: 200, maxWidth: "100%",
                              objectFit: "cover", display: "block",
                              border: `1px solid ${T.border}`,
                              boxShadow: "0 2px 12px rgba(0,0,0,0.15)",
                            }} />
                          )}

                          {/* Voice label */}
                          {m.isVoice && (
                            <div style={{
                              display: "inline-flex", alignItems: "center", gap: 5,
                              fontSize: 10.5, color: T.accent, marginBottom: 8, fontWeight: 700,
                              padding: "2px 8px", borderRadius: 6,
                              background: `${T.accent}12`, border: `1px solid ${T.accent}22`,
                            }}>
                              <Mic size={10} />
                              Voice {m.language ? `· ${VOICE_LANGUAGES.find(l => l.code === m.language)?.label || m.language}` : ""}
                            </div>
                          )}

                          {/* Vision description tag */}
                          {m.visionDesc && (
                            <div style={{
                              fontSize: 12, padding: "6px 11px", borderRadius: 8,
                              background: `${T.accent}0a`, border: `1px solid ${T.accent}18`,
                              color: T.accent, marginBottom: 10, lineHeight: 1.5,
                              display: "flex", alignItems: "flex-start", gap: 7,
                            }}>
                              <Eye size={11} style={{ marginTop: 2, flexShrink: 0 }} />
                              <span>{m.visionDesc}</span>
                            </div>
                          )}

                          {/* Message text */}
                          <div style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                            {formatText(m.text, T.accent)}
                            {m.isStreaming && <span className="ma-cursor" />}
                          </div>

                          {/* Audio player */}
                          {m.audio_url && (
                            <AudioPlayer audioUrl={`${API}${m.audio_url}`} T={T} />
                          )}

                          {/* Bottom row: time + actions */}
                          <div style={{
                            display: "flex", alignItems: "center",
                            justifyContent: "space-between",
                            marginTop: 10, paddingTop: 8,
                            borderTop: `1px solid ${T.border}`,
                            flexWrap: "wrap", gap: 4,
                          }}>
                            <div style={{ fontSize: 10, color: T.textMuted, fontFamily: "'Fira Code',monospace", opacity: 0.6 }}>
                              {m.timestamp?.toLocaleTimeString?.([], { hour: "2-digit", minute: "2-digit" })}
                            </div>
                            {!m.isStreaming && m.text && (
                              <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
                                {m.role === "assistant" && (
                                  <button onClick={() => { setShowNearbyDoctor(true); setTab("tools"); }} style={{
                                    display: "inline-flex", alignItems: "center", gap: 4,
                                    padding: "3px 9px", borderRadius: 7,
                                    background: `${T.accent3}10`, border: `1px solid ${T.accent3}28`,
                                    color: T.accent3, fontSize: 10.5, fontWeight: 700,
                                    cursor: "pointer", transition: "all 0.12s",
                                    fontFamily: "'DM Sans',sans-serif",
                                  }}
                                    onMouseEnter={e => e.currentTarget.style.background = `${T.accent3}20`}
                                    onMouseLeave={e => e.currentTarget.style.background = `${T.accent3}10`}>
                                    <MapPin size={10} /> Find Doctor
                                  </button>
                                )}
                                <button onClick={() => copyMessage(m.id, m.text)} style={{
                                  display: "inline-flex", alignItems: "center", gap: 4,
                                  padding: "3px 9px", borderRadius: 7,
                                  background: "transparent", border: `1px solid transparent`,
                                  color: T.textMuted, fontSize: 10.5, fontWeight: 600,
                                  cursor: "pointer", transition: "all 0.12s",
                                  fontFamily: "'DM Sans',sans-serif",
                                }}
                                  onMouseEnter={e => { e.currentTarget.style.background = T.surface2; e.currentTarget.style.borderColor = T.border; e.currentTarget.style.color = T.text; }}
                                  onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.borderColor = "transparent"; e.currentTarget.style.color = T.textMuted; }}>
                                  {copiedMsgId === m.id
                                    ? <><Check size={10} style={{ color: T.accent3 }} /> Copied</>
                                    : <><Clipboard size={10} /> Copy</>}
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* User avatar */}
                      {m.role === "user" && (
                        <div style={{
                          flexShrink: 0, width: 32, height: 32, borderRadius: 10,
                          background: `${T.accent}18`, border: `1px solid ${T.accent}28`,
                          display: "flex", alignItems: "center", justifyContent: "center",
                          fontSize: 13, fontWeight: 800, color: T.accent, marginBottom: 4,
                        }}>
                          {(patientInfo?.name?.[0] || "U").toUpperCase()}
                        </div>
                      )}
                    </div>
                  ))}

                  {/* Loading state — animated thinking indicator */}
                  {isLoading && messages.length > 0 && !messages[messages.length - 1]?.isStreaming && (
                    <div style={{ display: "flex", alignItems: "flex-end", gap: 11 }} className="fade-in">
                      <RobotDoc isThinking={true} T={T} size={40} />
                      <div style={{
                        padding: "12px 18px", borderRadius: "5px 18px 18px 18px",
                        background: T.msgBot, border: `1px solid ${T.msgBotBorder}`,
                        display: "inline-flex", flexDirection: "column", gap: 6,
                        boxShadow: T.isDark ? "0 4px 20px rgba(0,0,0,0.25)" : "0 4px 16px rgba(0,0,0,0.06)",
                      }}>
                        <div style={{ display: "flex", gap: 5, alignItems: "center" }}>
                          <div className="dot1" style={{ width: 7, height: 7, borderRadius: "50%", background: T.accent }} />
                          <div className="dot2" style={{ width: 7, height: 7, borderRadius: "50%", background: T.accent, opacity: 0.65 }} />
                          <div className="dot3" style={{ width: 7, height: 7, borderRadius: "50%", background: T.accent, opacity: 0.4 }} />
                        </div>
                        <div style={{ fontSize: 10.5, color: T.textMuted, fontStyle: "italic", fontWeight: 500 }}>
                          Analysing your query…
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                <div ref={endRef} />
              </div>
            </div>

            {/* ── CHAT INPUT ── */}
            <div className="ma-chatinput" style={{
              borderTop: `1px solid ${T.border}`,
              background: T.isDark ? "rgba(3,5,10,0.9)" : "rgba(250,252,255,0.94)",
              backdropFilter: "blur(24px)", WebkitBackdropFilter: "blur(24px)",
              padding: "14px 22px 16px", flexShrink: 0,
            }}>
              <div style={{ maxWidth: 780, margin: "0 auto" }}>
                {/* Mode row */}
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 10, flexWrap: "wrap" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 5, padding: "3px 4px", borderRadius: 99, background: T.surface2, border: `1px solid ${T.border}` }}>
                    {[["fast", "Fast", Zap], ["balanced", "Balanced", Activity], ["detailed", "Detailed", BookOpen]].map(([key, label, Icon]) => (
                      <button key={key} onClick={() => setGenMode(key)} className={`ma-mode-pill ${genMode === key ? "active" : ""}`} style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                        <Icon size={11} />{label}
                      </button>
                    ))}
                  </div>
                  {/* Model Selector */}
                  <div style={{ position: "relative" }}>
                    <button onClick={() => setShowModelMenu(v => !v)} style={{
                      display: "inline-flex", alignItems: "center", gap: 5,
                      padding: "4px 10px", borderRadius: 99, cursor: "pointer",
                      background: selectedModel !== "core" ? `${T.accent2}15` : T.surface2,
                      border: `1px solid ${selectedModel !== "core" ? T.accent2 + "40" : T.border}`,
                      color: selectedModel !== "core" ? T.accent2 : T.textMuted,
                      fontSize: 11.5, fontWeight: 600, fontFamily: "'DM Sans',sans-serif",
                      transition: "all 0.15s",
                    }}>
                      <Cpu size={11} />
                      {modelProviders.find(p => p.id === selectedModel)?.label || "Core (Llama)"}
                      <ChevronDown size={10} />
                    </button>
                    {showModelMenu && (
                      <div className="pop-in" style={{
                        position: "absolute", bottom: "110%", left: 0,
                        minWidth: 200, padding: 6, borderRadius: 12,
                        background: T.surface, border: `1px solid ${T.border}`,
                        boxShadow: `0 12px 40px rgba(0,0,0,0.3)`, zIndex: 50,
                      }}>
                        {modelProviders.map(p => (
                          <button key={p.id} onClick={() => { setSelectedModel(p.id); setShowModelMenu(false); }}
                            style={{
                              display: "flex", alignItems: "center", gap: 8, width: "100%",
                              padding: "8px 12px", borderRadius: 8, cursor: p.available ? "pointer" : "not-allowed",
                              background: selectedModel === p.id ? `${T.accent}15` : "transparent",
                              border: "none", color: p.available ? T.text : T.textMuted,
                              fontSize: 12.5, fontWeight: selectedModel === p.id ? 700 : 500,
                              fontFamily: "'DM Sans',sans-serif", textAlign: "left",
                              opacity: p.available ? 1 : 0.5, transition: "all 0.1s",
                            }}
                            onMouseEnter={e => { if (p.available) e.currentTarget.style.background = `${T.accent}10`; }}
                            onMouseLeave={e => { e.currentTarget.style.background = selectedModel === p.id ? `${T.accent}15` : "transparent"; }}
                          >
                            <span style={{ width: 6, height: 6, borderRadius: "50%", background: p.available ? T.accent3 : T.textMuted, flexShrink: 0 }} />
                            <span>{p.label}</span>
                            {selectedModel === p.id && <Check size={12} style={{ marginLeft: "auto", color: T.accent }} />}
                            {!p.available && p.id !== "core" && <span style={{ marginLeft: "auto", fontSize: 10, color: T.textMuted }}>No key</span>}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  {selectedSpecialist && (
                    <div style={{ fontSize: 11.5, color: T.accent2, fontWeight: 600, padding: "3px 10px", borderRadius: 99, background: `${T.accent2}10`, border: `1px solid ${T.accent2}25` }}>
                      <Stethoscope size={10} style={{ display: "inline", marginRight: 5 }} />{selectedSpecialist.name}
                    </div>
                  )}
                  <div style={{ marginLeft: "auto", display: "flex", gap: 5 }}>
                    {/* Vitals quick-log toggle */}
                    <button onClick={() => setShowVitalsLog(v => !v)} title="Log vitals quickly" style={{
                      display: "flex", alignItems: "center", gap: 5,
                      padding: "4px 10px", borderRadius: 7, cursor: "pointer",
                      background: showVitalsLog ? `${T.accent3}18` : "transparent",
                      border: `1px solid ${showVitalsLog ? T.accent3 + "45" : T.border}`,
                      color: showVitalsLog ? T.accent3 : T.textMuted,
                      fontSize: 11.5, fontWeight: 700, transition: "all 0.15s",
                      fontFamily: "'DM Sans',sans-serif",
                    }}
                      onMouseEnter={e => { e.currentTarget.style.borderColor = T.accent3; e.currentTarget.style.color = T.accent3; }}
                      onMouseLeave={e => { e.currentTarget.style.borderColor = showVitalsLog ? T.accent3 + "45" : T.border; e.currentTarget.style.color = showVitalsLog ? T.accent3 : T.textMuted; }}>
                      <Activity size={12} /> Log Vitals
                    </button>
                    {/* Export session */}
                    {messages.length > 0 && (
                      <button onClick={exportSession} title="Export conversation" style={{
                        display: "flex", alignItems: "center", gap: 5,
                        padding: "4px 10px", borderRadius: 7, cursor: "pointer",
                        background: "transparent", border: `1px solid ${T.border}`,
                        color: T.textMuted, fontSize: 11.5, fontWeight: 700,
                        transition: "all 0.15s", fontFamily: "'DM Sans',sans-serif",
                      }}
                        onMouseEnter={e => { e.currentTarget.style.borderColor = T.accent2; e.currentTarget.style.color = T.accent2; }}
                        onMouseLeave={e => { e.currentTarget.style.borderColor = T.border; e.currentTarget.style.color = T.textMuted; }}>
                        <Download size={12} /> Export
                      </button>
                    )}
                  </div>
                </div>

                {/* ── VITALS QUICK-LOG PANEL ── */}
                {showVitalsLog && (
                  <div className="fade-up" style={{
                    marginBottom: 12, padding: "14px 16px", borderRadius: 13,
                    background: T.surface2, border: `1px solid ${T.border}`,
                    borderTop: `3px solid ${T.accent3}`,
                  }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
                      <div style={{ fontSize: 13, fontWeight: 800, color: T.accent3, display: "flex", alignItems: "center", gap: 7 }}>
                        <Activity size={14} /> Quick Vitals Log
                      </div>
                      <button onClick={() => setShowVitalsLog(false)} style={{ background: "none", border: "none", cursor: "pointer", color: T.textMuted, display: "flex" }}><X size={13} /></button>
                    </div>
                    <div className="ma-vitals-grid">
                      {[
                        { key: "bp_systolic", label: "BP Systolic", placeholder: "e.g. 120", unit: "mmHg", icon: "🩺" },
                        { key: "bp_diastolic", label: "BP Diastolic", placeholder: "e.g. 80", unit: "mmHg", icon: "🩺" },
                        { key: "heart_rate", label: "Heart Rate", placeholder: "e.g. 72", unit: "bpm", icon: "💓" },
                        { key: "weight_kg", label: "Weight", placeholder: "e.g. 70", unit: "kg", icon: "⚖️" },
                        { key: "temperature", label: "Temperature", placeholder: "e.g. 37.0", unit: "°C", icon: "🌡️" },
                        { key: "spo2", label: "SpO₂", placeholder: "e.g. 98", unit: "%", icon: "🫁" },
                      ].map(v => (
                        <div key={v.key}>
                          <label style={{ fontSize: 11, fontWeight: 700, color: T.textMuted, textTransform: "uppercase", letterSpacing: "0.07em", display: "block", marginBottom: 4 }}>
                            {v.icon} {v.label} <span style={{ opacity: 0.6 }}>({v.unit})</span>
                          </label>
                          <input
                            type="number"
                            placeholder={v.placeholder}
                            value={vitalsForm[v.key]}
                            onChange={e => setVitalsForm(p => ({ ...p, [v.key]: e.target.value }))}
                            className="ma-input"
                            style={{ fontSize: 13.5, padding: "8px 12px", fontFamily: "'Fira Code',monospace" }}
                          />
                        </div>
                      ))}
                    </div>
                    <button
                      onClick={submitVitals}
                      disabled={vitalsSubmitting || Object.values(vitalsForm).every(v => !v.trim())}
                      style={{
                        marginTop: 12, width: "100%",
                        padding: "10px", borderRadius: 10,
                        background: T.accent3, border: "none",
                        color: "white", fontSize: 14, fontWeight: 800,
                        cursor: "pointer", fontFamily: "'DM Sans',sans-serif",
                        display: "flex", alignItems: "center", justifyContent: "center", gap: 7,
                        opacity: vitalsSubmitting ? 0.6 : 1,
                        boxShadow: `0 4px 16px ${T.accent3}40`,
                      }}>
                      {vitalsSubmitting ? <Loader2 size={15} style={{ animation: "spin 1s linear infinite" }} /> : <Check size={15} />}
                      {vitalsSubmitting ? "Saving…" : "Save Vitals"}
                    </button>
                  </div>
                )}

                {/* ── IMAGE STAGING PANEL ── */}
                {showImageStage && stagedImages.length > 0 && (
                  <div className="fade-up" style={{
                    marginBottom: 10, padding: "14px 16px", borderRadius: 14,
                    background: T.surface2,
                    border: `1px solid ${T.accent2}30`,
                    borderTop: `3px solid ${T.accent2}`,
                    boxShadow: `0 4px 20px ${T.accent2}12`,
                  }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
                      <span style={{ fontSize: 13, fontWeight: 800, color: T.accent2, display: "flex", alignItems: "center", gap: 7 }}>
                        <ImageIcon size={15} />
                        {stagedImages.length} image{stagedImages.length > 1 ? "s" : ""} ready to send
                      </span>
                      <button onClick={() => { setStagedImages([]); setShowImageStage(false); setImageCaption(""); }}
                        style={{ background: "none", border: "none", cursor: "pointer", color: T.textMuted, display: "flex", padding: 4, borderRadius: 6, transition: "background 0.12s" }}
                        onMouseEnter={e => e.currentTarget.style.background = T.surface3}
                        onMouseLeave={e => e.currentTarget.style.background = "none"}>
                        <X size={14} />
                      </button>
                    </div>

                    {/* Image previews */}
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
                      {stagedImages.map(s => (
                        <div key={s.id} style={{ position: "relative", flexShrink: 0 }}>
                          <img src={s.url} alt="" style={{
                            width: 80, height: 80, borderRadius: 10, objectFit: "cover",
                            border: `2px solid ${T.accent2}40`,
                            boxShadow: `0 2px 12px rgba(0,0,0,0.2)`,
                          }} />
                          <button onClick={() => removeStagedImage(s.id)} style={{
                            position: "absolute", top: -6, right: -6, width: 20, height: 20, borderRadius: "50%",
                            background: T.danger, border: `2px solid ${T.isDark ? "#03050a" : "#f1f5ff"}`,
                            cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
                            boxShadow: "0 2px 6px rgba(0,0,0,0.3)",
                          }}>
                            <X size={10} color="white" />
                          </button>
                        </div>
                      ))}
                      {/* Add more images */}
                      <label style={{
                        width: 80, height: 80, borderRadius: 10,
                        border: `2px dashed ${T.accent2}40`,
                        display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
                        cursor: "pointer", flexShrink: 0, gap: 4,
                        transition: "border-color 0.15s, background 0.15s",
                      }}
                        onMouseEnter={e => { e.currentTarget.style.borderColor = T.accent2; e.currentTarget.style.background = `${T.accent2}08`; }}
                        onMouseLeave={e => { e.currentTarget.style.borderColor = `${T.accent2}40`; e.currentTarget.style.background = "none"; }}>
                        <input type="file" accept="image/*" multiple onChange={handleImageStage} style={{ display: "none" }} />
                        <Plus size={18} style={{ color: T.textMuted }} />
                        <span style={{ fontSize: 10, color: T.textMuted, fontWeight: 600 }}>Add more</span>
                      </label>
                    </div>

                    {/* Caption input */}
                    <input value={imageCaption} onChange={e => setImageCaption(e.target.value)}
                      placeholder="Describe what you see or ask a specific question… (optional)"
                      className="ma-input"
                      style={{ fontSize: 13, marginBottom: 10, background: T.inputBg }}
                      onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendStagedImages(); } }}
                    />

                    {/* Send button */}
                    <button onClick={sendStagedImages} disabled={isLoading} style={{
                      width: "100%", padding: "10px 16px", borderRadius: 10,
                      background: T.accent2, border: "none", color: "white",
                      fontSize: 13.5, fontWeight: 700, cursor: "pointer",
                      fontFamily: "'DM Sans',sans-serif",
                      display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
                      boxShadow: `0 4px 18px ${T.accent2}40`,
                      transition: "filter 0.15s",
                    }}
                      onMouseEnter={e => e.currentTarget.style.filter = "brightness(1.1)"}
                      onMouseLeave={e => e.currentTarget.style.filter = "brightness(1)"}>
                      {isLoading ? <Loader2 size={15} style={{ animation: "spin 1s linear infinite" }} /> : <Send size={15} />}
                      Analyse {stagedImages.length} image{stagedImages.length > 1 ? "s" : ""}
                    </button>
                  </div>
                )}

                {/* Recording wave */}
                {isRecording && (
                  <div className="fade-up" style={{
                    marginBottom: 11, borderRadius: 14, padding: "10px 16px",
                    background: `${T.danger}08`, border: `1px solid ${T.danger}22`,
                  }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 7 }}>
                      <div style={{ position: "relative", display: "flex" }}>
                        <div style={{ width: 9, height: 9, borderRadius: "50%", background: T.danger }} />
                        <div style={{ position: "absolute", width: 9, height: 9, borderRadius: "50%", background: `${T.danger}60`, animation: "pulse 1.2s ease-out infinite" }} />
                      </div>
                      <span style={{ fontSize: 12.5, fontWeight: 800, color: T.danger }}>
                        Recording
                      </span>
                      {/* Language tag shown prominently in recording bar */}
                      <div style={{
                        padding: "2px 9px", borderRadius: 6,
                        background: T.accent + "18", border: `1px solid ${T.accent}35`,
                        fontSize: 11, fontWeight: 800, color: T.accent,
                        letterSpacing: "0.05em",
                      }}>
                        {VOICE_LANGUAGES.find(l => l.code === voiceLang)?.label || "Auto Detect"}
                      </div>
                    </div>
                    <VoiceVisualizer analyserRef={analyserRef} isRecording={isRecording} T={T} />
                  </div>
                )}

                {/* Input row */}
                <div style={{ display: "flex", alignItems: "flex-end", gap: 9 }}>
                  {/* Attachment buttons */}
                  <div style={{ display: "flex", gap: 4, flexShrink: 0 }}>
                    <label style={{ cursor: "pointer", position: "relative" }}>
                      <input type="file" accept="image/*" multiple onChange={handleImageStage} style={{ display: "none" }} disabled={isLoading || isRecording} />
                      <div className="ma-btn ma-btn-ghost ma-btn-icon" style={{ pointerEvents: isLoading ? "none" : "auto", opacity: isLoading ? 0.35 : 1 }}>
                        <ImageIcon size={16} />
                        {stagedImages.length > 0 && (
                          <span style={{ position: "absolute", top: -4, right: -4, background: T.accent, color: T.isDark ? "#000" : "#fff", fontSize: 9, fontWeight: 800, width: 16, height: 16, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center" }}>
                            {stagedImages.length}
                          </span>
                        )}
                      </div>
                    </label>
                    <label style={{ cursor: "pointer" }}>
                      <input type="file" accept="image/*,.pdf" onChange={handleReportUpload} style={{ display: "none" }} disabled={isLoading || isRecording} />
                      <div className="ma-btn ma-btn-ghost ma-btn-icon" style={{ pointerEvents: isLoading ? "none" : "auto", opacity: isLoading ? 0.35 : 1 }}>
                        <FileText size={16} />
                      </div>
                    </label>
                  </div>

                  {/* Textarea or Audio Visualizer */}
                  {isRecording ? (
                    <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", minHeight: 46, padding: "0 10px" }}>
                      <VoiceVisualizer analyserRef={analyserRef} isRecording={isRecording} T={T} />
                    </div>
                  ) : (
                    <textarea
                      value={input}
                      onChange={e => setInput(e.target.value)}
                      onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
                      placeholder="Describe…"
                      className="ma-input ma-glow-input"
                      rows={1}
                      disabled={isLoading}
                      style={{ flex: 1, minHeight: 46, fontSize: 14, fontFamily: "'DM Sans',sans-serif" }}
                    />
                  )}

                  {/* Send or Voice */}
                  {input.trim() ? (
                    <button onClick={sendMessage} disabled={isLoading} className="ma-btn ma-btn-primary" style={{ width: 46, height: 46, padding: 0, borderRadius: 13, flexShrink: 0 }}>
                      {isLoading ? <Loader2 size={17} style={{ animation: "spin 1s linear infinite" }} /> : <Send size={16} />}
                    </button>
                  ) : (
                    <div style={{ display: "flex", gap: 6, flexShrink: 0, position: "relative" }}>
                      {/* Current language badge — always visible */}
                      {voiceLang && (
                        <div style={{
                          position: "absolute", top: -8, right: -4,
                          background: T.accent, color: T.isDark ? "#000" : "#fff",
                          fontSize: 9, fontWeight: 800, padding: "1px 5px",
                          borderRadius: 99, letterSpacing: "0.05em", pointerEvents: "none",
                          zIndex: 10,
                        }}>
                          {VOICE_LANGUAGES.find(l => l.code === voiceLang)?.abbr}
                        </div>
                      )}
                      {showLangPicker && !isRecording && (
                        <div className="ma-dropdown scale-in" style={{ position: "absolute", bottom: 54, right: 0, minWidth: 170, zIndex: 100 }}>
                          <div style={{ padding: "9px 15px 4px", fontSize: 10, fontWeight: 800, letterSpacing: "0.1em", textTransform: "uppercase", color: T.textMuted }}>Voice Language</div>
                          {VOICE_LANGUAGES.map(l => (
                            <div key={l.code || "auto"} onClick={() => { setVoiceLang(l.code); setShowLangPicker(false); }} className="ma-dropdown-item">
                              <span style={{ fontFamily: "'Fira Code',monospace", fontSize: 10, fontWeight: 700, color: T.textMuted, minWidth: 38 }}>{l.abbr}</span>
                              {l.label}
                              {voiceLang === l.code && <Check size={12} style={{ color: T.accent, marginLeft: "auto" }} />}
                            </div>
                          ))}
                        </div>
                      )}
                      <button onClick={() => setShowLangPicker(!showLangPicker)} disabled={isLoading || isRecording} className="ma-btn ma-btn-ghost ma-btn-icon" style={{ width: 46, height: 46, borderRadius: 13 }}>
                        <Globe size={16} />
                      </button>
                      <button onClick={isRecording ? stopRecording : startRecording} disabled={isLoading} className={`ma-btn ${isRecording ? "ma-btn-danger ma-recording-btn" : "ma-btn-primary"}`} style={{ width: 46, height: 46, padding: 0, borderRadius: 13 }}>
                        {isRecording ? <MicOff size={16} /> : <Mic size={16} />}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ════════════════════════════════════════
            DASHBOARD TAB
        ════════════════════════════════════════ */}
        {!seniorMode && tab === "dashboard" && (
          <div className="ma-scroll" style={{ flex: 1, padding: "26px 24px" }}>
            <div style={{ maxWidth: 1040, margin: "0 auto" }}>

              {/* ── HEALTH TRAJECTORY ALERT CARD ── */}
              {trajectory && trajectory.has_sufficient_data && trajectory.trajectories?.length > 0 && (
                <GCard style={{ marginBottom: 16, padding: 18 }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
                    <div style={{ fontSize: 15, fontWeight: 800, color: T.text, fontFamily: "'DM Sans',sans-serif", letterSpacing: "-0.02em", display: "flex", alignItems: "center", gap: 8 }}>
                      <Activity size={16} style={{ color: trajectory.alert_level === "red" ? T.danger : trajectory.alert_level === "orange" ? T.warn : T.accent3 }} />
                      Health Trajectory
                    </div>
                    <button onClick={loadTrajectory} disabled={trajectoryLoading} className="ma-btn ma-btn-ghost ma-btn-sm" style={{ gap: 5 }}>
                      {trajectoryLoading ? <Loader2 size={12} style={{ animation: "spin 1s linear infinite" }} /> : <RefreshCw size={12} />}Refresh
                    </button>
                  </div>

                  {/* Trajectory items */}
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(220px,1fr))", gap: 10 }}>
                    {trajectory.trajectories.slice(0, 6).map((t, i) => {
                      const sevColor = t.severity === "critical" ? T.danger : t.severity === "abnormal" ? T.warn : t.severity === "warning" ? "#f59e0b" : t.severity === "watch" ? T.accent : T.accent3;
                      const arrow = t.trend === "rising" ? "↑" : t.trend === "falling" ? "↓" : "→";
                      return (
                        <div key={i} className="fade-up" style={{
                          padding: "14px 16px", borderRadius: 10,
                          background: `${sevColor}08`, border: `1px solid ${sevColor}20`,
                        }}>
                          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
                            <div style={{ fontSize: 12, fontWeight: 700, color: T.text, textTransform: "capitalize" }}>{t.test_name.replace(/_/g, " ")}</div>
                            <div style={{ fontSize: 16, fontWeight: 800, color: sevColor, fontFamily: "'Fira Code',monospace" }}>{arrow}</div>
                          </div>
                          <div style={{ fontSize: 22, fontWeight: 800, color: T.text, fontFamily: "'Fira Code',monospace", lineHeight: 1, marginBottom: 6 }}>
                            {t.latest_value}<span style={{ fontSize: 11, fontWeight: 500, color: T.textMuted, marginLeft: 4 }}>{t.unit}</span>
                          </div>
                          <div style={{ fontSize: 11, color: T.textMuted, marginBottom: 4 }}>
                            {t.trend !== "stable" && <span style={{ color: sevColor, fontWeight: 700 }}>{t.percent_change > 0 ? "+" : ""}{t.percent_change}%</span>}
                            {t.trend !== "stable" ? ` over ${t.timespan_days}d` : "Stable"}
                            {t.acceleration === "accelerating" && <span style={{ color: T.danger, fontWeight: 700 }}> ⚡ accelerating</span>}
                          </div>
                          {t.intervention_window_days != null && (
                            <div style={{ fontSize: 11, fontWeight: 700, color: sevColor, padding: "3px 8px", borderRadius: 5, background: `${sevColor}15`, display: "inline-block" }}>
                              Intervene within {t.intervention_window_days}d
                            </div>
                          )}
                          {t.projected && t.trend !== "stable" && (
                            <div style={{ fontSize: 10, color: T.textMuted, marginTop: 4 }}>
                              Projected: {t.projected["3m"]} (3m) → {t.projected["6m"]} (6m)
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {/* Medication correlations */}
                  {trajectory.medication_correlations?.length > 0 && (
                    <div style={{ marginTop: 14, padding: "12px 14px", borderRadius: 8, background: T.surface2, border: `1px solid ${T.border}` }}>
                      <div style={{ fontSize: 12, fontWeight: 700, color: T.text, marginBottom: 8, display: "flex", alignItems: "center", gap: 6 }}>
                        <Pill size={13} style={{ color: T.accent2 }} />Medication Effects Detected
                      </div>
                      {trajectory.medication_correlations.slice(0, 3).map((c, i) => (
                        <div key={i} style={{ fontSize: 11, color: T.textMuted, marginBottom: 4, display: "flex", alignItems: "center", gap: 6 }}>
                          <div style={{ width: 5, height: 5, borderRadius: "50%", background: c.direction === "improved" ? T.accent3 : c.direction === "worsened" ? T.danger : T.warn, flexShrink: 0 }} />
                          <span><strong style={{ color: T.text }}>{c.medication}</strong>: {c.test_name.replace(/_/g, " ")} {c.percent_change > 0 ? "+" : ""}{c.percent_change}% ({c.direction})</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Recurring symptoms */}
                  {trajectory.symptom_patterns?.symptoms?.filter(s => s.recurring).length > 0 && (
                    <div style={{ marginTop: 10, padding: "10px 14px", borderRadius: 8, background: T.surface2, border: `1px solid ${T.border}` }}>
                      <div style={{ fontSize: 12, fontWeight: 700, color: T.text, marginBottom: 6 }}>Recurring Symptoms</div>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
                        {trajectory.symptom_patterns.symptoms.filter(s => s.recurring).map((s, i) => (
                          <span key={i} style={{ fontSize: 11, padding: "3px 10px", borderRadius: 6, background: `${T.warn}12`, border: `1px solid ${T.warn}22`, color: T.warn, fontWeight: 600 }}>
                            {s.symptom} ({s.mentions}×)
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </GCard>
              )}

              {/* Not enough data message */}
              {trajectory && !trajectory.has_sufficient_data && (
                <div style={{ padding: "14px 18px", borderRadius: 10, background: `${T.accent}06`, border: `1px solid ${T.accent}15`, marginBottom: 16, fontSize: 12, color: T.textMuted, display: "flex", alignItems: "center", gap: 10 }}>
                  <Activity size={15} style={{ color: T.accent, flexShrink: 0 }} />
                  <span>Health Trajectory will activate after you add lab results on at least 2 different dates. Upload a lab report or add values manually.</span>
                </div>
              )}

              {/* Stats row */}
              <div className="ma-stats-grid stagger" style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 1, marginBottom: 20, border: `1px solid ${T.border}`, borderRadius: 12, overflow: "hidden" }}>
                {[
                  { label: "Consultations", value: sessions.length, color: T.accent, icon: MessageSquare },
                  { label: "Lab Tests", value: labResults.length, color: T.accent3, icon: Microscope },
                  { label: "Scans", value: medImages.length, color: T.accent2, icon: ImageIcon },
                  { label: "Timeline", value: dashboard?.timeline?.length || 0, color: T.warn, icon: Clock },
                ].map((stat, i) => (
                  <div key={i} style={{
                    padding: "18px 20px",
                    background: T.surface,
                    borderRight: i < 3 ? `1px solid ${T.border}` : "none",
                    position: "relative", overflow: "hidden",
                    transition: "background 0.15s",
                  }}
                    onMouseEnter={e => e.currentTarget.style.background = T.surface2}
                    onMouseLeave={e => e.currentTarget.style.background = T.surface}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
                      <stat.icon size={15} style={{ color: stat.color }} />
                      <div style={{ fontSize: 11, color: T.textMuted, fontWeight: 500 }}>{stat.label}</div>
                    </div>
                    <div className="ma-metric-num" style={{
                      fontSize: 34, fontWeight: 800, color: T.text,
                      fontFamily: "'Fira Code',monospace", lineHeight: 1, letterSpacing: "-0.03em",
                    }}>{stat.value}</div>
                    {/* Bottom color bar */}
                    <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: 2, background: stat.color, opacity: 0.35 }} />
                  </div>
                ))}
              </div>

              {/* Health Score + Risk Predictions */}
              <div className="ma-score-grid" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
                <GCard>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 18 }}>
                    <div style={{ fontSize: 16, fontWeight: 800, color: T.text, fontFamily: "'DM Sans',sans-serif", letterSpacing: "-0.02em", display: "flex", alignItems: "center", gap: 8 }}>

                      Health Score
                    </div>
                    <button onClick={loadHealthScore} disabled={hsLoading} className="ma-btn ma-btn-ghost ma-btn-sm" style={{ gap: 5 }}>
                      {hsLoading ? <Loader2 size={12} style={{ animation: "spin 1s linear infinite" }} /> : <Activity size={12} />}Calculate
                    </button>
                  </div>
                  {healthScore ? (
                    <div className="ma-score-wrap" style={{ display: "flex", alignItems: "center", gap: 24 }}>
                      <ScoreRing score={healthScore.score} size={104} T={T} />
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 17, fontWeight: 800, marginBottom: 8, color: T.text }}>
                          Grade&nbsp;<span style={{ color: T.accent, fontFamily: "'Fira Code',monospace" }}>{healthScore.grade}</span>
                        </div>
                        {healthScore.factors?.slice(0, 3).map((f, i) => (
                          <div key={i} style={{ fontSize: 12, color: T.textMuted, marginBottom: 3, display: "flex", alignItems: "center", gap: 5 }}>
                            <div style={{ width: 6, height: 6, borderRadius: "50%", background: f.impact > 0 ? T.accent3 : T.danger, flexShrink: 0 }} />
                            {f.impact > 0 ? "+" : ""}{f.impact} {f.factor}
                          </div>
                        ))}
                        {healthScore.recommendations?.slice(0, 2).map((r, i) => (
                          <div key={i} style={{ fontSize: 12, color: T.accent, marginTop: 5, display: "flex", alignItems: "center", gap: 5 }}>
                            <ChevronRight size={11} />  {r}
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: "20px 0", gap: 12 }}>
                      <div style={{ width: 80, height: 80, borderRadius: "50%", border: `2px dashed ${T.border}`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                        <Activity size={28} style={{ color: T.textMuted, opacity: 0.4 }} />
                      </div>
                      <div style={{ color: T.textMuted, fontSize: 13, textAlign: "center", lineHeight: 1.5 }}>Add health data and<br />click Calculate</div>
                    </div>
                  )}
                </GCard>

                <GCard>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 18 }}>
                    <div style={{ fontSize: 16, fontWeight: 800, color: T.text, fontFamily: "'DM Sans',sans-serif", letterSpacing: "-0.02em", display: "flex", alignItems: "center", gap: 8 }}>

                      Risk Predictions
                    </div>
                    <button onClick={loadRiskPredictions} disabled={riskLoading} className="ma-btn ma-btn-ghost ma-btn-sm">
                      {riskLoading ? <Loader2 size={12} style={{ animation: "spin 1s linear infinite" }} /> : <AlertTriangle size={12} />}Assess
                    </button>
                  </div>
                  {riskData?.predictions?.length > 0 ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                      {riskData.predictions.map((r, i) => (
                        <div key={i}>
                          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
                            <span style={{ fontSize: 13, fontWeight: 700, textTransform: "capitalize", color: T.text }}>{r.disease}</span>
                            <span style={{ fontSize: 13, fontWeight: 800, fontFamily: "'Fira Code',monospace", color: r.risk_pct >= 60 ? T.danger : r.risk_pct >= 30 ? T.warn : T.accent3 }}>{r.risk_pct}%</span>
                          </div>
                          <div className="ma-risk-bg">
                            <div className="ma-risk-fill" style={{
                              "--target-w": `${r.risk_pct}%`,
                              width: `${r.risk_pct}%`,
                              background: `linear-gradient(90deg,${r.risk_pct >= 60 ? T.danger : r.risk_pct >= 30 ? T.warn : T.accent3}90,${r.risk_pct >= 60 ? T.danger : r.risk_pct >= 30 ? T.warn : T.accent3})`,
                              boxShadow: `0 0 8px ${r.risk_pct >= 60 ? T.danger : r.risk_pct >= 30 ? T.warn : T.accent3}50`,
                            }} />
                          </div>
                          {r.contributors?.length > 0 && <div style={{ fontSize: 10.5, color: T.textMuted, marginTop: 3 }}>{r.contributors.slice(0, 2).join(", ")}</div>}
                        </div>
                      ))}
                      <div style={{ fontSize: 10.5, color: T.textMuted, marginTop: 2 }}>Based on {riskData.data_points} data points</div>
                    </div>
                  ) : (
                    <div style={{ color: T.textMuted, fontSize: 13, textAlign: "center", padding: "20px 0" }}>{riskData ? "No significant risks detected." : "Analyzes lab data for disease risk."}</div>
                  )}
                </GCard>
              </div>

              {/* Organ Health + Body Map */}
              <div className="ma-bodymap-grid" style={{ display: "grid", gridTemplateColumns: "1fr 1.5fr", gap: 16, marginBottom: 16 }}>
                <GCard>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
                    <div style={{ fontSize: 16, fontWeight: 800, color: T.text, letterSpacing: "-0.02em", display: "flex", alignItems: "center", gap: 8 }}>

                      Organ Health
                    </div>
                    <button onClick={loadOrganHealth} disabled={organLoading} className="ma-btn ma-btn-ghost ma-btn-sm">
                      {organLoading ? <Loader2 size={12} style={{ animation: "spin 1s linear infinite" }} /> : <Heart size={12} />}Scan
                    </button>
                  </div>
                  {organData?.organs?.length > 0 ? (
                    <div>
                      {organData.overall_score != null && (
                        <div style={{
                          textAlign: "center", marginBottom: 14, padding: "10px", borderRadius: 12,
                          background: organData.overall_score >= 80 ? `${T.accent3}10` : organData.overall_score >= 60 ? `${T.warn}10` : `${T.danger}10`,
                          border: `1px solid ${organData.overall_score >= 80 ? `${T.accent3}25` : organData.overall_score >= 60 ? `${T.warn}25` : `${T.danger}25`}`,
                        }}>
                          <span style={{ fontSize: 28, fontWeight: 900, fontFamily: "'Fira Code',monospace", color: organData.overall_score >= 80 ? T.accent3 : organData.overall_score >= 60 ? T.warn : T.danger }}>{organData.overall_score}</span>
                          <span style={{ fontSize: 12, color: T.textMuted, marginLeft: 5 }}>overall score</span>
                        </div>
                      )}
                      <div className="ma-organ-grid" style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 7 }}>
                        {organData.organs.map((o, i) => (
                          <div key={i} className="ma-organ">
                            <div style={{ fontSize: 18, fontWeight: 900, fontFamily: "'Fira Code',monospace", color: o.score >= 80 ? T.accent3 : o.score >= 60 ? T.warn : T.danger }}>{o.score}</div>
                            <div style={{ fontSize: 10, color: T.textMuted, marginTop: 3, textTransform: "capitalize", fontWeight: 600 }}>{o.organ}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div style={{ color: T.textMuted, fontSize: 13, textAlign: "center", padding: "24px 0" }}>{organData ? "Not enough data." : "Heart, liver, kidney & more."}</div>
                  )}
                </GCard>

                {/* Body Map */}
                <GCard>
                  <div style={{ fontSize: 16, fontWeight: 800, color: T.text, letterSpacing: "-0.02em", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>

                    Body Map
                  </div>
                  <div style={{ display: "flex", gap: 18 }}>
                    <div style={{ flexShrink: 0 }}>
                      <svg width="200" height="275" viewBox="0 0 300 400">
                        <defs>
                          <linearGradient id="bmg" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor={T.isDark ? "#0d1626" : "#eef3ff"} />
                            <stop offset="100%" stopColor={T.isDark ? "#060c18" : "#e4eeff"} />
                          </linearGradient>
                          <filter id="bmglow">
                            <feGaussianBlur stdDeviation="2" result="blur" />
                            <feComposite in="SourceGraphic" in2="blur" operator="over" />
                          </filter>
                          {BODY_REGIONS.map(r => <clipPath key={`c-${r.id}`} id={`bmc-${r.id}`}><circle cx={r.cx} cy={r.cy} r="20" /></clipPath>)}
                        </defs>
                        <rect width="300" height="400" rx="18" fill="url(#bmg)" stroke={T.border} strokeWidth="1" />
                        {/* Body outline */}
                        {[["150 55 150 230", "body"], ["150 100 80 190", "la"], ["150 100 220 190", "ra"], ["150 230 125 370", "ll"], ["150 230 175 370", "rl"]].map(([pts, k]) => (
                          <polyline key={k} points={pts} fill="none" stroke={T.isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,128,0.08)"} strokeWidth="2" />
                        ))}
                        <ellipse cx="150" cy="32" rx="21" ry="24" fill="none" stroke={T.isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,128,0.08)"} strokeWidth="2" />
                        {/* Region dots */}
                        {BODY_REGIONS.map(r => {
                          const hasData = bodyMapData[r.id];
                          const hasImg = regionImages[r.id]?.url;
                          const sel = selectedRegion === r.id;
                          return (
                            <g key={r.id} onClick={() => setSelectedRegion(r.id === selectedRegion ? null : r.id)} style={{ cursor: "pointer" }}>
                              {hasImg && <image href={hasImg} x={r.cx - 20} y={r.cy - 20} width="40" height="40" clipPath={`url(#bmc-${r.id})`} opacity="0.65" preserveAspectRatio="xMidYMid slice" />}
                              {sel && <circle cx={r.cx} cy={r.cy} r="22" fill="none" stroke={T.accent} strokeWidth="1.5" strokeDasharray="4 3" opacity="0.6" />}
                              <circle cx={r.cx} cy={r.cy} r={sel ? 15 : 10}
                                fill={hasImg ? `${T.danger}20` : hasData ? `${T.danger}35` : sel ? `${T.accent}22` : "rgba(255,255,255,0.05)"}
                                stroke={hasImg ? T.danger : hasData ? T.danger : sel ? T.accent : T.isDark ? "rgba(255,255,255,0.2)" : "rgba(0,0,200,0.15)"}
                                strokeWidth={sel ? 2 : 1.5}
                                style={{ transition: "all 0.22s" }} />
                              {(hasData || hasImg) && <circle cx={r.cx + 6} cy={r.cy - 6} r="4" fill={T.danger} opacity="0.9" />}
                            </g>
                          );
                        })}
                      </svg>
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      {selectedRegion ? (() => {
                        const reg = BODY_REGIONS.find(r => r.id === selectedRegion);
                        const hist = regionImageHistory[selectedRegion] || [];
                        return (
                          <div className="fade-up">
                            <div style={{ fontSize: 15, fontWeight: 800, marginBottom: 4, color: T.text }}>{reg?.label}</div>
                            <div style={{ fontSize: 12.5, color: T.textMuted, marginBottom: 12, lineHeight: 1.5 }}>{reg?.desc}</div>
                            {hist.length > 0 && (
                              <div style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 12 }}>
                                {hist.map((img, idx) => (
                                  <div key={idx} style={{ display: "flex", alignItems: "center", gap: 9, padding: "8px 10px", borderRadius: 11, border: `1px solid ${T.border}`, background: T.surface2 }}>
                                    <img src={img.url} alt="Scan" style={{ width: 44, height: 44, borderRadius: 9, objectFit: "cover", flexShrink: 0 }} />
                                    <div style={{ flex: 1 }}>
                                      <div style={{ fontSize: 12.5, fontWeight: 700, color: T.text }}>{img.date ? new Date(img.date).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "2-digit" }) : "No date"}</div>
                                      <div style={{ fontSize: 10.5, color: T.textMuted }}>Scan #{idx + 1}</div>
                                    </div>
                                    <button onClick={() => handleDeleteImage(selectedRegion, img.imageId)} className="ma-btn ma-btn-ghost ma-btn-icon" style={{ padding: 5 }}><Trash2 size={11} /></button>
                                  </div>
                                ))}
                              </div>
                            )}
                            <label style={{ display: "inline-flex", alignItems: "center", gap: 7, padding: "8px 14px", borderRadius: 10, background: `${T.accent}12`, border: `1px solid ${T.accent}28`, color: T.accent, fontSize: 12.5, fontWeight: 700, cursor: "pointer" }}>
                              <Upload size={13} />{hist.length > 0 ? "Add Scan" : "Upload Scan"}
                              <input type="file" accept="image/*" multiple style={{ display: "none" }} onChange={e => handleImageStage(e)} />
                            </label>
                            <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 9 }}>
                              <Calendar size={12} style={{ color: T.textMuted }} />
                              <input type="date" value={uploadDate} onChange={e => setUploadDate(e.target.value)} className="ma-input" style={{ fontSize: 11.5, padding: "5px 9px", width: "auto" }} />
                            </div>
                          </div>
                        );
                      })() : (
                        <div style={{ textAlign: "center", marginTop: 48, color: T.textMuted }}>
                          <Eye size={26} style={{ margin: "0 auto 10px", opacity: 0.2, display: "block" }} />
                          <div style={{ fontSize: 13, fontWeight: 600 }}>Select a body region</div>
                          <div style={{ fontSize: 11.5, marginTop: 4, opacity: 0.6 }}>Red dots = regions with data</div>
                        </div>
                      )}
                    </div>
                  </div>
                </GCard>
              </div>

              {/* Lab Results */}
              {labResults.length > 0 && (
                <GCard style={{ padding: 0, overflow: "hidden", marginBottom: 16 }}>
                  <div style={{ padding: "15px 22px", borderBottom: `1px solid ${T.border}`, display: "flex", alignItems: "center", justifyContent: "space-between", background: T.surface }}>
                    <div style={{ fontSize: 16, fontWeight: 800, color: T.text, letterSpacing: "-0.02em", display: "flex", alignItems: "center", gap: 8 }}>
                      <FlaskConical size={16} style={{ color: T.accent2 }} />Lab Results
                    </div>
                    <span style={{ fontSize: 11, color: T.textMuted, fontFamily: "'Fira Code',monospace", padding: "2px 8px", borderRadius: 5, background: T.surface2, border: `1px solid ${T.border}` }}>{labResults.length} values</span>
                  </div>
                  <div className="ma-scroll" style={{ maxHeight: 280, overflowX: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "separate", borderSpacing: 0, minWidth: 520 }} className="ma-table">
                      <thead>
                        <tr>
                          {["Test", "Value", "Normal Range", "Status", "Date"].map(h => (
                            <th key={h} style={{ background: T.surface2, color: T.textMuted, borderBottom: `2px solid ${T.border}`, padding: "10px 16px", fontSize: 11, fontWeight: 700, letterSpacing: "0.07em", textTransform: "uppercase", whiteSpace: "nowrap" }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {labResults.slice(0, 20).map((r, i) => {
                          const statusColors = { normal: T.accent3, high: T.danger, low: T.warn, abnormal: T.danger, noted: T.accent2 };
                          const sc = statusColors[r.status] || T.textMuted;
                          return (
                            <tr key={i} style={{ background: i % 2 === 0 ? T.surface : T.surface2 }}
                              onMouseEnter={e => e.currentTarget.style.background = `${T.accent}08`}
                              onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? T.surface : T.surface2}>
                              <td style={{ padding: "11px 16px", fontWeight: 700, color: T.text, fontSize: 13, borderTop: `1px solid ${T.border}`, textTransform: "capitalize", whiteSpace: "nowrap" }}>
                                {(r.test_name || "").replace(/_/g, " ")}
                              </td>
                              <td style={{ padding: "11px 16px", fontFamily: "'Fira Code',monospace", fontSize: 13, color: sc, fontWeight: 700, borderTop: `1px solid ${T.border}`, whiteSpace: "nowrap" }}>
                                {r.value} <span style={{ fontWeight: 400, color: T.textMuted, fontSize: 11 }}>{r.unit || ""}</span>
                              </td>
                              <td style={{ padding: "11px 16px", color: T.textMuted, fontSize: 12, fontFamily: "'Fira Code',monospace", borderTop: `1px solid ${T.border}`, whiteSpace: "nowrap" }}>
                                {r.normal_range || "—"}
                              </td>
                              <td style={{ padding: "11px 16px", borderTop: `1px solid ${T.border}`, whiteSpace: "nowrap" }}>
                                <span style={{
                                  display: "inline-flex", alignItems: "center", gap: 6,
                                  padding: "3px 10px", borderRadius: 99, fontSize: 11, fontWeight: 700,
                                  background: `${sc}15`, color: sc, border: `1px solid ${sc}30`, textTransform: "capitalize",
                                }}>
                                  <span style={{ width: 6, height: 6, borderRadius: "50%", background: sc, flexShrink: 0, boxShadow: `0 0 6px ${sc}` }} />
                                  {r.status || "—"}
                                </span>
                              </td>
                              <td style={{ padding: "11px 16px", color: T.textMuted, fontSize: 12, fontFamily: "'Fira Code',monospace", borderTop: `1px solid ${T.border}`, whiteSpace: "nowrap" }}>
                                {r.date ? new Date(r.date).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "2-digit" }) : "—"}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </GCard>
              )}

              {/* Timeline */}
              {dashboard?.timeline?.length > 0 && (
                <GCard style={{ padding: 0, overflow: "hidden" }}>
                  <div style={{ padding: "15px 22px", borderBottom: `1px solid ${T.border}` }}>
                    <div style={{ fontSize: 16, fontWeight: 800, color: T.text, letterSpacing: "-0.02em", display: "flex", alignItems: "center", gap: 8 }}>
                      <Clock size={16} style={{ color: T.warn }} />Health Timeline
                    </div>
                  </div>
                  {dashboard.timeline.slice(0, 10).map((ev, i) => (
                    <div key={i} style={{
                      padding: "12px 22px",
                      borderBottom: i < 9 ? `1px solid ${T.border}` : "none",
                      display: "flex", gap: 14, alignItems: "flex-start",
                      transition: "background 0.15s",
                    }}
                      onMouseEnter={e => e.currentTarget.style.background = T.surface2}
                      onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                      <div className="ma-timeline-dot" style={{ background: ev.severity === "critical" ? T.danger : ev.severity === "urgent" ? T.warn : T.accent, boxShadow: `0 0 8px ${ev.severity === "critical" ? T.danger : ev.severity === "urgent" ? T.warn : T.accent}60` }} />
                      <div style={{ flex: 1 }}>
                        <div style={{ display: "flex", justifyContent: "space-between" }}>
                          <div style={{ fontSize: 13.5, fontWeight: 700, color: T.text }}>{ev.title}</div>
                          <div style={{ fontSize: 11, color: T.textMuted, flexShrink: 0, fontFamily: "'Fira Code',monospace" }}>{ev.date ? new Date(ev.date).toLocaleDateString(undefined, { month: "short", day: "numeric" }) : ""}</div>
                        </div>
                        {ev.description && <div style={{ fontSize: 12.5, color: T.textMuted, marginTop: 3, lineHeight: 1.5 }}>{ev.description}</div>}
                        {ev.body_region && <span style={{ display: "inline-block", fontSize: 10.5, padding: "2px 9px", borderRadius: 99, background: `${T.accent}10`, border: `1px solid ${T.accent}22`, color: T.accent, marginTop: 5, fontWeight: 600 }}>{ev.body_region.replace(/_/g, " ")}</span>}
                      </div>
                    </div>
                  ))}
                </GCard>
              )}
            </div>
          </div>
        )}

        {/* ════════════════════════════════════════
            TOOLS TAB
        ════════════════════════════════════════ */}
        {!seniorMode && tab === "tools" && (
          <div className="ma-scroll" style={{ flex: 1, padding: "26px 24px" }}>
            <div style={{ maxWidth: 860, margin: "0 auto" }}>

              {/* Tools grid */}
              {!activeTool && (
                <div className="stagger" style={{ display: "flex", flexDirection: "column", gap: 1, border: `1px solid ${T.border}`, borderRadius: 12, overflow: "hidden" }}>
                  {[
                    { icon: Search, t: "Symptom Checker", d: "AI differential diagnosis", accent: T.accent, fn: () => setShowSymptomChecker(true) },
                    { icon: Pill, t: "Drug Interactions", d: "Check medication safety", accent: T.accent3, fn: () => setShowDrugChecker(true) },
                    { icon: Brain, t: "Mental Health", d: "PHQ-9 & GAD-7 screening", accent: T.accent2, fn: () => setShowMentalHealth(true) },
                    { icon: ListChecks, t: "Medications", d: "Track & manage prescriptions", accent: T.warn, fn: () => setShowMedTracker(true) },
                    { icon: Users, t: "AI Specialists", d: "Consult specialty doctors", accent: T.accent, fn: () => setShowSpecialistPanel(true) },
                    { icon: Target, t: "Symptom Flow", d: "Guided diagnostic Q&A", accent: T.danger, fn: () => setShowSymptomFlow(true) },
                    { icon: BookOpen, t: "Treatment Plan", d: "Personalized protocol", accent: T.accent2, fn: () => setShowTreatmentPlan(true) },
                    { icon: Sparkles, t: "Health Coach", d: "Daily insights & goals", accent: T.accent3, fn: () => setShowCoachPanel(true) },
                    { icon: Shield, t: "Screening Plan", d: "Preventive health schedule", accent: T.warn, fn: () => setShowScreeningPanel(true) },
                    { icon: Microscope, t: "Microorganism ID", d: "Bacteria, virus, fungus analysis", accent: T.accent, fn: () => setShowMicroorgTool(true) },
                    { icon: MapPin, t: "Find Doctor", d: "Nearby hospitals & clinics", accent: T.accent3, fn: () => setShowNearbyDoctor(true) },
                  ].map((tool, i) => (
                    <button key={i} onClick={tool.fn} style={{
                      display: "flex", alignItems: "center", gap: 16,
                      padding: "16px 20px",
                      background: T.surface,
                      border: "none",
                      borderBottom: i < 10 ? `1px solid ${T.border}` : "none",
                      cursor: "pointer", textAlign: "left", width: "100%",
                      transition: "background 0.12s",
                      fontFamily: "'DM Sans',sans-serif",
                    }}
                      onMouseEnter={e => { e.currentTarget.style.background = T.surface2; }}
                      onMouseLeave={e => { e.currentTarget.style.background = T.surface; }}>
                      {/* Number */}
                      <div style={{
                        width: 28, height: 28, borderRadius: 6, flexShrink: 0,
                        background: `${tool.accent}12`,
                        border: `1px solid ${tool.accent}22`,
                        display: "flex", alignItems: "center", justifyContent: "center",
                        fontSize: 11, fontWeight: 800, color: tool.accent, fontFamily: "'Fira Code',monospace",
                      }}>
                        {String(i + 1).padStart(2, "0")}
                      </div>
                      {/* Icon */}
                      <tool.icon size={18} style={{ color: tool.accent, flexShrink: 0 }} />
                      {/* Text */}
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: 14, fontWeight: 700, color: T.text, letterSpacing: "-0.02em", marginBottom: 1 }}>{tool.t}</div>
                        <div style={{ fontSize: 12.5, color: T.textMuted, fontWeight: 400 }}>{tool.d}</div>
                      </div>
                      <ChevronRight size={14} style={{ color: T.textMuted, flexShrink: 0 }} />
                    </button>
                  ))}
                </div>
              )}

              {/* ── SYMPTOM CHECKER ── */}
              {showSymptomChecker && (
                <GCard>
                  <ToolHeader title="Symptom Checker" icon={Search} accent={T.accent} T={T} onClose={closeTool} />
                  <div style={{ display: "flex", gap: 9, marginBottom: 12 }}>
                    <input value={symptomInput} onChange={e => setSymptomInput(e.target.value)} onKeyDown={e => { if (e.key === "Enter") addSymptom(); }}
                      placeholder="Type a symptom and press Enter…" className="ma-input" />
                    <button onClick={addSymptom} className="ma-btn ma-btn-primary" style={{ flexShrink: 0 }}>Add</button>
                  </div>
                  {symptomTags.length > 0 && (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 7, marginBottom: 14 }}>
                      {symptomTags.map((tt, i) => (
                        <span key={i} className="ma-tag">{tt}
                          <button onClick={() => setSymptomTags(p => p.filter((_, j) => j !== i))} style={{ color: "inherit", background: "none", border: "none", cursor: "pointer", opacity: 0.7, display: "flex" }}><X size={11} /></button>
                        </span>
                      ))}
                    </div>
                  )}
                  <button onClick={runSymptomCheck} disabled={!symptomTags.length || symptomLoading} className="ma-btn ma-btn-primary" style={{ gap: 7 }}>
                    {symptomLoading ? <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> : <Zap size={14} />}Analyze Symptoms
                  </button>
                  {symptomLoading && !symptomResult && (
                    <div className="fade-up" style={{ marginTop: 16, padding: 18, borderRadius: 14, background: `${T.accent}04`, border: `1px solid ${T.accent}10` }}>
                      <div className="ma-skeleton" style={{ height: 26, width: "25%", marginBottom: 16, borderRadius: 6 }} />
                      <div className="ma-skeleton" style={{ height: 14, width: "100%", marginBottom: 8, borderRadius: 4 }} />
                      <div className="ma-skeleton" style={{ height: 14, width: "95%", marginBottom: 8, borderRadius: 4 }} />
                      <div className="ma-skeleton" style={{ height: 14, width: "88%", borderRadius: 4 }} />
                    </div>
                  )}
                  {symptomResult && (
                    <div className="fade-up" style={{ marginTop: 16, padding: 18, borderRadius: 14, background: `${T.accent}07`, border: `1px solid ${T.accent}18` }}>
                      {symptomResult.triage?.level !== "general" && (
                        <div className="ma-triage" style={{ marginBottom: 12, background: TRIAGE[symptomResult.triage?.level]?.bg, border: `1.5px solid ${TRIAGE[symptomResult.triage?.level]?.border}`, color: TRIAGE[symptomResult.triage?.level]?.color }}>
                          <AlertTriangle size={12} />{symptomResult.triage?.level?.toUpperCase()}
                        </div>
                      )}
                      <div style={{ whiteSpace: "pre-wrap", fontSize: 14, lineHeight: 1.75, color: T.text }}>{symptomResult.analysis}</div>
                    </div>
                  )}
                </GCard>
              )}

              {/* ── DRUG CHECKER ── */}
              {showDrugChecker && (
                <GCard>
                  <ToolHeader title="Drug Interaction Checker" icon={Pill} accent={T.accent3} T={T} onClose={closeTool} />
                  <div style={{ position: "relative", marginBottom: 12 }}>
                    <div style={{ display: "flex", gap: 9 }}>
                      <input value={drugInput} onChange={e => handleDrugInput(e.target.value)} onKeyDown={e => { if (e.key === "Enter") addDrug(); }}
                        placeholder="Type medication name…" className="ma-input" />
                      <button onClick={addDrug} className="ma-btn ma-btn-success" style={{ flexShrink: 0 }}>Add</button>
                    </div>
                    {drugSuggestions.length > 0 && (
                      <div className="ma-dropdown" style={{ position: "absolute", left: 0, right: 88, top: "calc(100% + 5px)", zIndex: 100 }}>
                        {drugSuggestions.map((med, i) => (
                          <div key={i} onClick={() => selectDrugSuggestion(med)} className="ma-suggest">
                            <span style={{ fontWeight: 700 }}>{med.display}</span>
                            <span style={{ fontSize: 11.5, color: T.textMuted }}>{med.category}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  {drugTags.length > 0 && (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 7, marginBottom: 14 }}>
                      {drugTags.map((d, i) => (
                        <span key={i} className="ma-tag ma-tag-green"><Pill size={11} />{d}
                          <button onClick={() => setDrugTags(p => p.filter((_, j) => j !== i))} style={{ color: "inherit", background: "none", border: "none", cursor: "pointer", opacity: 0.7, display: "flex" }}><X size={11} /></button>
                        </span>
                      ))}
                    </div>
                  )}
                  <button onClick={runDrugCheck} disabled={drugTags.length < 2 || drugLoading} className="ma-btn ma-btn-success" style={{ gap: 7 }}>
                    {drugLoading ? <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> : <Search size={14} />}Check Interactions
                  </button>
                  {drugLoading && !drugResult && (
                    <div className="fade-up" style={{ marginTop: 16, padding: 18, borderRadius: 14, background: `${T.accent3}04`, border: `1px solid ${T.accent3}10` }}>
                      <div className="ma-skeleton" style={{ height: 20, width: "35%", marginBottom: 16, borderRadius: 6 }} />
                      <div className="ma-skeleton" style={{ height: 14, width: "100%", marginBottom: 8, borderRadius: 4 }} />
                      <div className="ma-skeleton" style={{ height: 14, width: "80%", marginBottom: 12, borderRadius: 4 }} />
                      <div className="ma-skeleton" style={{ height: 11, width: "70%", borderRadius: 4 }} />
                    </div>
                  )}
                  {drugResult && (
                    <div className="fade-up" style={{ marginTop: 16, padding: 18, borderRadius: 14, background: `${T.accent3}07`, border: `1px solid ${T.accent3}18` }}>
                      <div style={{ whiteSpace: "pre-wrap", fontSize: 14, lineHeight: 1.75, color: T.text }}>{drugResult.analysis}</div>
                      <div style={{ fontSize: 11.5, color: T.textMuted, marginTop: 10 }}>{drugResult.disclaimer}</div>
                    </div>
                  )}
                </GCard>
              )}

              {/* ── MENTAL HEALTH ── */}
              {showMentalHealth && (
                <GCard>
                  <ToolHeader title="Mental Health Screening" icon={Brain} accent={T.accent2} T={T} onClose={closeTool} />
                  <div style={{ display: "flex", gap: 7, marginBottom: 20 }}>
                    {[["phq9", "PHQ-9 Depression"], ["gad7", "GAD-7 Anxiety"]].map(([k, l]) => (
                      <button key={k} onClick={() => { setMentalType(k); setMentalAnswers([]); setMentalResult(null); }} className={`ma-mh-opt ${mentalType === k ? "active" : ""}`}>{l}</button>
                    ))}
                  </div>
                  {!mentalResult ? (
                    <div>
                      <div style={{ fontSize: 13, color: T.textMuted, marginBottom: 16, padding: "10px 14px", borderRadius: 11, background: T.surface2, border: `1px solid ${T.border}`, lineHeight: 1.5 }}>
                        Over the last 2 weeks, how often have you been bothered by the following?
                      </div>
                      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                        {mentalQuestions.map((q, i) => (
                          <div key={i} style={{ padding: "13px 16px", borderRadius: 12, border: `1px solid ${T.border}`, background: T.surface2 }}>
                            <div style={{ fontSize: 13.5, marginBottom: 10, color: T.text, fontWeight: 500 }}>{i + 1}. {q}</div>
                            <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 7 }}>
                              {["Not at all", "Several days", "Half the days", "Nearly daily"].map((opt, val) => (
                                <button key={val} onClick={() => { const a = [...mentalAnswers]; a[i] = val; setMentalAnswers(a); }}
                                  style={{
                                    padding: "7px 5px", borderRadius: 9, fontSize: 11.5, fontWeight: 600, cursor: "pointer",
                                    border: mentalAnswers[i] === val ? `1.5px solid ${T.accent2}55` : `1px solid ${T.border}`,
                                    background: mentalAnswers[i] === val ? `${T.accent2}18` : T.surface,
                                    color: mentalAnswers[i] === val ? T.accent2 : T.textMuted, transition: "all 0.15s",
                                  }}>
                                  {opt} ({val})
                                </button>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                      <button onClick={submitMentalHealth} disabled={mentalAnswers.filter(a => a !== undefined).length < mentalQuestions.length}
                        className="ma-btn" style={{ marginTop: 18, background: T.accent2, color: "white", fontWeight: 800, padding: "11px 28px", boxShadow: `0 4px 20px ${T.accent2}45` }}>
                        Submit Assessment
                      </button>
                    </div>
                  ) : (
                    <div className="fade-up" style={{ padding: 22, borderRadius: 14, background: `${T.accent2}08`, border: `1px solid ${T.accent2}22` }}>
                      <div style={{ fontSize: 16, fontWeight: 800, marginBottom: 14, color: T.text }}>{mentalResult.assessment}</div>
                      <div style={{ display: "flex", alignItems: "center", gap: 24, marginBottom: 14 }}>
                        <div style={{ textAlign: "center" }}>
                          <div style={{ fontSize: 48, fontWeight: 900, fontFamily: "'Fira Code',monospace", color: T.accent2, lineHeight: 1 }}>{mentalResult.score}</div>
                          <div style={{ fontSize: 11, color: T.textMuted }}>of {mentalResult.max_score}</div>
                        </div>
                        <div>
                          <div style={{ fontWeight: 800, fontSize: 16, color: mentalResult.score > 14 ? T.danger : mentalResult.score > 9 ? T.warn : T.accent3, marginBottom: 7 }}>{mentalResult.severity}</div>
                          <div style={{ fontSize: 13.5, color: T.textSub, lineHeight: 1.5 }}>{mentalResult.recommendation}</div>
                        </div>
                      </div>
                      <button onClick={() => { setMentalResult(null); setMentalAnswers([]); }} style={{ fontSize: 13, color: T.accent2, background: "none", border: "none", cursor: "pointer", textDecoration: "underline", fontWeight: 600 }}>Retake Assessment</button>
                    </div>
                  )}
                </GCard>
              )}

              {/* ── MEDICATION TRACKER ── */}
              {showMedTracker && (
                <GCard>
                  <ToolHeader title="Medication Tracker" icon={Syringe} accent={T.warn} T={T} onClose={closeTool} />
                  <div style={{ display: "flex", gap: 9, marginBottom: 14 }}>
                    <button onClick={() => setShowMedForm(!showMedForm)} className="ma-btn ma-btn-ghost"><Plus size={14} />Add Medication</button>
                    {medications.filter(m => m.active).length >= 2 && (
                      <button onClick={checkMedInteractions} className="ma-btn ma-btn-ghost"><Pill size={14} />Check Interactions</button>
                    )}
                  </div>
                  {showMedForm && (
                    <div className="fade-up" style={{ padding: 16, borderRadius: 14, border: `1px solid ${T.border}`, background: T.surface2, marginBottom: 14 }}>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 9, marginBottom: 10 }}>
                        <div style={{ position: "relative" }}>
                          <input value={medForm.name} onChange={e => handleMedNameInput(e.target.value)} placeholder="Medicine name" className="ma-input" style={{ fontSize: 13 }} />
                          {medSuggestions.length > 0 && (
                            <div className="ma-dropdown" style={{ position: "absolute", left: 0, right: 0, top: "calc(100% + 5px)", zIndex: 100 }}>
                              {medSuggestions.map((med, i) => (
                                <div key={i} onClick={() => selectMedSuggestion(med)} className="ma-suggest">
                                  <div style={{ fontWeight: 700, fontSize: 13 }}>{med.display}</div>
                                  <div style={{ fontSize: 10.5, color: T.textMuted }}>{med.use}</div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                        <input value={medForm.dosage} onChange={e => setMedForm(p => ({ ...p, dosage: e.target.value }))} placeholder="Dosage (e.g. 500mg)" className="ma-input" style={{ fontSize: 13 }} />
                        <select value={medForm.frequency} onChange={e => setMedForm(p => ({ ...p, frequency: e.target.value }))} className="ma-input" style={{ fontSize: 13 }}>
                          {["Once daily", "Twice daily", "Three times daily", "As needed", "Weekly"].map(f => <option key={f}>{f}</option>)}
                        </select>
                      </div>
                      <button onClick={addMedication} disabled={!medForm.name.trim()} className="ma-btn" style={{ background: T.warn, color: "#020817", fontWeight: 800 }}>Save Medication</button>
                    </div>
                  )}
                  {medications.length > 0 ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: 9 }}>
                      {medications.map((m, i) => (
                        <div key={i} style={{ padding: "13px 16px", borderRadius: 13, border: `1px solid ${T.border}`, background: T.surface2, opacity: m.active ? 1 : 0.52 }}>
                          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                            <div>
                              <span style={{ fontSize: 14.5, fontWeight: 800, color: T.text }}>{m.name}</span>
                              {m.dosage && <span style={{ fontSize: 12.5, color: T.textMuted, marginLeft: 7 }}>{m.dosage}</span>}
                              <div style={{ fontSize: 12, color: T.textMuted, marginTop: 3 }}>{m.frequency}{!m.active && <span style={{ color: T.danger, fontWeight: 800 }}> · Stopped</span>}</div>
                            </div>
                            <div style={{ display: "flex", gap: 7 }}>
                              {m.active && <button onClick={() => logMedTaken(m.id)} className="ma-btn ma-btn-success ma-btn-sm"><Check size={12} />Taken</button>}
                              <button onClick={() => toggleMedActive(m.id)} className="ma-btn ma-btn-ghost ma-btn-sm ma-btn-icon">
                                {m.active ? <Square size={13} style={{ color: T.warn }} /> : <Play size={13} style={{ color: T.accent3 }} />}
                              </button>
                              <button onClick={() => deleteMed(m.id)} className="ma-btn ma-btn-ghost ma-btn-sm ma-btn-icon"><Trash2 size={13} /></button>
                            </div>
                          </div>
                          {m.active && (
                            <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 9, paddingTop: 9, borderTop: `1px solid ${T.border}`, flexWrap: "wrap" }}>
                              <label style={{ display: "flex", alignItems: "center", gap: 6, cursor: "pointer", fontSize: 12.5, color: T.textMuted, fontWeight: 600 }}>
                                <input type="checkbox" checked={!!m.reminder_enabled} onChange={e => updateMedReminder(m.id, "reminder_enabled", e.target.checked ? 1 : 0)} style={{ accentColor: T.warn }} />
                                Reminders
                              </label>
                              {!!m.reminder_enabled && (
                                <>
                                  <div style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 12.5 }}>
                                    <span style={{ color: T.textMuted, fontWeight: 600 }}>AM</span>
                                    <input type="time" value={m.reminder_morning || "08:00"} onChange={e => updateMedReminder(m.id, "reminder_morning", e.target.value)} className="ma-input" style={{ fontSize: 12, padding: "3px 8px", width: "auto" }} />
                                  </div>
                                  <div style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 12.5 }}>
                                    <span style={{ color: T.textMuted, fontWeight: 600 }}>PM</span>
                                    <input type="time" value={m.reminder_evening || "21:00"} onChange={e => updateMedReminder(m.id, "reminder_evening", e.target.value)} className="ma-input" style={{ fontSize: 12, padding: "3px 8px", width: "auto" }} />
                                  </div>
                                </>
                              )}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : <div style={{ color: T.textMuted, fontSize: 13.5, textAlign: "center", padding: "20px 0" }}>No medications tracked yet.</div>}
                </GCard>
              )}

              {/* ── AI SPECIALISTS ── */}
              {showSpecialistPanel && (
                <GCard>
                  <ToolHeader title="AI Specialist Consultation" icon={Users} accent={T.accent} T={T} onClose={closeTool} />
                  <div style={{ fontSize: 13, color: T.textMuted, marginBottom: 16, padding: "10px 14px", borderRadius: 11, background: T.surface2, border: `1px solid ${T.border}`, lineHeight: 1.5 }}>
                    Select a specialist — all subsequent messages will use their expertise and knowledge base.
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 9 }}>
                    {specialists.map((spec, i) => {
                      const Icon = SPECIALIST_ICON_MAP[spec.id] || Stethoscope;
                      return (
                        <button key={i} onClick={() => { setSelectedSpecialist(spec); closeTool(); setTab("chat"); }} className="ma-spec" style={{ textAlign: "left" }}>
                          <Icon size={20} style={{ color: T.accent, marginBottom: 9 }} />
                          <div style={{ fontSize: 13.5, fontWeight: 800, color: T.text }}>{spec.name}</div>
                        </button>
                      );
                    })}
                  </div>
                </GCard>
              )}

              {/* ── SYMPTOM FLOW ── */}
              {showSymptomFlow && (
                <GCard>
                  <ToolHeader title="Smart Symptom Flow" icon={Target} accent={T.danger} T={T} onClose={closeTool} />
                  {!flowQuestion && !flowDiagnosis ? (
                    <div>
                      <div style={{ fontSize: 13, color: T.textMuted, marginBottom: 12, lineHeight: 1.5 }}>Describe your main symptom. The AI will ask targeted questions to narrow the diagnosis.</div>
                      <div style={{ display: "flex", gap: 9 }}>
                        <input value={flowSymptom} onChange={e => setFlowSymptom(e.target.value)} onKeyDown={e => { if (e.key === "Enter") startSymptomFlow(); }}
                          placeholder="e.g. chest pain, headache, fatigue…" className="ma-input" />
                        <button onClick={startSymptomFlow} disabled={!flowSymptom.trim() || flowLoading} className="ma-btn" style={{ background: T.danger, color: "white", fontWeight: 800, flexShrink: 0, boxShadow: `0 4px 16px ${T.danger}40` }}>
                          {flowLoading ? <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> : <Zap size={14} />}Start
                        </button>
                      </div>
                    </div>
                  ) : flowDiagnosis ? (
                    <div className="fade-up" style={{ padding: 18, borderRadius: 14, background: `${T.danger}07`, border: `1px solid ${T.danger}22` }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 9, marginBottom: 12 }}>
                        <Stethoscope size={16} style={{ color: T.danger }} />
                        <div style={{ fontSize: 15, fontWeight: 800, color: T.text }}>Assessment Complete</div>
                      </div>
                      <div style={{ whiteSpace: "pre-wrap", fontSize: 14, lineHeight: 1.75, color: T.text }}>{flowDiagnosis.analysis}</div>
                      <button onClick={() => { setFlowQuestion(null); setFlowDiagnosis(null); setFlowAnswers({}); setFlowSymptom(""); setFlowSessionId(null); }} style={{ marginTop: 14, fontSize: 13, color: T.danger, background: "none", border: "none", cursor: "pointer", textDecoration: "underline", fontWeight: 700 }}>Start New Flow</button>
                    </div>
                  ) : (
                    <div className="fade-up">
                      <div style={{ padding: "14px 16px", borderRadius: 12, background: `${T.danger}07`, border: `1px solid ${T.danger}22`, marginBottom: 12 }}>
                        <div style={{ fontSize: 11, fontWeight: 800, color: T.textMuted, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 7 }}>Question {Object.keys(flowAnswers).length + 1}</div>
                        <div style={{ fontSize: 15, color: T.text, fontWeight: 500 }}>{flowQuestion.question || flowQuestion}</div>
                      </div>
                      {flowQuestion.options?.length > 0 && (
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 7, marginBottom: 12 }}>
                          {flowQuestion.options.map((opt, oi) => (
                            <button key={oi} onClick={() => answerSymptomFlow(opt)} className="ma-btn ma-btn-ghost" style={{ fontSize: 13 }}>{opt}</button>
                          ))}
                        </div>
                      )}
                      <div style={{ display: "flex", gap: 9 }}>
                        <input id="flow-ans" onKeyDown={e => { if (e.key === "Enter") { answerSymptomFlow(e.target.value); e.target.value = ""; } }
                        } placeholder="Your answer…" className="ma-input" />
                        <button onClick={() => { const el = document.getElementById("flow-ans"); answerSymptomFlow(el.value); el.value = ""; }} disabled={flowLoading}
                          className="ma-btn" style={{ background: T.danger, color: "white", fontWeight: 800, flexShrink: 0 }}>
                          {flowLoading ? <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> : "Answer"}
                        </button>
                      </div>
                      <div style={{ fontSize: 11.5, color: T.textMuted, marginTop: 10 }}>{Object.keys(flowAnswers).length} of ~5 questions answered</div>
                    </div>
                  )}
                </GCard>
              )}

              {/* ── TREATMENT PLAN ── */}
              {showTreatmentPlan && (
                <GCard>
                  <ToolHeader title="Treatment Plan Generator" icon={BookOpen} accent={T.accent2} T={T} onClose={closeTool} />
                  <div style={{ fontSize: 13, color: T.textMuted, marginBottom: 12, lineHeight: 1.5 }}>Enter a diagnosis and generate a personalized treatment protocol based on your health data.</div>
                  <div style={{ display: "flex", gap: 9, marginBottom: 14 }}>
                    <input value={treatmentCondition} onChange={e => setTreatmentCondition(e.target.value)} onKeyDown={e => { if (e.key === "Enter") generateTreatmentPlan(); }}
                      placeholder="e.g. Type 2 Diabetes, Hypertension, GERD…" className="ma-input" />
                    <button onClick={generateTreatmentPlan} disabled={!treatmentCondition.trim() || treatmentLoading} className="ma-btn" style={{ background: T.accent2, color: "white", fontWeight: 800, flexShrink: 0 }}>
                      {treatmentLoading ? <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> : <Sparkles size={14} />}Generate
                    </button>
                  </div>
                  {treatmentResult && (
                    <div className="fade-up" style={{ padding: 18, borderRadius: 14, background: `${T.accent2}07`, border: `1px solid ${T.accent2}22` }}>
                      <div style={{ whiteSpace: "pre-wrap", fontSize: 14, lineHeight: 1.75, color: T.text }}>{treatmentResult.plan || treatmentResult}</div>
                    </div>
                  )}
                </GCard>
              )}

              {/* ── HEALTH COACH ── */}
              {showCoachPanel && (
                <GCard>
                  <ToolHeader title="AI Health Coach" icon={Sparkles} accent={T.accent3} T={T} onClose={closeTool} />
                  <div style={{ display: "flex", gap: 9, marginBottom: 14 }}>
                    <button onClick={loadCoachBriefing} disabled={coachLoading} className="ma-btn ma-btn-success" style={{ gap: 7 }}>
                      {coachLoading ? <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> : <Sparkles size={14} />}Today&apos;s Briefing
                    </button>
                    <button onClick={() => setShowLifestyleForm(!showLifestyleForm)} className="ma-btn ma-btn-ghost"><TrendingUp size={14} />Log Activity</button>
                  </div>
                  {showLifestyleForm && (
                    <div className="fade-up" style={{ padding: 16, borderRadius: 14, border: `1px solid ${T.border}`, background: T.surface2, marginBottom: 14 }}>
                      <div style={{ fontSize: 13, fontWeight: 800, marginBottom: 11, color: T.textMuted }}>Track Daily Activity</div>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 9, marginBottom: 9 }}>
                        {[["steps", "Steps", "e.g. 8000"], ["distance_km", "Distance (km)", "e.g. 5.2"], ["sleep_hours", "Sleep (hours)", "e.g. 7.5"], ["calories", "Calories", "e.g. 2000"]].map(([f, l, ph]) => (
                          <div key={f}>
                            <label style={{ fontSize: 11, color: T.textMuted, display: "block", marginBottom: 5, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em" }}>{l}</label>
                            <input type="number" value={lifestyleForm[f]} onChange={e => setLifestyleForm(p => ({ ...p, [f]: e.target.value }))} placeholder={ph} className="ma-input" style={{ fontSize: 13 }} />
                          </div>
                        ))}
                        <div style={{ gridColumn: "span 2" }}>
                          <label style={{ fontSize: 11, color: T.textMuted, display: "block", marginBottom: 5, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em" }}>Water Intake (ml)</label>
                          <input type="number" value={lifestyleForm.water_ml} onChange={e => setLifestyleForm(p => ({ ...p, water_ml: e.target.value }))} placeholder="e.g. 2500" className="ma-input" style={{ fontSize: 13 }} />
                        </div>
                      </div>
                      <button onClick={logLifestyle} className="ma-btn" style={{ background: T.accent3, color: "white", fontWeight: 800 }}>Save Activity Log</button>
                    </div>
                  )}
                  {coachBriefing ? (
                    <div className="fade-up" style={{ padding: 18, borderRadius: 14, background: `${T.accent3}07`, border: `1px solid ${T.accent3}22` }}>
                      <div style={{ whiteSpace: "pre-wrap", fontSize: 14, lineHeight: 1.75, color: T.text }}>{coachBriefing.briefing || coachBriefing}</div>
                    </div>
                  ) : <div style={{ fontSize: 13.5, color: T.textMuted, textAlign: "center", padding: "20px 0" }}>Personalized health insights based on your data.</div>}
                </GCard>
              )}

              {/* ── SCREENING PLAN ── */}
              {showScreeningPanel && (
                <GCard>
                  <ToolHeader title="Preventive Screening" icon={Shield} accent={T.warn} T={T} onClose={closeTool} />
                  <div style={{ display: "flex", gap: 9, marginBottom: 14 }}>
                    <button onClick={() => setShowScreeningInputs(!showScreeningInputs)} className="ma-btn ma-btn-ghost"><Settings size={14} />Optional Info</button>
                    <button onClick={loadScreeningWithInputs} disabled={screeningLoading} className="ma-btn" style={{ background: T.warn, color: "#020817", fontWeight: 800 }}>
                      {screeningLoading ? <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> : <Calendar size={14} />}Generate Plan
                    </button>
                  </div>
                  {showScreeningInputs && (
                    <div className="fade-up" style={{ padding: 16, borderRadius: 14, border: `1px solid ${T.border}`, background: T.surface2, marginBottom: 14 }}>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 9, marginBottom: 9 }}>
                        <div>
                          <label style={{ fontSize: 11, color: T.textMuted, display: "block", marginBottom: 5, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em" }}>Smoking Status</label>
                          <select value={screeningInputs.smoker} onChange={e => setScreeningInputs(p => ({ ...p, smoker: e.target.value }))} className="ma-input" style={{ fontSize: 13 }}>
                            <option value="">Not specified</option><option value="never">Never smoked</option><option value="former">Former smoker</option><option value="current">Current smoker</option>
                          </select>
                        </div>
                        <div>
                          <label style={{ fontSize: 11, color: T.textMuted, display: "block", marginBottom: 5, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em" }}>Alcohol Use</label>
                          <select value={screeningInputs.alcohol} onChange={e => setScreeningInputs(p => ({ ...p, alcohol: e.target.value }))} className="ma-input" style={{ fontSize: 13 }}>
                            <option value="">Not specified</option><option value="none">None</option><option value="occasional">Occasional</option><option value="regular">Regular</option><option value="heavy">Heavy</option>
                          </select>
                        </div>
                      </div>
                      <input value={screeningInputs.family_history} onChange={e => setScreeningInputs(p => ({ ...p, family_history: e.target.value }))} placeholder="Family history (e.g. diabetes, cancer…)" className="ma-input" style={{ fontSize: 13, marginBottom: 7 }} />
                      <input value={screeningInputs.notes} onChange={e => setScreeningInputs(p => ({ ...p, notes: e.target.value }))} placeholder="Additional notes…" className="ma-input" style={{ fontSize: 13 }} />
                    </div>
                  )}
                  {screeningPlan?.ai_advice && (
                    <div style={{ padding: "12px 15px", borderRadius: 11, background: `${T.warn}09`, border: `1px solid ${T.warn}25`, marginBottom: 12 }}>
                      <div style={{ fontSize: 11, fontWeight: 800, color: T.warn, marginBottom: 7, letterSpacing: "0.1em", textTransform: "uppercase" }}>Personalized Advice</div>
                      <div style={{ whiteSpace: "pre-wrap", fontSize: 13, lineHeight: 1.7, color: T.text }}>{screeningPlan.ai_advice}</div>
                    </div>
                  )}
                  {screeningPlan?.plan?.length > 0 ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: 7 }}>
                      {screeningPlan.plan.map((sc, i) => (
                        <div key={i} style={{ padding: "11px 15px", borderRadius: 11, border: `1px solid ${sc.has_recent ? `${T.accent3}30` : T.border}`, background: sc.has_recent ? `${T.accent3}07` : T.surface2, display: "flex", alignItems: "flex-start", gap: 11 }}>
                          <div style={{ width: 24, height: 24, borderRadius: "50%", background: sc.has_recent ? T.accent3 : T.surface3, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, marginTop: 1, fontSize: 11, fontWeight: 800, color: sc.has_recent ? "white" : T.textMuted, boxShadow: sc.has_recent ? `0 0 8px ${T.accent3}50` : "none" }}>
                            {sc.has_recent ? <Check size={13} /> : i + 1}
                          </div>
                          <div>
                            <div style={{ fontSize: 13.5, fontWeight: 700, color: T.text }}>{sc.test}</div>
                            <div style={{ fontSize: 12, color: T.textMuted, marginTop: 2 }}>{sc.frequency} · Priority: {sc.priority}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : <div style={{ fontSize: 13.5, color: T.textMuted, textAlign: "center", padding: "16px 0" }}>{screeningPlan ? "Set age & gender in profile for recommendations." : "Age-appropriate preventive screening schedule."}</div>}
                </GCard>
              )}

              {/* ── MICROORGANISM ID TOOL ── */}
              {showMicroorgTool && (
                <GCard>
                  <ToolHeader title="Microorganism Identification" icon={Microscope} accent={T.accent} T={T} onClose={closeTool} />
                  {/* Type selector */}
                  <div style={{ display: "flex", gap: 6, marginBottom: 14, flexWrap: "wrap" }}>
                    {[["bacteria", "🦠 Bacteria"], ["virus", "🧬 Virus"], ["fungus", "🍄 Fungus"], ["parasite", "🪱 Parasite"]].map(([val, label]) => (
                      <button key={val} onClick={() => setMicroType(val)} style={{
                        padding: "7px 14px", borderRadius: 8, fontSize: 12.5, fontWeight: 700,
                        background: microType === val ? `${T.accent}18` : T.surface2,
                        border: `1px solid ${microType === val ? T.accent + "50" : T.border}`,
                        color: microType === val ? T.accent : T.textSub,
                        cursor: "pointer", transition: "all 0.15s", fontFamily: "'DM Sans',sans-serif",
                      }}>{label}</button>
                    ))}
                  </div>
                  {/* Input */}
                  <div style={{ display: "flex", gap: 9, marginBottom: 14 }}>
                    <input value={microInput} onChange={e => setMicroInput(e.target.value)}
                      placeholder={`Enter ${microType} name (e.g. E. coli, Candida albicans…)`}
                      className="ma-input" style={{ flex: 1, fontSize: 13.5 }}
                      onKeyDown={e => { if (e.key === "Enter") runMicroorgAnalysis(); }}
                    />
                    <button onClick={runMicroorgAnalysis} disabled={microLoading || !microInput.trim()}
                      className="ma-btn" style={{ background: T.accent, color: T.isDark ? "#000" : "#fff", fontWeight: 800, whiteSpace: "nowrap" }}>
                      {microLoading ? <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> : <Microscope size={14} />}
                      Analyze
                    </button>
                  </div>
                  {/* Quick examples */}
                  <div style={{ display: "flex", gap: 5, flexWrap: "wrap", marginBottom: microResult ? 14 : 0 }}>
                    {(microType === "bacteria" ? ["E. coli", "Staphylococcus aureus", "Mycobacterium tuberculosis", "Pseudomonas aeruginosa"]
                      : microType === "virus" ? ["SARS-CoV-2", "Influenza A", "HIV", "Hepatitis B"]
                        : microType === "fungus" ? ["Candida albicans", "Aspergillus fumigatus", "Cryptococcus neoformans", "Trichophyton rubrum"]
                          : ["Plasmodium falciparum", "Entamoeba histolytica", "Ascaris lumbricoides", "Giardia lamblia"]
                    ).map(ex => (
                      <button key={ex} onClick={() => setMicroInput(ex)} style={{
                        padding: "4px 10px", borderRadius: 6, fontSize: 11, fontWeight: 600,
                        background: T.surface3, border: `1px solid ${T.border}`, color: T.textSub,
                        cursor: "pointer", fontFamily: "'DM Sans',sans-serif",
                      }}>{ex}</button>
                    ))}
                  </div>
                  {/* Result */}
                  {microLoading && !microResult && (
                    <div className="fade-up" style={{ padding: 16, borderRadius: 12, background: `${T.accent}03`, border: `1px solid ${T.accent}10`, marginTop: 8 }}>
                      <div className="ma-skeleton" style={{ height: 18, width: "30%", marginBottom: 12, borderRadius: 4 }} />
                      <div className="ma-skeleton" style={{ height: 14, width: "100%", marginBottom: 8, borderRadius: 4 }} />
                      <div className="ma-skeleton" style={{ height: 14, width: "85%", marginBottom: 8, borderRadius: 4 }} />
                      <div className="ma-skeleton" style={{ height: 14, width: "95%", borderRadius: 4 }} />
                    </div>
                  )}
                  {microResult && (
                    <div className="fade-up" style={{ padding: 16, borderRadius: 12, background: `${T.accent}06`, border: `1px solid ${T.accent}20`, marginTop: 8 }}>
                      <div style={{ whiteSpace: "pre-wrap", fontSize: 13.5, lineHeight: 1.75, color: T.text, wordBreak: "break-word" }}>
                        {formatText(microResult, T.accent)}
                        {microLoading && <span className="ma-cursor" />}
                      </div>
                    </div>
                  )}
                </GCard>
              )}

              {/* ── NEARBY DOCTOR / HOSPITAL SEARCH ── */}
              {showNearbyDoctor && (
                <GCard>
                  <ToolHeader title="Find Nearby Doctor / Hospital" icon={MapPin} accent={T.accent3} T={T} onClose={closeTool} />
                  <div style={{ display: "flex", gap: 9, marginBottom: 12 }}>
                    <input value={doctorCity} onChange={e => setDoctorCity(e.target.value)}
                      placeholder="Enter city name (e.g. Chandigarh, Mohali, Delhi…)"
                      className="ma-input" style={{ flex: 1, fontSize: 13.5 }}
                      onKeyDown={e => { if (e.key === "Enter") searchNearbyDoctors(); }}
                    />
                    <button onClick={searchNearbyDoctors} disabled={doctorLoading || !doctorCity.trim()}
                      className="ma-btn" style={{ background: T.accent3, color: T.isDark ? "#000" : "#fff", fontWeight: 800 }}>
                      {doctorLoading ? <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> : <Search size={14} />}
                      Search
                    </button>
                  </div>
                  {/* Quick city buttons */}
                  <div style={{ display: "flex", gap: 5, flexWrap: "wrap", marginBottom: 12 }}>
                    {["Chandigarh", "Mohali", "Panchkula", "Delhi", "Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Ambala", "Rohtak"].map(city => (
                      <button key={city} onClick={() => { setDoctorCity(city); }} style={{
                        padding: "5px 12px", borderRadius: 7, fontSize: 11.5, fontWeight: 600,
                        background: doctorCity.toLowerCase() === city.toLowerCase() ? `${T.accent3}18` : T.surface3,
                        border: `1px solid ${doctorCity.toLowerCase() === city.toLowerCase() ? T.accent3 + "50" : T.border}`,
                        color: doctorCity.toLowerCase() === city.toLowerCase() ? T.accent3 : T.textSub,
                        cursor: "pointer", fontFamily: "'DM Sans',sans-serif",
                      }}>{city}</button>
                    ))}
                  </div>
                  {/* Optional specialty filter */}
                  <input value={doctorSpecialty} onChange={e => setDoctorSpecialty(e.target.value)}
                    placeholder="Filter by specialty (optional, e.g. Super Specialty, Government…)"
                    className="ma-input" style={{ fontSize: 12.5, marginBottom: 14 }}
                  />
                  {/* Results */}
                  {doctorLoading ? (
                    <div className="stagger" style={{ display: "flex", flexDirection: "column", gap: 7 }}>
                      {[1, 2, 3].map(i => (
                        <div key={i} className="ma-skeleton" style={{ height: 110, width: "100%", borderRadius: 10 }} />
                      ))}
                    </div>
                  ) : doctorResults.length > 0 && (
                    <div className="stagger" style={{ display: "flex", flexDirection: "column", gap: 7 }}>
                      {doctorResults.map((h, i) => (
                        h.type === "info" ? (
                          <div key={i} style={{ padding: "14px 16px", borderRadius: 10, background: `${T.warn}09`, border: `1px solid ${T.warn}25`, fontSize: 13, color: T.textSub }}>{h.name}</div>
                        ) : (
                          <div key={i} style={{
                            padding: "14px 16px", borderRadius: 10,
                            border: `1px solid ${T.border}`, background: T.surface2,
                            display: "flex", alignItems: "flex-start", gap: 12,
                          }}>
                            <div style={{
                              width: 36, height: 36, borderRadius: 10,
                              background: `${T.accent3}12`, border: `1px solid ${T.accent3}25`,
                              display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
                            }}>
                              <Stethoscope size={16} style={{ color: T.accent3 }} />
                            </div>
                            <div style={{ flex: 1, minWidth: 0 }}>
                              <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                                <span style={{ fontSize: 14, fontWeight: 700, color: T.text }}>{h.name}</span>
                                {h.emergency && (
                                  <span style={{ fontSize: 9, fontWeight: 800, padding: "2px 7px", borderRadius: 5, background: `${T.danger}15`, border: `1px solid ${T.danger}30`, color: T.danger, letterSpacing: "0.06em", textTransform: "uppercase" }}>Emergency</span>
                                )}
                              </div>
                              <div style={{ fontSize: 12, color: T.textSub, marginTop: 3 }}>{h.address}</div>
                              <div style={{ display: "flex", gap: 10, marginTop: 6, flexWrap: "wrap" }}>
                                <span style={{ fontSize: 11, color: T.textMuted, padding: "2px 8px", borderRadius: 5, background: T.surface3, fontWeight: 600 }}>{h.type}</span>
                                {h.phone && (
                                  <a href={`tel:${h.phone}`} style={{
                                    fontSize: 11, color: T.accent, fontWeight: 700, textDecoration: "none",
                                    display: "flex", alignItems: "center", gap: 4,
                                    padding: "2px 8px", borderRadius: 5, background: `${T.accent}08`,
                                  }}>
                                    <Phone size={10} /> {h.phone}
                                  </a>
                                )}
                              </div>
                            </div>
                          </div>
                        )
                      ))}
                    </div>
                  )}
                  {doctorResults.length === 0 && !doctorLoading && (
                    <div style={{ fontSize: 13, color: T.textMuted, textAlign: "center", padding: "20px 0" }}>
                      Search for hospitals by entering a city name above. Available: Chandigarh, Mohali, Panchkula, Delhi, Ludhiana, Amritsar, Jalandhar, Patiala, Ambala, Rohtak.
                    </div>
                  )}
                </GCard>
              )}
            </div>
          </div>
        )}

        {/* ════════════════════════════════════════
            RECORDS TAB
        ════════════════════════════════════════ */}
        {!seniorMode && tab === "reports" && (
          <div className="ma-scroll" style={{ flex: 1, padding: "26px 24px" }}>
            <div style={{ maxWidth: 860, margin: "0 auto" }}>

              {/* Header row */}
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20, flexWrap: "wrap", gap: 12 }}>
                <div style={{ fontSize: 24, fontWeight: 900, color: T.text, fontFamily: "'DM Sans',sans-serif", letterSpacing: "-0.04em", display: "flex", alignItems: "center", gap: 10 }}>
                  <Microscope size={22} style={{ color: T.accent2 }} />Records
                </div>
                <div style={{ display: "flex", gap: 9 }}>
                  <button onClick={() => setShowLabEntry(!showLabEntry)} className="ma-btn ma-btn-ghost"><Plus size={14} />Add Lab Value</button>
                  <label className="ma-btn ma-btn-primary" style={{ cursor: "pointer" }}>
                    <Upload size={14} />Upload Report
                    <input type="file" accept="image/*,.pdf" onChange={handleReportUpload} style={{ display: "none" }} />
                  </label>
                  <button onClick={generateReport} disabled={reportLoading} className="ma-btn ma-btn-ghost">
                    {reportLoading ? <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> : <Download size={14} />}AI Report
                  </button>
                </div>
              </div>

              {/* Lab Entry Form */}
              {showLabEntry && (
                <GCard style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 17, fontWeight: 800, color: T.text, fontFamily: "'DM Sans',sans-serif", marginBottom: 14, letterSpacing: "-0.02em", display: "flex", alignItems: "center", gap: 8 }}>
                    <FlaskConical size={18} style={{ color: T.accent }} />Add Lab Value
                  </div>
                  <div style={{ position: "relative", marginBottom: 10 }}>
                    <input value={labSearch} onChange={e => handleLabSearch(e.target.value)} placeholder="Search test (e.g. hemoglobin, glucose, TSH…)" className="ma-input" />
                    {labSuggestions.length > 0 && (
                      <div className="ma-dropdown" style={{ position: "absolute", left: 0, right: 0, top: "calc(100% + 5px)", zIndex: 100 }}>
                        {labSuggestions.map((tt, i) => (
                          <div key={i} onClick={() => selectLabTest(tt)} className="ma-suggest">
                            <div>
                              <span style={{ fontWeight: 700 }}>{tt.display}</span>
                              <span style={{ fontSize: 11.5, color: T.textMuted, marginLeft: 9, padding: "2px 7px", borderRadius: 5, background: T.surface3 }}>{tt.category}</span>
                            </div>
                            <span style={{ fontSize: 11.5, color: T.textMuted, fontFamily: "'Fira Code',monospace" }}>{tt.normal_range} {tt.unit}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  {selectedLabTest && (
                    <div className="fade-up" style={{ padding: "10px 14px", borderRadius: 11, background: `${T.accent}08`, border: `1px solid ${T.accent}20`, marginBottom: 10, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                      <div>
                        <div style={{ fontSize: 14, fontWeight: 700, color: T.text }}>{selectedLabTest.display}</div>
                        <div style={{ fontSize: 11.5, color: T.textMuted }}>{selectedLabTest.category}</div>
                      </div>
                      <div style={{ textAlign: "right" }}>
                        <div style={{ fontSize: 12.5 }}>Normal: <span style={{ fontWeight: 800, color: T.accent3, fontFamily: "'Fira Code',monospace" }}>{selectedLabTest.normal_range}</span> {selectedLabTest.unit}</div>
                      </div>
                    </div>
                  )}
                  <div style={{ display: "flex", gap: 9 }}>
                    <input value={labValue} onChange={e => setLabValue(e.target.value)} placeholder={`Value${selectedLabTest ? ` (${selectedLabTest.unit})` : ""}`} className="ma-input" onKeyDown={e => { if (e.key === "Enter") submitLabEntry(); }} style={{ fontFamily: "'Fira Code',monospace" }} />
                    <input type="date" value={labDate} onChange={e => setLabDate(e.target.value)} className="ma-input" style={{ width: "auto" }} />
                    <button onClick={submitLabEntry} disabled={!selectedLabTest || !labValue.trim()} className="ma-btn ma-btn-success" style={{ flexShrink: 0 }}>Save</button>
                  </div>
                </GCard>
              )}

              {/* AI Report */}
              {reportData && (
                <GCard style={{ marginBottom: 16 }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
                    <div>
                      <div style={{ fontSize: 17, fontWeight: 800, color: T.text, fontFamily: "'DM Sans',sans-serif", letterSpacing: "-0.02em" }}>AI Health Report</div>
                      <div style={{ fontSize: 11, color: T.textMuted, fontFamily: "'Fira Code',monospace", marginTop: 3 }}>{new Date(reportData.generated_at).toLocaleString()} · {reportData.report_id}</div>
                    </div>
                    <button onClick={() => window.print()} className="ma-btn ma-btn-ghost ma-btn-sm"><Download size={13} /></button>
                  </div>
                  <div style={{ padding: 18, borderRadius: 14, background: `${T.accent}06`, border: `1px solid ${T.accent}16` }}>
                    <div style={{ whiteSpace: "pre-wrap", fontSize: 14, lineHeight: 1.8, color: T.text }}>{reportData.ai_summary}</div>
                  </div>
                </GCard>
              )}

              {/* Lab Intelligence */}
              <GCard style={{ marginBottom: 16 }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
                  <div style={{ fontSize: 17, fontWeight: 800, color: T.text, fontFamily: "'DM Sans',sans-serif", letterSpacing: "-0.02em", display: "flex", alignItems: "center", gap: 9 }}>
                    <Cpu size={17} style={{ color: T.accent2 }} />Lab Intelligence
                  </div>
                  <button onClick={loadLabIntelligence} disabled={labIntelLoading} className="ma-btn ma-btn-ghost ma-btn-sm">
                    {labIntelLoading ? <Loader2 size={12} style={{ animation: "spin 1s linear infinite" }} /> : "Analyze"}
                  </button>
                </div>
                {labIntel?.findings?.length > 0 ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: 9 }}>
                    {labIntel.findings.map((f, i) => (
                      <div key={i} className="fade-up" style={{
                        padding: "14px 16px", borderRadius: 13,
                        border: `1px solid ${f.severity === "high" ? `${T.danger}32` : f.severity === "medium" ? `${T.warn}32` : `${T.accent2}32`}`,
                        background: f.severity === "high" ? `${T.danger}07` : f.severity === "medium" ? `${T.warn}07` : `${T.accent2}06`,
                      }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 9, marginBottom: 6 }}>
                          <span style={{ fontSize: 10, fontWeight: 900, letterSpacing: "0.12em", textTransform: "uppercase", padding: "3px 8px", borderRadius: 5, background: f.severity === "high" ? T.danger : f.severity === "medium" ? T.warn : T.accent2, color: "white" }}>{f.severity}</span>
                          <span style={{ fontSize: 14, fontWeight: 800, color: T.text }}>{f.name}</span>
                        </div>
                        <div style={{ fontSize: 13.5, marginBottom: 5, color: T.text, lineHeight: 1.5 }}>{f.message}</div>
                        <div style={{ fontSize: 12.5, color: T.textMuted, lineHeight: 1.5 }}>{f.recommendation}</div>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 5, marginTop: 9 }}>
                          {f.triggered_tests?.map((tt, j) => <span key={j} style={{ fontSize: 11, padding: "2px 9px", borderRadius: 5, background: T.surface2, border: `1px solid ${T.border}`, fontFamily: "'Fira Code',monospace", color: T.text }}>{tt}</span>)}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : <div style={{ fontSize: 13.5, color: T.textMuted, textAlign: "center", padding: "16px 0" }}>{labIntel ? "No patterns detected." : "Detects metabolic syndrome, anemia patterns & more."}</div>}
              </GCard>

              {/* Lab Trends */}
              <GCard style={{ marginBottom: 16 }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
                  <div style={{ fontSize: 17, fontWeight: 800, color: T.text, fontFamily: "'DM Sans',sans-serif", letterSpacing: "-0.02em", display: "flex", alignItems: "center", gap: 9 }}>
                    <TrendingUp size={17} style={{ color: T.accent }} />Lab Trends
                  </div>
                  <button onClick={loadTrends} disabled={trendsLoading} className="ma-btn ma-btn-ghost ma-btn-sm">
                    {trendsLoading ? <Loader2 size={12} style={{ animation: "spin 1s linear infinite" }} /> : "Detect"}
                  </button>
                </div>
                {trendsData?.trends?.length > 0 ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: 9 }}>
                    {trendsData.trends.map((tt, i) => (
                      <div key={i} style={{ padding: "12px 16px", borderRadius: 12, border: `1px solid ${tt.is_concerning ? `${T.danger}25` : T.border}`, background: tt.is_concerning ? `${T.danger}06` : T.surface2 }}>
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
                          <span style={{ fontSize: 13.5, fontWeight: 700, color: T.text }}>{tt.display}</span>
                          <span style={{ fontSize: 14, fontWeight: 900, fontFamily: "'Fira Code',monospace", color: tt.direction === "increasing" ? T.danger : tt.direction === "decreasing" ? T.accent : T.accent3 }}>
                            {tt.direction === "increasing" ? "↑" : tt.direction === "decreasing" ? "↓" : "→"} {Math.abs(tt.change_pct)}%
                          </span>
                        </div>
                        <div style={{ display: "flex", gap: 14 }}>
                          {tt.data_points?.map((p, j) => <span key={j} style={{ fontSize: 12, color: T.textMuted, fontFamily: "'Fira Code',monospace" }}>{p.date?.slice(5)}: <span style={{ fontWeight: 700, color: T.text }}>{p.value}</span></span>)}
                        </div>
                        <div style={{ fontSize: 11, color: T.textMuted, marginTop: 4 }}>Normal: {tt.normal_range}</div>
                      </div>
                    ))}
                  </div>
                ) : <div style={{ fontSize: 13.5, color: T.textMuted, textAlign: "center", padding: "16px 0" }}>{trendsData ? "Not enough data for trends." : "Tracks lab value changes over time."}</div>}
              </GCard>

              {/* Full Lab Table */}
              {labResults.length > 0 ? (
                <GCard style={{ padding: 0, overflow: "hidden" }}>
                  <div style={{ padding: "15px 22px", borderBottom: `1px solid ${T.border}`, display: "flex", alignItems: "center", justifyContent: "space-between", background: T.surface }}>
                    <div style={{ fontSize: 17, fontWeight: 800, color: T.text, fontFamily: "'DM Sans',sans-serif", letterSpacing: "-0.02em", display: "flex", alignItems: "center", gap: 8 }}>
                      <FlaskConical size={16} style={{ color: T.accent2 }} />All Lab Results
                    </div>
                    <span style={{ fontSize: 11.5, color: T.textMuted, fontFamily: "'Fira Code',monospace", padding: "2px 9px", borderRadius: 5, background: T.surface2, border: `1px solid ${T.border}` }}>{labResults.length} values</span>
                  </div>
                  <div className="ma-scroll" style={{ maxHeight: 500, overflowX: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "separate", borderSpacing: 0, minWidth: 580 }}>
                      <thead>
                        <tr>
                          {["Test", "Value", "Normal Range", "Status", "Date", ""].map(h => (
                            <th key={h} style={{ background: T.surface2, color: T.textMuted, borderBottom: `2px solid ${T.border}`, padding: "10px 16px", fontSize: 11, fontWeight: 700, letterSpacing: "0.07em", textTransform: "uppercase", whiteSpace: "nowrap", position: "sticky", top: 0, zIndex: 1 }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {labResults.map((r, i) => {
                          const statusColors = { normal: T.accent3, high: T.danger, low: T.warn, abnormal: T.danger, noted: T.accent2 };
                          const sc = statusColors[r.status] || T.textMuted;
                          return (
                            <tr key={i} style={{ background: i % 2 === 0 ? T.surface : T.surface2 }}
                              onMouseEnter={e => e.currentTarget.style.background = `${T.accent}08`}
                              onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? T.surface : T.surface2}>
                              <td style={{ padding: "11px 16px", fontWeight: 700, color: T.text, fontSize: 13, borderTop: `1px solid ${T.border}`, textTransform: "capitalize" }}>
                                {(r.test_name || "").replace(/_/g, " ")}
                              </td>
                              <td style={{ padding: "11px 16px", fontFamily: "'Fira Code',monospace", fontSize: 13, color: sc, fontWeight: 700, borderTop: `1px solid ${T.border}`, whiteSpace: "nowrap" }}>
                                {r.value} <span style={{ fontWeight: 400, color: T.textMuted, fontSize: 11 }}>{r.unit || ""}</span>
                              </td>
                              <td style={{ padding: "11px 16px", color: T.textMuted, fontSize: 12, fontFamily: "'Fira Code',monospace", borderTop: `1px solid ${T.border}`, whiteSpace: "nowrap" }}>
                                {r.normal_range || "—"}
                              </td>
                              <td style={{ padding: "11px 16px", borderTop: `1px solid ${T.border}`, whiteSpace: "nowrap" }}>
                                <span style={{
                                  display: "inline-flex", alignItems: "center", gap: 6,
                                  padding: "3px 10px", borderRadius: 99, fontSize: 11, fontWeight: 700,
                                  background: `${sc}15`, color: sc, border: `1px solid ${sc}30`, textTransform: "capitalize",
                                }}>
                                  <span style={{ width: 6, height: 6, borderRadius: "50%", background: sc, flexShrink: 0, boxShadow: `0 0 5px ${sc}` }} />
                                  {r.status || "—"}
                                </span>
                              </td>
                              <td style={{ padding: "11px 16px", color: T.textMuted, fontSize: 12, fontFamily: "'Fira Code',monospace", borderTop: `1px solid ${T.border}`, whiteSpace: "nowrap" }}>
                                {r.date}
                              </td>
                              <td style={{ padding: "11px 12px", borderTop: `1px solid ${T.border}`, textAlign: "right" }}>
                                <button onClick={() => deleteLabResult(r.id)}
                                  style={{ background: "none", border: "none", cursor: "pointer", color: T.textMuted, display: "inline-flex", padding: 5, borderRadius: 6, transition: "color 0.12s, background 0.12s" }}
                                  onMouseEnter={e => { e.currentTarget.style.color = T.danger; e.currentTarget.style.background = `${T.danger}15`; }}
                                  onMouseLeave={e => { e.currentTarget.style.color = T.textMuted; e.currentTarget.style.background = "none"; }}>
                                  <Trash2 size={12} />
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </GCard>
              ) : (
                <div style={{ textAlign: "center", padding: "70px 20px", color: T.textMuted }}>
                  <div style={{ width: 70, height: 70, borderRadius: 20, background: T.surface2, border: `1px solid ${T.border}`, display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 18px" }}>
                    <Microscope size={28} style={{ opacity: 0.2 }} />
                  </div>
                  <div style={{ fontSize: 16, fontWeight: 800, marginBottom: 5, color: T.text }}>No lab reports yet</div>
                  <div style={{ fontSize: 13.5 }}>Upload a report or add values manually</div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ════════════════════════════════════════
            GLOBAL TOAST NOTIFICATIONS
        ════════════════════════════════════════ */}
        <div style={{ position: "fixed", bottom: 24, left: "50%", transform: "translateX(-50%)", zIndex: 9999, display: "flex", flexDirection: "column", gap: 8, pointerEvents: "none" }}>
          {toasts.map(t => (
            <div key={t.id} className="fade-up" style={{
              padding: "10px 20px", borderRadius: 30,
              background: T.isDark ? "rgba(255,255,255,0.92)" : "rgba(0,0,0,0.85)",
              color: T.isDark ? "#000" : "#fff",
              fontSize: 13, fontWeight: 700,
              boxShadow: T.shadowLg,
              display: "flex", alignItems: "center", gap: 8
            }}>
              {t.type === "success" && <Check size={14} style={{ color: T.accent3 }} />}
              {t.msg}
            </div>
          ))}
        </div>

      </div>
    </div>
  );
}