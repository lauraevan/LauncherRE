#!/usr/bin/env python3
"""Read-only discovery of resource paths and possible ZIP local headers in a native binary.

Does not decompile or execute native code and never writes proprietary bytes.
"""
from __future__ import annotations

import argparse
import json
import re
import struct
from pathlib import Path

JS = re.compile(rb"launcher/static/js/[A-Za-z0-9_.-]+\.js")
CSS = re.compile(rb"launcher/static/css/[A-Za-z0-9_.-]+\.css")
MEDIA = re.compile(rb"launcher/static/media/[A-Za-z0-9_.-]+\.(?:png|svg|jpg|webp|woff2?)")
INTERNAL = re.compile(rb"https://mojang/launcher/[A-Za-z0-9_./-]+")
ZIP_SIGNATURE = b"PK\x03\x04"


def decode_matches(data: bytes, pattern: re.Pattern) -> list[str]:
    return sorted({match.group(0).decode("ascii") for match in pattern.finditer(data)})


def local_headers(data: bytes, max_headers: int = 5000) -> tuple[int, list[dict]]:
    """Best-effort ZIP local-file-header search (not a ZIP parser or extractor)."""
    positions = 0
    plausible: list[dict] = []
    cursor = 0
    while True:
        start = data.find(ZIP_SIGNATURE, cursor)
        if start < 0:
            break
        cursor = start + 4
        positions += 1
        if start + 30 > len(data):
            continue
        try:
            (
                signature, version, flags, method, modified_time,
                modified_date, crc32, comp_size, uncomp_size, name_size, extra_size
            ) = struct.unpack_from("<IHHHHHIIIHH", data, start)
        except struct.error:
            continue
        if (
            signature != 0x04034B50 or version > 100 or
            method not in (0, 8, 12, 14, 93, 99) or
            not (1 <= name_size <= 512) or extra_size > 65535 or
            start + 30 + name_size + extra_size > len(data)
        ):
            continue
        name_bytes = data[start + 30: start + 30 + name_size]
        if any(c < 32 or c == 127 for c in name_bytes):
            continue
        try:
            filename = name_bytes.decode("utf-8")
        except UnicodeDecodeError:
            filename = name_bytes.decode("cp437", "replace")
        plausible.append({
            "offset": start, "filename": filename, "method": method,
            "encrypted": bool(flags & 1), "compressed_size": comp_size,
            "uncompressed_size": uncomp_size,
            "header_uses_data_descriptor": bool(flags & 0x08),
            "version": version,
        })
        if len(plausible) >= max_headers:
            break
    return positions, plausible


def inspect(path: Path) -> dict:
    data = path.read_bytes()
    signatures, headers = local_headers(data)
    js = decode_matches(data, JS)
    css = decode_matches(data, CSS)
    media = decode_matches(data, MEDIA)
    internal = decode_matches(data, INTERNAL)
    return {
        "path": str(path), "size": len(data),
        "resource_paths": {
            "javascript": js, "css": css,
            "media": media, "internal_urls": internal,
        },
        "counts": {
            "javascript_paths": len(js), "css_paths": len(css),
            "media_paths": len(media), "internal_urls": len(internal),
            "pk_local_header_signatures": signatures,
            "plausible_local_file_headers": len(headers),
        },
        "plausible_zip_headers": headers,
        "note": "String references are not extracted source files. PK signatures may be false positives.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", nargs="?", default=".cache/launcher/liblauncher.so")
    parser.add_argument("--output", default="reports/embedded-resources.json")
    args = parser.parse_args()
    source = Path(args.binary)
    if source.stat().st_size > 100_000_000:
        parser.error("Binary exceeds 100 MB safety limit")
    result = inspect(source)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("Resource path counts:", result["counts"])
    print("CSS:", *result["resource_paths"]["css"], sep="\n  ")
    print("JS candidates excluding language chunks:")
    app_js = [
        x for x in result["resource_paths"]["javascript"]
        if "launcher-language" not in x
    ]
    print(*app_js[:100], sep="\n  ")
    print(f"JSON report: {destination}")


if __name__ == "__main__":
    main()
