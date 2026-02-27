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

SKIP_NAMES = {".DS_Store", "#recycle"}

TV_RE = re.compile(
    r"^(?P<show>.+?)(?:\.(?P<year>19\d{2}|20\d{2}))?\.S(?P<season>\d{2})E(?P<ep>\d{2})\b",
    re.IGNORECASE,
)
MOVIE_RE = re.compile(r"^(?P<title>.+?)\.(?P<year>19\d{2}|20\d{2})\b", re.IGNORECASE)

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
    LOG_FILE.open("a", encoding="utf-8").write(line)
    print(line, end="")


def audit(event: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    event = {"ts": now_iso(), **event}
    AUDIT_FILE.open("a", encoding="utf-8").write(json.dumps(event, ensure_ascii=False) + "\n")


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


def move_path(src: Path, dst: Path, run: bool) -> None:
    ensure_dir(dst.parent, run)
    if run:
        shutil.move(str(src), str(dst))
    log_line(f"move {src} -> {dst}")


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


def process_series_folder(folder: Path, run: bool) -> dict:
    release = folder.name
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
            move_path(v, dest_dir / v.name, run)
            moved_any = True
    elif extless:
        # rename using release name
        for f in extless:
            new_name = f"{release}.mkv"
            move_path(f, dest_dir / new_name, run)
            moved_any = True
    else:
        log_line(f"IRREGULAR: no rar/video files found in {folder}")
        return {**details, "status": "error", "reason": "no_media_found"}

    if moved_any:
        # recycle only after success
        recycle_dest = unique_recycle_dest(folder)
        ensure_dir(recycle_dest.parent, run)
        if run:
            shutil.move(str(folder), str(recycle_dest))
        log_line(f"recycle {folder} -> {recycle_dest}")
        details["recycled_to"] = str(recycle_dest)

    return details


def process_movie_folder(folder: Path, run: bool) -> dict:
    release = folder.name
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
            move_path(v, dest_dir / v.name, run)
            moved_any = True
    elif extless:
        for f in extless:
            new_name = f"{release}.mkv"
            move_path(f, dest_dir / new_name, run)
            moved_any = True
    else:
        log_line(f"IRREGULAR: no rar/video files found in {folder}")
        return {**details, "status": "error", "reason": "no_media_found"}

    if moved_any:
        recycle_dest = unique_recycle_dest(folder)
        ensure_dir(recycle_dest.parent, run)
        if run:
            shutil.move(str(folder), str(recycle_dest))
        log_line(f"recycle {folder} -> {recycle_dest}")
        details["recycled_to"] = str(recycle_dest)

    return details


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true", help="Perform changes (default is dry-run)")
    args = ap.parse_args()

    run = bool(args.run)

    # sanity checks
    for p in [SRC_SERIES, SRC_MOVIES, DST_TV, DST_MOVIES, CODA_HOME]:
        if not p.exists():
            log_line(f"ERROR missing path: {p}")
            return 2

    log_line(f"process-downloads start mode={'RUN' if run else 'DRY_RUN'}")
    audit({"event": "start", "mode": "run" if run else "dry"})

    results: list[dict] = []

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
    err = sum(1 for r in results if r.get("status") != "ok")
    log_line(f"process-downloads done ok={ok} error={err}")
    audit({"event": "done", "ok": ok, "error": err})

    return 0 if err == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
