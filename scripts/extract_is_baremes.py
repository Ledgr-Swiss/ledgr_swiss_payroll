"""Validation et statistiques des fichiers baremes IS ESTV.

Usage:
  python scripts/extract_is_baremes.py --data-dir ledgr_swiss_payroll/data/is-baremes/2026
"""
import argparse
import hashlib
from pathlib import Path


def parse_header(file_path):
    with open(file_path, "r", encoding="latin-1") as f:
        line = f.readline()
    if line[0:2] != "00":
        return None
    return {"canton": line[2:4], "created": line[19:27]}


def sha256(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description="Validate ESTV IS tariff files")
    ap.add_argument("--data-dir", required=True, type=Path)
    ap.add_argument("--canton", type=str)
    args = ap.parse_args()

    for fp in sorted(args.data_dir.glob("tar*.txt")):
        hdr = parse_header(fp)
        if not hdr:
            continue
        if args.canton and hdr["canton"] != args.canton.upper():
            continue

        h = sha256(fp)
        total = 0
        payroll = 0
        codes = set()
        with open(fp, "r", encoding="latin-1") as f:
            for line in f:
                if len(line.rstrip()) >= 59 and line[0:2] == "06":
                    total += 1
                    code = line[6:16].strip()
                    codes.add(code)
                    if code[0] in "ABCH":
                        payroll += 1

        ct = hdr["canton"]
        cr = hdr["created"]
        print(f"\n=== {ct} ({fp.name}) ===")
        print(f"  Created: {cr}")
        print(f"  SHA-256: {h}")
        print(f"  Total records: {total}")
        print(f"  Payroll (A/B/C/H): {payroll}")
        print(f"  Codes: {sorted(codes)}")


if __name__ == "__main__":
    main()
