"""
Safely merge selected ARD Excel files from the same clinical study.

Main safety rule
----------------
Values are merged ONLY when the complete clinical key matches exactly:
USUBJID + AVISIT + AVISITN + AVISIT_ORDER.

Rows with incomplete keys are never matched across files.
The script also validates that the final merge did not create a populated
variable at an AVISIT where that variable was never populated in any source.

Dependencies
------------
pip install pandas openpyxl
"""

from __future__ import annotations

from numbers import Number
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


# ==========================================================
# Configuration - edit only this section
# ==========================================================

INPUT_FOLDER = Path(
    r"C:\Users\JMende95\OneDrive - JNJ\Desktop\ard_data"
)

OUTPUT_FOLDER = INPUT_FOLDER / "merged_xlsx"

FILES_TO_MERGE = [
    "CNTO1959UCO3001_quasar_ind1_wk32_ard_20260619.xlsx",
    "CNTO1959UCO3001_quasar_ind2_wk32_ard_20260621.xlsx",
    "CNTO1959UCO3001_quasar_maint_wk44_ard_20260616.xlsx",
    "CNTO1959UCO3001_quasar_lte_wk92_ard_20261012.xlsx",
    "CNTO1959UCO3001_quasar_lte_wk140_ard_20261013.xlsx",
    "CNTO1959UCO3001_quasar_lte_wk188_ard_20261013.xlsx",
]

OUTPUT_NAME = "CNTO1959UCO3001_quasar_lte_wk188_ard_merged_20261013.xlsx"

DEFAULT_KEYS = [
    "USUBJID",
    "AVISIT",
    "AVISITN",
    "AVISIT_ORDER",
]

VALUE_SEPARATOR = " | "
STRICT_VISIT_QC = True


# ==========================================================
# Internal constants
# ==========================================================

INTERNAL_ROW_KEY = "__ARD_MERGE_INTERNAL_ROW_KEY__"
INCOMING_SUFFIX = "__INCOMING__"


# ==========================================================
# Value utilities
# ==========================================================

def is_missing(value: Any) -> bool:
    """Return True for None, NaN, NaT, pd.NA, and empty strings."""
    if value is None:
        return True

    if isinstance(value, str):
        return not value.strip()

    try:
        result = pd.isna(value)
        if isinstance(result, bool):
            return result
        return bool(result)
    except (TypeError, ValueError):
        return False


def display_value(value: Any) -> str:
    """Convert a value to a stable text representation."""
    if is_missing(value):
        return ""

    if isinstance(value, pd.Timestamp):
        if value.hour == value.minute == value.second == value.microsecond == 0:
            return value.strftime("%Y-%m-%d")
        return value.strftime("%Y-%m-%d %H:%M:%S")

    return str(value).strip()


def values_equal(left: Any, right: Any) -> bool:
    """Compare values while treating numeric 1 and 1.0 as equal."""
    if is_missing(left) and is_missing(right):
        return True
    if is_missing(left) or is_missing(right):
        return False

    if (
        isinstance(left, Number)
        and not isinstance(left, bool)
        and isinstance(right, Number)
        and not isinstance(right, bool)
    ):
        return float(left) == float(right)

    return display_value(left) == display_value(right)


def split_unique_values(value: Any, separator: str = VALUE_SEPARATOR) -> list[str]:
    """Split an already combined cell and return unique alternatives."""
    if is_missing(value):
        return []

    result: list[str] = []
    for item in display_value(value).split(separator):
        item = item.strip()
        if item and item not in result:
            result.append(item)
    return result


def merge_cell_values(left: Any, right: Any, separator: str = VALUE_SEPARATOR) -> Any:
    """Keep equal values once; otherwise preserve both using the separator."""
    if is_missing(left):
        return right
    if is_missing(right):
        return left
    if values_equal(left, right):
        return left

    values: list[str] = []
    for item in split_unique_values(left, separator) + split_unique_values(right, separator):
        if item not in values:
            values.append(item)

    return separator.join(values)


def merge_series_values(series: pd.Series) -> Any:
    """Merge all values in one column from a duplicated-key group."""
    result: Any = None
    for value in series:
        result = merge_cell_values(result, value)
    return result


def missing_key_mask(df: pd.DataFrame, keys: list[str]) -> pd.Series:
    """Rows with at least one missing key component."""
    return df[keys].apply(
        lambda row: any(is_missing(value) for value in row),
        axis=1,
    )


# ==========================================================
# Input validation / within-file duplicate consolidation
# ==========================================================

def validate_required_keys(df: pd.DataFrame, keys: list[str], filename: str) -> None:
    missing = [key for key in keys if key not in df.columns]
    if missing:
        raise ValueError(f"{filename}: missing required key columns: {missing}")

    reserved = [
        column for column in df.columns
        if column == INTERNAL_ROW_KEY or column.endswith(INCOMING_SUFFIX)
    ]
    if reserved:
        raise ValueError(
            f"{filename}: reserved merge column name(s) found: {reserved}"
        )


def consolidate_duplicate_complete_keys(
    df: pd.DataFrame,
    keys: list[str],
    filename: str,
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict[str, Any]], dict[str, int]]:
    """
    Consolidate duplicate COMPLETE keys inside one source file.

    Incomplete-key rows are preserved separately and never merged with each
    other or with rows from another source file.
    """
    working = df.copy().astype(object)
    incomplete_mask = missing_key_mask(working, keys)

    complete = working.loc[~incomplete_mask].copy()
    incomplete = working.loc[incomplete_mask].copy()

    duplicate_mask = complete.duplicated(keys, keep=False)
    duplicate_rows = complete.loc[duplicate_mask].copy()
    unique_rows = complete.loc[~duplicate_mask].copy()

    duplicate_report_records: list[dict[str, Any]] = []
    conflict_records: list[dict[str, Any]] = []

    if not duplicate_rows.empty:
        grouped = duplicate_rows.groupby(keys, dropna=False, sort=False)

        for group_key, group in grouped:
            if not isinstance(group_key, tuple):
                group_key = (group_key,)

            conflict_columns: list[str] = []

            for column in group.columns:
                if column in keys:
                    continue

                alternatives: list[str] = []
                for value in group[column]:
                    if is_missing(value):
                        continue
                    for alternative in split_unique_values(value):
                        if alternative not in alternatives:
                            alternatives.append(alternative)

                if len(alternatives) > 1:
                    conflict_columns.append(column)
                    record = {key: value for key, value in zip(keys, group_key)}
                    record.update(
                        {
                            "CONFLICT_STAGE": "WITHIN_FILE_DUPLICATE",
                            "COLUMN": column,
                            "ACCUMULATED_FILES": filename,
                            "ACCUMULATED_VALUE": alternatives[0],
                            "INCOMING_FILE": filename,
                            "INCOMING_VALUE": VALUE_SEPARATOR.join(alternatives[1:]),
                            "MERGED_VALUE": VALUE_SEPARATOR.join(alternatives),
                        }
                    )
                    conflict_records.append(record)

            duplicate_report_records.append(
                {
                    "FILE": filename,
                    **{key: value for key, value in zip(keys, group_key)},
                    "ROW_COUNT": len(group),
                    "KEY_STATUS": "COMPLETE",
                    "ACTION": "CONSOLIDATED",
                    "CONFLICT_COLUMNS": VALUE_SEPARATOR.join(conflict_columns),
                }
            )

        value_columns = [column for column in working.columns if column not in keys]
        rules = {column: merge_series_values for column in value_columns}

        consolidated_duplicates = (
            duplicate_rows.groupby(keys, dropna=False, sort=False, as_index=False)
            .agg(rules)
        )

        complete = pd.concat(
            [unique_rows, consolidated_duplicates],
            ignore_index=True,
            sort=False,
        )

    # Incomplete keys are intentionally NOT consolidated.
    if incomplete.empty:
        consolidated = complete
    elif complete.empty:
        consolidated = incomplete
    else:
        consolidated = pd.concat([complete, incomplete], ignore_index=True, sort=False)

    consolidated = consolidated.reindex(columns=working.columns).astype(object)

    duplicate_report = pd.DataFrame(duplicate_report_records)

    stats = {
        "INPUT_ROWS": len(working),
        "NULL_KEY_ROWS": int(incomplete_mask.sum()),
        "DUPLICATE_COMPLETE_KEY_ROWS": int(duplicate_mask.sum()),
        "DUPLICATE_COMPLETE_KEY_GROUPS": int(
            duplicate_rows[keys].drop_duplicates().shape[0]
        ),
        "ROWS_AFTER_INTERNAL_CONSOLIDATION": len(consolidated),
    }

    return consolidated, duplicate_report, conflict_records, stats


def add_internal_discriminator(
    df: pd.DataFrame,
    keys: list[str],
    filename: str,
) -> pd.DataFrame:
    """
    Complete clinical keys use a common discriminator and may match.
    Incomplete keys receive a unique discriminator and can never match.
    """
    result = df.copy().astype(object)
    incomplete = missing_key_mask(result, keys)

    result[INTERNAL_ROW_KEY] = "COMPLETE_KEY"

    for sequence, row_index in enumerate(result.index[incomplete], start=1):
        result.at[row_index, INTERNAL_ROW_KEY] = (
            f"{filename}::INCOMPLETE::{sequence}"
        )

    return result


# ==========================================================
# Safe cross-file merge
# ==========================================================

def merge_two_ards(
    left: pd.DataFrame,
    right: pd.DataFrame,
    merge_keys: list[str],
    processed_files: list[str],
    incoming_file: str,
    conflict_records: list[dict[str, Any]],
) -> pd.DataFrame:
    """
    Outer-join two prepared ARDs on the FULL key.

    pandas validate='one_to_one' is deliberately used as a safety barrier:
    if either side is not unique on the complete merge key, execution stops.
    """
    left_columns = list(left.columns)
    right_columns = list(right.columns)

    shared_value_columns = [
        column
        for column in left_columns
        if column in right_columns and column not in merge_keys
    ]

    new_columns = [
        column
        for column in right_columns
        if column not in left_columns and column not in merge_keys
    ]

    joined = pd.merge(
        left,
        right,
        on=merge_keys,
        how="outer",
        suffixes=("", INCOMING_SUFFIX),
        validate="one_to_one",
        sort=False,
    ).astype(object)

    for column in shared_value_columns:
        incoming_column = f"{column}{INCOMING_SUFFIX}"

        if incoming_column not in joined.columns:
            continue

        left_values = joined[column]
        right_values = joined[incoming_column]

        left_present = left_values.map(lambda value: not is_missing(value))
        right_present = right_values.map(lambda value: not is_missing(value))

        fill_mask = ~left_present & right_present
        if fill_mask.any():
            # Positional assignment avoids accidental label/index realignment.
            joined.loc[fill_mask, column] = right_values.loc[fill_mask].to_numpy()

        both_mask = left_present & right_present
        for row_index in joined.index[both_mask]:
            left_value = joined.at[row_index, column]
            right_value = joined.at[row_index, incoming_column]

            if values_equal(left_value, right_value):
                continue

            combined = merge_cell_values(left_value, right_value)

            record = {
                key: joined.at[row_index, key]
                for key in DEFAULT_KEYS
            }
            record.update(
                {
                    "CONFLICT_STAGE": "BETWEEN_FILES",
                    "COLUMN": column,
                    "ACCUMULATED_FILES": VALUE_SEPARATOR.join(processed_files),
                    "ACCUMULATED_VALUE": display_value(left_value),
                    "INCOMING_FILE": incoming_file,
                    "INCOMING_VALUE": display_value(right_value),
                    "MERGED_VALUE": display_value(combined),
                }
            )
            conflict_records.append(record)
            joined.at[row_index, column] = combined

        joined = joined.drop(columns=[incoming_column])

    # Rename truly new incoming columns back to their original names if needed.
    # pd.merge leaves non-overlapping right columns unchanged, so this is mainly
    # a defensive check.
    for column in new_columns:
        incoming_column = f"{column}{INCOMING_SUFFIX}"
        if incoming_column in joined.columns and column not in joined.columns:
            joined = joined.rename(columns={incoming_column: column})

    # Restore predictable column order: original left columns, then new right ones.
    final_order = left_columns + [column for column in new_columns if column not in left_columns]
    final_order = [column for column in final_order if column in joined.columns]
    extras = [column for column in joined.columns if column not in final_order]

    return joined[final_order + extras].astype(object)


def sort_merged_ard(df: pd.DataFrame) -> pd.DataFrame:
    """Stable clinical sorting without changing clinical key values."""
    result = df.copy()
    helpers: list[str] = []

    if "USUBJID" in result.columns:
        helper = "__SORT_USUBJID__"
        result[helper] = result["USUBJID"].map(display_value)
        helpers.append(helper)

    if "AVISITN" in result.columns:
        num = "__SORT_AVISITN_NUM__"
        txt = "__SORT_AVISITN_TEXT__"
        result[num] = pd.to_numeric(result["AVISITN"], errors="coerce").fillna(float("inf"))
        result[txt] = result["AVISITN"].map(display_value)
        helpers.extend([num, txt])

    if "AVISIT_ORDER" in result.columns:
        helper = "__SORT_AVISIT_ORDER__"
        result[helper] = result["AVISIT_ORDER"].map(display_value)
        helpers.append(helper)

    if "AVISIT" in result.columns:
        helper = "__SORT_AVISIT__"
        result[helper] = result["AVISIT"].map(display_value)
        helpers.append(helper)

    if helpers:
        result = result.sort_values(helpers, kind="stable", na_position="last")
        result = result.drop(columns=helpers)

    return result.reset_index(drop=True)


def merge_ard_tables(
    ard_tables: dict[str, pd.DataFrame],
    keys: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, dict[str, int]]]:
    prepared_tables: list[tuple[str, pd.DataFrame]] = []
    duplicate_reports: list[pd.DataFrame] = []
    conflict_records: list[dict[str, Any]] = []
    file_stats: dict[str, dict[str, int]] = {}

    for filename, original in ard_tables.items():
        validate_required_keys(original, keys, filename)

        consolidated, duplicate_report, within_conflicts, stats = (
            consolidate_duplicate_complete_keys(original, keys, filename)
        )

        prepared = add_internal_discriminator(consolidated, keys, filename)
        prepared_tables.append((filename, prepared))
        file_stats[filename] = stats
        conflict_records.extend(within_conflicts)

        if not duplicate_report.empty:
            duplicate_reports.append(duplicate_report)

        print(
            f"  Prepared {filename}: {stats['INPUT_ROWS']:,} -> "
            f"{stats['ROWS_AFTER_INTERNAL_CONSOLIDATION']:,} rows"
        )

    if not prepared_tables:
        raise ValueError("No ARD tables were loaded.")

    merge_keys = [*keys, INTERNAL_ROW_KEY]

    first_filename, merged = prepared_tables[0]
    merged = merged.copy().astype(object)
    processed_files = [first_filename]

    for incoming_file, current in prepared_tables[1:]:
        print(f"  Merging: {incoming_file}")

        merged = merge_two_ards(
            merged,
            current,
            merge_keys,
            processed_files,
            incoming_file,
            conflict_records,
        )
        processed_files.append(incoming_file)

    merged = merged.drop(columns=[INTERNAL_ROW_KEY])
    merged = sort_merged_ard(merged)

    conflicts = pd.DataFrame(conflict_records)

    if duplicate_reports:
        duplicates = pd.concat(duplicate_reports, ignore_index=True, sort=False)
    else:
        duplicates = pd.DataFrame(
            columns=[
                "FILE", *keys, "ROW_COUNT", "KEY_STATUS", "ACTION", "CONFLICT_COLUMNS"
            ]
        )

    return merged, conflicts, duplicates, file_stats


# ==========================================================
# Post-merge safety QC
# ==========================================================

def build_column_visit_qc(
    ard_tables: dict[str, pd.DataFrame],
    merged_ard: pd.DataFrame,
) -> pd.DataFrame:
    """
    Verify that merge did not create a populated variable at a new AVISIT.

    Example: if ADHISTI_PARAMCD_HREMGB_AVALC is populated only at Screening,
    Week 12, and Week 28 in ALL inputs, the output is forbidden from having it
    populated at Week 16 or Week 36.
    """
    source_visits: dict[str, set[str]] = {}

    for df in ard_tables.values():
        if "AVISIT" not in df.columns:
            continue

        for column in df.columns:
            if column in DEFAULT_KEYS:
                continue

            populated = df[column].map(lambda value: not is_missing(value))
            if not populated.any():
                continue

            visits = {
                display_value(value)
                for value in df.loc[populated, "AVISIT"]
                if not is_missing(value)
            }
            source_visits.setdefault(column, set()).update(visits)

    records: list[dict[str, Any]] = []

    for column in merged_ard.columns:
        if column in DEFAULT_KEYS or column not in source_visits:
            continue

        populated = merged_ard[column].map(lambda value: not is_missing(value))
        output_visits = {
            display_value(value)
            for value in merged_ard.loc[populated, "AVISIT"]
            if not is_missing(value)
        }

        unexpected = output_visits - source_visits[column]

        records.append(
            {
                "COLUMN": column,
                "SOURCE_POPULATED_VISITS": VALUE_SEPARATOR.join(sorted(source_visits[column])),
                "OUTPUT_POPULATED_VISITS": VALUE_SEPARATOR.join(sorted(output_visits)),
                "UNEXPECTED_OUTPUT_VISITS": VALUE_SEPARATOR.join(sorted(unexpected)),
                "QC_STATUS": "FAIL" if unexpected else "PASS",
            }
        )

    return pd.DataFrame(records)


def assert_visit_qc(column_visit_qc: pd.DataFrame) -> None:
    if column_visit_qc.empty:
        return

    failed = column_visit_qc.loc[column_visit_qc["QC_STATUS"] == "FAIL"]
    if failed.empty:
        return

    examples = failed[
        ["COLUMN", "UNEXPECTED_OUTPUT_VISITS"]
    ].head(10).to_string(index=False)

    raise RuntimeError(
        "Post-merge visit QC failed. The merge produced populated variables at "
        "AVISIT values where those variables were not populated in any source.\n\n"
        f"Examples:\n{examples}\n\n"
        "No output workbook was written. Review the merge keys/source data."
    )


# ==========================================================
# Reports / dictionaries
# ==========================================================

def compare_files(
    ard_tables: dict[str, pd.DataFrame],
    file_stats: dict[str, dict[str, int]],
) -> pd.DataFrame:
    all_columns: set[str] = set()
    common_columns: set[str] | None = None

    for df in ard_tables.values():
        columns = set(df.columns)
        all_columns.update(columns)
        common_columns = columns if common_columns is None else common_columns & columns

    common_columns = common_columns or set()
    records: list[dict[str, Any]] = []

    for filename, df in ard_tables.items():
        stats = file_stats[filename]
        records.append(
            {
                "FILE": filename,
                "ROWS": len(df),
                "ROWS_AFTER_INTERNAL_CONSOLIDATION": stats["ROWS_AFTER_INTERNAL_CONSOLIDATION"],
                "COLUMNS": len(df.columns),
                "SUBJECTS": df["USUBJID"].nunique(dropna=True),
                "VISITS": df["AVISIT"].nunique(dropna=True),
                "NULL_KEY_ROWS_KEPT_SEPARATE": stats["NULL_KEY_ROWS"],
                "DUPLICATE_COMPLETE_KEY_ROWS": stats["DUPLICATE_COMPLETE_KEY_ROWS"],
                "DUPLICATE_COMPLETE_KEY_GROUPS": stats["DUPLICATE_COMPLETE_KEY_GROUPS"],
                "COLUMNS_ONLY_IN_THIS_FILE": len(set(df.columns) - common_columns),
                "MISSING_FROM_GLOBAL_COLUMN_UNION": len(all_columns - set(df.columns)),
            }
        )

    return pd.DataFrame(records)


def merge_paramcd_dict(dictionaries: Iterable[pd.DataFrame]) -> pd.DataFrame:
    available = [df.copy() for df in dictionaries if df is not None and not df.empty]
    if not available:
        return pd.DataFrame(columns=["PARAMCD", "PARAM", "SOURCE"])

    merged = pd.concat(available, ignore_index=True, sort=False)
    return merged.drop_duplicates().reset_index(drop=True)


# ==========================================================
# File I/O
# ==========================================================

def validate_configuration() -> tuple[list[Path], Path]:
    if not INPUT_FOLDER.exists():
        raise FileNotFoundError(f"Input folder not found:\n{INPUT_FOLDER}")

    if len(FILES_TO_MERGE) < 2:
        raise ValueError("FILES_TO_MERGE must contain at least two files.")

    input_files = [INPUT_FOLDER / name for name in FILES_TO_MERGE]
    missing = [file for file in input_files if not file.is_file()]

    if missing:
        text = "\n".join(f"  - {file.name}" for file in missing)
        raise FileNotFoundError(f"Configured files not found:\n{text}")

    output_file = OUTPUT_FOLDER / OUTPUT_NAME
    return input_files, output_file


def load_workbooks(
    files: list[Path],
) -> tuple[dict[str, pd.DataFrame], list[pd.DataFrame]]:
    ard_tables: dict[str, pd.DataFrame] = {}
    dictionaries: list[pd.DataFrame] = []

    print(f"Files selected: {len(files)}\n")

    for file in files:
        print(f"  Reading: {file.name}")
        with pd.ExcelFile(file, engine="openpyxl") as excel:
            if "ARD" not in excel.sheet_names:
                raise ValueError(f"{file.name}: sheet 'ARD' was not found.")

            ard_tables[file.name] = pd.read_excel(excel, sheet_name="ARD")

            if "PARAMCD_DICT" in excel.sheet_names:
                dictionaries.append(pd.read_excel(excel, sheet_name="PARAMCD_DICT"))

    return ard_tables, dictionaries


def write_output(
    output_file: Path,
    merged_ard: pd.DataFrame,
    merged_dict: pd.DataFrame,
    comparison: pd.DataFrame,
    conflicts: pd.DataFrame,
    duplicates: pd.DataFrame,
    source_files: pd.DataFrame,
    column_visit_qc: pd.DataFrame,
) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            merged_ard.to_excel(writer, sheet_name="ARD", index=False)
            merged_dict.to_excel(writer, sheet_name="PARAMCD_DICT", index=False)
            comparison.to_excel(writer, sheet_name="FILE_COMPARISON", index=False)
            conflicts.to_excel(writer, sheet_name="VALUE_CONFLICTS", index=False)
            duplicates.to_excel(writer, sheet_name="DUPLICATE_KEYS", index=False)
            column_visit_qc.to_excel(writer, sheet_name="COLUMN_VISIT_QC", index=False)
            source_files.to_excel(writer, sheet_name="SOURCE_FILES", index=False)
    except PermissionError as error:
        raise PermissionError(
            f"Could not write output:\n{output_file}\nClose it in Excel and run again."
        ) from error


# ==========================================================
# Main
# ==========================================================

def main() -> None:
    input_files, output_file = validate_configuration()
    ard_tables, dictionaries = load_workbooks(input_files)

    print("\nSafely merging ARD tables using the full clinical key...")

    merged_ard, conflicts, duplicates, file_stats = merge_ard_tables(
        ard_tables,
        DEFAULT_KEYS,
    )

    print("\nRunning post-merge visit-scope QC...")
    column_visit_qc = build_column_visit_qc(ard_tables, merged_ard)

    if STRICT_VISIT_QC:
        assert_visit_qc(column_visit_qc)

    comparison = compare_files(ard_tables, file_stats)
    merged_dict = merge_paramcd_dict(dictionaries)

    source_files = pd.DataFrame(
        {
            "LOAD_ORDER": range(1, len(input_files) + 1),
            "FILE": [file.name for file in input_files],
        }
    )

    print("Writing output workbook...")
    write_output(
        output_file,
        merged_ard,
        merged_dict,
        comparison,
        conflicts,
        duplicates,
        source_files,
        column_visit_qc,
    )

    print("\nMerge completed successfully.")
    print(f"Output: {output_file}")
    print(f"ARD rows: {len(merged_ard):,}")
    print(f"ARD columns: {len(merged_ard.columns):,}")
    print(f"Subjects: {merged_ard['USUBJID'].nunique(dropna=True):,}")
    print(f"Visits: {merged_ard['AVISIT'].nunique(dropna=True):,}")
    print(f"Conflict records: {len(conflicts):,}")
    print(f"Duplicated-key groups reported: {len(duplicates):,}")
    print("COLUMN_VISIT_QC: all checks PASS.")


if __name__ == "__main__":
    main()