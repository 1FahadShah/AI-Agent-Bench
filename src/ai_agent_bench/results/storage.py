"""Persistence utilities for benchmark execution results."""

import json
from datetime import datetime, timezone
from pathlib import Path


class ResultStorage:
    """Save benchmark run records as JSON files."""

    def __init__(self, results_directory: Path) -> None:
        self.results_directory = results_directory.resolve()
        self.results_directory.mkdir(parents=True, exist_ok=True)

    def save_run(self, run_id: str, result: dict) -> Path:
        """Persist a run record and return its file path."""

        if not run_id or not run_id.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Invalid run ID.")

        run_record = {
            **result,
            "run_id": run_id,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }

        output_path = self.results_directory / f"{run_id}.json"

        if output_path.exists():
            raise FileExistsError(f"Run record already exists: {output_path}")

        with output_path.open("w", encoding="utf-8") as file:
            json.dump(
                run_record,
                file,
                indent=2,
                ensure_ascii=False,
            )

        return output_path
