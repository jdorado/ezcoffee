import asyncio, os, sys, unittest, uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
os.environ['APP_MODE']='personal'
os.environ['COFFEE_AI_ENABLED']='true'
os.environ['OPENROUTER_API_KEY']='test-key'
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
  self.assertEqual([s['id'] for s in recent],[s['id'] for s in rows[:-1]][::-1])
  self.assertEqual(recent[0]['rating'],4)
  self.assertEqual(recent[0]['revision'],1)
  self.assertEqual(payload['current_records']['selected_coffee']['name'],'Chat snapshot test')
  self.assertIn('profile',payload['current_records'])
  self.assertNotIn(plan['id'],[s['id'] for s in recent])
  self.assertEqual(payload['current_records']['planned_next_shot']['id'],plan['id'])
  self.assertEqual(payload['current_records']['planned_next_shot']['status'],'planned')
  self.assertIn('always update that same planned record',payload['record_guidance'])
  self.assertIn('even when the owner asked only for advice',payload['record_guidance'])
  self.http.delete('/coffees/'+coffee['id']+'?revision=1')
 def test_chat_context_answers_which_coffee_last_shots_and_best_settings(self):
  import json
  from src.main import chat_prompt
  ethiopia=self.http.post('/coffees',json={'name':'Smoke Ethiopia','brand':'Test Roaster','roast_date':'2026-09-10','notes':'Washed Yirgacheffe, floral and sweet.'}).json()
  brazil=self.http.post('/coffees',json={'name':'Smoke Brazil','brand':'Test Roaster','roast_date':'2026-08-01','notes':'Natural, nutty and heavy.'}).json()
  ratings=[3,4,5,4,5]
  shots=[self.http.post('/shots',json={'coffee_id':ethiopia['id'],'date':f'2026-09-{day:02}','dose':18,'grind':'5.0','yield_g':36,'temp':'I','rating':rating,'taste':'shot note'}).json() for day,rating in zip(range(1,6),ratings)]
  locked=self.http.put('/shots/'+shots[-1]['id'],json={'coffee_id':ethiopia['id'],'revision':shots[-1]['revision'],'locked':True}).json()
  self.assertTrue(locked['locked'])
  for day in (6,7):
   self.http.post('/shots',json={'coffee_id':brazil['id'],'date':f'2026-09-{day:02}','dose':18,'grind':'6.0','yield_g':36,'rating':2})
  retired=self.http.post('/coffees',json={'name':'Smoke Retired'}).json()
  gem=self.http.post('/shots',json={'coffee_id':retired['id'],'date':'2026-08-20','dose':18,'grind':'4.5','yield_g':37,'rating':5,'taste':'retired gem'}).json()
  retired_archived=self.http.put('/coffees/'+retired['id'],json={**retired,'archived':True}).json()
  payload=json.loads(self.http.portal.call(chat_prompt,{'account_id':'test-owner','id':'smoke','message':'Which coffee next?','coffee_id':ethiopia['id']}))
  records=payload['current_records']
  # Archived beans leave the catalog but lend their best shots as reference.
  self.assertFalse(any(c['id']==retired['id'] for c in records['coffee_catalog']))
  self.assertFalse(any(c['id']==retired['id'] for c in records['coffee_overview']))
  reference=records['reference_shots']
  self.assertLessEqual(len(reference),15)
  gem_ref=next(r for r in reference if r['coffee']=='Smoke Retired')
  self.assertTrue(gem_ref['archived'])
  self.assertEqual((gem_ref['grind'],gem_ref['yield_g'],gem_ref['rating']),( '4.5',37,5))
  self.assertEqual([r['date'] for r in reference],sorted([r['date'] for r in reference],reverse=True))
  # Q1 — which coffee to try next: catalog plus per-coffee stats.
  catalog={c['name']:c for c in records['coffee_catalog']}
  self.assertIn('Washed Yirgacheffe',catalog['Smoke Ethiopia']['notes'])
  self.assertEqual(catalog['Smoke Ethiopia']['roast_date'],'2026-09-10')
  overview={c['name']:c for c in records['coffee_overview']}
  self.assertEqual(overview['Smoke Ethiopia']['logged_count'],5)
  self.assertEqual(overview['Smoke Ethiopia']['average_rating'],4.2)
  self.assertEqual(overview['Smoke Brazil']['average_rating'],2)
  self.assertEqual(records['selected_coffee']['notes'],'Washed Yirgacheffe, floral and sweet.')
  # Q2 — last shots: newest-first full records with a documented bound of six.
  recent=records['recent_logged_shots']
  self.assertEqual(len(recent),5)
  self.assertEqual([s['date'] for s in recent],['2026-09-05','2026-09-04','2026-09-03','2026-09-02','2026-09-01'])
  self.assertTrue(all('dose' in s and 'grind' in s for s in recent))
  # Q3 — best settings: the top-rated shot is identifiable with full settings.
  best=max(recent,key=lambda s:s['rating'] or 0)
  self.assertEqual(best['rating'],5)
  self.assertEqual((best['dose'],best['grind'],best['yield_g']),(18,'5.0',36))
  self.assertTrue(any(s.get('locked') for s in recent))
  self.http.delete('/coffees/'+ethiopia['id']+'?revision=1')
  self.http.delete('/coffees/'+brazil['id']+'?revision=1')
  self.http.delete('/coffees/'+retired['id']+'?revision='+str(retired_archived['revision']))
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
 def test_structured_bean_details_round_trip_and_validate(self):
  coffee=self.http.post('/coffees',json={'name':'Structured bean','origin':'Ethiopia, Yirgacheffe','variety':'Heirloom','process':'washed','roast_level':'light','single_origin':'single_origin','decaf':True}).json()
  self.assertEqual((coffee['origin'],coffee['variety'],coffee['process'],coffee['roast_level'],coffee['single_origin'],coffee['decaf']),('Ethiopia, Yirgacheffe','Heirloom','washed','light','single_origin',True))
  saved=next(c for c in self.http.get('/state').json()['coffees'] if c['id']==coffee['id'])
  self.assertEqual(saved['process'],'washed')
  updated=self.http.put('/coffees/'+coffee['id'],json={**coffee,'revision':coffee['revision'],'process':'natural','roast_level':'dark'}).json()
  self.assertEqual((updated['process'],updated['roast_level']),('natural','dark'))
  plain=self.http.post('/coffees',json={'name':'Plain bean'}).json()
  self.assertEqual((plain['origin'],plain['variety'],plain['process'],plain['roast_level'],plain['single_origin'],plain['decaf']),('','','','','',False))
  for field,value in [('process','fermented'),('roast_level','extra_dark'),('single_origin','multi')]:
   self.assertEqual(self.http.post('/coffees',json={'name':'Bad bean',field:value}).status_code,422)
  self.http.delete('/coffees/'+coffee['id']+'?revision='+str(updated['revision']))
  self.http.delete('/coffees/'+plain['id']+'?revision=1')
 def test_chat_context_carries_structured_bean_details(self):
  import json
  from src.main import chat_prompt
  coffee=self.http.post('/coffees',json={'name':'Bean context','origin':'Colombia, Huila','variety':'Caturra','process':'natural','roast_level':'medium_dark','single_origin':'blend','decaf':False}).json()
  other=self.http.post('/coffees',json={'name':'Washed reference','origin':'Kenya','process':'washed','roast_level':'light'}).json()
  self.http.post('/shots',json={'coffee_id':other['id'],'date':'2026-09-04','dose':16,'grind':'4.5','yield_g':32,'outcome':'good','rating':5,'reference':True})
  payload=json.loads(self.http.portal.call(chat_prompt,{'account_id':'test-owner','id':'bean-context','message':'What should I expect from this coffee?','coffee_id':coffee['id']}))
  records=payload['current_records']
  catalog=next(c for c in records['coffee_catalog'] if c['id']==coffee['id'])
  self.assertEqual((catalog['origin'],catalog['variety'],catalog['process'],catalog['roast_level'],catalog['single_origin'],catalog['decaf']),('Colombia, Huila','Caturra','natural','medium_dark','blend',False))
  self.assertEqual(records['selected_coffee']['process'],'natural')
  overview=next(c for c in records['coffee_overview'] if c['id']==coffee['id'])
  self.assertEqual((overview['origin'],overview['process'],overview['roast_level']),('Colombia, Huila','natural','medium_dark'))
  reference=next(r for r in records['reference_shots'] if r['coffee']=='Washed reference')
  self.assertEqual((reference['coffee_origin'],reference['coffee_process'],reference['coffee_roast_level'],reference['coffee_decaf']),('Kenya','washed','light',False))
  guidance=payload['action_guidance']
  for field in ['origin','variety','process','roast_level','single_origin','decaf']:
   self.assertIn(field,guidance['coffee_fields'])
  self.assertEqual(guidance['coffee_field_values']['process'][0],'washed')
  self.http.delete('/coffees/'+coffee['id']+'?revision=1')
  self.http.delete('/coffees/'+other['id']+'?revision=1')
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
 def test_archived_coffee_leaves_chat_context_but_keeps_history(self):
  import json
  from src.main import chat_prompt
  coffee=self.http.post('/coffees',json={'name':'Archive test'}).json()
  shot=self.http.post('/shots',json={'coffee_id':coffee['id'],'taste':'favorite'}).json()
  archived=self.http.put('/coffees/'+coffee['id'],json={**coffee,'archived':True}).json()
  self.assertTrue(archived['archived'])
  self.assertTrue(next(c for c in self.http.get('/state').json()['coffees'] if c['id']==coffee['id'])['archived'])
  self.assertEqual(self.http.post('/shots',json={'coffee_id':coffee['id']}).status_code,404)
  payload=json.loads(self.http.portal.call(chat_prompt,{'account_id':'test-owner','id':'archive-test','message':'What should I buy next?','coffee_id':None}))
  self.assertFalse(any(row['id']==coffee['id'] for row in payload['current_records']['coffee_catalog']))
  self.assertFalse(any(row['id']==coffee['id'] for row in payload['current_records']['coffee_overview']))
  self.assertFalse(any(s['coffee_id']==coffee['id'] for s in payload['current_records']['recent_logged_shots']))
  scoped=json.loads(self.http.portal.call(chat_prompt,{'account_id':'test-owner','id':'archive-scoped','message':'Tell me about this one.','coffee_id':coffee['id']}))
  self.assertEqual(scoped['current_records']['selected_coffee']['id'],coffee['id'])
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
  database.messages.insert_many([
   {'account_id':'test-owner','id':'same-coffee-user','coffee_id':'coffee-1','role':'user','text':'Earlier note for this coffee.'},
   {'account_id':'test-owner','id':'other-coffee-user','coffee_id':'coffee-2','role':'user','text':'Do not leak this other coffee.'},
   {'account_id':'test-owner','id':job['id']+'-user','coffee_id':'coffee-1','role':'user','text':job['message']},
  ])
  reply=AsyncMock(return_value=OpenRouterReply(text='Try one small grind adjustment.',actions=[]))
  with patch('src.main.openrouter_reply',reply):
   self.http.portal.call(run_chat,job)
  prompt,history=reply.await_args.args
  context=json.loads(prompt)
  self.assertEqual(context['current_records']['selected_coffee']['id'],'coffee-1')
  self.assertIn('coffee_overview',context['current_records'])
  self.assertIn('equipment_context',context['current_records'])
  self.assertIn('tracked_fields',context['current_records']['equipment_context'])
  self.assertIn('defaults',context['current_records']['equipment_context'])
  self.assertEqual(context['current_records']['scope'],'selected coffee plus bounded all-coffee overview')
  self.assertNotIn('account_id',prompt)
  self.assertEqual([message['text'] for message in history],['Earlier note for this coffee.'])
  saved=database.messages.find_one({'account_id':'test-owner','id':job['id']+'-assistant'})
  self.assertEqual(saved['text'],'Try one small grind adjustment.')
  self.assertEqual(saved['coffee_id'],'coffee-1')
  self.assertEqual(database.jobs.find_one({'account_id':'test-owner','id':job['id']})['status'],'complete')
  database.client.close()
 def test_rejected_openrouter_action_preserves_records_and_reports_the_right_retry(self):
  from pymongo import MongoClient
  from unittest.mock import AsyncMock, patch
  from src.main import CHAT_ACTION_REJECTED, run_chat, state_for
  from src.services.openrouter import OpenRouterReply
  database=MongoClient(os.getenv('MONGO_URL','mongodb://127.0.0.1:27019'))[os.environ['MONGO_DB']]
  job={'account_id':'test-owner','id':'rejected-openrouter-action','message':'Save this change.','coffee_id':'coffee-1','shot_date':'2026-09-15','status':'queued','created_at':'2026-09-15T00:00:00+00:00','receipts':[]}
  database.jobs.insert_one(job)
  database.messages.insert_one({'account_id':'test-owner','id':job['id']+'-user','coffee_id':'coffee-1','role':'user','text':job['message']})
  reply=AsyncMock(return_value=OpenRouterReply(text='Saved.',actions=[{'kind':'shot','id':None,'data':{'coffee_id':'missing-coffee'}}]))
  with patch('src.main.openrouter_reply',reply):
   self.http.portal.call(run_chat,job)
  failed=database.jobs.find_one({'account_id':'test-owner','id':job['id']})
  self.assertEqual(failed['status'],'failed')
  self.assertEqual(failed['error'],CHAT_ACTION_REJECTED)
  self.assertIn('HTTPException',failed['error_detail'])
  self.assertIn('Coffee not found',failed['error_detail'])
  self.assertIn('kind=shot',failed['error_detail'])
  self.assertEqual(failed['receipts'],[])
  state=self.http.portal.call(state_for,'test-owner')
  sent=next(row for row in state['messages'] if row['id']==job['id']+'-user')
  self.assertTrue(sent['failed'])
  self.assertFalse(sent['retryable'])
  message=next(row for row in state['messages'] if row['id']==job['id']+'-assistant-failed')
  self.assertIn('saved coffees and shots were left unchanged',message['text'])
  self.assertFalse(message['retryable'])
  database.client.close()
 def test_invented_plan_id_creates_the_planned_shot(self):
  from pymongo import MongoClient
  from unittest.mock import AsyncMock, patch
  from src.main import run_chat
  from src.services.openrouter import OpenRouterReply
  database=MongoClient(os.getenv('MONGO_URL','mongodb://127.0.0.1:27019'))[os.environ['MONGO_DB']]
  job={'account_id':'test-owner','id':'invented-plan-create','message':'first shot','coffee_id':'coffee-3','shot_date':'2026-09-21','status':'queued','created_at':'2026-09-21T00:00:00+00:00','receipts':[],'retry_count':0,'action_attempted':False}
  database.jobs.insert_one(job)
  database.messages.insert_one({'account_id':'test-owner','id':job['id']+'-user','coffee_id':'coffee-3','role':'user','text':job['message']})
  action={'kind':'shot','id':'planned-next-shot','data':{'coffee_id':'coffee-3','revision':0,'status':'planned','dose':14.5,'grind':'9'}}
  reply=AsyncMock(return_value=OpenRouterReply(text='Plan saved.',actions=[action]))
  with patch('src.main.openrouter_reply',reply):
   self.http.portal.call(run_chat,job)
  done=database.jobs.find_one({'account_id':'test-owner','id':job['id']})
  self.assertEqual(done['status'],'complete')
  self.assertEqual(len(done['receipts']),1)
  saved=done['receipts'][0]['record']
  self.assertNotEqual(saved['id'],'planned-next-shot')
  self.assertEqual((saved['coffee_id'],saved['status'],saved['grind'],saved['dose'],saved['revision']),('coffee-3','planned','9',14.5,1))
  self.assertEqual(database.shots.count_documents({'account_id':'test-owner','coffee_id':'coffee-3','status':'planned','deleted_at':{'$exists':False}}),1)
  message=database.messages.find_one({'account_id':'test-owner','id':job['id']+'-assistant'})
  self.assertEqual(message['text'],'Plan saved.')
  database.client.close()
 def test_invented_plan_id_resyncs_the_existing_plan(self):
  from pymongo import MongoClient
  from unittest.mock import AsyncMock, patch
  from src.main import run_chat
  from src.services.openrouter import OpenRouterReply
  database=MongoClient(os.getenv('MONGO_URL','mongodb://127.0.0.1:27019'))[os.environ['MONGO_DB']]
  plan=self.http.post('/shots',json={'coffee_id':'coffee-4','status':'planned','dose':14.5,'grind':'9'}).json()
  job={'account_id':'test-owner','id':'invented-plan-resync','message':'Plan my next shot for this coffee.','coffee_id':'coffee-4','shot_date':'2026-09-21','status':'queued','created_at':'2026-09-21T00:00:00+00:00','receipts':[],'retry_count':0,'action_attempted':False}
  database.jobs.insert_one(job)
  database.messages.insert_one({'account_id':'test-owner','id':job['id']+'-user','coffee_id':'coffee-4','role':'user','text':job['message']})
  action={'kind':'shot','id':'shot-1','data':{'coffee_id':'coffee-4','revision':0,'status':'planned','grind':'8'}}
  reply=AsyncMock(return_value=OpenRouterReply(text='Updated the plan.',actions=[action]))
  with patch('src.main.openrouter_reply',reply):
   self.http.portal.call(run_chat,job)
  done=database.jobs.find_one({'account_id':'test-owner','id':job['id']})
  self.assertEqual(done['status'],'complete')
  saved=done['receipts'][0]['record']
  self.assertEqual(saved['id'],plan['id'])
  self.assertEqual((saved['grind'],saved['dose']),('8',14.5))
  self.assertEqual(saved['status'],'planned')
  self.assertEqual(database.shots.count_documents({'account_id':'test-owner','coffee_id':'coffee-4','status':'planned','deleted_at':{'$exists':False}}),1)
  database.client.close()
 def test_unknown_shot_id_without_plan_status_is_still_rejected(self):
  from pymongo import MongoClient
  from unittest.mock import AsyncMock, patch
  from src.main import CHAT_ACTION_REJECTED, run_chat
  from src.services.openrouter import OpenRouterReply
  database=MongoClient(os.getenv('MONGO_URL','mongodb://127.0.0.1:27019'))[os.environ['MONGO_DB']]
  job={'account_id':'test-owner','id':'invented-logged-id','message':'That shot was nice.','coffee_id':'coffee-5','shot_date':'2026-09-21','status':'queued','created_at':'2026-09-21T00:00:00+00:00','receipts':[],'retry_count':0,'action_attempted':False}
  database.jobs.insert_one(job)
  database.messages.insert_one({'account_id':'test-owner','id':job['id']+'-user','coffee_id':'coffee-5','role':'user','text':job['message']})
  action={'kind':'shot','id':'shot-1','data':{'coffee_id':'coffee-5','revision':1,'taste':'nice'}}
  reply=AsyncMock(return_value=OpenRouterReply(text='Logged.',actions=[action]))
  with patch('src.main.openrouter_reply',reply):
   self.http.portal.call(run_chat,job)
  failed=database.jobs.find_one({'account_id':'test-owner','id':job['id']})
  self.assertEqual(failed['status'],'failed')
  self.assertEqual(failed['error'],CHAT_ACTION_REJECTED)
  self.assertIn('id=shot-1: 404: Record not found',failed['error_detail'])
  self.assertEqual(failed['receipts'],[])
  self.assertEqual(database.shots.count_documents({'account_id':'test-owner','coffee_id':'coffee-5','deleted_at':{'$exists':False}}),0)
  database.client.close()
 def test_openrouter_failure_records_provider_and_stage(self):
  from pymongo import MongoClient
  from unittest.mock import AsyncMock, patch
  from src.main import run_chat
  from src.services.openrouter import OpenRouterError
  database=MongoClient(os.getenv('MONGO_URL','mongodb://127.0.0.1:27019'))[os.environ['MONGO_DB']]
  job={'account_id':'test-owner','id':'openrouter-provider-failure','message':'What should I change?','coffee_id':'coffee-1','shot_date':'2026-09-15','status':'queued','created_at':'2026-09-15T00:00:00+00:00','receipts':[]}
  database.jobs.insert_one(job)
  database.messages.insert_one({'account_id':'test-owner','id':job['id']+'-user','coffee_id':'coffee-1','role':'user','text':job['message']})
  reply=AsyncMock(side_effect=OpenRouterError('OpenRouter returned invalid structured output.',code='invalid_structured_output',provider='Parasail',finish_reason='stop',stage='parse'))
  with patch('src.main.openrouter_reply',reply):
   self.http.portal.call(run_chat,job)
  failed=database.jobs.find_one({'account_id':'test-owner','id':job['id']})
  self.assertEqual(failed['status'],'failed')
  self.assertEqual(failed['error_code'],'invalid_structured_output')
  self.assertEqual(failed['response_provider'],'Parasail')
  self.assertEqual(failed['finish_reason'],'stop')
  self.assertIn('stage=parse',failed['error_detail'])
  database.client.close()
 def test_failed_chat_retry_reuses_the_original_message_and_is_bounded(self):
  from pymongo import MongoClient
  from unittest.mock import AsyncMock, patch
  from src.main import CHAT_RETRY_LIMIT, state_for
  database=MongoClient(os.getenv('MONGO_URL','mongodb://127.0.0.1:27019'))[os.environ['MONGO_DB']]
  job_id='retryable-chat'
  database.jobs.insert_one({'account_id':'test-owner','id':job_id,'message':'Try again.','coffee_id':'coffee-1','shot_date':'2026-09-15','status':'failed','created_at':'2026-09-15T00:00:00+00:00','receipts':[],'retry_count':0,'action_attempted':False,'error':'Coffee chat is temporarily unavailable. Please try again.'})
  database.messages.insert_one({'account_id':'test-owner','id':job_id+'-user','coffee_id':'coffee-1','role':'user','text':'Try again.'})
  state=self.http.portal.call(state_for,'test-owner')
  sent=next(row for row in state['messages'] if row['id']==job_id+'-user')
  self.assertTrue(sent['failed'])
  self.assertTrue(sent['retryable'])
  failed=next(row for row in state['messages'] if row['id']==job_id+'-assistant-failed')
  self.assertTrue(failed['failed'])
  self.assertFalse(failed['retryable'])
  with patch('src.main.run_chat',new=AsyncMock()) as run:
   response=self.http.post('/chat/'+job_id+'/retry')
   self.http.portal.call(asyncio.sleep,0)
   self.assertEqual(response.status_code,200)
   self.assertEqual(response.json()['retry_count'],1)
   run.assert_awaited_once()
  updated=database.jobs.find_one({'account_id':'test-owner','id':job_id})
  self.assertEqual(updated['status'],'queued')
  self.assertEqual(updated['retry_count'],1)
  self.assertEqual(database.messages.count_documents({'account_id':'test-owner','id':job_id+'-user'}),1)
  database.jobs.update_one({'account_id':'test-owner','id':job_id},{'$set':{'status':'failed','retry_count':CHAT_RETRY_LIMIT,'error':'Coffee chat is temporarily unavailable. Please try again.'}})
  limited=self.http.post('/chat/'+job_id+'/retry')
  self.assertEqual(limited.status_code,409)
  database.messages.delete_many({'account_id':'test-owner','id':{'$in':[job_id+'-user',job_id+'-assistant']}})
  database.jobs.delete_one({'account_id':'test-owner','id':job_id})
  database.client.close()
 def test_plan_sync_failure_reports_its_own_retryable_notice(self):
  from pymongo import MongoClient
  from src.main import PLAN_SYNC_MESSAGE, state_for
  database=MongoClient(os.getenv('MONGO_URL','mongodb://127.0.0.1:27019'))[os.environ['MONGO_DB']]
  job_id='plan-sync-chat'
  database.jobs.insert_one({'account_id':'test-owner','id':job_id,'message':'What next?','coffee_id':'coffee-1','shot_date':'2026-09-15','status':'failed','created_at':'2026-09-15T00:00:00+00:00','receipts':[],'retry_count':0,'action_attempted':False,'error':PLAN_SYNC_MESSAGE})
  database.messages.insert_one({'account_id':'test-owner','id':job_id+'-user','coffee_id':'coffee-1','role':'user','text':'What next?'})
  state=self.http.portal.call(state_for,'test-owner')
  sent=next(row for row in state['messages'] if row['id']==job_id+'-user')
  self.assertTrue(sent['failed'])
  self.assertTrue(sent['retryable'])
  notice=next(row for row in state['messages'] if row['id']==job_id+'-assistant-failed')
  self.assertIn("didn't save it to your planned shot",notice['text'])
  self.assertFalse(notice['retryable'])
  database.messages.delete_many({'account_id':'test-owner','id':{'$in':[job_id+'-user',job_id+'-assistant']}})
  database.jobs.delete_one({'account_id':'test-owner','id':job_id})
  database.client.close()
 def test_chat_context_carries_cross_coffee_dial_in_evidence(self):
  import json
  from src.main import chat_prompt
  coffee=self.http.post('/coffees',json={'name':'Dial-in target','roast_date':'2026-09-01'}).json()
  other=self.http.post('/coffees',json={'name':'Reference bean','roast_date':'2026-08-25'}).json()
  self.http.post('/shots',json={'coffee_id':coffee['id'],'date':'2026-09-01','dose':18,'grind':'5.2','target_yield_g':36,'yield_g':37,'water_temp_c':93,'outcome':'good','rating':5})
  self.http.post('/shots',json={'coffee_id':coffee['id'],'date':'2026-09-02','dose':18,'grind':'5.0','stop_yield_g':34,'yield_g':36,'water_temp_c':93,'taste_balance':'sour','outcome':'adjust'})
  self.http.post('/shots',json={'coffee_id':coffee['id'],'date':'2026-09-03','dose':18,'grind':'4.9','yield_g':36,'water_temp_c':93,'taste_balance':'sour','outcome':'adjust'})
  self.http.post('/shots',json={'coffee_id':other['id'],'date':'2026-09-04','dose':16,'grind':'4.5','target_yield_g':32,'yield_g':32,'water_temp_c':94,'outcome':'good','rating':5,'reference':True})
  payload=json.loads(self.http.portal.call(chat_prompt,{'account_id':'test-owner','id':'dial','message':'Plan my next shot for this coffee.','coffee_id':coffee['id']}))
  records=payload['current_records']
  # Each change is measured against the previous shot and reports the taste result.
  self.assertEqual(records['shot_deltas'][0]['changes']['grind'],'5.0→4.9')
  self.assertEqual(records['shot_deltas'][0]['taste_balance'],'sour')
  # The next test anchors on the good shot's recipe, not the newest failed one.
  self.assertEqual(records['best_shot_for_coffee']['grind'],'5.2')
  # A sour report earns a decisive two-step grind candidate from that anchor.
  self.assertEqual(records['next_shot_candidates']['finer_2']['plan']['grind'],'5.0')
  # A working recipe from another coffee is offered as a starting point, but
  # only its settings travel: dose and targets stay this coffee's.
  borrowed=records['next_shot_candidates']['reference_0']['plan']
  self.assertEqual(borrowed['coffee_id'],coffee['id'])
  self.assertEqual(borrowed['grind'],'4.5')
  self.assertEqual(borrowed['dose'],18)
  self.assertEqual(borrowed['target_yield_g'],36)
  self.assertIn('Reference bean',records['next_shot_candidates']['reference_0']['label'])
  # Derived facts and roast age travel with each shot and reference.
  self.assertEqual(records['recent_logged_shots'][1]['facts']['drip_g'],2)
  self.assertEqual(records['shot_deltas'][1]['choked'],False)
  self.assertEqual(records['reference_shots'][0]['reference'],True)
  self.assertEqual(records['reference_shots'][0]['facts']['ratio'],'1:2.00')
  self.assertIsInstance(records['reference_shots'][0]['roast_age_days'],int)
  self.assertIsInstance(records['selected_coffee']['roast_age_days'],int)
  self.assertIn(records['selected_coffee']['roast_window'].split(' ·')[0],('resting','optimal','past peak'))
  # The whole attempt arc is summarized: two failures since the good anchor.
  self.assertEqual(records['dial_in_summary']['attempts_since_last_success'],2)
  self.assertFalse(records['dial_in_summary']['unresolved'])
  self.assertEqual([trial['grind'] for trial in records['dial_in_summary']['grind_trials']],['4.9','5.0','5.2'])
  self.assertIn('paper',records['reference_shots'][0])
  self.assertIn('reference_shots',payload['dial_in_guidance'])
  self.assertIn('dial_in_summary',payload['dial_in_guidance'])
  self.http.delete('/coffees/'+coffee['id']+'?revision=1')
  self.http.delete('/coffees/'+other['id']+'?revision=1')
 def test_next_shot_candidates_do_not_invert_target_range_from_a_short_measured_yield(self):
  from src.main import next_shot_candidates
  candidates=next_shot_candidates({'coffee_id':'coffee-1','target_yield_g':31,'stop_yield_g':29,'yield_g':30.6,'grind':'8.0'})
  for candidate in candidates.values():
   plan=candidate['plan']
   self.assertTrue(plan['target_yield_max_g'] is None or plan['target_yield_max_g']>=plan['target_yield_g'])
 def test_next_shot_candidates_never_repeat_an_outright_failure(self):
  from src.main import next_shot_candidates, roast_age_from, shot_facts
  # Imported logbooks carry "5 August 2026"; app-created records use ISO.
  self.assertIsInstance(roast_age_from('5 August 2026'),int)
  self.assertIsInstance(roast_age_from('2026-08-25'),int)
  self.assertIsNone(roast_age_from(''))
  self.assertIsNone(roast_age_from('August 2026'))
  # Legacy rows encode choking in outcome while the boolean stays false.
  self.assertTrue(shot_facts({'outcome':'choked'})['choked'])
  self.assertFalse(shot_facts({'outcome':'adjust'})['choked'])
  facts=shot_facts({'dose':18,'yield_g':36,'stop_yield_g':34,'seconds':30,'taste_balance':'sour'})
  self.assertEqual((facts['drip_g'],facts['ratio'],facts['flow_g_s'],facts['evidence']),(2,'1:2.00',1.2,'taste'))
  self.assertEqual(shot_facts({'outcome':'unrated','dose':18})['evidence'],'settings')
  self.assertEqual(shot_facts({})['evidence'],'none')
  for outcome in ('bad','choked'):
   candidates=next_shot_candidates({'coffee_id':'coffee-1','grind':'5.0','outcome':outcome})
   self.assertNotIn('repeat',candidates)
   self.assertIn('finer',candidates)
  self.assertIn('repeat',next_shot_candidates({'coffee_id':'coffee-1','grind':'5.0','outcome':'adjust'}))
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
 def test_openrouter_action_repair_tolerates_model_slips(self):
  from fastapi import HTTPException
  from pymongo import MongoClient
  from src.main import apply_inference_action
  database=MongoClient(os.getenv('MONGO_URL','mongodb://127.0.0.1:27019'))[os.environ['MONGO_DB']]
  job={'account_id':'test-owner','id':'openrouter-repair','shot_date':'2026-09-15','coffee_id':'coffee-1'}
  database.jobs.insert_one({**job,'status':'running','receipts':[]})
  row=self.http.portal.call(apply_inference_action,job,{'kind':'shot','id':None,'data':{'coffee_id':'coffee-1','dose':14,'taste':'repair base'}})
  # Missing revision is filled from the current record instead of 409.
  repaired=self.http.portal.call(apply_inference_action,job,{'kind':'shot','id':row['id'],'data':{'taste':'repaired without revision'}})
  self.assertEqual(repaired['taste'],'repaired without revision')
  self.assertEqual(repaired['dose'],14)
  # String revisions coerce; unknown fields (ratio, id) are dropped, not rejected.
  coerced=self.http.portal.call(apply_inference_action,job,{'kind':'shot','id':row['id'],'data':{'revision':str(repaired['revision']),'taste':'repaired types','ratio':'1:2.00','id':'ignored'}})
  self.assertEqual(coerced['taste'],'repaired types')
  # An explicitly wrong revision still rejects stale edits.
  with self.assertRaises(HTTPException):
   self.http.portal.call(apply_inference_action,job,{'kind':'shot','id':row['id'],'data':{'revision':0,'taste':'stale'}})
  # Creates reset a stray revision, fill coffee_id from the job, drop an
  # inverted target max, and coerce "5"/5.0 ratings.
  created=self.http.portal.call(apply_inference_action,job,{'kind':'shot','id':None,'data':{'revision':1,'dose':15,'target_yield_g':30,'target_yield_max_g':20,'rating':'5'}})
  self.assertEqual((created['coffee_id'],created['revision'],created['rating']),('coffee-1',1,5))
  self.assertIsNone(created['target_yield_max_g'])
  self.assertEqual(created['target_yield_g'],30)
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
 def test_selfhost_profile_exposes_shots_without_chat(self):
  from unittest.mock import patch
  with patch('src.main.AI_ENABLED',False),patch('src.main.REQUIRE_AUTH',False):
   state=self.http.get('/state').json()
   self.assertEqual(state['messages'],[])
   self.assertIsNone(state['active_job'])
   self.assertEqual(state['capabilities'],{'chat':False,'auth':False,'app_mode':'personal'})
   self.assertEqual(self.http.post('/chat',json={'id':'disabled','message':'test'}).status_code,404)
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
