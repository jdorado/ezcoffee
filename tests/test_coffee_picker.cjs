const assert = require('node:assert/strict')
const fs = require('node:fs')
const ts = require('../coffee_app/node_modules/typescript')
const source = fs.readFileSync(require('node:path').join(__dirname,'../coffee_app/src/coffeePicker.ts'),'utf8')
const moduleRef = {exports:{}}
new Function('module','exports',ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText)(moduleRef,moduleRef.exports)
const {coffeePickerRows,initialCoffeeSelection,currentBagCoffee} = moduleRef.exports
const bag = (id,extra={})=>({id,name:'Same beans',brand:'Roaster',bean_id:'beans',freeze_date:'2026-09-18',bag_g:250,frozen_g:250,...extra})
const batch = (id,parent,date,extra={})=>({...parent,id,source_coffee_id:parent.id,thaw_date:date,portion_g:125,...extra})
const first=bag('first'),second=bag('second'),unopened=bag('unopened'),archived=bag('archived',{archived:true})
const old=batch('old',first,'2026-09-20'),latest=batch('latest',first,'2026-09-28'),other=batch('other',second,'2026-09-28')
const rows=[first,second,unopened,archived,latest,old,other,batch('archived-batch',archived,'2026-09-28',{archived:true}),batch('retired',first,'2026-09-29',{archived:true})]
// Two bags of the same beans remain separate; each bag's batches share one entry.
assert.deepEqual(coffeePickerRows(rows).map(row=>row.id),['latest','other','unopened'])
assert.equal(initialCoffeeSelection(rows,'first'),'latest')
assert.equal(initialCoffeeSelection(rows,'old'),'old')
assert.equal(initialCoffeeSelection(rows,'missing'),'unopened')
assert.equal(initialCoffeeSelection([archived],''),'')
assert.equal(currentBagCoffee(rows,first).id,'latest')
// Explicit history selection stays accessible without adding a second bag entry.
assert.deepEqual(coffeePickerRows(rows,'old').map(row=>row.id),['old','other','unopened'])
assert.deepEqual(coffeePickerRows(rows,'first').map(row=>row.id),['first','other','unopened'])
console.log('Coffee picker: one entry per bag, current batch, distinct purchases, archives and history passed.')
