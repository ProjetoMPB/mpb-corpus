[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19222220.svg)](https://doi.org/10.5281/zenodo.19222220)
[![Article](https://img.shields.io/badge/TISMIR-10.5334%2Ftismir.357-blue)](https://doi.org/10.5334/tismir.357)

The MPB Corpus is a dataset of 500 musical pieces from Brazilian Popular Music (MPB), encoded across four musical dimensions: melodic contour, melodic rhythm, harmony, and melody–harmony relationships. It provides a structured and detailed representation of musical information aimed at supporting research in computational musicology, music analysis, and data-driven studies of MPB. Overall, the MPB Corpus enables both qualitative and quantitative investigations, offering a foundation for systematically addressing musicological questions about the genre.

The dataset and the methodology behind it are described in the following article, which we ask you to cite when using the corpus (a BibTeX entry is given under [Citation](#citation)):

> de L. Almada, C., de Carvalho, H. T., & Martins, F. D. (2026). The MPB Corpus: A Dataset of Melody, Rhythm, Harmony, and Melody–Harmony Relationships in Brazilian Popular Music. *Transactions of the International Society for Music Information Retrieval*, 9(1), 565–587. https://doi.org/10.5334/tismir.357

# The MPB corpus
Melodic contour, melodic rhythm, harmony, and melody–harmony relationships annotations for 500 compositions of 10 composers of the Brazilian MPB. The methodology behind the annotations can be found in the article mentioned above.

## Obtaining the dataset
- Download as [ZIP file](https://github.com/ProjetoMPB/mpb-corpus/archive/refs/heads/main.zip).
- Clone the repository: `git clone https://github.com/ProjetoMPB/mpb-corpus.git`

## Versions and branches

`main` is the living repository. It is where the dataset is curated and where
the documentation, metadata and tooling are kept, and it may change at any time
— a corrected reference, an added link, a new analysis — without the dataset
itself being affected. **It carries no version tags.**

Released versions of the dataset live on the `dataset-release` branch, which
holds only the two `dataset_*` folders and a changelog. Each release is tagged
there, and those tags are what Zenodo archives and what published analyses pin
to. `CHANGELOG.md` records what changed between versions, for the dataset
alone.

So: cite a tag when you need a fixed version of the data, and follow `main` for
everything else.

## Repository layout

| folder | contents |
|---|---|
| `dataset_aggregated/` | the three dataset tables, one file each |
| `dataset_by_corpus/` | the same data split into one folder per composer |
| `documentation/` | reference documents needed to decode the annotations |
| `metadata/` | external identifiers |
| `papers/` | notebooks reproducing the analyses of each published paper |
| `scripts/` | command-line tools for building and checking the dataset |
| `encoding_example.pdf` | worked example of the annotation process |

## Data format

The dataset is provided in two layouts holding exactly the same rows:

- **`dataset_aggregated/`** — `contour_rhythm.csv`, `harmony.csv` and `note_function.csv`, each containing every composer. This is the convenient form for analysis, and what the companion notebooks load.
- **`dataset_by_corpus/`** — the same three files split into one folder per composer, e.g. `dataset_by_corpus/JOBIM/harmony.csv`. This is the form the annotations are curated in, and it is the source of truth: the aggregated files are generated from it.

Every file is comma-delimited, UTF-8 without a byte-order mark, with LF line endings. The two layouts can be checked against each other at any time (see *Reproducibility* below).

Two details matter when loading the files. Four `r_word` values are the literal string `nan`, so `pandas.read_csv` needs `keep_default_na=False` or they silently become missing values. Five `c_word` values are empty, since they mark single-syllable segments.

The CSV files are structured as follows:

### contour_rhythm.csv
This file contains the following columns:
- `corpus_id`: Identifier of the composer.
- `composition_id`: Numerical identifier of the composition.
- `composition_name`: Name of the composition.
- `word_index`: Index of the segment within the composition.
- `c_word`: Encoded melodic contour.
- `r_word`: Encoded melodic rhythm.

For a detailed description of the encoding, see [de L. Almada et al. (2026)](https://doi.org/10.5334/tismir.357).

### harmony.csv
This file contains the following columns:
- `corpus_id`: Identifier of the composer.
- `composition_id`: Numerical identifier of the composition.
- `composition_name`: Name of the composition.
- `chord_index`: Index of the chord within the composition.
- `root`: Root of the chord (in pitch-class notation).
- `bass`: Bass note of the chord (in pitch-class notation).
- `chord_type`: Genealogical notation of the chord.
- `chord_symbol`: Standard alphanumeric chord notation.
- `functional_category`: Harmonic function of the chord.
- `key`: Key of the excerpt (in pitch-class notation).
- `mode`: Mode of the excerpt.
- `position`: Measure number where the chord begins.

The file `documentation/chord_types.pdf` provides a mapping between the genealogical notation and more familiar alphanumeric notation. For a detailed description of the encoding, see [de L. Almada et al. (2026)](https://doi.org/10.5334/tismir.357).

### note_function.csv
This file contains the following columns:
- `corpus_id`: Identifier of the composer.
- `composition_id`: Numerical identifier of the composition.
- `composition_name`: Name of the composition.
- `mode`: Mode of the excerpt.
- `note_index`: Index of the note within the composition.
- `scale_degree`: Scale degree of the note relative to the global context.
- `note_function`: Function of the note relative to the local harmonic context (inflections marked with "x").

For a detailed description of the encoding, see [de L. Almada et al. (2026)](https://doi.org/10.5334/tismir.357).

## Encoding example
The file `encoding_example.pdf` in this repository (Figure 6 in [de L. Almada et al., 2026](https://doi.org/10.5334/tismir.357)) provides an example of how the data is annotated. See the step-by-step process below:
- Exerpt to be encoded (a)
- Segment the melody into autonomous units (b)
- Encode pitch in each segment as c-words (transitions between segments are ignored):
  * `<Apps>`, `<pPSa>`, `<PPsp>`, and `<pAAAa>`
- Encode rhythm in each segment as r-words (only attack points are considered, durations are ignored):
  * `<tn>`, `<ul>`, `<pbee>`, and `<pgnc>`
- Encode harmonic information for each chord: root, bass, type, function, key, mode, and metric position (c)
- Encode note functions relative to both global (key) and local (chord) contexts (d). NF webs and MAI summarize these relationships (e)

## Documentation
Two of the dataset's columns use notations that cannot be interpreted without the documents in `documentation/`. See `documentation/README.md` for the full guide; the files are:

- `lexicon_of_functional_categories.pdf`: A reference document describing the notation and meaning of the functional categories used in the dataset.
- `chord_types.pdf`: Mapping between the genealogical chord notation and more familiar alphanumeric notation.
- `full_genealogy.pdf`: Complete genealogy of the 10 protochords, resulting in 161 chord types. Each figure corresponds to the genealogy of a protochord, and each block shows the genealogical notation, the usual alphanumeric chord notation (using C as the root), and the number of notes in that chord.

Some additional important documentation files are:

- `chord_review_examples.pdf`: Examples of frequent corrections made when annotating harmony.
- `r_letters_countermetricity_values.csv`: Contains the numerical values assigned to each r-letter according to their degree of countermetricity, used in the computation of the countermetricity index (CMI).

## Metadata
`metadata/` records links each composition to external catalogues (Spotify tracks, ISRCs and MusicBrainz identifiers) so that the annotations can be connected to recordings and to other datasets. See `metadata/README.md` for the columns and how each was produced.

These identifiers are provided for convenience and are **not** part of the annotated dataset. They have not been reviewed by hand, and matching was performed on titles, so an identifier may point at a different recording, release or version of the intended composition.

## Companion code
We provide a companion Jupyter Notebook (`papers/2026-tismir/analysis.ipynb`) containing code to reproduce the main analyses presented in this work. The notebook includes:
- Implementations of the proposed metrics (CIEI, CMI, and MAI)
- Code to generate and visualize the NF web
- Scripts to reproduce all figures and tables presented in the paper
- Utilities to convert our encoding schemes into alternative formats, along with usage examples

Each folder under `papers/` corresponds to one publication and pins the dataset version its results were computed from.

## Reproducibility

The `scripts/` folder holds two command-line tools: one that keeps the two dataset layouts in step and verifies them against each other, and one that builds the contents of `metadata/`. Both use only the Python standard library. See `scripts/README.md` for how to run them.

The analysis notebooks are a different matter, since they need pandas, numpy, matplotlib, scipy and abjad. Each paper folder pins its own environment, so a published result stays reproducible as later work moves on to newer versions. With [uv](https://docs.astral.sh/uv/) installed:

```
cd papers/2026-tismir
uv sync                       # build the environment from uv.lock
uv run jupyter lab            # open the notebook in it
```

`uv sync` installs the exact package versions recorded in `uv.lock`, and the Python version recorded in `.python-version`, downloading that interpreter if it is not already present. Nothing else is required, and the result is the same on Linux, macOS and Windows.

One limitation: the r-word visualisation uses [abjad](https://abjad.github.io/), which renders through **LilyPond** — a separate program, not a Python package, so `uv sync` does not install it. Every other cell runs without it.

## Spotify playlists
To facilitate listening and provide musical context for the dataset, we provide curated Spotify playlists corresponding to each composer included in the MPB Corpus. Each playlist contains the musical pieces analyzed in this work, when available on the platform.

Links to the playlists are provided below (in order of analysis):
- [Tom Jobim](https://open.spotify.com/playlist/7HDlN5BRxsGnOwp0NVLBGt)
- [Ivan Lins](https://open.spotify.com/playlist/5bewWfR5wUDizEZVUJcBQa)
- [Chico Buarque](https://open.spotify.com/playlist/0BifNmWohJVSSl0HgMnbGk)
- [Edu Lobo](https://open.spotify.com/playlist/0nvyNKHMzHy83HRIwZymQr)
- [Caetano Veloso](https://open.spotify.com/playlist/7rIffYGLzaUnPM4dftNkPa)
- [Djavan](https://open.spotify.com/playlist/4kKc4eHUMrOaWiGwsCj1uM)
- [João Bosco](https://open.spotify.com/playlist/4UZMRJeXRtLMburXqLwVLy)
- [Milton Nascimento](https://open.spotify.com/playlist/3JfQIADWnWdsTKNgOi8Iex)
- [Gilberto Gil](https://open.spotify.com/playlist/37QMF6EuxOneQTLlFgLORg)
- [Rita Lee](https://open.spotify.com/playlist/5N3gtetTypnsFvI3Sl3bEQ?si=4412bbb41f774d18&nd=1&dlsi=3955ff4a906b4163)

## Citation
If the MPB Corpus is useful in your work, please cite the article that introduces it. The same reference is available in [`CITATION.cff`](CITATION.cff), and from the *Cite this repository* button on GitHub.

```bibtex
@article{almada2026mpb,
  author    = {de L. Almada, Carlos and de Carvalho, Hugo T. and Martins, Felipe D.},
  title     = {The {MPB} Corpus: A Dataset of Melody, Rhythm, Harmony, and Melody--Harmony Relationships in {Brazilian} Popular Music},
  journal   = {Transactions of the International Society for Music Information Retrieval},
  volume    = {9},
  number    = {1},
  pages     = {565--587},
  year      = {2026},
  publisher = {Ubiquity Press},
  doi       = {10.5334/tismir.357},
  url       = {https://doi.org/10.5334/tismir.357}
}
```

To refer to an exact version of the data, also cite the Zenodo DOI of that release (see [Versions and branches](#versions-and-branches)):

| version | DOI |
|---|---|
| all versions (resolves to the latest) | [10.5281/zenodo.19222220](https://doi.org/10.5281/zenodo.19222220) |
| v1.1 | [10.5281/zenodo.22737013](https://doi.org/10.5281/zenodo.22737013) |
| v1.0 | [10.5281/zenodo.19222221](https://doi.org/10.5281/zenodo.19222221) |

### Publications using the corpus
Each publication has a companion folder under `papers/` that reproduces its results from a pinned version of the dataset.

| publication | dataset version | companion code |
|---|---|---|
| de L. Almada, de Carvalho & Martins (2026). The MPB Corpus: A Dataset of Melody, Rhythm, Harmony, and Melody–Harmony Relationships in Brazilian Popular Music. *TISMIR* 9(1). [doi:10.5334/tismir.357](https://doi.org/10.5334/tismir.357) | v1.1 | [`papers/2026-tismir/`](papers/2026-tismir/) |

## License
The material in this repository (code, dataset, and documentation) is licensed under the Creative Commons Attribution 4.0 International (CC BY 4.0). You are free to share and adapt the material for any purpose, provided that appropriate credit is given to the authors and the source.

This repository contains derived musical representations. No original copyrighted scores or audio files are distributed.

The external identifiers in `metadata/` are reference codes pointing to third-party catalogues (Spotify, MusicBrainz, ISRC), included for convenience. They are facts about existing recordings rather than original material, and their use is subject to the terms of the respective providers.
