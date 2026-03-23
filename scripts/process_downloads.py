#!/usr/bin/env python3
"""Process media downloads from the Synology NAS.

Source:
  /mnt/jace_complete/Series
  /mnt/jace_complete/Movies

Dest:
  /mnt/jace_media/Video/TV/{Show}/Season XX/
  /mnt/jace_media/Video/Movies/{Movie (Year)}/

Behavior:
  - dry-run by default; use --run to perform changes
  - only move the source folder to #recycle on *clean success*
  - on irregularities/errors: log and leave source in place

Logs:
  /mnt/jace_coda/logs/process-downloads.log
  /mnt/jace_coda/logs/process-downloads.audit.jsonl
"""

from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

COMPLETE = Path("/mnt/jace_complete")
MEDIA = Path("/mnt/jace_media")
CODA_HOME = Path("/mnt/jace_coda")

SRC_SERIES = COMPLETE / "Series"
SRC_MOVIES = COMPLETE / "Movies"
DST_TV = MEDIA / "Video" / "TV"
DST_MOVIES = MEDIA / "Video" / "Movies"
RECYCLE = COMPLETE / "#recycle" / "process-downloads"

LOG_DIR = CODA_HOME / "logs"
LOG_FILE = LOG_DIR / "process-downloads.log"
AUDIT_FILE = LOG_DIR / "process-downloads.audit.jsonl"

# Prevent concurrent runs (cron/UI double-fires, gateway restarts, etc.)
LOCK_PATH = Path("/tmp/process-downloads.lock")

SKIP_NAMES = {".DS_Store", "#recycle", "Books", "Default", "Music"}

TV_RE = re.compile(
    r"^(?P<show>.+?)(?:[. ](?P<year>19\d{2}|20\d{2}))?[. ]S(?P<season>\d{2})E(?P<ep>\d{2})\b",
    re.IGNORECASE,
)
# Matches both "Title.Year" and "Title (Year)" folder formats
MOVIE_RE = re.compile(
    r"^(?P<title>.+?)(?:\.| \()(?P<year>19\d{2}|20\d{2})\b",
    re.IGNORECASE,
)

VIDEO_EXTS = {".mkv", ".mp4", ".avi", ".mov", ".m4v", ".wmv"}


@dataclass
class ParsedTV:
    show: str
    year: Optional[int]
    season: int
    episode: int


@dataclass
class ParsedMovie:
    title: str
    year: int


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def log_line(msg: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}\n"
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line)
    print(line, end="")


def audit(event: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    event = {"ts": now_iso(), **event}
    with AUDIT_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def slug_to_name(s: str) -> str:
    # Release names are dot-separated; keep some punctuation but normalize whitespace.
    s = s.replace(".", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_tv(release: str) -> Optional[ParsedTV]:
    m = TV_RE.match(release)
    if not m:
        return None
    show = slug_to_name(m.group("show"))
    year = int(m.group("year")) if m.group("year") else None
    season = int(m.group("season"))
    episode = int(m.group("ep"))
    return ParsedTV(show=show, year=year, season=season, episode=episode)


def parse_movie(release: str) -> Optional[ParsedMovie]:
    m = MOVIE_RE.match(release)
    if not m:
        return None
    title = slug_to_name(m.group("title"))
    year = int(m.group("year"))
    return ParsedMovie(title=title, year=year)


def iter_items(src_root: Path) -> Iterable[Path]:
    if not src_root.exists():
        return
    for p in sorted(src_root.iterdir()):
        if p.name in SKIP_NAMES:
            continue
        if p.name.startswith("."):
            continue
        yield p


def find_first_rar(root: Path) -> Optional[Path]:
    for p in root.rglob("*.rar"):
        if p.is_file():
            return p
    return None


def find_video_files(root: Path) -> list[Path]:
    vids: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() in VIDEO_EXTS:
            vids.append(p)
    return vids


def purge_exe_files(root: Path, run: bool) -> int:
    """Delete any .exe files found recursively under root. Returns count deleted."""
    count = 0
    for p in root.rglob("*.exe"):
        if not p.is_file():
            continue
        log_line(f"MALWARE purge: {p}")
        if run:
            p.unlink()
        count += 1
    return count


def find_existing_show(show: str, year: Optional[int]) -> Optional[Path]:
    """Return an existing show folder in DST_TV matching show name (exact, then year-qualified, then prefix)."""
    if not DST_TV.exists():
        return None
    candidates = [show]
    if year:
        candidates.append(f"{show} ({year})")
    for name in candidates:
        p = DST_TV / name
        if p.is_dir():
            return p
    # case-insensitive prefix fallback
    lower = show.lower()
    for p in sorted(DST_TV.iterdir()):
        if p.is_dir() and p.name.lower().startswith(lower):
            return p
    return None


def find_large_extensionless(root: Path, min_bytes: int = 100 * 1024 * 1024) -> list[Path]:
    out: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix != "":
            continue
        try:
            if p.stat().st_size >= min_bytes:
                out.append(p)
        except FileNotFoundError:
            continue
    return out


def run_cmd(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return proc.returncode, proc.stdout


def ensure_dir(path: Path, run: bool) -> None:
    if path.exists():
        return
    if run:
        path.mkdir(parents=True, exist_ok=True)
    log_line(f"mkdir -p {path}")


def move_path(src: Path, dst: Path, run: bool) -> bool:
    """Move src to dst. Returns True if moved/deleted, False if src vanished.

    If dst already exists (e.g. Sonarr already placed the file), the source
    is deleted to avoid leaving duplicates behind.
    """
    # Destination already exists — delete the source duplicate.
    if dst.exists():
        log_line(f"DELETE src (already at dest): {src}")
        if run:
            src.unlink(missing_ok=True)
        return True
    ensure_dir(dst.parent, run)
    if run:
        try:
            shutil.move(str(src), str(dst))
        except FileNotFoundError:
            # Source vanished between detection and move — likely moved by Sonarr.
            log_line(f"SKIP (src vanished, likely moved externally): {src}")
            return False
    log_line(f"move {src} -> {dst}")
    return True


def extract_rar(rar: Path, dest_dir: Path, run: bool) -> tuple[bool, str]:
    ensure_dir(dest_dir, run)
    cmd = ["unrar", "e", "-o+", str(rar), str(dest_dir)]
    log_line("unrar " + " ".join(cmd[1:]))
    if not run:
        return True, "DRY_RUN"
    code, out = run_cmd(cmd)
    return code == 0, out


def unique_recycle_dest(src_folder: Path) -> Path:
    date = dt.datetime.now().strftime("%Y-%m-%d")
    base = RECYCLE / date / src_folder.name
    if not base.exists():
        return base
    # deconflict
    for i in range(1, 1000):
        cand = RECYCLE / date / f"{src_folder.name}.{i}"
        if not cand.exists():
            return cand
    return RECYCLE / date / f"{src_folder.name}.{os.getpid()}"


def process_straggler(item: Path, run: bool) -> dict:
    """Handle a folder or file found directly in the COMPLETE root (outside Series/Movies)."""
    release = item.name
    details_base: dict = {"path": str(item), "release": release}

    # --- folder straggler ---
    if item.is_dir():
        # Purge malware first
        purge_exe_files(item, run)

        tv = parse_tv(release)
        if tv:
            # Check if the show already exists in DST_TV to confirm it's a TV release
            existing = find_existing_show(tv.show, tv.year)
            if existing:
                log_line(f"STRAGGLER TV (matched existing show '{existing.name}'): {release} -> Series/")
            else:
                log_line(f"STRAGGLER TV (new show, treating as series): {release} -> Series/")
            # Delegate to normal series processor (it handles dest dir creation)
            return process_series_folder(item, run)

        movie = parse_movie(release)
        if movie:
            log_line(f"STRAGGLER Movie: {release} -> Movies/")
            return process_movie_folder(item, run)

        log_line(f"STRAGGLER unclassified folder (can't parse as TV or movie): {release}")
        # Still recycle the folder so it doesn't linger in the source tree
        recycle_dest = unique_recycle_dest(item)
        ensure_dir(recycle_dest.parent, run)
        if run:
            shutil.move(str(item), str(recycle_dest))
        log_line(f"recycle (unclassified) {item} -> {recycle_dest}")
        return {**details_base, "kind": "straggler", "status": "error", "reason": "unclassified", "recycled_to": str(recycle_dest)}

    # --- loose file straggler ---
    if item.is_file():
        if item.suffix.lower() == ".exe":
            log_line(f"MALWARE purge (root): {item}")
            if run:
                item.unlink()
            return {**details_base, "kind": "straggler", "status": "ok", "reason": "malware_purged"}

        if item.suffix.lower() not in VIDEO_EXTS:
            log_line(f"STRAGGLER skipping non-video file: {item.name}")
            return {**details_base, "kind": "straggler", "status": "skipped", "reason": "not_video"}

        # Bare video file — try to classify by filename
        stem = item.stem
        tv = parse_tv(stem)
        if tv:
            show_folder = tv.show if tv.year is None else f"{tv.show} ({tv.year})"
            # Prefer existing show dir if found
            existing = find_existing_show(tv.show, tv.year)
            if existing:
                show_folder = existing.name
            season_folder = f"Season {tv.season:02d}"
            dest_dir = DST_TV / show_folder / season_folder
            log_line(f"STRAGGLER loose TV file -> {dest_dir / item.name}")
            moved = move_path(item, dest_dir / item.name, run)
            status = "ok" if moved else "skipped"
            return {**details_base, "kind": "tv", "status": status, "dest": str(dest_dir)}

        movie = parse_movie(stem)
        if movie:
            movie_folder = f"{movie.title} ({movie.year})"
            dest_dir = DST_MOVIES / movie_folder
            log_line(f"STRAGGLER loose movie file -> {dest_dir / item.name}")
            moved = move_path(item, dest_dir / item.name, run)
            status = "ok" if moved else "skipped"
            return {**details_base, "kind": "movie", "status": status, "dest": str(dest_dir)}

        log_line(f"STRAGGLER loose file unclassified: {item.name}")
        return {**details_base, "kind": "straggler", "status": "error", "reason": "unclassified"}

    return {**details_base, "kind": "straggler", "status": "skipped", "reason": "not_file_or_dir"}


def process_series_folder(folder: Path, run: bool) -> dict:
    release = folder.name
    # Purge any malware before processing
    purge_exe_files(folder, run)
    parsed = parse_tv(release)
    if not parsed:
        msg = f"IRREGULAR TV name (can't parse): {release}"
        log_line(msg)
        return {"kind": "tv", "release": release, "status": "error", "reason": "unparseable", "path": str(folder)}

    show_folder = parsed.show if parsed.year is None else f"{parsed.show} ({parsed.year})"
    season_folder = f"Season {parsed.season:02d}"
    dest_dir = DST_TV / show_folder / season_folder

    ensure_dir(dest_dir, run)

    # decide what to do
    rar = find_first_rar(folder)
    vids = find_video_files(folder)
    extless = find_large_extensionless(folder)

    moved_any = False
    details: dict = {"kind": "tv", "release": release, "status": "ok", "dest": str(dest_dir), "path": str(folder)}

    if rar:
        ok, out = extract_rar(rar, dest_dir, run)
        if not ok:
            log_line(f"ERROR unrar failed for {rar} (leaving source)")
            audit({"event": "unrar_failed", "release": release, "rar": str(rar), "output": out[-2000:]})
            return {**details, "status": "error", "reason": "unrar_failed"}
        moved_any = True
    elif vids:
        for v in vids:
            if move_path(v, dest_dir / v.name, run):
                moved_any = True
    elif extless:
        # rename using release name
        for f in extless:
            new_name = f"{release}.mkv"
            if move_path(f, dest_dir / new_name, run):
                moved_any = True
    else:
        log_line(f"IRREGULAR: no rar/video files found in {folder}")
        # Nothing processable (e.g. malware purged, folder now empty) — still recycle the shell
        recycle_dest = unique_recycle_dest(folder)
        ensure_dir(recycle_dest.parent, run)
        if run:
            shutil.move(str(folder), str(recycle_dest))
        log_line(f"recycle (no-media) {folder} -> {recycle_dest}")
        return {**details, "status": "error", "reason": "no_media_found", "recycled_to": str(recycle_dest)}

    if moved_any:
        # recycle only after success
        recycle_dest = unique_recycle_dest(folder)
        ensure_dir(recycle_dest.parent, run)
        if run:
            shutil.move(str(folder), str(recycle_dest))
        log_line(f"recycle {folder} -> {recycle_dest}")
        details["recycled_to"] = str(recycle_dest)
    else:
        # All files were already at destination (externally moved) — treat as ok/skipped
        log_line(f"SKIP (all files already at dest or src vanished): {folder}")
        details["status"] = "skipped"

    return details


def process_movie_folder(folder: Path, run: bool) -> dict:
    release = folder.name
    # Purge any malware before processing
    purge_exe_files(folder, run)
    parsed = parse_movie(release)
    if not parsed:
        msg = f"IRREGULAR Movie name (can't parse year): {release}"
        log_line(msg)
        return {"kind": "movie", "release": release, "status": "error", "reason": "unparseable", "path": str(folder)}

    movie_folder = f"{parsed.title} ({parsed.year})"
    dest_dir = DST_MOVIES / movie_folder
    ensure_dir(dest_dir, run)

    rar = find_first_rar(folder)
    vids = find_video_files(folder)
    extless = find_large_extensionless(folder)

    details: dict = {"kind": "movie", "release": release, "status": "ok", "dest": str(dest_dir), "path": str(folder)}
    moved_any = False

    if rar:
        ok, out = extract_rar(rar, dest_dir, run)
        if not ok:
            log_line(f"ERROR unrar failed for {rar} (leaving source)")
            audit({"event": "unrar_failed", "release": release, "rar": str(rar), "output": out[-2000:]})
            return {**details, "status": "error", "reason": "unrar_failed"}
        moved_any = True
    elif vids:
        for v in vids:
            if move_path(v, dest_dir / v.name, run):
                moved_any = True
    elif extless:
        for f in extless:
            new_name = f"{release}.mkv"
            if move_path(f, dest_dir / new_name, run):
                moved_any = True
    else:
        log_line(f"IRREGULAR: no rar/video files found in {folder}")
        # Nothing processable (e.g. malware purged, folder now empty) — still recycle the shell
        recycle_dest = unique_recycle_dest(folder)
        ensure_dir(recycle_dest.parent, run)
        if run:
            shutil.move(str(folder), str(recycle_dest))
        log_line(f"recycle (no-media) {folder} -> {recycle_dest}")
        return {**details, "status": "error", "reason": "no_media_found", "recycled_to": str(recycle_dest)}

    if moved_any:
        recycle_dest = unique_recycle_dest(folder)
        ensure_dir(recycle_dest.parent, run)
        if run:
            shutil.move(str(folder), str(recycle_dest))
        log_line(f"recycle {folder} -> {recycle_dest}")
        details["recycled_to"] = str(recycle_dest)
    else:
        # All files already at destination or source vanished — not an error
        log_line(f"SKIP (all files already at dest or src vanished): {folder}")
        details["status"] = "skipped"

    return details


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true", help="Perform changes (default is dry-run)")
    args = ap.parse_args()

    run = bool(args.run)

    # best-effort single-instance lock
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    lock_fh = LOCK_PATH.open("w")
    try:
        fcntl.flock(lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        # Another instance is already running; don't pile on.
        try:
            log_line("process-downloads: lock held; another instance is running (skipping)")
        except Exception:
            pass
        return 0

    # sanity checks
    for p in [SRC_SERIES, SRC_MOVIES, DST_TV, DST_MOVIES, CODA_HOME]:
        if not p.exists():
            log_line(f"ERROR missing path: {p}")
            return 2

    log_line(f"process-downloads start mode={'RUN' if run else 'DRY_RUN'}")
    audit({"event": "start", "mode": "run" if run else "dry"})

    results: list[dict] = []

    # process straggler items dropped directly into the COMPLETE root
    for item in iter_items(COMPLETE):
        # skip the Series/, Movies/, and #recycle/ subdirs — handled below
        if item.name in {"Series", "Movies", "#recycle"}:
            continue
        log_line(f"STRAGGLER found in complete root: {item.name}")
        r = process_straggler(item, run)
        results.append(r)
        audit({"event": "straggler", **r})

    # process Series folders (each release is usually its own folder)
    for item in iter_items(SRC_SERIES):
        if not item.is_dir():
            continue
        r = process_series_folder(item, run)
        results.append(r)
        audit({"event": "item", **r})

    for item in iter_items(SRC_MOVIES):
        if not item.is_dir():
            continue
        r = process_movie_folder(item, run)
        results.append(r)
        audit({"event": "item", **r})

    ok = sum(1 for r in results if r.get("status") == "ok")
    skipped = sum(1 for r in results if r.get("status") == "skipped")
    err = sum(1 for r in results if r.get("status") not in ("ok", "skipped"))
    log_line(f"process-downloads done ok={ok} skipped={skipped} error={err}")
    audit({"event": "done", "ok": ok, "skipped": skipped, "error": err})

    return 0 if err == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
