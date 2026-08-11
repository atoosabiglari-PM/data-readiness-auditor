import argparse
import json
from pathlib import Path
import pandas as pd
import re

def has_id_token(column_name: str) -> bool:
    separated_name = re.sub(
        r"([A-Z]+)([A-Z][a-z])",
        r"\1 \2",
        column_name,
    )

    separated_name = re.sub(
        r"([a-z0-9])([A-Z])",
        r"\1 \2",
        separated_name,
    )

    tokens = re.split(
        r"[^A-Za-z0-9]+",
        separated_name.lower(),
    )

    return "id" in tokens
def main() -> None:
    parser = argparse.ArgumentParser(
    description="Audit a CSV dataset for data-readiness issues."
)

    parser.add_argument(
        "csv_file",
        type=Path,
        help="Path to the CSV file to audit.",
    )

    parser.add_argument(
        "--id-columns",
        nargs="+",
        default=[],
        metavar="COLUMN",
        help="One or more columns to treat as identifiers.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        metavar="PATH",
        help="Optional path for saving the audit as a JSON report.",
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

    if dataset.shape[0] == 0:
        parser.error(
            f"CSV file contains headers but no data rows: {data_file}"
        )

    column_name_lookup = {
        column.casefold(): column
        for column in dataset.columns
    }

    unknown_identifier_columns = [
        requested_column
        for requested_column in args.id_columns
        if requested_column.casefold() not in column_name_lookup
    ]

    if unknown_identifier_columns:
        parser.error(
            "Identifier column(s) not found: "
            + ", ".join(unknown_identifier_columns)
        )

    user_identifier_columns = [
        column_name_lookup[requested_column.casefold()]
        for requested_column in args.id_columns
    ]

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

    unique_counts = dataset.nunique(dropna=False)

    print("\nUnique values by column:")
    print(unique_counts)

    unique_percentages = (
        unique_counts
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
        if (
            has_id_token(column)
            or column in user_identifier_columns
        )
    ]


    possible_identifier_columns = [
        column
        for column in dataset.columns
        if (
            column not in identifier_columns
            and dataset[column].notna().all()
            and dataset[column].nunique() == len(dataset)
        )
    ]
    print("\nPossible identifier columns requiring review:")
    print(possible_identifier_columns)


    numeric_columns = [
        column
        for column in dataset.select_dtypes(
            include="number"
        ).columns
        if column not in identifier_columns
    ]

    print("\nNumeric summary statistics:")

    if numeric_columns:
        numeric_summary = dataset[
            numeric_columns
        ].describe()
        print(numeric_summary)
    else:
        numeric_summary = None
        print("No numeric columns available for analysis.")

    outlier_columns = []
    outlier_counts = {}

    print("\nPotential outliers by numeric column:")

    if not numeric_columns:
        print("No numeric columns available for outlier analysis.")

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
        outlier_counts[column] = int(outlier_count)

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

    report_recommendations = (
        recommendations
        if recommendations
        else ["No major readiness issues detected."]
    )

    audit_report = {
        "source_file": str(data_file),
        "dataset": {
            "rows": int(dataset.shape[0]),
            "columns": int(dataset.shape[1]),
        },
        "data_types": {
            column: str(dataset.dtypes[column])
            for column in dataset.columns
        },
        "unique_values": {
            column: {
                "count": int(unique_counts[column]),
                "percentage": float(
                    unique_percentages[column]
                ),
            }
            for column in dataset.columns
        },
        "numeric_summary": (
            {
                column: {
                    statistic: float(value)
                    for statistic, value
                    in numeric_summary[column].items()
                }
                for column in numeric_summary.columns
            }
            if numeric_summary is not None
            else None
        ),
        "missing_values": {
            column: {
                "count": int(missing_counts[column]),
                "percentage": float(missing_percentages[column]),
            }
            for column in dataset.columns
        },
        "duplicate_rows": int(dataset.duplicated().sum()),
        "constant_columns": constant_columns,
        "high_cardinality_text_columns": high_cardinality_columns,
        "identifier_columns": identifier_columns,
        "possible_identifier_columns": possible_identifier_columns,
        "potential_outliers": outlier_counts,
        "recommendations": report_recommendations,
    }
    if args.output_json is not None:
        output_path = args.output_json

        try:
            output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with output_path.open(
                "w",
                encoding="utf-8",
            ) as output_file:
                json.dump(
                    audit_report,
                    output_file,
                    indent=2,
                )

        except OSError as error:
            parser.error(
                f"JSON report could not be written: {error}"
            )

        print(f"\nJSON report saved to: {output_path}")
if __name__ == "__main__":
    main()