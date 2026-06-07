from pathlib import Path
import pandas as pd


def inventory_csv_columns(input_dir, output_path):
    input_dir = Path(input_dir)
    rows = []

    for csv_file in sorted(input_dir.rglob("*.csv")):
        source_database = csv_file.parts[-2] if len(csv_file.parts) >= 2 else "unknown"

        df = pd.read_csv(csv_file, nrows=1000)

        for col in df.columns:
            non_empty = df[col].notna().sum()
            examples = df[col].dropna().astype(str).head(5).tolist()

            rows.append({
                "source_database": source_database,
                "source_file": str(csv_file),
                "original_column": col,
                "n_non_empty_in_first_1000": int(non_empty),
                "example_values": " | ".join(examples),
                "mapped_to": "",
            })

    out = pd.DataFrame(rows)
    out.to_csv(output_path, index=False)
    print(f"Inventário salvo em: {output_path}")


if __name__ == "__main__":
    inventory_csv_columns(
        "data/raw/databases",
        "reports/tables/source_field_inventory.csv",
    )
