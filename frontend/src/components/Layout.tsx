import type { ReactNode } from 'react';
import { Activity, LayoutDashboard, UserRound, Video, History, MessageCircle, Settings, Stethoscope, ClipboardPlus } from 'lucide-react';
import { StatusPill } from './StatusPill';
import { useAppStore } from '../store/appStore';
export function Layout({page,setPage,children}:{page:string;setPage:(v:string)=>void;children:ReactNode}){
 const n=useAppStore(s=>s.network);
 const items=[['dashboard','Dashboard',LayoutDashboard],['profile','Athlete Profile',UserRound],['assessment','New Assessment',ClipboardPlus],['history','Assessment History',History],['trend','Recovery Trend',Activity],['coach','Coach / Physio',Stethoscope],['assistant','AI Recovery Support',MessageCircle],['settings','Settings',Settings]] as const;
 return <div className="shell"><aside className="sidebar"><div className="brand"><div className="brand-mark"><Activity size={19}/></div><div><b>Sports Rehab AI</b><span>Return-to-Play</span></div></div><nav>{items.map(([id,label,Icon])=><button key={id} className={page===id?'nav active':'nav'} onClick={()=>setPage(id)}><Icon size={18}/><span>{label}</span></button>)}</nav><div className="side-note"><Video size={18}/><div><b>Offline-first</b><small>Core assessment runs locally.</small></div></div></aside><main className="main"><header className="topbar"><div><div className="eyebrow">AI-POWERED REHABILITATION</div><h1>{items.find(x=>x[0]===page)?.[1] ?? 'Dashboard'}</h1></div><StatusPill network={n}/></header><div className="content">{children}</div></main></div>
}
