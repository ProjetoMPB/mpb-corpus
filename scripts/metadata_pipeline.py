#!/usr/bin/env python3
"""Build the contents of metadata/ - composition statistics and external ids.

Generative AI assistance
------------------------
This script was written with the assistance of generative AI (Claude, by
Anthropic) in September 2026, adapted from the scripts in the fork of this
repository made by Stefan Balke (https://github.com/stefan-balke/mpb-corpus).
The design decisions recorded in the comments below were measured against the
live services, not assumed.

What it produces
----------------
One row per composition in metadata/compositions.csv, linking each of them to
the outside world:

    corpus_id, composition_id     identity, from dataset_by_corpus/
    composition_name              "
    has_note_function             whether note-function data exists for it
    spotify_*                     the matched recording on Spotify
    isrc                          the recording's ISO 3901 identifier
    musicbrainz_*                 recording and work ids, and how certain

Commands
--------
build    refresh composition identity and has_note_function from
         dataset_by_corpus/, leaving every external identifier alone
spotify  fetch every corpus playlist named in corpora.csv, match each
         composition to a track by title, and fold the result in  (network)
isrc     fetch each matched track's ISRC from the Spotify Web API
         (network; the only command needing credentials)
mbisrc   look up MusicBrainz recording and work ids by ISRC - a direct
         lookup, nothing scored                                   (network)

Usage
-----
Run from the repository root - the directory holding dataset_by_corpus/::

    python scripts/metadata_pipeline.py build
    python scripts/metadata_pipeline.py spotify
    python scripts/metadata_pipeline.py isrc
    python scripts/metadata_pipeline.py mbisrc

That is also the order they depend on each other in: 'spotify' needs the rows
'build' writes, 'isrc' needs the track ids 'spotify' finds, and 'mbisrc' needs
the codes 'isrc' fetches. Each refuses to run if its input is missing.

'isrc' needs a Spotify app registered at
https://developer.spotify.com/dashboard, and reads its credentials from the
environment - never from a file::

    PowerShell  $env:SPOTIFY_CLIENT_ID='...'; $env:SPOTIFY_CLIENT_SECRET='...'
    bash        export SPOTIFY_CLIENT_ID=... SPOTIFY_CLIENT_SECRET=...

'mbisrc' is rate limited and resumable: it caches every answer, so an
interrupted run continues where it stopped rather than repeating hundreds of
requests.

How to read the results
-----------------------
None of the external identifiers has been reviewed by a human. The Spotify
match compares titles only, so it can pick the wrong recording, release or
version of the right composition - and a 'fuzzy' or 'normalized' status says
the title did not even match exactly.

The MusicBrainz columns are more careful, and say how certain they are rather
than only what they found. An id is written only where the answer is
unambiguous; where it is not, the count says how many candidates exist. See
cmd_mbisrc.

Everything here is generated except corpora.csv, which is hand-authored. Edits
made by hand to any other file are destroyed by the next run.

Standard library only, on purpose: this must still run years from now, when a
pinned scientific stack no longer resolves.
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import re
import sys
import tempfile
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

# --------------------------------------------------------------------------
# Format contract - identical to mpb_corpus.py
# --------------------------------------------------------------------------
DELIMITER = ","
READ_ENCODING = "utf-8-sig"
WRITE_ENCODING = "utf-8"
LINE_TERMINATOR = "\n"

METADATA_DIR = "metadata"
BY_CORPUS_DIR = "dataset_by_corpus"
TABLES = ("contour_rhythm", "harmony", "note_function")

# Every file is named for what one of its rows is.
COMPOSITIONS_CSV = "compositions.csv"          # one row per composition (500)
CORPORA_CSV = "corpora.csv"                    # one row per corpus (10)
# Cache for the 'mbisrc' stage: one row per ISRC looked up, holding every
# recording and work MusicBrainz returned. Keeping it makes the stage
# resumable, and it is the evidence behind a 'several_recordings' verdict.
ISRC_LOOKUPS_CSV = "musicbrainz_isrc_lookups.csv"

USER_AGENT = "mpb-corpus/0.1 (https://github.com/ProjetoMPB/mpb-corpus)"
MUSICBRAINZ_PAUSE = 2.0        # seconds between MusicBrainz requests
SPOTIFY_PAUSE = 0.2            # seconds between Spotify requests
# MusicBrainz returns 503 often, and usually recovers within seconds. A flat
# long sleep turns one bad moment into a stall of many minutes; back off from
# 10s instead, doubling, and only settle into long waits if it really is down.
RETRY_BASE_SECONDS = 10
RETRY_MAX_SECONDS = 5 * 60
RETRY_ATTEMPTS = 8
RETRY_CODES = {429, 500, 502, 503, 504}
# Replacing a file can fail transiently on Windows while a sync client or
# scanner holds the target open; see write_csv.
REPLACE_ATTEMPTS = 6
REPLACE_RETRY_SECONDS = 0.5
# How often a long loop prints progress and saves its cache. Saving on every
# single request would be safest against a crash, but it also makes a sync
# client re-upload the file hundreds of times, which is what provokes the
# lock above in the first place.
PROGRESS_EVERY = 25

# Playlist tracks are held in memory only and folded straight into
# compositions.csv. Spotify's 'isPlayable' flag is deliberately not carried
# over: it describes the request (region, licensing, session), not the track,
# so it differs between runs and between readers.
SPOTIFY_FIELDS = ["spotify_track_id", "spotify_track_title",
                  "spotify_track_artist", "spotify_duration_ms",
                  "spotify_match_status"]

# Columns produced by earlier versions of this pipeline, dropped on rewrite.
OBSOLETE_FIELDS = {"path", "contour_rhythm_rows", "harmony_rows",
                   "note_function_rows", "spotify_match_score",
                   "musicbrainz_recording_title", "musicbrainz_recording_artist",
                   "musicbrainz_match_score"}
ISRC_FIELDS = ["isrc"]
# Written by 'mbisrc'. The counts are what make an ambiguous answer visible:
# an id is written only when its count is 1, so an empty id next to a count of
# 7 says "MusicBrainz holds seven of these", not "nothing found".
MUSICBRAINZ_FIELDS = ["musicbrainz_recording_count", "musicbrainz_recording_id",
                      "musicbrainz_work_count", "musicbrainz_work_id",
                      "musicbrainz_work_title", "musicbrainz_match_status"]

IDENTITY_FIELDS = ["corpus_id", "composition_id", "composition_name",
                   "has_note_function"]
# The order columns appear in compositions.csv, whichever command last wrote it.
COLUMN_ORDER = (IDENTITY_FIELDS + SPOTIFY_FIELDS + ISRC_FIELDS
                + MUSICBRAINZ_FIELDS)
ISRC_LOOKUP_FIELDS = ["isrc", "recording_count", "recording_ids",
                      "work_count", "work_ids", "work_titles"]


# --------------------------------------------------------------------------
# I/O
# --------------------------------------------------------------------------
def order_fields(fields) -> list[str]:
    """Known columns in the canonical order, then anything unrecognised."""
    present = [f for f in fields if f not in OBSOLETE_FIELDS]
    known = [f for f in COLUMN_ORDER if f in present]
    return known + [f for f in present if f not in COLUMN_ORDER]


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read one CSV as (fieldnames, rows), each row a dict of strings.

    Decoded as utf-8-sig so a file that picked up a BOM in a spreadsheet still
    reads correctly. Nothing is coerced to a number: an id written ``1`` must
    not come back as ``1.0``.
    """
    with path.open(newline="", encoding=READ_ENCODING) as handle:
        reader = csv.DictReader(handle, delimiter=DELIMITER)
        if reader.fieldnames is None:
            raise ValueError(f"missing CSV header: {path}")
        return list(reader.fieldnames), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    """Write atomically, so an interrupted run never truncates a checkpoint.

    The final rename is retried: on Windows a sync client (OneDrive), an
    indexer or an antivirus scanner can hold a handle to the target for a
    moment and the replace fails with PermissionError, even though nothing is
    wrong. Waiting briefly and trying again clears it. The temporary file is
    removed if every attempt fails, so a failed write leaves no litter and
    never damages the existing file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", newline="", encoding=WRITE_ENCODING,
                                     dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter=DELIMITER,
                                lineterminator=LINE_TERMINATOR)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})
    for attempt in range(REPLACE_ATTEMPTS):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt == REPLACE_ATTEMPTS - 1:
                temporary.unlink(missing_ok=True)
                raise
            time.sleep(REPLACE_RETRY_SECONDS * (attempt + 1))


# --------------------------------------------------------------------------
# Text helpers - title comparison, used by the Spotify match
# --------------------------------------------------------------------------
def clean_spaces(value: str) -> str:
    """Spotify's embed payload joins artists with ',' + U+00A0.

    Left alone, that non-breaking space travels into every downstream file
    and breaks naive comparison against ordinary text.
    """
    if not value:
        return value
    return value.replace("\u00a0", " ").replace(" ,", ",").strip()


def normalize_title(value: str) -> str:
    """Casefold, strip accents, and keep only letters, digits and spaces.

    So that "Louvação", "louvacao" and "LOUVACAO" compare equal.
    """
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", value))


def canonical_title(value: str) -> str:
    """Drop parentheticals, ' - Remastered' style suffixes and medley tails."""
    value = re.sub(r"\s*\([^)]*\)\s*", " ", value)
    value = re.split(r"\s+-\s+", value, maxsplit=1)[0]
    parts = re.split(r"\s*/\s*", value, maxsplit=1)
    if len(parts) == 2 and len(normalize_title(parts[0]).split()) >= 3:
        value = parts[0]
    return normalize_title(value)


def similarity(left: str, right: str) -> float:
    """How alike two titles are once canonicalised, from 0.0 to 1.0."""
    return SequenceMatcher(None, canonical_title(left),
                           canonical_title(right)).ratio()


def fetch_playlist_tracks(corpora: list[dict]) -> list[dict]:
    """Fetch every corpus playlist. Returns track dicts, nothing is written."""
    rows, seen = [], set()
    for corpus in corpora:
        corpus_id = corpus["corpus_id"]
        url = ("https://open.spotify.com/embed/playlist/"
               f"{corpus['spotify_playlist_id']}")
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=30) as response:
            tracks = extract_track_list(response.read().decode("utf-8"))
        kept = 0
        for track in tracks:
            uri = str(track.get("uri", ""))
            if not uri.startswith("spotify:track:"):
                continue
            track_id = uri.removeprefix("spotify:track:")
            if (corpus_id, track_id) in seen:
                raise SystemExit(f"duplicate track in {corpus_id}: {track_id}")
            seen.add((corpus_id, track_id))
            rows.append({
                "corpus_id": corpus_id,
                "spotify_track_id": track_id,
                "track_title": clean_spaces(str(track.get("title", ""))),
                "track_artist": clean_spaces(str(track.get("subtitle", ""))),
                "duration_ms": str(track.get("duration", "")),
            })
            kept += 1
        print(f"  {corpus_id}: {kept} tracks")
        time.sleep(1.0)
    return rows


# --------------------------------------------------------------------------
# build - dataset statistics
# --------------------------------------------------------------------------
def cmd_build(root: Path) -> int:
    """Refresh composition identity in compositions.csv from the dataset.

    Reads every per-corpus table, and writes one row per composition with its
    identity and whether it has note-function data. External identifiers on
    existing rows are carried through untouched, so this is safe to re-run
    after the corpus changes; a composition that has disappeared from the
    dataset is dropped, and the count of those is reported.

    Per-table row counts are deliberately not recorded. They are file sizes,
    recomputable in milliseconds, and storing them only creates something that
    can go stale.
    """
    by_corpus = root / BY_CORPUS_DIR
    meta_path = root / METADATA_DIR / COMPOSITIONS_CSV

    counts: dict[tuple[str, str], dict[str, int]] = {}
    names: dict[tuple[str, str], str] = {}
    for table in TABLES:
        for corpus_dir in sorted(p for p in by_corpus.iterdir() if p.is_dir()):
            _, rows = read_csv(corpus_dir / f"{table}.csv")
            for row in rows:
                key = (row["corpus_id"], row["composition_id"])
                counts.setdefault(key, {t: 0 for t in TABLES})[table] += 1
                names[key] = row["composition_name"]

    if meta_path.exists():
        fields, meta = read_csv(meta_path)
        existing = {(r["corpus_id"], r["composition_id"]): r for r in meta}
    else:
        fields, existing = [], {}

    # Per-table row counts are deliberately not recorded: they are file sizes,
    # recomputable in milliseconds, and duplicating them here only creates
    # something that can go stale. 'has_note_function' is kept because it
    # answers a question users actually ask when filtering the corpus.
    out_fields = order_fields(IDENTITY_FIELDS + list(fields))

    rows_out = []
    for key in sorted(counts, key=lambda k: (k[0], int(k[1]))):
        row = {k: v for k, v in existing.get(key, {}).items()
               if k not in OBSOLETE_FIELDS}
        row.update({
            "corpus_id": key[0],
            "composition_id": key[1],
            "composition_name": names[key],
            "has_note_function": "true" if counts[key]["note_function"] else "false",
        })
        rows_out.append(row)

    write_csv(meta_path, out_fields, rows_out)
    missing = set(existing) - set(counts)
    if missing:
        print(f"  WARNING: {len(missing)} composition(s) dropped: "
              f"{sorted(missing)[:5]}")
    print(f"  wrote {meta_path.relative_to(root)} "
          f"({len(rows_out)} compositions, {len(out_fields)} columns)")
    print(f"  with note-function data: "
          f"{sum(1 for r in rows_out if r['has_note_function'] == 'true')}")
    return 0


def extract_track_list(html: str) -> list[dict]:
    """Pull the embedded JSON track list out of a Spotify embed page.

    The embed page carries the playlist as a JSON literal after a
    ``"trackList":`` marker. Decoding from that offset is what avoids parsing
    the surrounding HTML, and fails loudly if Spotify changes the shape.
    """
    marker = '"trackList":'
    offset = html.find(marker)
    if offset < 0:
        raise ValueError("Spotify page contains no trackList")
    value, _ = json.JSONDecoder().raw_decode(html, offset + len(marker))
    if not isinstance(value, list):
        raise ValueError("Spotify trackList is not a list")
    return value


# --------------------------------------------------------------------------
# spotify - fetch the playlists and fold the matches into compositions.csv
# --------------------------------------------------------------------------
def cmd_spotify(root: Path) -> int:
    """Match each composition to a playlist track, by title.

    Runs in two passes. First, titles that canonicalise identically and are
    unique on both sides are matched outright - status ``exact`` if the raw
    titles agreed too, ``normalized`` if only the canonical forms did. Then
    the leftovers are matched fuzzily, most confident first, accepting only
    where similarity is at least 0.88 AND beats the runner-up by 0.08. Both
    passes assign each track at most once.

    That margin test is what keeps the fuzzy pass honest: a composition with
    two near-equally plausible tracks is left unmatched rather than assigned
    the marginally better one.

    Playlist tracks are fetched fresh and never written to a file of their
    own, so the match cannot be recomputed offline - re-running re-fetches.
    Unclaimed tracks and any track used twice are reported: both usually mean
    a title in the dataset differs from the one on Spotify.
    """
    meta_dir = root / METADATA_DIR
    meta_path = meta_dir / COMPOSITIONS_CSV
    fields, metadata = read_csv(meta_path)
    _, corpora = read_csv(meta_dir / CORPORA_CSV)

    known = {row["corpus_id"] for row in metadata}
    listed = {row["corpus_id"] for row in corpora}
    if known - listed:
        raise SystemExit(f"{CORPORA_CSV} has no playlist for corpus/corpora "
                         f"{sorted(known - listed)}")
    if listed - known:
        print(f"  WARNING: {CORPORA_CSV} lists {sorted(listed - known)}, which "
              f"are not in the dataset")

    tracks = fetch_playlist_tracks(corpora)
    print(f"  {len(tracks)} tracks fetched; matching against "
          f"{len(metadata)} compositions")

    by_corpus: dict[str, list[dict]] = {}
    for track in tracks:
        by_corpus.setdefault(track["corpus_id"], []).append(track)

    assigned: set[str] = set()
    matches: dict[tuple[str, str], tuple[dict, str, float]] = {}

    # Unique canonical-title matches on both sides.
    for corpus_id in {row["corpus_id"] for row in metadata}:
        songs_by_title: dict[str, list[dict]] = {}
        tracks_by_title: dict[str, list[dict]] = {}
        for song in (r for r in metadata if r["corpus_id"] == corpus_id):
            songs_by_title.setdefault(
                canonical_title(song["composition_name"]), []).append(song)
        for track in by_corpus.get(corpus_id, []):
            tracks_by_title.setdefault(
                canonical_title(track["track_title"]), []).append(track)
        for title, title_songs in songs_by_title.items():
            title_tracks = tracks_by_title.get(title, [])
            if len(title_songs) == len(title_tracks) == 1:
                song, track = title_songs[0], title_tracks[0]
                raw_exact = (normalize_title(song["composition_name"]) ==
                             normalize_title(track["track_title"]))
                matches[(song["corpus_id"], song["composition_id"])] = (
                    track, "exact" if raw_exact else "normalized", 1.0)
                assigned.add(track["spotify_track_id"])

    # Conservative one-to-one fuzzy acceptance.
    candidates = []
    for song in metadata:
        key = (song["corpus_id"], song["composition_id"])
        if key in matches:
            continue
        available = [t for t in by_corpus.get(song["corpus_id"], [])
                     if t["spotify_track_id"] not in assigned]
        ranked = sorted(((similarity(song["composition_name"], t["track_title"]), t)
                         for t in available), key=lambda i: i[0], reverse=True)
        if ranked:
            best_score, best_track = ranked[0]
            second = ranked[1][0] if len(ranked) > 1 else 0.0
            candidates.append((best_score, best_score - second, song, best_track))

    for score, margin, song, track in sorted(candidates, reverse=True,
                                             key=lambda x: x[0]):
        if score < 0.88 or margin < 0.08 or track["spotify_track_id"] in assigned:
            continue
        matches[(song["corpus_id"], song["composition_id"])] = (track, "fuzzy", score)
        assigned.add(track["spotify_track_id"])

    # ---- fold the winning track straight into each composition row --------
    for song in metadata:
        key = (song["corpus_id"], song["composition_id"])
        found = matches.get(key)
        track, status = (found[0], found[1]) if found else ({}, "unmatched")
        matched = status != "unmatched"
        song.update({
            "spotify_track_id": track.get("spotify_track_id", "") if matched else "",
            "spotify_track_title": track.get("track_title", "") if matched else "",
            "spotify_track_artist": track.get("track_artist", "") if matched else "",
            "spotify_duration_ms": track.get("duration_ms", "") if matched else "",
            "spotify_match_status": status,
        })

    write_csv(meta_path, order_fields(list(fields) + SPOTIFY_FIELDS), metadata)

    counts = Counter(s["spotify_match_status"] for s in metadata)
    print(f"  {dict(counts)}")

    used = {s["spotify_track_id"] for s in metadata if s["spotify_track_id"]}
    unclaimed = [t for t in tracks if t["spotify_track_id"] not in used]
    if unclaimed:
        print(f"  {len(unclaimed)} playlist track(s) matched no composition:")
        for track in unclaimed:
            print(f"    {track['corpus_id']:<8} {track['track_title']}")
    duplicated = [t for t, n in Counter(
        s["spotify_track_id"] for s in metadata if s["spotify_track_id"]
    ).items() if n > 1]
    if duplicated:
        print(f"  WARNING: track id(s) used by more than one composition: "
              f"{duplicated}")
    print("  NOTE: fuzzy and normalized matches are automatic suggestions "
          "based on title similarity alone.")
    return 0


# --------------------------------------------------------------------------
# isrc - the recording identifier, from Spotify's Web API
# --------------------------------------------------------------------------
# The embed page used by 'spotify' does not expose ISRCs; the Web API does, and
# that needs an app registration. This is why ISRC is a separate command: every
# other command in this file runs with no credentials at all.
#
# Tracks are fetched ONE AT A TIME, which looks wasteful and is deliberate.
# The batch endpoint, GET /v1/tracks?ids=, answers 403 Forbidden for an app
# registered in 2026, while GET /v1/tracks/{id} answers 200 for the same token
# and the same ids - measured, both forms, with and without a market. Spotify
# has been narrowing what a client-credentials app may call, and the batch form
# is on the wrong side of that line. One request per track still costs only a
# few minutes for the whole corpus.
TOKEN_URL = "https://accounts.spotify.com/api/token"
TRACKS_URL = "https://api.spotify.com/v1/tracks"


def spotify_token() -> str:
    """Exchange the app credentials for a Web API token.

    Client-credentials flow: no user login, no redirect, catalogue data only.
    Credentials come from the environment and are never written anywhere.
    """
    client_id = os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        raise SystemExit(
            "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set.\n"
            "Register an app at https://developer.spotify.com/dashboard, then:\n"
            "  PowerShell  $env:SPOTIFY_CLIENT_ID='...'; "
            "$env:SPOTIFY_CLIENT_SECRET='...'\n"
            "  bash        export SPOTIFY_CLIENT_ID=... "
            "SPOTIFY_CLIENT_SECRET=...\n"
            "No user login is needed - this uses the client-credentials flow.\n"
            "Never commit these values.")
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    request = urllib.request.Request(
        TOKEN_URL,
        data=urllib.parse.urlencode({"grant_type": "client_credentials"}).encode(),
        headers={"Authorization": f"Basic {basic}",
                 "Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            token = json.load(response).get("access_token", "")
    except urllib.error.HTTPError as error:
        raise SystemExit(f"Spotify rejected the credentials (HTTP {error.code}). "
                         f"Check SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET.")
    if not token:
        raise SystemExit("Spotify returned no access token")
    return token


def fetch_isrcs(track_ids: list[str], token: str) -> dict[str, str]:
    """Map Spotify track id -> ISRC, one request per track.

    One at a time because the batch endpoint is forbidden to this kind of app;
    see the note above. A track that no longer exists (404) is skipped rather
    than fatal - ids come from the playlist scrape and Spotify does retire
    them. Any other refusal stops the run, with Spotify's own message.
    """
    found: dict[str, str] = {}
    gone: list[str] = []
    for number, track_id in enumerate(track_ids, start=1):
        request = urllib.request.Request(
            f"{TRACKS_URL}/{track_id}",
            headers={"Authorization": f"Bearer {token}"})
        while True:
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    track = json.load(response)
                # Spotify returns a handful of ISRCs in lower case; the
                # standard is upper, and the code is case-insensitive, so
                # normalising here keeps the column comparable and joinable.
                isrc = (track.get("external_ids") or {}).get("isrc", "").upper()
                if isrc:
                    found[track_id] = isrc
                break
            except urllib.error.HTTPError as error:
                if error.code == 429:
                    wait = int(error.headers.get("Retry-After", "2")) + 1
                    print(f"  rate limited; waiting {wait}s", flush=True)
                    time.sleep(wait)
                    continue
                if error.code == 404:
                    gone.append(track_id)
                    break
                # Spotify explains the refusal in the response body; a bare
                # traceback hides it and every 403 then looks the same.
                detail = error.read().decode("utf-8", "replace").strip()
                raise SystemExit(
                    f"Spotify refused the request (HTTP {error.code}) after "
                    f"{number - 1} of {len(track_ids)} tracks.\n"
                    f"  {detail}\n"
                    f"  request: {TRACKS_URL}/{track_id}\n"
                    f"A 403 usually means the app may not call this endpoint: "
                    f"open the app at\n"
                    f"https://developer.spotify.com/dashboard -> Settings and "
                    f"check that 'Web API' is enabled.")
        if number % PROGRESS_EVERY == 0 or number == len(track_ids):
            print(f"  {number}/{len(track_ids)} tracks, {len(found)} ISRCs",
                  flush=True)
        time.sleep(SPOTIFY_PAUSE)
    if gone:
        print(f"  {len(gone)} track id(s) no longer on Spotify: {gone[:5]}")
    return found


def cmd_isrc(root: Path) -> int:
    """Record each matched track's ISRC in compositions.csv.

    The ISRC identifies a *recording*, which is the distinction title
    matching cannot see, and unlike a Spotify id it is an ISO standard that
    outlives any one platform.

    Two compositions sharing an ISRC are reported: that means one recording
    has been matched to two different compositions, which is a matching
    error rather than a fact about the music.
    """
    meta_path = root / METADATA_DIR / COMPOSITIONS_CSV
    fields, metadata = read_csv(meta_path)

    track_ids = list(dict.fromkeys(r["spotify_track_id"] for r in metadata
                                   if r.get("spotify_track_id")))
    if not track_ids:
        raise SystemExit(f"no Spotify track ids in {COMPOSITIONS_CSV}; "
                         f"run the 'spotify' command first")
    print(f"  {len(track_ids)} tracks to look up, one request each "
          f"(about {round(len(track_ids) * (SPOTIFY_PAUSE + 0.3) / 60)} min)")

    isrcs = fetch_isrcs(track_ids, spotify_token())

    for song in metadata:
        song["isrc"] = isrcs.get(song.get("spotify_track_id", ""), "")

    write_csv(meta_path, order_fields(list(fields) + ISRC_FIELDS), metadata)

    filled = sum(1 for s in metadata if s["isrc"])
    missing = [s["spotify_track_id"] for s in metadata
               if s.get("spotify_track_id") and not s["isrc"]]
    print(f"\n  ISRC recorded for {filled} of {len(metadata)} compositions "
          f"({len(track_ids)} had a Spotify track)")
    if missing:
        print(f"  {len(missing)} matched track(s) carry no ISRC on Spotify: "
              f"{missing[:5]}")
    duplicated = [i for i, n in Counter(s["isrc"] for s in metadata
                                        if s["isrc"]).items() if n > 1]
    if duplicated:
        print(f"  NOTE: {len(duplicated)} ISRC(s) shared by more than one "
              f"composition: {duplicated[:5]}")
        print("        Two compositions pointing at the same recording is "
              "usually a matching error.")
    return 0


# --------------------------------------------------------------------------
# mbisrc - MusicBrainz ids by ISRC lookup
# --------------------------------------------------------------------------
# GET /ws/2/isrc/{isrc} is a lookup, not a search: MusicBrainz either holds the
# code on a recording or it does not. Nothing is scored and no threshold is
# applied, which is the whole point - the title search this replaces could not
# tell one recording of a song from another, and scored the wrong ones as
# highly as the right ones.
#
# Measured on the 29 rows whose verdict was already known, 2026-09-13:
#   - all 29 ISRCs were known to MusicBrainz;
#   - all 20 previously 'confirmed' rows returned the same recording id, so the
#     two methods agree completely where they overlap;
#   - all 9 'contradicted' rows returned several recordings each (up to 7) that
#     collapse to exactly ONE work. Those were never competing performances,
#     but duplicate recording entries for one composition.
# Hence recordings and works are both recorded, and an id is written only when
# its count is 1.
def isrc_recordings(isrc: str) -> list[dict]:
    """Recordings carrying this ISRC, each with its work relations.

    An ISRC MusicBrainz does not hold answers 404; that is a normal result
    here, not a failure, so it comes back as an empty list.
    """
    params = urllib.parse.urlencode({"fmt": "json",
                                     "inc": "artist-credits+work-rels"})
    try:
        payload = request_json(
            f"https://musicbrainz.org/ws/2/isrc/{urllib.parse.quote(isrc)}"
            f"?{params}")
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return []
        raise
    recordings = payload.get("recordings", [])
    return recordings if isinstance(recordings, list) else []


def works_of(recordings: list[dict]) -> list[tuple[str, str]]:
    """Distinct (work id, work title) across every recording, sorted."""
    works = set()
    for recording in recordings:
        for relation in recording.get("relations", []) or []:
            if isinstance(relation, dict) and isinstance(relation.get("work"), dict):
                work = relation["work"]
                if work.get("id"):
                    works.add((str(work["id"]), str(work.get("title", ""))))
    return sorted(works)


def cmd_mbisrc(root: Path) -> int:
    """Look up MusicBrainz recording and work ids for every ISRC.

    Writes six columns, of which the two counts carry the uncertainty:

        musicbrainz_recording_count   recordings MusicBrainz holds for the ISRC
        musicbrainz_recording_id      written ONLY when that count is 1
        musicbrainz_work_count        distinct works those recordings point to
        musicbrainz_work_id           written ONLY when that count is 1
        musicbrainz_work_title        the work's title, to read the id by
        musicbrainz_match_status      no_isrc | isrc_not_in_mb |
                                      one_recording | several_recordings

    An id is never chosen from among several candidates. An empty id beside a
    count of 7 therefore says "MusicBrainz holds seven of these", which is a
    different statement from "nothing was found" - and the two would be
    indistinguishable if only the id were recorded.

    Every answer is cached in musicbrainz_isrc_lookups.csv, so an interrupted
    run resumes instead of repeating hundreds of rate-limited requests.
    """
    meta_dir = root / METADATA_DIR
    meta_path = meta_dir / COMPOSITIONS_CSV
    cache_path = meta_dir / ISRC_LOOKUPS_CSV

    fields, metadata = read_csv(meta_path)
    if not any(row.get("isrc") for row in metadata):
        raise SystemExit(f"no ISRCs in {COMPOSITIONS_CSV}; "
                         f"run the 'isrc' command first")

    cached_rows: list[dict] = []
    if cache_path.exists():
        _, cached_rows = read_csv(cache_path)
    cache = {row["isrc"]: row for row in cached_rows}

    wanted = list(dict.fromkeys(row["isrc"] for row in metadata if row.get("isrc")))
    pending = [code for code in wanted if code not in cache]
    print(f"  {len(wanted)} ISRCs: {len(wanted) - len(pending)} cached, "
          f"{len(pending)} to look up "
          f"(about {round(len(pending) * (MUSICBRAINZ_PAUSE + 0.4) / 60)} min)")

    for number, code in enumerate(pending, start=1):
        recordings = isrc_recordings(code)
        works = works_of(recordings)
        row = {
            "isrc": code,
            "recording_count": len(recordings),
            "recording_ids": " ".join(str(r.get("id", "")) for r in recordings),
            "work_count": len(works),
            "work_ids": " ".join(work_id for work_id, _ in works),
            "work_titles": " | ".join(title for _, title in works),
        }
        cache[code] = row
        cached_rows.append(row)
        if number % PROGRESS_EVERY == 0 or number == len(pending):
            write_csv(cache_path, ISRC_LOOKUP_FIELDS, cached_rows)     # checkpoint
            print(f"  looked up {number}/{len(pending)}", flush=True)
        time.sleep(MUSICBRAINZ_PAUSE)

    for song in metadata:
        code = song.get("isrc", "")
        found = cache.get(code) if code else None
        recording_count = int(found["recording_count"]) if found else 0
        work_count = int(found["work_count"]) if found else 0
        recording_ids = (found["recording_ids"].split() if found else [])
        work_ids = (found["work_ids"].split() if found else [])
        work_titles = (found["work_titles"].split(" | ") if found else [])

        if not code:
            status = "no_isrc"
        elif recording_count == 0:
            status = "isrc_not_in_mb"
        elif recording_count == 1:
            status = "one_recording"
        else:
            status = "several_recordings"

        song.update({
            "musicbrainz_recording_count": recording_count if code else "",
            # An id only when there is exactly one; never a pick among several.
            "musicbrainz_recording_id": recording_ids[0] if recording_count == 1 else "",
            "musicbrainz_work_count": work_count if code else "",
            "musicbrainz_work_id": work_ids[0] if work_count == 1 else "",
            "musicbrainz_work_title": work_titles[0] if work_count == 1 else "",
            "musicbrainz_match_status": status,
        })

    write_csv(meta_path, order_fields(list(fields) + MUSICBRAINZ_FIELDS), metadata)

    counts = Counter(s["musicbrainz_match_status"] for s in metadata)
    print(f"\n  {dict(counts)}")
    print(f"  recording ids recorded: "
          f"{sum(1 for s in metadata if s['musicbrainz_recording_id'])}")
    print(f"  work ids recorded:      "
          f"{sum(1 for s in metadata if s['musicbrainz_work_id'])}")
    several = [s for s in metadata if s["musicbrainz_match_status"] == "several_recordings"]
    resolved = [s for s in several if s["musicbrainz_work_id"]]
    if several:
        print(f"  {len(several)} ISRC(s) map to several recordings; "
              f"{len(resolved)} of those still resolve to a single work")
    print("  NOTE: 'several_recordings' means MusicBrainz holds more than one "
          "recording for\n        that ISRC - usually duplicate entries for one "
          "composition. No recording id\n        is written, but the work id is "
          "when they share one.")
    return 0


# --------------------------------------------------------------------------
# MusicBrainz HTTP
# --------------------------------------------------------------------------
def request_json(url: str) -> dict:
    """GET one MusicBrainz endpoint, retrying transient failures.

    503 is treated like any other transient code: back off exponentially from
    RETRY_BASE_SECONDS rather than sleeping a flat five minutes. MusicBrainz
    hands out 503 freely and usually recovers at once, so the flat wait cost
    minutes per hiccup while the service was already available again.
    """
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(RETRY_ATTEMPTS):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.load(response)
            return payload if isinstance(payload, dict) else {}
        except urllib.error.HTTPError as error:
            if error.code not in RETRY_CODES or attempt == RETRY_ATTEMPTS - 1:
                raise
            wait = min(RETRY_MAX_SECONDS, RETRY_BASE_SECONDS * 2 ** attempt)
            print(f"  HTTP {error.code} from MusicBrainz; retrying in {wait}s",
                  flush=True)
            time.sleep(wait)
        except urllib.error.URLError:
            if attempt == RETRY_ATTEMPTS - 1:
                raise
            time.sleep(min(RETRY_MAX_SECONDS,
                           RETRY_BASE_SECONDS * 2 ** attempt))
    return {}

def text_recordings(title: str, artist: str) -> list[dict]:
    """Search MusicBrainz for a recording by Title and Artist via Lucene syntax."""
    # MusicBrainz limits search strings, so we clean them up
    clean_title = title.replace('"', '').replace(':', '')
    clean_artist = artist.replace('"', '').replace(':', '')
    
    # Exact phrase matches combined with AND
    query = f'recording:"{clean_title}" AND artist:"{clean_artist}"'
    params = urllib.parse.urlencode({"fmt": "json", "query": query})
    
    try:
        payload = request_json(f"https://musicbrainz.org/ws/2/recording/?{params}")
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return []
        raise
    
    recordings = payload.get("recordings", [])
    return recordings if isinstance(recordings, list) else []

def cmd_mbtext(root: Path) -> int:
    """Fallback: Look up missing MusicBrainz ids by text search (Title + Artist).
    
    Only targets rows that failed to find an ISRC or where the ISRC was not in 
    MusicBrainz. Uses the Spotify matched text, falling back to local dataset name.
    """
    meta_dir = root / METADATA_DIR
    meta_path = meta_dir / COMPOSITIONS_CSV
    
    fields, metadata = read_csv(meta_path)
    
    # Target only rows that have no recording ID AND failed due to missing info.
    # We skip 'several_recordings' because text search is even less likely to disambiguate.
    pending = [song for song in metadata if not song.get("musicbrainz_recording_id") 
               and song.get("musicbrainz_match_status") in ("isrc_not_in_mb", "no_isrc", "unmatched")]
    
    print(f"  {len(pending)} missing recordings targeted for text fallback search "
          f"(about {round(len(pending) * (MUSICBRAINZ_PAUSE + 0.4) / 60)} min)")

    for number, song in enumerate(pending, start=1):
        # Prefer the Spotify track title/artist if matched, else use local dataset name
        title = song.get("spotify_track_title") or song.get("composition_name")
        artist = song.get("spotify_track_artist") or "" # Local dataset might not have distinct artist
        
        if not title:
            continue
            
        recordings = text_recordings(title, artist)
        
        # Exact identical match requirement to maintain conservative philosophy
        if len(recordings) == 1:
            best_recording = recordings[0]
            # Since search doesn't pull works automatically by default without 'inc' params
            # We focus on capturing the Recording ID
            song.update({
                "musicbrainz_recording_count": "1",
                "musicbrainz_recording_id": best_recording.get("id", ""),
                "musicbrainz_match_status": "text_fallback_one",
            })
        elif len(recordings) > 1:
            song.update({
                "musicbrainz_recording_count": len(recordings),
                "musicbrainz_match_status": "text_fallback_several",
            })
        else:
             song.update({
                "musicbrainz_recording_count": "0",
                "musicbrainz_match_status": "text_fallback_failed",
            })
            
        if number % PROGRESS_EVERY == 0 or number == len(pending):
            print(f"  searched {number}/{len(pending)}", flush=True)
            # Write checkpoint directly to the file to save progress
            write_csv(meta_path, order_fields(list(fields)), metadata)
            
        time.sleep(MUSICBRAINZ_PAUSE)

    # Final write
    write_csv(meta_path, order_fields(list(fields)), metadata)
    
    counts = Counter(s.get("musicbrainz_match_status") for s in metadata if "text_fallback" in s.get("musicbrainz_match_status", ""))
    print(f"\n  Text fallback results: {dict(counts)}")
    return 0
# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def main() -> int:
    """Parse the command line and dispatch. Returns the process exit code."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", type=Path, default=Path("."),
                        help="repository root (default: current directory)")

    parser = argparse.ArgumentParser(
        parents=[common], description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build", parents=[common],
                   help="refresh composition identity in compositions.csv")
    sub.add_parser("spotify", parents=[common],
                   help="fetch playlists and match compositions (network)")
    sub.add_parser("isrc", parents=[common],
                   help="fetch each matched track's ISRC from the Spotify Web "
                        "API (network; needs credentials)")
    sub.add_parser("mbisrc", parents=[common],
                   help="look up MusicBrainz recording and work ids by ISRC "
                        "(network; no credentials)")
    sub.add_parser("mbtext", parents=[common],
                   help="fallback: busca IDs faltantes via texto no MusicBrainz "
                        "(network; no credentials)")

    args = parser.parse_args()
    root = args.root.resolve()

    if args.command != "build":
        print(f"WARNING: this reaches the network and rewrites files in "
              f"{METADATA_DIR}/.")
    print(f"Running '{args.command}' in {root}")

    return {"build": cmd_build, "spotify": cmd_spotify,
            "isrc": cmd_isrc, "mbisrc": cmd_mbisrc, 
            "mbtext": cmd_mbtext}[args.command](root)


if __name__ == "__main__":
    sys.exit(main())
