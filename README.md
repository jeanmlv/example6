# example6

from pathlib import Path

# CONFIGURATION

CSV_DIR = Path(
    r"C:\Users\JMende95\OneDrive - JNJ\Desktop\ard_data\csv"
)

SOURCE = CSV_DIR / (
    "77242113UC02001_anthem_wk78_ard_merged_20260818.csv"
)

OUTPUT_DIR = CSV_DIR / "compressed"

CHUNK_SIZE = 20 * 1024 * 1024

print("CSV directory exists:", CSV_DIR.exists())
print("Source file exists:", SOURCE.is_file())
print("Source:", SOURCE)

if not SOURCE.is_file():
    print("\nAvailable matching files:")
    for file in CSV_DIR.glob("*anthem*20260818*"):
        print(repr(file.name))
    raise FileNotFoundError(f"ARD file not found: {SOURCE}")

