import {forwardRef,useImperativeHandle,useState} from 'react'
import {api,today} from '../api'
import type {Bean,Coffee} from '../api'
import {coffeeBagId} from '../coffeePicker'
import './BagRows.css'

type Editor={row:Partial<Coffee>;parent?:Coffee;frozen?:boolean}
type Props={startAdding?:boolean;beanId?:string;coffees:Coffee[];ensureBean:()=>Promise<Bean>;refresh:()=>Promise<void>;select:(id:string)=>void}
export type BagRowsHandle={savePending:()=>Promise<boolean|undefined>}
const dateValue=(value='')=>{if(/^\d{4}-\d{2}-\d{2}$/.test(value))return value;const time=Date.parse(value);if(Number.isNaN(time))return '';const d=new Date(time);return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`}
const dateLabel=(value='')=>value?new Date(dateValue(value)+'T12:00:00').toLocaleDateString(undefined,{day:'numeric',month:'short'}):'Not set'
const newBag=():Editor=>({row:{roast_date:'',freeze_date:'',revision:0}})

export default forwardRef<BagRowsHandle,Props>(function BagRows({beanId,coffees,ensureBean,refresh,select,startAdding},ref){
 const [editor,setEditor]=useState<Editor|null>(()=>startAdding?newBag():null),[busy,setBusy]=useState(false),[error,setError]=useState('')
 useImperativeHandle(ref,()=>({savePending:saveRow}))
 const rows=coffees.filter(row=>beanId&&row.bean_id===beanId)
 const current=rows.find(row=>row.current),bag=current?rows.find(row=>row.id===coffeeBagId(current)):undefined
 const history=rows.filter(row=>row.id!==current?.id).sort((a,b)=>(b.created_at||b.thaw_date||b.roast_date||'').localeCompare(a.created_at||a.thaw_date||a.roast_date||''))
 async function run(action:()=>Promise<void>){if(busy)return false;setBusy(true);setError('');try{await action();return true}catch(e){setError((e as Error).message);return false}finally{setBusy(false)}}
 async function saveRow(){if(!editor)return;return run(async()=>{
  const {row,parent,frozen}=editor
  if(!parent&&frozen&&!row.freeze_date)throw new Error('Set the freeze date before saving.')
  const bean=await ensureBean()
  const payload={...row,...bean,id:row.id,revision:row.revision||0,archived:row.archived||false,bean_id:bean.id,source_coffee_id:parent?.id||'',roast_date:parent?.roast_date||row.roast_date||'',freeze_date:parent?parent.freeze_date||'':frozen?row.freeze_date:'',thaw_date:parent?row.thaw_date:''}
  const saved=await api(row.id?'/coffees/'+row.id:'/coffees',row.id?'PUT':'POST',payload)
  setEditor(null);await refresh();if(!row.id)select(saved.id)
 })}
 function edit(row:Coffee){setError('');setEditor({row,parent:row.source_coffee_id?coffees.find(parent=>parent.id===row.source_coffee_id):undefined,frozen:!!row.freeze_date})}
 async function remove(row:Coffee){
  if(!window.confirm(`Delete this ${row.source_coffee_id?'thaw':'bag'} record?${row.source_coffee_id?'':' Its thaw records will also be removed.'} Its shots will leave the visible logbook.`))return
  await run(async()=>{await api(`/coffees/${row.id}?revision=${row.revision}`,'DELETE');setEditor(null);await refresh()})
 }
 function record(row:Coffee){return <div className="inventory-row" key={row.id}><div className="inventory-name"><span>{row.source_coffee_id?'Thawed '+dateLabel(row.thaw_date):'Bag · roasted '+dateLabel(row.roast_date)}{row.current&&<span className="inventory-current">Current</span>}</span><small>{row.source_coffee_id?'Roasted '+dateLabel(row.roast_date):row.freeze_date?'Frozen '+dateLabel(row.freeze_date):'Room temperature'}</small></div><button type="button" disabled={busy} className="inventory-edit" onClick={()=>edit(row)}>Edit dates</button></div>}
 const row=editor?.row
 const set=(changes:Partial<Coffee>)=>setEditor(value=>value?{...value,row:{...value.row,...changes}}:value)
 return <section className="bean-inventory" aria-label="Coffee dates and history">
  <div className="inventory-heading"><strong>Dates & history</strong>{!editor&&<div className="inventory-actions"><button type="button" disabled={busy} onClick={()=>{setError('');setEditor(newBag())}}>+ New bag</button>{bag&&<button type="button" disabled={busy||bag.archived} onClick={()=>{setError('');setEditor({row:{thaw_date:today(),revision:0},parent:bag})}}>Thaw coffee</button>}</div>}</div>
  <p className="inventory-empty">A new bag or thaw replaces the previous one. Only dates are tracked.</p>
  {error&&<p role="alert">{error}</p>}
  {editor&&row?<div className="inventory-editor" role="group" aria-label={row.id?'Edit dates':editor.parent?'New thaw':'New bag'}>
   <div className="inventory-dates">{editor.parent?<label>Thawed<input type="date" value={dateValue(row.thaw_date)} onInput={e=>set({thaw_date:e.currentTarget.value})}/></label>:<label>Roasted<input type="date" value={dateValue(row.roast_date)} onInput={e=>set({roast_date:e.currentTarget.value})}/></label>}</div>
   {!editor.parent&&<div className="inventory-storage"><div className="inventory-options" role="group" aria-label="Bag storage"><button type="button" disabled={busy} aria-pressed={!editor.frozen} onClick={()=>setEditor({...editor,frozen:false})}>Room temperature</button><button type="button" disabled={busy} aria-pressed={!!editor.frozen} onClick={()=>setEditor({...editor,frozen:true,row:{...row,freeze_date:row.freeze_date||today()}})}>Freezer</button></div>{editor.frozen&&<label>Frozen<input type="date" value={dateValue(row.freeze_date)} onInput={e=>set({freeze_date:e.currentTarget.value})}/></label>}</div>}
   <div className="inventory-editor-actions"><button className="inventory-save" type="button" disabled={busy} onClick={saveRow}>{busy?'Saving…':row.id?'Save dates':editor.parent?'Record thaw':'Add bag'}</button><button type="button" disabled={busy} onClick={()=>{setEditor(null);setError('')}}>Cancel</button>{row.id&&<button className="inventory-delete" type="button" disabled={busy} onClick={()=>remove(row as Coffee)}>Delete record</button>}</div>
  </div>:current?record(current):<p className="inventory-empty">Add a bag to start using these beans.</p>}
  {!!history.length&&<details className="inventory-history"><summary>Earlier records ({history.length})</summary>{history.map(record)}</details>}
 </section>
})
