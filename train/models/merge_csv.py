from __future__ import annotations

import os.path
from pathlib import Path

import pandas as pd


MERGE_KEY = 'numero_processo'

# Ajuste estes caminhos conforme os seus arquivos.
CSV_A_PATH = os.path.join('../../data', 'resultados.csv')
CSV_B_PATH = os.path.join('../../data', 'subsidios.csv')
OUTPUT_PATH = os.path.join('../../data', 'merged.csv')


def load_csv(path: str) -> pd.DataFrame:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f'CSV not found: {file_path}')
    # utf-8-sig handles files with optional BOM (common from Excel exports).
    return pd.read_csv(file_path, encoding='utf-8-sig')


def validate_and_normalize_key(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    if MERGE_KEY not in df.columns:
        raise ValueError(f"Column '{MERGE_KEY}' not found in {source_name}.")

    df = df.copy()
    df[MERGE_KEY] = df[MERGE_KEY].astype(str).str.strip()
    return df


def merge_csvs(csv_a: str, csv_b: str, how: str = 'inner') -> pd.DataFrame:
    df_a = load_csv(csv_a)
    df_b = load_csv(csv_b)

    df_a = validate_and_normalize_key(df_a, 'csv-a')
    df_b = validate_and_normalize_key(df_b, 'csv-b')

    return pd.merge(df_a, df_b, on=MERGE_KEY, how=how)


def save_csv(df: pd.DataFrame, output_path: str) -> None:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, encoding='utf-8-sig')


def main() -> None:
    merged = merge_csvs(CSV_A_PATH, CSV_B_PATH)
    save_csv(merged, OUTPUT_PATH)
    print(f'Merged {len(merged)} rows into {OUTPUT_PATH}')


if __name__ == '__main__':
    main()
