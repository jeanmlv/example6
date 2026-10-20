"""QUASAR disk-backed ARD merger. Python 3.10+, openpyxl; no pandas required.

Preserves all distinct cell values joined by ' | ', using input file order.
Output: merged CSV, optional XLSX, and QA reports. Uses SQLite on disk.
"""
from __future__ import annotations

import csv
import hashlib
import os
import shutil
import sqlite3
import time
from datetime import date, datetime
from pathlib import Path
from openpyxl import Workbook, load_workbook

# -------------------- CONFIGURATION --------------------
INPUT_FOLDER = Path(r"C:\Users\JMende95\OneDrive - JNJ\Desktop\ard_data")
OUTPUT_FOLDER = INPUT_FOLDER / "merged_v4"
FILES_TO_MERGE = [
    "CNTO1959UCO3001_quasar_ind1_wk32_ard_20260619.xlsx",
    "CNTO1959UCO3001_quasar_ind2_wk32_ard_20260621.xlsx",
    "CNTO1959UCO3001_quasar_maint_wk44_ard_20260616.xlsx",
    "CNTO1959UCO3001_quasar_lte_wk92_ard_20261012.xlsx",
    "CNTO1959UCO3001_quasar_lte_wk140_ard_20261013.xlsx",
    "CNTO1959UCO3001_quasar_lte_wk188_ard_20261013.xlsx",
]
KEYS = ("USUBJID", "AVISIT", "AVISITN", "AVISIT_ORDER")
SEPARATOR = " | "
BATCH_ROWS = 100
GENERATE_XLSX = True
KEEP_SQLITE = False
MIN_FREE_GB = 8
# -------------------------------------------------------


def normalized(value):
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float):
        if value != value:
            return ""
        return str(int(value)) if value.is_integer() else str(value)
    return str(value).strip()


def distinct_merge(old, new):
    """V3-style first-seen unique values; preserves original concatenations."""
    if not old:
        return new, False
    if not new or old == new:
        return old, False
    parts = [p.strip() for p in old.split(SEPARATOR) if p.strip()]
    changed = False
    for p in new.split(SEPARATOR):
        p = p.strip()
        if p and p not in parts:
            parts.append(p)
            changed = True
    return SEPARATOR.join(parts), changed


def row_id(keys, filename, row_number):
    complete = all(keys)
    payload = ["COMPLETE", *keys] if complete else ["INCOMPLETE", filename, str(row_number)]
    return hashlib.sha256("\x1f".join(payload).encode("utf-8")).hexdigest(), complete


def setup_db(db):
    db.execute("PRAGMA journal_mode=DELETE")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute("PRAGMA cache_size=-65536")  # 64 MiB cache
    db.execute("PRAGMA temp_store=FILE")
    db.execute("CREATE TABLE keys (id TEXT PRIMARY KEY, subj TEXT, visit TEXT, visitn TEXT, visit_order TEXT, first_seq INTEGER)")
    db.execute("CREATE TABLE cells (id TEXT, col TEXT, val TEXT, PRIMARY KEY(id,col)) WITHOUT ROWID")
    db.execute("CREATE TABLE source_visits (col TEXT, visit TEXT, PRIMARY KEY(col,visit)) WITHOUT ROWID")
    db.execute("CREATE TABLE seen (file_no INTEGER, id TEXT, PRIMARY KEY(file_no,id)) WITHOUT ROWID")
    db.execute("CREATE TABLE conflicts (file TEXT, subj TEXT, visit TEXT, visitn TEXT, visit_order TEXT, col TEXT, previous TEXT, incoming TEXT, merged TEXT)")
    db.execute("CREATE TABLE duplicate_keys (file TEXT, subj TEXT, visit TEXT, visitn TEXT, visit_order TEXT, row_number INTEGER)")
    db.commit()


def iter_sheet(path, name):
    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        if name not in wb.sheetnames:
            raise ValueError(f"{path.name}: missing worksheet {name}")
        ws = wb[name]
        it = ws.iter_rows(values_only=True)
        try:
            headers = [normalized(v) for v in next(it)]
        except StopIteration:
            raise ValueError(f"{path.name}: empty worksheet {name}")
        if len(set(headers)) != len(headers) or not all(headers):
            raise ValueError(f"{path.name}: duplicate/blank column headers")
        yield headers, it
    finally:
        wb.close()


def import_ard(db, path, file_no, all_columns, seq_start):
    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        if "ARD" not in wb.sheetnames:
            raise ValueError(f"{path.name}: sheet 'ARD' not found")
        iterator = wb["ARD"].iter_rows(values_only=True)
        headers = [normalized(v) for v in next(iterator)]
        if len(set(headers)) != len(headers) or not all(headers):
            raise ValueError(f"{path.name}: duplicate/blank headers")
        if not set(KEYS).issubset(headers):
            raise ValueError(f"{path.name}: missing keys: {set(KEYS) - set(headers)}")
        for col in headers:
            if col not in all_columns:
                all_columns.append(col)
        key_indices = [headers.index(k) for k in KEYS]
        value_indices = [(i, c) for i, c in enumerate(headers) if c not in KEYS]
        count = dup_count = incomplete_count = conflicts_count = 0
        for row_number, row in enumerate(iterator, start=2):
            if not row or all(v is None or v == "" for v in row):
                continue
            keyvals = [normalized(row[i]) if i < len(row) else "" for i in key_indices]
            rid, complete = row_id(keyvals, path.name, row_number)
            if not complete:
                incomplete_count += 1
            seq_start += 1
            db.execute("INSERT OR IGNORE INTO keys VALUES (?,?,?,?,?,?)", (rid, *keyvals, seq_start))
            if complete:
                found = db.execute("SELECT 1 FROM seen WHERE file_no=? AND id=?", (file_no, rid)).fetchone()
                if found:
                    dup_count += 1
                    db.execute("INSERT INTO duplicate_keys VALUES (?,?,?,?,?,?)", (path.name, *keyvals, row_number))
                else:
                    db.execute("INSERT INTO seen VALUES (?,?)", (file_no, rid))
            populated = []
            for idx, col in value_indices:
                val = normalized(row[idx]) if idx < len(row) else ""
                if val:
                    populated.append((col, val))
                    if keyvals[1]:
                        db.execute("INSERT OR IGNORE INTO source_visits VALUES (?,?)", (col, keyvals[1]))
            if populated:
                existing = dict(db.execute(
                    "SELECT col,val FROM cells WHERE id=?", (rid,)).fetchall())
                inserts = []
                updates = []
                for col, val in populated:
                    old = existing.get(col)
                    if old is None:
                        inserts.append((rid, col, val))
                    else:
                        merged, changed = distinct_merge(old, val)
                        if changed:
                            updates.append((merged, rid, col))
                            db.execute("INSERT INTO conflicts VALUES (?,?,?,?,?,?,?,?,?)",
                                       (path.name, *keyvals, col, old, val, merged))
                            conflicts_count += 1
                if inserts:
                    db.executemany("INSERT INTO cells VALUES (?,?,?)", inserts)
                if updates:
                    db.executemany("UPDATE cells SET val=? WHERE id=? AND col=?", updates)
            count += 1
            if count % BATCH_ROWS == 0:
                db.commit()
            if count % 1000 == 0:
                print(f"    {count:,} rows; conflicts: {conflicts_count:,}", flush=True)
        db.commit()
        print(f"  Finished: {count:,} rows; duplicates: {dup_count:,}; incomplete keys: {incomplete_count:,}; conflicts: {conflicts_count:,}", flush=True)
        return seq_start, (path.name, count, len(headers), dup_count, incomplete_count, conflicts_count)
    finally:
        wb.close()


def export_merged(db, columns, folder):
    if len(columns) > 16384:
        raise RuntimeError(f"{len(columns):,} columns exceeds Excel limit of 16,384")
    csv_path = folder / "QUASAR_MERGED_ARD.csv"
    xlsx_path = folder / "QUASAR_MERGED_ARD.xlsx"
    book = Workbook(write_only=True) if GENERATE_XLSX else None
    sheet = book.create_sheet("ARD") if book else None
    if sheet:
        sheet.append(columns)
    col_index = {name: idx for idx, name in enumerate(columns)}
    nrows = 0
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        # Sort by first appearance to avoid expensive global sort.
        keys_cursor = db.execute("SELECT id,subj,visit,visitn,visit_order FROM keys ORDER BY first_seq")
        # SQLite cannot run another query on the same cursor; use separate cursor.
        cells_cursor = db.cursor()
        for rid, subj, visit, visitn, visit_order in keys_cursor:
            output = [""] * len(columns)
            for k, v in zip(KEYS, (subj, visit, visitn, visit_order)):
                output[col_index[k]] = v
            for col, val in cells_cursor.execute("SELECT col,val FROM cells WHERE id=?", (rid,)):
                output[col_index[col]] = val
            writer.writerow(output)
            if sheet:
                if nrows >= 1048575:
                    raise RuntimeError("Excel row limit exceeded; CSV remains available")
                sheet.append(output)
            nrows += 1
            if nrows % 1000 == 0:
                print(f"  Exported {nrows:,} rows", flush=True)
    if book:
        print("Saving XLSX (may take a while)...", flush=True)
        book.save(xlsx_path)
    return nrows, csv_path, xlsx_path if book else None


def export_reports(db, stats, folder):
    book = Workbook(write_only=True)
    sheet = book.create_sheet("FILE_COMPARISON")
    sheet.append(["FILE", "INPUT_ROWS", "COLUMNS", "DUPLICATE_KEY_ROWS", "INCOMPLETE_KEY_ROWS", "CONFLICT_EVENTS"])
    for row in stats:
        sheet.append(row)
    for table, sheet_name, headers in [
        ("conflicts", "VALUE_CONFLICTS", ["INCOMING_FILE", *KEYS, "COLUMN", "PREVIOUS_VALUE", "INCOMING_VALUE", "MERGED_VALUE"]),
        ("duplicate_keys", "DUPLICATE_KEYS", ["FILE", *KEYS, "ROW_NUMBER"]),
    ]:
        count = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        if count > 1048575:
            path = folder / f"{sheet_name}.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(headers)
                for record in db.execute(f"SELECT * FROM {table}"):
                    w.writerow(record)
            continue
        ws = book.create_sheet(sheet_name)
        ws.append(headers)
        for record in db.execute(f"SELECT * FROM {table}"):
            ws.append(record)
    qc = book.create_sheet("COLUMN_VISIT_QC")
    qc.append(["COLUMN", "AVISIT", "QC_STATUS"])
    unexpected = 0
    sql = """SELECT DISTINCT c.col,k.visit FROM cells c JOIN keys k ON k.id=c.id
             LEFT JOIN source_visits s ON s.col=c.col AND s.visit=k.visit
             WHERE k.visit<>'' AND s.col IS NULL"""
    for col, visit in db.execute(sql):
        qc.append([col, visit, "FAIL"])
        unexpected += 1
    if not unexpected:
        qc.append(["ALL", "", "PASS"])
    meta = book.create_sheet("SOURCE_FILES")
    meta.append(["LOAD_ORDER", "FILE"])
    for i, stat in enumerate(stats, start=1):
        meta.append([i, stat[0]])
    summary = book.create_sheet("SUMMARY")
    summary.append(["METRIC", "VALUE"])
    for label, query in [
        ("Output rows", "SELECT COUNT(*) FROM keys"),
        ("Populated cells", "SELECT COUNT(*) FROM cells"),
        ("Conflict events", "SELECT COUNT(*) FROM conflicts"),
        ("Duplicate key rows", "SELECT COUNT(*) FROM duplicate_keys"),
    ]:
        summary.append([label, db.execute(query).fetchone()[0]])
    summary.append(["Unexpected variable/visit combinations", unexpected])
    book.save(folder / "QUASAR_MERGE_QC.xlsx")
    if unexpected:
        raise RuntimeError(f"Visit QC found {unexpected} unexpected column/visit pairs; review QUASAR_MERGE_QC.xlsx")


def main():
    paths = [INPUT_FOLDER / name for name in FILES_TO_MERGE]
    missing = [str(p) for p in paths if not p.is_file()]
    if missing:
        raise FileNotFoundError("Missing input files:\n" + "\n".join(missing))
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    free_gb = shutil.disk_usage(OUTPUT_FOLDER).free / 1024 ** 3
    print(f"Free disk: {free_gb:.1f} GiB", flush=True)
    if free_gb < MIN_FREE_GB:
        raise RuntimeError("Insufficient free disk space; choose another output folder")
    db_path = OUTPUT_FOLDER / "quasar_working.sqlite"
    if db_path.exists():
        raise FileExistsError(f"Existing database found: {db_path}. Move/delete only if no longer needed.")
    started = time.time()
    db = sqlite3.connect(str(db_path))
    success = False
    try:
        setup_db(db)
        columns = list(KEYS)
        seq = 0
        stats = []
        for i, path in enumerate(paths, 1):
            print(f"[{i}/{len(paths)}] Processing {path.name}", flush=True)
            seq, stat = import_ard(db, path, i, columns, seq)
            stats.append(stat)
        print("Exporting merged dataset...", flush=True)
        nrows, csv_path, xlsx_path = export_merged(db, columns, OUTPUT_FOLDER)
        print("Exporting QC reports...", flush=True)
        export_reports(db, stats, OUTPUT_FOLDER)
        print(f"SUCCESS: {nrows:,} rows, {len(columns):,} columns", flush=True)
        print(f"CSV: {csv_path}", flush=True)
        if xlsx_path:
            print(f"XLSX: {xlsx_path}", flush=True)
        print(f"QC: {OUTPUT_FOLDER / 'QUASAR_MERGE_QC.xlsx'}", flush=True)
        print(f"Elapsed: {(time.time()-started)/60:.1f} minutes", flush=True)
        success = True
    finally:
        db.close()
        if success and not KEEP_SQLITE:
            db_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
