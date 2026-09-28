import type {Shot} from '../api'
import {numericShotLimits,plannedStopAt} from '../shotEditing'
import type {InlineShotEdit,ShotMetric} from '../shotEditing'
import Icon from './ui/Icon'

type Props={shot:Shot;metrics:ShotMetric[];edit:InlineShotEdit|null;onEdit:(edit:InlineShotEdit|null)=>void;onSave:()=>void;onReload:()=>void;saving:boolean;error:string;disabled?:boolean;className?:string}

export default function ShotMetrics({shot,metrics,edit,onEdit,onSave,onReload,saving,error,disabled=false,className=''}:Props){
 return <div className={'metrics '+className}>{metrics.map(({field,value,unit,label,note})=>{
  const active=!!edit&&edit.shot.id===shot.id&&edit.field===field
  const name=label.toLowerCase()
  return <div key={label} className={active?'metric-editing':undefined}>
   <span className="metric-label">{label}</span>
   {active&&edit?<form className="inline-metric-editor" onSubmit={event=>{event.preventDefault();onSave()}} onKeyDown={event=>{if(event.key==='Escape'){event.preventDefault();event.stopPropagation();if(!saving)onEdit(null)}}}>
    {field==='temp'?<select autoFocus aria-label={label} value={edit.value} disabled={saving} onChange={event=>onEdit({...edit,value:event.target.value})}>{[['','—'],['0','0'],['I','I'],['II','II']].map(([key,text])=><option key={key} value={key}>{text}</option>)}</select>:<input autoFocus aria-label={label} type={field==='grind'?'text':'number'} inputMode="decimal" enterKeyHint="done" step="any" min={field&&field!=='grind'?numericShotLimits[field][0]:undefined} max={field&&field!=='grind'?numericShotLimits[field][1]:undefined} maxLength={field==='grind'?80:undefined} value={edit.value} disabled={saving} onFocus={event=>event.currentTarget.select()} onChange={event=>onEdit({...edit,value:event.target.value})}/>}
    <div className="inline-metric-actions"><button type="submit" disabled={saving} aria-label={`Save ${name}`} title="Save · Enter"><Icon name="check"/></button><button type="button" disabled={saving} aria-label={`Cancel ${name} edit`} title="Cancel · Escape" onClick={()=>onEdit(null)}><Icon name="close"/></button>{saving&&<span role="status">Saving…</span>}</div>
    {error&&<div className="inline-metric-error" role="alert">{error}<button type="button" disabled={saving} onClick={onReload}>Reload values</button></div>}
   </form>:<>{field?<button type="button" className="metric-edit-button" aria-label={`Edit ${name}`} title={`Edit ${name}`} disabled={disabled||!!edit||saving} onClick={()=>onEdit({shot,field,value:String((field==='target_yield_g'&&shot.status==='planned'?plannedStopAt(shot):shot[field])??'')})}><strong>{value??'—'}</strong><span className="metric-unit">{unit}</span><Icon name="edit"/></button>:<div><strong>{value??'—'}</strong><span className="metric-unit">{unit}</span></div>}{note&&<small className="stop-yield">{note}</small>}</>}
  </div>
 })}</div>
}
