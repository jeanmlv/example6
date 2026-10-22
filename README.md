# example6


from pathlib import Path
import gzip
import hashlib
import json
import shutil

# CONFIGURATION
SOURCE = Path(
    r"C:\Users\SEU_USUARIO\OneDrive - JNJ"
    r"\Desktop\ard_data\csv"
    r"\77242113UC02001_anthem_wk78_ard_merged_20260722.csv"
)

OUTPUT_DIR = SOURCE.parent / "compressed"
CHUNK_SIZE = 20 * 1024 * 1024  # 20 MB

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def main():
    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    gz_path = OUTPUT_DIR / (SOURCE.name + ".gz")

    # Compress without changing CSV contents
    with open(SOURCE, "rb") as src:
        with gzip.open(gz_path, "wb", compresslevel=9) as dst:
            shutil.copyfileobj(src, dst)

    # Split compressed file into 20 MB parts
    parts = []
    with open(gz_path, "rb") as src:
        index = 1
        while chunk := src.read(CHUNK_SIZE):
            part = OUTPUT_DIR / f"{gz_path.name}.part{index:03d}"
            part.write_bytes(chunk)
            parts.append(part.name)
            index += 1

    manifest = {
        "original_filename": SOURCE.name,
        "original_size": SOURCE.stat().st_size,
        "original_sha256": sha256(SOURCE),
        "compressed_sha256": sha256(gz_path),
        "parts": parts,
    }

    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8"
    )

    print("Original:", SOURCE.stat().st_size / 1024**2, "MiB")
    print("Compressed:", gz_path.stat().st_size / 1024**2, "MiB")
    print("Parts:", len(parts))
    print("Output:", OUTPUT_DIR)

if __name__ == "__main__":
    main()

