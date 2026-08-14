import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUDITOR_PATH = PROJECT_ROOT / "auditor.py"


def run_auditor(
    *arguments: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(AUDITOR_PATH),
            *arguments,
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_sample_dataset_audit_succeeds() -> None:
    result = run_auditor("data/sample_data.csv")

    assert result.returncode == 0
    assert "Rows: 10" in result.stdout
    assert "Columns: 6" in result.stdout


def test_missing_csv_returns_error() -> None:
    result = run_auditor("data/not_found.csv")

    assert result.returncode != 0
    assert "CSV file not found" in result.stderr


def test_unknown_identifier_column_returns_error() -> None:
    result = run_auditor(
        "data/sample_data.csv",
        "--id-columns",
        "WrongColumn",
    )

    assert result.returncode != 0
    assert "Identifier column(s) not found: WrongColumn" in result.stderr


def test_identifier_matching_is_case_insensitive() -> None:
    result = run_auditor(
        "data/sample_data.csv",
        "--id-columns",
        "INCOME",
    )

    assert result.returncode == 0
    assert "age: 0" in result.stdout
    assert "income: 1" not in result.stdout


def test_header_only_csv_returns_error(
    tmp_path: Path,
) -> None:
    csv_file = tmp_path / "headers_only.csv"

    csv_file.write_text(
        "name,city\n",
        encoding="utf-8",
    )

    result = run_auditor(str(csv_file))

    assert result.returncode != 0
    assert "CSV file contains headers but no data rows" in result.stderr


def test_blank_csv_returns_error(
    tmp_path: Path,
) -> None:
    csv_file = tmp_path / "blank.csv"

    csv_file.write_text(
        "",
        encoding="utf-8",
    )

    result = run_auditor(str(csv_file))

    assert result.returncode != 0
    assert "CSV file is empty" in result.stderr


def test_text_only_csv_succeeds(
    tmp_path: Path,
) -> None:
    csv_file = tmp_path / "text_only.csv"
    output_file = tmp_path / "text_only.json"

    csv_file.write_text(
        "name,city\nAna,San Jose\nBen,Oakland\n",
        encoding="utf-8",
    )

    result = run_auditor(
        str(csv_file),
        "--output-json",
        str(output_file),
    )

    assert result.returncode == 0
    assert "No numeric columns available for analysis." in result.stdout
    assert "No numeric columns available for outlier analysis." in result.stdout
    assert output_file.is_file()

    report = json.loads(output_file.read_text(encoding="utf-8"))

    assert report["numeric_summary"] is None


def test_malformed_csv_returns_error(
    tmp_path: Path,
) -> None:
    csv_file = tmp_path / "malformed.csv"

    csv_file.write_text(
        'name,city\n"Ana,San Jose\nBen,Oakland\n',
        encoding="utf-8",
    )

    result = run_auditor(str(csv_file))

    assert result.returncode != 0
    assert "CSV file could not be parsed" in result.stderr


def test_automatic_identifier_is_excluded_from_numeric_analysis() -> None:
    result = run_auditor("data/sample_data.csv")

    numeric_section = result.stdout.split("Numeric summary statistics:", 1)[1].split(
        "Potential outliers by numeric column:", 1
    )[0]

    outlier_section = result.stdout.split("Potential outliers by numeric column:", 1)[
        1
    ].split("Data-readiness recommendations:", 1)[0]

    assert result.returncode == 0
    assert "customer_id" not in numeric_section
    assert "customer_id" not in outlier_section
    assert "age" in numeric_section
    assert "income" in numeric_section


def test_json_report_is_created(
    tmp_path: Path,
) -> None:
    output_file = tmp_path / "reports" / "audit.json"

    result = run_auditor(
        "data/sample_data.csv",
        "--output-json",
        str(output_file),
    )

    assert result.returncode == 0
    assert output_file.is_file()
    assert "JSON report saved to:" in result.stdout

    report = json.loads(output_file.read_text(encoding="utf-8"))

    assert report["dataset"] == {
        "rows": 10,
        "columns": 6,
    }
    assert report["data_types"] == {
        "customer_id": "int64",
        "name": "str",
        "age": "float64",
        "city": "str",
        "income": "float64",
        "country": "str",
    }
    assert report["unique_values"] == {
        "customer_id": {
            "count": 9,
            "percentage": 90.0,
        },
        "name": {
            "count": 9,
            "percentage": 90.0,
        },
        "age": {
            "count": 9,
            "percentage": 90.0,
        },
        "city": {
            "count": 5,
            "percentage": 50.0,
        },
        "income": {
            "count": 9,
            "percentage": 90.0,
        },
        "country": {
            "count": 1,
            "percentage": 10.0,
        },
    }
    assert report["numeric_summary"]["age"]["count"] == 9.0
    assert report["numeric_summary"]["age"]["50%"] == 34.0
    assert report["numeric_summary"]["income"]["max"] == 999999.0
    assert report["duplicate_rows"] == 1
    assert report["identifier_columns"] == ["customer_id"]
    assert report["potential_outliers"] == {
        "age": 0,
        "income": 1,
    }
