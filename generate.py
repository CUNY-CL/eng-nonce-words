#!/usr/bin/env python
"""First-pass English stimulus generation.

This simply generates potential stimuli and codes their basic properties.
Subsequent steps will remove actual lexical items and balance the stimuli
according to our assumptions about grammaticality.
"""

import csv
import dataclasses
import logging

from typing import Iterator, List, Optional, Set

import citylex


MONOSYLLABLES = "monosyllables.tsv"
DISYLLABLES = "disyllables.tsv"


# Onsets.
VOICELESS_STOPS = ["p", "t", "k"]
VOICED_STOPS = ["b", "d", "g"]
STOPS = VOICELESS_STOPS + VOICED_STOPS
# Leaving off /θ, ð/ because of the obvious spelling issues.
FRICATIVES = ["f", "s", "h"]
LIQUID = ["l", "r"]
# ŋ does not occur word-initially
NASALS = ["m", "n"]
SIMPLE_ONSETS = STOPS + ["s"] + FRICATIVES + NASALS

# For simplicity, I avoid the low-back vowels.
# I put aside /ɔɪ/ as it's pretty rare.
TENSE_NUCLEI = ["iː", "uː", "eɪ", "oʊ", "aɪ", "aʊ"]
# Of course some dialects have a tense variant of [æ].
LAX_NUCLEI = ["ɪ", "ʊ", "ɛ", "æ"]
NUCLEI = TENSE_NUCLEI + LAX_NUCLEI


# Codas.
NASAL_CODAS = ["m", "n", "ŋ"]
# I leave off voiceless variants to simplify the place checking.
STOP_CODAS = ["p", "t", "k"]
CODAS = ["s"] + NASAL_CODAS + STOP_CODAS


class Error(Exception):
    pass


@dataclasses.dataclass
class Monosyllable:
    onset: str
    nucleus: str
    coda: Optional[str]
    shape: Optional[str]

    @property
    def transcription(self) -> str:
        return self.onset + self.nucleus + self.coda

    @property
    def line(self) -> List[str]:
        return [
            self.onset,
            self.nucleus,
            self.coda,
            self.shape,
            self.transcription,
        ]


@dataclasses.dataclass
class Bisyllable:
    syl1: Monosyllable
    syl2: Monosyllable
    shape: str

    @property
    def transcription(self) -> str:
        return f"{self.syl1.transcription}.{self.syl2.transcription}"

    @property
    def line(self) -> List[str]:
        return [*self.syl1.line, *self.syl2.line, self.shape]


def _monosyllables() -> Iterator[Monosyllable]:
    # CVC.
    for onset in SIMPLE_ONSETS:
        for nucleus in NUCLEI:
            for coda in CODAS:
                if coda.startswith(onset[0]):
                    continue
                yield Monosyllable(onset, nucleus, coda, "CVC")
    # sCVC.
    # I could do sl here too, but not a lot gained from it.
    for stop in VOICELESS_STOPS:
        for nucleus in NUCLEI:
            for coda in CODAS:
                if stop == coda:
                    continue
                yield Monosyllable("s" + stop, nucleus, coda, "sCVC")
    # CwVC.
    for stop in STOPS:
        for nucleus in LAX_NUCLEI:
            for coda in CODAS:
                if stop == coda:
                    continue
                yield Monosyllable(stop + "w", nucleus, coda, "CwVC")
    # TlVC and TrVC.
    for stop in ["t", "d"]:
        for nucleus in NUCLEI:
            for coda in CODAS:
                if stop == coda:
                    continue
                yield Monosyllable(stop + "l", nucleus, coda, "TlVC")
                yield Monosyllable(stop + "ɹ", nucleus, coda, "TɹVC")
    # Prenasal and postnasal.
    for stop in STOPS:
        for coda in STOP_CODAS:
            if stop == coda:
                continue
            for nasal in NASALS:
                for nucleus in NUCLEI:
                    yield Monosyllable(stop + nasal, nucleus, coda, "CNVC")
                    yield Monosyllable(nasal + stop, nucleus, coda, "NCVC")


def main():
    cl = citylex.read_textproto("citylex.textproto")
    lexicon: Set[str] = set()
    for entry in cl.entry.values():
        for pron in entry.wikipron_us_pron:
            lexicon.add(pron.replace(" ", ""))
    logging.info(f"{len(lexicon):,} lexicon entries")
    filtered = 0
    with open(MONOSYLLABLES, "w") as sink:
        tsv_writer = csv.writer(sink, delimiter="\t")
        tsv_writer.writerow(
            ["onset", "nucleus", "coda", "shape", "transcription"]
        )
        for entry in _monosyllables():
            if entry.transcription in lexicon:
                logging.info(f"{entry.transcription} is lexical")
                filtered += 1
                continue
            tsv_writer.writerow(entry.line)
    logging.info(f"{filtered:,} monosyllables filtered")


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s: %(message)s", level="INFO")
    main()
