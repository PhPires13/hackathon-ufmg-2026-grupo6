from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


TARGET_COL = 'valor_condenacao'

LEGALCASE_FEATURES = [
    'uf',
    'assunto',
    'sub_assunto',
    'valor_causa',
    'has_contrato',
    'has_extrato',
    'has_comprovante_credito',
    'has_dossie',
    'has_demonstrativo_evolucao_divida',
    'has_laudo_referenciado',
]

BOOLEAN_FEATURES = [
    'has_contrato',
    'has_extrato',
    'has_comprovante_credito',
    'has_dossie',
    'has_demonstrativo_evolucao_divida',
    'has_laudo_referenciado',
]

CATEGORICAL_FEATURES = ['uf', 'assunto', 'sub_assunto']
NUMERIC_FEATURES = ['valor_causa'] + BOOLEAN_FEATURES

DEFAULT_DATA_PATH = Path(__file__).resolve().parents[1] / 'merged.csv'
DEFAULT_ARTIFACT_DIR = Path(__file__).resolve().parent / 'artifacts'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Train a scikit-learn model to predict valor_condenacao from LegalCase data.'
    )
    parser.add_argument(
        '--data-path',
        default=str(DEFAULT_DATA_PATH),
        help=f'CSV path (default: {DEFAULT_DATA_PATH})',
    )
    parser.add_argument(
        '--artifact-dir',
        default=str(DEFAULT_ARTIFACT_DIR),
        help=f'Directory to save model artifacts (default: {DEFAULT_ARTIFACT_DIR})',
    )
    parser.add_argument('--test-size', type=float, default=0.2, help='Test split size (default: 0.2).')
    parser.add_argument('--random-state', type=int, default=42, help='Random seed (default: 42).')
    return parser.parse_args()


def _parse_br_number(value: Any) -> float:
    if pd.isna(value):
        return np.nan

    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)

    text = str(value).strip()
    if not text:
        return np.nan

    text = text.replace('.', '').replace(',', '.')
    try:
        return float(text)
    except ValueError:
        return np.nan


def _parse_bool_like(value: Any) -> float:
    if pd.isna(value):
        return 0.0

    if isinstance(value, (bool, np.bool_)):
        return 1.0 if value else 0.0

    text = str(value).strip().lower()
    if text in {'1', 'true', 't', 'yes', 'y', 'sim'}:
        return 1.0
    if text in {'0', 'false', 'f', 'no', 'n', 'nao'}:
        return 0.0

    return 0.0


def load_training_data(csv_path: Path) -> tuple[pd.DataFrame, pd.Series]:
    if not csv_path.exists():
        raise FileNotFoundError(f'CSV not found: {csv_path}')

    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    required_columns = set(LEGALCASE_FEATURES + [TARGET_COL])
    missing = required_columns.difference(df.columns)
    if missing:
        missing_list = ', '.join(sorted(missing))
        raise ValueError(f'Missing required columns in CSV: {missing_list}')

    data = df[LEGALCASE_FEATURES + [TARGET_COL]].copy()

    data['valor_causa'] = data['valor_causa'].apply(_parse_br_number)
    data[TARGET_COL] = data[TARGET_COL].apply(_parse_br_number)

    for col in BOOLEAN_FEATURES:
        data[col] = data[col].apply(_parse_bool_like)

    # Keep rows with a known target value for supervised training.
    data = data.dropna(subset=[TARGET_COL])

    x = data[LEGALCASE_FEATURES]
    y = data[TARGET_COL]
    return x, y


def build_pipeline(random_state: int) -> Pipeline:
    categorical_transformer = Pipeline(
        steps=[
            ('imputer', SimpleImputer(strategy='most_frequent')),
            ('onehot', OneHotEncoder(handle_unknown='ignore')),
        ]
    )

    numeric_transformer = Pipeline(
        steps=[
            ('imputer', SimpleImputer(strategy='median')),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ('categorical', categorical_transformer, CATEGORICAL_FEATURES),
            ('numeric', numeric_transformer, NUMERIC_FEATURES),
        ]
    )

    model = RandomForestRegressor(
        n_estimators=300,
        random_state=random_state,
        n_jobs=-1,
        min_samples_leaf=2,
    )

    return Pipeline(
        steps=[
            ('preprocessor', preprocessor),
            ('model', model),
        ]
    )


def train_and_evaluate(
    x: pd.DataFrame,
    y: pd.Series,
    test_size: float,
    random_state: int,
) -> tuple[Pipeline, dict[str, float]]:
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=test_size,
        random_state=random_state,
    )

    pipeline = build_pipeline(random_state=random_state)
    pipeline.fit(x_train, y_train)

    y_pred = pipeline.predict(x_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = r2_score(y_test, y_pred)

    metrics = {
        'mae': float(mae),
        'rmse': float(rmse),
        'r2': float(r2),
        'rows_total': float(len(x)),
        'rows_train': float(len(x_train)),
        'rows_test': float(len(x_test)),
    }

    return pipeline, metrics


def save_artifacts(model: Pipeline, metrics: dict[str, float], artifact_dir: Path) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)

    model_path = artifact_dir / 'valor_condenacao_model.pkl'
    metrics_path = artifact_dir / 'valor_condenacao_metrics.json'

    joblib.dump(model, model_path)
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding='utf-8')


def main() -> None:
    args = parse_args()

    data_path = Path(args.data_path).resolve()
    artifact_dir = Path(args.artifact_dir).resolve()

    x, y = load_training_data(data_path)
    model, metrics = train_and_evaluate(
        x=x,
        y=y,
        test_size=args.test_size,
        random_state=args.random_state,
    )
    # save_artifacts(model=model, metrics=metrics, artifact_dir=artifact_dir)

    print('Training complete.')
    print(f'Data path: {data_path}')
    print(f'Model saved at: {artifact_dir / "valor_condenacao_model.pkl"}')
    print(f'Metrics saved at: {artifact_dir / "valor_condenacao_metrics.json"}')
    print('Metrics:')
    # print(json.dumps(metrics, indent=2))


if __name__ == '__main__':
    main()

