const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const ts = require('../coffee_app/node_modules/typescript')

const source = fs.readFileSync(path.join(__dirname, '../coffee_app/src/coffeeScore.ts'), 'utf8')
const compiled = ts.transpileModule(source, {compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText
const moduleRef = {exports:{}}
new Function('module', 'exports', compiled)(moduleRef, moduleRef.exports)
const {coffeeAgeDays,coffeeScore} = moduleRef.exports
const coffee = {id:'bag-1',roast_date:'2026-09-01'}
const shot = (id, date, rating, outcome='good', status='logged', coffee_id='bag-1') => ({id,date,rating,outcome,status,coffee_id})

const scored = [
 shot('peak','2026-09-10',5),
 shot('latest','2026-09-12',3),
 shot('dial-in','2026-09-13',1,'bad'),
 shot('plan','2026-09-14',5,'good','planned'),
 shot('other-bag','2026-09-15',5,'good','logged','bag-2'),
]
assert.deepEqual(coffeeScore(scored,coffee),{score:'4.1',count:2})
assert.equal(coffeeScore([shot('early','2026-09-03',5),shot('optimal','2026-09-12',3)],coffee).score,'3.5')
assert.deepEqual(coffeeScore(scored,{id:'bag-3',roast_date:'2026-09-20'}),{score:null,count:0})
const frozen={id:'frozen',roast_date:'2026-09-01',freeze_date:'2026-09-05'}
const thawed={id:'portion',source_coffee_id:'frozen',roast_date:'2026-09-01',freeze_date:'2026-09-05',thaw_date:'2026-10-01',portion_g:125}
assert.equal(coffeeAgeDays(frozen,'2026-10-10'),4)
assert.equal(coffeeAgeDays(thawed,'2026-10-10'),13)
const frozenShots=[shot('before-freeze','2026-09-03',4,'good','logged','frozen'),shot('after-thaw','2026-10-10',5,'good','logged','portion')]
assert.equal(coffeeScore(frozenShots,frozen,[frozen,thawed]).count,2)
assert.deepEqual(coffeeScore(frozenShots,thawed,[frozen,thawed]),coffeeScore(frozenShots,frozen,[frozen,thawed]))
console.log('Coffee score: recent qualifying shots and an in-window peak count; bad, planned, and other-bag shots do not.')
