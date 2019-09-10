import kaldi_edit_distance as ke

# int edit distance
a = [0, 0, 1, 0, 3, 4]
b = [0, 0, 1, 3, 5]
assert ke.edit_distance(a, b) == 2
e = ke.edit_distance_stats(a, b)
assert e.distance == 2
assert e.ins_num == 0
assert e.del_num == 1
assert e.sub_num == 1
assert e.ref_num == 6

a = ke.align(a, b, eps=-1)
assert a.alignment == [(0, 0), (0, 0), (1, 1), (0, -1), (3, 3), (4, 5)]


# str edit distance
assert ke.edit_distance(list("kitten"), list("sitting")) == 3
e2 = ke.edit_distance_stats(list("kitten"), list("sitting"))
assert e2.distance == 3
assert e2.ins_num == 1
assert e2.del_num == 0
assert e2.sub_num == 2
assert e2.ref_num == 6

a2 = ke.align(list("kitten"), list("sitting"), eps="<eps>")
assert a2.alignment == [('k', 's'), ('i', 'i'), ('t', 't'), ('t', 't'), ('e', 'i'), ('n', 'n'), ('<eps>', 'g')]

print("OK")
