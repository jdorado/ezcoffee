// AIFit's raw-text CLI sidecar, reduced to the local single-user coffee app.
import http from 'node:http';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {buildCodexArgs,parseCodexJsonl} from './codex.mjs';
const workspace=process.env.WORKSPACE_DIR||fileURLToPath(new URL('./workspace',import.meta.url));
const port=Number(process.env.AI_PORT||8102);
function run(message,sessionId,token){return new Promise((resolve,reject)=>{
 const args=buildCodexArgs({},sessionId);
 const child=spawn(process.env.CODEX_BIN||'codex',args,{cwd:workspace,env:{...process.env,COFFEE_TOKEN:token,COFFEE_API_URL:process.env.COFFEE_API_URL||'http://127.0.0.1:8001'},stdio:['pipe','pipe','pipe']});
 let out='',err='',bytes=0;
 const timer=setTimeout(()=>{child.kill('SIGKILL');reject(new Error('Chat timed out. Check saved shots before retrying.'));},280000);
 child.stdout.on('data',chunk=>{bytes+=chunk.length;if(bytes>2*1024*1024){child.kill('SIGKILL');return;}out+=chunk;});
 child.stderr.on('data',chunk=>{err=(err+chunk).slice(-12000);});
 child.on('error',error=>{clearTimeout(timer);reject(error);});
 child.on('close',code=>{clearTimeout(timer);try{if(code!==0)throw new Error(err||'Codex failed');resolve(parseCodexJsonl(out,sessionId));}catch(e){reject(e);}});
 child.stdin.end(message);
});}
let busy=false;
http.createServer(async(req,res)=>{
 if(req.method==='GET'&&req.url==='/health'){res.end('ok');return;}
 if(req.method!=='POST'||req.url!=='/message'){res.writeHead(404).end();return;}
 if(busy){res.writeHead(409).end('Chat is busy');return;}
 busy=true;
 const started=performance.now();
 const timing={event:"coffee_chat",resumed:Boolean(req.headers["x-agent-session-id"]),status:"error"};
 try{
  let body='';for await(const chunk of req){body+=chunk;if(body.length>64000)throw new Error('Message too large');}
  const token=req.headers['x-coffee-token'];if(!token)throw new Error('Missing job capability');
  const check=await fetch((process.env.COFFEE_API_URL||'http://127.0.0.1:8001')+'/agent/context?auth_only=true',{headers:{'X-Coffee-Token':token}});if(!check.ok)throw new Error('Invalid job capability');
  timing.authorization_ms=Math.round(performance.now()-started);
  timing.prompt_bytes=Buffer.byteLength(body);
  const inferenceStarted=performance.now();
  const result=await run(body,req.headers['x-agent-session-id']||null,token);
  timing.inference_ms=Math.round(performance.now()-inferenceStarted);
  timing.status="complete";
  res.writeHead(200,{'Content-Type':'text/plain; charset=utf-8','X-Agent-Session-Id':result.sessionId});res.end(result.answer);
 }catch(error){console.error(error.message);res.writeHead(502).end('Coffee chat failed. Check the AI service log.');}finally{timing.total_ms=Math.round(performance.now()-started);console.log(JSON.stringify(timing));busy=false;}
}).listen(port,process.env.AI_HOST||'127.0.0.1',()=>console.log(`Coffee AI on ${port}`));
