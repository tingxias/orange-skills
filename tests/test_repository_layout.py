import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"


class RepositoryLayoutTests(unittest.TestCase):
    def test_repository_root_is_not_an_installable_skill(self):
        self.assertFalse((ROOT / "SKILL.md").exists())
        self.assertTrue((ROOT / "README.md").is_file())

    def test_each_skill_has_matching_directory_and_frontmatter_name(self):
        skill_dirs = sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir())
        self.assertEqual([path.name for path in skill_dirs], ["daily-report"])

        for skill_dir in skill_dirs:
            skill_file = skill_dir / "SKILL.md"
            self.assertTrue(skill_file.is_file(), skill_file)
            text = skill_file.read_text(encoding="utf-8")
            match = re.search(r"(?m)^name:\s*([a-z0-9-]+)\s*$", text)
            self.assertIsNotNone(match, skill_file)
            self.assertEqual(match.group(1), skill_dir.name)


if __name__ == "__main__":
    unittest.main()
