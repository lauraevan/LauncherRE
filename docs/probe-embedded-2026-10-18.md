# Embedded-resource probe: 2026-10-18

**Successful run:** https://github.com/lauraevan/LauncherRE/actions/runs/39159394472

The automated runner re-downloaded the pinned official \`liblauncher.so\` and supporting candidate files, verified their SHA-1 values, and ran \`tools/embedded_resources.py\`.

## Evidence from the actual 2026 native library

| Finding | Count |
| --- | ---: |
| Distinct \`launcher/static/js/*.js\` paths | **240** |
| Distinct \`launcher/static/css/*.css\` paths | **6** |
| Internal launcher URLs | **3** |
| \`PK\x03\x04\` local ZIP header signatures | **435** |
| Structurally plausible ZIP local-file headers | **433** |

Important: **these are embedded path references and structurally plausible ZIP headers, not already recovered source files.** Their co-occurrence is a strong hypothesis that the launcher carries embedded web assets in a ZIP-style archive, but metadata alone does not establish that all entries can be independently decompressed.

Directly observed main JavaScript bundle reference:

\`\`\`text
launcher/static/js/app.17713a88.bundle.js
\`\`\`

Other observed source-path references:

\`\`\`text
launcher/static/js/error.82e7e351.bundle.js
launcher/static/js/log.44cc57c0.bundle.js
launcher/static/js/1301.10be1e32.bundle.js
launcher/static/js/1311.e643be28.bundle.js
launcher/static/js/2839.1193d460.bundle.js
launcher/static/js/8137.562456da.bundle.js
launcher/static/js/1120.db6f4edf.chunk.js
launcher/static/js/3358.7099f946.chunk.js
launcher/static/css/app.e3e412d7.css
launcher/static/css/1120.c314187b.chunk.css
launcher/static/css/1301.2e4904be.css
launcher/static/css/3358.ffc9bd21.chunk.css
launcher/static/css/7676.7b32cebb.chunk.css
launcher/static/css/8137.a6a248ad.css
\`\`\`

The 240 JavaScript path references include many hashed localized language chunks. Because the list comes from binary string inspection, these are not claims that all files were successfully decrypted or reconstructed.

## Investigate next

1. Inspect \`reports/embedded-resources.json\` from the [workflow artifact](https://github.com/lauraevan/LauncherRE/actions/runs/39159394472) for local-file header offsets, filenames, compression methods and flags.
2. Correlate legitimate local-file header filenames with frontend bundle paths. Check if compressed content can be decoded individually, without executing the binary.
3. Hash any decoded content and record structure and interfaces. Do not commit proprietary source bundles unless redistribution rights are established.
4. Reimplement observed launcher behavior in independent browser-compatible code.

This probe is a substantial improvement over the 2021 HTML/CSS launcher clones: it provides **current Mojang launcher frontend filenames from Mojang-distributed bytes**, not a visual guess.
