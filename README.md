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

## Supplementary material
- `supplementary-material/lexicon_of_functional_categories.pdf`: A reference document describing the notation and meaning of the functional categories used in the dataset.
- `supplementary-material/chord_types.pdf` Mapping between the genealogical chord notation to more familiar alphanumeric notation.
- `supplementary-material/r_letters_countermetricity_values.csv`: Contains the numerical values assigned to each r-letter according to their degree of countermetricity, used in the computation of the countermetricity index (CMI).
