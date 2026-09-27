import {forwardRef,useImperativeHandle,useState} from 'react'
import {api,today} from '../api'
import type {Bean,Coffee,Shot} from '../api'
import './BagRows.css'

type Editor={kind:'bag'|'batch';row:Partial<Coffee>;parent?:Coffee;frozen?:boolean}
type Props={startAdding?:boolean;beanId?:string;coffees:Coffee[];shots:Shot[];selected:string;ensureBean:()=>Promise<Bean>;refresh:()=>Promise<void>;select:(id:string)=>void}
export type BagRowsHandle={savePending:()=>Promise<boolean|undefined>}
const dateValue=(value='')=>{if(/^\d{4}-\d{2}-\d{2}$/.test(value))return value;const time=Date.parse(value);if(Number.isNaN(time))return '';const d=new Date(time);return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`}
const dateLabel=(value='')=>value?new Date(dateValue(value)+'T12:00:00').toLocaleDateString(undefined,{day:'numeric',month:'short'}):'Not set'
const sizeLabel=(grams:number)=>grams===1000?'1 kg':`${grams} g`
const bagEditor=(row:Partial<Coffee>):Editor=>({kind:'bag',row,frozen:!!row.freeze_date})
const newBag=()=>bagEditor({bag_g:1000,roast_date:'',freeze_date:'',revision:0})

export default forwardRef<BagRowsHandle,Props>(function BagRows({beanId,coffees,shots,selected,ensureBean,refresh,select,startAdding},ref){
 const [editor,setEditor]=useState<Editor|null>(()=>startAdding?newBag():null),[busy,setBusy]=useState(false),[error,setError]=useState('')
 useImperativeHandle(ref,()=>({savePending:saveRow}))
 const bags=coffees.filter(c=>c.bean_id===beanId&&!c.source_coffee_id).sort((a,b)=>(a.created_at||a.purchased_on||a.id).localeCompare(b.created_at||b.purchased_on||b.id))
 const selectedRow=coffees.find(c=>c.id===selected)
 const bag=bags.find(c=>c.id===(selectedRow?.source_coffee_id||selected))||bags.at(-1)
 const children=(parent:Coffee)=>coffees.filter(c=>c.source_coffee_id===parent.id).sort((a,b)=>(a.created_at||a.id).localeCompare(b.created_at||b.id))
 const used=(row:Coffee)=>shots.filter(s=>s.coffee_id===row.id&&s.status==='logged').reduce((sum,s)=>sum+(s.dose||0),0)
 const remaining=(parent:Coffee)=>Math.max(0,(parent.freeze_date?parent.frozen_g||0:parent.bag_g||0)-children(parent).reduce((sum,c)=>sum+(c.portion_g||0),0)-(parent.freeze_date?0:used(parent)))
 const batches=bag?children(bag):[]
 const bagName=(row:Coffee)=>`Bag ${bags.indexOf(row)+1} · ${row.bag_g?sizeLabel(row.bag_g):'Size not set'}`
 const editingBag=editor?.kind==='bag'
 async function run(action:()=>Promise<void>){if(busy)return false;setBusy(true);setError('');try{await action();return true}catch(e){setError((e as Error).message);return false}finally{setBusy(false)}}
 function chooseBag(id:string){const next=bags.find(row=>row.id===id);if(!next)return;setEditor(null);setError('');select(children(next).at(-1)?.id||id)}
 async function saveRow(){if(!editor)return;return run(async()=>{
  const row=editor.row,parent=editor.parent
  if(editor.kind==='bag'&&editor.frozen){
   if(!row.freeze_date)throw new Error('Set the freeze date before saving.')
   if(!row.roast_date)throw new Error('Set the roast date before freezing this bag.')
  }
  const bean=await ensureBean()
  const payload=editor.kind==='bag'?{...row,...bean,id:row.id,revision:row.revision||0,archived:row.archived||false,bean_id:bean.id,source_coffee_id:'',roast_date:row.roast_date||'',purchased_on:row.purchased_on||'',bag_g:row.bag_g,freeze_date:editor.frozen?row.freeze_date:'',frozen_g:editor.frozen?(row.frozen_g??row.bag_g):null,portion_g:null,thaw_date:'',frozen_portions:[]}:{...row,...bean,id:row.id,revision:row.revision||0,archived:row.archived||false,bean_id:bean.id,source_coffee_id:parent!.id,roast_date:parent!.roast_date,freeze_date:parent!.freeze_date||'',bag_g:null,frozen_g:null,frozen_portions:[],portion_g:row.portion_g,thaw_date:row.thaw_date}
  const saved=await api(row.id?'/coffees/'+row.id:'/coffees',row.id?'PUT':'POST',payload)
  setEditor(null);await refresh();if(!row.id||editor.kind==='batch')select(saved.id)
 })}
 async function addBatch(parent:Coffee,size:125|250|500){await run(async()=>{
  const bean=await ensureBean();const saved=await api('/coffees','POST',{...bean,id:undefined,revision:0,bean_id:bean.id,source_coffee_id:parent.id,roast_date:parent.roast_date,freeze_date:parent.freeze_date||'',portion_g:size,thaw_date:today()})
  setEditor(null);await refresh();select(saved.id)
 })}
 async function remove(row:Coffee){const nested=children(row),ids=new Set([row.id,...nested.map(c=>c.id)]),count=shots.filter(s=>ids.has(s.coffee_id)).length
  if(!window.confirm(`Delete this ${row.source_coffee_id?'batch':'bag'}${nested.length?` and its ${nested.length} batches`:''}?${count?` Its ${count} shots will be removed from the visible logbook.`:''}`))return
  await run(async()=>{await ensureBean();await api(`/coffees/${row.id}?revision=${row.revision}`,'DELETE');setEditor(null);await refresh();if(row.source_coffee_id){const siblings=children(bag!).filter(c=>c.id!==row.id);select(siblings.at(-1)?.id||row.source_coffee_id)}else{const next=bags.filter(c=>c.id!==row.id).at(-1);if(next)select(children(next).at(-1)?.id||next.id)}})
 }
 function rowEditor(value:Editor){
  const row=value.row,isBag=value.kind==='bag',frozen=!!value.frozen
  const set=(changes:Partial<Coffee>)=>setEditor(current=>current?{...current,row:{...current.row,...changes}}:current)
  const setFrozen=(next:boolean)=>setEditor(current=>current?{...current,frozen:next,row:{...current.row,freeze_date:next?(current.row.freeze_date||today()):'',frozen_g:next?(current.row.frozen_g??current.row.bag_g):null}}:current)
  const setSize=(grams:number)=>set({bag_g:grams,frozen_g:frozen?(row.frozen_g===row.bag_g?grams:Math.min(row.frozen_g||grams,grams)):null})
  return <div className="inventory-editor" role="group" aria-label={isBag?(row.id?'Edit bag':'New bag'):'Edit batch'}>
   {isBag?<>
    <div className="inventory-size" role="group" aria-label="Bag size"><span>Bag size</span><div className="inventory-options">{[250,500,1000].map(size=><button type="button" key={size} disabled={busy} aria-pressed={row.bag_g===size} onClick={()=>setSize(size)}>{sizeLabel(size)}</button>)}<label className="inventory-custom-size"><input aria-label="Custom bag size in grams" type="number" min="1" max="10000" placeholder="Other" value={[250,500,1000].includes(row.bag_g||0)?'':row.bag_g??''} onChange={e=>setSize(Number(e.target.value))}/><span>g</span></label></div></div>
    <div className="inventory-dates"><label>Roasted<input type="date" value={dateValue(row.roast_date)} onInput={e=>set({roast_date:e.currentTarget.value})}/></label></div>
    <div className="inventory-storage"><div className="inventory-options" role="group" aria-label="Bag storage"><button type="button" disabled={busy} aria-pressed={!frozen} onClick={()=>setFrozen(false)}>Room temperature</button><button type="button" disabled={busy} aria-pressed={frozen} onClick={()=>{if(!frozen)setFrozen(true)}}>Freezer</button></div>{frozen&&<label>Frozen<input type="date" value={dateValue(row.freeze_date)} onInput={e=>set({freeze_date:e.currentTarget.value})}/></label>}</div>
   </>:<div className="inventory-dates"><label>Size<select value={row.portion_g||125} onChange={e=>set({portion_g:Number(e.target.value) as 125|250|500})}>{[125,250,500].map(size=><option key={size} value={size}>{size} g</option>)}</select></label><label>Started<input type="date" value={dateValue(row.thaw_date)} onInput={e=>set({thaw_date:e.currentTarget.value})}/></label></div>}
   <div className="inventory-editor-actions"><button className="inventory-save" type="button" disabled={busy} onClick={saveRow}>{busy?'Saving…':row.id?'Save changes':'Add bag'}</button><button type="button" disabled={busy} onClick={()=>{setEditor(null);setError('')}}>Cancel</button>{row.id&&<button className="inventory-delete" type="button" disabled={busy} onClick={()=>remove(row as Coffee)}>Delete {value.kind}</button>}</div>
  </div>
 }
 return <section className="bean-inventory" aria-label="Bags and batches">
  <div className="inventory-heading"><strong>{editingBag?(editor.row.id?'Edit bag':'New bag'):'Bags'}</strong>{!editingBag&&<button type="button" disabled={busy} onClick={()=>{setError('');setEditor(newBag())}}>+ Bag</button>}</div>
  {error&&<p role="alert">{error}</p>}
  {editingBag?rowEditor(editor):bag?<>
   <div className="inventory-bag-picker"><select aria-label="Choose bag" value={bag.id} disabled={busy} onChange={e=>chooseBag(e.target.value)}>{bags.map(row=><option key={row.id} value={row.id}>{bagName(row)}</option>)}</select><button type="button" disabled={busy} onClick={()=>{setError('');setEditor(bagEditor(bag))}}>Edit bag</button></div>
   <div className="inventory-bag-summary"><span>Roasted {dateLabel(bag.roast_date)}</span><span>{bag.freeze_date?`${Math.round(remaining(bag))} g in freezer`:bag.bag_g?`~${Math.round(remaining(bag))} g ${batches.length?'in bag':'left'}`:'Room temperature'}</span></div>
   <div className="inventory-batches" aria-label="Batches in selected bag">
    <div className="inventory-batch-heading"><strong>Batches</strong>{!!(bag.bag_g||bag.frozen_g)&&<div className="inventory-options" role="group" aria-label="Start a new batch today">{([125,250,500] as const).map(size=><button type="button" key={size} disabled={busy||!!editor||bag.archived||size>remaining(bag)} aria-label={`Add ${size} g batch`} onClick={()=>addBatch(bag,size)}>+ {size} g</button>)}</div>}</div>
    {!batches.length&&<p className="inventory-empty">{bag.freeze_date?'Tap a size to take your first batch out.':bag.bag_g?'Using the whole bag. Tap a size to split off a batch.':'Set the bag size to add batches.'}</p>}
    {batches.map((batch,i)=><div className="inventory-batch" key={batch.id}>
     {editor?.row.id===batch.id?rowEditor(editor):<div className="inventory-row"><button type="button" className="inventory-name" disabled={busy||batch.archived} aria-pressed={selected===batch.id} onClick={()=>select(batch.id)}><span>Batch {i+1} <span className="inventory-batch-size">· {batch.portion_g} g</span>{selected===batch.id&&<span className="inventory-current">Current</span>}</span><small>{bag.freeze_date?'Thawed':'Started'} {dateLabel(batch.thaw_date)} · ~{Math.round(Math.max(0,(batch.portion_g||0)-used(batch)))} g left</small></button><button type="button" className="inventory-edit" disabled={busy} aria-label={`Edit batch ${i+1}`} onClick={()=>{setError('');setEditor({kind:'batch',row:batch,parent:bag})}}>Edit</button></div>}
    </div>)}
   </div>
  </>:<p className="inventory-empty">Add your first bag of these beans.</p>}
 </section>
})
