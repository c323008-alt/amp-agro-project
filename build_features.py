"""
build_features.py

Script para gerar tabela de features clássicas.

Entrada:
data/curated/curation_pilot_validated.csv

Saída:
data/interim/classic_features_v0.csv

Uso no terminal:
python -m src.features.build_features \
  --input data/curated/curation_pilot_validated.csv \
  --output data/interim/classic_features_v0.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import pandas as pd

from src.features.sequence_features import (
    clean_sequence,
    compute_basic_sequence_features,
)
from src.features.physicochemical_descriptors import (
    compute_physicochemical_descriptors,
)


REQUIRED_COLUMNS = [
    "assay_id",
    "peptide_id",
    "sequence_standardized",
]

METADATA_COLUMNS = [
    "assay_id",
    "peptide_id",
    "reference_id",
    "peptide_name",
    "sequence_standardized",
    "length_aa",
    "canonical_status",
    "chemical_regime",
    "target_name",
    "target_group",
    "endpoint_type",
    "endpoint_value_normalized",
    "endpoint_unit_normalized",
    "activity_label",
    "gray_zone",
    "train_eligible",
]


def check_required_columns(df: pd.DataFrame, required_columns: List[str]) -> None:
    """
    Verifica se o DataFrame contém as colunas obrigatórias.
    """
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {missing}")


def normalize_boolean_column(series: pd.Series) -> pd.Series:
    """
    Normaliza colunas booleanas que podem vir como:
    yes/no, true/false, sim/não, 1/0.
    """
    true_values = {"true", "yes", "sim", "1", "y"}
    false_values = {"false", "no", "não", "nao", "0", "n"}

    def convert(value):
        if pd.isna(value):
            return pd.NA

        text = str(value).strip().lower()

        if text in true_values:
            return True
        if text in false_values:
            return False

        return value

    return series.map(convert)


def prepare_input_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza a entrada antes da extração de features.
    """
    df = df.copy()

    check_required_columns(df, REQUIRED_COLUMNS)

    df["sequence_standardized"] = df["sequence_standardized"].map(clean_sequence)

    if "train_eligible" in df.columns:
        df["train_eligible"] = normalize_boolean_column(df["train_eligible"])

    if "gray_zone" in df.columns:
        df["gray_zone"] = normalize_boolean_column(df["gray_zone"])

    # Remove linhas sem sequência
    df = df[df["sequence_standardized"].str.len() > 0].copy()

    return df


def build_features_for_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula features para todas as linhas do DataFrame.
    """
    rows = []

    for _, row in df.iterrows():
        sequence = row["sequence_standardized"]

        basic_features = compute_basic_sequence_features(sequence)
        physicochemical_features = compute_physicochemical_descriptors(sequence)

        feature_row = {}

        # Mantém metadados disponíveis
        for col in METADATA_COLUMNS:
            if col in df.columns:
                feature_row[col] = row[col]

        feature_row.update(basic_features)
        feature_row.update(physicochemical_features)

        rows.append(feature_row)

    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gera tabela de features clássicas para peptídeos."
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Caminho do CSV curado/validado de entrada.",
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Caminho do CSV de saída com features.",
    )

    parser.add_argument(
        "--trainable-only",
        action="store_true",
        help="Se usado, mantém apenas registros train_eligible = true.",
    )

    parser.add_argument(
        "--regime-a-only",
        action="store_true",
        help="Se usado, mantém apenas chemical_regime = A.",
    )

    parser.add_argument(
        "--canonical-only",
        action="store_true",
        help="Se usado, mantém apenas canonical_status = canonical.",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    df = pd.read_csv(input_path)
    df = prepare_input_dataframe(df)

    if args.trainable_only:
        if "train_eligible" not in df.columns:
            raise ValueError("A coluna train_eligible não existe no dataset.")
        df = df[df["train_eligible"] == True].copy()

    if args.regime_a_only:
        if "chemical_regime" not in df.columns:
            raise ValueError("A coluna chemical_regime não existe no dataset.")
        df = df[df["chemical_regime"] == "A"].copy()

    if args.canonical_only:
        if "canonical_status" not in df.columns:
            raise ValueError("A coluna canonical_status não existe no dataset.")
        df = df[df["canonical_status"] == "canonical"].copy()

    features_df = build_features_for_dataframe(df)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    features_df.to_csv(output_path, index=False)

    print(f"Features geradas com sucesso.")
    print(f"Entrada: {input_path}")
    print(f"Saída: {output_path}")
    print(f"Número de linhas: {len(features_df)}")
    print(f"Número de colunas: {len(features_df.columns)}")


if __name__ == "__main__":
    main()
