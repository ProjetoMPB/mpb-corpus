# Documentation

Reference material for reading the MPB Corpus. Two of the dataset's columns use notations that cannot be interpreted without the documents in this folder.

| file | decodes |
|---|---|
| `chord_types.pdf` | `harmony.chord_type` |
| `full_genealogy.pdf` | `harmony.chord_type` (how the notation is derived) |
| `lexicon_of_functional_categories.pdf` | `harmony.functional_category` |

This folder contains two additional files, `r_letters_countermetricity_values.csv` and `chord_review_examples.pdf`, discussed below.

For a full discussion of the theory regarding the data collection, see [de L. Almada et al. (2026)](https://doi.org/10.5334/tismir.357).

## Chord types — `chord_types.pdf`, `full_genealogy.pdf`

Chords are encoded in a genealogical notation: a protochord letter followed by
digits, for example `Y1.1` or `z2`. `chord_types.pdf` maps that notation to the
familiar alphanumeric chord symbols. `full_genealogy.pdf` gives the complete
list of chord types and their genealogical relations, one figure per protochord;
each block shows the genealogical notation, the usual alphanumeric notation
(written on C), and the number of notes in the chord.

The genealogy derives 161 chord types from 10 protochords (`V W X Y Z v w x y z`).
The corpus uses 98 of them, in a strict one-to-one correspondence with the 98
distinct values of `harmony.chord_symbol`.

## Functional categories — `lexicon_of_functional_categories.pdf`

For each chord we also collected its alphanumeric notation and its functional
analysis within the context of the piece. Functional categories follow a
notation detailed in this lexicon.

The corpus uses 69 distinct categories. One of them is `?`, which marks a chord
whose function was left undetermined, and it appears on 159 chords.

## Countermetricity of r-letters — `r_letters_countermetricity_values.csv`

A value is assigned to each letter of an r-word based on its rhythmical
identity: `n` is the *most countermetric* r-letter, with an assigned value of
one, and `b` the *least countermetric*, with an assigned value of `0.1` (disregarding `a`, that is a rest, and therefore, discarded from the CMI computation). This file lists the value for all 26 r-letters; the corpus uses 22 of them.

It is the machine-readable source for the countermetricity index (CMI) -- the
analysis notebook reads it rather than restating the numbers.

## Annotation corrections — `chord_review_examples.pdf`

Occasional errors in source scores were identified and corrected during the
analysis. Typical examples include the reinterpretation of chord symbols that,
though notated so as to simplify harmonic execution (particularly on the
guitar, a central instrument in MPB) represent a different chord in context;
the incorporation of structurally relevant melodic notes into the underlying
chord; and the correction of inaccurately notated harmonies. This document
collects examples of such corrections.

It documents how the harmonic annotations were produced, and so describes the
provenance of `harmony.csv` rather than decoding any particular column.