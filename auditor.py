import argparse
from pathlib import Path

import pandas as pd


parser = argparse.ArgumentParser(
    description="Audit a CSV dataset for data-readiness issues."
)

parser.add_argument(
    "csv_file",
    type=Path,
    help="Path to the CSV file to audit.",
)

args = parser.parse_args()
data_file = args.csv_file

if not data_file.is_file():
    parser.error(f"CSV file not found: {data_file}")

try:
    dataset = pd.read_csv(data_file)
except pd.errors.EmptyDataError:
    parser.error(f"CSV file is empty: {data_file}")
except pd.errors.ParserError:
    parser.error(f"CSV file could not be parsed: {data_file}")
except UnicodeDecodeError:
    parser.error(f"CSV file encoding could not be read: {data_file}")
except OSError as error:
    parser.error(f"CSV file could not be opened: {error}")

print("\nDataset dimensions:")
print(f"Rows: {dataset.shape[0]}")
print(f"Columns: {dataset.shape[1]}")

print("\nDataset preview:")
print(dataset.head())

print("\nColumn data types:")
print(dataset.dtypes)

missing_counts = dataset.isna().sum()

missing_percentages = (
    dataset.isna()
    .mean()
    .mul(100)
    .round(1)
)

missing_summary = pd.DataFrame(
    {
        "missing_count": missing_counts,
        "missing_percentage": missing_percentages,
    }
)

print("\nMissing-data summary:")
print(missing_summary)

print("\nDuplicate rows:")
print(dataset.duplicated().sum())

constant_columns = [
    column
    for column in dataset.columns
    if dataset[column].nunique(dropna=False) == 1
]

print("\nConstant columns:")
print(constant_columns)

print("\nUnique values by column:")
print(dataset.nunique(dropna=False))

unique_percentages = (
    dataset.nunique(dropna=False)
    .div(len(dataset))
    .mul(100)
    .round(1)
)

print("\nUnique-value percentage by column:")
print(unique_percentages)

text_columns = dataset.select_dtypes(
    include=["object", "string"]
).columns

high_cardinality_columns = [
    column
    for column in text_columns
    if unique_percentages[column] >= 80
]

print("\nHigh-cardinality text columns:")
print(high_cardinality_columns)

identifier_columns = [
    column
    for column in dataset.columns
    if column.lower() == "id"
    or column.lower().endswith("_id")
]

numeric_columns = [
    column
    for column in dataset.select_dtypes(
        include="number"
    ).columns
    if column not in identifier_columns
]

print("\nNumeric summary statistics:")
print(dataset[numeric_columns].describe())

outlier_columns = []

print("\nPotential outliers by numeric column:")

for column in numeric_columns:
    q1 = dataset[column].quantile(0.25)
    q3 = dataset[column].quantile(0.75)
    iqr = q3 - q1

    lower_bound = q1 - (1.5 * iqr)
    upper_bound = q3 + (1.5 * iqr)

    outlier_count = (
        (dataset[column] < lower_bound)
        | (dataset[column] > upper_bound)
    ).sum()

    if outlier_count > 0:
        outlier_columns.append(column)

    print(f"{column}: {outlier_count}")

print("\nData-readiness recommendations:")

recommendations = []

if missing_counts.sum() > 0:
    recommendations.append(
        "Review and handle missing values before modeling."
    )

if dataset.duplicated().sum() > 0:
    recommendations.append(
        "Review and remove or justify duplicate rows."
    )

if constant_columns:
    recommendations.append(
        "Consider removing constant columns: "
        + ", ".join(constant_columns)
        + "."
    )

if high_cardinality_columns:
    recommendations.append(
        "Review high-cardinality text columns before encoding: "
        + ", ".join(high_cardinality_columns)
        + "."
    )

if outlier_columns:
    recommendations.append(
        "Review potential outliers in numeric columns: "
        + ", ".join(outlier_columns)
        + "."
    )

if recommendations:
    for recommendation in recommendations:
        print(f"- {recommendation}")
else:
    print("- No major readiness issues detected.")
