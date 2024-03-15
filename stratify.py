#!/usr/bin/env python
"""Implements stratified sampling for English.

This produces lsts of 60 words with the same gross properties. For each
list:

* 30 of the words are monosyllables; 30 are disyllables.
* 30 of the words are expected to be well-formed; 30 of the words are
  expected to be ill-formed.

The stratification is rather complex.

To balance out grammaticality of monosyllables, we select:

 x 5  CVC examples
 x 4 sCVC examples
 ? 4 CwVC examples
 x 2 TɹVC examples
 * 5 TlVC examples
 * 5 NCVC examples
 * 5 CNVC examples

For disyllables, we select:

 x 5  CVC.CVC, +OVA examples
 x 4  CVC.CVC, +NPA examples
 x 3 TɹVC.CVC, +OVA examples
 x 3 TɹVC.CVC, +NPA examples
 * 4  CVC.CVC, -OVA examples
 * 4  CVC.CVC, -NPA examples
** 4 TlVC.CVC, -OVA examples
** 3 TlVC.CVC, -NPA examples
"""


import collections
import csv
import random
import string

from typing import Dict, Iterator, List, Tuple


SEED = 1568
MONOSYLLABLES = "monosyllables.tsv"
DISYLLABLES = "disyllables.tsv"
LIST_PATH = "eng-list-%02d.tsv"
N_LISTS = 16  # We can make a lot of these, so why not.
# Because lexical filtration is not a sure thing, we will have to cannibalize
# examples so we need more lists than we plan to run.


def _proc_file(path: str) -> Iterator[Tuple[str, Dict]]:
    with open(path, "r") as source:
        for row in csv.DictReader(source, delimiter="\t"):
            shape = row["shape"]
            scc = row.get("syllable.contact.code")
            if scc:
                shape = f"{shape}, {row['syllable.contact.code']}"
            yield shape, row


def _chunks(lst: List[str], size: int, chunks: int):
    for chunk in range(chunks):
        start = size * chunk
        yield lst[start : start + size]


def main() -> None:
    random.seed(SEED)  # Same result every time.
    lsts = [[] for _ in range(N_LISTS)]
    by_shape = collections.defaultdict(list)
    for shape, row in _proc_file(MONOSYLLABLES):
        by_shape[shape].append(row)
    for shape, row in _proc_file(DISYLLABLES):
        by_shape[shape].append(row)
    for shape, entries in by_shape.items():
        elist = list(entries)
        # Special cases for sizing; it all adds up to 60.
        # We give slight preference for querying OVA over NPA.
        if shape == "CVC":
            size = 5
        elif shape == "sCVC":
            size = 4
        elif shape == "CwVC":
            size = 4
        elif shape == "TɹVC":
            size = 2
        elif shape == "TlVC":
            size = 5
        elif shape == "NCVC":
            size = 5
        elif shape == "CNVC":
            size = 5
        elif shape == "CVC.CVC, +OVA":
            size = 5
        elif shape == "CVC.CVC, +NPA":
            size = 4
        elif shape == "TɹVC.CVC, +OVA":
            size = 3
        elif shape == "TɹVC.CVC, +NPA":
            size = 3
        elif shape == "CVC.CVC, -OVA":
            size = 4
        elif shape == "CVC.CVC, -NPA":
            size = 4
        elif shape == "TlVC.CVC, -OVA":
            size = 4
        elif shape == "TlVC.CVC, -NPA":
            size = 3
        else:
            continue
        # This will fail if N_LISTS is larger than can be sustained.
        assert len(elist) >= size * N_LISTS, (shape, len(elist))
        random.shuffle(elist)
        for i, chunk in enumerate(_chunks(elist, size, N_LISTS)):
            lsts[i].extend(chunk)
    # Randomize list order.
    for lst in lsts:
        random.shuffle(lst)
    for index, lst in enumerate(lsts, 1):
        with open(LIST_PATH % index, "w") as sink:
            writer = csv.DictWriter(
                sink, delimiter="\t", fieldnames=row.keys()
            )
            writer.writeheader()
            assert len(lst) == 60, len(lst)
            writer.writerows(lst)


if __name__ == "__main__":
    main()
