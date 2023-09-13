#!/usr/bin/env python
"""First-pass English stimulus generation.

This simply generates potential stimuli and codes their basic properties.
Subsequent steps will remove actual lexical items and balance the stimuli
according to our assumptions about grammaticality.
"""

import dataclasses
import logging

from typing import List, Optional, Set

import citylex


MONOSYLLABLES = "monosyllables.tsv"
DISYLLABLES = "disyllables.tsv"


class Error(Exception):
    pass


@dataclasses.dataclass
class Monosyllable:
    onset: str
    nucleus: str
    coda: Optional[str]
    shape: Optional[str]

    @property
    def line(self) -> List[str]:
        return [self.onset, self.nucleus, self.coda, self.shape]


@dataclasses.dataclass
class Bisyllable:
    syl1: Monosyllable
    syl2: Monosyllable
    shape: str

    @property
    def line(self) -> List[str]:
        return [*self.syl1.line, *self.syl2.line, self.shape]


def main():
    cl = citylex.read_textproto("citylex.textproto")
    lexicon: Set[
        str
    ] = set()  # We store them as strings because lists aren't hashable.
    for entry in cl.entry.values():
        for pron in entry.wikipron_us_pron:
            lexicon.add(pron)
    logging.info(f"{len(lexicon):,} lexicon entries")
    """
    with open(MONOSYLLABLES, "w") as sink:
        tsv_writer = csv.writer(sink, delimiter="\t")
        tsv_writer.writerow(["onset", "nucleus", "coda", "shape"])
        for entry in _monosyllables():
            tsv_writer.writerow(entry.line)
    """


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s: %(message)s", level="INFO")
    main()
