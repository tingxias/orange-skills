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
        self.assertEqual([path.name for path in skill_dirs], ["daily-report", "yonyou-skill"])

        for skill_dir in skill_dirs:
            skill_file = skill_dir / "SKILL.md"
            self.assertTrue(skill_file.is_file(), skill_file)
            text = skill_file.read_text(encoding="utf-8")
            match = re.search(r"(?m)^name:\s*([a-z0-9-]+)\s*$", text)
            self.assertIsNotNone(match, skill_file)
            self.assertEqual(match.group(1), skill_dir.name)

    def test_yonyou_skill_contains_nc65_skill_content_and_references(self):
        source = Path("/Users/a1234/.codex/skills/nc65-api-dev")
        target = SKILLS_DIR / "yonyou-skill"

        self.assertTrue((target / "SKILL.md").is_file())
        skill_text = (target / "SKILL.md").read_text(encoding="utf-8")
        self.assertRegex(skill_text, r"(?m)^name:\s*yonyou-skill\s*$")
        self.assertIn("NC65", skill_text)
        self.assertIn("AbstractApiProcessor", skill_text)
        self.assertIn("Use `codegraph_explore`", skill_text)

        for reference in [
            "data-dictionary.md",
            "mes-patterns.md",
            "nc-patterns.md",
            "projects.md",
            "sync-framework.md",
        ]:
            target_reference = target / "references" / reference
            source_reference = source / "references" / reference
            self.assertTrue(target_reference.is_file(), target_reference)
            self.assertEqual(
                target_reference.read_text(encoding="utf-8"),
                source_reference.read_text(encoding="utf-8"),
                reference,
            )


if __name__ == "__main__":
    unittest.main()
