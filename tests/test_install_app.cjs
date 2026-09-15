const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const ts = require('../coffee_app/node_modules/typescript')

const source = fs.readFileSync(path.resolve(__dirname, '../coffee_app/src/installApp.ts'), 'utf8')
const code = ts.transpile(source, {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020})

function load({agent='Mozilla/5.0 Chrome/140 Safari/537.36',touches=0,standalone=false}={}){
 const listeners = new Map()
 Object.defineProperty(globalThis,'navigator',{value:{userAgent:agent,maxTouchPoints:touches},configurable:true})
 global.window = {
  addEventListener(name,listener){listeners.set(name,listener)},
  removeEventListener(){},
  dispatchEvent(event){listeners.get(event.type)?.(event)},
  matchMedia(){return{matches:standalone}},
 }
 const module={exports:{}}
 new Function('module','exports','require',code)(module,module.exports,require)
 return {api:module.exports,listeners}
}

async function main(){
 const {api,listeners}=load()
 let prevented=false,prompted=false
 api.captureInstallPrompt()
 listeners.get('beforeinstallprompt')({
  preventDefault(){prevented=true},
  async prompt(){prompted=true},
  userChoice:Promise.resolve({outcome:'accepted'}),
 })
 assert.equal(prevented,true)
 assert.equal(api.installKind(),'native')
 const outcome=await api.promptInstall()
 assert.equal(prompted,true)
 assert.equal(outcome,'accepted')

 assert.equal(load({agent:'Mozilla/5.0 (iPhone) AppleWebKit/605.1.15 Version/26.0 Mobile Safari/604.1'}).api.installKind(),'ios-safari')
 assert.equal(load({agent:'Mozilla/5.0 (iPhone) AppleWebKit/605.1.15 CriOS/140 Mobile/15E148 Safari/604.1'}).api.installKind(),'ios-other')
 assert.equal(load({agent:'Mozilla/5.0 (Macintosh) AppleWebKit/605.1.15 Version/26.0 Safari/605.1.15'}).api.installKind(),'mac-safari')
 assert.equal(load({standalone:true}).api.installKind(),'installed')
 console.log('PWA install: native prompt, Safari guidance, and installed-app hiding covered.')
}

main().catch(error=>{console.error(error);process.exit(1)})
