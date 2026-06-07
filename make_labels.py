import pandas as pd

def label_activity(
    df: pd.DataFrame,
    endpoint_col: str = "endpoint_value_normalized",
    endpoint_type_col: str = "endpoint_type",
    unit_col: str = "endpoint_unit_normalized",
    active_max: float = 16,
    inactive_min: float = 64,
) -> pd.DataFrame:
    df = df.copy()

    df["activity_label"] = None

    mask_mic = (
        df[endpoint_type_col].str.upper().eq("MIC")
        & df[unit_col].str.lower().isin(["um", "µm"])
    )

    df.loc[mask_mic & (df[endpoint_col] <= active_max), "activity_label"] = 1
    df.loc[mask_mic & (df[endpoint_col] >= inactive_min), "activity_label"] = 0

    df["gray_zone"] = mask_mic & df["activity_label"].isna()

    return df
