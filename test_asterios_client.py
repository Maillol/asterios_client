import argparse
from io import StringIO
import subprocess
import sys
import textwrap
import unittest
import unittest.mock

from asterios_client import get_puzzle, ShowCommand


class BaseTestClient(unittest.TestCase):

    command_class = None

    def setUp(self):
        self._parser = argparse.ArgumentParser()
        self._stdout = StringIO()
        subparsers = self._parser.add_subparsers()
        self.command_class(subparsers)

    def execute_cmd(self, *cmd_line_args):
        with unittest.mock.patch("sys.stdout", self._stdout):
            args = self._parser.parse_args(cmd_line_args)
            args.func(args)


class TestShowCommand(BaseTestClient):

    command_class = ShowCommand

    def execute_cmd(self, *cmd_line_args):
        value = {
            "tip": "the tip",
            "puzzle": {"key_1": "the\npuzzle\t1", "key_2": "the\npuzzle\t2"},
        }
        with unittest.mock.patch("asterios_client.get_puzzle", return_value=value):
            super().execute_cmd(*cmd_line_args)

    def test_show_should_display_tip_and_puzzle(self):
        self.execute_cmd("sh", "a", "b", "c")
        self.assertEqual(
            self._stdout.getvalue(),
            textwrap.dedent("""
                TIPS
                the tip

                PUZZLE
                {'key_1': 'the\\npuzzle\\t1', 'key_2': 'the\\npuzzle\\t2'}
                """).lstrip()
        )

    def test_show_with_p_option_should_only_display_puzzle(self):
        self.execute_cmd("sh", "a", "b", "c", "-p")
        self.assertEqual(
            self._stdout.getvalue(),
            "{'key_1': 'the\\npuzzle\\t1', 'key_2': 'the\\npuzzle\\t2'}\n",
        )

    def test_show_with_p_and_b_options_should_only_display_puzzle_with_new_line_interpreted(
        self
    ):
        self.execute_cmd("sh", "a", "b", "c", "-p", "-b")
        self.assertEqual(
            self._stdout.getvalue(),
            textwrap.dedent("""
                {
                  key_1:
                  the
                  puzzle\t1,
                  key_2:
                  the
                  puzzle\t2
                }
                """)
        )

    def test_show_with_t_option_should_only_display_tip(self):
        self.execute_cmd("sh", "a", "b", "c", "-t")
        self.assertEqual(self._stdout.getvalue(), "the tip\n")
