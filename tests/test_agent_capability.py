import os, sys, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "coffee_api"))

ACCOUNT = 'agent-cap-owner'
SECRET = 'test-agent-capability-secret-32-bytes!!'
BASE_URL = 'http://127.0.0.1:5176'
FULL_PERMS = {'coffees:write', 'shots:write', 'records:delete'}


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = {d['id']: dict(d) for d in (docs or [])}

    async def find_one(self, query):
        for doc in self.docs.values():
            if all(doc.get(k) == v for k, v in query.items() if not isinstance(v, dict)):
                return dict(doc)
        return None

    async def insert_one(self, doc):
        self.docs[doc['id']] = dict(doc)

    async def update_one(self, query, update, upsert=False):
        doc = await self.find_one(query)
        if not doc and upsert:
            doc = {'id': query.get('id'), 'account_id': query.get('account_id')}
            for op, changes in update.items():
                if op in ('$setOnInsert', '$set'):
                    doc.update(changes)
            self.docs[doc['id']] = doc
            return
        if not doc:
            return
        for op, changes in update.items():
            if op == '$set':
                doc.update(changes)
            elif op == '$unset':
                for k in changes:
                    doc.pop(k, None)
            elif op == '$inc':
                for k, v in changes.items():
                    doc[k] = doc.get(k, 0) + v
        self.docs[doc['id']] = doc

    async def find_one_and_update(self, query, update, return_document=False):
        doc = await self.find_one({k: v for k, v in query.items() if not isinstance(v, dict)})
        if not doc:
            return None
        await self.update_one(query, update)
        return dict(self.docs[doc['id']])

def wipe_account():
    from pymongo import MongoClient
    with MongoClient(os.getenv('MONGO_URL', 'mongodb://127.0.0.1:27019')) as mongo:
        database = mongo[os.environ['MONGO_DB']]
        for collection in ('coffees', 'shots', 'jobs', 'messages'):
            database[collection].delete_many({'account_id': ACCOUNT})


class AgentCapabilitySetup:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Import here (sync context, no running loop) so the shared motor
        # client never binds to an ephemeral async-test event loop.
        import src.main  # noqa: F401
        from src.services import ez as ez_module
        cls._secret = ez_module.COFFEE_AGENT_CAPABILITY_SECRET
        cls._base = ez_module.COFFEE_AGENT_API_BASE_URL
        ez_module.COFFEE_AGENT_CAPABILITY_SECRET = SECRET
        ez_module.COFFEE_AGENT_API_BASE_URL = BASE_URL

    @classmethod
    def tearDownClass(cls):
        from src.services import ez as ez_module
        ez_module.COFFEE_AGENT_CAPABILITY_SECRET = cls._secret
        ez_module.COFFEE_AGENT_API_BASE_URL = cls._base
        super().tearDownClass()

    def tearDown(self):
        wipe_account()
        super().tearDown()

    def mint(self, account=ACCOUNT, job='job-1', permissions=FULL_PERMS, **kwargs):
        from src.services import ez as ez_module
        return ez_module.mint_agent_capability(account_id=account, job_id=job, permissions=set(permissions), **kwargs)

    def client(self):
        from fastapi.testclient import TestClient
        from src.main import app
        context = TestClient(app)
        http = context.__enter__()
        self.addCleanup(context.__exit__, None, None, None)
        return http

    def state_for(self, http):
        from src import main
        with patch.object(main, 'verify_privy_access_token', AsyncMock(return_value=SimpleNamespace(user_id=ACCOUNT))), \
             patch.object(main, 'OWNER_SUB', ACCOUNT):
            response = http.get('/state', headers={'Authorization': 'Bearer test'})
        self.assertEqual(response.status_code, 200)
        return response.json()


class AgentCapabilityContract(AgentCapabilitySetup, unittest.IsolatedAsyncioTestCase):
    async def test_capability_is_bound_to_one_account_and_permission_set(self):
        from src.services import ez as ez_module
        capability = await ez_module.require_agent_capability(f'Bearer {self.mint()}')
        self.assertEqual(capability.account_id, ACCOUNT)
        self.assertEqual(capability.job_id, 'job-1')
        self.assertEqual(capability.permissions, frozenset(FULL_PERMS))
        self.assertIsNone(ez_module.require_agent_request(capability, 'job-1'))
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as ctx:
            ez_module.require_agent_request(capability, 'job-2')
        self.assertEqual(ctx.exception.status_code, 403)
        with self.assertRaises(HTTPException) as ctx:
            ez_module.require_agent_permission(capability, 'workouts:swap')
        self.assertEqual(ctx.exception.status_code, 403)

    async def test_agent_inputs_carry_no_identity_or_secret(self):
        from src.main import AgentCoffeeSave, AgentRecordDelete, AgentShotSave
        forbidden = {'owner', 'tenant', 'account_id', 'api_url', 'api_base_url', 'capability', 'token', 'url'}
        for model in (AgentCoffeeSave, AgentShotSave, AgentRecordDelete):
            self.assertTrue(forbidden.isdisjoint(model.model_fields))

    async def test_plugin_context_is_namespaced_and_verifiable(self):
        from src.services import ez as ez_module
        context = ez_module.agent_run_context(ACCOUNT, 'job-9')
        self.assertEqual(set(context), {'plugins'})
        plugin = context['plugins']['coffee']
        self.assertEqual(plugin['api_base_url'], BASE_URL)
        capability = await ez_module.require_agent_capability(f"Bearer {plugin['capability']}")
        self.assertEqual((capability.account_id, capability.job_id), (ACCOUNT, 'job-9'))
        self.assertEqual(capability.permissions, frozenset(FULL_PERMS))

    async def test_plugin_context_is_absent_without_config(self):
        from src.services import ez as ez_module
        with patch.object(ez_module, 'COFFEE_AGENT_API_BASE_URL', 'https://example.test/x?token=leak'):
            self.assertIsNone(ez_module.agent_run_context(ACCOUNT, 'job-9'))
        with patch.object(ez_module, 'COFFEE_AGENT_CAPABILITY_SECRET', ''):
            self.assertIsNone(ez_module.agent_run_context(ACCOUNT, 'job-9'))

    async def test_admission_mints_plugin_context_for_chat_turn(self):
        from src import main
        from src.services import ez as ez_module
        jobs = FakeCollection([{'account_id': ACCOUNT, 'id': 'job-7', 'message': 'log it',
                                'coffee_id': None, 'shot_date': '2026-09-15', 'status': 'queued',
                                'receipts': [], 'retry_count': 0}])
        messages = FakeCollection([])
        fake_db = SimpleNamespace(jobs=jobs, messages=messages)
        seen = {}

        async def fake_call(binding, method, path, body=None):
            if method == 'POST':
                seen['admission'] = body
                return {'id': 'run-7'}
            return {'status': 'completed', 'messages': [{'id': 'm1', 'text': 'Saved.'}], 'receipts': []}

        with patch.object(main, 'db', fake_db), \
             patch.object(main, 'verified_binding', AsyncMock(return_value={'bindingId': 'binding-7'})), \
             patch.object(main, 'ez_call', fake_call):
            await main.ez_chat_cycle(ACCOUNT, 'job-7')
        plugin = seen['admission']['context']['plugins']['coffee']
        self.assertEqual(plugin['api_base_url'], BASE_URL)
        capability = await ez_module.require_agent_capability(f"Bearer {plugin['capability']}")
        self.assertEqual((capability.account_id, capability.job_id), (ACCOUNT, 'job-7'))
        self.assertNotIn('account_id', seen['admission'])
        updated = await jobs.find_one({'id': 'job-7'})
        self.assertEqual(updated['status'], 'complete')


def rebind_db():
    # TestClient lifespan shutdown closes the shared motor client, which would
    # break whichever test class enters next. Rebinding keeps every class
    # independent regardless of discovery order.
    from motor.motor_asyncio import AsyncIOMotorClient
    from src import main
    main.client = AsyncIOMotorClient(os.getenv('MONGO_URL', 'mongodb://127.0.0.1:27019'), serverSelectionTimeoutMS=3000)
    main.db = main.client[os.environ['MONGO_DB']]


class AgentRouteContract(AgentCapabilitySetup, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # One client per class: exiting TestClient shuts down the lifespan and
        # closes the shared motor client, so it cannot be re-entered per test.
        rebind_db()
        from fastapi.testclient import TestClient
        from src.main import app
        cls._context = TestClient(app)
        cls.http = cls._context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls._context.__exit__(None, None, None)
        rebind_db()
        super().tearDownClass()

    def client(self):
        return self.http

    def bodies(self, request_id):
        return {
            '/v1/agent/coffees/save': {'name': 'Agent roast', 'coffee_id': None, 'expected_revision': None, 'request_id': request_id},
            '/v1/agent/shots/save': {'coffee_id': 'missing-coffee', 'shot_id': None, 'expected_revision': None, 'request_id': request_id},
            '/v1/agent/records/delete': {'kind': 'coffee', 'id': 'missing', 'expected_revision': 1, 'request_id': request_id},
        }

    def test_missing_or_invalid_capability_is_401(self):
        http = self.client()
        expired = self.mint(job='job-exp', expires_in_minutes=-1)
        headers_options = [{}, {'Authorization': 'Bearer bad'}, {'Authorization': f'Bearer {expired}'}]
        for path, body in self.bodies('job-exp').items():
            for headers in headers_options:
                self.assertEqual(http.post(path, headers=headers, json=body).status_code, 401, (path, headers))

    def test_every_agent_write_rejects_request_id_mismatch(self):
        http = self.client()
        headers = {'Authorization': f"Bearer {self.mint(job='job-ok')}"}
        for path, body in self.bodies('job-other').items():
            response = http.post(path, headers=headers, json=body)
            self.assertEqual(response.status_code, 403, path)

    def test_wrong_permission_is_rejected_per_route(self):
        http = self.client()
        limited = {'Authorization': f"Bearer {self.mint(job='job-perm', permissions={'coffees:write'})}"}
        ok = http.post('/v1/agent/coffees/save', headers=limited, json=self.bodies('job-perm')['/v1/agent/coffees/save'])
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(http.post('/v1/agent/shots/save', headers=limited, json=self.bodies('job-perm')['/v1/agent/shots/save']).status_code, 403)
        self.assertEqual(http.post('/v1/agent/records/delete', headers=limited, json=self.bodies('job-perm')['/v1/agent/records/delete']).status_code, 403)

    def test_wrong_account_cannot_touch_records(self):
        http = self.client()
        headers_a = {'Authorization': f"Bearer {self.mint(job='job-a')}"}
        coffee = http.post('/v1/agent/coffees/save', headers=headers_a, json=self.bodies('job-a')['/v1/agent/coffees/save']).json()
        headers_b = {'Authorization': f"Bearer {self.mint(account='other-account', job='job-b')}"}
        stolen = http.post('/v1/agent/coffees/save', headers=headers_b, json={
            'name': 'Stolen', 'coffee_id': coffee['id'], 'expected_revision': coffee['revision'], 'request_id': 'job-b'})
        self.assertEqual(stolen.status_code, 409)
        gone = http.post('/v1/agent/records/delete', headers=headers_b, json={
            'kind': 'coffee', 'id': coffee['id'], 'expected_revision': coffee['revision'], 'request_id': 'job-b'})
        self.assertEqual(gone.status_code, 409)

    def test_receipt_and_readback_on_success(self):
        http = self.client()
        headers = {'Authorization': f"Bearer {self.mint(job='job-flow')}"}
        coffee = http.post('/v1/agent/coffees/save', headers=headers, json={
            'name': 'Agent roast', 'coffee_id': None, 'expected_revision': None, 'request_id': 'job-flow'}).json()
        self.assertEqual(coffee['revision'], 1)
        self.assertTrue(coffee['id'])
        self.assertTrue({'_id', 'account_id', 'token'}.isdisjoint(coffee))
        revised = http.post('/v1/agent/coffees/save', headers=headers, json={
            'name': 'Agent roast v2', 'coffee_id': coffee['id'], 'expected_revision': 1, 'request_id': 'job-flow'}).json()
        self.assertEqual(revised['revision'], 2)
        stale = http.post('/v1/agent/coffees/save', headers=headers, json={
            'name': 'stale', 'coffee_id': coffee['id'], 'expected_revision': 1, 'request_id': 'job-flow'})
        self.assertEqual(stale.status_code, 409)
        shot = http.post('/v1/agent/shots/save', headers=headers, json={
            'coffee_id': coffee['id'], 'dose': 18, 'shot_id': None, 'expected_revision': None, 'request_id': 'job-flow'}).json()
        self.assertEqual(shot['revision'], 1)
        state = self.state_for(http)
        self.assertEqual(next(c for c in state['coffees'] if c['id'] == coffee['id'])['name'], 'Agent roast v2')
        self.assertTrue(any(s['id'] == shot['id'] for s in state['shots']))
        deleted = http.post('/v1/agent/records/delete', headers=headers, json={
            'kind': 'shot', 'id': shot['id'], 'expected_revision': 1, 'request_id': 'job-flow'}).json()
        self.assertEqual(deleted, {'id': shot['id'], 'deleted': True, 'revision': 2})
        resurrected = http.post('/v1/agent/shots/save', headers=headers, json={
            'coffee_id': coffee['id'], 'shot_id': shot['id'], 'expected_revision': 2, 'request_id': 'job-flow'})
        self.assertEqual(resurrected.status_code, 409)
        state = self.state_for(http)
        self.assertFalse(any(s['id'] == shot['id'] for s in state['shots']))
        removed = http.post('/v1/agent/records/delete', headers=headers, json={
            'kind': 'coffee', 'id': coffee['id'], 'expected_revision': 2, 'request_id': 'job-flow'}).json()
        self.assertTrue(removed['deleted'])
        state = self.state_for(http)
        self.assertFalse(any(c['id'] == coffee['id'] for c in state['coffees']))

    def test_archived_coffee_rejects_agent_shots(self):
        http = self.client()
        headers = {'Authorization': f"Bearer {self.mint(job='job-arch')}"}
        coffee = http.post('/v1/agent/coffees/save', headers=headers, json={
            'name': 'Archive me', 'coffee_id': None, 'expected_revision': None, 'request_id': 'job-arch'}).json()
        archived = http.post('/v1/agent/coffees/save', headers=headers, json={
            'name': 'Archive me', 'archived': True, 'coffee_id': coffee['id'],
            'expected_revision': 1, 'request_id': 'job-arch'}).json()
        self.assertTrue(archived['archived'])
        blocked = http.post('/v1/agent/shots/save', headers=headers, json={
            'coffee_id': coffee['id'], 'shot_id': None, 'expected_revision': None, 'request_id': 'job-arch'})
        self.assertEqual(blocked.status_code, 404)


if __name__ == '__main__':
    unittest.main()
