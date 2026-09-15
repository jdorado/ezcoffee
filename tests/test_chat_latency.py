import os, sys, unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'coffee_api'))
from fastapi import HTTPException

class ChatLatency(unittest.IsolatedAsyncioTestCase):
 async def test_auth_only_does_not_load_logbook(self):
  from src.main import agent_context
  with patch('src.main.authorize',AsyncMock(return_value={})), patch('src.main.state',AsyncMock(side_effect=AssertionError('unneeded read'))) as state:
   self.assertEqual(await agent_context('test',auth_only=True),{'authorized':True})
   state.assert_not_called()
 async def test_auth_only_rejects_invalid_capability(self):
  from src.main import agent_context
  with patch('src.main.authorize',AsyncMock(side_effect=HTTPException(403))), patch('src.main.state',AsyncMock()) as state:
   with self.assertRaises(HTTPException): await agent_context('invalid',auth_only=True)
   state.assert_not_called()
