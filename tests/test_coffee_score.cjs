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
assert.deepEqual(coffeeScore(scored,{id:'bag-3',roast_date:'2026-09-20'}),{score:null,count:0})

// Actual active-day gaps replace the arbitrary position in a five-shot list.
const close=[shot('old','2026-09-08',1),shot('new','2026-09-09',5)]
const apart=[close[0],shot('new','2026-09-22',5)]
assert.ok(Number(coffeeScore(apart,coffee).score)>Number(coffeeScore(close,coffee).score))
assert.equal(coffeeScore(apart,coffee).score,'3.9') // 14 active days => half weight.
const sameDay=[shot('a','2026-09-12',1),shot('b','2026-09-12',5)]
assert.deepEqual(coffeeScore(sameDay,coffee),coffeeScore([...sameDay].reverse(),coffee))

// Smooth freshness weights on either side of the app's estimated window.
const early=coffeeScore([shot('early','2026-09-03',5),shot('optimal','2026-09-12',3)],coffee)
assert.ok(Number(early.score)<Number(coffeeScore([shot('ready','2026-09-11',5),shot('optimal','2026-09-12',3)],coffee).score))
const boundaryScore=date=>Number(coffeeScore([shot('first',date,5),shot('second','2026-09-12',3)],coffee).score)
assert.ok(Math.abs(boundaryScore('2026-09-07')-boundaryScore('2026-09-08'))<=.2)

// Useful older evidence stays in the score; one high rating has no fixed bonus.
const history=Array.from({length:10},(_,i)=>shot('steady-'+i,'2026-09-12',3))
assert.deepEqual(coffeeScore([...history,shot('lucky','2026-09-12',5)],coffee),{score:'3.2',count:11})
assert.deepEqual(coffeeScore([shot('only','2026-09-12',2)],coffee),{score:'2.0',count:1})
const excluded=[...['adjust','bad','choked'].map(outcome=>shot(outcome,'2026-09-13',1,outcome)),{...shot('blocked','2026-09-13',1),choked:true},shot('unrated','2026-09-13',null),shot('nan','2026-09-13',NaN),shot('range','2026-09-13',6)]
assert.deepEqual(coffeeScore([...history,...excluded],coffee),coffeeScore(history,coffee))

const frozen={id:'frozen',roast_date:'2026-09-01',freeze_date:'2026-09-05'}
const thawed={id:'portion',source_coffee_id:'frozen',roast_date:'2026-09-01',freeze_date:'2026-09-05',thaw_date:'2026-10-01',portion_g:125}
assert.equal(coffeeAgeDays(frozen,'2026-10-10'),4)
assert.equal(coffeeAgeDays(thawed,'2026-10-10'),13)
assert.equal(coffeeAgeDays({...frozen,bag_g:1000,frozen_g:875},'2026-10-10'),39)
assert.equal(coffeeAgeDays({...frozen,bag_g:1000,frozen_g:1000},'2026-10-10'),4)
assert.equal(coffeeAgeDays({...coffee,roast_date:'27 August 2026'},'2026-09-01'),5)
assert.equal(coffeeAgeDays({...coffee,roast_date:null},'2026-09-01'),null)
const frozenShots=[shot('before-freeze','2026-09-03',4,'good','logged','frozen'),shot('after-thaw','2026-10-10',5,'good','logged','portion')]
assert.equal(coffeeScore(frozenShots,frozen,[frozen,thawed]).count,2)
assert.deepEqual(coffeeScore(frozenShots,thawed,[frozen,thawed]),coffeeScore(frozenShots,frozen,[frozen,thawed]))
assert.deepEqual(coffeeScore(frozenShots,frozen,[frozen,thawed]),coffeeScore([shot('early','2026-09-03',4),shot('ready','2026-09-14',5)],coffee))

// Extending frozen storage changes neither effective age nor evidence weights.
const laterThaw={...thawed,thaw_date:'2027-04-01'}
assert.deepEqual(coffeeScore([frozenShots[0],{...frozenShots[1],date:'2027-04-10'}],frozen,[frozen,laterThaw]),coffeeScore(frozenShots,frozen,[frozen,thawed]))

// A fresh new batch resets the age reference; stale earlier batches lose weight.
const batch2={...thawed,id:'portion-2',thaw_date:'2026-12-01'}
const batches=[frozen,thawed,batch2]
const batchShots=[shot('first','2026-10-10',1,'good','logged','portion'),shot('second','2026-12-10',5,'good','logged','portion-2')]
assert.equal(coffeeScore(batchShots,batch2,batches).score,coffeeScore(sameDay,coffee).score)
assert.ok(Number(coffeeScore([{...batchShots[0],date:'2026-11-10'},batchShots[1]],batch2,batches).score)>Number(coffeeScore(batchShots,batch2,batches).score))
const repurchase={...frozen,id:'repurchase',bean_id:'same-bean'}
assert.deepEqual(coffeeScore(batchShots,repurchase,[...batches,repurchase]),{score:null,count:0})

// Missing dates do not crash or invent ages; extreme ages remain finite.
assert.equal(coffeeScore(sameDay,{...coffee,roast_date:''}).score,coffeeScore(sameDay,coffee).score)
assert.deepEqual(coffeeScore([shot('undated','',4)],coffee),{score:'4.0',count:1})
assert.deepEqual(coffeeScore([shot('old','2099-01-01',4)],coffee),{score:'4.0',count:1})
console.log('Coffee score: active-day weighting, frozen-time invariance, batch reset, supported peaks, and bag isolation passed.')
