const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const ts = require('../coffee_app/node_modules/typescript')
const {renderToStaticMarkup} = require('../coffee_app/node_modules/react-dom/server')
const source = fs.readFileSync(path.join(__dirname,'../coffee_app/src/main.tsx'),'utf8')
const ast = ts.createSourceFile('main.tsx',source,ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX)
let calculation, badge
function visit(node){
 if(ts.isFunctionDeclaration(node)&&node.name?.text==='ratio')calculation=node.getText(ast)
 if(ts.isJsxElement(node)&&node.openingElement.attributes.properties.some(prop=>ts.isJsxAttribute(prop)&&prop.name.text==='className'&&prop.initializer?.text==='shot-settings'))badge=node.children.find(ts.isJsxExpression).getText(ast)
 ts.forEachChild(node,visit)
}
visit(ast)
assert.ok(calculation&&badge,'Test the calculation and JSX used by the real shot card')
const code=ts.transpileModule(`export function render(s:Shot,metrics:ShotMetric[],isFilter:boolean){${calculation};return <>${badge}</>}`,{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2022}}).outputText
const moduleRef={exports:{}}
new Function('module','exports','require',code)(moduleRef,moduleRef.exports,name=>require('../coffee_app/node_modules/'+name))
const render=(shot,metrics=[],isFilter=false)=>renderToStaticMarkup(moduleRef.exports.render(shot,metrics,isFilter))
const shot={dose:18,yield_g:36,water_g:300,stop_yield_g:30,target_yield_g:40,ice_g:100}
assert.equal(render(shot),'<span class="ratio" aria-label="Dose-to-yield ratio">1 : 2.00</span>')
assert.match(render({...shot,dose:20,yield_g:45}),/>1 : 2.25</)
assert.match(render({...shot,dose:20},[],true),/aria-label="Coffee-to-water ratio">1 : 15.00</)
assert.equal(render(shot,[{label:'RATIO'}]),'','Do not duplicate a ratio already in the card metrics')
for(const value of [null,undefined,0,-1,NaN,Infinity]){
 assert.match(render({...shot,dose:value}),/>Ratio —</)
 assert.match(render({...shot,yield_g:value}),/>Ratio —</)
 assert.match(render({...shot,water_g:value},[],true),/>Ratio —</)
}
assert.match(render({...shot,yield_g:null}),/>Ratio —</,'A target or stop yield does not stand in for measured output')
assert.match(render({...shot,dose:18.5,yield_g:40}),/>1 : 2.16</)
console.log('Shot card ratio: measured yield/dose, filter water/dose, rounding, updated values, missing/zero inputs, rendering and no duplicate display passed.')
