import argparse
import json
import sys
from pathlib import Path

import ruly_dmn.dmn
from ruly_dmn.handlers.camunda_modeler import CamundaModelerHandler


def main():
    args = _create_parser().parse_args()
    handler = CamundaModelerHandler(args.file, args.output_file)
    dmn = ruly_dmn.dmn.DMN(handler)
    inputs = {}
    for k, v in (a.split('=', 2) for a in args.inputs):
        try:
            inputs[k] = json.loads(v)
        except json.JSONDecodeError:
            inputs[k] = v
    print(args.goal, '=', dmn.decide(inputs, args.goal))


def _create_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('file', type=Path,
                        help='DMN file.')
    parser.add_argument('goal',
                        help='Name of the goal decision.')
    parser.add_argument('inputs', nargs='*',
                        help='Input value pairs in format '
                        '<input name>=<value>, where value will be attempted '
                        'to be parsed as JSON, otherwise it will be '
                        'interpreted as a string. '
                        'i.e. a=1 b=xyz c=\'"{"json": "value"}"\'')
    parser.add_argument('--output-file', '-o', metavar='path', type=Path,
                        help='Output DMN file path, in case new rules are '
                        'added. Can be the same path as the input file. If '
                        'not set, DMN changes are not written anywhere.',
                        default=None)

    return parser


if __name__ == '__main__':
    sys.exit(main())
