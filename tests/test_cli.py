# Task T-003 · Spec §US1 FR-104–108 · Plan §Phase I console plan (CLI surface), §OQ-5, §Test-First 1
import contextlib
import io
import unittest
from unittest import mock

import todo_app


class TestCliProtocol(unittest.TestCase):
    def run_cli(self, input_lines):
        stdin = io.StringIO("\n".join(input_lines) + "\n")
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch("sys.stdin", stdin),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            try:
                exit_code = todo_app.main()
            except SystemExit as e:
                exit_code = e.code
        return exit_code, stdout.getvalue(), stderr.getvalue()


class TestCliStreamPlacement(TestCliProtocol):
    def test_add_multi_line_session_stdout_confirmation(self):
        code, out, err = self.run_cli(["add Buy groceries", "exit"])
        self.assertIn("Buy groceries", out)
        self.assertIn("1", out)
        self.assertEqual(err, "")

    def test_errors_on_stderr(self):
        code, out, err = self.run_cli(["add   ", "exit"])
        self.assertNotEqual(err, "")


class TestCliListOutput(TestCliProtocol):
    def test_list_includes_id_description_status(self):
        _, out, _ = self.run_cli(
            [
                "add Buy groceries",
                "add Clean house",
                "complete 1",
                "list",
                "exit",
            ]
        )
        self.assertIn("1", out)
        self.assertIn("Buy groceries", out)
        self.assertIn("complete", out)
        self.assertIn("2", out)
        self.assertIn("Clean house", out)
        # FR-104 (pre-arranged wording update, spec OQ-5): pending -> incomplete
        self.assertIn("incomplete", out)


class TestCliAddWithDescription(TestCliProtocol):
    """FR-103: `add <title> | <description>` canonical form + legacy bare add."""

    def test_add_title_pipe_description(self):
        _, out, err = self.run_cli(["add Buy groceries | Milk eggs", "exit"])
        self.assertIn("Added item 1: Buy groceries", out)
        self.assertEqual(err, "")

    def test_add_title_pipe_list_row_shows_description(self):
        _, out, err = self.run_cli(["add Buy groceries | Milk eggs", "list", "exit"])
        self.assertIn("1. Buy groceries — Milk eggs [incomplete]", out)
        self.assertEqual(err, "")

    def test_add_title_pipe_empty_description(self):
        _, out, _ = self.run_cli(["add Buy groceries |", "list", "exit"])
        self.assertIn("1. Buy groceries [incomplete]", out)

    def test_bare_add_legacy_whole_text_is_title(self):
        _, out, err = self.run_cli(["add legacy text here", "list", "exit"])
        self.assertIn("Added item 1: legacy text here", out)
        self.assertIn("1. legacy text here [incomplete]", out)
        self.assertEqual(err, "")

    def test_empty_add_errors_on_stderr(self):
        _, out, err = self.run_cli(["add", "exit"])
        self.assertIn("Error", err)
        self.assertNotIn("Added item", out)

    def test_whitespace_pipe_title_errors_on_stderr(self):
        _, out, err = self.run_cli(["add   | desc", "exit"])
        self.assertIn("Error", err)
        self.assertNotIn("Added item", out)


class TestCliUpdate(TestCliProtocol):
    """FR-105: `update <id> <title> | <description>`."""

    def test_update_rewrites_title_and_description(self):
        _, out, _ = self.run_cli(
            [
                "add Buy groceries | Milk",
                "update 1 New title | New desc",
                "list",
                "exit",
            ]
        )
        self.assertIn("1. New title — New desc [incomplete]", out)

    def test_update_title_only_legacy_form(self):
        _, out, _ = self.run_cli(
            [
                "add Buy groceries | Milk",
                "update 1 New title",
                "list",
                "exit",
            ]
        )
        self.assertIn("1. New title [incomplete]", out)

    def test_update_unknown_id_errors_on_stderr(self):
        _, out, err = self.run_cli(["add Buy groceries", "update 9 T | D", "exit"])
        self.assertIn("Error: no item with that id", err)
        self.assertNotIn("Updated", out)


class TestCliToggle(TestCliProtocol):
    """FR-107: `toggle <id>` flips both directions."""

    def test_toggle_pending_to_complete(self):
        _, out, err = self.run_cli(["add Task", "toggle 1", "exit"])
        self.assertIn("Toggled item 1: Task [complete]", out)
        self.assertEqual(err, "")

    def test_toggle_complete_to_incomplete(self):
        _, out, _ = self.run_cli(["add Task", "toggle 1", "toggle 1", "exit"])
        self.assertIn("Toggled item 1: Task [incomplete]", out)

    def test_toggle_unknown_id_errors_on_stderr(self):
        _, _, err = self.run_cli(["add Task", "toggle 9", "exit"])
        self.assertIn("no item with that id", err)


class TestCliCompleteAlias(TestCliProtocol):
    """FR-108/OQ-5: `complete <id>` kept as legacy mark-complete alias."""

    def test_complete_alias_legacy_output(self):
        _, out, err = self.run_cli(["add Task", "complete 1", "exit"])
        self.assertIn("Completed item 1: Task", out)
        self.assertEqual(err, "")

    def test_complete_alias_errors_when_already_complete(self):
        _, _, err = self.run_cli(["add Task", "complete 1", "complete 1", "exit"])
        self.assertIn("Error", err)

    def test_complete_alias_not_flipped_by_toggle_semantics(self):
        # complete must not un-complete; second call errors (legacy behavior)
        _, _, err = self.run_cli(["add Task", "complete 1", "complete 1", "exit"])
        self.assertIn("already complete", err)


class TestCliHelp(TestCliProtocol):
    def test_unknown_command_prints_help(self):
        _, out, _ = self.run_cli(["frobnicate", "exit"])
        self.assertIn("add", out.lower())
        self.assertIn("list", out.lower())
        self.assertIn("complete", out.lower())
        self.assertIn("delete", out.lower())
        self.assertIn("exit", out.lower())
        self.assertIn("help", out.lower())

    def test_help_lists_new_commands(self):
        _, out, _ = self.run_cli(["help", "exit"])
        lowered = out.lower()
        self.assertIn("update", lowered)
        self.assertIn("toggle", lowered)


class TestCliExit(TestCliProtocol):
    def test_exit_terminates_with_code_0(self):
        code, _, _ = self.run_cli(["exit"])
        self.assertEqual(code, 0)

    def test_exit_after_commands_terminates_with_code_0(self):
        code, _, _ = self.run_cli(["add do something", "list", "delete 1", "exit"])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()