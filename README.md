# Data Readiness Auditor

[![Run Tests](https://github.com/atoosabiglari-PM/data-readiness-auditor/actions/workflows/tests.yml/badge.svg)](https://github.com/atoosabiglari-PM/data-readiness-auditor/actions/workflows/tests.yml)

A Python command-line application that evaluates the quality and readiness of tabular datasets before data analysis or machine-learning development.

## Purpose

Machine-learning results depend heavily on the quality of the underlying data. This project provides an automated first-pass audit of CSV datasets and highlights issues that should be reviewed before analysis or modeling.

## Current Features

- Accepts any CSV file through the command line
- Displays dataset dimensions, a data preview, and column data types
- Reports missing-value counts and percentages
- Detects duplicate rows and constant columns
- Calculates unique-value counts and percentages
- Identifies high-cardinality text columns
- Recognizes common identifier naming styles such as `customer_id`, `PassengerId`, and `TransactionID`
- Reports fully unique columns as possible identifier candidates
- Supports user-specified identifier columns with `--id-columns`
- Calculates numeric summary statistics while excluding confirmed identifiers
- Detects potential numeric outliers using the interquartile range (IQR) method
- Generates actionable data-readiness recommendations
- Handles missing, blank, malformed, header-only, and text-only CSV files

## Usage

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 3. Audit a CSV file

```powershell
python auditor.py data/sample_data.csv
```

### 4. Specify identifier columns manually

```powershell
python auditor.py path/to/dataset.csv --id-columns record_number account_code
```

Column matching for `--id-columns` is case-insensitive.

### Command help

```powershell
python auditor.py --help
```

## Automated Testing

Install the development and testing dependencies:

```powershell
python -m pip install -r requirements-dev.txt
```

Run the complete test suite:

```powershell
python -m pytest -v
```

The automated CLI tests verify:

- Successful CSV audits
- Missing and malformed file handling
- Blank and header-only dataset handling
- Text-only dataset handling
- Identifier-column validation
- Case-insensitive identifier matching
- Automatic exclusion of identifiers from numeric analysis

A GitHub Actions continuous-integration workflow automatically installs the project dependencies and runs the complete test suite on every push and pull request.

## Interpretation Notes

- Potential outliers are values flagged for review, not automatically errors.
- Fully unique columns are reported as possible identifier candidates but are not automatically removed.
- Identifier columns are excluded only from numeric summary statistics and outlier analysis; they remain visible in the rest of the audit.
- High-cardinality columns may still contain useful information and require human judgment before encoding or removal.
- The auditor performs an initial readiness assessment and does not automatically clean or modify the source dataset.

## Technologies

- Python
- pandas
- NumPy
- pytest
- GitHub Actions

## Project Status

This project is under active development as part of my 12-week applied AI and machine-learning portfolio.

## Author

**Atoosa Biglari**

Technical Program Manager | AI & Machine Learning Builder | Enterprise Infrastructure, Networking & Cloud