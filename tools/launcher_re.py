#!/usr/bin/env python3
"""LauncherRE: inspect official Mojang launcher distribution metadata and local files.

Python 3.10+; no third-party dependencies. This does not decrypt archives,
reconstruct proprietary source, or run downloaded executables.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCK_FILE = REPO_ROOT / "data" / "media-2026-10-12.json"
PINNED_MANIFEST = (
    "https://redstone-launcher.mojang.com/release/v2/packages/"
    "5d80e3741c770efb29509f2dabf74673449d4365/manifest.json"
)
ALLOWED_HOST = "redstone-launcher.mojang.com"
MAX_MANIFEST_BYTES = 4_000_000
MAX_DOWNLOAD_BYTES = 350_000_000
INTERESTING = re.compile(
    rb"(?:mojang://|https://mojang/|launcher/static/|"
    rb"\b(?:app|main)\.[A-Za-z0-9_-]{5,}\.bundle\.js\b|"
    rb"\b(?:index\.html|bundle\.js|static/js|static/css|\.js\.map)\b|"
    rb"background\.zip|common\.zip)",
    re.IGNORECASE,
)
PRINTABLE = re.compile(rb"[\x20-\x7e]{6,512}")


def confined_path(root: Path, name: str) -> Path:
    """Reject absolute paths, traversal and unusual path separators."""
    if not isinstance(name, str) or not name or "\\" in name:
        raise ValueError(f"unsafe path: {name!r}")
    p = PurePosixPath(name)
    if p.is_absolute() or any(part in (".", "..") for part in p.parts):
        raise ValueError(f"unsafe path: {name!r}")
    dest = root.joinpath(*p.parts)
    if not dest.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"unsafe path: {name!r}")
    return dest


def validated_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != ALLOWED_HOST
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port is not None
        or not parsed.path.startswith("/release/v2/objects/")
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(f"Untrusted Mojang object URL: {url!r}")
    return url


def parse_entries(manifest: dict) -> dict[str, dict]:
    entries: dict[str, dict] = {}
    files = manifest.get("files")
    if not isinstance(files, dict):
        raise ValueError("Manifest is missing a files object")
    for path, info in files.items():
        confined_path(Path("/tmp/launcher-re-validation"), path)
        if not isinstance(info, dict):
            continue
        raw = info.get("downloads", {}).get("raw")
        if not isinstance(raw, dict):
            continue  # directory
        sha1 = raw.get("sha1")
        size = raw.get("size")
        url = raw.get("url")
        if (
            not isinstance(sha1, str)
            or not re.fullmatch(r"[0-9a-f]{40}", sha1)
            or not isinstance(size, int)
            or size < 0
            or size > MAX_DOWNLOAD_BYTES
            or not isinstance(url, str)
        ):
            raise ValueError(f"Invalid hash/size/URL in manifest: {path}")
        validated_url(url)
        entries[path] = {"sha1": sha1, "size": size, "url": url}
    return entries


def load_lock() -> dict:
    with LOCK_FILE.open(encoding="utf-8") as f:
        lock = json.load(f)
    return lock


def load_live_entries() -> dict[str, dict]:
    req = urllib.request.Request(
        PINNED_MANIFEST, headers={"User-Agent": "LauncherRE/0.1 (metadata research)"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        chunks = resp.read(MAX_MANIFEST_BYTES + 1)
    if len(chunks) > MAX_MANIFEST_BYTES:
        raise ValueError("Manifest exceeds allowed size")
    return parse_entries(json.loads(chunks))


def sha1_of_file(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_entry(path: str, meta: dict, dest_root: Path) -> str:
    url = validated_url(meta["url"])
    target = confined_path(dest_root, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file() and target.stat().st_size == meta["size"]:
        if sha1_of_file(target) == meta["sha1"]:
            return "verified-existing"
    temp = target.with_name(target.name + ".part")
    temp.unlink(missing_ok=True)
    h = hashlib.sha1()
    total = 0
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LauncherRE/0.1"})
        with urllib.request.urlopen(req, timeout=45) as src, temp.open("wb") as dst:
            final_url = src.geturl()
            validated_url(final_url)
            for chunk in iter(lambda: src.read(1024 * 1024), b""):
                total += len(chunk)
                if total > min(MAX_DOWNLOAD_BYTES, meta["size"]):
                    raise ValueError(f"unexpected download size: {path}")
                dst.write(chunk)
                h.update(chunk)
        if total != meta["size"] or h.hexdigest() != meta["sha1"]:
            raise ValueError(f"SHA-1/size mismatch: {path}")
        temp.replace(target)
        return "downloaded+verified"
    finally:
        temp.unlink(missing_ok=True)


def select_entries(entries: dict[str, dict], selector: str) -> dict[str, dict]:
    if selector == "media":
        return {k: v for k, v in entries.items() if k.startswith("media/")}
    if selector == "small":
        return {k: v for k, v in entries.items() if v["size"] <= 1_000_000}
    if selector == "frontend-candidates":
        preferred = {
            "media/common.zip", "media/icons.zip", "media/images.zip",
            "media/logos.zip", "media/fonts.zip", "resources.pak",
            "liblauncher.so",
        }
        return {k: v for k, v in entries.items() if k in preferred}
    if selector == "all":
        return entries
    if selector in entries:
        return {selector: entries[selector]}
    raise ValueError("Select media, small, frontend-candidates, all, or an exact manifest path")


def report_zip(path: Path, root: Path) -> dict:
    item: dict = {"path": str(path.relative_to(root))}
    try:
        with zipfile.ZipFile(path) as z:
            data = []
            unsafe = []
            encrypted = 0
            for info in z.infolist():
                # metadata only: never decrypt and never extract implicitly
                if info.flag_bits & 1:
                    encrypted += 1
                try:
                    confined_path(Path("/tmp/launcher-re-zip"), info.filename)
                except ValueError:
                    unsafe.append(info.filename)
                data.append({
                    "filename": info.filename,
                    "size": info.file_size,
                    "compressed_size": info.compress_size,
                    "encrypted": bool(info.flag_bits & 1),
                })
            item.update({
                "valid_zip": True,
                "entry_count": len(data),
                "encrypted_entries": encrypted,
                "unsafe_entries": unsafe,
                "entries": data,
            })
    except (zipfile.BadZipFile, OSError) as exc:
        item.update({"valid_zip": False, "error": str(exc)})
    return item


def ascii_matches(data: bytes, limit: int = 80) -> list[str]:
    result = []
    seen = set()
    for found in PRINTABLE.finditer(data):
        segment = found.group(0)
        if INTERESTING.search(segment):
            text = segment.decode("ascii", "replace").strip()
            if text not in seen:
                seen.add(text)
                result.append(text[:512])
                if len(result) >= limit:
                    break
    return result


def atomic_json_write(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(path)


def command_inventory(args: argparse.Namespace) -> None:
    if args.live:
        entries = load_live_entries()
        source = PINNED_MANIFEST
    else:
        lock = load_lock()
        entries = parse_entries({"files": {k: {"downloads": {"raw": v}} for k, v in lock["media"].items()}})
        source = LOCK_FILE.relative_to(REPO_ROOT).as_posix()
    data = {
        "source": source,
        "entries": len(entries),
        "total_bytes": sum(v["size"] for v in entries.values()),
        "files": entries,
    }
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(f"{len(entries)} files, {data['total_bytes']:,} bytes ({source})")
        for path, meta in sorted(entries.items()):
            print(f"{meta['size']:>12,}  {meta['sha1']}  {path}")


def command_fetch(args: argparse.Namespace) -> None:
    if args.live:
        entries = load_live_entries()
    else:
        pinned = json.loads(
            (REPO_ROOT / "data" / "mojang-manifest-2026-10-12.json").read_text(encoding="utf-8")
        )
        entries = parse_entries(pinned)
    selected = select_entries(entries, args.select)
    root = Path(args.output).resolve()
    success = failures = 0
    for name, meta in sorted(selected.items()):
        try:
            status = fetch_entry(name, meta, root)
            print(f"{status}: {name}")
            success += 1
        except (OSError, ValueError, urllib.error.URLError) as exc:
            print(f"ERROR: {name}: {exc}", file=sys.stderr)
            failures += 1
    print(f"Completed: {success} verified, {failures} failed; files in {root}")
    if failures:
        raise SystemExit(1)


def command_inspect(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    if not root.is_dir():
        raise ValueError(f"Directory not found: {root}")
    archives = [report_zip(path, root) for path in sorted(root.rglob("*.zip")) if path.is_file()]
    report = {"root": str(root), "archives": archives, "count": len(archives)}
    atomic_json_write(Path(args.output), report)
    print(f"Inspected {len(archives)} ZIP files; report: {args.output}")


def command_scan(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    if not root.is_dir():
        raise ValueError(f"Directory not found: {root}")
    extensions = {".html", ".js", ".css", ".json", ".pak", ".so", ".dll", ".bin", ".a"}
    results = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in extensions:
            continue
        if path.stat().st_size > MAX_DOWNLOAD_BYTES:
            continue
        try:
            hits = ascii_matches(path.read_bytes())
        except OSError:
            continue
        if hits:
            results.append({"path": str(path.relative_to(root)), "matches": hits})
    atomic_json_write(Path(args.output), {"root": str(root), "matches": results})
    print(f"Found possible frontend references in {len(results)} files; report: {args.output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    inv = sub.add_parser("inventory", help="Show pinned archive metadata (offline) or live manifest")
    inv.add_argument("--live", action="store_true", help="Read pinned URL live instead of checked-in archive inventory")
    inv.add_argument("--json", action="store_true")
    fet = sub.add_parser("fetch", help="Download SHA-1-verified Mojang launcher files")
    fet.add_argument("--select", default="frontend-candidates", help="media|small|frontend-candidates|all|exact path")
    fet.add_argument("--output", default=".cache/launcher")
    fet.add_argument("--live", action="store_true",
                     help="Re-read pinned Mojang manifest URL; default uses checked-in metadata")
    ins = sub.add_parser("inspect", help="Record ZIP filenames/encryption status without decrypting/extracting")
    ins.add_argument("--root", default=".cache/launcher")
    ins.add_argument("--output", default="reports/inspection.json")
    sca = sub.add_parser("scan", help="Scan downloaded text/binaries for likely web frontend paths")
    sca.add_argument("--root", default=".cache/launcher")
    sca.add_argument("--output", default="reports/strings.json")
    args = parser.parse_args()
    try:
        {
            "inventory": command_inventory,
            "fetch": command_fetch,
            "inspect": command_inspect,
            "scan": command_scan,
        }[args.command](args)
    except (ValueError, OSError, urllib.error.URLError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
