import importlib
import json
import pathlib
import pprint
import re
import textwrap
import traceback
from urllib.parse import parse_qsl, urlencode
from urllib.request import HTTPError, Request, urlopen


def get_puzzle(args):

    url = "{host}/asterios/{team}/member/{member_id}".format(
        host=args.host, team=args.team, member_id=args.member_id
    )
    try:
        request = Request(url, method="GET")  # headers=dict(headers)
    except ValueError:
        exit("Error: Wrong url: `{}`".format(url))

    try:
        response = urlopen(request)  # timeout=120
    except HTTPError as error:
        msg = error.read().decode("utf-8")

        try:
            data = json.loads(msg)
        except:
            exit("Error: {}".format(msg))
        else:
            if data["exception"] == "LevelSet.DoneException":
                print("*** Victory ***")
                exit(0)
            else:
                exit(msg)

    return json.loads(response.read().decode("utf-8"))


class ShowCommand:

    def __init__(self, subparsers):
        show_parser = subparsers.add_parser(
            "show", aliases=["sh"], help="Show the current puzzle"
        )
        show_parser.add_argument("host", help="The Asterios server hostname")
        show_parser.add_argument("team", help="The name of your team or game")
        show_parser.add_argument("member_id", help="Your member id")

        show_parser.add_argument(
            "-b",
            "--backslash-interpretation",
            dest="format_func",
            action="store_const",
            default=pprint.pformat,
            const=self.format_new_line,
            help="Enable interpretation of backslash escapes",
        )
        show_parser.add_argument(
            "-t", "--tip", action="store_true", help="Show only the tip"
        )
        show_parser.add_argument(
            "-p", "--puzzle", action="store_true", help="Show only the puzzle"
        )

        show_parser.set_defaults(func=self)

    def __call__(self, args):
        """
        Show the current puzzle.
        """
        data = get_puzzle(args)
        if args.tip:
            print(data["tip"])
        elif args.puzzle:
            print(args.format_func(data["puzzle"]))
        else:
            print("TIPS")
            print(data["tip"])
            print("\nPUZZLE")
            print(args.format_func(data["puzzle"]))

    @classmethod
    def format_new_line(cls, obj, indent=0):
        prefix = "  " * indent
        if isinstance(obj, list):
            return textwrap.indent(
                "\n["
                + ",".join(cls.format_new_line(e, indent + 1) for e in obj)
                + "\n]",
                prefix,
            )
        elif isinstance(obj, dict):
            return textwrap.indent(
                "\n{"
                + (
                    ",".join(
                        "{}:{}".format(
                            cls.format_new_line(k, indent + 1),
                            cls.format_new_line(v, indent + 1),
                        )
                        for k, v in sorted(obj.items())
                    )
                )
                + "\n}",
                prefix,
            )
        return textwrap.indent("\n" + str(obj), prefix)


class SolveCommand:

    @staticmethod
    def _filter_traceback(tb):
        """
        Remove this module from traceback.
        """
        expected_line = '  File "{}"'.format(__file__)
        return [line for line in tb if not line.startswith(expected_line)]

    def __init__(self, subparsers):
        solve_parser = subparsers.add_parser(
            "solve",
            aliases=["so"],
            help="Solve the current puzzle reading a module containing a"
            " solve function and send the answer to the asterios server",
        )
        solve_parser.add_argument("host", help="The Asterios server hostname")
        solve_parser.add_argument("team", help="The name of your team or game")
        solve_parser.add_argument("member_id", help="Your member id")

        solve_parser.add_argument(
            "--module",
            help="The module name containing the solve function",
            default="asterios_solver",
        )
        solve_parser.set_defaults(func=self)

    def __call__(self, args):
        """
        Solve the current puzzle running `solve` function in args.module
        and send the answer to the asterios server.
        """

        module_solver = importlib.import_module(args.module)

        if not (hasattr(module_solver, "solve") and callable(module_solver.solve)):
            exit("Error: `solve` function not found in module {}".format(module_solver))

        puzzle = get_puzzle(args)["puzzle"]

        try:
            solution_or_error = module_solver.solve(puzzle)
        except Exception as error:
            tb = traceback.format_exception(type(error), error, error.__traceback__)
            tb = self._filter_traceback(tb)
            exit("".join(tb))

        try:
            solution = json.dumps(solution_or_error)
        except (ValueError, TypeError) as error:
            exit(
                "The solve function should return a"
                " JSON serializable object ({})".format(error)
            )

        url = "{host}/asterios/{team}/member/{member_id}".format(
            host=args.host, team=args.team, member_id=args.member_id
        )

        try:
            # headers=dict(headers)
            request = Request(url, method="POST")
        except ValueError:
            exit("Error: Wrong url: `{}`".format(url))
        else:
            request.data = solution.encode("utf-8")
            try:
                response = urlopen(request)  # timeout=120
            except HTTPError as error:
                exit(json.loads(error.read().decode("utf-8")))
            else:
                print(json.loads(response.read().decode("utf-8")))


class GenerateModuleCommand:

    def __init__(self, subparsers):
        parser = subparsers.add_parser(
            "generate_module",
            aliases=["ge"],
            help="Generate a module containing the solve function",
        )
        parser.add_argument(
            "--module",
            help="The module name containing the solve function without the `.py`",
            default="asterios_solver",
        )
        parser.set_defaults(func=self)

    def __call__(self, args):
        module_name = args.module
        if not module_name.endswith(".py"):
            module_name += ".py"

        path_to_module = pathlib.Path(module_name)
        if path_to_module.exists():
            exit("The file `{!s}` already exists".format(path_to_module))

        with path_to_module.open("w") as file:
            file.write(
                textwrap.dedent(
                    '''
                    def solve(puzzle):
                        """
                        You can execute this function using:

                            $ python3 -m asterios_client so ...
                        
                        See `$ python3 -m asterios_client so --help` 
                        """

                        puzzle_solved = '...'

                        return puzzle_solved
                    '''
                )
            )


