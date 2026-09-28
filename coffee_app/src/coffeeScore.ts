import type {Coffee,Shot} from './api'

function day(value?:string|null){
 if(!value)return null
 const dateOnly=/^\d{4}-\d{2}-\d{2}$/.test(value)?value+'T12:00:00Z':/^\d{1,2} [A-Za-z]+ \d{4}$/.test(value)?value+' 12:00:00 UTC':value
 const time=Date.parse(dateOnly)
 return Number.isNaN(time)?null:Math.floor(time/86400000)
}

// Product heuristics, matching the freshness indicator's estimated 7–28 day window.
const AGE_HALF_LIFE=14
const WINDOW_HALF_LIFE=7
const PEAK_SHARE=.25

export function coffeeAgeDays(coffee:Coffee,asOf:string){
 const roast=day(coffee.roast_date),current=day(asOf)
 if(roast==null||current==null||current<roast)return null
 if(coffee.bag_g&&coffee.bag_g>(coffee.frozen_g||0)&&!coffee.source_coffee_id)return current-roast
 const freeze=day(coffee.freeze_date)
 if(freeze==null||freeze<roast||current<freeze)return current-roast
 const thaw=day(coffee.thaw_date)
 if(thaw!=null&&thaw<freeze)return null
 return freeze-roast+(thaw!=null&&current>=thaw?current-thaw:0)
}

export function coffeeScore(shots:Shot[],coffee:Coffee,coffees:Coffee[]=[coffee]){
 const rootId=coffee.source_coffee_id||coffee.id
 const group=coffees.filter(row=>row.id===rootId||row.source_coffee_id===rootId)
 const byId=new Map(group.map(row=>[row.id,row]))
 const rated=shots.filter(shot=>byId.has(shot.coffee_id)&&shot.status==='logged'&&shot.rating!=null&&Number.isFinite(shot.rating)&&shot.rating>=1&&shot.rating<=5&&!shot.choked&&!['adjust','bad','choked'].includes(shot.outcome||''))
  .map(shot=>({shot,day:day(shot.date),age:coffeeAgeDays(byId.get(shot.coffee_id)!,shot.date)}))
  .sort((a,b)=>(b.day??-Infinity)-(a.day??-Infinity)||(Date.parse(b.shot.recorded_at||'')||0)-(Date.parse(a.shot.recorded_at||'')||0)||(a.shot.id||'').localeCompare(b.shot.id||''))
 if(!rated.length)return {score:null,count:0}
 const latest=rated[0]
 const entries=rated.map(({shot,day:shotDay,age})=>{
  // Across batches, the age can reset after thawing. Compare both directions:
  // a months-later batch at day 12 should still learn from earlier day-12 brews.
  // Missing roast dates fall back to elapsed brew days; undated shots are neutral.
  const gap=age!=null&&latest.age!=null?Math.abs(latest.age-age):latest.day!=null&&shotDay!=null?Math.max(0,latest.day-shotDay):0
  const outsideWindow=age==null?null:Math.max(7-age,age-28,0)
  const penalty=gap/AGE_HALF_LIFE+(outsideWindow==null?-Math.log2(.6):outsideWindow/WINDOW_HALF_LIFE)
  return {rating:shot.rating!,penalty,weight:0}
 })
 // Normalize before exponentiating so even very old bags retain a finite score.
 const minimumPenalty=entries.reduce((minimum,entry)=>Math.min(minimum,entry.penalty),Infinity)
 entries.forEach(entry=>{entry.weight=Math.pow(2,minimumPenalty-entry.penalty)})
 const weight=entries.reduce((sum,entry)=>sum+entry.weight,0)
 const mean=entries.reduce((sum,entry)=>sum+entry.rating*entry.weight,0)/weight
 // Better shots add a small lift proportional to their evidence weight. One
 // lucky or out-of-window high rating no longer gets a fixed 25% peak bonus.
 const peakLift=entries.reduce((sum,entry)=>sum+Math.max(0,entry.rating-mean)*entry.weight,0)/weight
 return {score:(mean+PEAK_SHARE*peakLift).toFixed(1),count:entries.length}
}
