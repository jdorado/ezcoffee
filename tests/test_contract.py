import asyncio, os, sys, unittest, uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
os.environ['APP_MODE']='personal'
os.environ['COFFEE_AI_ENABLED']='true'
os.environ['COFFEE_AI_BACKEND']='codex'
os.environ['COFFEE_REQUIRE_AUTH']='true'
os.environ['COFFEE_OWNER_SUB']='test-owner'
os.environ['PRIVY_APP_ID']='test-app'
os.environ['PRIVY_APP_SECRET']='test-secret'
os.environ['MONGO_URL']=os.getenv('TEST_MONGO_URL','mongodb://127.0.0.1:27019')
os.environ['MONGO_DB']='coffee_test_'+uuid.uuid4().hex[:24]
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'coffee_api'))
from fastapi.testclient import TestClient
from src.main import app, client

class CoffeeContract(unittest.TestCase):
 def test_chat_includes_fresh_manual_shots(self):
  import json
  from src.main import chat_prompt
  coffee=self.http.post('/coffees',json={'name':'Chat snapshot test'}).json()
  rows=[self.http.post('/shots',json={'coffee_id':coffee['id'],'date':f'2026-09-{day:02}','rating':4}).json() for day in range(1,7)]
  self.http.delete('/shots/'+rows[-1]['id']+'?revision=1')
  plan=self.http.post('/shots',json={'coffee_id':coffee['id'],'status':'planned','date':'2026-09-09'}).json()
  payload=json.loads(self.http.portal.call(chat_prompt,{'account_id':'test-owner','id':'test','message':'That shot was nice','coffee_id':coffee['id']}))
  recent=payload['current_records']['recent_logged_shots']
  self.assertEqual([s['id'] for s in recent],[s['id'] for s in rows[1:5]][::-1])
  self.assertEqual(recent[0]['rating'],4)
  self.assertEqual(recent[0]['revision'],1)
  self.assertEqual(payload['current_records']['selected_coffee']['name'],'Chat snapshot test')
  self.assertIn('profile',payload['current_records'])
  self.assertNotIn(plan['id'],[s['id'] for s in recent])
  self.assertEqual(payload['current_records']['planned_next_shot']['id'],plan['id'])
  self.assertEqual(payload['current_records']['planned_next_shot']['status'],'planned')
  self.http.delete('/coffees/'+coffee['id']+'?revision=1')
 def test_timestamp_and_taste_survive_edits(self):
  c=self.http.post('/coffees',json={'name':'Timestamp test'}).json()
  first=self.http.post('/shots',json={'coffee_id':c['id'],'date':'2026-09-09','taste_balance':'slightly_sour','choked':False,'rating':4}).json()
  second=self.http.post('/shots',json={'coffee_id':c['id'],'date':'2026-09-09','taste_balance':'bitter','choked':True}).json()
  self.assertTrue(first['recorded_at'])
  edited=self.http.put('/shots/'+first['id'],json={'coffee_id':c['id'],'revision':first['revision'],'taste':'updated note'}).json()
  self.assertEqual(edited['recorded_at'],first['recorded_at'])
  self.assertEqual(edited['taste_balance'],'slightly_sour')
  self.assertEqual(edited['rating'],4)
  for invalid in [0,6,1.5,True]:
   self.assertEqual(self.http.post('/shots',json={'coffee_id':c['id'],'rating':invalid}).status_code,422)
  cleared=self.http.put('/shots/'+first['id'],json={'coffee_id':c['id'],'revision':edited['revision'],'rating':None}).json()
  self.assertIsNone(cleared['rating'])
  rows=[s['id'] for s in self.http.get('/state').json()['shots'] if s['coffee_id']==c['id']]
  self.assertEqual(rows,[second['id'],first['id']])
  self.assertEqual(self.http.post('/shots',json={'coffee_id':c['id'],'taste_balance':'too coarse'}).status_code,422)
 @classmethod
 def setUpClass(cls):
  from unittest.mock import AsyncMock
  from types import SimpleNamespace
  import src.main
  cls.original_verifier=src.main.verify_privy_access_token
  src.main.verify_privy_access_token=AsyncMock(return_value=SimpleNamespace(user_id='test-owner'))
  cls.context=TestClient(app);cls.http=cls.context.__enter__()
  cls.http.headers.update({'Authorization':'Bearer test'})
  # Public repositories ship no personal seed data; contract fixtures are isolated here.
  from pymongo import MongoClient
  database=MongoClient(os.getenv('MONGO_URL','mongodb://127.0.0.1:27019'))[os.environ['MONGO_DB']]
  database.coffees.insert_many([{'account_id':'test-owner','id':f'coffee-{index}','name':f'Test coffee {index}','roast_date':'','notes':'','tag_color':'','archived':False,'revision':1} for index in range(1,7)])
  database.shots.insert_many([{'account_id':'test-owner','id':f'import-{index}','coffee_id':'coffee-1','revision':1,'date':f'2026-09-0{index+2}','status':'planned','source':'test fixture'} for index in range(1,6)])
  database.client.close()
 @classmethod
 def tearDownClass(cls):
  # Only this test's random database is removed.
  from pymongo import MongoClient
  with MongoClient(os.getenv('MONGO_URL','mongodb://127.0.0.1:27019')) as mongo:
   mongo.drop_database(os.environ['MONGO_DB'])
  cls.context.__exit__(None,None,None)
  import src.main
  src.main.verify_privy_access_token=cls.original_verifier
 def test_seed_preserves_plans_and_chronological_dates(self):
  state=self.http.get('/state').json()
  self.assertEqual(len([c for c in state['coffees'] if c['id'].startswith('coffee-')]),6)
  self.assertEqual(sum(x['status']=='planned' for x in state['shots'] if x['id'].startswith('import-')),5)
  imported=[x for x in state['shots'] if x['id'].startswith('import-')]
  self.assertTrue(all(x['date'] for x in imported))
  self.assertLess(next(x['date'] for x in imported if x['id']=='import-1'),next(x['date'] for x in imported if x['id']=='import-2'))
 def test_revision_conflict_and_readback(self):
  coffee=self.http.post('/coffees',json={'name':'Contract test'}).json()
  shot=self.http.post('/shots',json={'coffee_id':coffee['id'],'dose':14,'taste':'original'}).json()
  updated=self.http.put('/shots/'+shot['id'],json={**shot,'taste':'sweet'})
  self.assertEqual(updated.status_code,200)
  stale=self.http.put('/shots/'+shot['id'],json={**shot,'taste':'stale'})
  self.assertEqual(stale.status_code,409)
  state=self.http.get('/state').json()
  self.assertEqual(next(s for s in state['shots'] if s['id']==shot['id'])['taste'],'sweet')
 def test_targets_outcomes_and_legacy_updates(self):
  shot=self.http.post('/shots',json={'coffee_id':'coffee-1','status':'planned','target_yield_g':24,'target_yield_max_g':26}).json()
  self.assertIsNone(shot['yield_g'])
  self.assertEqual(shot['outcome'],'unrated')
  self.assertFalse(shot['locked'])
  logged=self.http.put('/shots/'+shot['id'],json={**shot,'status':'logged','stop_yield_g':25,'yield_g':25.2,'outcome':'good'}).json()
  self.assertEqual(logged['target_yield_max_g'],26)
  self.assertEqual(logged['stop_yield_g'],25)
  self.assertEqual(logged['yield_g'],25.2)
  legacy={k:v for k,v in logged.items() if k not in ['target_yield_g','target_yield_max_g','outcome']}
  updated=self.http.put('/shots/'+shot['id'],json={**legacy,'taste':'sweet'}).json()
  self.assertEqual(updated['outcome'],'good')
  self.assertEqual(updated['stop_yield_g'],25)
  self.assertEqual(updated['target_yield_g'],24)
  locked=self.http.put('/shots/'+shot['id'],json={'coffee_id':'coffee-1','revision':updated['revision'],'locked':True}).json()
  self.assertTrue(locked['locked'])
  self.assertEqual(locked['outcome'],'good')
  self.assertEqual(updated['target_yield_max_g'],26)
  self.assertEqual(self.http.put('/shots/'+shot['id'],json={'coffee_id':'coffee-1','revision':locked['revision'],'target_yield_g':30}).status_code,422)
  self.assertEqual(self.http.put('/shots/'+shot['id'],json={**logged,'outcome':'bad'}).status_code,409)
  for fields in [{'outcome':'green'},{'target_yield_g':30,'target_yield_max_g':20},{'target_yield_max_g':26},{'target_yield_g':0},{'stop_yield_g':-1}]:
   self.assertEqual(self.http.post('/shots',json={'coffee_id':'coffee-1',**fields}).status_code,422)
 def test_invalid_coffee_and_measurement(self):
  self.assertEqual(self.http.post('/shots',json={'coffee_id':'missing'}).status_code,404)
  self.assertEqual(self.http.post('/shots',json={'coffee_id':'coffee-1','dose':-1}).status_code,422)
  self.assertEqual(self.http.post('/shots',json={'coffee_id':'coffee-1','dose':123}).status_code,200)
  self.assertEqual(self.http.post('/shots',json={'coffee_id':'coffee-1','dose':1001}).status_code,422)
 def test_profile_and_pour_over_fields_are_revisioned(self):
  default=self.http.get('/profile').json()
  self.assertEqual(default['brew_method'],'espresso')
  fields=['water_temp_c','water_g','ice_g','dose','ratio','grind','seconds','bloom_seconds','taste']
  saved=self.http.put('/profile',json={'brew_method':'filter','equipment_preset':'standard_pour_over','equipment_name':'V60','tracked_fields':fields,'revision':default['revision']})
  self.assertEqual(saved.status_code,200)
  current=saved.json()
  self.assertEqual(self.http.get('/state').json()['profile']['tracked_fields'],fields)
  self.assertEqual(self.http.put('/profile',json={**default,'equipment_name':'stale'}).status_code,409)
  self.assertEqual(self.http.put('/profile',json={**current,'tracked_fields':['dose','dose']}).status_code,422)
  coffee=self.http.post('/coffees',json={'name':'Pour-over test','brand':'Friend Roasters'}).json()
  brew=self.http.post('/shots',json={'coffee_id':coffee['id'],'water_temp_c':93,'water_g':250,'ice_g':0,'dose':15,'grind':'medium-fine','seconds':180,'bloom_seconds':40}).json()
  self.assertEqual(brew['water_g'],250)
  self.assertEqual(brew['bloom_seconds'],40)
  self.assertEqual(coffee['brand'],'Friend Roasters')
  self.assertEqual(self.http.post('/shots',json={'coffee_id':coffee['id'],'water_temp_c':101}).status_code,422)
  self.assertEqual(self.http.put('/profile',json={**default,'revision':current['revision']}).status_code,200)
 def test_archived_coffee_keeps_history_for_chat_but_cannot_receive_shots(self):
  import json
  from src.main import chat_prompt
  coffee=self.http.post('/coffees',json={'name':'Archive test'}).json()
  shot=self.http.post('/shots',json={'coffee_id':coffee['id'],'taste':'favorite'}).json()
  archived=self.http.put('/coffees/'+coffee['id'],json={**coffee,'archived':True}).json()
  self.assertTrue(archived['archived'])
  self.assertTrue(next(c for c in self.http.get('/state').json()['coffees'] if c['id']==coffee['id'])['archived'])
  self.assertEqual(self.http.post('/shots',json={'coffee_id':coffee['id']}).status_code,404)
  payload=json.loads(self.http.portal.call(chat_prompt,{'account_id':'test-owner','id':'archive-test','message':'What should I buy next?','coffee_id':None}))
  self.assertTrue(next(row for row in payload['current_records']['coffee_catalog'] if row['id']==coffee['id'])['archived'])
  restored=self.http.put('/coffees/'+coffee['id'],json={**archived,'archived':False}).json()
  self.assertFalse(restored['archived'])
  self.assertEqual(self.http.post('/shots',json={'coffee_id':coffee['id']}).status_code,200)
 def test_dated_shots_are_returned_newest_first_before_unknown_dates(self):
  older=self.http.post('/shots',json={'coffee_id':'coffee-1','date':'2026-09-01','dose':14}).json()
  newer=self.http.post('/shots',json={'coffee_id':'coffee-1','date':'2026-09-08T10:00:00+00:00','dose':14}).json()
  rows=self.http.get('/state').json()['shots']
  ids=[row['id'] for row in rows]
  self.assertLess(ids.index(newer['id']),ids.index(older['id']))
  self.assertLess(ids.index(newer['id']),ids.index('import-5'))
  self.assertLess(ids.index('import-5'),ids.index(older['id']))
 def test_gateway_returns_and_records_canonical_receipt(self):
  from pymongo import MongoClient
  database=MongoClient(os.getenv('MONGO_URL','mongodb://127.0.0.1:27019'))[os.environ['MONGO_DB']]
  database.jobs.insert_one({'account_id':'test-owner','id':'gateway-test','token':'test-only','status':'running','shot_date':'2026-09-08','receipts':[]})
  response=self.http.post('/agent/save',headers={'X-Coffee-Token':'test-only'},json={'kind':'shot','data':{'coffee_id':'coffee-1','dose':14,'taste':'test only','outcome':'choked','target_yield_g':30}})
  self.assertEqual(response.status_code,200)
  row=response.json()
  receipt=database.jobs.find_one({'account_id':'test-owner','id':'gateway-test'})['receipts'][0]
  self.assertEqual(receipt['record'],row)
  self.assertEqual(row['outcome'],'choked')
  self.assertEqual(row['target_yield_g'],30)
  self.assertEqual(row['date'],'2026-09-08')
  self.assertEqual(database.shots.find_one({'account_id':'test-owner','id':row['id']})['taste'],'test only')
  database.jobs.update_one({'account_id':'test-owner','id':'gateway-test'},{'$set':{'status':'complete'}})
  database.client.close()
 def test_production_rejects_anonymous_and_other_accounts(self):
  from unittest.mock import patch, AsyncMock
  from types import SimpleNamespace
  with patch('src.main.REQUIRE_AUTH',True),patch('src.main.OWNER_SUB','owner'):
   self.assertEqual(self.http.get('/state',headers={'Authorization':''}).status_code,401)
   self.assertEqual(self.http.post('/chat',headers={'Authorization':''},json={'id':'unauthorized','message':'test'}).status_code,401)
   with patch('src.main.verify_privy_access_token',AsyncMock(return_value=SimpleNamespace(user_id='other'))):
    self.assertEqual(self.http.get('/state',headers={'Authorization':'Bearer test'}).status_code,403)
   with patch('src.main.verify_privy_access_token',AsyncMock(return_value=SimpleNamespace(user_id='owner'))):
    self.assertEqual(self.http.get('/state',headers={'Authorization':'Bearer test'}).status_code,200)
 def test_openrouter_chat_uses_bounded_account_context(self):
  import json
  from pymongo import MongoClient
  from unittest.mock import AsyncMock, patch
  from src.main import run_chat
  from src.services.openrouter import OpenRouterReply
  database=MongoClient(os.getenv('MONGO_URL','mongodb://127.0.0.1:27019'))[os.environ['MONGO_DB']]
  job={'account_id':'test-owner','id':'openrouter-contract','message':'What should I change next?','coffee_id':'coffee-1','shot_date':'2026-09-15','status':'queued','created_at':'2026-09-15T00:00:00+00:00','receipts':[]}
  database.jobs.insert_one(job)
  database.messages.insert_one({'account_id':'test-owner','id':job['id']+'-user','role':'user','text':job['message']})
  reply=AsyncMock(return_value=OpenRouterReply(text='Try one small grind adjustment.',actions=[]))
  with patch('src.main.AI_BACKEND','openrouter'),patch('src.main.openrouter_reply',reply):
   self.http.portal.call(run_chat,job)
  prompt,history=reply.await_args.args
  context=json.loads(prompt)
  self.assertEqual(context['current_records']['selected_coffee']['id'],'coffee-1')
  self.assertNotIn('account_id',prompt)
  self.assertLessEqual(len(history),2)
  saved=database.messages.find_one({'account_id':'test-owner','id':job['id']+'-assistant'})
  self.assertEqual(saved['text'],'Try one small grind adjustment.')
  self.assertEqual(database.jobs.find_one({'account_id':'test-owner','id':job['id']})['status'],'complete')
  database.client.close()
 def test_fast_next_shot_uses_ten_logged_shots_and_replaces_the_plan(self):
  from unittest.mock import AsyncMock, patch
  roast_date=(datetime.now(timezone.utc).date()-timedelta(days=7)).isoformat()
  coffee=self.http.post('/coffees',json={'name':'Triage test','roast_date':roast_date}).json()
  for index in range(12):
   self.http.post('/shots',json={'coffee_id':coffee['id'],'date':f'2026-08-{index+1:02}','dose':18,'grind':'5.0','stop_yield_g':35,'yield_g':36,'water_temp_c':93,'temp':'I','taste':'sour','taste_balance':'sour','outcome':'adjust'})
  choice=AsyncMock(return_value=('finer',.84,'jev-test'))
  with patch('src.main.TYPESAFE_ENABLED',True),patch('src.main.typesafe_choice',choice):
   response=self.http.post('/recommendations/next-shot',json={'coffee_id':coffee['id'],'guidance':'Make it sweeter today.','paper':'no'})
  self.assertEqual(response.status_code,200)
  result=response.json()
  self.assertEqual(result['shots_considered'],10)
  self.assertEqual(result['plan']['grind'],'4.9')
  self.assertEqual(result['plan']['target_yield_g'],35)
  self.assertEqual(result['plan']['target_yield_max_g'],36)
  self.assertEqual(result['plan']['status'],'planned')
  self.assertEqual(result['plan']['paper'],'no')
  self.assertEqual(result['plan']['temp'],'I')
  self.assertIsNone(result['plan']['yield_g'])
  self.assertEqual(len(choice.await_args.args[0]['shots']),10)
  self.assertEqual(choice.await_args.args[0]['owner_guidance'],'Make it sweeter today.')
  self.assertEqual(choice.await_args.args[0]['coffee']['roast_age_days'],7)
  self.assertEqual(choice.await_args.args[0]['coffee']['days_left_in_28_day_window'],21)
  self.assertEqual(choice.await_args.args[0]['recipe_constraints'],{'paper':'no'})
  self.assertTrue(all(candidate['plan']['paper']=='no' for candidate in choice.await_args.args[1].values()))
  self.assertEqual(choice.await_args.args[1]['pid_0']['plan']['temp'],'0')
  self.assertEqual(choice.await_args.args[1]['pid_II']['plan']['temp'],'II')
  state=self.http.get('/state').json()
  plans=[s for s in state['shots'] if s['coffee_id']==coffee['id'] and s['status']=='planned']
  self.assertEqual(len(plans),1)
  first_id=plans[0]['id']
  with patch('src.main.TYPESAFE_ENABLED',True),patch('src.main.typesafe_choice',choice):
   replaced=self.http.post('/recommendations/next-shot',json={'coffee_id':coffee['id']}).json()['plan']
  self.assertEqual(replaced['id'],first_id)
  self.assertEqual(replaced['revision'],2)
  self.assertEqual(len([s for s in self.http.get('/state').json()['shots'] if s['coffee_id']==coffee['id'] and s['status']=='planned']),1)
  profile_without_paper=AsyncMock(return_value={'tracked_fields':['dose','grind','temp']})
  choice.reset_mock()
  with patch('src.main.TYPESAFE_ENABLED',True),patch('src.main.typesafe_choice',choice),patch('src.main.read_profile',profile_without_paper):
   self.http.post('/recommendations/next-shot',json={'coffee_id':coffee['id'],'paper':'yes'})
  self.assertEqual(choice.await_args.args[0]['recipe_constraints'],{})
  self.assertTrue(all(candidate['plan']['paper']=='unknown' for candidate in choice.await_args.args[1].values()))
 def test_openrouter_actions_use_canonical_account_scoped_writes(self):
  from fastapi import HTTPException
  from pymongo import MongoClient
  from src.main import apply_inference_action
  database=MongoClient(os.getenv('MONGO_URL','mongodb://127.0.0.1:27019'))[os.environ['MONGO_DB']]
  job={'account_id':'test-owner','id':'openrouter-write','shot_date':'2026-09-15'}
  database.jobs.insert_one({**job,'status':'running','receipts':[]})
  coffee=self.http.portal.call(apply_inference_action,job,{'kind':'coffee','id':None,'data':{'name':'AI coffee','brand':'Test roaster'}})
  updated_coffee=self.http.portal.call(apply_inference_action,job,{'kind':'coffee','id':coffee['id'],'data':{'revision':coffee['revision'],'name':'Updated AI coffee'}})
  self.assertEqual(updated_coffee['brand'],'Test roaster')
  row=self.http.portal.call(apply_inference_action,job,{'kind':'shot','id':None,'data':{'coffee_id':'coffee-1','dose':14,'taste':'sweet'}})
  self.assertEqual(row['date'],'2026-09-15')
  self.assertEqual(database.shots.find_one({'account_id':'test-owner','id':row['id']})['taste'],'sweet')
  updated=self.http.portal.call(apply_inference_action,job,{'kind':'shot','id':row['id'],'data':{'revision':row['revision'],'taste':'sweeter'}})
  self.assertEqual(updated['dose'],14)
  self.assertEqual(updated['taste'],'sweeter')
  with self.assertRaises(HTTPException):
   self.http.portal.call(apply_inference_action,job,{'kind':'shot','id':row['id'],'data':{'coffee_id':'coffee-1','revision':0,'taste':'stale'}})
  database.coffees.insert_one({'account_id':'another-account','id':'private-coffee','name':'Private','revision':1})
  with self.assertRaises(HTTPException):
   self.http.portal.call(apply_inference_action,job,{'kind':'coffee','id':'private-coffee','data':{'revision':1,'name':'Stolen'}})
  receipts=database.jobs.find_one({'account_id':'test-owner','id':job['id']})['receipts']
  self.assertEqual([receipt['kind'] for receipt in receipts],['coffee','coffee','shot','shot'])
  database.client.close()
 def test_hosted_accounts_are_isolated(self):
  from unittest.mock import patch
  from types import SimpleNamespace
  async def verify(token): return SimpleNamespace(user_id=token)
  headers_a={'Authorization':'Bearer user-a'}
  headers_b={'Authorization':'Bearer user-b'}
  with patch('src.main.APP_MODE','hosted'),patch('src.main.verify_privy_access_token',verify):
   coffee=self.http.post('/coffees',headers=headers_a,json={'name':'Only A'}).json()
   shot=self.http.post('/shots',headers=headers_a,json={'coffee_id':coffee['id'],'dose':18}).json()
   saved=self.http.put('/profile',headers=headers_a,json={'brew_method':'filter','equipment_preset':'standard_pour_over','equipment_name':'A brewer','tracked_fields':['dose','water_g'],'revision':0})
   self.assertEqual(saved.status_code,200)
   state_b=self.http.get('/state',headers=headers_b).json()
   self.assertFalse(any(row['id']==coffee['id'] for row in state_b['coffees']))
   self.assertFalse(any(row['id']==shot['id'] for row in state_b['shots']))
   self.assertEqual(state_b['profile']['equipment_name'],'')
   self.assertEqual(self.http.put('/coffees/'+coffee['id'],headers=headers_b,json={**coffee,'revision':coffee['revision'],'name':'Stolen'}).status_code,409)
   self.assertEqual(self.http.delete('/shots/'+shot['id']+'?revision=1',headers=headers_b).status_code,409)
   self.assertEqual(self.http.post('/shots',headers=headers_b,json={'coffee_id':coffee['id'],'dose':18}).status_code,404)
   state_a=self.http.get('/state',headers=headers_a).json()
   self.assertEqual(next(row for row in state_a['coffees'] if row['id']==coffee['id'])['name'],'Only A')
   self.assertTrue(any(row['id']==shot['id'] for row in state_a['shots']))
 def test_gateway_requires_live_job(self):
  self.assertEqual(self.http.get('/agent/context',headers={'X-Coffee-Token':'bad'}).status_code,403)
  self.assertEqual(self.http.post('/agent/save',headers={'X-Coffee-Token':'bad'},json={'kind':'coffee','data':{'name':'blocked'}}).status_code,403)
 def test_selfhost_profile_exposes_shots_without_chat(self):
  from unittest.mock import patch
  with patch('src.main.AI_ENABLED',False),patch('src.main.REQUIRE_AUTH',False):
   state=self.http.get('/state').json()
   self.assertEqual(state['messages'],[])
   self.assertIsNone(state['active_job'])
   self.assertEqual(state['capabilities'],{'chat':False,'next_shot':False,'auth':False,'app_mode':'personal'})
   self.assertEqual(self.http.post('/chat',json={'id':'disabled','message':'test'}).status_code,404)
   self.assertEqual(self.http.get('/agent/context',headers={'X-Coffee-Token':'bad'}).status_code,404)
 def test_delete_revision_and_coffee_history(self):
  coffee=self.http.post('/coffees',json={'name':'Deletion test'}).json()
  shot=self.http.post('/shots',json={'coffee_id':coffee['id'],'dose':14}).json()
  self.assertEqual(self.http.delete('/shots/'+shot['id']+'?revision=99').status_code,409)
  self.assertEqual(self.http.delete('/shots/'+shot['id']+'?revision=1').status_code,200)
  self.assertEqual(self.http.put('/shots/'+shot['id'],json={**shot,'revision':2,'taste':'resurrect'}).status_code,409)
  other=self.http.post('/shots',json={'coffee_id':coffee['id'],'dose':14}).json()
  self.assertEqual(self.http.delete('/coffees/'+coffee['id']+'?revision=1').status_code,200)
  state=self.http.get('/state').json()
  self.assertFalse(any(c['id']==coffee['id'] for c in state['coffees']))
  self.assertFalse(any(s['coffee_id']==coffee['id'] for s in state['shots']))
  self.assertEqual(self.http.post('/shots',json={'coffee_id':coffee['id']}).status_code,404)
  from unittest.mock import patch
  with patch('src.main.REQUIRE_AUTH',True),patch('src.main.OWNER_SUB','owner'):
   self.assertEqual(self.http.delete('/shots/'+other['id']+'?revision=1',headers={'Authorization':''}).status_code,401)

if __name__=='__main__':unittest.main()
