# AGS Tools - Data Flow & Pathways

## Overview

The AGS Tools plugin provides three export pathways for converting geotechnical AGS4 data into CSV and database formats. Each pathway can feed into the next, creating a complete audit trail of data lineage.

---

## Three Export Pathways

### **Pathway 1: AGS → CSV (ags_2_csv.py)**

Direct conversion from AGS file to CSV folder.

```
AGS file (.ags)
  ↓ [AGSParser.load()]
Parser object with group DataFrames
  ↓ [AGSTransformer(parser)]
    - Reads LOCA group → builds elevation lookup (GL values)
    - Reads GEOL group → builds interval mappings
    - Creates source_file = "filename|folder|project_id"
  ↓ [transform_<group>() methods]
    - Each group transformed to output schema
    - Injects: source_file, ELEV_* columns (elevation calculations)
    - Filters to expected columns per table
  ↓ [CSVExporter.write(table, df, source_file)]
    - Deduplication: matches first 3 pipe parts of source_file
    - Append mode: removes old rows with same source prefix, adds new rows
    - Prevents duplicates on re-export
CSV files + manifest.csv
```

**Example source_file**: `Esholt.ags|batch_01|P001`

---

### **Pathway 2: AGS → Database (ags_2_db_algorithm.py)**

Conversion from AGS file to GeoPackage/SpatiaLite database with geometry.

```
AGS file (.ags)
  ↓ [same as Pathway 1: Parser → Transformer]
Transformed DataFrames with source_file = "filename|db_name|project_id"
  ↓ [QgsVectorFileWriter]
    - Creates in-memory QgsVectorLayers
    - Writes to GeoPackage or SpatiaLite database
    - Preserves geometry (LOCA points as lat/lon, converted from BNG)
GeoPackage/SpatiaLite with source_file column per row
```

**Use case**: User wants to edit data in QGIS (add new boreholes, modify depths, etc.)

---

### **Pathway 3: Database → CSV (db_2_csv_algorithm.py)**

Export an edited database back to CSV format.

```
GeoPackage/SpatiaLite database
  ↓ [_list_db_tables()]
    - Discovers all table names in database
    - Filters out metadata: gpkg_*, sqlite_*, rtree_*, spatial_ref_sys, etc.
  ↓ [QgsVectorLayer(db|layername=TABLE)]
    - Loads each table as a QGIS layer
  ↓ [_layer_to_dataframe()]
    - Converts layer to pandas DataFrame
    - Drops geometry (not exported to CSV)
  ↓ [_ensure_provenance_columns()]
    - Appends csv_folder_name to existing source_file
    - Builds complete lineage trail
  ↓ [CSVExporter.write(table, df, source_file)]
    - Same dedup logic as Pathway 1
CSV files + manifest.csv
```

---

## Key Components

| Component | File | Purpose |
|-----------|------|---------|
| **AGSParser** | `core/parser.py` | Reads .ags file into dict of DataFrames, one per AGS group |
| **AGSTransformer** | `core/transformer.py` | Injects columns (source_file, ELEV_*, lat/lon), builds lookups (LOCA_GL, depth intervals) |
| **CSVExporter** | `core/exporter.py` | Handles dedup (first 3 pipe parts), append mode, manifest.csv tracking |
| **source_file** | All pathways | Audit trail column: `ags_file\|destination\|project_id[\|csv_folder]` |

### source_file Column

The **source_file** column is the key to the entire system:

- **Format**: Pipe-separated string with 3 core parts + optional additional parts
  - `ags_filename` - which AGS file the data originated from
  - `destination` - where data was exported (database name, CSV folder, etc.)
  - `project_id` - project identifier from PROJ group
  - `[csv_folder]` - additional CSV export batch (when going DB → CSV)

- **Deduplication Logic**: CSVExporter compares only the **first 3 parts** for dedup key
  - Same prefix = same source
  - Allows tracking multiple CSV folders from same DB without duplication
  - Latest export with same prefix replaces previous export

---

## Data Lineage Trail Example

### Scenario: Multi-Step Export

**Step 1**: AGS file "Esholt.ags" → Pathway 1 (AGS→CSV to folder "batch_01")
```
source_file = "Esholt.ags|batch_01|P001"
20 rows from Esholt imported to batch_01/
```

**Step 2**: User edits database in QGIS
```
- Adds 5 new boreholes (no prior source_file)
- Modifies depths on 3 existing boreholes
```

**Step 3**: Database → Pathway 3 (DB→CSV to folder "batch_02")
```
For 20 Esholt rows:
  source_file = "Esholt.ags|batch_01|P001|batch_02"
  
For 5 new boreholes (no prior lineage):
  source_file = "batch_02"
```

**Step 4**: Power BI Analysis
```
User can now filter by source_file to see:
✓ Which AGS file originated each row (Esholt.ags vs others)
✓ Which database batch processed it (batch_01 vs edits)
✓ Which CSV export batch it ended up in (batch_02)
✓ Which rows are new (batch_02 only, no prior prefix)
```

---

## Deduplication in Action

### Re-export the Same AGS File

If user re-exports Esholt.ags to batch_01 again:

```
First export:
  CSV has 20 rows with source_file = "Esholt.ags|batch_01|P001"

Second export (same file, same folder):
  1. CSVExporter compares dedup key: "Esholt.ags|batch_01|P001"
  2. Finds 20 existing rows with matching prefix
  3. Removes old 20 rows
  4. Adds new 20 rows (may have different data if AGS was updated)
  5. Result: Still 20 rows (no duplicates, latest data wins)
```

### Same Database → Different CSV Folders

If user exports same database to batch_02 and batch_03:

```
After DB→batch_02 export:
  20 rows with source_file = "Esholt.ags|batch_01|P001|batch_02"

After DB→batch_03 export (same DB):
  Dedup key still = "Esholt.ags|batch_01|P001" (first 3 parts)
  Old batch_02 rows replaced with batch_03 suffix
  20 rows with source_file = "Esholt.ags|batch_01|P001|batch_03"
```

This allows tracking multiple CSV exports from same DB while preventing duplicates.

---

## Workflow Summary

### AGS → CSV (Single Step)
```
ags_2_csv.py:
  1. User selects .ags file
  2. Enters output folder name
  3. Algorithm processes:
     - Parse AGS
     - Transform schema
     - Write CSVs with source_file prefix
  4. User has CSVs ready for analysis
```

### AGS → DB → CSV (Multi-Step with Editing)
```
Step 1 - ags_2_db_algorithm.py:
  - AGS → GeoPackage with geometry

Step 2 - User edits in QGIS:
  - Add new boreholes
  - Modify depths
  - Change lithology
  - Edit coordinates

Step 3 - db_2_csv_algorithm.py:
  - DB → CSV with appended source_file
  - Complete lineage preserved
  - Deduplication prevents overwrites

Result: CSVs with full data lineage for Power BI
```

---

## Manifest File (manifest.csv)

CSVExporter creates manifest.csv tracking all exports:

| Column | Example | Purpose |
|--------|---------|---------|
| source_file | Esholt.ags\|batch_01\|P001 | Data lineage key |
| csv_name | samp.csv | Which table exported |
| ags_group | SAMP | Original AGS group name |
| row_count | 1250 | Rows in this table |
| has_data | true | Whether any data was present |
| exported_at | 2026-05-11 14:30:00 | Export timestamp |

---

## Elevation Calculations (ELEV_* Columns)

AGS Transformer automatically creates elevation columns for depth measurements:

```
Formula: ELEV_<DEPTH_COLUMN> = LOCA_GL - DEPTH_VALUE

Examples:
  ELEV_SAMP_TOP = LOCA_GL - SAMP_TOP
  ELEV_SAMP_BASE = LOCA_GL - SAMP_BASE
  ELEV_SAMP_WDEP = LOCA_GL - SAMP_WDEP
  
  ELEV_ISPT_TOP = LOCA_GL - ISPT_TOP
  ELEV_ISPT_CAS = LOCA_GL - ISPT_CAS
```

Applies to 45+ AGS groups. Each group gets ELEV_* columns for all its depth measurements.

---

## Summary

The AGS Tools system provides:

1. **Three flexible pathways** for different use cases
2. **Complete data lineage** via source_file column
3. **Smart deduplication** preventing duplicates across re-exports
4. **Multi-step workflows** with QGIS editing in the middle
5. **Automatic calculations** (elevation, lat/lon conversion)
6. **Manifest tracking** for audit and debugging

The key insight: **source_file column acts as an audit trail**, allowing users and analysts to trace any row back to its original AGS file, intermediate database exports, and final CSV batch.
