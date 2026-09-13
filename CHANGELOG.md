# Changelog

Changes to the **MPB Corpus dataset** — the annotation tables in
`dataset_aggregated/` and `dataset_by_corpus/`. Documentation, metadata and
tooling are versioned with the repository and are not covered here.

Versioning follows [Semantic Versioning](https://semver.org/), applied to the
data rather than to code:

- **Major** — an annotation changed, in a way that could alter published results.
- **Minor** — compositions or columns were added, leaving existing values intact.
- **Patch** — packaging or formatting only; every value unchanged.

## [1.1] — 2026-09-13

**No annotation changed.** Every value in every table is identical to 1.0 —
8,426 contour and rhythm segments, 17,053 chords, and 23,447 notes, in the same
order, under the same column names. Results computed from 1.0 do not need to
be recomputed.

### Added

- `dataset_by_corpus/`: the same three tables split into one folder per
  composer, e.g. `dataset_by_corpus/JOBIM/harmony.csv`. Useful for working with
  a single composer without loading the whole corpus.

### Changed

- `dataset/` is now `dataset_aggregated/`. The three files inside keep their
  names: `contour_rhythm.csv`, `harmony.csv`, `note_function.csv`.
- Line endings are now LF on every platform, where 1.0 used CRLF. This is the
  only byte-level difference in the annotation files, and the reason the
  checksums differ between versions while the data does not.

### Unchanged

- Every annotated value, and the order of every row.
- Column names and column order in all three tables.
- The 500 compositions, 50 per composer, across the same 10 composers.
- Comma delimiter, UTF-8 encoding without a byte-order mark, trailing newline.

## [1.0] — 2026-03-25

Initial public release: melodic contour, melodic rhythm, harmony, and
melody–harmony relationship annotations for 500 compositions by 10 composers of
Brazilian Popular Music, as three comma-delimited tables in `dataset/`.
