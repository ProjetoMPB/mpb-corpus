#!/usr/bin/env python3
"""Resolve MusicBrainz ID ambiguities using release dates.

Generative AI assistance
------------------------
This script was written with the assistance of generative AI (Google Gemini)
to resolve missing identifiers in the dataset by finding the oldest release date.

What it produces
----------------
Updates metadata/compositions.csv by filling in missing
musicbrainz_recording_id values. It also creates a new column 
`musicbrainz_match_criteria` to provide traceability for how each ID was resolved.
"""

import csv
import json
import os
import time
import urllib.parse
import urllib.request
import urllib.error
import tempfile
from collections import Counter
from pathlib import Path

# Configuration and network constants
USER_AGENT = "mpb-corpus/0.2 (https://github.com/ProjetoMPB/mpb-corpus)"
MUSICBRAINZ_PAUSE = 2.0
COMPOSITIONS_CSV = Path("metadata/compositions.csv")

def request_mb(url: str) -> dict:
    """Fetch data from MusicBrainz API with exponential backoff for 503 errors."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(8):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return {}
            if error.code in {503, 502, 500, 429}:
                wait = min(300, 10 * 2 ** attempt)
                print(f"    HTTP {error.code} received; waiting {wait}s...")
                time.sleep(wait)
                continue
            raise
    return {}

def extract_earliest_date(recording: dict) -> str:
    """Extract all dates linked to a recording and return the oldest one."""
    dates = []
    
    if recording.get("first-release-date"):
        dates.append(recording["first-release-date"])
        
    for release in recording.get("releases", []):
        if release.get("date"):
            dates.append(release["date"])
            
    valid_dates = [d for d in dates if len(d) >= 4]
    return min(valid_dates) if valid_dates else "9999-99-99"

def get_oldest_by_isrc(isrc: str) -> str:
    """Query the API via ISRC including release dates to resolve ambiguities."""
    url = f"https://musicbrainz.org/ws/2/isrc/{urllib.parse.quote(isrc)}?fmt=json&inc=releases"
    data = request_mb(url)
    recordings = data.get("recordings", [])
    if not recordings:
        return None
    
    recordings.sort(key=extract_earliest_date)
    return recordings[0].get("id")

def get_by_text(title: str, artist: str) -> tuple[str, str]:
    """Query by text via Lucene syntax and define the ID by the oldest recording."""
    clean_title = title.replace('"', '').replace(':', '')
    clean_artist = artist.replace('"', '').replace(':', '')
    query = f'recording:"{clean_title}" AND artist:"{clean_artist}"'
    params = urllib.parse.urlencode({"fmt": "json", "query": query})
    
    url = f"https://musicbrainz.org/ws/2/recording/?{params}"
    data = request_mb(url)
    recordings = data.get("recordings", [])
    
    if len(recordings) == 0:
        return None, "not_found"
    elif len(recordings) == 1:
        return recordings[0].get("id"), "text_exact_match"
    else:
        recordings.sort(key=extract_earliest_date)
        return recordings[0].get("id"), "text_oldest_match"

def save_csv(fields: list[str], rows: list[dict]) -> None:
    """Atomic write to prevent file corruption on Windows."""
    temp_name = ""
    with tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8", dir=COMPOSITIONS_CSV.parent, delete=False) as temp:
        writer = csv.DictWriter(temp, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
        temp_name = temp.name
    os.replace(temp_name, COMPOSITIONS_CSV)

def main() -> None:
    """Read the composition dataset, resolve ambiguous IDs, and output traceability."""
    print("Starting heuristic date sweep and traceability matrix creation...")
    
    with COMPOSITIONS_CSV.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames)
        rows = list(reader)
        
    if "musicbrainz_match_criteria" not in fields:
        fields.append("musicbrainz_match_criteria")

    for number, row in enumerate(rows, 1):
        isrc = row.get("isrc", "")
        mb_status = row.get("musicbrainz_match_status", "")
        current_id = row.get("musicbrainz_recording_id", "")
        criteria = row.get("musicbrainz_match_criteria", "")
        
        if criteria in ("isrc_exact_match", "isrc_oldest_match", "text_exact_match", "text_oldest_match", "not_found"):
            continue

        # 1. O(1) LOCAL RESOLUTION
        if mb_status == "one_recording" and current_id:
            row["musicbrainz_match_criteria"] = "isrc_exact_match"
            continue
            
        if mb_status == "text_fallback_one" and current_id:
            row["musicbrainz_match_criteria"] = "text_exact_match"
            continue
            
        # 2. NETWORK: Multiple ISRC (Tiebreak by date)
        if mb_status == "several_recordings":
            print(f"[{number}/{len(rows)}] Tiebreaking multiple ISRC by date: {row['composition_name']}")
            oldest_id = get_oldest_by_isrc(isrc)
            if oldest_id:
                row["musicbrainz_recording_id"] = oldest_id
                row["musicbrainz_match_criteria"] = "isrc_oldest_match"
            time.sleep(MUSICBRAINZ_PAUSE)
            continue
            
        # 3. NETWORK: Text search and Date
        print(f"[{number}/{len(rows)}] Tiebreaking text by date: {row['composition_name']}")
        title = row.get("spotify_track_title") or row.get("composition_name")
        artist = row.get("spotify_track_artist") or ""
        
        new_id, new_criteria = get_by_text(title, artist)
        row["musicbrainz_recording_id"] = new_id if new_id else ""
        row["musicbrainz_match_criteria"] = new_criteria
        
        time.sleep(MUSICBRAINZ_PAUSE)
        
        if number % 25 == 0:
            save_csv(fields, rows)

    save_csv(fields, rows)

    print("\nProcess successfully completed. Traceability matrix summary:")
    counts = Counter(r.get("musicbrainz_match_criteria") for r in rows)
    for crit, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {crit}: {count}")

if __name__ == "__main__":
    main()