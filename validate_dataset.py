import sys
import pandas as pd

CANONICAL_AA = set("ACDEFGHIKLMNPQRSTVWY")

REQUIRED_COLUMNS = [
    "assay_id",
    "peptide_id",
    "sequence_standardized",
    "canonical_status",
    "chemical_regime",
    "target_name",
    "target_group",
    "endpoint_type",
    "endpoint_value_normalized",
    "endpoint_unit_normalized",
    "train_eligible",
    "reference_id",
]

def is_canonical_sequence(seq: str) -> bool:
    if not isinstance(seq, str) or len(seq) == 0:
        return False
    return set(seq.upper()).issubset(CANONICAL_AA)

def validate_dataset(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Colunas ausentes: {missing_cols}")

    df["sequence_is_canonical_check"] = df["sequence_standardized"].apply(is_canonical_sequence)
    df["length_check"] = df["sequence_standardized"].str.len()

    problems = []

    duplicated_assays = df[df["assay_id"].duplicated()]["assay_id"].tolist()
    if duplicated_assays:
        problems.append(f"assay_id duplicado: {duplicated_assays}")

    invalid_sequences = df.loc[~df["sequence_is_canonical_check"], "assay_id"].tolist()
    if invalid_sequences:
        problems.append(f"sequências não canônicas ou inválidas: {invalid_sequences}")

    missing_endpoint = df.loc[df["endpoint_value_normalized"].isna(), "assay_id"].tolist()
    if missing_endpoint:
        problems.append(f"endpoint normalizado ausente: {missing_endpoint}")

    if problems:
        print("Problemas encontrados:")
        for p in problems:
            print(f"- {p}")
    else:
        print("Dataset passou nas validações básicas.")

    return df

if __name__ == "__main__":
    input_path = sys.argv[1]
    validate_dataset(input_path)
