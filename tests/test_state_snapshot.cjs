const assert = require('node:assert/strict')
const fs = require('node:fs')
const ts = require('../coffee_app/node_modules/typescript')
const source = fs.readFileSync(require('node:path').join(__dirname,'../coffee_app/src/stateSnapshot.ts'),'utf8')
const moduleRef = {exports:{}}
new Function('module','exports',ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText)(moduleRef,moduleRef.exports)
const {readSnapshot,writeSnapshot,clearSnapshot} = moduleRef.exports
const memory = (limit=Infinity)=>{const data=new Map();return {data,getItem:key=>data.get(key)??null,removeItem:key=>{data.delete(key)},setItem:(key,value)=>{if(value.length>limit)throw new Error('QuotaExceededError');data.set(key,value)}}}
const state = {beans:[{id:'bean',name:'Beans',revision:1}],coffees:[{id:'bag',name:'Beans',revision:2}],shots:[{id:'shot',coffee_id:'bag',revision:3}],messages:[{id:'m',role:'user',text:'hello'}],profile:{revision:1},capabilities:{chat:true},active_job:{id:'running'}}

// A saved state paints the next start, without live job state.
const store = memory()
writeSnapshot('owner','build-1',state,store)
const restored = readSnapshot('owner','build-1',store)
assert.deepEqual(restored.coffees,state.coffees)
assert.deepEqual(restored.shots,state.shots)
assert.deepEqual(restored.messages,state.messages)
assert.equal(restored.capabilities.chat,true)
assert.equal('active_job' in restored,false)

// Another account, another build, or damaged data never paints.
assert.equal(readSnapshot('someone-else','build-1',store),null)
assert.equal(readSnapshot('owner','build-2',store),null)
store.data.set('coffee.snapshot','{not json')
assert.equal(readSnapshot('owner','build-1',store),null)
store.data.set('coffee.snapshot',JSON.stringify({v:1,owner:'owner',build:'build-1',state:{coffees:{}}}))
assert.equal(readSnapshot('owner','build-1',store),null)
assert.equal(readSnapshot('owner','build-1',memory()),null)
assert.equal(readSnapshot('owner','build-1',null),null)

// A full store drops chat history before giving up the logbook.
const full = memory(JSON.stringify({v:1,owner:'owner',build:'build-1',state:{...state,active_job:undefined,messages:[]}}).length)
writeSnapshot('owner','build-1',state,full)
assert.deepEqual(readSnapshot('owner','build-1',full).messages,[])
assert.deepEqual(readSnapshot('owner','build-1',full).coffees,state.coffees)

// If nothing fits, the old copy is removed rather than left stale.
const tiny = memory(10)
tiny.data.set('coffee.snapshot','old')
writeSnapshot('owner','build-1',state,tiny)
assert.equal(tiny.data.has('coffee.snapshot'),false)

// Sign-out clears it, and a missing or throwing store is harmless.
writeSnapshot('owner','build-1',state,store)
clearSnapshot(store)
assert.equal(readSnapshot('owner','build-1',store),null)
clearSnapshot(null)
writeSnapshot('owner','build-1',state,null)
assert.equal(readSnapshot('owner','build-1',{getItem(){throw new Error('blocked')},setItem(){},removeItem(){}}),null)
console.log('State snapshot: paints own account and build only, drops chat first when full, clears on sign-out passed.')
