const assert = require('node:assert/strict')
const fs = require('node:fs')
const ts = require('../coffee_app/node_modules/typescript')
const source = fs.readFileSync(require.resolve('../coffee_app/src/copyContext.ts'), 'utf8')
const code = ts.transpile(source, {module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020})
let fetchText, requests=[],writes=[]
const moduleMock={exports:{}}
new Function('module','exports','require',code)(moduleMock,moduleMock.exports,()=>({api:async path=>{requests.push(path);return {text:await fetchText()}}}))
const copy=moduleMock.exports.copyCoffeeContext
Object.defineProperty(globalThis,'navigator',{value:{clipboard:{}},configurable:true})
global.ClipboardItem=class{constructor(data){this.data=data}}

async function main(){
 let resolveText
 fetchText=()=>new Promise(resolve=>{resolveText=resolve})
 let started=false
 navigator.clipboard.write=async items=>{started=true;const blob=await items[0].data['text/plain'];writes.push(await blob.text())}
 const pending=copy('bag/one')
 assert.equal(started,true,'Clipboard write starts before the network resolves (Safari user gesture)')
 resolveText('Fresh context one');await pending
 fetchText=async()=>'Fresh context two';await copy('bag/one')
 assert.deepEqual(writes,['Fresh context one','Fresh context two'])
 assert.deepEqual(requests,['/coffees/bag%2Fone/context','/coffees/bag%2Fone/context'])
 fetchText=async()=>{throw new Error('Sign in again')}
 await assert.rejects(copy('bag'),/Sign in again/)
 fetchText=async()=>'Context'
 navigator.clipboard.write=async items=>{await items[0].data['text/plain'];throw new Error('Clipboard permission denied')}
 await assert.rejects(copy('bag'),/Clipboard permission denied/)
 delete global.ClipboardItem
 navigator.clipboard.writeText=async text=>writes.push(text)
 await copy('bag');assert.equal(writes.at(-1),'Context')
 navigator.clipboard=undefined
 const count=requests.length
 await assert.rejects(copy('bag'),/HTTPS/)
 assert.equal(requests.length,count,'Unavailable clipboard does not fetch context')
 console.log('Copy context: gesture-safe write, fresh repeated copies, API/permission failures, fallback and unavailable clipboard passed.')
}
main().catch(error=>{console.error(error);process.exit(1)})
