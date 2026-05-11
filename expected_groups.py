# Exact headings from sample_file.ags for each group, plus source_file injected by the plugin.
# FILE_FSET is excluded as it is an AGS internal reference not needed in output CSVs.
# Groups not present in sample_file.ags (SCPT/TREG) are retained as stubs for forward compatibility.

COMMON_FILTER_COLUMNS = ["LOCA_CLST", "LOCA_TYPE", "GEOL_LEG", "GEOL_GEO2", "GEOL_GEOL"]

EXPECTED_CSVS = {

    # ------------------------------------------------------------------ #
    # Meta / manifest (plugin-generated, not from AGS groups)             #
    # ------------------------------------------------------------------ #

    "meta": [
        "source_file", "PROJ_ID", "PROJ_NAME", "PROJ_LOC", "PROJ_CLNT",
        "PROJ_CONT", "PROJ_ENG", "PROJ_MEMO",
        "exported_at", "exported_by",
    ],

    "proj": [
        "source_file", "data_desc", "PROJ_ID", "PROJ_NAME", "PROJ_LOC", "PROJ_CLNT",
        "PROJ_CONT", "PROJ_ENG", "PROJ_MEMO",
    ],

    "manifest": [
        "source_file", "csv_name", "ags_group", "row_count", "has_data", "exported_at",
    ],

    # ------------------------------------------------------------------ #
    # Location spine                                                       #
    # ------------------------------------------------------------------ #

    "loca": [
        "source_file",
        "LOCA_ID", "LOCA_TYPE", "LOCA_STAT", "LOCA_NATE", "LOCA_NATN",
        "LOCA_GREF", "LOCA_GL", "LOCA_REM", "LOCA_FDEP", "ELEV_LOCA_FDEP", "LOCA_STAR",
        "LOCA_PURP", "LOCA_TERM", "LOCA_ENDD", "LOCA_LETT", "LOCA_LOCX",
        "LOCA_LOCY", "LOCA_LOCZ", "LOCA_LREF", "LOCA_DATM", "LOCA_ETRV",
        "LOCA_NTRV", "LOCA_LTRV", "LOCA_XTRL", "LOCA_YTRL", "LOCA_ZTRL",
        "LOCA_LAT", "LOCA_LON", "LOCA_ELAT", "LOCA_ELON", "LOCA_LLZ",
        "LOCA_LOCM", "LOCA_LOCA", "LOCA_CLST", "LOCA_ALID", "LOCA_OFFS",
        "LOCA_CNGE", "LOCA_TRAN",
        "lat", "lon",  # derived WGS84 columns added by plugin
    ],

    # ------------------------------------------------------------------ #
    # Samples                                                              #
    # ------------------------------------------------------------------ #

    "samp": [
        "samp_id",  # derived composite key
        "source_file",
        "LOCA_ID", "SAMP_TOP", "ELEV_SAMP_TOP", "SAMP_REF", "SAMP_TYPE", "SAMP_ID",
        "SAMP_BASE", "ELEV_SAMP_BASE", "SAMP_DTIM", "SAMP_UBLO", "SAMP_CONT", "SAMP_PREP",
        "SAMP_SDIA", "SAMP_WDEP", "ELEV_SAMP_WDEP", "SAMP_RECV", "SAMP_TECH", "SAMP_MATX",
        "SAMP_TYPC", "SAMP_WHO", "SAMP_WHY", "SAMP_REM", "SAMP_DESC",
        "SAMP_DESD", "SAMP_LOG", "SAMP_COND", "SAMP_CLSS", "SAMP_BAR",
        "SAMP_TEMP", "SAMP_PRES", "SAMP_FLOW", "SAMP_ETIM", "SAMP_DURN",
        "SAMP_CAPT", "SAMP_LINK", "GEOL_STAT",
    ],

    # ------------------------------------------------------------------ #
    # Field / in-situ                                                      #
    # ------------------------------------------------------------------ #

    "geol": [
        "source_file",
        "LOCA_ID", "GEOL_TOP", "ELEV_GEOL_TOP", "GEOL_BASE", "ELEV_GEOL_BASE", "GEOL_DESC", "GEOL_LEG",
        "GEOL_GEOL", "GEOL_GEO2", "GEOL_STAT", "GEOL_BGS", "GEOL_FORM",
        "GEOL_REM",
    ],

    "ispt": [
        "source_file",
        "LOCA_ID", "ISPT_TOP", "ELEV_ISPT_TOP", "ISPT_SEAT", "ISPT_MAIN", "ISPT_NPEN",
        "ISPT_NVAL", "ISPT_REP", "ISPT_CAS", "ELEV_ISPT_CAS", "ISPT_WAT", "ISPT_TYPE",
        "ISPT_HAM", "ISPT_ERAT", "ISPT_SWP",
        "ISPT_INC1", "ISPT_INC2", "ISPT_INC3", "ISPT_INC4", "ISPT_INC5", "ISPT_INC6",
        "ISPT_PEN1", "ISPT_PEN2", "ISPT_PEN3", "ISPT_PEN4", "ISPT_PEN5", "ISPT_PEN6",
        "ISPT_ROCK", "ISPT_REM", "ISPT_ENV", "ISPT_METH", "ISPT_CRED", "TEST_STAT",
    ],

    "dcpg": [
        "source_file",
        "LOCA_ID", "DCPG_DATE", "DCPG_TESN", "DCPG_DPTH", "ELEV_DCPG_DPTH", "DCPG_ZERO",
        "DCPG_LREM", "DCPG_REM", "DCPG_ENV", "DCPG_METH", "DCPG_CONT",
        "DCPG_CRED", "TEST_STAT",
    ],

    "dcpt": [
        "source_file",
        "LOCA_ID", "DCPG_DATE", "DCPG_TESN", "DCPG_DPTH",
        "DCPT_CBLO", "DCPT_PEN", "DCPT_DEL", "DCPT_REM",
    ],

    "dprg": [
        "source_file",
        "LOCA_ID", "DPRG_TESN", "DPRG_DATE", "DPRG_TYPE", "DPRG_METH",
        "DPRG_MASS", "DPRG_DROP", "DPRG_CONE", "DPRG_ROD", "DPRG_TANV",
        "DPRG_DAMP", "DPRG_TIP", "ELEV_DPRG_TIP", "DPRG_REM", "DPRG_ANG", "DPRG_RMSS",
        "DPRG_PARF", "DPRG_PDIU", "DPRG_BCF", "DPRG_GW", "DPRG_REET",
        "DPRG_ENV", "DPRG_CONT", "DPRG_CRED", "TEST_STAT",
    ],

    "icbr": [
        "source_file",
        "LOCA_ID", "ICBR_DPTH", "ELEV_ICBR_DPTH", "ICBR_TESN", "ICBR_ICBR", "ICBR_MC",
        "ICBR_DATE", "ICBR_KENT", "ICBR_SEAT", "ICBR_SURC", "ICBR_TYPE",
        "ICBR_REM", "ICBR_ENV", "ICBR_METH", "ICBR_CONT", "ICBR_CRED",
        "TEST_STAT", "GEOL_STAT",
    ],

    "ipid": [
        "source_file",
        "LOCA_ID", "IPID_DPTH", "ELEV_IPID_DPTH", "IPID_TESN", "IPID_DATE", "IPID_TEMP",
        "IPID_RES", "IPID_REM", "IPID_ENV", "IPID_METH", "IPID_CONT",
        "IPID_CRED", "TEST_STAT", "GEOL_STAT",
    ],

    "ivan": [
        "source_file",
        "LOCA_ID", "IVAN_DPTH", "ELEV_IVAN_DPTH", "IVAN_TESN", "IVAN_TYPE", "IVAN_IVAN",
        "IVAN_IVAR", "IVAN_DATE", "IVAN_REM", "IVAN_ENV", "IVAN_METH",
        "IVAN_CONT", "IVAN_CRED", "TEST_STAT", "GEOL_STAT",
    ],

    "chis": [
        "source_file",
        "LOCA_ID", "CHIS_FROM", "ELEV_CHIS_FROM", "CHIS_TO", "ELEV_CHIS_TO", "CHIS_TIME", "CHIS_STAR",
        "CHIS_TOOL", "CHIS_REM",
    ],

    "ptim": [
        "source_file",
        "LOCA_ID", "PTIM_DTIM", "PTIM_DPTH", "ELEV_PTIM_DPTH", "PTIM_CAS", "ELEV_PTIM_CAS", "PTIM_WAT", "PTIM_REM",
    ],

    "core": [
        "source_file",
        "LOCA_ID", "CORE_TOP", "ELEV_CORE_TOP", "CORE_BASE", "ELEV_CORE_BASE", "CORE_PREC", "CORE_SREC",
        "CORE_RQD", "CORE_DIAM", "CORE_DURN", "CORE_REM",
    ],

    "frac": [
        "source_file",
        "LOCA_ID", "FRAC_FROM", "ELEV_FRAC_FROM", "FRAC_TO", "ELEV_FRAC_TO", "FRAC_SET", "FRAC_IMAX",
        "FRAC_IAVE", "FRAC_IMIN", "FRAC_FI", "FRAC_REM",
    ],

    "weth": [
        "source_file",
        "LOCA_ID", "WETH_TOP", "ELEV_WETH_TOP", "WETH_BASE", "ELEV_WETH_BASE", "WETH_SCH", "WETH_SYS",
        "WETH_WETH", "WETH_REM",
    ],

    "wins": [
        "source_file",
        "LOCA_ID", "WINS_TESN", "WINS_TOP", "ELEV_WINS_TOP", "WINS_BASE", "WINS_DIAM",
        "WINS_DURN", "WINS_REC", "WINS_REM",
    ],

    "hdph": [
        "source_file",
        "LOCA_ID", "HDPH_TOP", "ELEV_HDPH_TOP", "HDPH_BASE", "ELEV_HDPH_BASE", "HDPH_TYPE", "HDPH_STAR",
        "HDPH_ENDD", "HDPH_CREW", "HDPH_EXC", "HDPH_SHOR", "HDPH_STAB",
        "HDPH_DIML", "HDPH_DIMW", "HDPH_DBIT", "HDPH_BCON", "HDPH_BTYP",
        "HDPH_BLEN", "HDPH_LOG", "HDPH_LOGD", "HDPH_REM", "HDPH_ENV",
        "HDPH_METH", "HDPH_CONT",
    ],

    "bkfl": [
        "source_file",
        "LOCA_ID", "BKFL_TOP", "ELEV_BKFL_TOP", "BKFL_BASE", "ELEV_BKFL_BASE", "BKFL_DESC", "BKFL_LEG",
        "BKFL_DATE", "BKFL_REM",
    ],

    "detl": [
        "source_file",
        "LOCA_ID", "DETL_TOP", "ELEV_DETL_TOP", "DETL_BASE", "ELEV_DETL_BASE", "DETL_DESC", "DETL_REM",
    ],

    "wstg": [
        "source_file",
        "LOCA_ID", "WSTG_DPTH", "ELEV_WSTG_DPTH", "WSTG_DTIM", "WSTG_SEAL", "ELEV_WSTG_SEAL", "WSTG_CAS", "ELEV_WSTG_CAS", "WSTG_REM",
    ],

    "wstd": [
        "source_file",
        "LOCA_ID", "WSTG_DPTH", "WSTD_NMIN", "WSTD_POST", "ELEV_WSTD_POST", "WSTD_REM",
    ],

    "mong": [
        "source_file",
        "LOCA_ID", "MONG_ID", "MONG_DIS", "PIPE_REF", "MONG_DATE",
        "MONG_TYPE", "MONG_DETL", "MONG_TRZ", "MONG_BRZ", "MONG_BRGA",
        "MONG_BRGB", "MONG_BRGC", "MONG_INCA", "MONG_INCB", "MONG_INCC",
        "MONG_RSCA", "MONG_RSCB", "MONG_RSCC", "MONG_REM", "MONG_CONT",
    ],

    "mond": [
        "source_file",
        "LOCA_ID", "MONG_ID", "MONG_DIS", "MOND_DTIM", "MOND_TYPE",
        "MOND_REF", "MOND_INST", "MOND_RDNG", "MOND_UNIT", "MOND_METH",
        "MOND_LIM", "MOND_ULIM", "MOND_NAME", "MOND_CRED", "MOND_CONT",
        "MOND_REM",
    ],

    # ------------------------------------------------------------------ #
    # Lab tests                                                            #
    # ------------------------------------------------------------------ #

    "llpl": [
        "samp_id",  # derived
        "source_file",
        "LOCA_ID", "SAMP_TOP", "ELEV_SAMP_TOP", "SAMP_REF", "SAMP_TYPE", "SAMP_ID",
        "SPEC_REF", "SPEC_DPTH", "ELEV_SPEC_DPTH", "SPEC_DESC", "SPEC_PREP",
        "LLPL_LL", "LLPL_PL", "LLPL_PI", "LLPL_425", "LLPL_PREP",
        "LLPL_STAB", "LLPL_STYP", "LLPL_REM", "LLPL_METH", "LLPL_LAB",
        "LLPL_CRED", "TEST_STAT",
    ],

    "grat": [
        "samp_id",  # derived
        "source_file",
        "LOCA_ID", "SAMP_TOP", "ELEV_SAMP_TOP", "SAMP_REF", "SAMP_TYPE", "SAMP_ID",
        "SPEC_REF", "SPEC_DPTH", "ELEV_SPEC_DPTH",
        "GRAT_SIZE", "GRAT_PERP", "GRAT_TYPE", "GRAT_REM",
    ],

    "grag": [
        "samp_id",  # derived
        "source_file",
        "LOCA_ID", "SAMP_TOP", "ELEV_SAMP_TOP", "SAMP_REF", "SAMP_TYPE", "SAMP_ID",
        "SPEC_REF", "SPEC_DPTH", "ELEV_SPEC_DPTH", "SPEC_DESC", "SPEC_PREP",
        "GRAG_UC", "GRAG_VCRE", "GRAG_GRAV", "GRAG_SAND", "GRAG_SILT",
        "GRAG_CLAY", "GRAG_FINE", "GRAG_REM", "GRAG_METH", "GRAG_LAB",
        "GRAG_CRED", "TEST_STAT",
    ],

    "mcvg": [
        "samp_id",  # derived
        "source_file",
        "LOCA_ID", "SAMP_TOP", "ELEV_SAMP_TOP", "SAMP_REF", "SAMP_TYPE", "SAMP_ID",
        "SPEC_REF", "SPEC_DPTH", "ELEV_SPEC_DPTH", "SPEC_DESC", "SPEC_PREP",
        "MCVG_200", "MCVG_NMC", "MCVG_STAB", "MCVG_STYP",
        "MCVG_REM", "MCVG_METH", "MCVG_LAB", "MCVG_CRED", "TEST_STAT",
    ],

    "lnmc": [
        "samp_id",  # derived
        "source_file",
        "LOCA_ID", "SAMP_TOP", "ELEV_SAMP_TOP", "SAMP_REF", "SAMP_TYPE", "SAMP_ID",
        "SPEC_REF", "SPEC_DPTH", "ELEV_SPEC_DPTH", "SPEC_DESC", "SPEC_PREP",
        "LNMC_MC", "LNMC_TEMP", "LNMC_STAB", "LNMC_STYP", "LNMC_ISNT",
        "LNMC_COMM", "LNMC_REM", "LNMC_METH", "LNMC_LAB", "LNMC_CRED",
        "TEST_STAT",
    ],

    "mcvt": [
        "samp_id",  # derived
        "source_file",
        "LOCA_ID", "SAMP_TOP", "ELEV_SAMP_TOP", "SAMP_REF", "SAMP_TYPE", "SAMP_ID",
        "SPEC_REF", "SPEC_DPTH", "ELEV_SPEC_DPTH",
        "MCVT_TESN", "MCVT_MC", "MCVT_CURV", "MCVT_RELK", "MCVT_BDEN",
        "MCVT_DIFF", "MCVT_RAPD", "MCVT_REM",
    ],

    "cbrg": [
        "samp_id",  # derived
        "source_file",
        "LOCA_ID", "SAMP_TOP", "ELEV_SAMP_TOP", "SAMP_REF", "SAMP_TYPE", "SAMP_ID",
        "SPEC_REF", "SPEC_DPTH", "ELEV_SPEC_DPTH", "SPEC_DESC", "SPEC_PREP",
        "CBRG_COND", "CBRG_NMC", "CBRG_200", "CBRG_STAB", "CBRG_STYP",
        "CBRG_REM", "CBRG_METH", "CBRG_LAB", "CBRG_CRED", "TEST_STAT",
    ],

    "cbrt": [
        "samp_id",  # derived
        "source_file",
        "LOCA_ID", "SAMP_TOP", "ELEV_SAMP_TOP", "SAMP_REF", "SAMP_TYPE", "SAMP_ID",
        "SPEC_REF", "SPEC_DPTH", "ELEV_SPEC_DPTH",
        "CBRT_TESN", "CBRT_TOP", "CBRT_BASE", "CBRT_MCT", "CBRT_MCBT",
        "CBRT_IMC", "CBRT_BDEN", "CBRT_DDEN", "CBRT_SURC", "CBRT_SKDT",
        "CBRT_SWEL", "CBRT_REM",
    ],

    "cmpg": [
        "samp_id",  # derived
        "source_file",
        "LOCA_ID", "SAMP_TOP", "ELEV_SAMP_TOP", "SAMP_REF", "SAMP_TYPE", "SAMP_ID",
        "SPEC_REF", "SPEC_DPTH", "ELEV_SPEC_DPTH", "CMPG_TESN", "SPEC_PREP", "SPEC_DESC",
        "CMPG_TYPE", "CMPG_MOLD", "CMPG_375", "CMPG_200", "CMPG_PDEN",
        "CMPG_MAXD", "CMPG_MCOP", "CMPG_STAB", "CMPG_STYP",
        "CMPG_REM", "CMPG_METH", "CMPG_LAB", "CMPG_CRED", "TEST_STAT",
    ],

    "cmpt": [
        "samp_id",  # derived
        "source_file",
        "LOCA_ID", "SAMP_TOP", "ELEV_SAMP_TOP", "SAMP_REF", "SAMP_TYPE", "SAMP_ID",
        "SPEC_REF", "SPEC_DPTH", "ELEV_SPEC_DPTH", "CMPG_TESN",
        "CMPT_TESN", "CMPT_MC", "CMPT_DDEN", "CMPT_REM",
    ],

    "cong": [
        "samp_id",  # derived
        "source_file",
        "LOCA_ID", "SAMP_TOP", "ELEV_SAMP_TOP", "SAMP_REF", "SAMP_TYPE", "SAMP_ID",
        "SPEC_REF", "SPEC_DPTH", "ELEV_SPEC_DPTH", "SPEC_DESC", "SPEC_PREP",
        "CONG_TYPE", "CONG_COND", "CONG_SDIA", "CONG_HIGT", "CONG_MCI",
        "CONG_MCF", "CONG_BDEN", "CONG_DDEN", "CONG_PDEN", "CONG_SATR",
        "CONG_SPRS", "CONG_SATH", "CONG_IVR", "CONG_REM", "CONG_METH",
        "CONG_LAB", "CONG_CRED", "TEST_STAT",
    ],

    "cons": [
        "samp_id",  # derived
        "source_file",
        "LOCA_ID", "SAMP_TOP", "ELEV_SAMP_TOP", "SAMP_REF", "SAMP_TYPE", "SAMP_ID",
        "SPEC_REF", "SPEC_DPTH", "ELEV_SPEC_DPTH",
        "CONS_INCN", "CONS_IVR", "CONS_INCF", "CONS_INCE", "CONS_INMV",
        "CONS_INSC", "CONS_CVRT", "CONS_CVLG", "CONS_TEMP", "CONS_REM",
    ],

    "shbg": [
        "samp_id",  # derived
        "source_file",
        "LOCA_ID", "SAMP_TOP", "ELEV_SAMP_TOP", "SAMP_REF", "SAMP_TYPE", "SAMP_ID",
        "SPEC_REF", "SPEC_DPTH", "ELEV_SPEC_DPTH", "SPEC_DESC", "SPEC_PREP",
        "SHBG_TYPE", "SHBG_COND", "SHBG_CONS", "SHBG_PCOH", "SHBG_PHI",
        "SHBG_RCOH", "SHBG_RPHI", "SHBG_ENCA", "SHBG_REM", "SHBG_METH",
        "SHBG_LAB", "SHBG_CRED", "TEST_STAT",
    ],

    "shbt": [
        "samp_id",  # derived
        "source_file",
        "LOCA_ID", "SAMP_TOP", "ELEV_SAMP_TOP", "SAMP_REF", "SAMP_TYPE", "SAMP_ID",
        "SPEC_REF", "SPEC_DPTH", "ELEV_SPEC_DPTH",
        "SHBT_TESN", "SHBT_BDEN", "SHBT_DDEN", "SHBT_NORM", "SHBT_DISP",
        "SHBT_DISR", "SHBT_REVS", "SHBT_PEAK", "SHBT_RES", "SHBT_PDIS",
        "SHBT_RDIS", "SHBT_PDIN", "SHBT_RDIN", "SHBT_PDEN", "SHBT_IVR",
        "SHBT_MCI", "SHBT_MCF", "SHBT_DIA1", "SHBT_DIA2", "SHBT_HGT",
        "SHBT_CRIT", "SHBT_REM",
    ],

    "trig": [
        "samp_id",  # derived
        "source_file",
        "LOCA_ID", "SAMP_TOP", "ELEV_SAMP_TOP", "SAMP_REF", "SAMP_TYPE", "SAMP_ID",
        "SPEC_REF", "SPEC_DPTH", "ELEV_SPEC_DPTH", "SPEC_DESC", "SPEC_PREP",
        "TRIG_TYPE", "TRIG_COND", "TRIG_REM", "TRIG_METH", "TRIG_LAB",
        "TRIG_CRED", "TEST_STAT",
    ],

    "trit": [
        "samp_id",  # derived
        "source_file",
        "LOCA_ID", "SAMP_TOP", "ELEV_SAMP_TOP", "SAMP_REF", "SAMP_TYPE", "SAMP_ID",
        "SPEC_REF", "SPEC_DPTH", "ELEV_SPEC_DPTH",
        "TRIT_TESN", "TRIT_SDIA", "TRIT_SLEN", "TRIT_IMC", "TRIT_FMC",
        "TRIT_CELL", "TRIT_DEVF", "TRIT_BDEN", "TRIT_DDEN", "TRIT_STRN",
        "TRIT_CU", "TRIT_MODE", "TRIT_REM",
    ],

    "gchm": [
        "samp_id",  # derived
        "source_file",
        "LOCA_ID", "SAMP_TOP", "ELEV_SAMP_TOP", "SAMP_REF", "SAMP_TYPE", "SAMP_ID",
        "SPEC_REF", "SPEC_DPTH", "ELEV_SPEC_DPTH",
        "GCHM_CODE", "GCHM_METH", "GCHM_TTYP", "GCHM_RESL", "GCHM_UNIT",
        "GCHM_NAME", "SPEC_DESC", "SPEC_PREP", "GCHM_REM", "GCHM_LAB",
        "GCHM_CRED", "TEST_STAT",
    ],

    "eres": [
        "samp_id",  # derived
        "source_file",
        "LOCA_ID", "SAMP_TOP", "ELEV_SAMP_TOP", "SAMP_REF", "SAMP_TYPE", "SAMP_ID",
        "SPEC_REF", "SPEC_DPTH", "ELEV_SPEC_DPTH",
        "ERES_CODE", "ERES_METH", "ERES_MATX", "ERES_RTYP", "ERES_TESN",
        "ERES_NAME", "ERES_TNAM", "ERES_RVAL", "ERES_RUNI", "ERES_RTXT",
        "ERES_RTCD", "ERES_RRES", "ERES_DETF", "ERES_ORG", "ERES_IQLF",
        "ERES_LQLF", "ERES_RDLM", "ERES_MDLM", "ERES_QLM", "ERES_DUNI",
        "ERES_TICP", "ERES_TICT", "ERES_RDAT", "ERES_SGRP", "SPEC_PREP",
        "SPEC_DESC", "ERES_DTIM", "ERES_TEST", "ERES_TORD", "ERES_LOCN",
        "ERES_BAS", "ERES_DIL", "ERES_LMTH", "ERES_LDTM", "ERES_IREF",
        "ERES_SIZE", "ERES_PERP", "ERES_REM", "ERES_LAB", "ERES_CRED",
        "TEST_STAT",
    ],

    # ------------------------------------------------------------------ #
    # Stub for forward compatibility (not in this sample file)            #
    # ------------------------------------------------------------------ #

    "lpdn": [
        "samp_id",  # derived
        "source_file",
        "LOCA_ID", "SAMP_TOP", "ELEV_SAMP_TOP", "SAMP_REF", "SAMP_TYPE", "SAMP_ID",
        "SPEC_REF", "SPEC_DPTH", "ELEV_SPEC_DPTH", "SPEC_DESC", "SPEC_PREP",
        "LPDN_PDEN", "LPDN_TYPE", "LPDN_REM", "LPDN_METH", "LPDN_LAB",
        "LPDN_CRED", "TEST_STAT",
    ],

    # ------------------------------------------------------------------ #
    # Additional tables with depth measurements (stub stubs with ELEV_*)  #
    # ------------------------------------------------------------------ #

    "spec": [
        "samp_id",  # derived
        "source_file",
        "LOCA_ID", "SAMP_TOP", "ELEV_SAMP_TOP", "SAMP_REF", "SAMP_TYPE", "SAMP_ID",
        "SPEC_REF", "SPEC_DPTH", "ELEV_SPEC_DPTH", "SPEC_BASE", "ELEV_SPEC_BASE", "SPEC_DESC",
        "SPEC_PREP", "SPEC_PUID", "SPEC_COND", "SPEC_STAT",
    ],

    "cdia": [
        "source_file",
        "LOCA_ID", "CDIA_DPTH", "ELEV_CDIA_DPTH", "CDIA_TOOL", "CDIA_DIAM", "CDIA_REM",
    ],

    "disc": [
        "source_file",
        "LOCA_ID", "DISC_TOP", "ELEV_DISC_TOP", "DISC_BASE", "ELEV_DISC_BASE", "DISC_DESC", "DISC_REM",
    ],

    "dlog": [
        "source_file",
        "LOCA_ID", "DLOG_TOP", "ELEV_DLOG_TOP", "DLOG_BASE", "ELEV_DLOG_BASE", "DLOG_REM",
    ],

    "dobs": [
        "source_file",
        "LOCA_ID", "DOBS_TOP", "ELEV_DOBS_TOP", "DOBS_BASE", "ELEV_DOBS_BASE", "DOBS_DESC", "DOBS_REM",
    ],

    "dprb": [
        "source_file",
        "LOCA_ID", "DPRB_DPTH", "ELEV_DPRB_DPTH", "DPRB_REM",
    ],

    "drem": [
        "source_file",
        "LOCA_ID", "DREM_TOP", "ELEV_DREM_TOP", "DREM_BASE", "ELEV_DREM_BASE", "DREM_DESC", "DREM_REM",
    ],

    "fghg": [
        "source_file",
        "LOCA_ID", "FGHG_TOP", "ELEV_FGHG_TOP", "FGHG_BASE", "ELEV_FGHG_BASE", "FGHG_HBAS", "ELEV_FGHG_HBAS",
        "FGHG_CAS", "ELEV_FGHG_CAS", "FGHG_PRWL", "ELEV_FGHG_PRWL", "FGHG_AWL", "ELEV_FGHG_AWL", "FGHG_REM",
    ],

    "flsh": [
        "source_file",
        "LOCA_ID", "FLSH_TOP", "ELEV_FLSH_TOP", "FLSH_BASE", "ELEV_FLSH_BASE", "FLSH_DESC", "FLSH_REM",
    ],

    "hdia": [
        "source_file",
        "LOCA_ID", "HDIA_DPTH", "ELEV_HDIA_DPTH", "HDIA_TOOL", "HDIA_DIAM", "HDIA_REM",
    ],

    "horn": [
        "source_file",
        "LOCA_ID", "HORN_TOP", "ELEV_HORN_TOP", "HORN_BASE", "ELEV_HORN_BASE", "HORN_DESC", "HORN_REM",
    ],

    "iden": [
        "source_file",
        "LOCA_ID", "IDEN_DPTH", "ELEV_IDEN_DPTH", "IDEN_TYPE", "IDEN_REM",
    ],

    "ifid": [
        "source_file",
        "LOCA_ID", "IFID_DPTH", "ELEV_IFID_DPTH", "IFID_TYPE", "IFID_REM",
    ],

    "ipen": [
        "source_file",
        "LOCA_ID", "IPEN_DPTH", "ELEV_IPEN_DPTH", "IPEN_TYPE", "IPEN_REM",
    ],

    "iprg": [
        "source_file",
        "LOCA_ID", "IPRG_TOP", "ELEV_IPRG_TOP", "IPRG_BASE", "ELEV_IPRG_BASE", "IPRG_PRWL", "ELEV_IPRG_PRWL",
        "IPRG_SWAL", "ELEV_IPRG_SWAL", "IPRG_AWL", "ELEV_IPRG_AWL", "IPRG_REM",
    ],

    "iprt": [
        "source_file",
        "LOCA_ID", "IPRT_DPTH", "ELEV_IPRT_DPTH", "IPRT_TYPE", "IPRT_REM",
    ],

    "irdx": [
        "source_file",
        "LOCA_ID", "IRDX_DPTH", "ELEV_IRDX_DPTH", "IRDX_TYPE", "IRDX_REM",
    ],

    "ires": [
        "source_file",
        "LOCA_ID", "IRES_DPTH", "ELEV_IRES_DPTH", "IRES_BASE", "ELEV_IRES_BASE", "IRES_REM",
    ],

    "isag": [
        "source_file",
        "LOCA_ID", "ISAG_DPTS", "ELEV_ISAG_DPTS", "ISAG_DPTE", "ELEV_ISAG_DPTE", "ISAG_AGG", "ISAG_REM",
    ],

    "isat": [
        "source_file",
        "LOCA_ID", "ISAT_DPTH", "ELEV_ISAT_DPTH", "ISAT_TYPE", "ISAT_REM",
    ],

    "pltg": [
        "source_file",
        "LOCA_ID", "PLTG_DPTH", "ELEV_PLTG_DPTH", "PLTG_TYPE", "PLTG_REM",
    ],

    "pmtg": [
        "source_file",
        "LOCA_ID", "PMTG_DPTH", "ELEV_PMTG_DPTH", "PMTG_TYPE", "PMTG_REM",
    ],

    "pumt": [
        "source_file",
        "LOCA_ID", "PUMT_DPTH", "ELEV_PUMT_DPTH", "PUMT_TEST", "PUMT_REM",
    ],

    "scdg": [
        "source_file",
        "LOCA_ID", "SCDG_DPTH", "ELEV_SCDG_DPTH", "SCDG_TYPE", "SCDG_REM",
    ],

    "scpp": [
        "source_file",
        "LOCA_ID", "SCPP_TOP", "ELEV_SCPP_TOP", "SCPP_BASE", "ELEV_SCPP_BASE", "SCPP_DESC", "SCPP_REM",
    ],

    "scpt": [
        "source_file",
        "LOCA_ID", "SCPT_DPTH", "ELEV_SCPT_DPTH", "SCPT_TYPE", "SCPT_REM",
    ],

    "wadd": [
        "source_file",
        "LOCA_ID", "WADD_TOP", "ELEV_WADD_TOP", "WADD_BASE", "ELEV_WADD_BASE", "WADD_DESC", "WADD_REM",
    ],

    "wgpg": [
        "source_file",
        "LOCA_ID", "WGPG_STRT", "ELEV_WGPG_STRT", "WGPG_STOP", "ELEV_WGPG_STOP", "WGPG_BHD", "ELEV_WGPG_BHD", "WGPG_REM",
    ],

    "wgpt": [
        "source_file",
        "LOCA_ID", "WGPT_DPTH", "ELEV_WGPT_DPTH", "WGPT_TYPE", "WGPT_REM",
    ],
}

# Append shared filter columns to all tables (except meta/manifest) so Power BI
# users can filter any table by location cluster, location type, or geology legend.
for _table, _cols in EXPECTED_CSVS.items():
    if _table in {"meta", "manifest", "proj"}:
        continue
    for _col in COMMON_FILTER_COLUMNS:
        if _col not in _cols:
            _cols.append(_col)