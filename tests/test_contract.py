import asyncio, os, sys, unittest, uuid
from pathlib import Path
os.environ['APP_MODE']='personal'
os.environ['COFFEE_AI_ENABLED']='true'
os.environ['MONGO_DB']='coffee_test_'+uuid.uuid4().hex
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
  payload=json.loads(self.http.portal.call(chat_prompt,{'id':'test','message':'That shot was nice','coffee_id':coffee['id']}))
  recent=payload['current_records']['recent_logged_shots']
  self.assertEqual([s['id'] for s in recent],[s['id'] for s in rows[1:5]][::-1])
  self.assertEqual(recent[0]['rating'],4)
  self.assertEqual(recent[0]['revision'],1)
  self.assertEqual(payload['current_records']['selected_coffee']['name'],'Chat snapshot test')
  self.assertNotIn(plan['id'],[s['id'] for s in recent])
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
  cls.context=TestClient(app);cls.http=cls.context.__enter__()
 @classmethod
 def tearDownClass(cls):
  # Only this test's random database is removed.
  from pymongo import MongoClient
  with MongoClient(os.getenv('MONGO_URL','mongodb://127.0.0.1:27019')) as mongo:
   mongo.drop_database(os.environ['MONGO_DB'])
  cls.context.__exit__(None,None,None)
 def test_seed_preserves_plans_and_chronological_dates(self):
  state=self.http.get('/state').json()
  self.assertEqual(len([c for c in state['coffees'] if c['id'].startswith('coffee-')]),6)
  self.assertEqual(sum(x['status']=='planned' for x in state['shots']),5)
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
 def test_archived_coffee_keeps_history_for_chat_but_cannot_receive_shots(self):
  import json
  from src.main import chat_prompt
  coffee=self.http.post('/coffees',json={'name':'Archive test'}).json()
  shot=self.http.post('/shots',json={'coffee_id':coffee['id'],'taste':'favorite'}).json()
  archived=self.http.put('/coffees/'+coffee['id'],json={**coffee,'archived':True}).json()
  self.assertTrue(archived['archived'])
  self.assertTrue(next(c for c in self.http.get('/state').json()['coffees'] if c['id']==coffee['id'])['archived'])
  self.assertEqual(self.http.post('/shots',json={'coffee_id':coffee['id']}).status_code,404)
  payload=json.loads(self.http.portal.call(chat_prompt,{'id':'archive-test','message':'What should I buy next?','coffee_id':None}))
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
  database.jobs.insert_one({'id':'gateway-test','token':'test-only','status':'running','shot_date':'2026-09-08','receipts':[]})
  response=self.http.post('/agent/save',headers={'X-Coffee-Token':'test-only'},json={'kind':'shot','data':{'coffee_id':'coffee-1','dose':14,'taste':'test only','outcome':'choked','target_yield_g':30}})
  self.assertEqual(response.status_code,200)
  row=response.json()
  receipt=database.jobs.find_one({'id':'gateway-test'})['receipts'][0]
  self.assertEqual(receipt['record'],row)
  self.assertEqual(row['outcome'],'choked')
  self.assertEqual(row['target_yield_g'],30)
  self.assertEqual(row['date'],'2026-09-08')
  self.assertEqual(database.shots.find_one({'id':row['id']})['taste'],'test only')
  database.jobs.update_one({'id':'gateway-test'},{'$set':{'status':'complete'}})
  database.client.close()
 def test_production_rejects_anonymous_and_other_accounts(self):
  from unittest.mock import patch, AsyncMock
  from types import SimpleNamespace
  with patch('src.main.REQUIRE_AUTH',True),patch('src.main.OWNER_SUB','owner'):
   self.assertEqual(self.http.get('/state').status_code,401)
   self.assertEqual(self.http.post('/chat',json={'id':'unauthorized','message':'test'}).status_code,401)
   with patch('src.main.verify_privy_access_token',AsyncMock(return_value=SimpleNamespace(user_id='other'))):
    self.assertEqual(self.http.get('/state',headers={'Authorization':'Bearer test'}).status_code,403)
   with patch('src.main.verify_privy_access_token',AsyncMock(return_value=SimpleNamespace(user_id='owner'))):
    self.assertEqual(self.http.get('/state',headers={'Authorization':'Bearer test'}).status_code,200)
 def test_gateway_requires_live_job(self):
  self.assertEqual(self.http.get('/agent/context',headers={'X-Coffee-Token':'bad'}).status_code,403)
  self.assertEqual(self.http.post('/agent/save',headers={'X-Coffee-Token':'bad'},json={'kind':'coffee','data':{'name':'blocked'}}).status_code,403)
 def test_selfhost_profile_exposes_shots_without_chat(self):
  from unittest.mock import patch
  with patch('src.main.AI_ENABLED',False):
   state=self.http.get('/state').json()
   self.assertEqual(state['messages'],[])
   self.assertIsNone(state['active_job'])
   self.assertEqual(state['capabilities'],{'chat':False,'auth':False,'app_mode':'personal'})
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
   self.assertEqual(self.http.delete('/shots/'+other['id']+'?revision=1').status_code,401)

if __name__=='__main__':unittest.main()
