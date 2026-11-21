import {useState} from 'react'
import type {Shot} from '../api'
import {inlineShotPatch,planSlider} from '../shotEditing'
import type {ShotMetric} from '../shotEditing'
import Icon from './ui/Icon'

export default function PlanMetrics({shot,metrics,disabled,onChange}:{
 shot:Shot;metrics:ShotMetric[];disabled:boolean;onChange:(patch:Partial<Shot>)=>void
}){
 const [active,setActive]=useState<{label:string;initial:string}|null>(null)
 const [typed,setTyped]=useState<string|null>(null)
 const [error,setError]=useState('')

 return <div className="metrics next-plan-metrics">{metrics.map(({field,value,unit,label})=>{
  const name=label.toLowerCase()
  const text=String(value??'')
  const slider=field&&active?.label===label?planSlider(field,active.initial):null
  function commit(input:string){
   if(!field||disabled||input===text)return
   try{
    const patch=inlineShotPatch({shot,field,value:input})
    delete patch.coffee_id
    delete patch.revision
    onChange(patch)
    setError('')
   }
   catch(error){setError((error as Error).message)}
  }
  return <div key={label} className={active?.label===label?'metric-editing':undefined}>
   <span className="metric-label">{label}</span>
   {field&&active?.label===label&&!disabled?<div className="inline-metric-editor plan-metric-editor"
    onKeyDown={event=>{if(event.key==='Escape'){setTyped(null);setActive(null)}}}>
    {field==='temp'?<select autoFocus aria-label={label} value={text} onChange={event=>commit(event.target.value)}>
     {['','0','I','II'].map(setting=><option key={setting} value={setting}>{setting||'—'}</option>)}
    </select>:<>
     <input autoFocus={!slider} aria-label={label} inputMode={field==='grind'&&!slider?'text':'decimal'} value={typed??text}
      onFocus={event=>event.currentTarget.select()} onChange={event=>setTyped(event.target.value)}
      onBlur={event=>{commit(event.currentTarget.value);setTyped(null)}}
      onKeyDown={event=>{
       if(event.key!=='Enter')return
       event.preventDefault()
       commit(event.currentTarget.value)
       setTyped(null)
       setActive(null)
      }}/>
     {slider&&<input autoFocus className="plan-metric-slider" type="range" aria-label={`Adjust ${name}`}
      {...slider} value={text!==''&&Number.isFinite(Number(text))?Number(text):slider.value}
      onChange={event=>commit(event.target.value)}/>}
    </>}
   </div>:field?<button type="button" className="metric-edit-button" aria-label={`Edit ${name}`} disabled={disabled}
    onClick={()=>{setActive({label,initial:text});setTyped(null);setError('')}}><strong>{value??'—'}</strong><span className="metric-unit">{unit}</span><Icon name="edit"/></button>
    :<div><strong>{value??'—'}</strong><span className="metric-unit">{unit}</span></div>}
  </div>
 })}{error&&<p className="inline-metric-error" role="alert">{error}</p>}</div>
}
