# Task T0701
import unittest
from todo_app.chat import runner


class TestChatSecurity(unittest.TestCase):
    def test_sanitizer_no_secrets(self):
        msg = runner._sanitize_tool_error(Exception('sk-12345'))
        self.assertNotIn('sk-12345', msg)
