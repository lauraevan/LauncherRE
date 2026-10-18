# Evidence and findings

Last documented: 2026-10-18.

## 1. Identified official distribution

Pinned official Mojang manifest:
https://redstone-launcher.mojang.com/release/v2/packages/5d80e3741c770efb29509f2dabf74673449d4365/manifest.json

The observed manifest has **104 paths** (including directory entries). It references the Linux launcher **3.41.29**, reported as an October 12, 2026 build. The pinned manifest is a research snapshot, not a universal "latest" endpoint.

Downloadable items include:

| Original path | SHA-1 | Size |
| --- | --- | ---: |
| \`liblauncher.so\` | \`82057cde263854ee0cbc18da896dadf5e6a46a40\` | 32,029,200 |
| \`libcef.so\` | \`6fc6e59c8f67e52ab49aa6979e75376f8ccae1b1\` | 218,760,864 |
| \`resources.pak\` | \`4dfe88c0a36a205b48105eee834fa933b5bebe07\` | 8,816,122 |
| \`lib/libmat.a\` | \`7b9299d2f8737fcdcfdb2b1719c7bf9ace2c7153\` | 5,282,704 |
| \`v8_context_snapshot.bin\` | \`6e235702cdf292ab3820d22e21a24a277f329c86\` | 671,997 |

These sizes and hashes come from the distribution manifest; they are **not** proof of downloaded, inspected, or decompiled contents.

The pinned manifest also includes **24 \`media/*.zip\` archives totaling 143,633,626 bytes**. All 24 name/hash/size/object URL records are in \`data/media-2026-10-12.json\`. Notable groups: \`background\`, \`common\`, \`animation\`, \`icons\`, \`images\`, \`fonts\`, \`logos\`, \`profile\`, \`onevanilla\`, \`textures\`, \`realms\`, \`dungeons2carousel\`.

## 2. Web interface / native boundary

Mojang has a public [fork of CEF](https://github.com/Mojang/cef) with launcher-specific changes. **That fork is the browser embedding framework and does not publish the modern launcher application source.**

A historical launcher CEF log at https://github.com/imvickykumar999/TLauncher-Minecraft/blob/main/launcher_cef_log.txt includes such console-origin references as:

\`\`\`text
https://mojang/launcher/index.html
https://mojang/launcher/static/js/app.69876942.bundle.js
\`\`\`

These are clues for the **internal frontend resource namespace**. They are from a historical launcher log, so **the hashed bundle filename and implementation must not be assumed current in 2026**. Find the 2026 equivalent from local binaries and resource-loading behavior.

\`resources.pak\` is a Chromium resource container; its presence by itself does **not** show where launcher-specific React code lives. Likewise, \`media/*.zip\` filenames show assets exist but say nothing definitive about where the frontend JS is bundled.

## 3. Independent archive research

https://blog.mr.cringe-studios.com/01-minecraft-launcher

Research published in 2024 details ZIP archive inspection in the launcher, including conditional breakpoints and encrypted media archives. Its observations are a useful lead but must be revalidated against the pinned 2026 build. This repository does not presume any encryption password or upload decrypted third-party assets.

## 4. Status / missing evidence

- [x] Locate official versioned distribution metadata
- [x] Preserve 24 media archive filenames, SHA-1, sizes and URLs
- [x] Identify native/Chromium candidate files for further static analysis
- [x] Document historical internal frontend URL conventions
- [x] Publish reproducible read-only investigation tools
- [ ] Download and hash-verify official candidate binaries in a research environment with outbound HTTP access
- [ ] Enumerate ZIP contents and encryption flags from real archive bytes
- [ ] Locate current JavaScript bundles / resource-loading paths, if accessible
- [ ] Map page-to-native bridge calls
- [ ] Build independently maintained browser UI implementing observed behavior

No obtained Mojang binary, extracted asset, or original bundle has been committed. Do not interpret the metadata inventory as recovered source code.

## Trust model

Manifest object hashes make distribution downloads reproducible, but SHA-1 should be used **only for checking against Mojang's stated distribution hash**, not as a general proof of authenticity for arbitrary files. Treat downloaded archives, URL strings, native binaries, and HTML as untrusted input. Never execute downloaded native components on a main development machine merely to inspect them. Use an isolated VM for dynamic analysis.
