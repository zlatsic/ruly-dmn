import argparse
import json
import sys
from pathlib import Path

import ruly_dmn.dmn


def main():
    args = _create_parser().parse_args()
    dmn = ruly_dmn.dmn.parse(args.file, args.output_file)
    inputs = {k: json.loads(v) for k, v in
              (a.split('=', 2) for a in args.inputs)}
    print(args.goal, '=', dmn.decide(inputs, args.goal))


def _create_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('file', type=Path,
                        help='DMN file.')
    parser.add_argument('goal',
                        help='Name of the goal decision.')
    parser.add_argument('inputs', nargs='*',
                        help='Input value pairs in format '
                        '<input name>=<json string>, i.e a=1 b='"string"'.')
    parser.add_argument('--output-file', '-o', metavar='path', type=Path,
                        help='Output DMN file path, in case new rules are '
                        'added. Can be the same path as the input file. If '
                        'not set, DMN changes are not written anywhere.',
                        default=None)

    return parser


if __name__ == '__main__':
    sys.exit(main())
