# CLI and PowerShell Command Reference

This document records the PowerShell and command-line commands used for the Data Readiness Auditor project.

## Open the Project Folder

```powershell
cd C:\Users\atooo\Documents\data-readiness-auditor
```

## Activate the Virtual Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

## Install Application Dependencies

```powershell
python -m pip install -r requirements.txt
```

## Install Development and Testing Dependencies

```powershell
python -m pip install -r requirements-dev.txt
```

## Audit the Sample Dataset

```powershell
python auditor.py data/sample_data.csv
```

## Audit Another Dataset

```powershell
python auditor.py path\to\dataset.csv
```

## Specify Identifier Columns

```powershell
python auditor.py data/sample_data.csv --id-columns customer_id
```

## View Command Help

```powershell
python auditor.py --help
```

## Run All Tests

```powershell
python -m pytest -v
```

## Check Git Status

```powershell
git status
```

## Save and Push Changes

```powershell
git add .
git commit -m "Document CLI and PowerShell commands"
git push
```

## Important Note

The Data Readiness Auditor reports data-quality and readiness issues. It does not clean, overwrite, or modify the original CSV file. 
