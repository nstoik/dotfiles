# Python Scripts

Personal Python scripts symlinked to `~/python_scripts` via the `python-scripts` dotbot config.

## Requirements

- Python 3.10+ (scripts use `X | Y` union type syntax)
- Dependencies are per-script via `requirements.txt`

## Running a Script

```bash
cd ~/python_scripts/<script-dir>
pip install -r requirements.txt   # first time only
python3 <script>.py --help
```

If you use `pipx` and the dependencies are already installed globally, you can run directly:

```bash
python3 ~/python_scripts/<script-dir>/<script>.py
```

## Dev Tooling — Ruff

All scripts use [Ruff](https://docs.astral.sh/ruff/) for formatting and linting.
Ruff replaces both Black (formatter) and Flake8 (linter) in a single tool.

Config lives at `python_scripts/ruff.toml` (deployed to `~/python_scripts/ruff.toml`).

### Install Ruff

```bash
pipx install ruff          # or: pip install ruff
```

### Run manually

```bash
ruff format python_scripts/   # format all scripts
ruff check python_scripts/    # lint all scripts
ruff check --fix python_scripts/  # lint + auto-fix
```

### VS Code

Install the [Ruff extension](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff):

```
ext install charliermarsh.ruff
```

The extension bundles its own Ruff binary — no separate `ruff` install is needed for VS Code to work.
A standalone install (see above) is only needed if you want to run `ruff` from the terminal manually.

Add to your VS Code **User Settings** (`settings.json`):

```json
"[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true
}
```

If you previously had the Flake8 or Black extensions enabled for Python, disable or uninstall them —
Ruff covers both.

Pylance remains active alongside Ruff for type checking and IntelliSense. They don't conflict.

## Scripts

### `plex_unwatched/plex_unwatched.py`

Analyzes Plex media for unwatched or rarely-watched content using the Tautulli and Plex APIs.
Cross-references watch history with live file sizes to identify reclaimable disk space.

**Dependencies:** `requests`, `rich`

**Config** (CLI flags, `.env` file, or environment variables):

| Variable | Flag | Description |
|----------|------|-------------|
| `PLEX_URL` | `--plex-url` | Plex base URL |
| `PLEX_TOKEN` | `--plex-token` | Plex auth token |
| `TAUTULLI_URL` | `--tautulli-url` | Tautulli base URL |
| `TAUTULLI_API_KEY` | `--tautulli-key` | Tautulli API key |

Copy `.env.example` to `.env` in the script directory and fill in values.

**Key flags:**

```
--top N                   Show top N results (default: 30)
--min-size MB             Minimum file size to include
--movies-only / --shows-only
--movie-max-plays N       Only movies with ≤ N plays
--show-max-watched-pct N  Only shows with ≤ N% of episodes watched
--ignore-recent-days N    Exclude media with activity in the last N days
--exclude-library NAME    Skip a Plex library by name (default: Sports)
```
