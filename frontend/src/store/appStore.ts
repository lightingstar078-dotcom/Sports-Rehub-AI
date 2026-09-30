import { create } from 'zustand';

export type Athlete = { id:number; name:string; age:number; sport:string; injury:string; injury_side:string };
export type Assessment = { id:number; athlete_id:number; exercise:string; date:string; movement_quality:number; symmetry:number; rom:number; stability:number; landing_control:number; movement_consistency:number; pain:number; psychological_readiness:number; readiness_score:number; status:string; compressed_size:number; original_size:number; sync_status:string; analysis_json?:any };

type State={
  athlete: Athlete | null; setAthlete:(a:Athlete)=>void;
  network:'ONLINE'|'OFFLINE'; setNetwork:(v:'ONLINE'|'OFFLINE')=>void;
  current: Assessment|null; setCurrent:(a:Assessment|null)=>void;
};
export const useAppStore=create<State>((set)=>({athlete:null,setAthlete:(athlete)=>set({athlete}),network:'OFFLINE',setNetwork:(network)=>set({network}),current:null,setCurrent:(current)=>set({current})}));
