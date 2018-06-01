import argparse
from . import ShowCommand, GenerateModuleCommand, SolveCommand


parser = argparse.ArgumentParser()
parser.set_defaults(func=lambda args: parser.print_help())
subparsers = parser.add_subparsers()
ShowCommand(subparsers)
GenerateModuleCommand(subparsers)
SolveCommand(subparsers)
args = parser.parse_args()
args.func(args)
