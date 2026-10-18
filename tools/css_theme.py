#!/usr/bin/env python3
"""Summarize recovered CSS palettes and structural signals without publishing vendor CSS."""
import collections
import json
import re
from pathlib import Path

def profile(folder: Path):
    files = sorted(folder.glob("*.css"))
    palette=collections.Counter()
    vars=collections.Counter()
    font_faces=[]
    for f in files:
        s=f.read_text(encoding="utf-8",errors="replace")
        colors=collections.Counter(m.group(0).lower() for m in re.finditer(
            r"#[0-9a-fA-F]{3,8}\b",s
        ))
        palette.update(colors)
        vars.update(m.group(0) for m in re.finditer(r"--[A-Za-z][\w-]*\s*:",s))
        font_faces.extend(re.findall(r"font-family\s*:\s*(['\"]?)[^;'\"}]+\1",s)[:0])
        print(f.name, "bytes", f.stat().st_size, "top colors",colors.most_common(15))
    result={"file_count":len(files),"total_bytes":sum(x.stat().st_size for x in files),
       "top_colors":palette.most_common(50),"custom_properties":vars.most_common(40),
       "font_families_expected_from_zip":["Minecraft-Seven_v2","MinecraftSixteen","NotoSans","NotoSans-Bold"],
       "note":"Color statistics from binary-extracted CSS, not a redistributed original stylesheet."}
    return result

if __name__=="__main__":
    folder=Path(".cache/extracted-css")
    o=Path("reports/css-theme.json")
    o.parent.mkdir(parents=True,exist_ok=True)
    o.write_text(json.dumps(profile(folder),indent=2)+"\n")
    print("theme report:",o)
