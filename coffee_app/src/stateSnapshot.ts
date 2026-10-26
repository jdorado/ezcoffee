import type {BrewProfile,Bean,Coffee,Shot,Message} from './api'

// A read-only copy of the last server state, used only to paint the first screen.
// Mongo stays canonical: every load replaces this copy, edits still carry revisions,
// and the copy is ignored across accounts and builds and cleared on sign-out.
export type ServerState={beans?:Bean[];coffees:Coffee[];shots:Shot[];messages?:Message[];profile?:BrewProfile;capabilities?:{chat?:boolean};active_job?:unknown}
export type StateSnapshot=Omit<ServerState,'active_job'>
type Store=Pick<Storage,'getItem'|'setItem'|'removeItem'>

const KEY='coffee.snapshot'
const VERSION=1
function browserStore():Store|null{try{return localStorage}catch{return null}}

export function readSnapshot(owner:string,build:string,store:Store|null=browserStore()):StateSnapshot|null{
 try{
  const saved=JSON.parse(store?.getItem(KEY)||'null')
  if(saved?.v!==VERSION||saved.owner!==owner||saved.build!==build)return null
  const state=saved.state
  return Array.isArray(state?.coffees)&&Array.isArray(state.shots)?state:null
 }catch{return null}
}

export function clearSnapshot(store:Store|null=browserStore()){try{store?.removeItem(KEY)}catch{}}

export function writeSnapshot(owner:string,build:string,state:ServerState,store:Store|null=browserStore()){
 if(!store)return
 // A running job is live server state; chat history is the only unbounded part, so it goes first when storage is full.
 const base={...state,active_job:undefined}
 for(const copy of [base,{...base,messages:[]}]){
  try{store.setItem(KEY,JSON.stringify({v:VERSION,owner,build,state:copy}));return}catch{}
 }
 clearSnapshot(store)
}
