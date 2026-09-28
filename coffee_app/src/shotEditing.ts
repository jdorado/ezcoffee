import type {Shot,TrackedField} from './api'

export const numericShotLimits={dose:[0,1000],yield_g:[0,1000],stop_yield_g:[0,1000],target_yield_g:[0,1000],seconds:[0,600],water_temp_c:[0,100],water_g:[0,5000],ice_g:[0,5000],bloom_seconds:[0,600],first_drip:[0,600],rating:[1,5]} as const
export type EditableShotField=keyof typeof numericShotLimits|'grind'|'temp'
export type ShotMetric={field:EditableShotField|null;value:string|number|null;unit:string;label:string;note?:string}
export type InlineShotEdit={shot:Shot;field:EditableShotField;value:string}
const recipeFields=new Set(['dose','grind','water_temp_c','water_g','ice_g','bloom_seconds','target_yield_g','paper','temp','pressure','basket','puck_screen'])

export const plannedStopAt=(shot:Shot)=>shot.stop_yield_g??shot.target_yield_g??null

export function plannedEditorFields(fields:TrackedField[]):TrackedField[]{
 return [...new Set(fields.map(field=>field==='yield_g'||field==='stop_yield_g'?'target_yield_g':field).filter(field=>recipeFields.has(field)))]
}

export function loggedEditorFields(fields:TrackedField[]):TrackedField[]{
 return [...new Set(fields.map(field=>field==='target_yield_g'?'stop_yield_g':field))]
}

export function inlineShotPatch(edit:InlineShotEdit):Partial<Shot>{
 const {shot,field,value}=edit
 if(shot.status==='planned'&&!recipeFields.has(field))throw new Error('Edit recipe settings here; record the result after brewing.')
 let changed:string|number|null=value.trim()
 if(field==='temp'){
  if(!['','0','I','II'].includes(changed))throw new Error('Choose a PID setting.')
 }else if(field!=='grind'){
  changed=changed===''?null:Number(changed)
  const [min,max]=numericShotLimits[field]
  if(field==='rating'&&changed!=null&&!Number.isInteger(changed))throw new Error('Choose 1 to 5 stars, or clear the rating.')
  if(changed!=null&&(!Number.isFinite(changed)||changed<min||changed>max||(['dose','target_yield_g'].includes(field)&&changed===0)))throw new Error(`Enter ${field==='dose'||field==='target_yield_g'?'more than 0':min} to ${max}, or leave it blank.`)
 }
 const patch:Partial<Shot>={coffee_id:shot.coffee_id,revision:shot.revision,[field]:changed}
 if(field==='target_yield_g'){
  patch.target_yield_max_g=null
  // Planned targets use the recipe field; clear an older stop override so it
  // cannot replace this value when the plan is used to log a shot.
  if(shot.status==='planned')patch.stop_yield_g=null
 }
 return patch
}
