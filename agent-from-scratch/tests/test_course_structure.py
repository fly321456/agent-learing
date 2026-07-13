from pathlib import Path
import re


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
COURSE_ROOT = (
    REPOSITORY_ROOT
    / "\u8bfe\u7a0b"
    / "\u4e3b\u7ebf-Coding-Agent"
)
COURSES_ROOT = COURSE_ROOT.parent
GOVERNANCE_ROOT = COURSES_ROOT / "\u8bfe\u7a0b\u6cbb\u7406"
ARCHIVED_COURSES = (
    COURSES_ROOT
    / "\u5f52\u6863"
    / "2026-07-\u6df1\u5ea6\u91cd\u6784\u524d"
    / "\u65e7\u8bfe\u7a0b"
)
MAPPING = GOVERNANCE_ROOT / "\u65e7\u8bfe\u8fc1\u79fb\u6620\u5c04.md"
MARKDOWN_LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")


def test_course_has_exactly_eight_complete_milestones() -> None:
    milestones = sorted(path for path in COURSE_ROOT.iterdir() if path.is_dir())

    assert [path.name[:3] for path in milestones] == [f"M{index:02d}" for index in range(1, 9)]
    for milestone in milestones:
        assert (milestone / "课程.md").is_file()
        assert (milestone / "验收与面试.md").is_file()


def test_course_documents_are_utf8_and_contain_delivery_commands() -> None:
    for document in COURSE_ROOT.rglob("*.md"):
        content = document.read_text(encoding="utf-8", errors="strict")
        assert "##" in content
        assert "pytest" in content or "coding-agent" in content


def test_every_archived_lesson_and_interview_is_in_the_migration_map() -> None:
    mapping = MAPPING.read_text(encoding="utf-8", errors="strict")

    archived_documents = list(ARCHIVED_COURSES.rglob("*.md"))
    assert len(archived_documents) == 112
    assert all(document.name in mapping for document in archived_documents)


def test_active_course_links_resolve() -> None:
    optional_root = COURSES_ROOT / "\u9009\u4fee\u4e13\u9898"
    reference_index = COURSES_ROOT / "\u53c2\u8003\u8d44\u6599" / "README.md"
    documents = [
        REPOSITORY_ROOT / "README.md",
        REPOSITORY_ROOT / "Agent\u5b66\u4e60\u7b14\u8bb0.md",
        REPOSITORY_ROOT / "Agent\u9762\u8bd5\u9898\u96c6.md",
        REPOSITORY_ROOT / "agent-from-scratch" / "README.md",
        COURSES_ROOT / "README.md",
        reference_index,
    ]
    documents.extend(COURSE_ROOT.rglob("*.md"))
    documents.extend(GOVERNANCE_ROOT.rglob("*.md"))
    documents.extend(optional_root.rglob("*.md"))

    broken: list[str] = []
    for document in documents:
        content = document.read_text(encoding="utf-8", errors="strict")
        for target in MARKDOWN_LINK.findall(content):
            if target.startswith(("http://", "https://", "#")):
                continue
            path = (document.parent / target.split("#", 1)[0]).resolve()
            if not path.exists():
                broken.append(f"{document}: {target}")

    assert broken == []
