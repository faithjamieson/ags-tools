# loading AGS file into memory as pandas DataFrames using python-ags4
# script defines a small AGSParser class that loads an AGS file into memory and makes its groups easy to access.
# once loaded it can then be transformed (in transformer.py) and exported as needed.

try:
    from python_ags4 import AGS4
except ModuleNotFoundError:
    try:
        from ags4 import AGS4
    except ModuleNotFoundError:
        AGS4 = None
from pathlib import Path


class AGSParser:
    # __init__ stores the input path, extracts the source filename, and prepares two dictionaries
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.filename = Path(filepath).name
        self.tables = {}
        self.headings = {}

    # load uses python-ags4 to read the AGS file and populate the tables and headings dictionaries. It returns True if successful.
    def load(self) -> bool:
        if AGS4 is None:
            raise ModuleNotFoundError(
                "Missing AGS parser dependency. Install 'python-ags4' in the QGIS Python environment."
            )
        tables, headings = AGS4.AGS4_to_dataframe(self.filepath)
        # python-ags4 returns dicts of {GROUP_NAME: DataFrame}
        self.tables = tables
        self.headings = headings
        return True

    # helper methods to access the loaded groups. get_group returns the DataFrame for a group or None if it doesn't exist, while has_group returns a boolean indicating whether the group is present.
    def get_group(self, group_name: str):
        """Returns DataFrame for group or None if not present."""
        return self.tables.get(group_name, None)

    def has_group(self, group_name: str) -> bool:
        return group_name in self.tables