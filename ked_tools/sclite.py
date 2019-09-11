#!/usr/bin/env python3
"""Clone of `sclite` command in SCTK."""

import argparse
import collections
import math
import numpy
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


def std1(xs):
    # NOTE: sclite uses ddof=1
    # https://github.com/usnistgov/SCTK/blob/master/src/sclite/statdist.c#L593
    return numpy.std(xs, ddof=1)


eps = "<kaldi-edit-distance-eps>"


class Sclite:
    def __init__(self, ref_dict, hyp_dict, name="", no_speaker=False):
        diff = set(ref_dict.keys()).difference(set(hyp_dict.keys()))
        if len(diff) > 0:
            raise ValueError(f"key mismatch: {diff}")

        self.name = name
        self.no_speaker = no_speaker
        self.all_stats = dict()
        self.all_corr = dict()
        self.total_stats = ke.ErrorStats()
        self.total_sent_err = 0
        self.spkr_stats = collections.defaultdict(ke.ErrorStats)
        self.spkr_sent_err = collections.defaultdict(int)
        self.spkr_corr = collections.defaultdict(int)
        self.spkr_sent = collections.defaultdict(int)
        self.spkr_ali = collections.defaultdict(dict)

        self.alignments = dict()
        for k, ref in ref_dict.items():
            hyp = hyp_dict[k]
            stats = ke.edit_distance_stats(ref, hyp)
            self.all_stats[k] = stats
            if no_speaker:
                spkr = "<no speaker info>"
            else:
                try:
                    spkr = k.split("-")[0]
                except ValueError:
                    spkr = "<no speaker info>"
            self.spkr_stats[spkr] += stats
            self.spkr_sent[spkr] += 1
            self.total_stats += stats
            if stats.distance > 0:
                self.total_sent_err += 1
                self.spkr_sent_err[spkr] += 1
            ali = ke.align(ref, hyp, eps=eps).alignment
            self.spkr_ali[spkr][k] = ali
            self.alignments[k] = ali
            corr = sum(1 for a, b in ali if a == b and a != eps)
            self.all_corr[k] = corr
            self.spkr_corr[spkr] += corr

    def speaker(self, speaker, rate=True):
        n_sent = self.spkr_sent[speaker]
        n_corr = self.spkr_corr[speaker]
        stats = self.spkr_stats[speaker]
        n = stats.ref_num
        return {
            "# Snt": n_sent,
            "# Wrd": n,
            "Corr": n_corr / n * 100 if rate else n_corr,
            "Sub": stats.sub_num / n * 100 if rate else stats.sub_num,
            "Del": stats.del_num / n * 100 if rate else stats.del_num,
            "Ins": stats.ins_num / n * 100 if rate else stats.ins_num,
            "Err": stats.distance / n * 100 if rate else stats.distance,
            "S.Err": self.spkr_sent_err[speaker] / n_sent * 100 if rate else self.spkr_sent_err[speaker],
        }

    def total(self, rate=True):
        n_sent = sum(self.spkr_sent.values())
        n_corr = sum(self.spkr_corr.values())
        stats = self.total_stats
        n = stats.ref_num
        return {
            "# Snt": n_sent,
            "# Wrd": n,
            "Corr": n_corr / n * 100 if rate else n_corr,
            "Sub": stats.sub_num / n * 100 if rate else stats.sub_num,
            "Del": stats.del_num / n * 100 if rate else stats.del_num,
            "Ins": stats.ins_num / n * 100 if rate else stats.ins_num,
            "Err": stats.distance / n * 100 if rate else stats.distance,
            "S.Err": self.total_sent_err / n_sent * 100 if rate else self.total_sent_err,
        }

    def error_rate(self):
        return self.total(rate=True)["Err"]

    def draw_table(self, rate):
        # FIXME: Corr is not exacly matched to sclite because of different alignment in Kaldi (see fjlp-fjlp-cen8-b)
        header = ["# Snt", "# Wrd", "Corr", "Sub", "Del", "Ins", "Err", "S.Err"]
        header_width = max(map(len, header))
        name_width = max(max(map(len, self.spkr_stats.keys())), len("Sum/Avg"))
        value_width = int(math.log10(max(self.total_stats.distance, self.total_stats.ref_num))) + 2  # for xxx.y
        value_width = max(value_width, header_width) + 1
        width = max(len(self.name) + 2, 5 + name_width + len(header) * (value_width))

        # filename
        s = "," + "-" * width + ".\n"
        if self.name != "":
            s += "|" + self.name.center(width) + "|\n"
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
        if not self.no_speaker:
            for i, (k, v) in enumerate(self.spkr_stats.items()):
                st = self.spkr_stats[k]
                s += "| " + k.ljust(name_width)

                total = self.speaker(speaker=k, rate=rate)
                s += "|" + f"{total['# Snt']}".rjust(value_width) + f"{total['# Wrd']}".rjust(value_width)
                s += " |"
                for h in header[2:]:
                    a = f"{total[h]:0.1f}" if rate else f"{total[h]}"
                    s += a.rjust(value_width)
                s += " |\n"
                if i + 1 < len(self.spkr_stats):
                    s += hsep
        s += "|" + "=" * width + "|\n"

        # sum
        s += "| " + "Sum".ljust(name_width)
        total = self.total(rate=rate)
        s += "|" + f"{total['# Snt']}".rjust(value_width) + f"{total['# Wrd']}".rjust(value_width)
        s += " |"
        for h in header[2:]:
            a = f"{total[h]:0.1f}" if rate else f"{total[h]}"
            s += a.rjust(value_width)
        s += " |\n"

        s += "|" + "=" * width + "|\n"

        spkr_stats = self.spkr_stats
        for name, func in [("Mean", numpy.mean), ("S.D.", std1), ("Median", numpy.median)]:
            s += "| " + name.ljust(name_width) + "|"
            n_sents = numpy.array([v for v in self.spkr_sent.values()])
            m = func(n_sents)
            s += f"{m:0.1f}".rjust(value_width)
            n_words = numpy.array([v.ref_num for v in spkr_stats.values()])
            m = func(n_words)
            s += f"{m:0.1f}".rjust(value_width)
            s += " |"
            if rate:
                m = func([v  for v in self.spkr_corr.values()] / n_words * 100)
                s += f"{m:0.1f}".rjust(value_width)
                m = func([v.sub_num for v in spkr_stats.values()] / n_words * 100)
                s += f"{m:0.1f}".rjust(value_width)
                m = func([v.del_num for v in spkr_stats.values()] / n_words * 100)
                s += f"{m:0.1f}".rjust(value_width)
                m = func([v.ins_num for v in spkr_stats.values()] / n_words * 100)
                s += f"{m:0.1f}".rjust(value_width)
                m = func([v.distance for v in spkr_stats.values()] / n_words * 100)
                s += f"{m:0.1f}".rjust(value_width)
                m = func([v for v in self.spkr_sent_err.values()] / n_sents * 100)
                s += f"{m:0.1f}".rjust(value_width)
            else:
                m = func([v for v in self.spkr_corr.values()])
                s += f"{m:0.1f}".rjust(value_width)
                m = func([v.sub_num for v in spkr_stats.values()])
                s += f"{m:0.1f}".rjust(value_width)
                m = func([v.del_num for v in spkr_stats.values()])
                s += f"{m:0.1f}".rjust(value_width)
                m = func([v.ins_num for v in spkr_stats.values()])
                s += f"{m:0.1f}".rjust(value_width)
                m = func([v.distance for v in spkr_stats.values()])
                s += f"{m:0.1f}".rjust(value_width)
                m = func([v for v in self.spkr_sent_err.values()])
                s += f"{m:0.1f}".rjust(value_width)
            s += " |\n"

        s += "`" + "-" * width + "'"
        return s

    def visualize_alignment(self, utt):
        s = f"id: ({utt})\n"
        ali = self.alignments[utt]
        st = self.all_stats[utt]
        s += f"Scores: (#C #S #D #I) {self.all_corr[utt]} {st.sub_num} {st.del_num} {st.ins_num}\n"
        rs = []
        hs = []
        ev = []
        for r, h in ali:
            pad = max(len(r), len(h))
            if r == h:
                pad = max(len(r), len(h))
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
        s += "REF:  " + " ".join(rs) + " \n"
        s += "HYP:  " + " ".join(hs) + " \n"
        s += "Eval: " + " ".join(ev) + " \n"
        return s

    def draw_alignment(self):
        # alignment
        s = ""
        for i, (spk, ali_dict) in enumerate(self.spkr_ali.items()):
            s += f"Speaker sentences   {i}:  " + spk + f"   #utts: {len(ali_dict)}\n"
            for utt, ali in ali_dict.items():
                s += self.visualize_alignment(utt)
                s += "\n"
        return s


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
    sc = Sclite(ref_dict, hyp_dict, name=args.hyp[0])

    global_width = 80
    for rate in (True, False):
        print("\n\n")
        print("SYSTEM SUMMARY PERCENTAGES by SPEAKER".center(global_width))
        print("\n")
        for line in sc.draw_table(rate=rate).split("\n"):
            print(line.center(global_width))

    print("\n\n		DUMP OF SYSTEM ALIGNMENT STRUCTURE")

    print("\nSystem name:   " + args.hyp[0])

    print("\nSpeakers: ")

    for i, k in enumerate(sc.spkr_stats):
        print(f"{i:5d}:  {k}")

    print("")
    print(sc.draw_alignment())


if __name__ == "__main__":
    main()
