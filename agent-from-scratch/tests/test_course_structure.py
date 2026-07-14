from pathlib import Path
import re
import subprocess
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
COURSES_ROOT = next(
    path
    for path in REPOSITORY_ROOT.iterdir()
    if path.is_dir() and any(child.name.endswith("-Coding-Agent") for child in path.iterdir())
)
MAIN_ROOT = next(path for path in COURSES_ROOT.iterdir() if path.name.endswith("-Coding-Agent"))
OPTIONAL_ROOT = next(
    path
    for path in COURSES_ROOT.iterdir()
    if path.is_dir() and (path / "RAG").is_dir() and (path / "Multi-Agent").is_dir()
)
ARCHIVE_ROOT = next(
    path
    for path in COURSES_ROOT.iterdir()
    if path.is_dir() and any(child.name.startswith("2026-07-") for child in path.iterdir())
)
CHECKPOINT_ROOT = REPOSITORY_ROOT / "agent-from-scratch" / "course-checkpoints"
MARKDOWN_LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")


def test_main_course_has_eight_modules_and_thirty_two_lessons() -> None:
    modules = sorted(path for path in MAIN_ROOT.iterdir() if path.is_dir())
    assert len(modules) == 8
    assert [re.search(r"(\d{2})-", path.name).group(1) for path in modules] == [
        f"{index:02d}" for index in range(1, 9)
    ]

    lessons = []
    for module_index, module in enumerate(modules, start=1):
        module_lessons = sorted(module.glob("L[0-9][0-9]-*.md"))
        assert len(module_lessons) == 4
        support_documents = [path for path in module.glob("*.md") if path not in module_lessons]
        assert len(support_documents) == 3
        lessons.extend(module_lessons)

    assert [lesson.name[:3] for lesson in lessons] == [
        f"L{index:02d}" for index in range(1, 33)
    ]


def test_every_main_lesson_uses_the_teaching_template() -> None:
    lessons = sorted(MAIN_ROOT.rglob("L[0-9][0-9]-*.md"))
    for lesson in lessons:
        content = lesson.read_text(encoding="utf-8", errors="strict")
        assert all(re.search(fr"^## {index}\.", content, re.MULTILINE) for index in range(1, 13))
        assert "60" in content and "90" in content
        assert "powershell" in content
        assert content.count("1. ") >= 1


def test_optional_modules_each_have_four_lessons_and_acceptance() -> None:
    expected = {"RAG": "R", "Multi-Agent": "A"}
    assert {path.name for path in OPTIONAL_ROOT.iterdir() if path.is_dir()} == set(expected)
    for directory, prefix in expected.items():
        root = OPTIONAL_ROOT / directory
        assert len(list(root.glob(f"{prefix}[0-9][0-9]-*.md"))) == 4
        assert len(list(root.glob("*.md"))) == (7 if directory == "RAG" else 6)


def test_all_nine_course_states_run_offline() -> None:
    checkpoints = sorted(path for path in CHECKPOINT_ROOT.iterdir() if path.is_dir())
    assert [path.name[:2] for path in checkpoints] == [f"{index:02d}" for index in range(9)]
    for checkpoint in checkpoints:
        assert (checkpoint / "README.md").is_file()
        completed = subprocess.run(
            [sys.executable, "demo.py"],
            cwd=checkpoint,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            timeout=10,
            check=False,
        )
        assert completed.returncode == 0, f"{checkpoint.name}: {completed.stderr}"
        assert completed.stdout.strip()


def test_history_mapping_covers_every_archived_course_document() -> None:
    archive_roots = [
        path
        for path in ARCHIVE_ROOT.iterdir()
        if path.name.startswith("2026-07-") and len(list(path.rglob("*.md"))) > 1
    ]
    documents = [document for root in archive_roots for document in root.rglob("*.md")]
    active_documents = [
        path
        for path in COURSES_ROOT.rglob("*.md")
        if ARCHIVE_ROOT not in path.parents
    ]
    mapping = max(
        (path.read_text(encoding="utf-8", errors="strict") for path in active_documents),
        key=lambda content: sum(document.name in content for document in documents),
    )
    covered = [document for document in documents if document.name in mapping]
    assert len(covered) == 132


def test_active_document_links_resolve() -> None:
    documents = [
        REPOSITORY_ROOT / "README.md",
        REPOSITORY_ROOT / "agent-from-scratch" / "README.md",
        COURSES_ROOT / "README.md",
    ]
    documents.extend(REPOSITORY_ROOT.glob("Agent*.md"))
    documents.extend(
        path for path in COURSES_ROOT.rglob("*.md") if ARCHIVE_ROOT not in path.parents
    )

    broken = []
    for document in documents:
        content = document.read_text(encoding="utf-8", errors="strict")
        for target in MARKDOWN_LINK.findall(content):
            if target.startswith(("http://", "https://", "#")):
                continue
            path = (document.parent / target.split("#", 1)[0]).resolve()
            if not path.exists():
                broken.append(f"{document}: {target}")
    assert broken == []
