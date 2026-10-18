"""Network-free tests of LauncherRE's manifest and archive inspection tools."""
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools import launcher_re as lr


class LauncherRETests(unittest.TestCase):
    def test_pinned_inventory_has_24_valid_archives(self):
        lock = lr.load_lock()
        self.assertEqual(len(lock["media"]), 24)
        self.assertEqual(sum(x["size"] for x in lock["media"].values()), 143633626)
        self.assertTrue(all(name.startswith("media/") for name in lock["media"]))
        self.assertEqual(
            lr.parse_entries({
                "files": {k: {"downloads": {"raw": v}} for k, v in lock["media"].items()}
            }).keys(), lock["media"].keys()
        )

    def test_full_manifest_has_expected_paths(self):
        manifest = json.loads((lr.REPO_ROOT / "data" / "mojang-manifest-2026-10-12.json").read_text())
        self.assertEqual(len(manifest["files"]), 104)
        entries = lr.parse_entries(manifest)
        self.assertIn("liblauncher.so", entries)
        self.assertIn("resources.pak", entries)
        self.assertIn("media/common.zip", entries)

    def test_reject_traversal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("../escape", "/absolute", "one/../../escape", r"..\escape", ""):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    lr.confined_path(root, name)

    def test_reject_non_mojang_hosts(self):
        bad = (
            "http://redstone-launcher.mojang.com/release/v2/objects/a/x",
            "https://redstone-launcher.mojang.com.evil.test/release/v2/objects/a/x",
            "https://evil.test/release/v2/objects/a/x",
            "https://redstone-launcher.mojang.com@evil.test/release/v2/objects/a/x",
            "https://redstone-launcher.mojang.com/release/v2/objects/a/x?redirect=1",
        )
        for url in bad:
            with self.subTest(url=url), self.assertRaises(ValueError):
                lr.validated_url(url)

    def test_report_zip_is_metadata_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "sample.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("frontend/index.html", "<h1>placeholder</h1>")
                z.writestr("../outside.txt", "unsafe")
            result = lr.report_zip(archive, root)
            self.assertTrue(result["valid_zip"])
            self.assertEqual(result["entry_count"], 2)
            self.assertEqual(result["encrypted_entries"], 0)
            self.assertEqual(result["unsafe_entries"], ["../outside.txt"])
            self.assertFalse((root.parent / "outside.txt").exists())

    def test_ascii_matches(self):
        sample = b"\0\0prefix https://mojang/launcher/static/js/app.abcdefg.bundle.js \0"
        hits = lr.ascii_matches(sample)
        self.assertEqual(len(hits), 1)
        self.assertIn("launcher/static/js", hits[0])

    def test_hash_calculation(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "test.bin"
            path.write_bytes(b"launcher-re")
            self.assertEqual(lr.sha1_of_file(path), hashlib.sha1(b"launcher-re").hexdigest())


if __name__ == "__main__":
    unittest.main()
