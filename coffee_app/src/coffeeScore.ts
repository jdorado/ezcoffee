import type {Coffee,Shot} from './api'

function day(value:string){const time=Date.parse(value.length===10?value+'T12:00:00':value);return Number.isNaN(time)?null:Math.floor(time/86400000)}
function shotOrder(shot:Shot){return day(shot.date)||day(shot.recorded_at||'')||Number(shot.id?.match(/^import-(\d+)$/)?.[1]||0)}

export function coffeeAgeDays(coffee:Coffee,asOf:string){
 const roast=day(coffee.roast_date),current=day(asOf)
 if(roast==null||current==null||current<roast)return null
 const freeze=day(coffee.freeze_date||'')
 if(freeze==null||current<freeze)return current-roast
 const thaw=day(coffee.thaw_date||'')
 return freeze-roast+(thaw!=null&&current>=thaw?current-thaw:0)
}

export function coffeeScore(shots:Shot[],coffee:Coffee,coffees:Coffee[]=[coffee]){
 const rootId=coffee.source_coffee_id||coffee.id
 const group=coffees.filter(row=>row.id===rootId||row.source_coffee_id===rootId)
 const byId=new Map(group.map(row=>[row.id,row]))
 const recent=shots.filter(shot=>byId.has(shot.coffee_id)&&shot.status==='logged'&&shot.rating!=null&&!shot.choked&&!['adjust','bad','choked'].includes(shot.outcome||''))
  .sort((a,b)=>shotOrder(b)-shotOrder(a)).slice(0,5)
 if(!recent.length)return {score:null,count:0}
 const entries=recent.map((shot,index)=>{
  const age=coffeeAgeDays(byId.get(shot.coffee_id)!,shot.date)
  const inWindow=age!=null&&age>=7&&age<=28
  return {rating:shot.rating!,weight:Math.pow(.72,index)*(age!=null&&!inWindow?.6:1),inWindow}
 })
 const weight=entries.reduce((sum,entry)=>sum+entry.weight,0)
 const recentMean=entries.reduce((sum,entry)=>sum+entry.rating*entry.weight,0)/weight
 const peakPool=entries.some(entry=>entry.inWindow)?entries.filter(entry=>entry.inWindow):entries
 const peak=Math.max(...peakPool.map(entry=>entry.rating))
 return {score:(.75*recentMean+.25*peak).toFixed(1),count:entries.length}
}
