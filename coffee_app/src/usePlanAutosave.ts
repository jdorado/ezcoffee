import {useEffect,useRef,useState} from 'react'
import type {Shot} from './api'

type Patch=Partial<Shot>
type Queue={base:Shot;pending:Patch;timer?:ReturnType<typeof setTimeout>;writing:boolean;recovering?:boolean}
type Status={patch:Patch;saving:boolean;recovering?:boolean;error?:string}

export function usePlanAutosave(
 write:(id:string,patch:Patch)=>Promise<Shot>,
 accept:(shot:Shot)=>void,
 reload:()=>Promise<unknown>,
){
 const queues=useRef(new Map<string,Queue>())
 const [status,setStatus]=useState<Record<string,Status|undefined>>({})
 const show=(id:string,value:Status|undefined)=>setStatus(current=>({...current,[id]:value}))

 useEffect(()=>{
  const active=queues.current
  return()=>{active.forEach(queue=>clearTimeout(queue.timer));active.clear()}
 },[])

 function schedule(id:string,queue:Queue){
  clearTimeout(queue.timer)
  queue.timer=setTimeout(()=>{queue.timer=undefined;void flush(id,queue)},300)
 }

 async function flush(id:string,queue:Queue){
  if(queue.writing||queues.current.get(id)!==queue)return
  queue.writing=true
  const patch=queue.pending
  queue.pending={}
  try{
   const saved=await write(id,{...patch,coffee_id:queue.base.coffee_id,revision:queue.base.revision})
   if(queues.current.get(id)!==queue)return
   queue.base=saved
   accept(saved)
   if(Object.keys(queue.pending).length){
    show(id,{patch:queue.pending,saving:true})
   }else{
    queues.current.delete(id)
    show(id,undefined)
   }
  }catch(error){
   if(queues.current.get(id)!==queue)return
   clearTimeout(queue.timer)
   queue.recovering=true
   const message='Plan changes could not be saved. '+(error as Error).message
   show(id,{patch:{},saving:false,recovering:true,error:message})
   try{await reload()}catch{/* Keep the error visible if sync also fails. */}
   if(queues.current.get(id)===queue){
    queues.current.delete(id)
    show(id,{patch:{},saving:false,error:message})
   }
  }finally{
   queue.writing=false
   if(queues.current.get(id)===queue&&!queue.timer&&Object.keys(queue.pending).length)void flush(id,queue)
  }
 }

 function change(shot:Shot,patch:Patch){
  if(!shot.id)return
  const id=shot.id
  const queue=queues.current.get(id)??{base:shot,pending:{},writing:false}
  if(queue.recovering)return
  queues.current.set(id,queue)
  queue.pending={...queue.pending,...patch}
  setStatus(current=>({...current,[id]:{patch:{...current[id]?.patch,...patch},saving:true}}))
  schedule(id,queue)
 }

 return {change,status}
}
