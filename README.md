# kaldi-edit-distance

Wrap Kaldi's edit distance for python

## Install

```
pip install git+https://github.com/ShigekiKarita/kaldi-edit-distance
```

## Usage

as a library

```python
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
```

as a sclite clone

```
$ sclite.py -r ./test/ref.trn trn -h ./test/hyp.trn trn -i rm -o all stdout




                     SYSTEM SUMMARY PERCENTAGES by SPEAKER                      
,--------------------------------------------------------------------.
|                           ./test/hyp.trn                           |
|--------------------------------------------------------------------|
| SPKR   |  # Snt  # Wrd |   Corr    Sub    Del    Ins    Err  S.Err |
|--------|---------------|-------------------------------------------|
| fcaw   |     13    237 |   94.9    4.2    0.8    0.0    5.1   46.2 |
|--------|---------------|-------------------------------------------|
| fjlp   |     13    242 |   94.2    2.9    2.5    0.8    6.2   46.2 |
|--------|---------------|-------------------------------------------|
| fvap   |     13    274 |   92.7    4.0    3.3    0.4    7.7   61.5 |
|--------|---------------|-------------------------------------------|
| marh   |     13    276 |   94.6    3.6    1.8    1.1    6.5   38.5 |
|--------|---------------|-------------------------------------------|
| mdms2  |     13    274 |   93.8    4.7    1.5    0.4    6.6   61.5 |
|--------|---------------|-------------------------------------------|
| menk   |     13    258 |   95.7    1.9    2.3    0.8    5.0   38.5 |
|--------|---------------|-------------------------------------------|
| miry   |     13    274 |   93.4    2.9    3.6    0.7    7.3   38.5 |
|--------|---------------|-------------------------------------------|
| mjgm   |     13    226 |   87.2    3.1    9.7    0.0   12.8   38.5 |
|--------|---------------|-------------------------------------------|
| mjwl   |     13    241 |   85.1    2.1   12.9    0.8   15.8   61.5 |
|--------|---------------|-------------------------------------------|
| mmxg   |     13    263 |   90.5    4.9    4.6    1.9   11.4   61.5 |
|====================================================================|
| Sum    |    130   2565 |   92.3    3.5    4.2    0.7    8.3   49.2 |
|====================================================================|
| Mean   |   13.0  256.5 |   92.2    3.4    4.3    0.7    8.4   49.2 |
| S.D.   |    0.0   17.6 |    3.4    1.0    3.7    0.5    3.4   10.4 |
| Median |   13.0  260.5 |   93.6    3.4    2.9    0.8    6.9   46.2 |
`--------------------------------------------------------------------'



                     SYSTEM SUMMARY PERCENTAGES by SPEAKER                      
,--------------------------------------------------------------------.
|                           ./test/hyp.trn                           |
|--------------------------------------------------------------------|
| SPKR   |  # Snt  # Wrd |   Corr    Sub    Del    Ins    Err  S.Err |
|--------|---------------|-------------------------------------------|
| fcaw   |     13    237 |    225     10      2      0     12      6 |
|--------|---------------|-------------------------------------------|
| fjlp   |     13    242 |    228      7      6      2     15      6 |
|--------|---------------|-------------------------------------------|
| fvap   |     13    274 |    254     11      9      1     21      8 |
|--------|---------------|-------------------------------------------|
| marh   |     13    276 |    261     10      5      3     18      5 |
|--------|---------------|-------------------------------------------|
| mdms2  |     13    274 |    257     13      4      1     18      8 |
|--------|---------------|-------------------------------------------|
| menk   |     13    258 |    247      5      6      2     13      5 |
|--------|---------------|-------------------------------------------|
| miry   |     13    274 |    256      8     10      2     20      5 |
|--------|---------------|-------------------------------------------|
| mjgm   |     13    226 |    197      7     22      0     29      5 |
|--------|---------------|-------------------------------------------|
| mjwl   |     13    241 |    205      5     31      2     38      8 |
|--------|---------------|-------------------------------------------|
| mmxg   |     13    263 |    238     13     12      5     30      8 |
|====================================================================|
| Sum    |    130   2565 |   2368     89    107     18    214     64 |
|====================================================================|
| Mean   |   13.0  256.5 |  236.8    8.9   10.7    1.8   21.4    6.4 |
| S.D.   |    0.0   17.6 |   21.4    2.8    8.6    1.4    8.0    1.4 |
| Median |   13.0  260.5 |  242.5    9.0    7.5    2.0   19.0    6.0 |
`--------------------------------------------------------------------'


		DUMP OF SYSTEM ALIGNMENT STRUCTURE

System name:   ./test/hyp.trn

Speakers:
    0:   fcaw
    1:   fjlp
    2:   fvap
    3:   marh
    4:   mdms2
    5:   menk
    6:   miry
    7:   mjgm
    8:   mjwl
    9:   mmxg

Speaker sentences     0:  fcaw   #utts: 13
id: (fcaw-fcaw-an406-b)
Scores: (#C #S #D #I) 24 1 0 0
REF:  r u b o u t <space> g <space> M <space> e <space> f <space> t h r e e <space> n i n e
HYP:  r u b o u t <space> g <space> N <space> e <space> f <space> t h r e e <space> n i n e
Eval:                               S                                                      


id: (fcaw-fcaw-an407-b)
Scores: (#C #S #D #I) 19 0 0 0
REF:  e r a s e <space> c <space> q <space> q <space> f <space> s e v e n
HYP:  e r a s e <space> c <space> q <space> q <space> f <space> s e v e n
Eval:                                                                    

...
```

## Diffs from original sclite

- Corr is different becuase sclite and kaldi's alignment are different (see fjlp-fjlp-cen8-b in test/{result.txt,expect.txt})
- Table format is slightly different from original sclite

see [test/result.diff](test/result.diff) for actual diff created by
```bash
sclite -r ./test/ref.trn trn -h ./test/hyp.trn trn -i rm -o all stdout > expect.txt
sclite.py -r ./test/ref.trn trn -h ./test/hyp.trn trn -i rm -o all stdout > actual.txt
diff expect.txt actual.txt
```
