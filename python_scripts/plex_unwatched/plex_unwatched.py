#!/usr/bin/env python3
"""
plex_unwatched.py — Analyze Plex media for unwatched/least-watched content.

Requires Python 3.10+ (uses X | Y union type syntax).

Sources:
  - Tautulli API  : watch history, play counts, max progress per item
  - Plex API      : current file sizes and metadata (always live, bypasses Tdarr)

Configuration (any of these methods, in priority order):
  1. CLI flags        --plex-url, --plex-token, --tautulli-url, --tautulli-key
  2. .env file        PLEX_URL, PLEX_TOKEN, TAUTULLI_URL, TAUTULLI_API_KEY
  3. Environment vars same names as .env keys

Usage:
  python3 plex_unwatched.py
  python3 plex_unwatched.py --plex-url http://192.168.1.10:32400 --plex-token abc123 \\
                             --tautulli-url http://192.168.1.10:8181 --tautulli-key xyz
  python3 plex_unwatched.py --top 50 --min-size 500 --movies-only
"""

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: 'requests' not installed. Run: pip install requests")
    sys.exit(1)

try:
    from rich import box
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    from rich.text import Text
except ImportError:
    print("ERROR: 'rich' not installed. Run: pip install rich")
    sys.exit(1)

# ── Constants ─────────────────────────────────────────────────────────────────
WATCHED_THRESHOLD = 0.90
UNWATCHED_SEASON_THRESHOLD = 1.0
DEFAULT_TOP = 30
DEFAULT_MIN_SIZE_MB = 0
PLEX_PAGE_SIZE = 1000
TAUTULLI_PAGE_SIZE = 1000
DEFAULT_EXCLUDE_LIBRARIES = ["Sports"]
ENV_FILE = Path(".env")

console = Console()


# ── .env loader ───────────────────────────────────────────────────────────────


def load_env_file(path: Path) -> dict:
    """Parse a simple KEY=value .env file. Ignores comments and blank lines."""
    env = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        env[key.strip()] = val.strip().strip('"').strip("'")
    return env


def resolve_config(args: argparse.Namespace) -> dict:
    """
    Merge config from CLI > .env file > environment variables.
    Returns a dict with plex_url, plex_token, tautulli_url, tautulli_key.
    """
    env_file = load_env_file(ENV_FILE)

    def get(cli_val, env_key):
        if cli_val:
            return cli_val
        if env_key in env_file:
            return env_file[env_key]
        return os.environ.get(env_key, "")

    return {
        "plex_url": get(args.plex_url, "PLEX_URL").rstrip("/"),
        "plex_token": get(args.plex_token, "PLEX_TOKEN"),
        "tautulli_url": get(args.tautulli_url, "TAUTULLI_URL").rstrip("/"),
        "tautulli_key": get(args.tautulli_key, "TAUTULLI_API_KEY"),
    }


# ── Helpers ───────────────────────────────────────────────────────────────────


def fmt_size(b: int | float) -> str:
    if b is None or b < 0:
        return "—"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


def pct_str(p: float | None) -> str:
    if p is None:
        return "—"
    return f"{p * 100:.0f}%"


def fmt_date(ts: int) -> str:
    if not ts:
        return "—"
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def get(
    session: requests.Session, url: str, params: dict | None = None, timeout: int = 30
):
    """GET with basic error handling."""
    try:
        r = session.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r
    except requests.exceptions.ConnectionError:
        console.print(f"[bold red]Connection error:[/] Could not reach {url}")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        console.print(f"[bold red]HTTP error:[/] {e} — {url}")
        sys.exit(1)
    except requests.exceptions.Timeout:
        console.print(f"[bold red]Timeout:[/] {url}")
        sys.exit(1)


# ── Tautulli API ──────────────────────────────────────────────────────────────


def tautulli_call(
    session: requests.Session,
    base_url: str,
    api_key: str,
    cmd: str,
    extra: dict | None = None,
) -> dict:
    params = {"apikey": api_key, "cmd": cmd}
    if extra:
        params.update(extra)
    r = get(session, f"{base_url}/api/v2", params=params)
    data = r.json()
    if data.get("response", {}).get("result") != "success":
        msg = data.get("response", {}).get("message", "unknown error")
        console.print(f"[bold red]Tautulli API error ({cmd}):[/] {msg}")
        sys.exit(1)
    return data["response"]["data"]


def fetch_tautulli_history(
    session: requests.Session, base_url: str, api_key: str
) -> dict:
    """
    Pull full watch history from Tautulli in pages.
    Returns dict keyed by rating_key → {play_count, max_progress}.
    """
    history: dict[str, dict] = {}
    start = 0
    page_size = TAUTULLI_PAGE_SIZE

    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Fetching Tautulli history...", total=None)

        while True:
            data = tautulli_call(
                session,
                base_url,
                api_key,
                "get_history",
                {
                    "length": page_size,
                    "start": start,
                    "media_type": "movie,episode",
                },
            )

            records = data.get("data", [])
            total = data.get("recordsFiltered", data.get("recordsTotal", 0))

            for rec in records:
                rk = str(rec.get("rating_key", ""))
                if not rk:
                    continue

                duration = rec.get("duration") or 0
                view_offset = rec.get("view_offset") or 0
                progress_pct = (view_offset / duration) if duration > 0 else 0.0

                # Also check if Tautulli marked it as watched
                watched = rec.get("watched_status", 0)
                if watched == 1:
                    progress_pct = max(progress_pct, 1.0)

                if rk not in history:
                    history[rk] = {
                        "play_count": 0,
                        "max_progress": 0.0,
                        "last_watched": 0,
                    }

                history[rk]["play_count"] += 1
                history[rk]["max_progress"] = max(
                    history[rk]["max_progress"], progress_pct
                )
                history[rk]["last_watched"] = max(
                    history[rk]["last_watched"], rec.get("date", 0) or 0
                )

            start += len(records)
            progress.update(
                task, description=f"Fetching Tautulli history... {start}/{total}"
            )

            if start >= total or not records:
                break

    return history


# ── Plex API ──────────────────────────────────────────────────────────────────


def plex_get(
    session: requests.Session,
    base_url: str,
    token: str,
    path: str,
    extra_params: dict | None = None,
) -> ET.Element:
    """GET a Plex API endpoint, return parsed XML root."""
    params: dict = {"X-Plex-Token": token}
    if extra_params:
        params.update(extra_params)
    r = get(session, f"{base_url}{path}", params=params, timeout=120)
    return ET.fromstring(r.content)


def plex_fetch_all(
    session: requests.Session,
    base_url: str,
    token: str,
    path: str,
    tag: str,
    extra_params: dict | None = None,
    progress: Progress | None = None,
    description: str = "Fetching...",
) -> list[ET.Element]:
    """Paginate through a Plex library endpoint, return all matching XML elements."""
    items: list[ET.Element] = []
    start = 0
    base_params: dict = {"X-Plex-Token": token}
    if extra_params:
        base_params.update(extra_params)

    task = progress.add_task(description, total=None) if progress else None

    while True:
        params = {
            **base_params,
            "X-Plex-Container-Start": start,
            "X-Plex-Container-Size": PLEX_PAGE_SIZE,
        }
        r = get(session, f"{base_url}{path}", params=params, timeout=120)
        root = ET.fromstring(r.content)
        total = int(root.get("totalSize", root.get("size", 0)))
        if task is not None and progress:
            progress.update(task, total=total)
        batch = root.findall(f".//{tag}")
        items.extend(batch)
        start += len(batch)
        if task is not None and progress:
            progress.update(
                task, completed=start, description=f"{description} {start}/{total}"
            )
        if not batch or start >= total:
            break

    if task is not None and progress:
        progress.remove_task(task)

    return items


def fetch_plex_libraries(
    session: requests.Session, base_url: str, token: str
) -> list[dict]:
    """Return list of {key, title, type} for all Plex libraries."""
    root = plex_get(session, base_url, token, "/library/sections")
    return [
        {
            "key": d.get("key"),
            "title": d.get("title"),
            "type": d.get("type"),  # 'movie' or 'show'
        }
        for d in root.findall(".//Directory")
        if d.get("type") in ("movie", "show")
    ]


def fetch_plex_movies(
    session: requests.Session,
    base_url: str,
    token: str,
    library_key: str,
    progress: Progress | None = None,
    description: str = "Fetching movies...",
) -> list[dict]:
    """Fetch all movies from a Plex movie library."""
    movies = []
    for video in plex_fetch_all(
        session,
        base_url,
        token,
        f"/library/sections/{library_key}/all",
        "Video",
        progress=progress,
        description=description,
    ):
        size = 0
        for part in video.findall(".//Part"):
            try:
                size += int(part.get("size", 0))
            except (ValueError, TypeError):
                pass
        movies.append(
            {
                "rating_key": video.get("ratingKey", ""),
                "title": video.get("title", "Unknown"),
                "year": video.get("year", "—"),
                "size_bytes": size,
            }
        )
    return movies


def fetch_plex_episodes(
    session: requests.Session,
    base_url: str,
    token: str,
    library_key: str,
    progress: Progress | None = None,
    description: str = "Fetching episodes...",
) -> list[dict]:
    """Fetch all episodes from a Plex TV library."""
    episodes = []
    for video in plex_fetch_all(
        session,
        base_url,
        token,
        f"/library/sections/{library_key}/all",
        "Video",
        extra_params={"type": "4"},
        progress=progress,
        description=description,
    ):
        size = 0
        for part in video.findall(".//Part"):
            try:
                size += int(part.get("size", 0))
            except (ValueError, TypeError):
                pass
        episodes.append(
            {
                "rating_key": video.get("ratingKey", ""),
                "title": video.get("title", "Unknown"),
                "show_title": video.get("grandparentTitle", "Unknown Show"),
                "grandparent_key": video.get("grandparentRatingKey", ""),
                "season_num": video.get("parentIndex", "?"),
                "ep_num": video.get("index", "?"),
                "size_bytes": size,
            }
        )
    return episodes


def fetch_all_plex_media(
    session: requests.Session,
    base_url: str,
    token: str,
    exclude_libraries: list[str] | None = None,
) -> tuple[list, list]:
    """Fetch all movies and episodes from all Plex libraries."""
    exclude = {name.lower() for name in (exclude_libraries or [])}
    all_movies: list[dict] = []
    all_episodes: list[dict] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        lib_task = progress.add_task("Fetching Plex libraries...", total=None)
        libraries = fetch_plex_libraries(session, base_url, token)
        libraries = [lib for lib in libraries if lib["title"].lower() not in exclude]
        progress.update(lib_task, total=len(libraries), completed=0)

        for lib in libraries:
            progress.update(
                lib_task, description=f"Library: {lib['title']} ({lib['type']})"
            )

            if lib["type"] == "movie":
                movies = fetch_plex_movies(
                    session,
                    base_url,
                    token,
                    lib["key"],
                    progress=progress,
                    description=f"  {lib['title']} movies",
                )
                all_movies.extend(movies)
            elif lib["type"] == "show":
                episodes = fetch_plex_episodes(
                    session,
                    base_url,
                    token,
                    lib["key"],
                    progress=progress,
                    description=f"  {lib['title']} episodes",
                )
                all_episodes.extend(episodes)

            progress.advance(lib_task)

    return all_movies, all_episodes


# ── Analysis ──────────────────────────────────────────────────────────────────


def analyze_movies(movies: list, history: dict, min_size_bytes: int) -> list[dict]:
    results = []
    for m in movies:
        rk = str(m["rating_key"])
        h = history.get(rk, {})
        play_count = h.get("play_count", 0)
        max_progress = h.get("max_progress", 0.0)

        never_watched = play_count == 0
        partially_watched = (not never_watched) and (max_progress < WATCHED_THRESHOLD)
        fully_watched = (not never_watched) and (max_progress >= WATCHED_THRESHOLD)

        size = m.get("size_bytes", 0)
        if size < min_size_bytes:
            continue

        results.append(
            {
                "title": m["title"],
                "year": m.get("year", "—"),
                "play_count": play_count,
                "max_progress": max_progress if play_count > 0 else None,
                "never_watched": never_watched,
                "partially_watched": partially_watched,
                "fully_watched": fully_watched,
                "last_watched": h.get("last_watched", 0),
                "size_bytes": size,
            }
        )

    results.sort(key=lambda x: x["size_bytes"], reverse=True)
    return results


def analyze_shows(episodes: list, history: dict, min_size_bytes: int) -> list[dict]:
    shows: dict[str, dict] = {}

    for ep in episodes:
        show_key = ep["grandparent_key"] or ep["show_title"]
        show_title = ep["show_title"]

        rk = str(ep["rating_key"])
        h = history.get(rk, {})
        play_count = h.get("play_count", 0)
        max_progress = h.get("max_progress", 0.0)

        size = max(ep.get("size_bytes", 0), 0)

        never_watched = play_count == 0
        partial = (not never_watched) and (max_progress < WATCHED_THRESHOLD)

        if show_key not in shows:
            shows[show_key] = {
                "title": show_title,
                "total_episodes": 0,
                "never_watched_count": 0,
                "partial_count": 0,
                "fully_watched_count": 0,
                "never_watched_size": 0,
                "partial_size": 0,
                "total_size": 0,
                "last_watched": 0,
                "seasons": {},
            }

        s = shows[show_key]
        s["total_episodes"] += 1
        s["total_size"] += size
        s["last_watched"] = max(s["last_watched"], h.get("last_watched", 0))

        season = str(ep.get("season_num", "?"))
        if season not in s["seasons"]:
            s["seasons"][season] = {"total": 0, "never": 0}
        s["seasons"][season]["total"] += 1

        if never_watched:
            s["never_watched_count"] += 1
            s["seasons"][season]["never"] += 1
            if size >= min_size_bytes:
                s["never_watched_size"] += size
        elif partial:
            s["partial_count"] += 1
            if size >= min_size_bytes:
                s["partial_size"] += size
        else:
            s["fully_watched_count"] += 1

    for s in shows.values():
        total = s["total_episodes"]
        s["pct_never_watched"] = (
            (s["never_watched_count"] / total * 100) if total else 0.0
        )
        s["unwatched_seasons"] = sorted(
            (
                season
                for season, counts in s["seasons"].items()
                if counts["total"] > 0
                and counts["never"] / counts["total"] >= UNWATCHED_SEASON_THRESHOLD
                and season != "0"  # skip specials season
            ),
            key=lambda x: int(x) if x.isdigit() else 999,
        )

    results = [
        s
        for s in shows.values()
        if s["never_watched_count"] > 0 or s["partial_count"] > 0
    ]
    results.sort(
        key=lambda x: x["never_watched_size"] + x["partial_size"],
        reverse=True,
    )
    return results


# ── Rendering ─────────────────────────────────────────────────────────────────


def render_summary(
    movies: list,
    shows: list,
    movie_filters: list[str] | None = None,
    show_filters: list[str] | None = None,
) -> None:
    total_movie_size = sum(m["size_bytes"] for m in movies)
    total_show_size = sum(s["total_size"] for s in shows)
    never_movies = sum(1 for m in movies if m["never_watched"])
    partial_movies = sum(1 for m in movies if m["partially_watched"])
    watched_movies = sum(1 for m in movies if m["fully_watched"])
    never_eps = sum(s["never_watched_count"] + s["partial_count"] for s in shows)
    total_shows = len(shows)
    total_seasons = sum(len(s["seasons"]) for s in shows)

    movie_line = (
        f"[bold cyan]Movies[/]   Never watched: [red]{never_movies}[/]  "
        f"Partial: [yellow]{partial_movies}[/]  "
        f"Watched: [dim green]{watched_movies}[/]  "
        f"Size on disk (filtered): [green]{fmt_size(total_movie_size)}[/]"
    )
    show_line = (
        f"[bold cyan]TV Shows[/] Shows: [cyan]{total_shows}[/]  "
        f"Seasons: [cyan]{total_seasons}[/]  "
        f"Unwatched/partial eps: [red]{never_eps}[/]  "
        f"Size on disk (filtered): [green]{fmt_size(total_show_size)}[/]"
    )

    lines = [movie_line]
    if movie_filters:
        lines.append(f"  [dim]Filters: {' · '.join(movie_filters)}[/]")
    lines.append(show_line)
    if show_filters:
        lines.append(f"  [dim]Filters: {' · '.join(show_filters)}[/]")
    lines += [
        "",
        "[dim]File sizes sourced live from Plex API — always current post-Tdarr.[/]",
    ]

    console.print(Panel("\n".join(lines), title="Summary", border_style="bright_blue"))


def render_movies_table(movies: list, top: int) -> None:
    shown = movies[:top]
    table = Table(
        title=f"Movies — All unwatched/partial/watched  ({len(shown)} of {len(movies)} by size)",
        box=box.ROUNDED,
        header_style="bold magenta",
    )
    table.add_column("Title", style="bold", min_width=28, max_width=48)
    table.add_column("Year", justify="center", width=6)
    table.add_column("Plays", justify="right", width=6)
    table.add_column("Progress", justify="right", width=9)
    table.add_column("Last Watched", justify="center", width=12)
    table.add_column("Status", justify="center", width=14)
    table.add_column("Size", justify="right", width=10)

    for m in shown:
        if m["never_watched"]:
            status = Text("Never watched", style="red")
        elif m["partially_watched"]:
            status = Text("Partial", style="yellow")
        else:
            status = Text("Watched", style="dim green")
        table.add_row(
            m["title"],
            str(m["year"]),
            str(m["play_count"]),
            pct_str(m["max_progress"]),
            fmt_date(m["last_watched"]),
            status,
            fmt_size(m["size_bytes"]),
        )
    console.print(table)


def render_shows_table(shows: list, top: int) -> None:
    shown = shows[:top]
    table = Table(
        title=f"TV Shows — Unwatched / Partial  (top {len(shown)} of {len(shows)} by wasted space)",
        box=box.ROUNDED,
        header_style="bold magenta",
    )
    table.add_column("Show", style="bold", min_width=28, max_width=44)
    table.add_column("Total Eps", justify="right", width=10)
    table.add_column("Unwatched", justify="right", width=10)
    table.add_column("Watched", justify="right", width=9)
    table.add_column("% Never", justify="right", width=8)
    table.add_column("Last Watched", justify="center", width=13)
    table.add_column("Wasted Total", justify="right", width=13)
    table.add_column("Unwatched Seasons", justify="left", width=28)

    for s in shown:
        wasted = s["never_watched_size"] + s["partial_size"]
        pct = s["pct_never_watched"]
        pct_color = "red" if pct >= 75 else "yellow" if pct >= 25 else "dim"
        unwatched = s["never_watched_count"] + s["partial_count"]

        seasons = s["unwatched_seasons"]
        if pct >= 100:
            season_str = "All"
        elif len(seasons) > 5:
            season_str = (
                ", ".join(f"S{n}" for n in seasons[:4]) + f" (+{len(seasons) - 4} more)"
            )
        else:
            season_str = ", ".join(f"S{n}" for n in seasons) or "—"

        table.add_row(
            s["title"],
            str(s["total_episodes"]),
            f"[red]{unwatched}[/]",
            f"[green]{s['fully_watched_count']}[/]",
            f"[{pct_color}]{pct:.0f}%[/]",
            fmt_date(s["last_watched"]),
            f"[bold]{fmt_size(wasted)}[/]",
            f"[red]{season_str}[/]" if season_str != "—" else "—",
        )
    console.print(table)


# ── CLI ───────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze Plex unwatched media via Tautulli + Plex APIs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--plex-url",
        metavar="URL",
        help="Plex base URL, e.g. http://192.168.1.10:32400 or https://plex.example.com",
    )
    parser.add_argument(
        "--plex-token", metavar="TOKEN", help="Plex authentication token (X-Plex-Token)"
    )
    parser.add_argument(
        "--tautulli-url",
        metavar="URL",
        help="Tautulli base URL, e.g. http://192.168.1.10:8181",
    )
    parser.add_argument("--tautulli-key", metavar="KEY", help="Tautulli API key")
    parser.add_argument(
        "--top",
        type=int,
        default=DEFAULT_TOP,
        metavar="N",
        help=f"Top N results per section (default: {DEFAULT_TOP})",
    )
    parser.add_argument(
        "--min-size",
        type=int,
        default=DEFAULT_MIN_SIZE_MB,
        metavar="MB",
        help=f"Minimum file size in MB to include (default: {DEFAULT_MIN_SIZE_MB})",
    )
    parser.add_argument("--movies-only", action="store_true")
    parser.add_argument("--shows-only", action="store_true")
    parser.add_argument(
        "--movie-max-plays",
        type=int,
        metavar="N",
        default=None,
        help="Only show movies with N or fewer total plays (e.g. 0=never, 2=watched ≤2 times)",
    )
    parser.add_argument(
        "--show-max-watched-pct",
        type=int,
        metavar="N",
        default=None,
        help="Only show TV shows where at most N%% of episodes have been watched (e.g. 10)",
    )
    parser.add_argument(
        "--ignore-recent-days",
        type=int,
        metavar="N",
        default=None,
        help="Exclude media with any watch activity in the last N days (e.g. 365 for 1 year)",
    )
    parser.add_argument(
        "--exclude-library",
        action="append",
        dest="exclude_libraries",
        metavar="NAME",
        help="Exclude a Plex library by name (case-insensitive). Can be passed multiple times. "
        "Defaults to excluding 'Sports' if not specified.",
    )
    parser.add_argument(
        "--env-file",
        metavar="PATH",
        default=".env",
        help="Path to .env config file (default: .env in current directory)",
    )
    return parser.parse_args()


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    args = parse_args()

    global ENV_FILE
    ENV_FILE = Path(args.env_file)

    cfg = resolve_config(args)

    missing = [k for k, v in cfg.items() if not v]
    if missing:
        console.print(f"[bold red]Missing config:[/] {', '.join(missing)}")
        console.print(
            "  Set via CLI flags, a .env file, or environment variables.\n"
            "  See --help for details."
        )
        sys.exit(1)

    min_size_bytes = args.min_size * 1024 * 1024

    exclude_libraries = args.exclude_libraries or DEFAULT_EXCLUDE_LIBRARIES

    console.print()
    console.print(f"[bold]Plex:[/]      {cfg['plex_url']}")
    console.print(f"[bold]Tautulli:[/]  {cfg['tautulli_url']}")
    console.print(
        f"[bold]Watched threshold:[/]         {int(WATCHED_THRESHOLD * 100)}% progress = watched"
    )
    console.print(
        "[bold]Unwatched season threshold:[/] all eps unwatched = season flagged"
    )
    console.print(f"[bold]Top results:[/]               {args.top}")
    console.print(
        f"[bold]Env file:[/]                  {ENV_FILE}"
        f" ({'found' if ENV_FILE.exists() else 'not found'})"
    )
    if args.min_size:
        console.print(f"[bold]Min size:[/]                  {args.min_size} MB")
    if args.movie_max_plays is not None:
        console.print(f"[bold]Movie max plays:[/]           {args.movie_max_plays}")
    if args.show_max_watched_pct is not None:
        console.print(
            f"[bold]Show max watched:[/]          {args.show_max_watched_pct}%"
        )
    if args.ignore_recent_days is not None:
        console.print(
            f"[bold]Ignore recent activity:[/]    last {args.ignore_recent_days} days"
        )
    if exclude_libraries:
        console.print(
            f"[bold]Excluding libraries:[/]       {', '.join(exclude_libraries)}"
        )
    console.print()

    tautulli_session = requests.Session()
    tautulli_session.headers.update({"Accept": "application/json"})
    plex_session = requests.Session()

    # Fetch data
    history = fetch_tautulli_history(
        tautulli_session, cfg["tautulli_url"], cfg["tautulli_key"]
    )
    console.print(f"  [dim]→ {len(history)} items with watch history[/]\n")

    raw_movies, raw_episodes = fetch_all_plex_media(
        plex_session,
        cfg["plex_url"],
        cfg["plex_token"],
        exclude_libraries=exclude_libraries,
    )
    console.print(
        f"  [dim]→ {len(raw_movies)} movies, {len(raw_episodes)} episodes from Plex[/]\n"
    )

    # Analyze
    movies = (
        [] if args.shows_only else analyze_movies(raw_movies, history, min_size_bytes)
    )
    shows = (
        [] if args.movies_only else analyze_shows(raw_episodes, history, min_size_bytes)
    )

    if args.movie_max_plays is not None:
        movies = [m for m in movies if m["play_count"] <= args.movie_max_plays]

    if args.show_max_watched_pct is not None:
        shows = [
            s
            for s in shows
            if s["total_episodes"] > 0
            and (s["fully_watched_count"] / s["total_episodes"] * 100)
            <= args.show_max_watched_pct
        ]

    if args.ignore_recent_days is not None:
        cutoff = datetime.now().timestamp() - (args.ignore_recent_days * 86400)
        movies = [
            m for m in movies if m["last_watched"] == 0 or m["last_watched"] < cutoff
        ]
        shows = [
            s for s in shows if s["last_watched"] == 0 or s["last_watched"] < cutoff
        ]

    # Build filter descriptions for summary
    movie_filters: list[str] = []
    show_filters: list[str] = []
    if args.min_size:
        movie_filters.append(f"min size {args.min_size} MB")
        show_filters.append(f"min size {args.min_size} MB")
    if args.movie_max_plays is not None:
        movie_filters.append(f"max {args.movie_max_plays} plays")
    if args.show_max_watched_pct is not None:
        show_filters.append(f"max {args.show_max_watched_pct}% watched")
    if args.ignore_recent_days is not None:
        recent_label = f"no activity in last {args.ignore_recent_days} days"
        movie_filters.append(recent_label)
        show_filters.append(recent_label)

    # Render
    render_summary(
        movies,
        shows,
        movie_filters=movie_filters or None,
        show_filters=show_filters or None,
    )
    console.print()

    if not args.shows_only:
        render_movies_table(movies, args.top)
        console.print()

    if not args.movies_only:
        render_shows_table(shows, args.top)
        console.print()


if __name__ == "__main__":
    main()
