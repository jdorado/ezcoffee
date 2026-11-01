const assert = require('node:assert/strict')
const fs = require('node:fs')
const ts = require('../coffee_app/node_modules/typescript')
const source = fs.readFileSync(require('node:path').join(__dirname,'../coffee_app/src/coffeePicker.ts'),'utf8')
const moduleRef = {exports:{}}
new Function('module','exports',ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText)(moduleRef,moduleRef.exports)
const {coffeePickerRows,initialCoffeeSelection} = moduleRef.exports
const first={id:'first',name:'Decaf',bean_id:'beans',current:false}
const old={...first,id:'old-thaw',source_coffee_id:first.id,thaw_date:'2026-09-20'}
const latest={...first,id:'new-bag',current:true}
const unrelated={id:'other',name:'Other coffee',bean_id:'other-beans',current:true}
const rows=[first,latest,old,unrelated]
assert.deepEqual(coffeePickerRows(rows).map(row=>row.id),['new-bag','other'])
// A remembered earlier bag or thaw follows the current record for that bean.
assert.equal(initialCoffeeSelection(rows,'first'),'new-bag')
assert.equal(initialCoffeeSelection(rows,'old-thaw'),'new-bag')
assert.equal(initialCoffeeSelection(rows,'other'),'other')
assert.equal(initialCoffeeSelection(rows,'missing'),'other')
const newThaw={...old,id:'latest-thaw',current:true}
const advanced=[first,{...latest,current:false},old,newThaw,unrelated]
assert.equal(initialCoffeeSelection(advanced,'new-bag'),'latest-thaw')
// Archiving the latest record does not bring an earlier finished bag back.
const archived=[first,old,{...latest,archived:true},unrelated]
assert.deepEqual(coffeePickerRows(archived).map(row=>row.id),['other'])
assert.deepEqual(coffeePickerRows(archived,true).map(row=>row.id),['new-bag'])
assert.equal(initialCoffeeSelection(archived,'first'),'other')
console.log('Coffee picker: API current record only, new bag and thaw advance selection, unrelated beans stay separate, archives do not revive old bags.')
