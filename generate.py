#!/usr/bin/env python
"""First-pass English stimulus generation.

This simply generates potential stimuli and codes their basic properties.
Subsequent steps will remove actual lexical items and balance the stimuli
according to our assumptions about grammaticality.
"""

import csv
import dataclasses
import logging

from typing import Iterator, List, Set

import citylex


MONOSYLLABLES = "monosyllables.tsv"
BISYLLABLES = "disyllables.tsv"


# Onsets.
VOICELESS_STOPS = ["p", "t", "k"]
VOICED_STOPS = ["b", "d", "g"]
STOPS = VOICELESS_STOPS + VOICED_STOPS
STOPS_PLUS_S = STOPS + ["s"]
LIQUID = ["l", "r"]
# ŋ does not occur word-initially
NASALS = ["m", "n"]
SIMPLE_ONSETS = STOPS + NASALS
SIMPLE_ONSETS_PLUS_S = STOPS + NASALS + ["s"]

# I put aside /ɔɪ/ as it's pretty rare.
TENSE_NUCLEI = ["iː", "uː", "eɪ", "oʊ", "ɑ", "aɪ", "aʊ"]
# Of course some dialects have a tense variant of [æ].
LAX_NUCLEI = ["ɪ", "ʊ", "ɛ", "æ"]
NUCLEI = TENSE_NUCLEI + LAX_NUCLEI


# Codas.
NASAL_CODAS = ["m", "n", "ŋ"]
STOP_CODAS = ["p", "t", "k"]
SIMPLE_CODAS = NASAL_CODAS + STOP_CODAS
SIMPLE_CODAS_PLUS_S = SIMPLE_CODAS + ["s"]

# Place coding; add segments as needed.
PLACE = {
    "p": "labial",
    "t": "coronal",
    "k": "velar",
    "b": "labial",
    "d": "coronal",
    "g": "velar",
    "s": "coronal",
    "m": "labial",
    "n": "coronal",
    "ŋ": "velar",
}


class Error(Exception):
    pass


@dataclasses.dataclass
class Monosyllable:
    onset: str
    nucleus: str
    coda: str
    shape: str

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
class Disyllable:
    syl1: Monosyllable
    syl2: Monosyllable

    @property
    def shape(self) -> str:
        return f"{self.syl1.shape}.{self.syl2.shape}"

    @property
    def syllable_contact_code(self) -> str:
        coda = self.syl1.coda
        onset = self.syl2.onset
        if coda in NASAL_CODAS:
            # Check nasal place agreement (see Gorman 2013:75).
            if PLACE[coda] == PLACE[onset]:
                return "+NPA"
            else:
                return "-NPA"
        else:
            # Check obstruent voice assimilation (see Gorman 2013:74).
            coda_coding = coda == "s" or coda in VOICELESS_STOPS
            onset_coding = onset == "s" or onset in VOICELESS_STOPS
            return "+OVA" if coda_coding == onset_coding else "-OVA"

    @property
    def transcription(self) -> str:
        return f"{self.syl1.transcription}{self.syl2.transcription}"

    @property
    def line(self) -> List[str]:
        return [
            self.syl1.onset,
            self.syl1.nucleus,
            self.syl1.coda,
            self.syl1.shape,
            self.syl2.onset,
            self.syl2.nucleus,
            self.syl2.coda,
            self.syl2.shape,
            self.shape,
            self.syllable_contact_code,
            self.transcription,
        ]


def _monosyllables() -> Iterator[Monosyllable]:
    # CVC.
    for onset in SIMPLE_ONSETS_PLUS_S:
        for nucleus in NUCLEI:
            for coda in SIMPLE_CODAS_PLUS_S:
                if onset == coda:
                    continue
                yield Monosyllable(onset, nucleus, coda, "CVC")
    # sCVC.
    # I could do sl here too, but not a lot gained from it.
    for stop in VOICELESS_STOPS:
        onset = "s" + stop
        for nucleus in NUCLEI:
            for coda in SIMPLE_CODAS:
                if stop == coda:
                    continue
                yield Monosyllable(onset, nucleus, coda, "sCVC")
    # CwVC.
    for stop in STOPS:
        onset = stop + "w"
        for nucleus in LAX_NUCLEI:
            for coda in SIMPLE_CODAS_PLUS_S:
                if stop == coda:
                    continue
                yield Monosyllable(onset, nucleus, coda, "CwVC")
    # T[liquid]VC.
    for stop in ["t", "d"]:
        for nucleus in NUCLEI:
            for coda in SIMPLE_CODAS_PLUS_S:
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


def _disyllables() -> Iterator[Disyllable]:
    # We enforce tense v1, lax v2, to get a natural, trochaic weight pattern.
    # CVCCVC.
    for onset1 in SIMPLE_ONSETS_PLUS_S:
        for nucleus1 in TENSE_NUCLEI:
            for coda1 in SIMPLE_CODAS_PLUS_S:
                if onset1 == coda1:
                    continue
                syl1 = Monosyllable(onset1, nucleus1, coda1, "CVC")
                for onset2 in STOPS_PLUS_S:
                    if onset1 == onset2 or coda1 == onset2:
                        continue
                    for nucleus2 in LAX_NUCLEI:
                        for coda2 in SIMPLE_CODAS_PLUS_S:
                            if coda1 == coda2:
                                continue
                            syl2 = Monosyllable(onset2, nucleus2, coda2, "CVC")
                            yield Disyllable(syl1, syl2)
    # T[liquid]VCCVC.
    for stop1 in ["t", "d"]:
        for nucleus1 in TENSE_NUCLEI:
            for coda1 in SIMPLE_CODAS_PLUS_S:
                if stop1 == coda1:
                    continue
                syls1 = [
                    Monosyllable(stop1 + "l", nucleus1, coda1, "TlVC"),
                    Monosyllable(stop1 + "ɹ", nucleus1, coda1, "TrVC"),
                ]
                for onset2 in STOPS_PLUS_S:
                    if stop1 == onset2 or coda1 == onset2:
                        continue
                    for nucleus2 in LAX_NUCLEI:
                        for coda2 in SIMPLE_CODAS_PLUS_S:
                            if coda1 == coda2:
                                continue
                            syl2 = Monosyllable(onset2, nucleus2, coda2, "CVC")
                            for syl1 in syls1:
                                yield Disyllable(syl1, syl2)


def main():
    cl = citylex.read_textproto("citylex.textproto")
    lexicon: Set[str] = set()
    for entry in cl.entry.values():
        for pron in entry.wikipron_us_pron:
            lexicon.add(pron.replace(" ", ""))
    logging.info(f"{len(lexicon):,} lexicon entries")
    with open(MONOSYLLABLES, "w") as sink:
        tsv_writer = csv.writer(sink, delimiter="\t")
        tsv_writer.writerow(
            ["onset", "nucleus", "coda", "shape", "transcription"]
        )
        filtered = 0
        for entry in _monosyllables():
            if entry.transcription in lexicon:
                logging.info(f"{entry.transcription} is lexical")
                filtered += 1
                continue
            tsv_writer.writerow(entry.line)
    logging.info(f"{filtered:,} monosyllables filtered")
    with open(BISYLLABLES, "w") as sink:
        tsv_writer = csv.writer(sink, delimiter="\t")
        tsv_writer.writerow(
            [
                "onset1",
                "nucleus1",
                "coda1",
                "shape1",
                "onset2",
                "nucleus2",
                "coda2",
                "shape2",
                "shape",
                "syllable.contact.code",
                "transcription",
            ]
        )
        filtered = 0
        for entry in _disyllables():
            if entry.transcription in lexicon:
                logging.info(f"{entry.transcription} is lexical")
                filtered += 1
                continue
            tsv_writer.writerow(entry.line)
    logging.info(f"{filtered:,} disyllables filtered")


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s: %(message)s", level="INFO")
    main()
