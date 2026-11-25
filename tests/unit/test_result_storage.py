import json

import pytest

from ai_agent_bench.results.storage import ResultStorage


def test_save_run_creates_json_record(tmp_path):
    storage = ResultStorage(tmp_path / "runs")

    result = {
        "task_id": "PB-SWE-001",
        "completed": True,
        "steps_used": 5,
    }

    output_path = storage.save_run("run-001", result)

    assert output_path.exists()

    saved_record = json.loads(output_path.read_text(encoding="utf-8"))

    assert saved_record["run_id"] == "run-001"
    assert saved_record["task_id"] == "PB-SWE-001"
    assert saved_record["completed"] is True
    assert saved_record["steps_used"] == 5
    assert "recorded_at" in saved_record


def test_save_run_rejects_duplicate_run_id(tmp_path):
    storage = ResultStorage(tmp_path / "runs")

    storage.save_run("run-001", {"task_id": "PB-SWE-001"})

    with pytest.raises(FileExistsError):
        storage.save_run("run-001", {"task_id": "PB-SWE-001"})


@pytest.mark.parametrize(
    "run_id",
    ["", "../outside", "run/001", "run 001", ".."],
)
def test_save_run_rejects_invalid_run_id(tmp_path, run_id):
    storage = ResultStorage(tmp_path / "runs")

    with pytest.raises(ValueError):
        storage.save_run(run_id, {"task_id": "PB-SWE-001"})


def test_save_run_protects_reserved_metadata(tmp_path):
    storage = ResultStorage(tmp_path / "runs")

    output_path = storage.save_run(
        "run-001",
        {
            "run_id": "fake-id",
            "recorded_at": "fake-timestamp",
            "task_id": "PB-SWE-001",
        },
    )

    saved_record = json.loads(output_path.read_text(encoding="utf-8"))

    assert saved_record["run_id"] == "run-001"
    assert saved_record["recorded_at"] != "fake-timestamp"
