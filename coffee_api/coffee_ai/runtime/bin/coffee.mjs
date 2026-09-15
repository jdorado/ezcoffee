#!/usr/bin/env node
// The same protected read/write gateway pattern as AIFit's runtime client.
const [action,file]=process.argv.slice(2);
if(!['read','save'].includes(action))throw new Error('Usage: node ../runtime/bin/coffee.mjs read | save payload.json');
let options={headers:{'X-Coffee-Token':process.env.COFFEE_TOKEN}};
if(action==='save'){
 const {readFile}=await import('node:fs/promises');
 options={...options,method:'POST',headers:{...options.headers,'Content-Type':'application/json'},body:await readFile(file,'utf8')};
}
const response=await fetch(`${process.env.COFFEE_API_URL}/agent/${action==='read'?'context':'save'}`,options);
const result=await response.text();if(!response.ok)throw new Error(result);console.log(result);
