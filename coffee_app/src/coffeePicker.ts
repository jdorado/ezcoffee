import type {Coffee} from './api'

export const coffeeBagId=(coffee:Coffee)=>coffee.source_coffee_id||coffee.id
const beanId=(coffees:Coffee[],coffee:Coffee)=>coffee.bean_id||coffees.find(row=>row.id===coffeeBagId(coffee))?.bean_id||coffeeBagId(coffee)

export function coffeeBags(coffees:Coffee[],coffee:Coffee):Coffee[]{
 const id=beanId(coffees,coffee)
 return coffees.filter(row=>!row.source_coffee_id&&beanId(coffees,row)===id)
}

export function currentBagCoffee(coffees:Coffee[],bag:Coffee):Coffee{
 return coffees.filter(row=>row.source_coffee_id===bag.id&&!row.archived)
  .sort((a,b)=>(a.thaw_date||'').localeCompare(b.thaw_date||'')||(a.created_at||'').localeCompare(b.created_at||'')||a.id.localeCompare(b.id)).at(-1)||bag
}

// The coffee list groups beans; the selected bag or batch still owns new brews.
export function coffeePickerRows(coffees:Coffee[],selected='',archived=false):Coffee[]{
 const current=coffees.find(row=>row.id===selected&&!!row.archived===archived)
 const activeBeans=new Set(coffees.filter(row=>!row.source_coffee_id&&!row.archived).map(row=>beanId(coffees,row)))
 const rows=new Map<string,Coffee>()
 for(const bag of coffees.filter(row=>!row.source_coffee_id&&!!row.archived===archived)){
  const id=beanId(coffees,bag)
  if(archived&&activeBeans.has(id))continue
  rows.set(id,current&&beanId(coffees,current)===id?current:currentBagCoffee(coffees,bag))
 }
 return [...rows.values()]
}

export function initialCoffeeSelection(coffees:Coffee[],selected:string):string{
 const current=coffees.find(row=>row.id===selected&&!row.archived)
 if(current)return current.source_coffee_id?current.id:currentBagCoffee(coffees,current).id
 return coffeePickerRows(coffees).at(-1)?.id||''
}
