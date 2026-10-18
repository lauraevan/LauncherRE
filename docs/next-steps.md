# LauncherRE roadmap

## Phase 1: establish a reproducible evidence base (started)

- Pin the official 3.41.29 Linux manifest and all asset object hashes.
- Use the \`fetch\` command to fetch a minimal asset group before attempting larger native binaries.
- Record whether \`common.zip\`, \`icons.zip\`, and \`images.zip\` are traditional ZIPs, which entries are encrypted, and how files are named.
- Hash-verify everything. Record errors instead of substituting another launcher version.

Suggested commands:

\`\`\`sh
python tools/launcher_re.py inventory
python tools/launcher_re.py fetch --select media/icons.zip
python tools/launcher_re.py fetch --select frontend-candidates
python tools/launcher_re.py inspect
python tools/launcher_re.py scan
\`\`\`

The default fetch selection does not execute downloaded code.

## Phase 2: locate the 2026 frontend

- Inspect the output of \`scan\` on \`liblauncher.so\`, \`resources.pak\` and related candidates for URL schemes, app bundle names and registration code.
- Do **not** assume a Chromium \`.pak\` is the React bundle. Inspect resource IDs and references first.
- If bundles are compressed, embedded, or served from a custom app resource handler, document offsets, encoding, and route mappings precisely.
- On a sandboxed local launcher installation, record frontend network/resource traffic and inspect Chromium devtools only when supported.
- Record every discovery as \`path + hash + evidence + confidence\` in a new research note.

## Phase 3: create an independent frontend reconstruction

Do not drop an old 2021 clone in as a substitute. Recreate current UI page-by-page from observed behavior:

1. Shell / global sidebar / settings / account switcher
2. Java Edition Play, Installations, Skins, Patch Notes
3. Bedrock entry and installation path, as supported by the target platform
4. Dungeons and other storefront sections visible in the observed build
5. Exact typography, artwork placement, scaling, hover/focus animations, accessibility and error states
6. Native-dependent actions as explicit interfaces, initially with offline mocks

A browser replica can reproduce the *launcher interface*. It cannot actually start a desktop JVM or a Windows Store game inside an ordinary browser tab without a separate suitable runtime/bridge.

## Research rules

- Keep this work version-pinned. Never silently mix archive sets from different manifests.
- Separate **proven facts**, **historical clues**, and **hypotheses**.
- Do not commit proprietary binaries, decrypted media, credentials or auth tokens.
- Do not represent framework source (\`Mojang/cef\`) as Mojang's launcher application source.
- Prefer small reproducible probes and unit tests before GUI imitation.
- Treat native files as potentially hostile to the research machine; static inspection is the default.
