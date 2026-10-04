const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const ts = require('../coffee_app/node_modules/typescript')
const source = fs.readFileSync(path.join(__dirname,'../coffee_app/src/coffeeHistory.ts'),'utf8')
const moduleRef = {exports:{}}
new Function('module','exports',ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText)(moduleRef,moduleRef.exports)
const {coffeeMessages} = moduleRef.exports
const coffees=[
 {id:'bag-a',bean_id:'bean-a'},
 {id:'old-a',bean_id:'bean-a',archived:true},
 {id:'batch-a',source_coffee_id:'bag-a'},
 {id:'bag-b',bean_id:'bean-b'}
]
const messages=[
 {id:'a-user',coffee_id:'bag-a',role:'user',text:'First bean'},
 {id:'b-user',coffee_id:'bag-b',role:'user',text:'Second bean'},
 {id:'a-reply',coffee_id:'old-a',role:'assistant',text:'Earlier bag'},
 {id:'a-failed',coffee_id:'batch-a',role:'assistant',text:'Retry',failed:true,retryable:true},
 {id:'general',coffee_id:null,role:'user',text:'General'},
 {id:'legacy',role:'user',text:'Unassigned'}
]
assert.deepEqual(coffeeMessages(messages,coffees,'batch-a').map(m=>m.id),['a-user','a-reply','a-failed'])
assert.deepEqual(coffeeMessages(messages,coffees,'bag-b').map(m=>m.id),['b-user'])
assert.deepEqual(coffeeMessages(messages,coffees,'bag-a').map(m=>m.id),['a-user','a-reply','a-failed'])
assert.deepEqual(coffeeMessages(messages,coffees,'').map(m=>m.id),['general','legacy'])
assert.deepEqual(coffeeMessages(messages,coffees,'missing'),[])
assert.equal(messages.length,6)
console.log('Chat history: bean switching, archived bags, batches, retries and general messages passed.')
