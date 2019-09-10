#!/usr/bin/env python3
"""Clone of `sclite` command in SCTK."""

import argparse
import kaldi_edit_distance as ke


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--ref", "-r", nargs="+", help="ref file and type", required=True)
parser.add_argument("--hyp", "-h", nargs="+", help="hyp file and type", required=True)
parser.add_argument("--output", "-o", nargs=2, default=["all", "stdout"], help="output option")
parser.add_argument("--input", "-i", default="rm", choices=["rm"], help="input option")

args = parser.parse_args()
print(args)

# validate args
assert args.input == "rm", "unsupported"
assert args.output == ["all", "stdout"], "unsupported"
if len(args.ref) > 1:
    assert len(args.ref) == 2 and args.ref[1] == "trn", "unsupported"
if len(args.hyp) > 1:
    assert len(args.ref) == 2 and args.ref[1] == "trn", "unsupported"


def load_trn(path):
    ret = dict()
    with open(path) as f:
        for line in f:
            xs = line.strip().split()
            key = xs[-1]
            ret[xs[-1]] = xs[:-1]
    return ret


ref_dict = load_trn(args.ref[0])
hyp_dict = load_trn(args.hyp[0])
diff = set(ref_dict.keys()).difference(set(hyp_dict.keys()))
if len(diff) > 0:
    raise ValueError(f"key mismatch: {diff}")

for k, ref in ref_dict.items():
    hyp = hyp_dict[k]
    stat = ke.edit_distance_stat(ref, hyp)
