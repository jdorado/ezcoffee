import {useState} from 'react'
import {api,today} from '../api'
import type {Bean,Coffee,Shot} from '../api'
import './BagRows.css'

type Editor={kind:'bag'|'batch';row:Partial<Coffee>;parent?:Coffee}
type Props={startAdding?:boolean;beanId?:string;coffees:Coffee[];shots:Shot[];selected:string;ensureBean:()=>Promise<Bean>;refresh:()=>Promise<void>;select:(id:string)=>void}
const dateValue=(value='')=>{if(/^\d{4}-\d{2}-\d{2}$/.test(value))return value;const time=Date.parse(value);if(Number.isNaN(time))return '';const d=new Date(time);return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`}
const dateLabel=(value='')=>value?new Date(dateValue(value)+'T12:00:00').toLocaleDateString(undefined,{day:'numeric',month:'short'}):'Not set'

export default function BagRows({beanId,coffees,shots,selected,ensureBean,refresh,select,startAdding}:Props){
 const [editor,setEditor]=useState<Editor|null>(null),[adding,setAdding]=useState(!!startAdding),[busy,setBusy]=useState(false),[error,setError]=useState('')
 const bags=coffees.filter(c=>c.bean_id===beanId&&!c.source_coffee_id).sort((a,b)=>(a.purchased_on||'').localeCompare(b.purchased_on||'')||(a.created_at||a.id).localeCompare(b.created_at||b.id))
 const children=(bag:Coffee)=>coffees.filter(c=>c.source_coffee_id===bag.id).sort((a,b)=>(a.created_at||a.id).localeCompare(b.created_at||b.id))
 const remaining=(bag:Coffee)=>Math.max(0,(bag.freeze_date?bag.frozen_g||0:bag.bag_g||0)-children(bag).reduce((sum,c)=>sum+(c.portion_g||0),0)-(bag.freeze_date?0:used(bag)))
 const used=(row:Coffee)=>shots.filter(s=>s.coffee_id===row.id&&s.status==='logged').reduce((sum,s)=>sum+(s.dose||0),0)
 async function run(action:()=>Promise<void>){if(busy)return;setBusy(true);setError('');try{await action()}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 function addBag(size:number){setAdding(false);setEditor({kind:'bag',row:{bag_g:size,purchased_on:today(),roast_date:'',freeze_date:'',revision:0}})}
 async function saveRow(){if(!editor)return;await run(async()=>{
  const bean=await ensureBean();const row=editor.row,parent=editor.parent
  if(editor.kind==='bag'&&row.freeze_date&&!row.roast_date)throw new Error('Set the roast date before freezing this bag.')
  const payload=editor.kind==='bag'?{...row,...bean,id:row.id,revision:row.revision||0,archived:row.archived||false,bean_id:bean.id,source_coffee_id:'',roast_date:row.roast_date||'',purchased_on:row.purchased_on||today(),bag_g:row.bag_g,freeze_date:row.freeze_date||'',frozen_g:row.freeze_date?(row.frozen_g??row.bag_g):null,portion_g:null,thaw_date:'',frozen_portions:[]}:{...row,...bean,id:row.id,revision:row.revision||0,archived:row.archived||false,bean_id:bean.id,source_coffee_id:parent!.id,roast_date:parent!.roast_date,freeze_date:parent!.freeze_date||'',bag_g:null,frozen_g:null,frozen_portions:[],portion_g:row.portion_g,thaw_date:row.thaw_date}
  const saved=await api(row.id?'/coffees/'+row.id:'/coffees',row.id?'PUT':'POST',payload)
  setEditor(null);await refresh();select(saved.id)
 })}
 async function addBatch(bag:Coffee,size:125|250|500){await run(async()=>{
  const bean=await ensureBean();const saved=await api('/coffees','POST',{...bean,id:undefined,revision:0,bean_id:bean.id,source_coffee_id:bag.id,roast_date:bag.roast_date,freeze_date:bag.freeze_date||'',portion_g:size,thaw_date:today()})
  await refresh();select(saved.id)
 })}
 async function remove(row:Coffee){const nested=children(row),ids=new Set([row.id,...nested.map(c=>c.id)]),count=shots.filter(s=>ids.has(s.coffee_id)).length
  if(!window.confirm(`Delete this ${row.source_coffee_id?'batch':'bag'}${nested.length?` and its ${nested.length} batches`:''}?${count?` Its ${count} shots will be removed from the visible logbook.`:''}`))return
  await run(async()=>{await ensureBean();await api(`/coffees/${row.id}?revision=${row.revision}`,'DELETE');setEditor(null);await refresh()})
 }
 function rowEditor(value:Editor){const row=value.row;const set=(changes:Partial<Coffee>)=>setEditor(current=>current?{...current,row:{...current.row,...changes}}:current)
  return <div className="inventory-editor" aria-label={value.kind==='bag'?'Edit bag':'Edit batch'}>
   {value.kind==='bag'?<><label>Size · g<input type="number" min="1" max="10000" value={row.bag_g??''} onChange={e=>{const grams=Number(e.target.value);set({bag_g:grams,frozen_g:row.freeze_date?(row.frozen_g===row.bag_g?grams:Math.min(row.frozen_g||grams,grams)):null})}}/></label><label>Roasted<input type="date" value={dateValue(row.roast_date)} onInput={e=>set({roast_date:e.currentTarget.value})}/></label><label>Bought<input type="date" value={dateValue(row.purchased_on)} onInput={e=>set({purchased_on:e.currentTarget.value})}/></label><label className="inventory-freeze"><input type="checkbox" checked={!!row.freeze_date} onChange={e=>set({freeze_date:e.target.checked?today():'',frozen_g:e.target.checked?row.bag_g:null})}/>Freeze</label>{row.freeze_date&&<label>Frozen<input type="date" value={dateValue(row.freeze_date)} onInput={e=>set({freeze_date:e.currentTarget.value})}/></label>}</>:<><label>Size<select value={row.portion_g||125} onChange={e=>set({portion_g:Number(e.target.value) as 125|250|500})}>{[125,250,500].map(size=><option key={size} value={size}>{size} g</option>)}</select></label><label>Started<input type="date" value={dateValue(row.thaw_date)} onInput={e=>set({thaw_date:e.currentTarget.value})}/></label></>}
   <div className="inventory-actions"><button type="button" disabled={busy} onClick={saveRow}>Save</button><button type="button" disabled={busy} onClick={()=>setEditor(null)}>Cancel</button></div>
  </div>
 }
 return <section className="bean-inventory" aria-label="Bags and batches">
  <div className="inventory-heading"><strong>Bags</strong><button type="button" disabled={busy} aria-expanded={adding} onClick={()=>setAdding(!adding)}>+ Bag</button></div>
  {error&&<p role="alert">{error}</p>}
  {adding&&<div className="inventory-add" aria-label="New bag size">{[250,500,1000].map(size=><button type="button" key={size} onClick={()=>addBag(size)}>{size===1000?'1 kg':size+' g'}</button>)}</div>}
  {editor?.kind==='bag'&&!editor.row.id&&rowEditor(editor)}
  {!bags.length&&!editor&&<p className="inventory-empty">Add your first bag of these beans.</p>}
  {bags.map((bag,index)=><div className="inventory-bag" key={bag.id}>
   <div className="inventory-row"><button type="button" className="inventory-name" aria-pressed={selected===bag.id} onClick={()=>select(bag.id)}>Bag {index+1} · {bag.bag_g?`${bag.bag_g} g`:'Size unknown'}<small>Roasted {dateLabel(bag.roast_date)}{bag.freeze_date?` · ${remaining(bag)} g frozen`:bag.purchased_on?` · Bought ${dateLabel(bag.purchased_on)}`:''}</small></button><div className="inventory-actions"><button type="button" disabled={busy} aria-label={`Edit bag ${index+1}`} onClick={()=>setEditor({kind:'bag',row:bag})}>Edit</button><button type="button" disabled={busy} aria-label={`Delete bag ${index+1}`} onClick={()=>remove(bag)}>Delete</button></div></div>
   {editor?.kind==='bag'&&editor.row.id===bag.id&&rowEditor(editor)}
   <div className="inventory-batches">
    {children(bag).map((batch,i)=><div key={batch.id}><div className="inventory-row"><button type="button" className="inventory-name" aria-pressed={selected===batch.id} onClick={()=>select(batch.id)}>Batch {i+1} · {batch.portion_g} g<small>{dateLabel(batch.thaw_date)} · ~{Math.max(0,(batch.portion_g||0)-used(batch))} g left</small></button><div className="inventory-actions"><button type="button" disabled={busy} aria-label={`Edit batch ${i+1} in bag ${index+1}`} onClick={()=>setEditor({kind:'batch',row:batch,parent:bag})}>Edit</button><button type="button" disabled={busy} aria-label={`Delete batch ${i+1} in bag ${index+1}`} onClick={()=>remove(batch)}>Delete</button></div></div>{editor?.kind==='batch'&&editor.row.id===batch.id&&rowEditor(editor)}</div>)}
    {(bag.bag_g||bag.frozen_g)&&<div className="inventory-add"><span>+ Batch</span>{([125,250,500] as const).map(size=><button type="button" key={size} disabled={busy||bag.archived||size>remaining(bag)} onClick={()=>addBatch(bag,size)}>{size} g</button>)}</div>}
   </div>
  </div>)}
 </section>
}
