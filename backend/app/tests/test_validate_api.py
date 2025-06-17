import gzip
import io
from typing import Any, Dict, List
from fastapi.testclient import TestClient
from backend.app.main import app  # ✅ Confirm app entry is correct

client = TestClient(app)


def test_validate_csv_gz_with_errors():
    csv_data = "member_id,name,gender\n,John,M\n123,,X"
    gzipped = io.BytesIO()
    with gzip.GzipFile(fileobj=gzipped, mode="wb") as f:
        f.write(csv_data.encode("utf-8"))
    gzipped.seek(0)

    files = {
        "file": ("test.csv.gz", gzipped.read(), "application/gzip")
    }

    response = client.post("/validate/", files=files, params={"show_errors": "true"})
    assert response.status_code == 200

    data: Dict[str, Any] = response.json()
    assert isinstance(data.get("summary"), dict)
    assert data["summary"].get("rows_with_errors", 0) >= 1

    errors_by_row: Dict[str, List[str]] = data.get("errors_by_row", {})
    assert isinstance(errors_by_row, dict)
    assert any(
        isinstance(e, str) and ("TRC" in e or ":" in e)
        for errs in errors_by_row.values()  # type: ignore
        for e in errs  # type: ignore
    )


def test_validate_pretty_error_format():
    csv_data = "member_id,name,gender\n,Jane,F"
    files = {
        "file": ("test.csv", csv_data, "text/csv")
    }

    response = client.post("/validate/", files=files, params={"show_errors": "true"})
    assert response.status_code == 200

    data: Dict[str, Any] = response.json()
    errors_by_row: Dict[str, List[str]] = data.get("errors_by_row", {})
    assert isinstance(errors_by_row, dict)

    for row_errors in errors_by_row.values():
        for e in row_errors:
            assert isinstance(e, str)
            assert ":" in e  # format like TRC004: message


def test_validate_with_debug_and_benchmark():
    csv_data = "member_id,name,gender\n123,Jane,F\n,John,M"
    files = {
        "file": ("test.csv", csv_data, "text/csv")
    }

    response = client.post("/validate/", files=files, params={"debug": "true"})
    assert response.status_code == 200

    data: Dict[str, Any] = response.json()
    results: List[Dict[str, Any]] = data.get("results", [])
    assert isinstance(results, list)

    for row in results:
        assert "debug_time_ms" in row
        assert isinstance(row["debug_time_ms"], float)

    benchmark: Dict[str, Any] = data.get("benchmark", {})
    assert isinstance(benchmark, dict)
    for key in ["total_validation_time_ms", "mean_row_time_ms", "p95_row_time_ms"]:
        assert key in benchmark
        assert isinstance(benchmark[key], float)
        assert benchmark[key] > 0
