"""Feature pipeline — ColumnTransformer với preprocessing.

Yêu cầu: sklearn Pipeline cho numeric (impute + scale),
categorical (OneHot), ordinal (OrdinalEncoder).
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Tuple, Dict
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, OrdinalEncoder, LabelEncoder


def build_preprocessing_pipeline(
    numeric_features: List[str] = None,
    categorical_features: List[str] = None,
    ordinal_features: List[str] = None,
    ordinal_categories: List[List[str]] = None,
) -> ColumnTransformer:
    """Xây dựng preprocessing pipeline.

    Args:
        numeric_features: cột số (impute median + standard scale)
        categorical_features: cột phân loại (OneHot encode)
        ordinal_features: cột thứ tự (Ordinal encode)
        ordinal_categories: thứ tự cho từng ordinal feature

    Returns:
        ColumnTransformer với 3 pipelines
    """
    transformers = []

    if numeric_features:
        numeric_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ])
        transformers.append(("numeric", numeric_pipeline, numeric_features))

    if categorical_features:
        categorical_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ])
        transformers.append(("categorical", categorical_pipeline, categorical_features))

    if ordinal_features:
        ordinal_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="constant", fill_value="unknown")),
            ("ordinal", OrdinalEncoder(
                categories=ordinal_categories if ordinal_categories else "auto",
                handle_unknown="use_encoded_value",
                unknown_value=-1,
            )),
        ])
        transformers.append(("ordinal", ordinal_pipeline, ordinal_features))

    return ColumnTransformer(
        transformers,
        remainder="drop",
        verbose_feature_names_out=False,
    )


def prepare_target(
    df: pd.DataFrame,
    target_col: str = "salary_mid",
    mode: str = "regression",
    log_transform: bool = False,
) -> Tuple[pd.Series, Optional[pd.Series]]:
    """Chuẩn bị target variable.

    Args:
        df: DataFrame chứa target column
        target_col: tên cột target
        mode: "regression" | "classification"
        log_transform: log-transform target (cho regression)

    Returns:
        y (pd.Series), y_class (pd.Series or None)
    """
    y = df[target_col].copy()

    # Remove NaN targets
    valid = y.notna()
    y = y[valid]

    if log_transform:
        y = np.log1p(y)

    if mode == "classification":
        # Salary classes: low < 10M, medium 10-25M, high > 25M
        y_class = pd.cut(
            y,
            bins=[0, 10, 25, np.inf],
            labels=["low", "medium", "high"],
            right=True,
        )
        return y, y_class

    return y, None


def prepare_features(
    df: pd.DataFrame,
    target_col: str = "salary_mid",
    drop_cols: List[str] = None,
) -> pd.DataFrame:
    """Remove target + unnecessary columns from feature set.

    Args:
        df: DataFrame
        target_col: target column to remove
        drop_cols: additional columns to remove (IDs, text, etc.)

    Returns:
        Feature DataFrame (no target)
    """
    if drop_cols is None:
        drop_cols = [
            "job_id", "company_id", "job_title", "description", "description_raw",
            "source_url", "source_site", "source_html_path", "crawled_at",
            "posted_at", "salary_min", "salary_max", "salary_mid",
        ]

    df = df.copy()

    # Drop columns that exist
    cols_to_drop = [c for c in drop_cols if c in df.columns]
    # Also drop target if specified and not in drop_cols
    if target_col in df.columns and target_col not in cols_to_drop:
        cols_to_drop.append(target_col)

    X = df.drop(columns=cols_to_drop, errors="ignore")

    # Drop any remaining ID-like columns
    for c in X.columns:
        if c.lower().endswith("_id") or c == "index":
            X = X.drop(columns=[c])

    return X


def get_default_features() -> Dict:
    """Get default feature groups cho dự đoán lương."""
    return {
        "numeric": ["experience_years"],
        "categorical": [
            "city", "job_type", "remote_option", "education_level",
            "industry", "company_size",
        ],
        "ordinal": ["experience_bin"],
        "ordinal_categories": [
            ["entry", "junior", "mid", "senior", "lead"],
        ],
    }


if __name__ == "__main__":
    # Test pipeline
    from sklearn.model_selection import train_test_split

    # Create sample data
    np.random.seed(42)
    n = 100

    df = pd.DataFrame({
        "experience_years": np.random.gamma(2, 1.5, n),
        "city": np.random.choice(["HCMC", "Hanoi", "Da Nang"], n),
        "job_type": np.random.choice(["Full-time", "Part-time", "Contract"], n),
        "remote_option": np.random.choice(["On-site", "Hybrid", "Remote"], n),
        "education_level": np.random.choice(["Bachelor", "Master", "Not specified"], n),
        "experience_bin": np.random.choice(["entry", "junior", "mid", "senior"], n),
        "salary_mid": np.random.lognormal(2.8, 0.4, n),
    })

    # Build pipeline
    config = get_default_features()
    preprocessor = build_preprocessing_pipeline(
        numeric_features=config["numeric"],
        categorical_features=config["categorical"],
        ordinal_features=config["ordinal"],
        ordinal_categories=config["ordinal_categories"],
    )

    X = prepare_features(df, target_col="salary_mid")
    y = prepare_target(df, target_col="salary_mid")[0]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Transform
    X_train_transformed = preprocessor.fit_transform(X_train)
    print(f"Train shape: {X_train_transformed.shape}, Test shape: {preprocessor.transform(X_test).shape}")
    print(f"Feature names: {preprocessor.get_feature_names_out()[:10]}")