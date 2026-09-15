import {profile} from './profile'

declare const process: {env: {API_BASE_URL?: string}}
const base=process.env.API_BASE_URL||'http://127.0.0.1:8001'
let accessToken:()=>Promise<string|null>=async()=>null
export function setAccessTokenProvider(provider:()=>Promise<string|null>){accessToken=provider}
export async function api(path:string,method='GET',body?:unknown){
 const token=await accessToken()
 const headers:Record<string,string>={}
 if(body)headers['Content-Type']='application/json'
 if(token)headers.Authorization='Bearer '+token
 const response=await fetch(base+path,{method,headers,body:body?JSON.stringify(body):undefined})
 const value=await response.json()
 if(!response.ok)throw new Error(typeof value.detail==='string'?value.detail:JSON.stringify(value.detail||value))
 return value
}
export type Coffee={id:string;name:string;brand?:string;roast_date:string;notes:string;tag_color?:string;archived?:boolean;revision:number}
export type TrackedField='water_temp_c'|'water_g'|'ice_g'|'dose'|'ratio'|'grind'|'seconds'|'bloom_seconds'|'brand'|'yield_g'|'stop_yield_g'|'target_yield_g'|'first_drip'|'paper'|'temp'|'pressure'|'basket'|'puck_screen'|'taste_balance'|'rating'|'taste'
export type BrewProfile={brew_method:'espresso'|'filter';equipment_preset:'lelit_mara_x'|'generic_espresso'|'standard_pour_over'|'custom';equipment_name:string;tracked_fields:TrackedField[];revision:number}
export type Shot={id?:string;coffee_id:string;revision:number;date:string;recorded_at?:string;taste_balance?:TasteBalance;choked?:boolean;rating?:number|null;dose:number|null;grind:string;paper:string;temp:string;water_temp_c?:number|null;water_g?:number|null;ice_g?:number|null;bloom_seconds?:number|null;stop_yield_g?:number|null;yield_g:number|null;target_yield_g?:number|null;target_yield_max_g?:number|null;outcome?:'unrated'|'good'|'adjust'|'bad'|'choked';locked?:boolean;seconds:number|null;first_drip:number|null;pressure:string;basket:string;puck_screen:string;status:string;taste:string;source:string}
export type Message={id:string;role:string;text:string}
export type TasteBalance=''|'sour'|'slightly_sour'|'balanced'|'slightly_bitter'|'bitter'
export const today=()=>{const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`}
export const blankShot=(coffee_id:string):Shot=>({coffee_id,revision:0,date:today(),dose:profile.defaults.dose,grind:profile.defaults.grind,paper:profile.defaults.paper,temp:profile.defaults.temp,water_temp_c:null,water_g:null,ice_g:null,bloom_seconds:null,stop_yield_g:null,yield_g:null,target_yield_g:null,target_yield_max_g:null,outcome:'unrated',locked:false,seconds:null,first_drip:null,pressure:'',basket:profile.defaults.basket,puck_screen:profile.defaults.puckScreen,status:'logged',taste:'',source:''})
