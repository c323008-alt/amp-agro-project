import sys
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    f1_score,
    matthews_corrcoef,
    balanced_accuracy_score,
)

from src.modeling.make_labels import label_activity
from src.features.sequence_features import build_feature_table

def train_baseline(input_path: str):
    df = pd.read_csv(input_path)

    df = df[
        (df["train_eligible"].str.lower() == "yes")
        & (df["canonical_status"].str.lower() == "canonical")
        & (df["chemical_regime"].str.lower() == "linear")
    ].copy()

    df = label_activity(df)
    df = df[df["activity_label"].notna()].copy()

    features = build_feature_table(df)

    modeling_df = df[["assay_id", "peptide_id", "activity_label"]].merge(
        features,
        on=["assay_id", "peptide_id"],
        how="inner"
    )

    y = modeling_df["activity_label"].astype(int)
    groups = modeling_df["peptide_id"]

    X = modeling_df.drop(columns=["assay_id", "peptide_id", "activity_label"])

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.2,
        random_state=42
    )

    train_idx, test_idx = next(splitter.split(X, y, groups=groups))

    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

    model = RandomForestClassifier(
        n_estimators=500,
        random_state=42,
        class_weight="balanced"
    )

    model.fit(X_train, y_train)

    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)

    metrics = {
        "n_total": len(modeling_df),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "auroc": roc_auc_score(y_test, y_prob) if len(set(y_test)) > 1 else None,
        "auprc": average_precision_score(y_test, y_prob),
        "f1": f1_score(y_test, y_pred),
        "mcc": matthews_corrcoef(y_test, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_test, y_pred),
    }

    print("Métricas do baseline:")
    for key, value in metrics.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    train_baseline(sys.argv[1])
