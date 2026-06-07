import pandas as pd
from pathlib import Path


def export_review_markdown(input_path, output_path, filter_reason=None, max_records=100):
    df = pd.read_csv(input_path)

    if filter_reason is not None:
        df = df[df["exclusion_reason"] == filter_reason].copy()

    df = df.head(max_records)

    lines = []
    lines.append("# Relatório de revisão de curadoria\n")

    if filter_reason:
        lines.append(f"Filtro aplicado: `{filter_reason}`\n")

    for i, row in df.iterrows():
        lines.append(f"## Registro {i + 1}\n")
        lines.append(f"- **source_database:** {row.get('source_database', '')}")
        lines.append(f"- **source_record_id:** {row.get('source_record_id', '')}")
        lines.append(f"- **peptide_id:** {row.get('peptide_id', '')}")
        lines.append(f"- **peptide_name:** {row.get('peptide_name', '')}")
        lines.append(f"- **sequence:** `{row.get('sequence_standardized', '')}`")
        lines.append(f"- **target_name:** {row.get('target_name', '')}")
        lines.append(f"- **endpoint_value_raw:** {row.get('endpoint_value_raw', '')}")
        lines.append(f"- **endpoint_unit_raw:** {row.get('endpoint_unit_raw', '')}")
        lines.append(f"- **reference_id:** {row.get('reference_id', '')}")
        lines.append(f"- **exclusion_reason:** {row.get('exclusion_reason', '')}")
        lines.append("\n**Decisão de curadoria:** \n")
        lines.append("- [ ] manter como treinável")
        lines.append("- [ ] manter como contextual")
        lines.append("- [ ] excluir")
        lines.append("- [ ] buscar artigo original")
        lines.append("\n---\n")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Markdown salvo em: {output_path}")


if __name__ == "__main__":
    export_review_markdown(
        input_path="data/interim/staging_all_databases.csv",
        output_path="reports/curation_review/review_pending_endpoint.md",
        filter_reason="pending_endpoint_normalization",
        max_records=100,
    )
