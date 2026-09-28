import type {Coffee} from './api'

export const coffeeBagId=(coffee:Coffee)=>coffee.source_coffee_id||coffee.id

export function currentBagCoffee(coffees:Coffee[],bag:Coffee):Coffee{
 return coffees.filter(row=>row.source_coffee_id===bag.id&&!row.archived)
  .sort((a,b)=>(a.thaw_date||'').localeCompare(b.thaw_date||'')||(a.created_at||'').localeCompare(b.created_at||'')||a.id.localeCompare(b.id)).at(-1)||bag
}

// A batch is a portion of a bag, not another dropdown entry for the same coffee.
export function coffeePickerRows(coffees:Coffee[],selected=''):Coffee[]{
 const current=coffees.find(row=>row.id===selected&&!row.archived)
 return coffees.filter(row=>!row.source_coffee_id&&!row.archived).map(bag=>
  current&&coffeeBagId(current)===bag.id?current:currentBagCoffee(coffees,bag))
}

export function initialCoffeeSelection(coffees:Coffee[],selected:string):string{
 const current=coffees.find(row=>row.id===selected&&!row.archived)
 if(current)return current.source_coffee_id?current.id:currentBagCoffee(coffees,current).id
 return coffeePickerRows(coffees).at(-1)?.id||''
}
