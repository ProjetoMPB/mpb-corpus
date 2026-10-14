# The MPB Corpus — TISMIR 2026

Companion code for:

> de L. Almada, C., de Carvalho, H. T., & Martins, F. D. (2026). The MPB Corpus: A Dataset of Melody, Rhythm, Harmony, and Melody–Harmony Relationships in Brazilian Popular Music. *Transactions of the International Society for Music Information Retrieval*, 9(1), 565–587. https://doi.org/10.5334/tismir.357

`analysis.ipynb` computes every metric proposed in the paper and reproduces every figure and table in it. All of them are discussed in the text.

## Notebook content

It is organised in three parts.

**Functions** — reference implementations of the three metrics the paper
proposes, plus the conversions and plots they rely on:

- the compensated intervallic economy index (CIEI)
- the countermetricity index (CMI)
- the melodic anchoring index (MAI)
- the NF-web plot
- converters between the corpus encodings and more familiar notations (c-letters to Parsons Code and to Dowling contour notation, r-words to a 12-dimensional attack-point vector, genealogical chord notation to pitch classes)
- the $R$ statistic and its hypothesis test

**Exploratory data analysis** — the figures and tables of the paper, grouped by musical dimension: melodic rhythm, melodic contour, harmony, and note functions.

**Examples** — worked demonstrations of each converter.

## Running it

The environment is pinned here, in this folder, rather than at the repository
root: a published result should stay reproducible as later work moves on to
newer versions of pandas and the rest. With [uv](https://docs.astral.sh/uv/)
installed and the repository cloned:

```
cd papers/2026-tismir
uv sync                       # build the environment from uv.lock
uv run jupyter lab            # open the notebook in it
```

`uv sync` installs the exact package versions recorded in `uv.lock` — 126 of
them — and the Python version recorded in `.python-version`, downloading that
interpreter if it is not already present. Nothing else is needed, and the
result is the same on Linux, macOS and Windows.

| file | purpose |
|---|---|
| `analysis.ipynb` | the notebook |
| `pyproject.toml` | the six direct dependencies |
| `uv.lock` | every version pinned, with hashes — this is what makes it reproducible |
| `.python-version` | the interpreter version |

`uv sync` creates a `.venv/` folder of roughly 460 MB. It is generated, listed
in `.gitignore`, and safe to delete at any time; `uv sync` rebuilds it. If this
repository lives inside a synchronised folder such as OneDrive or Dropbox, put
the environment elsewhere so the sync client does not try to copy twenty
thousand files:

```
UV_PROJECT_ENVIRONMENT=/some/path/outside/the/synced/folder uv sync
```

### One cell needs more than uv can install

The r-word visualisation uses [abjad](https://abjad.github.io/), which renders
notation through **LilyPond**. LilyPond is a separate program rather than a
Python package, so `uv sync` does not install it; fetch it from
[lilypond.org](https://lilypond.org/) if you want that cell to run. Every other
cell works without it.

## Which corpus version the results come from

The published results were computed from **dataset version v1.1**, archived on
Zenodo as [10.5281/zenodo.22737013](https://doi.org/10.5281/zenodo.22737013).

The notebook does not read the dataset from the repository it sits in. It
downloads it from GitHub, pinned in the first code cell:

```python
DATA = ("https://raw.githubusercontent.com/ProjetoMPB/mpb-corpus"
        "/v1.1/dataset_aggregated")
DOCS = ("https://raw.githubusercontent.com/ProjetoMPB/mpb-corpus"
        "/af8fd507d716fa9b288624f5b389447a07de7816/documentation")
```

`DATA` points at the `v1.1` tag, the released dataset. `DOCS` points at a fixed
commit rather than at `main`, because the documentation lives on `main`, which
keeps changing, and one of its files
(`r_letters_countermetricity_values.csv`) feeds the CMI computation. With both
pinned, the published figures can be reproduced exactly however much the
corpus grows afterwards. Running the notebook therefore needs an internet
connection.

To work offline, or against a later version of the corpus, swap in the local
paths given in the comment in that cell:

```python
DATA = "../../dataset_aggregated"
DOCS = "../../documentation"
```

Results computed that way may differ from those in the article.

## A note on loading the data

`contour_rhythm.csv` must be read with `keep_default_na=False`. Four r-words
are the literal string `nan` (in Chico Buarque's *Acorda amor*, Gilberto Gil's
*Rebento*, Tom Jobim's *Bebel* and Ivan Lins's *Leva e traz*), and five c-words
are empty, marking a segment of a single syllable (Chico Buarque's *Calice*,
Gilberto Gil's *Drao*, Tom Jobim's *Modinha* twice, and Milton Nascimento's *Os
povos*). None of these is a missing value, and pandas silently converts all of
them unless that option is given.
