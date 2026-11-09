# BBC Radio 6 Music Collection

An offline database of **every track played on BBC Radio 6 Music** since the station's tracklists
begin, plus a small, fast command-line program (`bbc6`) to keep it up to date and turn it into playlists.

- **1.8 million plays** from **67,359 episodes** (2008-06-29 to 2026-09-08)
- **442,900 distinct tracks**, **108,621 artists**, **439 shows**
- Genre, country and era for **23,340 artists** (from MusicBrainz)
- One 2.5 MB program, no runtime, no accounts. Everything is plain CSV you can open in Excel.

All of the information comes from BBC pages that are public on bbc.co.uk. Only factual broadcast
metadata is collected: no audio, no artwork. It was built for 6 Music; other BBC radio stations use the
same pages and should work via `--service`, but that is untested.

## The data

It is already in the [`data/`](data) folder: no scraping needed to use it.

| File | What it is |
| --- | --- |
| `data/tracks_unique.csv` | **The song database.** One row per distinct artist + title: plays, first/last played, album, label, MusicBrainz artist ID. Most-played first. |
| `data/tracks_by_programme.csv` | What each **show** played, with play counts. |
| `data/artists_unique.csv` | Every artist with distinct-track and play totals. |
| `data/artists_enriched.csv` | Artists with genre, country, begin area, era (MusicBrainz). |
| `data/episodes.csv` | Every episode seen: date, time, show, title, BBC episode ID, tracks found. |
| `data/plays/plays_YYYY.csv.gz` | **The full play-by-play record**, one gzip file per year. Everything above is built from these. |

Column details, coverage and licensing: [docs/DATA.md](docs/DATA.md).

## Quick start

Download a build from the [Releases](../../releases) page (Windows, macOS, Linux), or build it yourself with
[Rust](https://rustup.rs):

```
cargo build --release
```

The program is then `target/release/bbc6` (`bbc6.exe` on Windows). Run it from the repository folder:

```
bbc6 find roxy music              # search the database
bbc6 playlists                    # write per-show and per-genre playlists to data/playlists/
bbc6 derive                       # rebuild the song database from data/plays
```

## Commands

| Command | What it does |
| --- | --- |
| `probe` | Checks the BBC feeds still work: fetches one day and one tracklist (2 requests). Run this first. |
| `scrape` | Downloads schedules and tracklists and **adds** new plays to `data/plays/`. Resumable. |
| `derive` | Builds `tracks_unique`, `tracks_by_programme` and `artists_unique` from all plays files. About 10 seconds. |
| `enrich` | Looks artists up on MusicBrainz for genre, country and era. Slow (1 request/second), resumable. |
| `playlists` | Writes one file per show and one per broad genre. Output is `Artist,Title,Album,...`, ready for Soundiiz, TuneMyMusic or MusicTransfer. |
| `find` | Searches the song database from the command line. |

Options common to all: `--data DIR` (default `data`), `--offline` (never touch the network). Run `bbc6 --help` for the rest.

### Keeping it up to date

```
bbc6 probe
bbc6 scrape --start 2026-09-09        # everything since the last episode in the database
bbc6 derive
bbc6 enrich --contact you@example.com --min-plays 3
bbc6 playlists
```

- `scrape` skips every episode already listed in `data/episodes.csv`, and caches every response in
  `data/_cache/`, so stopping and restarting costs nothing. A day of 6 Music is about a dozen requests
  (roughly 3 seconds); the whole 19-year history from scratch is about 80,000 requests and takes several hours.
- The scraper is deliberately gentle: at most about 4 requests a second across all workers.
- New plays go to plain `data/plays/plays_YYYY.csv` files, which git ignores so nothing is published by accident.
  To publish an update on purpose, gzip the file(s), `git add -f` them together with the regenerated CSVs, and commit.
- `enrich` needs `--contact` (an email address or URL). MusicBrainz asks for one in the User-Agent so they can
  get in touch if a program misbehaves; it is sent nowhere else. Artists already enriched are skipped.

### Playlists

`bbc6 playlists` writes `data/playlists/by_programme/<Show>.csv` and `data/playlists/by_genre/<Genre>.csv`.
Artists with no MusicBrainz genre land in `Unmatched.csv`. Useful options: `--min-plays N`, `--minimal`
(just `Artist,Title,Album`), `--format txt`, `--report` (which genres fall into "Other").
Most streaming services cap playlists at around 10,000 tracks; every file is sorted most-played first, so
keeping the top N rows is easy.

## How it works

```
bbc.co.uk/schedules/<service>/<yyyy>/<mm>/<dd>    ->  which episodes aired that day
bbc.co.uk/programmes/<episode>/segments.json      ->  the tracks played in that episode
                       |
                  scrape  ->  data/plays/plays_YYYY.csv       (+ data/episodes.csv)
                       |
                  derive  ->  tracks_unique / tracks_by_programme / artists_unique
                       |
   enrich (MusicBrainz) ->  artists_enriched.csv
                       |
                playlists ->  per-show and per-genre files
```

The code is small and commented: `src/scrape.rs`, `src/derive.rs`, `src/enrich.rs`, `src/playlists.rs`.
The history of how it got here, and what was found in the original Python scripts, is in
[docs/ANALYSIS.md](docs/ANALYSIS.md).

## Privacy and security

- No accounts, telemetry or tracking. The program only uses the network when you run `probe` or `scrape`
  (bbc.co.uk) or `enrich` (musicbrainz.org), and never otherwise. There is no automatic update check.
- Your working data (scraped files, caches, generated playlists, any music files) stays on your machine and is
  never committed: `.gitignore` excludes caches, playlists, newly scraped plays, PDFs, music files, archives and key files.
- Real email addresses sometimes appear inside BBC tracklist text. The program replaces them with
  `[email removed]` when scraping, deriving and enriching, and the published data contains none.
- Every push runs [gitleaks](https://github.com/gitleaks/gitleaks) (`.gitleaks.toml`) before anything is built.
  If it finds an API key, token, password, private key or personal email address, the build fails and nothing is
  released. The `data/` folder is scanned separately for email addresses. gitleaks itself is downloaded
  from its GitHub release and verified against its published SHA-256 checksum before it runs.
- Each release is published with a `SHA256SUMS` file. Check your download against it before running it.

## Data sources and licences

- **BBC**: factual broadcast metadata (show, episode, track listings) from public bbc.co.uk pages.
- **MusicBrainz**: artist IDs come from the BBC's own data. Genre, tags, country and era come from
  [MusicBrainz](https://musicbrainz.org). Its genre data is user-contributed tag data, released under
  [CC BY-NC-SA 3.0](https://creativecommons.org/licenses/by-nc-sa/3.0/): credit MusicBrainz, non-commercial use,
  share alike. See [docs/DATA.md](docs/DATA.md).
- The program's code is MIT licensed (see `LICENSE`).

## Development

```
cargo test        # unit tests
cargo build --release
```

Dependencies are kept minimal: `ureq` (HTTP), `serde_json`, `csv` and `flate2`. Command-line parsing,
dates and the rate limiter are hand-written to keep the binary small.
