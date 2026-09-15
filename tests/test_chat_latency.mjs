import assert from 'node:assert/strict';
import test from 'node:test';
import {buildCodexArgs} from '../coffee_api/coffee_ai/codex.mjs';
test('compaction preserves native resume and handles invalid settings',()=>{
 const before=process.env.CODEX_AUTO_COMPACT_TOKEN_LIMIT;
 try{
  for(const [value,expected] of [['',32000],['64000',64000],['invalid',32000],['-1',32000]]){
   process.env.CODEX_AUTO_COMPACT_TOKEN_LIMIT=value;
   const args=buildCodexArgs({},'existing-session');
   assert.ok(args.includes(`model_auto_compact_token_limit=${expected}`));
   assert.deepEqual(args.slice(-3),['resume','existing-session','-']);
   assert.ok(!args.includes('--ephemeral'));
  }
 }finally{if(before===undefined)delete process.env.CODEX_AUTO_COMPACT_TOKEN_LIMIT;else process.env.CODEX_AUTO_COMPACT_TOKEN_LIMIT=before;}
});
