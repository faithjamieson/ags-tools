# -*- coding: utf-8 -*-

"""
AGS to CSV Export Algorithm

QGIS Processing algorithm that reads a single AGS4 file and exports all supported
AGS groups as CSV tables into a named folder. Supports append mode for multi-file
export, and full data lineage tracing via the 'source_file' column.

Workflow:
  1. Load .ags file using python-ags4
  2. Extract PROJ_ID for data lineage tracking
  3. Build transformer with geometry lookups (LOCA_GL, intervals, etc.)
  4. For each supported AGS group:
     - Call transform_<group>() to produce output schema
     - Inject elevation calculations (ELEV_* columns)
     - Reindex to fixed column order
  5. Write group to CSV file with deduplication/append logic
  6. Write manifest.csv with row counts and timestamps

Data lineage: Each row contains source_file = ags_filename|csv_folder_name|project_id
Deduplication: Prefix-match on first 3 pipe parts prevents duplicates on re-export
"""

import os
from pathlib import Path

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFile,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterString,
)

if __package__:
    from .core.parser import AGSParser
    from .core.transformer import AGSTransformer
    from .core.exporter import CSVExporter
else:
    from core.parser import AGSParser
    from core.transformer import AGSTransformer
    from core.exporter import CSVExporter


class AGS2CSVAlgorithm(QgsProcessingAlgorithm):
    """
    QGIS Processing algorithm: Export AGS4 file to CSV tables.
    
    Parameters:
      INPUT: Path to .ags file
      OUTPUT_DIR: Parent directory for CSV output
      OUTPUT_FOLDER_NAME: Name of subfolder to create/append into
      ALLOW_APPEND: Toggle append vs. overwrite mode
    
    Processing Flow:
      1. Validate inputs (file exists, paths valid)
      2. Determine append_mode (prompt user if folder exists)
      3. Build AGSTransformer with lookups from LOCA/GEOL groups
      4. Loop through TABLES list, transform and write each
      5. Write manifest.csv with export metadata
    """
    
    # Parameter keys for QGIS Processing framework
    INPUT = "INPUT"
    OUTPUT_DIR = "OUTPUT_DIR"
    OUTPUT_FOLDER_NAME = "OUTPUT_FOLDER_NAME"
    ALLOW_APPEND = "ALLOW_APPEND"

    # List of AGS groups to export, in order
    # Each group will be transformed, column-filtered, and written to uppercase.csv
    TABLES = [
        "proj",
        "loca",
        "samp",
        "bkfl",
        "geol",
        "detl",
        "ispt",
        "core",
        "weth",
        "frac",
        "hdph",
        "wins",
        "wstg",
        "wstd",
        "mong",
        "mond",
        "dcpg",
        "dcpt",
        "dprg",
        "icbr",
        "ipid",
        "ivan",
        "chis",
        "ptim",
        "lpdn",
        "llpl",
        "grat",
        "grag",
        "mcvg",
        "lnmc",
        "mcvt",
        "cbrg",
        "cbrt",
        "cmpg",
        "cmpt",
        "cong",
        "cons",
        "shbg",
        "shbt",
        "trig",
        "trit",
        "gchm",
        "eres",
    ]

    # ================================================================ #
    # QGIS Algorithm Metadata                                            #
    # ================================================================ #
    
    def name(self):
        """Internal algorithm identifier (used in scripts/API)."""
        return "ags2csv"

    def displayName(self):
        """User-facing algorithm name in QGIS Processing toolbox."""
        return self.tr("AGS to CSV")

    def group(self):
        """User-facing group name in Processing toolbox."""
        return self.tr("AGS tools")

    def groupId(self):
        """Internal group identifier."""
        return "agstools"

    def shortHelpString(self):
        """Help text shown in Processing toolbox."""
        return self.tr(
            "Exports AGS4 file(s) to a folder of CSV tables, one per AGS group, "
            "plus manifest.csv. Supports appending multiple AGS files to the same folder. "
            "The 'source_file' column identifies which rows came from which AGS file."
        )

    def tr(self, text):
        """Translate string for QGIS UI."""
        return QCoreApplication.translate("Processing", text)

    def createInstance(self):
        """Create a new instance of this algorithm."""
        return AGS2CSVAlgorithm()

    # ================================================================ #
    # QGIS Algorithm Interface: Metadata and Parameter Definition       #
    # ================================================================ #
    
    def initAlgorithm(self, config=None):
        """Define algorithm parameters shown in QGIS Processing dialog."""
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT,
                self.tr("Input AGS file(s)"),
                behavior=QgsProcessingParameterFile.File,
                extension="ags",
            )
        )
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT_DIR,
                self.tr("Output parent folder"),
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.OUTPUT_FOLDER_NAME,
                self.tr("CSV folder name"),
                defaultValue="ags_csv_export",
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.ALLOW_APPEND,
                self.tr("Allow append to existing folder?"),
                defaultValue=False,
            )
        )

    # ================================================================ #
    # Main Processing Logic                                              #
    # ================================================================ #
    
    def processAlgorithm(self, parameters, context, feedback):
        """
        Main processing function: validate inputs → load AGS → transform → export CSVs.
        
        Flow:
          1. Extract and validate all parameters
          2. Resolve output directory
          3. Determine append mode (prompt user if needed)
          4. Load AGS file and extract PROJ_ID
          5. Build transformer with metadata lookups
          6. Transform each group and write to CSV
          7. Write manifest.csv
        """
        # ---- Step 1: Extract Parameters ---- #
        ags_filepath = self.parameterAsFile(parameters, self.INPUT, context)
        output_parent_dir = self.parameterAsString(parameters, self.OUTPUT_DIR, context)
        output_folder_name = self.parameterAsString(
            parameters, self.OUTPUT_FOLDER_NAME, context
        )
        allow_append = self.parameterAsBool(parameters, self.ALLOW_APPEND, context)

        # Validate inputs
        if not ags_filepath:
            raise QgsProcessingException(self.tr("Input AGS file is required."))
        if not output_parent_dir:
            raise QgsProcessingException(self.tr("Output parent folder is required."))
        if not output_folder_name or not output_folder_name.strip():
            raise QgsProcessingException(self.tr("CSV folder name is required."))

        # Build final output directory path
        output_dir = os.path.join(output_parent_dir, output_folder_name.strip())

        # Extract base filenames for traceability
        ags_filename = Path(ags_filepath).name
        csv_folder_name = output_folder_name.strip()
        
        # ---- Step 2: Determine Append Mode ---- #
        # If allow_append flag is set AND folder already has CSVs, prompt user
        append_mode = False
        if allow_append and os.path.exists(output_dir):
            csv_files = [f for f in os.listdir(output_dir) if f.endswith('.csv')]
            if csv_files:
                # Show user dialog: append or overwrite?
                msg_box = QMessageBox()
                msg_box.setWindowTitle(self.tr("Append to Existing CSVs?"))
                msg_box.setText(
                    self.tr(
                        "The output folder already contains CSV files.\n"
                        "Do you want to append the new AGS data to the existing CSVs?\n\n"
                        "Click 'Yes' to append, 'No' to overwrite."
                    )
                )
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg_box.setDefaultButton(QMessageBox.Yes)
                result = msg_box.exec_()
                append_mode = (result == QMessageBox.Yes)
                
                if append_mode:
                    feedback.pushInfo(self.tr("Appending to existing CSVs..."))
                else:
                    feedback.pushInfo(self.tr("Overwriting existing CSVs..."))

        # ---- Step 3: Load AGS File ---- #
        feedback.pushInfo(self.tr(f"Loading AGS file: {ags_filename}..."))
        parser = AGSParser(ags_filepath)
        parser.load()  # Populates parser.tables dict from AGS file

        # ---- Step 4: Extract Project ID ---- #
        # Read PROJ_ID from PROJ group for data lineage
        # Format: source_file = ags_filename|csv_folder_name|project_id
        proj_id = ''
        proj_df = parser.get_group("PROJ")
        if proj_df is not None and 'PROJ_ID' in proj_df.columns:
            proj_vals = proj_df['PROJ_ID'].dropna().astype(str).str.strip()
            proj_vals = proj_vals[proj_vals != '']
            if len(proj_vals) > 0:
                proj_id = proj_vals.iloc[0]

        source_file = f"{ags_filename}|{csv_folder_name}|{proj_id}" if proj_id else f"{ags_filename}|{csv_folder_name}"
        feedback.pushInfo(self.tr(f"Data lineage: {source_file}"))

        # ---- Step 5: Build Transformer & Exporter ---- #
        # Transformer reads lookups (LOCA, GEOL) and builds mappings
        # Exporter handles CSV write + deduplication logic
        feedback.pushInfo(self.tr("Transforming AGS groups..."))
        transformer = AGSTransformer(parser, source_file)
        exporter = CSVExporter(output_dir, append_mode=append_mode)

        # ---- Step 6: Transform & Export Each Table ---- #
        # Loop through all supported AGS groups, transform schema, write CSV
        for table in self.TABLES:
            if feedback.isCanceled():
                return {}

            # Get transformer method for this group
            method_name = f"transform_{table}"
            transform_method = getattr(transformer, method_name, None)
            if transform_method is None:
                raise QgsProcessingException(
                    self.tr(f"Missing transformer method: {method_name}")
                )

            # Transform group DataFrame (inject columns, reindex to schema)
            df = transform_method()
            
            # Write to CSV with dedup/append logic
            exporter.write(table, df, source_file)
            feedback.pushInfo(self.tr(f"Wrote {table}.csv ({len(df)} rows)"))

        # ---- Step 7: Write Manifest ---- #
        # Manifest tracks which tables were exported, row counts, timestamps
        exporter.write_manifest()
        feedback.pushInfo(self.tr("Wrote manifest.csv"))

        return {self.OUTPUT_DIR: output_dir}