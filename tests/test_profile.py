from html.parser import HTMLParser
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlparse
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


class AttributeParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        for name in ("href", "src"):
            if name in values:
                self.references.append(values[name])


def markdown_references(text):
    return re.findall(r"!?\[[^]]*\]\(([^)]+)\)", text)


class ProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = README.read_text(encoding="utf-8")
        parser = AttributeParser()
        parser.feed(cls.text)
        cls.references = parser.references + markdown_references(cls.text)

    def test_all_local_references_exist(self):
        local = []
        for reference in self.references:
            scheme = urlparse(reference).scheme
            if not scheme and not reference.startswith("#"):
                local.append(ROOT / unquote(reference))
        self.assertTrue(local)
        self.assertEqual([path for path in local if not path.is_file()], [])

    def test_external_links_are_secure_or_email(self):
        external = [urlparse(reference) for reference in self.references if ":" in reference]
        self.assertTrue(external)
        self.assertEqual(
            [value.geturl() for value in external if value.scheme not in {"https", "mailto"}],
            [],
        )

    def test_featured_projects_link_to_github(self):
        expected = {
            "Biomechanics-Processing-Toolkit-COP-FP",
            "predicting-cybersickness-from-postural-data-with-machine-learning",
            "machine-learning-nltk-pipeline",
            "fivb-analysis-POWER-BI",
        }
        for repository in expected:
            self.assertIn(f"https://github.com/daniloarruda13/{repository}", self.text)

    def test_research_uses_stable_records(self):
        self.assertNotIn("under review", self.text.casefold())
        self.assertGreaterEqual(self.text.count("https://doi.org/"), 3)
        self.assertIn("conservancy.umn.edu", self.text)

    def test_text_has_no_encoding_artifacts(self):
        self.assertNotIn("\ufffd", self.text)
        self.assertNotIn("â€", self.text)
        self.assertNotIn("ðŸ", self.text)

    def test_svg_is_valid_and_motion_aware(self):
        root = ET.parse(ROOT / "animated_name.svg").getroot()
        self.assertTrue(root.tag.endswith("svg"))
        svg_text = (ROOT / "animated_name.svg").read_text(encoding="utf-8")
        self.assertIn("prefers-reduced-motion", svg_text)
        self.assertIn("<title", svg_text)
        self.assertIn("<desc", svg_text)

    def test_media_signatures(self):
        expected = {
            "Playing Volleyball in VR.gif": b"GIF",
            "Fifa_dashboard.gif": b"GIF",
        }
        for filename, signature in expected.items():
            with (ROOT / filename).open("rb") as media:
                self.assertEqual(media.read(3), signature)


if __name__ == "__main__":
    unittest.main()
