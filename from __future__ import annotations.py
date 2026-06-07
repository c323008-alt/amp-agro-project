from __future__ import annotations

import json
from pathlib import Path
import pandas as pd


CANONICAL_AA = set("ACDEFGHIKLMNPQRSTVWY")


COLUMN_MAP = {
    "dbaasp": {
        "peptide_name": ["NAME", "Target_Species"],
        "sequence_raw": ["peptides_sequence", "SEQUENCE"],
        "source_record_id": ["Peptide_id", "ID"],
        "target_name": ["Target", "Target_Species", "TARGET_OBJECT"],
        "endpoint_value_raw": ["activity", "MIC", "IC50", "IC90"],
        "endpoint_unit_raw": ["unit", "activity_mensure"],
        "reference_id": ["doi", "DOI", "pmid", "PMID", "Reference"],
    },
    "dramp": {
        "peptide_name": ["Name", "name"],
        "sequence_raw": ["Sequence", "sequence"],
        "source_record_id": ["DRAMP_ID", "id"],
        "target_name": ["Target_Organism", "target"],
        "endpoint_value_raw": ["Activity", "MIC", "Cytotoxicity"],
        "endpoint_unit_raw": ["Unit", "unit", "Activity"],
        "reference_id": ["Reference", "DOI", "PMID"],
    },
    "dbamp3": {
        "peptide_name": ["Name", "name"],
        "sequence_raw": ["Sequence", "sequence", "Seq"],
        "source_record_id": ["dbAMP_ID", "id"],
        "target_name": ["Targets", "target"],
        "endpoint_value_raw": ["MIC", "activity"],
        "endpoint_unit_raw": ["Unit", "unit", "Uniprot", "Uniprot_ID"],
        "reference_id": ["Reference", "DOI", "PMID"],
    },
    "pdblab": {
        "peptide_name": [],
        "sequence_raw": ["sequence"],
        "source_record_id": ["PepLab_id"],
        "target_name": ["Target"],
        "endpoint_value_raw": ["IC50", "MIC", "activity"],     
        "endpoint_unit_raw": []
    },
    "plantepepdb": {
        "peptide_name": ["peptide_name"],
        "sequence_raw": ["peptide_family"],
        "source_record_id": ["ppepdb-id"],
        "target_name": ["peptide_activity"],
        "endpoint_value_raw": ["MIC", "activity"],
        "endpoint_unit_raw": ["validation"]
    },
    "peplab": {
        "peptide_name": ["NAME", "name"],
        "sequence_raw": ["secuencia", "seuence"],
        "source_record_id": ["ID"],
        "target_name": ["Cepa", "activity"],
        "endpoint_value_raw": ["MIC", "activity"],
        "endpoint_unit_raw": []
    },
    "camp3": {
        "peptide_name": ["Title"],
        "sequence_raw": ["Sequence"],
        "source_record_id": ["CAMP_ID"],
        "target_name": ["Target"],
        "endpoint_value_raw": ["Validation"],
        "endpoint_unit_raw": ["Activity"]
    }
}


def clean_sequence(seq: str) -> str:
    if pd.isna(seq):
        return ""

    seq = str(seq).strip().upper()
    seq = seq.replace(" ", "")
    seq = seq.replace("-", "")
    seq = seq.replace("\n", "")
    seq = seq.replace("\r", "")
    seq = seq.replace("\t", "")

    return seq


def is_canonical(seq: str) -> bool:
    seq = clean_sequence(seq)
    return len(seq) > 0 and set(seq).issubset(CANONICAL_AA)


def first_available_value(row: pd.Series, possible_columns: list[str]):
    for col in possible_columns:
        if col in row.index:
            value = row[col]
            if not pd.isna(value) and str(value).strip() != "":
                return value
    return ""


def infer_database_name(path: Path) -> str:
    lower_path = str(path).lower()

    if "dbaasp" in lower_path:
        return "dbaasp"
    if "dramp" in lower_path:
        return "dramp"
    if "dbamp" in lower_path:
        return "dbamp"

    return "unknown"


def map_row_to_standard(row: pd.Series, source_database: str, source_file: str, row_number: int):
    mapping = COLUMN_MAP.get(source_database, {})

    sequence_raw = first_available_value(row, mapping.get("sequence_raw", []))
    sequence_standardized = clean_sequence(sequence_raw)

    canonical = is_canonical(sequence_standardized)

    source_record_id = first_available_value(row, mapping.get("source_record_id", []))

    if source_record_id == "":
        source_record_id = f"{source_database}_{row_number:07d}"

    peptide_id = f"{source_database.upper()}_{source_record_id}"

    standard = {
        "source_database": source_database,
        "source_file": source_file,
        "source_record_id": source_record_id,
        "original_columns_json": json.dumps(row.to_dict(), ensure_ascii=False),

        "assay_id": "",  # será preenchido depois, porque bancos nem sempre são assay-level
        "peptide_id": peptide_id,
        "peptide_name": first_available_value(row, mapping.get("peptide_name", [])),

        "sequence_raw": sequence_raw,
        "sequence_standardized": sequence_standardized,
        "length_aa": len(sequence_standardized) if sequence_standardized else "",

        "canonical_status": "canonical" if canonical else "noncanonical_or_invalid",
        "chemical_regime": "A" if canonical else "unknown",

        "target_name": first_available_value(row, mapping.get("target_name", [])),
        "target_group": "unknown",
        "host_plant_name": "not_reported",

        "endpoint_type": "unknown",
        "endpoint_value_raw": first_available_value(row, mapping.get("endpoint_value_raw", [])),
        "endpoint_operator": "",
        "endpoint_unit_raw": first_available_value(row, mapping.get("endpoint_unit_raw", [])),
        "endpoint_value_normalized": "",
        "endpoint_unit_normalized": "",

        "train_eligible": "unknown",
        "exclusion_reason": "needs_manual_curation",
        "reference_id": first_available_value(row, mapping.get("reference_id", [])),

        "curation_status": "staging",
        "curator_notes": "",
    }

    return standard


def harmonize_all_csvs(input_dir: str, output_path: str):
    input_dir = Path(input_dir)
    output_path = Path(output_path)

    all_rows = []

    csv_files = sorted(input_dir.rglob("*.csv"))

    for csv_file in csv_files:
        source_database = infer_database_name(csv_file)

        print(f"Lendo {csv_file} como {source_database}")

        df = pd.read_csv(csv_file)

        for i, row in df.iterrows():
            standard_row = map_row_to_standard(
                row=row,
                source_database=source_database,
                source_file=str(csv_file),
                row_number=i + 1,
            )
            all_rows.append(standard_row)

    out_df = pd.DataFrame(all_rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(output_path, index=False)

    print(f"Arquivo salvo em: {output_path}")
    print(f"Total de registros: {len(out_df)}")


if __name__ == "__main__":
    harmonize_all_csvs(
        input_dir="data/raw/databases",
        output_path="data/interim/staging_all_databases.csv",
    )