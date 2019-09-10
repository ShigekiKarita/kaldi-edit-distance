#!/usr/bin/env python3
"""Clone of `sclite` command in SCTK."""

import argparse
import collections
import math
import kaldi_edit_distance as ke


def load_trn(path):
    ret = dict()
    with open(path) as f:
        for line in f:
            # line looks like: "O N E <space> F I F T Y (fjlp-fjlp-cen3-b)"
            xs = line.strip().split()
            key = xs[-1][1:-1]  # remove paren
            ret[key] = xs[:-1]
    return ret


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--ref", "-r", nargs="+", help="ref file and type", required=True)
    parser.add_argument("--hyp", "-h", nargs="+", help="hyp file and type", required=True)
    parser.add_argument("--output", "-o", nargs=2, default=["all", "stdout"], help="output option")
    parser.add_argument("--input", "-i", default="rm", choices=["rm"], help="input option")

    args = parser.parse_args()

    # validate args
    assert args.input == "rm", "unsupported"
    assert args.output == ["all", "stdout"], "unsupported"
    if len(args.ref) > 1:
        assert len(args.ref) == 2 and args.ref[1] == "trn", "unsupported"
    if len(args.hyp) > 1:
        assert len(args.ref) == 2 and args.ref[1] == "trn", "unsupported"


    ref_dict = load_trn(args.ref[0])
    hyp_dict = load_trn(args.hyp[0])
    diff = set(ref_dict.keys()).difference(set(hyp_dict.keys()))
    if len(diff) > 0:
        raise ValueError(f"key mismatch: {diff}")

    all_stats = dict()
    all_corr = dict()
    total_stats = ke.ErrorStats()
    total_sent_err = 0
    spkr_stats = collections.defaultdict(ke.ErrorStats)
    spkr_sent_err = collections.defaultdict(int)
    spkr_corr = collections.defaultdict(int)
    spkr_sent = collections.defaultdict(int)
    spkr_ali = collections.defaultdict(dict)

    alignments = dict()
    eps = "<kaldi-edit-distance-eps>"
    for k, ref in ref_dict.items():
        hyp = hyp_dict[k]
        stats = ke.edit_distance_stats(ref, hyp)
        all_stats[k] = stats
        spkr = k.split("-")[0]
        spkr_stats[spkr] += stats
        spkr_sent[spkr] += 1
        total_stats += stats
        if stats.distance > 0:
            total_sent_err += 1
            spkr_sent_err[spkr] += 1
        ali = ke.align(ref, hyp, eps=eps).alignment
        spkr_ali[spkr][k] = ali
        alignments[k] = ali
        corr = sum(1 for a, b in ali if a == b and a != eps)
        all_corr[k] = corr
        spkr_corr[spkr] += corr

    def table(rate):
        # FIXME: Corr is not exacly matched to sclite because of different alignment in Kaldi (see fjlp-fjlp-cen8-b)
        hypfile = args.hyp[0]
        header = ["# Snt", "# Wrd", "Corr", "Sub", "Del", "Ins", "Err", "S.Err"]
        header_width = max(map(len, header))
        name_width = max(max(map(len, spkr_stats.keys())), len("Sum/Avg"))
        value_width = int(math.log10(max(total_stats.distance, total_stats.ref_num))) + 2  # for xxx.y
        value_width = max(value_width, header_width) + 2
        width = max(len(hypfile) + 2, 5 + name_width + len(header) * (value_width))

        # filename
        s = "," + "-" * width + ".\n"
        s += "|" + hypfile.center(width) + "|\n"
        s += "|" + "-" * width + "|\n"

        # header
        s += "| " + "SPKR".ljust(name_width)
        s += "| " + "# Snt".center(value_width) + "# Wrd".center(value_width)
        s += "|"
        hsep = "|-" + "-" * name_width
        hsep += "+-" + "-" * value_width + "-" * value_width
        hsep += "+-"
        for h in header[2:]:
            s += h.rjust(value_width)
            hsep += "-" * value_width
        s += " |\n"
        hsep += "|\n"

        # hsep = "|" + "-" * width + "|\n"  # TODO: use +
        s += hsep

        # speaker stats
        for i, (k, v) in enumerate(spkr_stats.items()):
            st = spkr_stats[k]
            s += "| " + k.ljust(name_width)
            s += "|"
            s += f"{spkr_sent[k]}".rjust(value_width) + f"{st.ref_num}".rjust(value_width)
            s += " |"
            if rate:
                s += f"{spkr_corr[k] / st.ref_num * 100:0.1f}".rjust(value_width)
                s += f"{st.sub_num / st.ref_num * 100:0.1f}".rjust(value_width)
                s += f"{st.del_num / st.ref_num * 100:0.1f}".rjust(value_width)
                s += f"{st.ins_num / st.ref_num * 100:0.1f}".rjust(value_width)
                s += f"{st.distance / st.ref_num * 100:0.1f}".rjust(value_width)
                s += f"{spkr_sent_err[k] / spkr_sent[k] * 100:0.1f}".rjust(value_width)
            else:
                s += f"{spkr_corr[k]}".rjust(value_width)
                s += f"{st.sub_num}".rjust(value_width)
                s += f"{st.del_num}".rjust(value_width)
                s += f"{st.ins_num}".rjust(value_width)
                s += f"{st.distance}".rjust(value_width)
                s += f"{spkr_sent_err[k]}".rjust(value_width)
            s += " |\n"
            if i + 1 < len(spkr_stats):
                s += hsep
        s += "|" + "=" * width + "|\n"

        # sum
        s += "| " + "Sum".ljust(name_width)
        n_sent = sum(spkr_sent.values())
        s += "|" + f"{n_sent}".rjust(value_width) + " " + f"{total_stats.ref_num}".center(value_width)
        s += "|"
        n_corr = sum(spkr_corr.values())
        if rate:
            s += f"{n_corr / total_stats.ref_num * 100:0.1f}".rjust(value_width)
            s += f"{total_stats.sub_num / total_stats.ref_num * 100:0.1f}".rjust(value_width)
            s += f"{total_stats.del_num / total_stats.ref_num * 100:0.1f}".rjust(value_width)
            s += f"{total_stats.ins_num / total_stats.ref_num * 100:0.1f}".rjust(value_width)
            s += f"{total_stats.distance / total_stats.ref_num * 100:0.1f}".rjust(value_width)
            s += f"{total_sent_err / n_sent * 100:0.1f}".rjust(value_width)
        else:
            s += f"{n_corr}".rjust(value_width)
            s += f"{total_stats.sub_num}".rjust(value_width)
            s += f"{total_stats.del_num}".rjust(value_width)
            s += f"{total_stats.ins_num}".rjust(value_width)
            s += f"{total_stats.distance}".rjust(value_width)
            s += f"{total_sent_err}".rjust(value_width)
        s += " |\n"

        s += "|" + "=" * width + "|\n"

        import numpy
        def std1(xs):
            # NOTE: sclite uses ddof=1
            # https://github.com/usnistgov/SCTK/blob/master/src/sclite/statdist.c#L593
            return numpy.std(xs, ddof=1)
        for name, func in [("Mean", numpy.mean), ("S.D.", std1), ("Median", numpy.median)]:
            s += "| " + name.ljust(name_width) + "|"
            n_sents = numpy.array([v for v in spkr_sent.values()])
            m = func(n_sents)
            s += f"{m:0.1f}".rjust(value_width)
            n_words = numpy.array([v.ref_num for v in spkr_stats.values()])
            m = func(n_words)
            s += f"{m:0.1f}".rjust(value_width)
            s += " |"
            if rate:
                m = func([v  for v in spkr_corr.values()] / n_words * 100)
                s += f"{m:0.1f}".rjust(value_width)
                m = func([v.sub_num for v in spkr_stats.values()] / n_words * 100)
                s += f"{m:0.1f}".rjust(value_width)
                m = func([v.del_num for v in spkr_stats.values()] / n_words * 100)
                s += f"{m:0.1f}".rjust(value_width)
                m = func([v.ins_num for v in spkr_stats.values()] / n_words * 100)
                s += f"{m:0.1f}".rjust(value_width)
                m = func([v.distance for v in spkr_stats.values()] / n_words * 100)
                s += f"{m:0.1f}".rjust(value_width)
                m = func([v for v in spkr_sent_err.values()] / n_sents * 100)
                s += f"{m:0.1f}".rjust(value_width)
            else:
                m = func([v for v in spkr_corr.values()])
                s += f"{m:0.1f}".rjust(value_width)
                m = func([v.sub_num for v in spkr_stats.values()])
                s += f"{m:0.1f}".rjust(value_width)
                m = func([v.del_num for v in spkr_stats.values()])
                s += f"{m:0.1f}".rjust(value_width)
                m = func([v.ins_num for v in spkr_stats.values()])
                s += f"{m:0.1f}".rjust(value_width)
                m = func([v.distance for v in spkr_stats.values()])
                s += f"{m:0.1f}".rjust(value_width)
                m = func([v for v in spkr_sent_err.values()])
                s += f"{m:0.1f}".rjust(value_width)
            s += " |\n"

        s += "`" + "-" * width + "'"

        print(s)



    print("\n\n\n                     SYSTEM SUMMARY PERCENTAGES by SPEAKER                      \n")

    table(rate=True)

    print("\n\n\n                     SYSTEM SUMMARY PERCENTAGES by SPEAKER                      \n")

    table(rate=False)

    print("\n\n		DUMP OF SYSTEM ALIGNMENT STRUCTURE")

    print("\nSystem name:   " + args.hyp[0])

    print("\nSpeakers: ")

    for i, k in enumerate(spkr_stats):
        print(f"{i:5d}:  {k}")

    print("")

    # alignment
    for i, (spk, ali_dict) in enumerate(spkr_ali.items()):
        print(f"Speaker sentences   {i}:  " + spk + f"   #utts: {len(ali_dict)}")
        for utt, ali in ali_dict.items():
            print(f"id: ({utt})")
            st = all_stats[utt]
            print(f"Scores: (#C #S #D #I) {all_corr[utt]} {st.sub_num} {st.del_num} {st.ins_num}")
            rs = []
            hs = []
            ev = []
            for r, h in ali:
                pad = max(len(r), len(h))
                if r == h:
                    pad = max(len(r), len(h))
                    # TODO: pad
                    rs.append(r.lower().ljust(pad))
                    hs.append(h.lower().ljust(pad))
                    ev.append("".ljust(pad))
                elif r == eps:
                    pad = len(h)
                    rs.append("*" * pad)
                    hs.append(h.upper().ljust(pad))
                    ev.append("I".ljust(pad))
                elif h == eps:
                    pad = len(r)
                    rs.append(r.upper().ljust(pad))
                    hs.append("*" * pad)
                    ev.append("D".ljust(pad))
                else:
                    pad = max(len(r), len(h))
                    rs.append(r.upper().ljust(pad))
                    hs.append(h.upper().ljust(pad))
                    ev.append("S".ljust(pad))

            print("REF:  " + " ".join(rs) + " ")
            print("HYP:  " + " ".join(hs) + " ")
            print("Eval: " + " ".join(ev) + " ")
            print("")


if __name__ == "__main__":
    main()
