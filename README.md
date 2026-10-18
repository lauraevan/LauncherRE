# LauncherRE

Research workspace and reproducible tooling for studying the **official Minecraft Launcher**, with an emphasis on its modern Chromium Embedded Framework (CEF) interface. The objective is to document and eventually reconstruct launcher behavior in readable, independently maintained code, with a browser-based UI as a possible target.

## Browser preview (independent CSS)

**[Open LauncherRE frontend preview](https://raw.githack.com/lauraevan/LauncherRE/main/preview/index.html)** · [Source HTML](preview/index.html) · [Editable CSS](preview/style.css) · [JavaScript](preview/app.js)

A deployable, static browser research preview is available from the public GitHub repository through RawGitHack. Its tabs, navigation and UI-only controls are interactive, but it does **not** launch Minecraft. This is **independently authored CSS**, not a verbatim distribution of Mojang's stylesheets. Some styling remains provisional pending deeper UI verification.

Official launcher CSS recovery has succeeded: **six real 2026 CSS files were individually decompressed and CRC/size-verified** from the Mojang-distributed `liblauncher.so`. The original CSS is available through a **short-lived GitHub Actions research artifact** (see [probe runs](https://github.com/lauraevan/LauncherRE/actions/workflows/probe.yml)) rather than being committed as public source. Re-run the probe to regenerate an expired artifact. No Mojang fonts are redistributed.

For future GitHub Pages publishing, enable **Settings → Pages → Build and deployment → GitHub Actions** on this repo, then manually trigger [preview.yml](.github/workflows/preview.yml). The workflow cannot enable Pages itself with its limited GitHub token.

## Current state (2026-10-18)

- **Verified:** Mojang's Redstone launcher distribution manifest at the pinned URL below lists 104 paths, including 24 `media/*.zip` asset archives, `liblauncher.so`, `libcef.so`, `resources.pak`, and Chromium support files.
- **Indexed:** filenames, SHA-1 identifiers and download sizes of all 24 official media archives are preserved under `data/`.
- **Tooling:** `tools/launcher_re.py` can retrieve manifests, download selected files, validate their SHA-1 hashes, inventory ZIP contents (including encrypted-entry flags), and scan locally available bundles for likely HTML/JS/CSS frontend files.
- **CSS recovered:** six 2026 CSS files and three HTML entry documents are individually verified after decompressing embedded ZIP entries with data descriptors. Metadata, byte hashes and theme profiles are recorded; extracted source files are not committed.
- **Not yet accomplished:** no original React source, main JavaScript bundle, or fully playable browser launcher has been reconstructed. A separate independently authored static preview is available. The pinned build was identified as launcher core **3.41.29**, dated **2026-10-12**; this is a specific research snapshot, not a promise of the newest build.

### Pinned primary source

```text
https://redstone-launcher.mojang.com/release/v2/packages/5d80e3741c770efb29509f2dabf74673449d4365/manifest.json
```

This is a Mojang-operated content distribution URL, not a third-party mirror. Manifest object URLs are SHA-1-addressed. **Do not mistake these launcher files for an open-source release**; fetching files is separate from permission to redistribute them.

## Usage

Python 3.10+; standard library only:

```sh
python tools/launcher_re.py inventory
python tools/launcher_re.py inventory --json
python tools/launcher_re.py fetch --select media --output .cache/launcher
python tools/launcher_re.py fetch --select frontend-candidates --output .cache/launcher
python tools/launcher_re.py inspect --root .cache/launcher --output reports/inspection.json
python tools/launcher_re.py scan --root .cache/launcher --output reports/strings.json
python -m unittest discover -s tests -v
```

By default, `inventory` reads the checked-in pinned manifest inventory and **needs no network connection**. `fetch` downloads directly from Mojang and verifies downloaded byte integrity against the manifest. `inspect` inventories ZIP metadata without attempting to break encryption; `scan` detects evidence of frontend paths in local text/native binaries.

All downloaded Mojang files stay in ignored local `.cache/` by default. Inspecting, extracting, or distributing proprietary content may be subject to license restrictions: keep this repository to our own tools, metadata, notes, and independently written reconstruction.

## Layout

- `data/mojang-manifest-2026-10-12.json`: pinned official manifest containing all 104 entries
- `data/media-2026-10-12.json`: verified metadata for the 24 media archives; **not extracted content**
- `tools/launcher_re.py`: manifest download, verification, ZIP inspection, frontend string scanning
- `tests/`: local tests for URL/ZIP safety, byte strings and manifest parsing
- `docs/findings.md`: evidence and research status
- `docs/next-steps.md`: practical investigation plan and reconstruction milestones
- `preview/`: static independently-authored frontend UI and CSS, directly viewable with RawGitHack
- `.github/workflows/probe.yml`: one-time GitHub-hosted static inspection of selected official files, uploading metadata reports only

## Related research

- Mojang's CEF fork: https://github.com/Mojang/cef (framework code, not launcher application source)
- CEF launcher asset research (2024): https://blog.mr.cringe-studios.com/01-minecraft-launcher
- Example historical CEF console log illustrating internal paths: https://github.com/imvickykumar999/TLauncher-Minecraft/blob/main/launcher_cef_log.txt

This project is unaffiliated with Mojang Studios or Microsoft. Minecraft is a trademark of Microsoft Corporation.
