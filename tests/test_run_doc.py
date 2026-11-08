from pathlib import Path

RUN = (Path(__file__).resolve().parent.parent / "docs" / "RUN.md").read_text()


def test_owner_checklist_section() -> None:
    assert "## Owner checklist" in RUN
    section = RUN.split("## Owner checklist", 1)[1]
    steps = [ln for ln in section.splitlines() if ln[:2] in ("1.", "2.", "3.", "4.", "5.")]
    assert 3 <= len(steps) <= 5
    assert "never printed" in section
    assert "EXECUTIONS_DATA_SAVE_ON_SUCCESS" in section
    assert "EXECUTIONS_DATA_SAVE_ON_ERROR" in section
