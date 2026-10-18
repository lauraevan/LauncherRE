#!/usr/bin/env python3
"""Statically recover ZIP local-file entries embedded in the launcher for local analysis.

Only writes extracted CSS to ignored .cache/ by default, plus a metadata report.
Does not execute launcher code, decrypt files, or publish extracted contents.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import struct
import zlib
from pathlib import Path
try:
    from .embedded_resources import local_headers
except ImportError:
    from embedded_resources import local_headers

CSS_PATH = re.compile(r"^launcher/static/css/[A-Za-z0-9_.-]+\.css$")
HTML_PATH = re.compile(r"^launcher/[A-Za-z0-9_.-]+\.html$")
LOCAL_STRUCT = "<IHHHHHIIIHH"

def inspect_css(data: bytes) -> dict:
    text = data.decode("utf-8", "replace")
    # approximate CSS summaries, do not commit third-party stylesheet contents
    import collections
    common_properties = collections.Counter(re.findall(
        r"(?<![-\w])([a-z-]{3,})\s*:", text, flags=re.IGNORECASE
    ))
    return {
        "utf8_valid": data.decode("utf-8", "replace").encode("utf-8") == data,
        "open_braces": text.count("{"), "close_braces": text.count("}"),
        "property_frequency": common_properties.most_common(25),
        "media_query_count": text.count("@media"),
        "keyframes_count": text.count("@keyframes"),
        "custom_properties_count": len(re.findall(r"--[a-zA-Z][\w-]*\s*:", text)),
    }

def inspect_entry(blob: bytes, header: dict, limit: int) -> dict:
    offset = header["offset"]
    _, version, flags, method, tm, dt, crc, csize, usize, nlen, xlen = struct.unpack_from(LOCAL_STRUCT, blob, offset)
    result = {"filename": header["filename"], "offset": offset, "method": method, "flags": flags,
              "compressed_size": csize, "declared_size": usize, "status": "unexamined"}
    if flags & 1:
        result["status"] = "encrypted"
        return result
    if flags & 8:
        result["status"] = "data_descriptor"
        return result
    if usize > limit or csize > limit or csize <= 0:
        result["status"] = "invalid_size"
        return result
    start = offset + 30 + nlen + xlen
    if start + csize > len(blob):
        result["status"] = "outside_file"
        return result
    payload = blob[start:start+csize]
    try:
        if method == 0:
            data = payload
        elif method == 8:
            decompressor = zlib.decompressobj(-zlib.MAX_WBITS)
            data = decompressor.decompress(payload, limit + 1)
            data += decompressor.flush()
            if not decompressor.eof:
                raise ValueError("deflate stream did not end")
        else:
            result["status"] = "unsupported_method"
            return result
    except (zlib.error, ValueError) as exc:
        result["status"] = "decompression_failed"
        result["error"] = str(exc)
        return result
    actual_crc = zlib.crc32(data) & 0xffffffff
    result.update({
        "actual_size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
        "crc32_ok": actual_crc == crc, "size_ok": len(data) == usize
    })
    result["status"] = "verified" if len(data) == usize and actual_crc == crc else "integrity_failure"
    if result["status"] == "verified":
        result["content"] = data
    return result

def analyze(binary: Path, output: Path, local_css_root: Path) -> dict:
    blob = binary.read_bytes()
    signatures, candidates = local_headers(blob)
    selected = [h for h in candidates if CSS_PATH.fullmatch(h["filename"]) or HTML_PATH.fullmatch(h["filename"])]
    report = {"binary_path": str(binary), "binary_size": len(blob), "pk_signatures": signatures,
              "header_candidates": len(candidates), "selected_files": [], "css_extracted": 0}
    for item in selected:
        result = inspect_entry(blob, item, 12_000_000)
        if result.get("status") == "verified":
            data = result.pop("content")
            if result["filename"].endswith(".css"):
                # store local bytes for the user's own inspection, never commit/deploy automatically
                filename = Path(result["filename"]).name
                local_css_root.mkdir(parents=True, exist_ok=True)
                (local_css_root / filename).write_bytes(data)
                result["css_analysis"] = inspect_css(data)
                report["css_extracted"] += 1
            else:
                result["contains_script_tag"] = b"<script" in data
        report["selected_files"].append(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Found {report['header_candidates']} plausible ZIP headers, examined {len(selected)} CSS/HTML entries")
    for entry in report["selected_files"]:
        print(entry["filename"], entry["status"], entry.get("actual_size", 0))
    print(f"Verified CSS files available for private local analysis: {report['css_extracted']}")
    return report

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("binary", nargs="?", default=".cache/launcher/liblauncher.so")
    p.add_argument("--report", default="reports/css-analysis.json")
    p.add_argument("--local-css-root", default=".cache/extracted-css")
    args = p.parse_args()
    analyze(Path(args.binary), Path(args.report), Path(args.local_css_root))
