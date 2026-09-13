# The MPB Corpus — dataset

Melodic contour, melodic rhythm, harmony, and melody–harmony relationship
annotations for 500 compositions by 10 composers of Brazilian Popular Music.

This branch holds the **dataset only**. Column definitions, the codebook needed
to interpret the chord and functional notations, metadata, code, and how to
cite this work are all in the repository:
<https://github.com/ProjetoMPB/mpb-corpus>

`CHANGELOG.md` records what changed in each version.

## Files

The same data in two layouts:

- `dataset_aggregated/` — `contour_rhythm.csv`, `harmony.csv` and
  `note_function.csv`, each containing all ten composers.
- `dataset_by_corpus/` — the same three tables split into one folder per
  composer, e.g. `dataset_by_corpus/JOBIM/harmony.csv`.

Composers are identified by a short `corpus_id`: JOBIM (Tom Jobim), LINS (Ivan
Lins), CHICO (Chico Buarque), EDU (Edu Lobo), CAETANO (Caetano Veloso), DJAVAN
(Djavan), BOSCO (João Bosco), MILTON (Milton Nascimento), GIL (Gilberto Gil),
RITA (Rita Lee).

All files are comma-delimited, UTF-8 without a byte-order mark, with LF line
endings. Every table begins with `corpus_id`, `composition_id` and
`composition_name`, identifying the composer and the piece.

## Loading the data

Read `contour_rhythm.csv` with `keep_default_na=False`. Four `r_word` values
are the literal string `nan` and five `c_word` values are empty, marking a
single-syllable segment; all nine are real annotations that pandas would
otherwise turn into missing values.

```python
import pandas as pd
df = pd.read_csv("dataset_aggregated/contour_rhythm.csv", keep_default_na=False)
```

## License

Creative Commons Attribution 4.0 International (CC BY 4.0). These are derived
musical representations; no original copyrighted scores or audio are
distributed.
