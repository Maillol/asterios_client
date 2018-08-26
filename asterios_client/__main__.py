import argparse
from . import ShowCommand, GenerateModuleCommand, SolveCommand, SetConf


parser = argparse.ArgumentParser("Asterios client")
parser.set_defaults(func=lambda args: parser.print_help())
subparsers = parser.add_subparsers()
SetConf(subparsers)
ShowCommand(subparsers)
GenerateModuleCommand(subparsers)
SolveCommand(subparsers)
args = parser.parse_args()
args.func(args)
