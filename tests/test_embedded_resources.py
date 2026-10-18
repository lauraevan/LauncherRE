"""Offline tests for scanning bundled ZIP/resource paths in native launchers."""
import io
import unittest
import zipfile

from tools import embedded_resources as er


class EmbeddedResourcesTests(unittest.TestCase):
    def test_extract_path_references_from_bytes(self):
        sample = (
            b"xxlauncher/static/js/app.17713a88.bundle.js\x00"
            b"launcher/static/css/app.e3e412d7.css\x00"
            b"https://mojang/launcher/index.html\x00"
        )
        self.assertEqual(
            er.decode_matches(sample, er.JS),
            ["launcher/static/js/app.17713a88.bundle.js"],
        )
        self.assertEqual(
            er.decode_matches(sample, er.CSS),
            ["launcher/static/css/app.e3e412d7.css"],
        )

    def test_detect_zip_local_file_header_inside_binary(self):
        bio = io.BytesIO()
        with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("launcher/index.html", "<html></html>")
        prefix = b"\x7fELF" + (b"\x00" * 120)
        signatures, headers = er.local_headers(prefix + bio.getvalue())
        self.assertGreaterEqual(signatures, 1)
        self.assertEqual(len(headers), 1)
        self.assertEqual(headers[0]["filename"], "launcher/index.html")
        self.assertEqual(headers[0]["offset"], len(prefix))
        self.assertFalse(headers[0]["encrypted"])

    def test_random_pk_does_not_count_as_valid_zip(self):
        signatures, headers = er.local_headers(b"PK\x03\x04" + b"\xff" * 40)
        self.assertEqual(signatures, 1)
        self.assertEqual(headers, [])


if __name__ == "__main__":
    unittest.main()
