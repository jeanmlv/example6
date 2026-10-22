# example6

from pathlib import Path
import os

# CONFIGURATION

# Locate corporate OneDrive automatically
ONEDRIVE = os.environ.get("OneDriveCommercial")

if not ONEDRIVE:
    raise RuntimeError("Corporate OneDrive not found.")

# Folder containing ARD CSV files
CSV_DIR = (
    Path(ONEDRIVE)
    / "Desktop"
    / "ard_data"
    / "csv"
)

# Selected ARD file
SOURCE = (
    CSV_DIR
    / "77242113UC02001_anthem_wk78_ard_merged_20260818.csv"
)

# Output directory
OUTPUT_DIR = CSV_DIR / "compressed"

# Maximum size per compressed part
CHUNK_SIZE = 20 * 1024 * 1024

# Validate file
if not SOURCE.exists():
    raise FileNotFoundError(f"ARD file not found: {SOURCE}")

print(f"ARD file: {SOURCE}")
print(f"File size: {SOURCE.stat().st_size / 1024**2:.2f} MB")

