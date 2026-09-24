import {profile} from './profile'

declare const process: {env: {API_BASE_URL?: string}}
const base=process.env.API_BASE_URL||'http://127.0.0.1:8001'
let accessToken:()=>Promise<string|null>=async()=>null
export function setAccessTokenProvider(provider:()=>Promise<string|null>){accessToken=provider}

type ApiIssue={type?:string;loc?:Array<string|number>;msg?:string;ctx?:Record<string,unknown>}
const fieldNames:Record<string,string>={dose:'Coffee dose',water_g:'Water quantity',ice_g:'Ice quantity',water_temp_c:'Water temperature',yield_g:'Output',stop_yield_g:'Stop yield',target_yield_g:'Target output',target_yield_max_g:'Target upper bound',seconds:'Brew time',bloom_seconds:'Bloom time',rating:'Rating'}
const units:Record<string,string>={dose:' g',water_g:' g',ice_g:' g',water_temp_c:' °C',yield_g:' g',stop_yield_g:' g',target_yield_g:' g',target_yield_max_g:' g',seconds:' s',bloom_seconds:' s'}
export function apiErrorMessage(detail:unknown){
 if(typeof detail==='string')return detail
 if(!Array.isArray(detail))return 'Something went wrong. Please try again.'
 return detail.map((issue:ApiIssue)=>{
  const key=String(issue.loc?.at(-1)||'entry'),label=fieldNames[key]||key.replaceAll('_',' '),unit=units[key]||''
  if(issue.type==='less_than_equal')return `${label} must be ${issue.ctx?.le}${unit} or less.`
  if(issue.type==='greater_than')return `${label} must be greater than ${issue.ctx?.gt}${unit}.`
  if(issue.type==='greater_than_equal')return `${label} must be ${issue.ctx?.ge}${unit} or more.`
  return `${label}: ${issue.msg||'invalid value'}.`
 }).join(' ')
}
export async function api(path:string,method='GET',body?:unknown){
 const token=await accessToken()
 const headers:Record<string,string>={}
 if(body)headers['Content-Type']='application/json'
 if(token)headers.Authorization='Bearer '+token
 const response=await fetch(base+path,{method,headers,body:body?JSON.stringify(body):undefined})
 const value=await response.json()
 if(!response.ok)throw new Error(apiErrorMessage(value.detail||value))
 return value
}
export type Coffee={id:string;name:string;brand?:string;origin?:string;variety?:string;process?:string;roast_level?:string;single_origin?:string;decaf?:boolean;roast_date:string;notes:string;tag_color?:string;archived?:boolean;revision:number}
export type TrackedField='water_temp_c'|'water_g'|'ice_g'|'dose'|'ratio'|'grind'|'seconds'|'bloom_seconds'|'yield_g'|'stop_yield_g'|'target_yield_g'|'first_drip'|'paper'|'temp'|'pressure'|'basket'|'puck_screen'|'taste_balance'|'rating'|'taste'
export type BrewProfile={brew_method:'espresso'|'filter';equipment_preset:'lelit_mara_x'|'generic_espresso'|'standard_pour_over'|'custom';equipment_name:string;tracked_fields:TrackedField[];revision:number}
export type Shot={id?:string;coffee_id:string;revision:number;date:string;recorded_at?:string;taste_balance?:TasteBalance;choked?:boolean;rating?:number|null;dose:number|null;grind:string;paper:string;temp:string;water_temp_c?:number|null;water_g?:number|null;ice_g?:number|null;bloom_seconds?:number|null;stop_yield_g?:number|null;yield_g:number|null;target_yield_g?:number|null;target_yield_max_g?:number|null;outcome?:'unrated'|'good'|'adjust'|'bad'|'choked';locked?:boolean;seconds:number|null;first_drip:number|null;pressure:string;basket:string;puck_screen:string;status:string;taste:string;source:string}
export type Message={id:string;coffee_id?:string|null;role:string;text:string;failed?:boolean;retryable?:boolean}
export type TasteBalance=''|'sour'|'slightly_sour'|'balanced'|'slightly_bitter'|'bitter'
export const today=()=>{const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`}
export const blankShot=(coffee_id:string):Shot=>({coffee_id,revision:0,date:today(),dose:profile.defaults.dose,grind:profile.defaults.grind,paper:profile.defaults.paper,temp:profile.defaults.temp,water_temp_c:null,water_g:null,ice_g:null,bloom_seconds:null,stop_yield_g:null,yield_g:null,target_yield_g:null,target_yield_max_g:null,outcome:'unrated',locked:false,seconds:null,first_drip:null,pressure:'',basket:profile.defaults.basket,puck_screen:profile.defaults.puckScreen,status:'logged',taste:'',source:''})
