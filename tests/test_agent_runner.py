# Task T0302 � Spec FR-012, FR-060-FR-063 � Plan Test-First US1
import os
import unittest
from pathlib import Path
from unittest import mock

from agents.mcp import MCPServerStdio

from todo_app import mcp_server
from todo_app.chat import runner


class TestAgentRunner(unittest.TestCase):
    def test_build_agent_uses_default_model(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('OPENAI_MODEL', None)
            agent = runner.build_agent()
            self.assertIsNotNone(agent)

    def test_build_agent_honors_env_model(self):
        with mock.patch.dict(os.environ, {'OPENAI_MODEL': 'gpt-test-model'}):
            agent = runner.build_agent()
            self.assertIsNotNone(agent)

    def test_mcp_stdio_config_has_minimal_env_and_resolver(self):
        with mock.patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test', 'JWT_SECRET': 'x', 'DATABASE_URL': 'sqlite://'}):
            agent = runner.build_agent()
            servers = getattr(agent, 'mcp_servers', []) or []
            self.assertTrue(len(servers) >= 1)
            srv = servers[0]
            self.assertIsInstance(srv, MCPServerStdio)
            params = getattr(srv, 'params', {}) or {}
            command = getattr(params, 'command', None)
            if isinstance(params, dict):
                command = params.get('command')
                env = params.get('env') or {}
            else:
                env = getattr(params, 'env', {}) or {}
            self.assertEqual(command, os.sys.executable)
            self.assertEqual(getattr(params, 'args', None) or (params.get('args') if isinstance(params, dict) else None), ['-m', 'todo_app.mcp_server'])
            self.assertEqual(env.get('DATABASE_URL'), 'sqlite://')
            self.assertNotIn('OPENAI_API_KEY', env)
            self.assertNotIn('JWT_SECRET', env)
            self.assertIsNotNone(getattr(srv, 'tool_meta_resolver', None))

    def test_resolve_user_meta_injects_from_context(self):
        class Ctx:
            def __init__(self):
                self.context = {'user_id': 'user-123'}
        class Meta:
            def __init__(self):
                self.run_context = Ctx()
        meta = Meta()
        res = runner.resolve_user_meta(meta)  # type: ignore
        self.assertEqual(res.get('user_id'), 'user-123')

    def test_sanitizer_returns_generic_message(self):
        msg = runner._sanitize_tool_error(Exception('secret key sk-123'))
        self.assertNotIn('sk-123', msg)
        self.assertTrue(len(msg) > 0)

    def test_sanitizer_logs_exception_with_redaction(self):
        with self.assertLogs('todo_app.chat.runner', level='ERROR') as captured:
            msg = runner._sanitize_tool_error(ValueError('secret key sk-123'))
        self.assertIn('The assistant encountered an error while using tools', msg)
        joined = '\n'.join(captured.output)
        self.assertIn('ValueError', joined)
        self.assertIn('sk-[REDACTED]', joined)
        self.assertNotIn('sk-123', joined)

    def test_mcp_server_logs_tool_exceptions(self):
        from unittest import mock
        with mock.patch('todo_app.mcp_server.task_service.add_task', side_effect=RuntimeError('secret token sk-abc123')):
            with self.assertLogs('todo_app.mcp_server', level='ERROR') as captured:
                result = __import__('todo_app.mcp_server', fromlist=['add_task']).add_task('user-1', 'Task')
        self.assertEqual(result.get('error'), 'invalid_input')
        joined = '\n'.join(captured.output)
        self.assertIn('RuntimeError', joined)
        self.assertIn('sk-[REDACTED]', joined)
        self.assertNotIn('sk-abc123', joined)

    def test_agent_runner_subprocess_uses_project_src_and_timeout(self):
        with mock.patch.dict(os.environ, {'PATH': 'C:/Tools', 'PYTHONPATH': 'custom-src'}, clear=False):
            agent = runner.build_agent()
            servers = getattr(agent, 'mcp_servers', []) or []
            self.assertTrue(servers)
            srv = servers[0]
            params = getattr(srv, 'params', {}) or {}
            env = params.get('env') if isinstance(params, dict) else getattr(params, 'env', {})
            repo_src = str(Path(__file__).resolve().parents[1] / 'src')
            self.assertIn(repo_src, env.get('PYTHONPATH', ''))
            self.assertGreaterEqual(getattr(srv, 'client_session_timeout_seconds', 0), 30)
            self.assertEqual(getattr(params, 'cwd', None), str(Path(__file__).resolve().parents[1]))

    def test_mcp_server_resolves_verified_user_from_tool_meta(self):
        class DummyContext:
            meta = {'user_id': 'user-verified'}
        self.assertEqual(mcp_server._resolve_tool_user_id(None, DummyContext()), 'user-verified')
        self.assertEqual(mcp_server._resolve_tool_user_id('user-verified', DummyContext()), 'user-verified')
        with self.assertRaises(ValueError):
            mcp_server._resolve_tool_user_id('attacker', DummyContext())

    def test_mcp_server_resolves_verified_user_from_request_context_meta(self):
        class RequestContext:
            meta = {'user_id': 'user-verified'}
        class DummyContext:
            request_context = RequestContext()
        self.assertEqual(mcp_server._resolve_tool_user_id(None, DummyContext()), 'user-verified')
        self.assertEqual(mcp_server._resolve_tool_user_id('user-verified', DummyContext()), 'user-verified')
        with self.assertRaises(ValueError):
            mcp_server._resolve_tool_user_id('attacker', DummyContext())
