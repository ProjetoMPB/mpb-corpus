[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19222221.svg)](https://doi.org/10.5281/zenodo.19222221)

The MPB Corpus is a dataset of 500 musical pieces from Brazilian Popular Music (MPB), encoded across four musical dimensions: melodic contour, melodic rhythm, harmony, and melody–harmony relationships. It provides a structured and detailed representation of musical information aimed at supporting research in computational musicology, music analysis, and data-driven studies of MPB. Overall, the MPB Corpus enables both qualitative and quantitative investigations, offering a foundation for systematically addressing musicological questions about the genre.

When using the dataset, please read and cite the following article: INSERT CITATION

# The MPB corpus
Melodic contour, melodic rhythm, harmony, and melody–harmony relationships annotations for 500 compositions of 10 composers of the Brazilian MPB. The methodology behind the annotations can be found in the article mentioned above. 

## Obtaining the dataset
- Download as [ZIP file](https://github.com/ProjetoMPB/mpb-corpus/archive/refs/heads/main.zip).
- Clone the repository: `git clone https://github.com/ProjetoMPB/mpb-corpus.git`

## Data format
The dataset is comprised of 3 CSV files, in the `dataset` folder: `contour_rhythm.csv`, `harmony.csv`, and `note_function.csv`.

The CSV files are structured as follows:

### dataset/contour_rhythm.csv
This file contains the following columns:
- `corpus_id`: Identifier of the composer.
- `composition_id`: Numerical identifier of the composition.
- `composition_name`: Name of the composition.
- `word_index`: Index of the segment within the composition.
- `c_word`: Encoded melodic contour.
- `r_word`: Encoded melodic rhythm.

For a detailed description of the encoding, see INSERT CITATION.

### dataset/harmony.csv
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

The file `supplementary-material/chord_types.pdf` provides a mapping between the genealogical notation to more familiar alphanumeric notation. For a detailed description of the encoding, see INSERT CITATION.

### dataset/note_function.csv
This file contains the following columns:
- `corpus_id`: Identifier of the composer.
- `composition_id`: Numerical identifier of the composition.
- `composition_name`: Name of the composition.
- `mode`: Mode of the excerpt.
- `note_index`: Index of the note within the composition.
- `scale_degree`: Scale degree of the note relative to the global context.
- `note_function`: Function of the note relative to the local harmonic context (inflections marked with "x").

For a detailed description of the encoding, see INSERT CITATION.

## Encoding example
The file `encoding-example.pdf` in this repository (Figure 6 in reference XXX) provides an example of how the data is annotated. See the step-by-step process below:
- Exerpt to be encoded (a)
- Segment the melody into autonomous units (b)
- Encode pitch in each segment as c-words (transitions between segments are ignored):
  * `<Apps>`, `<pPSa>`, `<PPsp>`, and `<pAAAa>`
- Encode rhythm in each segment as r-words (only attack points are considered, durations are ignored):
  * `<tn>`, `<ul>`, `<pbee>`, and `<pgnc>`
- Encode harmonic information for each chord: root, bass, type, function, key, mode, and metric position (c)
- Encode note functions relative to both global (key) and local (chord) contexts (d). NF webs and MAI summarize these relationships (e)

## Supplementary material
- `supplementary-material/lexicon_of_functional_categories.pdf`: A reference document describing the notation and meaning of the functional categories used in the dataset.
- `supplementary-material/chord_types.pdf`:  Mapping between the genealogical chord notation to more familiar alphanumeric notation.
- `supplementary-material/full_genealogy.pdf`: Complete genealogy of the 10 protochords, resulting in 161 chord types. Each figure corresponds to the genealogy of a protochord, and each block shows the genealogical notation, the usual alphanumeric chord notation (using C as the root), and the number of notes in that chord.
- `supplementary-material/chord_review_examples.pdf`: Examples of frequent corrections made when annotating harmony.
- `supplementary-material/r_letters_countermetricity_values.csv`: Contains the numerical values assigned to each r-letter according to their degree of countermetricity, used in the computation of the countermetricity index (CMI).

## Companion code
We provide a companion Jupyter Notebook (`exploratory_data_analysis.ipynb`) containing code to reproduce the main analyses presented in this work. The notebook includes:
- Implementations of the proposed metrics (CIEI, CMI, and MAI)
- Code to generate and visualize the NF web
- Scripts to reproduce all figures and tables presented in the paper
- Utilities to convert our encoding schemes into alternative formats, along with usage examples

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

## License
The material in this repository (code, dataset, and supplementary material) is licensed under the Creative Commons Attribution 4.0 International (CC BY 4.0). You are free to share and adapt the material for any purpose, provided that appropriate credit is given to the authors and the source.

This repository contains derived musical representations. No original copyrighted scores or audio files are distributed.
