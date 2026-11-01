import type {Coffee} from './api'

export const coffeeBagId=(coffee:Coffee)=>coffee.source_coffee_id||coffee.id
const beanId=(coffees:Coffee[],coffee:Coffee)=>coffee.bean_id||coffees.find(row=>row.id===coffeeBagId(coffee))?.bean_id||coffeeBagId(coffee)

// The API marks the latest bag or thaw for each bean as current.
export function coffeePickerRows(coffees:Coffee[],archived=false):Coffee[]{
 return coffees.filter(row=>row.current&&!!row.archived===archived)
}

export function initialCoffeeSelection(coffees:Coffee[],selected:string):string{
 const previous=coffees.find(row=>row.id===selected)
 const rows=coffeePickerRows(coffees)
 return (previous?rows.find(row=>beanId(coffees,row)===beanId(coffees,previous)):undefined)?.id||rows.at(-1)?.id||''
}
