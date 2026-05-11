# -*- coding: utf-8 -*-

"""
/***************************************************************************
 AGSTools
                                 A QGIS plugin
 Export a SpatiaLite / GeoPackage database to a folder of CSVs.
                              -------------------
        begin                : 2025
        copyright            : (C) 2025 by Oliver Burdekin / burdGIS
        email                : info@burdgis.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Oliver Burdekin / burdGIS'
__date__ = '2025'
__copyright__ = '(C) 2025 by Oliver Burdekin / burdGIS'

__revision__ = '$Format:%H$'

import os
import pandas as pd

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterFile,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterString,
    QgsProcessingException,
    QgsVectorLayer,
    QgsProject,
    QgsProviderRegistry,
)
from qgis.utils import iface

if __package__:
    from .core.exporter import CSVExporter
else:
    from core.exporter import CSVExporter


# ================================================================ #
# Helper Functions for Database Operations                           #
# ================================================================ #

def _get_active_db_path():
    """
    Auto-detect GeoPackage/SpatiaLite path from active QGIS layer.
    
    Extracts database path from the layer's OGR source string:
      source = "/path/file.gpkg|layername=LOCA"
      returns: "/path/file.gpkg"
    
    Returns empty string if no valid database layer is active.
    """
    try:
        if iface is None:
            return ''
        active = iface.activeLayer()
        if active is None:
            return ''
        source = active.source()
        # Source is often "/path/to/file.gpkg|layername=LOCA"
        db_path = source.split('|')[0]
        if db_path.lower().endswith(('.gpkg', '.sqlite')):
            return db_path
    except Exception:
        pass
    return ''


def _layer_to_dataframe(layer: QgsVectorLayer) -> pd.DataFrame:
    """
    Convert QgsVectorLayer to pandas DataFrame.
    
    - Reads all attribute fields from features
    - Drops geometry column (not exported to CSV)
    - Returns DataFrame with field names as column headers
    """
    fields = [field.name() for field in layer.fields()]
    rows = []
    for feature in layer.getFeatures():
        rows.append([feature[f] for f in fields])
    return pd.DataFrame(rows, columns=fields)


def _list_db_tables(db_path: str) -> list:
    """
    List all table/layer names in GeoPackage or SpatiaLite.
    
    Strategy:
      1. Try QGIS OGR provider API (QGIS 3.22+)
      2. Fall back to GDAL/OGR if API unavailable
      3. Return list of table names (no duplicates)
    """
    try:
        md = QgsProviderRegistry.instance().providerMetadata('ogr')
        sublayers = md.querySublayers(db_path)
        names = []
        for sub in sublayers:
            name = sub.name()
            if name and name not in names:
                names.append(name)
        return names
    except Exception:
        pass

    # GDAL fallback
    try:
        from osgeo import ogr
        ds = ogr.Open(db_path, 0)
        if ds is None:
            return []
        names = [ds.GetLayerByIndex(i).GetName() for i in range(ds.GetLayerCount())]
        ds = None
        return names
    except Exception:
        return []


def _first_non_empty_from_series(series: pd.Series) -> str:
    for value in series:
        text = str(value or '').strip()
        if text:
            return text
    return ''


def _get_project_id_from_db(db_path: str) -> str:
    """Get first non-empty PROJ_ID from PROJ table, if present."""
    proj_layer = QgsVectorLayer(f'{db_path}|layername=PROJ', 'PROJ', 'ogr')
    if not proj_layer.isValid():
        return ''

    fields = [field.name() for field in proj_layer.fields()]
    if 'PROJ_ID' not in fields:
        return ''

    for feature in proj_layer.getFeatures():
        proj_id = str(feature['PROJ_ID'] or '').strip()
        if proj_id:
            return proj_id
    return ''


def _ensure_provenance_columns(
    df: pd.DataFrame,
    csv_folder_name: str,
) -> pd.DataFrame:
    """
    Append csv_folder_name to source_file for complete data lineage.
    
    Behavior:
      - If source_file exists (from AGS→DB import):
        Append folder: "ags_filename|db_name|proj_id|csv_folder_name"
      - If source_file absent:
        Set to: "csv_folder_name"
    
    Deduplication:
      - Compares first 3 pipe parts (ags_filename|db_name|proj_id)
      - Same source to different folders → old folder replaced by new folder
      - Enables tracking multiple export batches while preventing duplicates
    """
    out = df.copy()
    
    if 'source_file' not in out.columns:
        out['source_file'] = csv_folder_name
    else:
        # Append csv_folder_name to existing source_file for full lineage
        source_values = out['source_file'].fillna('').astype(str).str.strip()
        out['source_file'] = source_values.apply(
            lambda x: f"{x}|{csv_folder_name}" if x else csv_folder_name
        )
    
    return out


class DB2CSVAlgorithm(QgsProcessingAlgorithm):
    """
    QGIS Processing algorithm: Export GeoPackage/SpatiaLite database to CSVs.
    
    Use case:
      Export a database that has been reviewed/edited in QGIS to CSV format
      for Power BI or other analytical tools.
    
    Processing Flow:
      1. Load and validate database path
      2. Discover all tables (filter out metadata tables)
      3. For each table:
         - Load as QgsVectorLayer
         - Convert to pandas DataFrame
         - Append csv_folder_name to source_file (data lineage)
         - Write to CSV with dedup/append logic
      4. Write manifest.csv
    
    Modes:
      - Overwrite: Replace all CSVs in output folder
      - Append: Keep existing CSVs, add/replace rows from this DB
    """

    # Parameter keys
    INPUT_DB = 'INPUT_DB'
    CSV_OUTPUT_DIR = 'CSV_OUTPUT_DIR'
    CSV_OUTPUT_FOLDER_NAME = 'CSV_OUTPUT_FOLDER_NAME'
    CSV_APPEND_MODE = 'CSV_APPEND_MODE'

    # ================================================================ #
    # QGIS Algorithm Interface: Parameter Definition                    #
    # ================================================================ #
    
    def initAlgorithm(self, config):
        """Define algorithm parameters shown in QGIS Processing dialog."""

        # Auto-detect GeoPackage from active QGIS layer
        default_db = _get_active_db_path()

        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT_DB,
                self.tr('Input Database File (GeoPackage or SpatiaLite)'),
                behavior=QgsProcessingParameterFile.File,
                fileFilter='GeoPackage (*.gpkg);;SpatiaLite (*.sqlite)',
                defaultValue=default_db,
            )
        )

        # --- Output CSV folder ----------------------------------------
        self.addParameter(
            QgsProcessingParameterFile(
                self.CSV_OUTPUT_DIR,
                self.tr('Output CSV Database Folder (existing or new)'),
                behavior=QgsProcessingParameterFile.Folder,
                optional=False,
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.CSV_OUTPUT_FOLDER_NAME,
                self.tr('Folder name of CSV database (leave blank to use folder above directly)'),
                defaultValue='',
                optional=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.CSV_APPEND_MODE,
                self.tr('Append to existing CSV files'),
                defaultValue=False,
            )
        )

    # ------------------------------------------------------------------ #
    # ================================================================ #
    # Main Processing Logic                                              #
    # ================================================================ #
    
    def processAlgorithm(self, parameters, context, feedback):
        """
        Main processing function: validate → discover tables → transform → export CSVs.
        
        Flow:
          1. Extract and validate parameters
          2. Resolve output directory
          3. Discover tables in database (filter metadata)
          4. Initialize CSVExporter with append mode
          5. For each table:
             - Load as QgsVectorLayer
             - Convert to DataFrame
             - Append csv_folder_name for lineage
             - Write CSV with dedup logic
          6. Write manifest.csv
        """
        
        # ---- Step 1: Validate Parameters ---- #
        db_path = self.parameterAsString(parameters, self.INPUT_DB, context)
        # Validate database file
        if not db_path:
            raise QgsProcessingException(
                'No database file specified. Select or browse to a .gpkg / .sqlite file.'
            )
        if not os.path.exists(db_path):
            raise QgsProcessingException(f'Database file not found: {db_path}')

        # Validate output directory
        csv_parent_dir = self.parameterAsString(parameters, self.CSV_OUTPUT_DIR, context)
        if not csv_parent_dir:
            raise QgsProcessingException('No output CSV folder specified.')

        # Get optional subfolder name
        folder_name = (
            self.parameterAsString(parameters, self.CSV_OUTPUT_FOLDER_NAME, context) or ''
        ).strip()

        # Get append mode flag
        append_mode = self.parameterAsBool(parameters, self.CSV_APPEND_MODE, context)

        # ---- Step 2: Resolve Output Path ---- #
        # If folder_name provided, create subfolder; otherwise use parent directly
        if folder_name:
            csv_output_dir = os.path.join(csv_parent_dir, folder_name)
        else:
            csv_output_dir = csv_parent_dir

        # Log parameters for user
        feedback.pushInfo(f'Database: {db_path}')
        feedback.pushInfo(f'Output CSV folder: {csv_output_dir}')
        feedback.pushInfo(f'Append mode: {append_mode}')

        # ---- Step 3: Discover Tables ---- #
        # Query all tables from database, filter out metadata tables
        table_names = _list_db_tables(db_path)
        # Check database is valid
        if not table_names:
            raise QgsProcessingException(
                'Could not read any tables from the database. '
                'Ensure the file is a valid GeoPackage or SpatiaLite.'
            )

        # Filter out internal metadata tables (don't export these)
        skip_prefixes = ('gpkg_', 'sqlite_', 'rtree_', 'spatial_ref_sys',
                         'geometry_columns', 'views_geometry_columns',
                         'virts_geometry_columns', 'ElementaryGeometries')
        tables_to_export = [
            t for t in table_names
            if not any(t.lower().startswith(p.lower()) for p in skip_prefixes)
        ]

        feedback.pushInfo(
            f'Found {len(tables_to_export)} table(s) to export: '
            + ', '.join(tables_to_export)
        )

        # ---- Step 4: Initialize Exporter ---- #
        # CSVExporter handles deduplication and append logic
        exporter = CSVExporter(csv_output_dir, append_mode=append_mode)
        db_name = os.path.basename(db_path)
        
        # ---- Step 5: Determine Folder Name for Lineage ---- #
        # Use provided folder_name, or fall back to output directory basename
        if folder_name:
            csv_folder_name = folder_name
        else:
            csv_folder_name = os.path.basename(csv_output_dir)
        
        feedback.pushInfo(f'CSV export folder name for traceability: {csv_folder_name}')
        feedback.pushInfo('Source files will be appended with CSV folder name for full lineage tracking.')

        # ---- Step 6: Export Each Table ---- #
        exported = 0
        for table in tables_to_export:
            # Allow user to cancel mid-processing
            if feedback.isCanceled():
                feedback.pushInfo('Export cancelled by user.')
                break

            # Load table as QgsVectorLayer
            layer = QgsVectorLayer(
                f'{db_path}|layername={table}', table, 'ogr'
            )
            if not layer.isValid():
                feedback.reportError(f"Could not load table '{table}' — skipping.")
                continue

            try:
                # Convert layer to DataFrame (drop geometry)
                df = _layer_to_dataframe(layer)
                
                # Append csv_folder_name to source_file for full lineage
                df = _ensure_provenance_columns(
                    df,
                    csv_folder_name=csv_folder_name,
                )
                
                # Extract representative source_file for deduplication key
                # (CSVExporter uses first 3 pipe-parts for dedup)
                batch_source_file = ''
                if 'source_file' in df.columns:
                    sources = df['source_file'].fillna('').astype(str).str.strip()
                    sources = sources[sources != '']
                    if len(sources) > 0:
                        batch_source_file = sources.iloc[0]
                
                # Fallback: use database name + folder for tables without source_file
                if not batch_source_file:
                    batch_source_file = f"{db_name}|{csv_folder_name}"
                
                # Write table to CSV with dedup/append logic
                exporter.write(table, df, source_file=batch_source_file)
                feedback.pushInfo(f"  Wrote {table}.csv  ({len(df)} rows)")
                exported += 1
            except Exception as exc:
                feedback.reportError(f"Error exporting '{table}': {exc}")

        # ---- Step 7: Write Manifest ---- #
        exporter.write_manifest()
        feedback.pushInfo(
            f'CSV export complete — {exported}/{len(tables_to_export)} tables written. '
            f'manifest.csv updated.'
        )

        return {}

    # ================================================================ #
    # QGIS Algorithm Metadata                                            #
    # ================================================================ #
    
    def name(self):
        """Internal algorithm identifier (used in scripts/API)."""
        return 'DB2CSV'

    def displayName(self):
        """User-facing algorithm name in QGIS Processing toolbox."""
        return self.tr('DB2CSV')

    def group(self):
        """User-facing group name in Processing toolbox."""
        return self.tr(self.groupId())

    def groupId(self):
        """Internal group identifier."""
        return ''

    def tr(self, string):
        """Translate string for QGIS UI."""
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        """Create a new instance of this algorithm."""
        return DB2CSVAlgorithm()
