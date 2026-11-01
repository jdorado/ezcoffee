const assert = require('node:assert/strict')
const fs = require('node:fs')
const ts = require('../coffee_app/node_modules/typescript')
const source = fs.readFileSync(require('node:path').join(__dirname,'../coffee_app/src/coffeePicker.ts'),'utf8')
const moduleRef = {exports:{}}
new Function('module','exports',ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText)(moduleRef,moduleRef.exports)
const {coffeeBags,coffeePickerRows,initialCoffeeSelection,currentBagCoffee} = moduleRef.exports
const bag = (id,extra={})=>({id,name:'Same beans',brand:'Roaster',bean_id:'beans',freeze_date:'2026-09-18',bag_g:250,frozen_g:250,...extra})
const batch = (id,parent,date,extra={})=>({...parent,id,source_coffee_id:parent.id,thaw_date:date,portion_g:125,...extra})
const first=bag('first'),second=bag('second'),unopened=bag('unopened'),archived=bag('archived',{archived:true})
const old=batch('old',first,'2026-09-20'),latest=batch('latest',first,'2026-09-28'),other=batch('other',second,'2026-09-28')
const rows=[first,second,unopened,archived,latest,old,other,batch('archived-batch',archived,'2026-09-28',{archived:true}),batch('retired',first,'2026-09-29',{archived:true})]
// One coffee entry, while its bags and thaw dates remain separate inventory.
assert.deepEqual(coffeePickerRows(rows).map(row=>row.id),['unopened'])
assert.deepEqual(coffeeBags(rows,old).map(row=>row.id),['first','second','unopened','archived'])
assert.equal(coffeePickerRows(rows,'old')[0].thaw_date,'2026-09-20')
assert.equal(coffeePickerRows(rows,'other')[0].thaw_date,'2026-09-28')
assert.equal(initialCoffeeSelection(rows,'first'),'latest')
assert.equal(initialCoffeeSelection(rows,'old'),'old')
assert.equal(initialCoffeeSelection(rows,'missing'),'unopened')
assert.equal(initialCoffeeSelection([archived],''),'')
assert.equal(currentBagCoffee(rows,first).id,'latest')
// Explicit history selection stays accessible without duplicating the coffee.
assert.deepEqual(coffeePickerRows(rows,'old').map(row=>row.id),['old'])
assert.deepEqual(coffeePickerRows(rows,'first').map(row=>row.id),['first'])
// Names never determine identity; unrelated beans and legacy purchases stay separate.
const unrelated=bag('unrelated',{bean_id:'other-beans'}),legacy=bag('legacy',{bean_id:undefined})
const legacyBatch=batch('legacy-batch',legacy,'2026-10-01')
assert.deepEqual(coffeePickerRows([...rows,unrelated,legacy,legacyBatch]).map(row=>row.id),['unopened','unrelated','legacy-batch'])
assert.deepEqual(coffeeBags([...rows,legacy,legacyBatch],legacyBatch).map(row=>row.id),['legacy'])
// Archived bags of an active coffee live in Manage bags, not duplicate coffee rows.
assert.deepEqual(coffeePickerRows(rows,'',true),[])
assert.deepEqual(coffeePickerRows([archived,bag('archived-two',{archived:true})],'',true).map(row=>row.id),['archived-two'])
console.log('Coffee picker: one entry per coffee, separate bags and thaw dates, preserved selection, archives and legacy identity passed.')
