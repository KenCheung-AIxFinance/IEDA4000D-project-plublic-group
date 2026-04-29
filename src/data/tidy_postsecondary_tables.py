from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# Add project root to Python path for relative imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.data.load_nces_tables import load_all_tables, scan_all_tables


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    source_dir = project_root / "data" / "sources"
    output_dir = project_root / "outputs" / "tables"
    review_dir = output_dir / "review"
    raw_dir = review_dir / "raw_rows"
    parsed_dir = review_dir / "parsed_tables"
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    parsed_dir.mkdir(parents=True, exist_ok=True)

    tidy_df = load_all_tables(source_dir)
    scan_df = scan_all_tables(source_dir)

    output_path = output_dir / "nces_postsecondary_tidy.csv"
    scan_path = output_dir / "nces_postsecondary_row_scan.csv"
    tidy_df.to_csv(output_path, index=False)
    scan_df.to_csv(scan_path, index=False)

    for source_file, group in scan_df.groupby("source_file", sort=True):
        (raw_dir / f"{Path(source_file).stem}_scan.csv").write_text(group.to_csv(index=False), encoding="utf-8")

    for table_id, group in tidy_df.groupby("table_id", sort=False):
        safe_table_id = str(table_id).replace("/", "-").replace(" ", "_")
        (parsed_dir / f"table_{safe_table_id}_tidy.csv").write_text(group.to_csv(index=False), encoding="utf-8")

    print(f"Saved {len(tidy_df)} tidy rows to {output_path}")
    print(f"Saved {len(scan_df)} scanned rows to {scan_path}")
    print(f"Wrote {scan_df['source_file'].nunique()} raw review files to {raw_dir}")
    print(f"Wrote {tidy_df['table_id'].nunique()} parsed review files to {parsed_dir}")
    print(tidy_df.head(10).to_string(index=False))
    print(scan_df.head(10).to_string(index=False))

    missing_ids = sorted(set(str(i) for i in range(1, 18)) - set(tidy_df["table_id"].astype(str).unique()))
    print(f"Missing table ids in tidy output: {missing_ids}")
    print(f"Row types in scan output: {sorted(scan_df['row_type'].unique())}")
    print(f"Rows with notes in scan output: {(scan_df['row_type'] == 'note').sum()}")

    flagged_estimates = tidy_df[tidy_df["estimate_flag"].notna()]
    print(f"Parsed rows carrying estimate flags: {len(flagged_estimates)}")
    if not flagged_estimates.empty:
        print(flagged_estimates[["table_id", "row_label", "column_group", "column_label", "estimate_flag"]].head(10).to_string(index=False))

    section_rows = tidy_df[tidy_df["section_label"].astype(str) != ""]
    print(f"Parsed rows carrying section labels: {len(section_rows)}")
    if not section_rows.empty:
        print(section_rows[["table_id", "section_label", "row_label"]].drop_duplicates().head(10).to_string(index=False))

    print("Review workflow:")
    print(f"- raw scans: {raw_dir}")
    print(f"- parsed tables: {parsed_dir}")
    print("Compare each *_scan.csv against the matching parsed table CSV before downstream analysis.")

    scan_summary = (
        scan_df.groupby(["table_id", "source_file", "file_role", "row_type"]).size().unstack(fill_value=0).reset_index()
    )
    summary_path = review_dir / "review_summary.csv"
    scan_summary.to_csv(summary_path, index=False)
    print(f"Saved review summary to {summary_path}")

    parsed_summary = (
        tidy_df.groupby(["table_id", "table_title", "source_file"]).agg(
            parsed_rows=("row_number", "nunique"),
            sections=("section_label", lambda s: s.astype(str).replace("", pd.NA).dropna().nunique()),
            flagged_cells=("estimate_flag", lambda s: s.notna().sum()),
        ).reset_index()
    )
    parsed_summary_path = review_dir / "parsed_summary.csv"
    parsed_summary.to_csv(parsed_summary_path, index=False)
    print(f"Saved parsed summary to {parsed_summary_path}")


if __name__ == "__main__":
    main()
