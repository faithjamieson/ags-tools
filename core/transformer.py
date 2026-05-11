# Schema mapping for all AGS groups found in sample_file.ags.
# Each transform method reads the raw AGS group, passes all native columns through
# unchanged, and injects plugin-generated fields (source_file, samp_id, lat, lon).
# Column names in output CSVs match the AGS headings exactly (uppercase) so that
# Power BI relationships and column references never break across files.

import pandas as pd
from datetime import datetime
from .geo_utils import bng_to_wgs84
from ..expected_groups import EXPECTED_CSVS


class AGSTransformer:
    # Map table names to lists of depth columns that should get ELEV_* columns calculated
    # Multiple depth columns per table = multiple ELEV_* columns
    ELEVATION_DEPTH_COLUMNS = {
        "samp": ["SAMP_TOP", "SAMP_BASE", "SAMP_WDEP"],
        "spec": ["SPEC_DPTH", "SPEC_BASE"],
        "bkfl": ["BKFL_TOP", "BKFL_BASE"],
        "cdia": ["CDIA_DPTH"],
        "chis": ["CHIS_FROM", "CHIS_TO"],
        "core": ["CORE_TOP", "CORE_BASE"],
        "dcpg": ["DCPG_DPTH"],
        "detl": ["DETL_TOP", "DETL_BASE"],
        "disc": ["DISC_TOP", "DISC_BASE"],
        "dlog": ["DLOG_TOP", "DLOG_BASE"],
        "dobs": ["DOBS_TOP", "DOBS_BASE"],
        "dprb": ["DPRB_DPTH"],
        "dprg": ["DPRG_TIP"],
        "drem": ["DREM_TOP", "DREM_BASE"],
        "fghg": ["FGHG_TOP", "FGHG_BASE", "FGHG_HBAS", "FGHG_CAS", "FGHG_PRWL", "FGHG_AWL"],
        "flsh": ["FLSH_TOP", "FLSH_BASE"],
        "frac": ["FRAC_FROM", "FRAC_TO"],
        "geol": ["GEOL_TOP", "GEOL_BASE"],
        "hdia": ["HDIA_DPTH"],
        "hdph": ["HDPH_TOP", "HDPH_BASE"],
        "horn": ["HORN_TOP", "HORN_BASE"],
        "icbr": ["ICBR_DPTH"],
        "iden": ["IDEN_DPTH"],
        "ifid": ["IFID_DPTH"],
        "ipen": ["IPEN_DPTH"],
        "ipid": ["IPID_DPTH"],
        "iprg": ["IPRG_TOP", "IPRG_BASE", "IPRG_PRWL", "IPRG_SWAL", "IPRG_AWL"],
        "iprt": ["IPRT_DPTH"],
        "irdx": ["IRDX_DPTH"],
        "ires": ["IRES_DPTH", "IRES_BASE"],
        "isag": ["ISAG_DPTS", "ISAG_DPTE"],
        "isat": ["ISAT_DPTH"],
        "ispt": ["ISPT_TOP", "ISPT_CAS"],
        "ivan": ["IVAN_DPTH"],
        "loca": ["LOCA_FDEP"],
        "pltg": ["PLTG_DPTH"],
        "pmtg": ["PMTG_DPTH"],
        "ptim": ["PTIM_DPTH", "PTIM_CAS"],
        "pumt": ["PUMT_DPTH"],
        "scdg": ["SCDG_DPTH"],
        "scpp": ["SCPP_TOP", "SCPP_BASE"],
        "scpt": ["SCPT_DPTH"],
        "wadd": ["WADD_TOP", "WADD_BASE"],
        "weth": ["WETH_TOP", "WETH_BASE"],
        "wgpg": ["WGPG_STRT", "WGPG_STOP", "WGPG_BHD"],
        "wgpt": ["WGPT_DPTH"],
        "wstg": ["WSTG_DPTH", "WSTG_SEAL", "WSTG_CAS"],
        "wstd": ["WSTD_POST"],
        "wins": ["WINS_TOP"],
    }

    GEOLOGY_INTERVAL_DEPTH_COLUMNS = {
        "samp": "SAMP_TOP",
        "bkfl": "BKFL_TOP",
        "detl": "DETL_TOP",
        "weth": "WETH_TOP",
        "core": "CORE_TOP",
        "hdph": "HDPH_TOP",
        "wins": "WINS_TOP",
        "wstg": "WSTG_DPTH",
        "wstd": "WSTG_DPTH",
        "ispt": "ISPT_TOP",
        "dcpg": "DCPG_DPTH",
        "dcpt": "DCPG_DPTH",
        "icbr": "ICBR_DPTH",
        "ipid": "IPID_DPTH",
        "ivan": "IVAN_DPTH",
        "ptim": "PTIM_DPTH",
        "lpdn": "SAMP_TOP",
        "llpl": "SAMP_TOP",
        "grat": "SAMP_TOP",
        "grag": "SAMP_TOP",
        "mcvg": "SAMP_TOP",
        "lnmc": "SAMP_TOP",
        "mcvt": "SAMP_TOP",
        "cbrg": "SAMP_TOP",
        "cbrt": "SAMP_TOP",
        "cmpg": "SAMP_TOP",
        "cmpt": "SAMP_TOP",
        "cong": "SAMP_TOP",
        "cons": "SAMP_TOP",
        "shbg": "SAMP_TOP",
        "shbt": "SAMP_TOP",
        "trig": "SAMP_TOP",
        "trit": "SAMP_TOP",
        "gchm": "SAMP_TOP",
        "eres": "SAMP_TOP",
    }

    def __init__(self, parser, source_file: str, data_desc: str = ""):
        self.parser = parser
        self.source_file = source_file
        self.data_desc = data_desc
        self.exported_at = datetime.utcnow().isoformat()
        (
            self.loca_clst_lookup,
            self.loca_type_lookup,
            self.geol_leg_lookup,
            self.geol_geo2_lookup,
            self.geol_geol_lookup,
            self.loca_gl_lookup,
        ) = (
            self._build_filter_lookups()
        )
        self.geol_intervals_lookup = self._build_geol_intervals_lookup()

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _empty_df(self, table_name: str) -> pd.DataFrame:
        """Returns an empty DataFrame with the correct column schema."""
        out = pd.DataFrame(columns=EXPECTED_CSVS[table_name])
        out = self._inject_elevation(out, table_name)
        return self._inject_filter_columns(out, table_name)

    def _safe_float(self, val):
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def _safe_int(self, val):
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return None

    def _parse_date(self, val):
        """Parses AGS date / datetime strings to YYYY-MM-DD."""
        if not val or (isinstance(val, float)):
            return None
        s = str(val).strip()
        for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    def _make_samp_id(self, loca_id, samp_ref, samp_top):
        return f"{loca_id}_{samp_ref}_{samp_top}"

    def _build_lookup(self, group_name: str, value_col: str) -> dict:
        df = self.parser.get_group(group_name)
        if df is None or "LOCA_ID" not in df.columns or value_col not in df.columns:
            return {}
        lookup_df = (
            df[["LOCA_ID", value_col]]
            .dropna(subset=["LOCA_ID"])
            .drop_duplicates(subset=["LOCA_ID"])
        )
        lookup_df["LOCA_ID"] = lookup_df["LOCA_ID"].astype(str)
        return lookup_df.set_index("LOCA_ID")[value_col].to_dict()

    def _build_filter_lookups(self):
        return (
            self._build_lookup("LOCA", "LOCA_CLST"),
            self._build_lookup("LOCA", "LOCA_TYPE"),
            self._build_lookup("GEOL", "GEOL_LEG"),
            self._build_lookup("GEOL", "GEOL_GEO2"),
            self._build_lookup("GEOL", "GEOL_GEOL"),
            self._build_lookup("LOCA", "LOCA_GL"),
        )

    def _build_geol_intervals_lookup(self):
        df = self.parser.get_group("GEOL")
        if df is None:
            return {}
        required_cols = {"LOCA_ID", "GEOL_TOP", "GEOL_BASE"}
        if not required_cols.issubset(df.columns):
            return {}

        available_cols = [
            col for col in ["LOCA_ID", "GEOL_TOP", "GEOL_BASE", "GEOL_GEO2", "GEOL_LEG", "GEOL_GEOL"]
            if col in df.columns
        ]
        geol_df = df[available_cols].copy()
        geol_df["LOCA_ID"] = geol_df["LOCA_ID"].astype(str)
        geol_df["GEOL_TOP"] = geol_df["GEOL_TOP"].apply(self._safe_float)
        geol_df["GEOL_BASE"] = geol_df["GEOL_BASE"].apply(self._safe_float)
        geol_df = geol_df.dropna(subset=["LOCA_ID", "GEOL_TOP", "GEOL_BASE"])

        intervals = {}
        for _, row in geol_df.iterrows():
            loca_id = row["LOCA_ID"]
            intervals.setdefault(loca_id, []).append(
                {
                    "GEOL_TOP": row["GEOL_TOP"],
                    "GEOL_BASE": row["GEOL_BASE"],
                    "GEOL_GEO2": row.get("GEOL_GEO2"),
                    "GEOL_LEG": row.get("GEOL_LEG"),
                    "GEOL_GEOL": row.get("GEOL_GEOL"),
                }
            )

        for loca_id in intervals:
            intervals[loca_id].sort(key=lambda item: (item["GEOL_TOP"], item["GEOL_BASE"]))
        return intervals

    def _map_geol_value_by_interval(self, out: pd.DataFrame, table_name: str, value_column: str):
        depth_col = self.GEOLOGY_INTERVAL_DEPTH_COLUMNS.get(table_name)
        if depth_col is None or depth_col not in out.columns:
            return None
        if "LOCA_ID" not in out.columns or not self.geol_intervals_lookup:
            return None

        loca_ids = out["LOCA_ID"].where(out["LOCA_ID"].notna(), "").astype(str)
        depths = out[depth_col].apply(self._safe_float)
        values = []

        for loca_id, depth in zip(loca_ids, depths):
            matched_value = None
            if depth is not None:
                for interval in self.geol_intervals_lookup.get(loca_id, []):
                    geol_top = interval.get("GEOL_TOP")
                    geol_base = interval.get("GEOL_BASE")
                    if geol_top is None or geol_base is None:
                        continue
                    if geol_top <= depth < geol_base:
                        matched_value = interval.get(value_column)
                        break
            values.append(matched_value)

        return pd.Series(values, index=out.index)

    def _inject_elevation(self, out: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """
        Calculate and inject ELEV_* columns for all depth columns in this table.
        Formula: ELEV_<depth_col> = LOCA_GL - <depth_col>
        
        Creates one ELEV_* column for each depth column found in the table.
        """
        depth_cols = self.ELEVATION_DEPTH_COLUMNS.get(table_name, [])
        if not depth_cols:
            return out
        
        if "LOCA_ID" not in out.columns:
            return out
        
        loca_ids = out["LOCA_ID"].where(out["LOCA_ID"].notna(), "").astype(str)
        loca_gl = loca_ids.map(self.loca_gl_lookup).apply(self._safe_float)
        
        # For each depth column in this table, create an ELEV_* column
        for depth_col in depth_cols:
            elev_col_name = f"ELEV_{depth_col}"
            
            # Only calculate if the depth column exists in the dataframe
            if depth_col in out.columns:
                depth = out[depth_col].apply(self._safe_float)
                out[elev_col_name] = [
                    (gl - d) if (gl is not None and d is not None) else None
                    for gl, d in zip(loca_gl, depth)
                ]
        
        return out

    def _inject_filter_columns(self, out: pd.DataFrame, table_name: str = None) -> pd.DataFrame:
        if "LOCA_ID" in out.columns:
            loca_ids = out["LOCA_ID"].where(out["LOCA_ID"].notna(), "").astype(str)
            mapped_loca_clst = loca_ids.map(self.loca_clst_lookup)
            mapped_loca_type = loca_ids.map(self.loca_type_lookup)
            mapped_geol_leg = self._map_geol_value_by_interval(out, table_name, "GEOL_LEG")
            if mapped_geol_leg is None:
                mapped_geol_leg = loca_ids.map(self.geol_leg_lookup)
            mapped_geol_geo2 = self._map_geol_value_by_interval(out, table_name, "GEOL_GEO2")
            if mapped_geol_geo2 is None:
                mapped_geol_geo2 = loca_ids.map(self.geol_geo2_lookup)
            mapped_geol_geol = self._map_geol_value_by_interval(out, table_name, "GEOL_GEOL")
            if mapped_geol_geol is None:
                mapped_geol_geol = loca_ids.map(self.geol_geol_lookup)
        else:
            mapped_loca_clst = None
            mapped_loca_type = None
            mapped_geol_leg = None
            mapped_geol_geo2 = None
            mapped_geol_geol = None

        if "LOCA_CLST" in out.columns:
            if mapped_loca_clst is not None:
                out["LOCA_CLST"] = out["LOCA_CLST"].where(
                    out["LOCA_CLST"].notna(), mapped_loca_clst
                )
        else:
            out["LOCA_CLST"] = mapped_loca_clst

        if "LOCA_TYPE" in out.columns:
            if mapped_loca_type is not None:
                out["LOCA_TYPE"] = out["LOCA_TYPE"].where(
                    out["LOCA_TYPE"].notna(), mapped_loca_type
                )
        else:
            out["LOCA_TYPE"] = mapped_loca_type

        if "GEOL_LEG" in out.columns:
            if mapped_geol_leg is not None:
                out["GEOL_LEG"] = out["GEOL_LEG"].where(
                    out["GEOL_LEG"].notna(), mapped_geol_leg
                )
        else:
            out["GEOL_LEG"] = mapped_geol_leg

        if "GEOL_GEO2" in out.columns:
            if mapped_geol_geo2 is not None:
                out["GEOL_GEO2"] = out["GEOL_GEO2"].where(
                    out["GEOL_GEO2"].notna(), mapped_geol_geo2
                )
        else:
            out["GEOL_GEO2"] = mapped_geol_geo2

        if "GEOL_GEOL" in out.columns:
            if mapped_geol_geol is not None:
                out["GEOL_GEOL"] = out["GEOL_GEOL"].where(
                    out["GEOL_GEOL"].notna(), mapped_geol_geol
                )
        else:
            out["GEOL_GEOL"] = mapped_geol_geol

        return out

    def _pass_through(self, df: pd.DataFrame, table_name: str,
                      extra_cols: dict = None) -> pd.DataFrame:
        """
        Generic pass-through: takes all columns from the raw AGS DataFrame,
        drops FILE_FSET, injects source_file (and any extra_cols), then
        reindexes to the schema in EXPECTED_CSVS so column order is fixed
        and any missing columns are filled with None.
        """
        out = df.copy()
        out.drop(columns=[c for c in ["FILE_FSET"] if c in out.columns], inplace=True)
        out.insert(0, "source_file", self.source_file)
        if extra_cols:
            for col, values in extra_cols.items():
                out.insert(0, col, values)
        # Reindex to schema — missing columns become NaN, extra columns dropped
        out = out.reindex(columns=EXPECTED_CSVS[table_name])
        out = self._inject_elevation(out, table_name)
        return self._inject_filter_columns(out, table_name)

    def _samp_id_series(self, df: pd.DataFrame) -> pd.Series:
        """Builds the composite samp_id for sample-linked tables."""
        return (
            df.get("LOCA_ID", pd.Series([""] * len(df))).astype(str)
            + "_"
            + df.get("SAMP_REF", pd.Series([""] * len(df))).astype(str)
            + "_"
            + df.get("SAMP_TOP", pd.Series([""] * len(df))).astype(str)
        )

    def transform_proj(self) -> pd.DataFrame:
        df = self.parser.get_group("PROJ")
        if df is None:
            return pd.DataFrame(columns=EXPECTED_CSVS["proj"])

        out = df.copy()
        out.drop(columns=[c for c in ["FILE_FSET"] if c in out.columns], inplace=True)
        out.insert(0, "source_file", self.source_file)
        out.insert(1, "data_desc", self.data_desc)
        return out.reindex(columns=EXPECTED_CSVS["proj"])

    # ------------------------------------------------------------------ #
    # Location spine                                                       #
    # ------------------------------------------------------------------ #

    def transform_loca(self) -> pd.DataFrame:
        df = self.parser.get_group("LOCA")
        if df is None:
            return self._empty_df("loca")

        out = df.copy()
        out.drop(columns=[c for c in ["FILE_FSET"] if c in out.columns], inplace=True)

        # Derive WGS84 lat/lon from BNG eastings/northings
        lats, lons = [], []
        for _, r in out.iterrows():
            e = self._safe_float(r.get("LOCA_NATE"))
            n = self._safe_float(r.get("LOCA_NATN"))
            lat, lon = bng_to_wgs84(e, n) if (e and n) else (None, None)
            lats.append(lat)
            lons.append(lon)

        out.insert(0, "source_file", self.source_file)
        out["lat"] = lats
        out["lon"] = lons

        out = out.reindex(columns=EXPECTED_CSVS["loca"])
        return self._inject_filter_columns(out, "loca")

    # ------------------------------------------------------------------ #
    # Samples                                                              #
    # ------------------------------------------------------------------ #

    def transform_samp(self) -> pd.DataFrame:
        df = self.parser.get_group("SAMP")
        if df is None:
            return self._empty_df("samp")

        return self._pass_through(
            df, "samp",
            extra_cols={"samp_id": self._samp_id_series(df)},
        )

    # ------------------------------------------------------------------ #
    # Geology / field description                                          #
    # ------------------------------------------------------------------ #

    def transform_geol(self) -> pd.DataFrame:
        df = self.parser.get_group("GEOL")
        if df is None:
            return self._empty_df("geol")
        return self._pass_through(df, "geol")

    def transform_bkfl(self) -> pd.DataFrame:
        df = self.parser.get_group("BKFL")
        if df is None:
            return self._empty_df("bkfl")
        return self._pass_through(df, "bkfl")

    def transform_detl(self) -> pd.DataFrame:
        df = self.parser.get_group("DETL")
        if df is None:
            return self._empty_df("detl")
        return self._pass_through(df, "detl")

    def transform_weth(self) -> pd.DataFrame:
        df = self.parser.get_group("WETH")
        if df is None:
            return self._empty_df("weth")
        return self._pass_through(df, "weth")

    def transform_core(self) -> pd.DataFrame:
        df = self.parser.get_group("CORE")
        if df is None:
            return self._empty_df("core")
        return self._pass_through(df, "core")

    def transform_frac(self) -> pd.DataFrame:
        df = self.parser.get_group("FRAC")
        if df is None:
            return self._empty_df("frac")
        return self._pass_through(df, "frac")

    def transform_hdph(self) -> pd.DataFrame:
        df = self.parser.get_group("HDPH")
        if df is None:
            return self._empty_df("hdph")
        return self._pass_through(df, "hdph")

    def transform_wins(self) -> pd.DataFrame:
        df = self.parser.get_group("WINS")
        if df is None:
            return self._empty_df("wins")
        return self._pass_through(df, "wins")

    def transform_wstg(self) -> pd.DataFrame:
        df = self.parser.get_group("WSTG")
        if df is None:
            return self._empty_df("wstg")
        return self._pass_through(df, "wstg")

    def transform_wstd(self) -> pd.DataFrame:
        df = self.parser.get_group("WSTD")
        if df is None:
            return self._empty_df("wstd")
        return self._pass_through(df, "wstd")

    def transform_mong(self) -> pd.DataFrame:
        df = self.parser.get_group("MONG")
        if df is None:
            return self._empty_df("mong")
        return self._pass_through(df, "mong")

    def transform_mond(self) -> pd.DataFrame:
        df = self.parser.get_group("MOND")
        if df is None:
            return self._empty_df("mond")
        return self._pass_through(df, "mond")

    # ------------------------------------------------------------------ #
    # In-situ tests                                                        #
    # ------------------------------------------------------------------ #

    def transform_ispt(self) -> pd.DataFrame:
        df = self.parser.get_group("ISPT")
        if df is None:
            return self._empty_df("ispt")
        return self._pass_through(df, "ispt")

    def transform_dcpg(self) -> pd.DataFrame:
        df = self.parser.get_group("DCPG")
        if df is None:
            return self._empty_df("dcpg")
        return self._pass_through(df, "dcpg")

    def transform_dcpt(self) -> pd.DataFrame:
        df = self.parser.get_group("DCPT")
        if df is None:
            return self._empty_df("dcpt")
        return self._pass_through(df, "dcpt")

    def transform_dprg(self) -> pd.DataFrame:
        df = self.parser.get_group("DPRG")
        if df is None:
            return self._empty_df("dprg")
        return self._pass_through(df, "dprg")

    def transform_icbr(self) -> pd.DataFrame:
        df = self.parser.get_group("ICBR")
        if df is None:
            return self._empty_df("icbr")
        return self._pass_through(df, "icbr")

    def transform_ipid(self) -> pd.DataFrame:
        df = self.parser.get_group("IPID")
        if df is None:
            return self._empty_df("ipid")
        return self._pass_through(df, "ipid")

    def transform_ivan(self) -> pd.DataFrame:
        df = self.parser.get_group("IVAN")
        if df is None:
            return self._empty_df("ivan")
        return self._pass_through(df, "ivan")

    def transform_chis(self) -> pd.DataFrame:
        df = self.parser.get_group("CHIS")
        if df is None:
            return self._empty_df("chis")
        return self._pass_through(df, "chis")

    def transform_ptim(self) -> pd.DataFrame:
        df = self.parser.get_group("PTIM")
        if df is None:
            return self._empty_df("ptim")
        return self._pass_through(df, "ptim")

    def transform_lpdn(self) -> pd.DataFrame:
        df = self.parser.get_group("LPDN")
        if df is None:
            return self._empty_df("lpdn")
        return self._pass_through(
            df, "lpdn",
            extra_cols={"samp_id": self._samp_id_series(df)},
        )

    # ------------------------------------------------------------------ #
    # Lab tests — sample-linked (all get samp_id injected)               #
    # ------------------------------------------------------------------ #

    def transform_llpl(self) -> pd.DataFrame:
        df = self.parser.get_group("LLPL")
        if df is None:
            return self._empty_df("llpl")
        return self._pass_through(
            df, "llpl",
            extra_cols={"samp_id": self._samp_id_series(df)},
        )

    def transform_grat(self) -> pd.DataFrame:
        df = self.parser.get_group("GRAT")
        if df is None:
            return self._empty_df("grat")
        return self._pass_through(
            df, "grat",
            extra_cols={"samp_id": self._samp_id_series(df)},
        )

    def transform_grag(self) -> pd.DataFrame:
        df = self.parser.get_group("GRAG")
        if df is None:
            return self._empty_df("grag")
        return self._pass_through(
            df, "grag",
            extra_cols={"samp_id": self._samp_id_series(df)},
        )

    def transform_mcvg(self) -> pd.DataFrame:
        df = self.parser.get_group("MCVG")
        if df is None:
            return self._empty_df("mcvg")
        return self._pass_through(
            df, "mcvg",
            extra_cols={"samp_id": self._samp_id_series(df)},
        )

    def transform_lnmc(self) -> pd.DataFrame:
        df = self.parser.get_group("LNMC")
        if df is None:
            return self._empty_df("lnmc")
        return self._pass_through(
            df, "lnmc",
            extra_cols={"samp_id": self._samp_id_series(df)},
        )

    def transform_mcvt(self) -> pd.DataFrame:
        df = self.parser.get_group("MCVT")
        if df is None:
            return self._empty_df("mcvt")
        return self._pass_through(
            df, "mcvt",
            extra_cols={"samp_id": self._samp_id_series(df)},
        )

    def transform_cbrg(self) -> pd.DataFrame:
        df = self.parser.get_group("CBRG")
        if df is None:
            return self._empty_df("cbrg")
        return self._pass_through(
            df, "cbrg",
            extra_cols={"samp_id": self._samp_id_series(df)},
        )

    def transform_cbrt(self) -> pd.DataFrame:
        df = self.parser.get_group("CBRT")
        if df is None:
            return self._empty_df("cbrt")
        return self._pass_through(
            df, "cbrt",
            extra_cols={"samp_id": self._samp_id_series(df)},
        )

    def transform_cmpg(self) -> pd.DataFrame:
        df = self.parser.get_group("CMPG")
        if df is None:
            return self._empty_df("cmpg")
        return self._pass_through(
            df, "cmpg",
            extra_cols={"samp_id": self._samp_id_series(df)},
        )

    def transform_cmpt(self) -> pd.DataFrame:
        df = self.parser.get_group("CMPT")
        if df is None:
            return self._empty_df("cmpt")
        return self._pass_through(
            df, "cmpt",
            extra_cols={"samp_id": self._samp_id_series(df)},
        )

    def transform_cong(self) -> pd.DataFrame:
        df = self.parser.get_group("CONG")
        if df is None:
            return self._empty_df("cong")
        return self._pass_through(
            df, "cong",
            extra_cols={"samp_id": self._samp_id_series(df)},
        )

    def transform_cons(self) -> pd.DataFrame:
        df = self.parser.get_group("CONS")
        if df is None:
            return self._empty_df("cons")
        return self._pass_through(
            df, "cons",
            extra_cols={"samp_id": self._samp_id_series(df)},
        )

    def transform_shbg(self) -> pd.DataFrame:
        df = self.parser.get_group("SHBG")
        if df is None:
            return self._empty_df("shbg")
        return self._pass_through(
            df, "shbg",
            extra_cols={"samp_id": self._samp_id_series(df)},
        )

    def transform_shbt(self) -> pd.DataFrame:
        df = self.parser.get_group("SHBT")
        if df is None:
            return self._empty_df("shbt")
        return self._pass_through(
            df, "shbt",
            extra_cols={"samp_id": self._samp_id_series(df)},
        )

    def transform_trig(self) -> pd.DataFrame:
        df = self.parser.get_group("TRIG")
        if df is None:
            return self._empty_df("trig")
        return self._pass_through(
            df, "trig",
            extra_cols={"samp_id": self._samp_id_series(df)},
        )

    def transform_trit(self) -> pd.DataFrame:
        df = self.parser.get_group("TRIT")
        if df is None:
            return self._empty_df("trit")
        return self._pass_through(
            df, "trit",
            extra_cols={"samp_id": self._samp_id_series(df)},
        )

    def transform_gchm(self) -> pd.DataFrame:
        df = self.parser.get_group("GCHM")
        if df is None:
            return self._empty_df("gchm")
        return self._pass_through(
            df, "gchm",
            extra_cols={"samp_id": self._samp_id_series(df)},
        )

    def transform_eres(self) -> pd.DataFrame:
        df = self.parser.get_group("ERES")
        if df is None:
            return self._empty_df("eres")
        return self._pass_through(
            df, "eres",
            extra_cols={"samp_id": self._samp_id_series(df)},
        )