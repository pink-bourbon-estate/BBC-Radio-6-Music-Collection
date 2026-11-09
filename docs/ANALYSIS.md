# Analysis of the original Python scripts

This project started as a folder of Python scripts. This note records
what each one did, what was found while reading them and their output, and where each piece lives in the Rust
program.

## What each script did

| Original script | Purpose | Now |
| --- | --- |
| `bbc_diagnose.py`, `bbc_diagnose2.py` | One-off probes that worked out which BBC URLs still return data (the schedule `.json` pages had been retired; the schedule HTML embeds the episode list as JSON-LD). | Superseded: the discovered route is built into `scrape` and checked by `probe`. |
| `bbc6music_tracklist_scraper.py` (v1) | First attempt, using guessed JSON endpoints. | Superseded. |
| `..._scraper_v2.py`, `_v3.py` | Confirmed route: schedule page, then episode `segments.json`. v2 held every play in memory. | Superseded. |
| `..._scraper_v4.py` | Same route, but writes plays straight to disk, caches every response, survives a locked output file. | `bbc6 scrape` + `bbc6 derive` |
| `musicbrainz_enrich.py` | Looks each artist up on the MusicBrainz web service (1 request/second, so days for the full list). | `bbc6 enrich` (kept as a top-up) |
| `musicbrainz_dump_join.py` | Reads MusicBrainz's 7.5 GB database export in place and joins genre/country/era onto the artists. This produced the shipped `artists_enriched.csv`. | Not ported: it needs the huge dump. Its output is shipped; `enrich` fills any gaps. |
| `split_tracks_by_programme.py` | One playlist file per show. | `bbc6 playlists programme` |
| `build_genre_playlists.py` | Groups MusicBrainz's 872 fine-grained genres into 17 broad buckets, one playlist each. | `bbc6 playlists genre` |

## How the data is gathered

1. `https://www.bbc.co.uk/schedules/p00fzl65/<yyyy>/<mm>/<dd>` returns an HTML page whose JSON-LD block lists
   every episode broadcast that day: episode ID, show, title, start time.
2. `https://www.bbc.co.uk/programmes/<episode>/segments.json` returns the tracks played, with artist, title,
   album, label, duration and the MusicBrainz ID of the artist.
3. Everything is cached so a restart costs nothing, and requests are limited to about four per second.

The Rust version keeps the **same cache layout**, so an existing `_cache` folder from the Python tool is
reused as is (copy it to `data/_cache`).

## Verification

The Rust `derive` was run on the Python tool's own `plays_raw.csv` (1,797,256 rows) and compared with the
Python tool's outputs:

- `tracks_unique.csv`, `tracks_by_programme.csv` and `artists_unique.csv`: **byte-identical** (apart from line
  endings: Python wrote `\r\n`, the Rust program writes `\n`).
- Spot-checked playlists (Rock, Reggae/Ska/Dub, Unmatched, Gideon Coe, Unknown Show): identical.
- The shipped data differs from the Python outputs only where an email address was redacted (see below).
- It takes about 10 seconds. CI repeats the rebuild-and-compare on every push.

The scraper itself could not be run against bbc.co.uk from where this was developed, so it is covered by unit
tests on the parsing and by a local mock of the two BBC endpoints (resume, 404 handling, retry on 503, midnight
overlap between days). Run `bbc6 probe` once on your own machine to confirm the live feeds still behave.

## Findings

- **Tracklists only exist from mid-2008.** None for 2007; 113 of 3,236 episodes in 2008 (first tracklist
  2008-06-29); about 75% in 2009; 92 to 99% from 2010. In total 67,359 of 74,551 episodes have one.
- **There are 1.80 million plays, not 2.3 million** as the v4 script's comment estimated.
- **Email addresses are in the public data.** Sixteen play rows (and one MusicBrainz disambiguation) contain real
  email addresses typed into BBC artist/title/label fields. They would break a "no personal email addresses" rule, so
  they are redacted as `[email removed]` in the shipped data and by the program.
- **The MusicBrainz data is not all CC0.** The dump-join script's comment says the data is CC0. That holds for
  core data (artists, areas, dates), but genres come from user tags, which are CC BY-NC-SA 3.0. Hence the licence
  note in `docs/DATA.md`.
- **Genre coverage is limited by MusicBrainz, not the code.** Of 66,172 enriched artists, 23,340 have a genre.
  About 1,300 artists that have a MusicBrainz ID were missing from the dump; `bbc6 enrich` fills them.
- **4,140 show/track rows have no show name.** The schedule did not name the show; they become `Unknown Show`.
- **The "Other" genre bucket** still holds some sizeable genres (neo-psychedelia, easy listening, canterbury scene,
  brass band, industrial, chanson, ...). The buckets were kept exactly as before so the output matches;
  `bbc6 playlists --report` lists what falls through, and `GENRE_GROUPS` in `src/playlists.rs` is where to add keywords.
- **The top of `tracks_unique.csv` includes show music**, not just records (the top entry was played 520 of its
  534 times on one show).

## Why Rust, and what changed

- One 2.5 MB program instead of seven scripts plus Python and `requests`.
- Fewer moving parts: one `data/` folder, one command per step (`scrape`, `derive`, `enrich`, `playlists`).
- Plays are kept in one gzip file per year, so the repository holds the complete history.
- `derive` replaces the in-memory Aggregator: it streams plays and keeps only compact summaries.
- A resumable ledger (`episodes.csv`) means new scrapes only fetch what is missing.
- Dropped as unnecessary: `spotify_import.csv` (use `playlists --minimal`), the per-artist folder export,
  the Excel-lock fallback (if a CSV is open in Excel, `derive` stops with an error naming the file; close it and re-run), and the diagnostic scripts.
