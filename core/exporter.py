# CSV written using pandas, and a manifest of what was written for each table, including row counts and timestamps.
# The manifest is written at the end of the export process.
# Supports both overwrite and append modes for multi-file AGS processing.
import os
import pandas as pd
from datetime import datetime

class CSVExporter:
    def __init__(self, output_dir: str, append_mode: bool = False):
        """
        Initialize CSVExporter.
        
        Args:
            output_dir: Directory to write CSVs to.
            append_mode: If True, append rows to existing CSVs, removing duplicate source files.
                        If False, overwrite.
        """
        self.output_dir = output_dir
        self.append_mode = append_mode
        os.makedirs(output_dir, exist_ok=True)
        self.manifest_rows = []
        self.sources_written = set()  # Track sources being written in this export

    def _extract_dedup_key(self, source_file: str) -> str:
        """
        Extract dedup key from source_file for prefix-match comparison.
        Dedup key is the first 3 pipe-separated parts: ags_filename|db_name|project_id
        This ensures same source (regardless of CSV folder) gets deduplicated.
        """
        parts = source_file.split('|')
        if len(parts) >= 3:
            return '|'.join(parts[:3])
        return source_file

    def write(self, table_name: str, df: pd.DataFrame, source_file: str):
        """Write or append a table DataFrame to CSV, replacing previous rows from the same source."""
        table_name_upper = table_name.upper()
        path = os.path.join(self.output_dir, f"{table_name_upper}.csv")
        
        if self.append_mode and os.path.exists(path):
            # Append mode: read existing CSV, remove rows from same base source, then append new data
            existing_df = pd.read_csv(path, encoding="utf-8-sig")
            
            # Remove existing rows where source_file has same dedup key (ags_filename|db_name|project_id)
            # This ensures re-exports of the same source replace old data, even if CSV folder differs
            if "source_file" in existing_df.columns:
                new_dedup_key = self._extract_dedup_key(source_file)
                existing_df = existing_df[
                    ~existing_df["source_file"].apply(lambda x: self._extract_dedup_key(str(x or '')) == new_dedup_key)
                ]
            
            df = pd.concat([existing_df, df], ignore_index=True)
        
        df.to_csv(path, index=False, encoding="utf-8-sig")  # utf-8-sig for Excel compat
        
        # Track this source as written in this export
        self.sources_written.add(source_file)
        
        self.manifest_rows.append({
            "source_file": source_file,
            "csv_name":    f"{table_name_upper}.csv",
            "ags_group":   table_name_upper,
            "row_count":   len(df),
            "has_data":    len(df) > 0,
            "exported_at": datetime.now().date().isoformat(),
        })

    def write_manifest(self):
        """Write manifest.csv, replacing entries for sources written in this export."""
        df = pd.DataFrame(self.manifest_rows)
        manifest_path = os.path.join(self.output_dir, "manifest.csv")
        
        if self.append_mode and os.path.exists(manifest_path):
            # Append mode: merge with existing, but remove old entries for same base sources
            existing_manifest = pd.read_csv(manifest_path, encoding="utf-8-sig")
            
            # Remove manifest rows where source_file has same dedup key as any source being written
            if "source_file" in existing_manifest.columns:
                new_dedup_keys = {self._extract_dedup_key(src) for src in self.sources_written}
                existing_manifest = existing_manifest[
                    ~existing_manifest["source_file"].apply(
                        lambda x: self._extract_dedup_key(str(x or '')) in new_dedup_keys
                    )
                ]
            
            df = pd.concat([existing_manifest, df], ignore_index=True)
        
        df.to_csv(manifest_path, index=False, encoding="utf-8-sig")