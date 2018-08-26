import importlib
import configparser
import json
import pathlib
import pprint
import re
import textwrap
import traceback
from urllib.parse import parse_qsl, urlencode
from urllib.request import HTTPError, Request, urlopen


class SetConf:

    FILE_NAME = "asterios_client.ini"
    KEYS = ("host", "team", "member_id")

    def __init__(self, subparsers):
        parser = subparsers.add_parser(
            "set_conf",
            aliases=["sc"],
            help="Set the asterios_client configuration file",
        )

        parser.add_argument("--host", help="The Asterios server hostname")
        parser.add_argument("--team", help="The name of your team")
        parser.add_argument("--member-id", help="Your member id")
        parser.set_defaults(func=self)

    def __call__(self, args):
        """
        Show the current puzzle.
        """
        config = self.current_config(check=False)
        for key in self.KEYS:
            value = getattr(args, key, None)
            if value is not None:
                config["DEFAULT"][key] = value

        with open(self.FILE_NAME, "w") as configfile:
            config.write(configfile)

    @classmethod
    def current_config(cls, check=True):
        """
        Read the current configuration file.
        """
        config = configparser.ConfigParser()
        config.read(cls.FILE_NAME)

        if check:
            for key in cls.KEYS:
                if key not in config["DEFAULT"]:
                    exit(
                        "You should edit your config using asterios_client set_conf --{}".format(
                            key.replace("_", "-")
                        )
                    )

        return config


def get_puzzle(conf):
    """
    Get the current puzzle from asterios server.
    """

    url = "{host}/asterios/{team}/member/{member_id}/puzzle".format(**conf["DEFAULT"])

    try:
        request = Request(url, method="PUT")  # headers=dict(headers)
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


def _filter_traceback(tb):
    """
    Remove this module from traceback.
    """
    expected_line = '  File "{}"'.format(__file__)
    return [line for line in tb if not line.startswith(expected_line)]


def send_answer(solve_func, conf):
    puzzle = get_puzzle(conf)["puzzle"]

    try:
        solution_or_error = solve_func(puzzle)
    except Exception as error:
        tb = traceback.format_exception(type(error), error, error.__traceback__)
        tb = _filter_traceback(tb)
        exit("".join(tb))

    try:
        solution = json.dumps(solution_or_error)
    except (ValueError, TypeError) as error:
        exit(
            "The solve function should return a"
            " JSON serializable object ({})".format(error)
        )

    url = "{host}/asterios/{team}/member/{member_id}/solve".format(**conf["DEFAULT"])

    try:
        # headers=dict(headers)
        request = Request(url, method="PUT")
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


class ShowCommand:
    def __init__(self, subparsers):
        show_parser = subparsers.add_parser(
            "show", aliases=["sh"], help="Show the current puzzle"
        )

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
        conf = SetConf.current_config()
        data = get_puzzle(conf)
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
    def __init__(self, subparsers):
        solve_parser = subparsers.add_parser(
            "solve",
            aliases=["so"],
            help="Solve the current puzzle reading a module containing a"
            " solve function and send the answer to the asterios server",
        )

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
        conf = SetConf.current_config()
        module_solver = importlib.import_module(args.module)
        if not (hasattr(module_solver, "solve") and callable(module_solver.solve)):
            exit("Error: `solve` function not found in module {}".format(module_solver))
        send_answer(module_solver.solve, conf)


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
        conf = SetConf.current_config()
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


                    if __name__ == '__main__':
                        from asterios_client import send_answer

                        CONFIG = {{
                            'DEFAULT': {{
                                'host': {host!r},
                                'team': {team!r},
                                'member_id': {member_id!r}
                            }}
                        }}

                        send_answer(solve, CONFIG)
                    '''.format(
                        **conf["DEFAULT"]
                    )
                )
            )
