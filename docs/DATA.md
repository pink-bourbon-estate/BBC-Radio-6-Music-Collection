# Data files

All files are UTF-8 CSV with a header row and `\n` line endings. They open directly in Excel, LibreOffice,
pandas and so on. `tracks_by_programme.csv` and `tracks_unique.csv` are large (about 43 MB and 46 MB) but
are under Excel's one-million-row limit.

Everything except `artists_enriched.csv` and `episodes.csv` can be rebuilt from `plays/` with `bbc6 derive`
(the output is byte-identical; CI checks this on every push).

## Coverage at a glance

| | |
| --- | --- |
| Plays | 1,797,256 |
| Episodes seen | 74,551 (67,359 with a tracklist) |
| Date range | 2007-09-15 to 2026-09-08 (tracklists start 2008-06-29) |
| Distinct tracks | 442,900 |
| Artists | 108,621 (67,473 with a MusicBrainz ID, covering 95.7% of plays) |
| Show/track combinations | 821,880 across 439 named shows (4,140 rows have no show name) |
| Artists with a genre | 23,340 of the 66,172 in `artists_enriched.csv` |

Tracklists are sparse in the early years because the BBC did not publish them: none for 2007, 113 of 3,236
episodes in 2008, about 75% for 2009, and 92 to 99% from 2010 onwards.

## `plays/plays_YYYY.csv.gz`

One row per track played, in broadcast order, gzip-compressed (one file per year, by broadcast date). `bbc6`
reads `.csv` and `.csv.gz` interchangeably; use `zcat`, 7-Zip or pandas to open them yourself.

`Date, Time, Show, Episode, EpisodePID, Position, OffsetSec, Artist, Title, Album, Label, Publisher, DurationSec, MusicBrainzArtistID`

`Position` is the track's order in the episode, `OffsetSec` is seconds into the programme (often blank), and
`DurationSec` is the track length when the BBC recorded it.

## `tracks_unique.csv`

`Artist, Title, Album, Label, Plays, First played, Last played, MusicBrainzArtistID`

Tracks are matched ignoring case, extra spaces and curly quotes, so "The Fall" and "THE FALL" are one artist.
The spelling shown is the first one seen. The top of the list includes recurring show music as well as records: the
most-played entry, for example, was played 520 of its 534 times on Steve Lamacq's show.

## `tracks_by_programme.csv`

`Show, Artist, Title, Plays`. Sorted by show, then most-played. An empty `Show` means the BBC schedule did not name one.

## `artists_unique.csv`

`Artist, MusicBrainzArtistID, Distinct tracks, Total plays`. Most-played first.

## `artists_enriched.csv`

`Artist, MusicBrainzArtistID, PrimaryGenre, Genres, Tags, Country, Area, BeginArea, Type, BeginYear, EndYear, Decade, Disambiguation, DistinctTracks, TotalPlays`

`PrimaryGenre` is the highest-voted MusicBrainz genre; `Genres` and `Tags` list up to eight, most-voted first.
Only 23,340 of the 66,172 artists have a genre at all: that is how complete MusicBrainz is, not a fault in the
program. About 1,300 artists with a MusicBrainz ID in `artists_unique.csv` are not in this file yet (the
dump it was built from predates them); `bbc6 enrich` fills those in.

**Licence note.** The artist IDs, names, countries, areas and dates are MusicBrainz core data (CC0). The genre
and tag columns are MusicBrainz user-contributed tag data, which is licensed
[CC BY-NC-SA 3.0](https://creativecommons.org/licenses/by-nc-sa/3.0/): attribute MusicBrainz, use it
non-commercially, and share derivatives under the same licence. Treat those columns accordingly.

## `episodes.csv`

`Date, Time, Show, Episode, EpisodePID, Tracks`. It doubles as the scraper's ledger: an episode listed here is
never fetched again (use `scrape --retry-empty` to re-check ones with 0 tracks).

## Not committed

`data/_cache/` and `data/_mbcache/` (raw responses), `data/playlists/` (regenerate with `bbc6 playlists`),
and any freshly scraped plain-text `plays_*.csv`.
