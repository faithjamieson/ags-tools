# AGS Tools: Plugin Functionality, Data Pipeline & Deduplication Logic

## Overview

The AGS Tools plugin provides three processing algorithms for exporting geotechnical AGS4 data:

| Algorithm | Source | Destination | Purpose |
|-----------|--------|-------------|---------|
| **AGS to DB** (`ags_2_db_algorithm.py`) | `.ags` file | GeoPackage / SpatiaLite | Parse and store AGS data in a spatial database |
| **AGS to CSV** (`ags_2_csv.py`) | `.ags` file | Folder of `.csv` files | Export AGS data directly to CSVs for Power BI or other data visualisation tools|
| **DB to CSV** (`db_2_csv_algorithm.py`) | GeoPackage / SpatiaLite | Folder of `.csv` files | Export an edited database to CSVs for Power BI |

All three algorithms write a `source_file` column into every output row, providing a complete audit trail of where data came from. Deduplication uses a prefix-match key on that column to prevent duplicate rows when re-exporting or appending.

---

## The Data Pipeline

### Full End-to-End Flow

```
  .ags file
      │
      ├──[AGS to DB]──────────────────► GeoPackage / SpatiaLite (.gpkg / .sqlite)
      │                                         │
      │                                         └──[DB to CSV]──► CSV folder
      │
      └──[AGS to CSV]─────────────────────────────────────────► CSV folder
```

A typical workflow uses **AGS to DB first**, then **DB to CSV** — this allows data to be reviewed and edited in QGIS before being exported to Power BI. The **AGS to CSV** pathway skips the database entirely for quick exports.

---

## The `source_file` Column

Every row in every output CSV contains a `source_file` column. Its format varies by pathway and records full data lineage:

| Pathway | Format | Example |
|---------|--------|---------|
| AGS to CSV | `ags_filename\|csv_folder_name\|project_id` | `Esholt.ags\|site_export\|BH-001` |
| AGS to DB (stored in DB) | `ags_filename\|db_filename\|project_id` | `Esholt.ags\|Esholt.gpkg\|BH-001` |
| DB to CSV (appended) | `ags_filename\|db_filename\|project_id\|csv_folder_name` | `Esholt.ags\|Esholt.gpkg\|BH-001\|site_export` |

The `project_id` is read directly from the `PROJ_ID` field in the AGS file's `PROJ` group. If absent, it is omitted from the string.

---

## Algorithm 1: AGS to CSV (`ags_2_csv.py`)

### What It Does
Reads a single `.ags` file, transforms every supported AGS group through `AGSTransformer`, and writes each group as a separate `.csv` file into a named folder. Optionally appends to an existing CSV folder rather than overwriting it.

### Parameters

| Parameter | Description |
|-----------|-------------|
| Input AGS file | Path to the `.ags` file to export |
| Output parent folder | The directory that will contain the named CSV folder |
| CSV folder name | Name of the subfolder to create/append into |
| Allow append to existing folder? | If ticked, prompts the user at runtime whether to append or overwrite |

### Step-by-Step Processing

```
1. Load .ags file via AGSParser
       └─ AGS4.AGS4_to_dataframe() → dict of {GROUP_NAME: DataFrame}

2. Extract PROJ_ID from PROJ group
       └─ source_file = "ags_filename|csv_folder_name|PROJ_ID"

3. Build AGSTransformer(parser, source_file)
       └─ Reads LOCA and GEOL at construction to build lookup dictionaries:
            • loca_gl_lookup        LOCA_ID → LOCA_GL (ground level, mAOD)
            • loca_clst_lookup      LOCA_ID → cluster classification
            • loca_type_lookup      LOCA_ID → borehole type
            • geol_intervals_lookup LOCA_ID → list of GEOL intervals with TOP/BASE/LEG/GEO2

4. For each table in TABLES list:
       └─ Call transformer.transform_<table>()
            └─ Reads raw AGS group DataFrame
            └─ Drops FILE_FSET column
            └─ Injects source_file column
            └─ Injects samp_id (composite key) for sample-linked tables
            └─ Reindexes to fixed column schema from expected_groups.EXPECTED_CSVS
            └─ _inject_elevation() → calculates ELEV_* columns (see below)
            └─ _inject_filter_columns() → backfills GEOL_LEG, GEOL_GEO2, GEOL_GEOL,
                                          LOCA_CLST, LOCA_TYPE using interval lookups

5. CSVExporter.write(table, df, source_file)
       └─ If append_mode and file exists: read existing, strip same source, concat
       └─ Write to TABLE_NAME.csv (utf-8-sig for Excel compatibility)

6. CSVExporter.write_manifest()
       └─ Writes manifest.csv with row counts and timestamps
```

### Tables Exported (42 groups)

| Category | Tables |
|----------|--------|
| Project | `proj` |
| Location | `loca` |
| Samples | `samp` |
| Geology / field description | `geol`, `bkfl`, `detl`, `weth`, `core`, `frac`, `hdph`, `wins` |
| Groundwater | `wstg`, `wstd`, `mong`, `mond` |
| In-situ tests | `ispt`, `dcpg`, `dcpt`, `dprg`, `icbr`, `ipid`, `ivan`, `chis`, `ptim` |
| Lab tests | `lpdn`, `llpl`, `grat`, `grag`, `mcvg`, `lnmc`, `mcvt`, `cbrg`, `cbrt`, `cmpg`, `cmpt`, `cong`, `cons`, `shbg`, `shbt`, `trig`, `trit`, `gchm`, `eres` |

If a group is not present in the AGS file, an empty CSV with the correct column headers is written (guarantees stable schema for Power BI).

### Append Mode Detail

When **Allow append** is ticked and the folder already contains CSVs, the user is shown a popup at runtime:

> "The output folder already contains CSV files. Do you want to append the new AGS data to the existing CSVs?"

- **Yes → append**: `CSVExporter(append_mode=True)` — existing rows from the same source are replaced, rows from other sources are preserved.
- **No → overwrite**: `CSVExporter(append_mode=False)` — all existing CSVs are overwritten.

---

## Algorithm 2: AGS to DB (`ags_2_db_algorithm.py`)

### What It Does
Reads a `.ags` file and writes each AGS group as a table into a GeoPackage or SpatiaLite database. The `LOCA` group is written as a spatial point layer (WGS84 lat/lon derived from BNG eastings/northings). Optionally also exports CSVs at the same time using the same transformer output.

### Parameters

| Parameter | Description |
|-----------|-------------|
| Input AGS file | Path to the `.ags` file |
| Coordinate reference system | CRS for input coordinates (default: EPSG:27700 BNG) |
| Output Database File | Path to create/overwrite the `.gpkg` or `.sqlite` file |
| Description of proposed use of data | Optional free-text label stored in the DB and CSVs |
| Create CSV Files for Power BI | Whether to also run the CSV export step |
| Output CSV Database Folder | Parent folder for CSV output (if CSV export enabled) |
| Folder name of CSV database | Subfolder name for CSVs |
| Append to existing CSV files | Append mode for CSV step |

### source_file in the Database

The database row `source_file` format is:
```
ags_filename|db_filename|project_id
```

This is injected at the point of writing each table layer into the GeoPackage/SpatiaLite file, so every row stored in the database carries its origin.

### Optional CSV Export

When **Create CSV Files** is enabled, AGS to DB runs the same transformer and CSVExporter pipeline as AGS to CSV. The source_file used for CSVs is the same `ags_filename|db_filename|project_id` string (not a CSV folder variant) — the CSV folder name is not appended at this stage. That happens only in DB to CSV.

---

## Algorithm 3: DB to CSV (`db_2_csv_algorithm.py`)

### What It Does
Reads every table from an existing GeoPackage or SpatiaLite database and writes each table as a `.csv` file. This is the primary route for exporting data that has been **reviewed or edited in QGIS** after the initial AGS import. It works independently of any AGS file.

### Parameters

| Parameter | Description |
|-----------|-------------|
| Input Database File | Path to the `.gpkg` or `.sqlite` file (auto-populated from active QGIS layer) |
| Output CSV Database Folder | Parent directory for CSV output |
| Folder name of CSV database | Optional subfolder name (if blank, writes directly into the parent folder) |
| Append to existing CSV files | Append mode toggle |

### Active Layer Auto-Population
The algorithm tries to detect the GeoPackage path from the currently active layer in QGIS:
```python
def _get_active_db_path():
    active = iface.activeLayer()
    source = active.source()           # e.g. "/path/Esholt.gpkg|layername=LOCA"
    db_path = source.split('|')[0]     # extracts "/path/Esholt.gpkg"
```
This pre-fills the database path so users don't need to browse for it manually.

### Step-by-Step Processing

```
1. Discover all tables in the database
       └─ QgsProviderRegistry.querySublayers() (QGIS 3.22+)
       └─ Falls back to GDAL/OGR if unavailable
       └─ Filters out internal metadata tables (gpkg_*, sqlite_*, rtree_*, etc.)

2. For each table:
       └─ Load as QgsVectorLayer(f'{db_path}|layername={table}')
       └─ Convert to pandas DataFrame via _layer_to_dataframe()
            └─ Reads all attribute fields (geometry dropped)

3. _ensure_provenance_columns(df, csv_folder_name)
       └─ If source_file column exists (from AGS import):
            Appends csv_folder_name: "existing_source_file|csv_folder_name"
            e.g. "Esholt.ags|Esholt.gpkg|BH-001" → "Esholt.ags|Esholt.gpkg|BH-001|site_export"
       └─ If source_file column is absent:
            Sets source_file = "csv_folder_name"

4. Extract batch_source_file for deduplication key
       └─ Takes the first non-empty source_file value from the DataFrame
       └─ Fallback: "db_filename|csv_folder_name"

5. CSVExporter.write(table, df, batch_source_file)
       └─ Append/dedup logic applied (see Deduplication section)

6. CSVExporter.write_manifest()
```

### Why csv_folder_name is Appended (Not Replaced)

The DB already stores the full origin trail (`ags_filename|db_filename|project_id`). Appending the CSV folder name to this string means the exported CSV retains the complete lineage:

```
Esholt.ags|Esholt.gpkg|BH-001|site_export
```

This allows Power BI to filter by:
- Which AGS file the data came from (`Esholt.ags`)
- Which database it was staged in (`Esholt.gpkg`)
- Which project it belongs to (`BH-001`)
- Which CSV export batch this is from (`site_export`)

---

## The Transformer: Injected Columns

`AGSTransformer` adds several calculated columns that are not in the raw AGS file.

### 1. `source_file`
Injected into every row of every table. Format described above.

### 2. `samp_id` (sample-linked tables only)
A composite key for joining sample-linked lab test tables back to their parent sample:
```
samp_id = LOCA_ID + "_" + SAMP_REF + "_" + SAMP_TOP
```
Applies to: `samp`, `lpdn`, `llpl`, `grat`, `grag`, `mcvg`, `lnmc`, `mcvt`, `cbrg`, `cbrt`, `cmpg`, `cmpt`, `cong`, `cons`, `shbg`, `shbt`, `trig`, `trit`, `gchm`, `eres`.

### 3. `lat` / `lon` (`loca` table only)
WGS84 decimal degrees derived from BNG grid references (LOCA_NATE / LOCA_NATN) using the `bng_to_wgs84()` utility. Enables Power BI map visuals without requiring coordinate transformation outside the plugin.

### 4. `ELEV_*` columns (depth-bearing tables)
For every depth measurement column in a table, a corresponding elevation column is calculated:
```
ELEV_<depth_col> = LOCA_GL - <depth_col>
```
where `LOCA_GL` is the ground level (mAOD) from the LOCA table, looked up per borehole.

**45+ tables have elevation columns.** Multiple depth columns per table each get their own `ELEV_*` column:

| Table | Depth columns → Elevation columns |
|-------|----------------------------------|
| `geol` | GEOL_TOP → ELEV_GEOL_TOP, GEOL_BASE → ELEV_GEOL_BASE |
| `ispt` | ISPT_TOP → ELEV_ISPT_TOP, ISPT_CAS → ELEV_ISPT_CAS |
| `samp` | SAMP_TOP → ELEV_SAMP_TOP, SAMP_BASE → ELEV_SAMP_BASE, SAMP_WDEP → ELEV_SAMP_WDEP |
| `core` | CORE_TOP → ELEV_CORE_TOP, CORE_BASE → ELEV_CORE_BASE |
| `wstg` | WSTG_DPTH → ELEV_WSTG_DPTH, WSTG_SEAL → ELEV_WSTG_SEAL, WSTG_CAS → ELEV_WSTG_CAS |
| `ptim` | PTIM_DPTH → ELEV_PTIM_DPTH, PTIM_CAS → ELEV_PTIM_CAS |
| `fghg` | 6 depth columns → 6 ELEV_* columns |
| `loca` | LOCA_FDEP → ELEV_LOCA_FDEP |
| *...40+ more* | *(see `ELEVATION_DEPTH_COLUMNS` in `core/transformer.py`)* |

If `LOCA_GL` is absent for a borehole, or the depth cell is empty, the elevation value is `None`.

### 5. Filter columns (`GEOL_LEG`, `GEOL_GEO2`, `GEOL_GEOL`, `LOCA_CLST`, `LOCA_TYPE`)
These are back-filled onto all tables using interval-based lookup against the GEOL table. For each row, the code finds which GEOL interval the row's depth falls within and copies the geology code, legend, and classification from that interval. This allows Power BI to filter any test result by geology without a join.

---

## Core Deduplication Logic

### Dedup Key Extraction
```python
def _extract_dedup_key(self, source_file: str) -> str:
    """Extract first 3 pipe-separated parts: ags_filename|db_name|project_id"""
    parts = source_file.split('|')
    if len(parts) >= 3:
        return '|'.join(parts[:3])
    return source_file
```

**Key insight:** Different CSV export folders with the same base source use the same dedup key → rows replaced, not duplicated.

---

---

## Deduplication Behaviour by Pathway

### Pathway 1: AGS to CSV (Direct AGS → CSV Export)

### Source File Format
```
ags_filename | csv_folder_name | project_id
```
Example: `sample.ags|ags_csv_export|BH-001`

### Append Behavior

#### First Export (No Existing Data)
1. User runs AGS2CSV with `sample.ags`, folder name = `ags_csv_export`
2. source_file = `sample.ags|ags_csv_export|BH-001`
3. CSVs created with this source_file value in every row

```
LOCA.csv:
LOCA_ID | LOCA_GL | source_file
--------+---------+----------------------------------
BH1     | 56.8    | sample.ags|ags_csv_export|BH-001
BH2     | 62.3    | sample.ags|ags_csv_export|BH-001
```

#### Second Export - Same AGS, Append Mode
1. User re-exports `sample.ags` with `Allow append = Yes`, folder = `ags_csv_export`
2. source_file = `sample.ags|ags_csv_export|BH-001` (same dedup key)
3. CSVExporter reads existing LOCA.csv
4. **Removes all rows where `source_file` prefix-matches `sample.ags|ags_csv_export|BH-001`**
5. Concatenates remaining + new rows
6. Writes result

```
Result (old data replaced, not duplicated):
LOCA_ID | LOCA_GL | source_file
--------+---------+----------------------------------
BH1     | 56.8    | sample.ags|ags_csv_export|BH-001  (NEW)
BH2     | 62.3    | sample.ags|ags_csv_export|BH-001  (NEW)
```

✅ **Safe:** Same source = same data, no duplicates

---

### Pathway 2: AGS to DB with Optional CSV Export

### Source File Format (DB Phase)
```
ags_filename | db_filename | project_id
```
Example: `sample.ags|sample.gpkg|BH-001`

### Source File Format (CSV Phase)
When exporting DB to CSV, CSVExporter reads `source_file` from each DB row and appends CSV folder name:
```
existing_source_file | csv_folder_name
```
Example: `sample.ags|sample.gpkg|BH-001|ags_csv_export`

### Append Behavior

#### Step 1: AGS → GeoPackage
1. User runs AGS2DB with `sample.ags` → creates `sample.gpkg`
2. All rows in DB tables have source_file = `sample.ags|sample.gpkg|BH-001`
3. DB created/updated

#### Step 2: AGS2DB Re-export (Updating Same DB)
1. User re-exports `sample.ags` to same `sample.gpkg`
2. AGS2DB writes with source_file = `sample.ags|sample.gpkg|BH-001` (same dedup key)
3. **GeoPackage updated** (rows replaced in database layer, not duplicated)

#### Step 3: Export DB to CSV (First Time)
1. User runs DB2CSV: `sample.gpkg` → CSV folder `ags_csv_export`
2. DB rows have source_file = `sample.ags|sample.gpkg|BH-001`
3. _ensure_provenance_columns() appends folder name: `sample.ags|sample.gpkg|BH-001|ags_csv_export`
4. CSV created with this extended source_file

```
LOCA.csv:
LOCA_ID | LOCA_GL | source_file
--------+---------+--------------------------------------------------
BH1     | 56.8    | sample.ags|sample.gpkg|BH-001|ags_csv_export
BH2     | 62.3    | sample.ags|sample.gpkg|BH-001|ags_csv_export
```

#### Step 4: Export DB to CSV (Append Mode, Different Folder)
1. User runs DB2CSV: same `sample.gpkg` → **different** CSV folder `project_exports`
2. DB rows still have source_file = `sample.ags|sample.gpkg|BH-001`
3. _ensure_provenance_columns() appends new folder: `sample.ags|sample.gpkg|BH-001|project_exports`
4. Dedup key = `sample.ags|sample.gpkg|BH-001` (first 3 parts)
5. CSVExporter reads existing CSV, finds old rows with dedup key prefix match, **removes them**
6. Appends new rows with new folder name

```
Result in same LOCA.csv:
LOCA_ID | LOCA_GL | source_file
--------+---------+--------------------------------------------------
BH1     | 56.8    | sample.ags|sample.gpkg|BH-001|project_exports (NEW)
BH2     | 62.3    | sample.ags|sample.gpkg|BH-001|project_exports (NEW)
```

✅ **Safe:** Same DB source = rows replaced; different folders tracked in source_file but not duplicated

---

### Pathway 3: DB to CSV (Database → CSV Export)

### Source File Format
```
db_filename | csv_folder_name
```
Example: `sample.gpkg|ags_csv_export`

### Append Behavior

#### First Export
1. User runs DB2CSV: `sample.gpkg` → `ags_csv_export` folder
2. Tables read from DB (source_file may exist from AGS2DB import)
3. If source_file absent, set to `sample.gpkg|ags_csv_export`
4. If source_file exists (from AGS2DB), append folder: `sample.ags|sample.gpkg|BH-001|ags_csv_export`
5. CSVs written

#### Second Export - Append Mode, Same CSV Folder
1. User re-exports same `sample.gpkg` to same `ags_csv_export` folder
2. source_file in DB = `sample.ags|sample.gpkg|BH-001`
3. Appends folder again: `sample.ags|sample.gpkg|BH-001|ags_csv_export`
4. **Dedup key = `sample.ags|sample.gpkg|BH-001`** (unchanged)
5. CSVExporter removes old rows with matching prefix
6. Appends new rows

✅ **Safe:** Same DB + folder = rows replaced

#### Third Export - Append Mode, New CSV Folder
1. User exports same `sample.gpkg` to **new** folder `new_export`
2. source_file = `sample.ags|sample.gpkg|BH-001|new_export` (different folder)
3. **Dedup key = `sample.ags|sample.gpkg|BH-001`** (same prefix)
4. CSVExporter removes previous rows from both folders
5. Appends only new folder's rows

```
Result:
LOCA_ID | LOCA_GL | source_file
--------+---------+-----------------------------------------
BH1     | 56.8    | sample.ags|sample.gpkg|BH-001|new_export
BH2     | 62.3    | sample.ags|sample.gpkg|BH-001|new_export
```

⚠️ **Important:** Re-exporting same DB to new CSV folder **removes** old folder's rows (same base source). If you want to keep both, append them to the **same folder**.

---

## Manifest Tracking

The `manifest.csv` file uses the same dedup logic:

```python
def write_manifest(self):
    # For each source_file being written, extract dedup_key
    new_dedup_keys = {self._extract_dedup_key(src) for src in self.sources_written}
    
    # Remove old manifest entries with matching dedup_keys
    # Then append new manifest entries
```

This ensures manifest.csv stays in sync with actual CSV data:

```
manifest.csv (after multiple appends):
source_file                                 | csv_name  | row_count | exported_at
--------------------------------------------+-----------+-----------+-------------
sample.ags|ags_csv_export|BH-001           | LOCA.csv  | 2         | 2026-05-10
sample.ags|ags_csv_export|BH-001           | SAMP.csv  | 5         | 2026-05-10
```

---

## Summary Table: What Happens on Append

| Scenario | Dedup Key | Result |
|----------|-----------|--------|
| AGS to CSV, re-export same file, same folder | `sample.ags` + folder + proj | Old rows replaced ✅ |
| AGS to CSV, re-export same file, different folder | `sample.ags` + folder + proj | Old folder's rows removed, new folder's rows added ⚠️ |
| AGS to DB, re-export to same DB | `sample.ags` + db + proj | DB table updated, no duplicates ✅ |
| DB to CSV, same DB, same folder | `sample.ags` + db + proj | Old rows replaced ✅ |
| DB to CSV, same DB, different folder | `sample.ags` + db + proj | Old folder's rows removed, new folder's rows added ⚠️ |

---

## Code References

| File | Key function | Role |
|------|-------------|------|
| `core/exporter.py` | `_extract_dedup_key()` | Extracts first 3 pipe parts for comparison |
| `core/exporter.py` | `write()` | Deduplicates on append by removing matching source_file prefixes, then concatenates |
| `core/exporter.py` | `write_manifest()` | Applies same dedup logic to manifest.csv |
| `core/transformer.py` | `_inject_elevation()` | Calculates ELEV_* columns from LOCA_GL minus depth values |
| `core/transformer.py` | `_inject_filter_columns()` | Backfills GEOL_LEG, GEO2, GEOL_GEOL, LOCA_CLST, LOCA_TYPE using interval lookup |
| `core/transformer.py` | `_pass_through()` | Generic method: drops FILE_FSET, injects source_file, reindexes to schema |
| `core/parser.py` | `AGSParser.load()` | Loads AGS file into dict of DataFrames via python-ags4 |
| `ags_2_csv.py` | `processAlgorithm()` | Asks user to append/overwrite; formats source_file as `ags_filename\|csv_folder_name\|project_id` |
| `db_2_csv_algorithm.py` | `_ensure_provenance_columns()` | Appends csv_folder_name to existing source_file for full lineage |
| `db_2_csv_algorithm.py` | `_get_active_db_path()` | Auto-detects GeoPackage path from active QGIS layer |
| `db_2_csv_algorithm.py` | `_list_db_tables()` | Enumerates tables in GeoPackage/SpatiaLite, filtering out metadata tables |
| `expected_groups.py` | `EXPECTED_CSVS` | Defines exact column schema for every output CSV, including all ELEV_* columns |

---

## Recommendations for Users

1. **Standard workflow** → AGS to DB first (for QGIS review/edit), then DB to CSV for Power BI
2. **Quick export** → AGS to CSV if no database editing is needed
3. **Same source, same folder, append mode** → Safe and idempotent; re-running produces the same result
4. **Adding a second AGS file to the same CSV folder** → Use append mode; rows from each AGS file are tracked separately by source_file
5. **Same source, different folders** → The new folder's rows replace the old folder's rows (same dedup key); only the latest folder is retained
6. **To keep exports to multiple folders** → Append all into the **same folder** and filter by source_file in Power BI
7. **Check manifest.csv** → Always verify row counts and `exported_at` timestamps after append operations
8. **Power BI relationships** → Use `source_file` to build slicers showing AGS origin, database, project ID, and CSV export batch
9. **Empty tables** → Groups absent from the AGS file still produce CSVs with correct headers, ensuring Power BI data model never breaks due to a missing file
