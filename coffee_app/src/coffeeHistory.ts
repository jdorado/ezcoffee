import type {Coffee,Message} from './api'

// History belongs to the beans; inventory and planned shots belong to a bag.
export function coffeeHistoryIds(coffees:Coffee[],selected:string):Set<string>{
 const coffee=coffees.find(row=>row.id===selected)
 if(!coffee)return new Set([selected])
 const bagId=coffee.source_coffee_id||coffee.id
 const beanId=coffee.bean_id||coffees.find(row=>row.id===bagId)?.bean_id
 const bagIds=new Set(coffees.filter(row=>!row.source_coffee_id&&(beanId?row.bean_id===beanId:row.id===bagId)).map(row=>row.id))
 return new Set([selected,...coffees.filter(row=>bagIds.has(row.source_coffee_id||row.id)).map(row=>row.id)])
}

// Use the same bean family as shot history and the server conversation context.
export function coffeeMessages(messages:Message[],coffees:Coffee[],selected:string):Message[]{
 const ids=coffeeHistoryIds(coffees,selected)
 return messages.filter(message=>selected?!!message.coffee_id&&ids.has(message.coffee_id):message.coffee_id==null)
}
