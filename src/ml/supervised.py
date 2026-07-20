"""Supervised learning — LinearRegression, DecisionTree, RandomForest.

Yêu cầu A10, G2, G3: ≥2 supervised models cho regression.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict

from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import cross_val_score
import logging

logger = logging.getLogger(__name__)


# Model registry
MODELS = {
    "linear": LinearRegression,
    "decision_tree": DecisionTreeRegressor,
    "random_forest": RandomForestRegressor,
}


@dataclass
class ModelMetrics:
    """Metrics của một model."""
    model_name: str
    rmse: float
    mae: float
    r2: float
    cv_rmse_mean: Optional[float] = None
    cv_rmse_std: Optional[float] = None
    n_train: int = 0
    n_test: int = 0


class SalaryRegressionModel:
    """Regression model for salary prediction.

    Wraps sklearn model with pipeline, training, evaluation.
    """

    def __init__(
        self,
        model_type: str = "linear",
        preprocessor=None,
        model_params: Optional[Dict] = None,
    ):
        """Initialize regression model.

        Args:
            model_type: "linear", "decision_tree", "random_forest"
            preprocessor: sklearn ColumnTransformer (from feature_pipeline)
            model_params: dict of params passed to model constructor
        """
        self.model_type = model_type
        self.model_class = MODELS.get(model_type)
        if self.model_class is None:
            raise ValueError(f"Unknown model type: {model_type}. Use: {list(MODELS.keys())}")

        # Default params
        default_params = {}
        if model_type == "decision_tree":
            default_params = {"max_depth": 10, "min_samples_leaf": 5, "random_state": 42}
        elif model_type == "random_forest":
            default_params = {"n_estimators": 100, "max_depth": 15, "min_samples_leaf": 4, "random_state": 42, "n_jobs": -1}
        elif model_type == "linear":
            default_params = {}

        params = {**default_params, **(model_params or {})}
        self.model = self.model_class(**params)
        self.preprocessor = preprocessor
        self.pipeline = None
        self.feature_names_ = None

    def build_pipeline(self, preprocessor) -> Pipeline:
        """Build Pipeline: preprocessor -> model."""
        self.preprocessor = preprocessor
        self.pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("model", self.model),
        ])
        return self.pipeline

    def train(self, X_train, y_train) -> "SalaryRegressionModel":
        """Train the model."""
        if self.preprocessor is not None and self.pipeline is None:
            self.build_pipeline(self.preprocessor)

        if self.pipeline is not None:
            self.pipeline.fit(X_train, y_train)
        else:
            self.model.fit(X_train, y_train)

        return self

    def predict(self, X_test) -> np.ndarray:
        """Predict on test data."""
        if self.pipeline is not None:
            return self.pipeline.predict(X_test)
        return self.model.predict(X_test)

    def evaluate(self, X_test, y_test) -> ModelMetrics:
        """Evaluate model on test set."""
        y_pred = self.predict(X_test)
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        mae = float(mean_absolute_error(y_test, y_pred))
        r2 = float(r2_score(y_test, y_pred))

        return ModelMetrics(
            model_name=self.model_type,
            rmse=rmse,
            mae=mae,
            r2=r2,
            n_train=0,
            n_test=len(y_test),
        )

    def cross_validate(self, X, y, cv: int = 5) -> Tuple[float, float]:
        """Cross-validation score."""
        if self.pipeline is not None:
            scores = cross_val_score(self.pipeline, X, y, cv=cv,
                                     scoring="neg_root_mean_squared_error")
        else:
            scores = cross_val_score(self.model, X, y, cv=cv,
                                     scoring="neg_root_mean_squared_error")
        return -scores.mean(), scores.std()

    def error_analysis(self, X_test, y_test, df_test: Optional[pd.DataFrame] = None,
                       n_samples: int = 10) -> pd.DataFrame:
        """Phân tích 10+ trường hợp dự đoán sai.

        Args:
            X_test: features
            y_test: true values
            df_test: original DataFrame with job_id, job_title, city etc.
            n_samples: number of worst errors to show

        Returns:
            DataFrame with: job_title, city, true, predicted, residual, error_pct, reason
        """
        y_pred = self.predict(X_test)

        errors = pd.DataFrame({
            "true": y_test.values if hasattr(y_test, "values") else np.array(y_test),
            "predicted": y_pred,
        })
        errors["residual"] = errors["true"] - errors["predicted"]
        errors["error_pct"] = abs(errors["residual"] / errors["true"]) * 100
        errors["abs_residual"] = abs(errors["residual"])

        if df_test is not None:
            errors["job_id"] = df_test.index if df_test.index.name else df_test.index
            if "job_title" in df_test.columns:
                errors["job_title"] = df_test["job_title"].values
            if "city" in df_test.columns:
                errors["city"] = df_test["city"].values
            if "experience_years" in df_test.columns:
                errors["experience_years"] = df_test["experience_years"].values

        # Sort by absolute error
        errors = errors.sort_values("abs_residual", ascending=False)

        # Analyze error reasons
        reasons = []
        for _, row in errors.iterrows():
            r = row.get("residual", 0)
            pct = row.get("error_pct", 0)

            if abs(r) > 20:
                reasons.append("Extreme (>20M)")
            elif abs(r) > 10:
                reasons.append("Large error (10-20M)")
            elif pct > 50:
                reasons.append("High relative error (>50%)")
            elif pct > 30:
                reasons.append("Moderate relative error (30-50%)")
            elif r > 0:
                reasons.append("Overpredicted")
            else:
                reasons.append("Underpredicted")

        errors["error_reason"] = reasons[:len(errors)]

        return errors.head(n_samples)


def train_all_models(
    X_train, y_train, X_test, y_test,
    preprocessor=None,
    model_types: List[str] = None,
    cv: int = 5,
) -> Dict[str, SalaryRegressionModel]:
    """Train multiple models and return all with metrics."""
    if model_types is None:
        model_types = ["linear", "decision_tree", "random_forest"]

    results = {}
    for mtype in model_types:
        logger.info(f"Training {mtype}...")
        model = SalaryRegressionModel(mtype, preprocessor=preprocessor)
        model.train(X_train, y_train)
        results[mtype] = model

    return results


if __name__ == "__main__":
    from sklearn.model_selection import train_test_split
    import pandas as pd
    import numpy as np

    # Sample data
    np.random.seed(42)
    n = 500
    X = pd.DataFrame({
        "experience_years": np.random.gamma(2, 1.5, n),
        "city": np.random.choice(["HCMC", "Hanoi", "Da Nang"], n),
        "job_type": np.random.choice(["Full-time", "Contract"], n),
    })
    y = 15 + 3 * X["experience_years"] + (X["city"] == "HCMC") * 5 + np.random.randn(n) * 3

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    models = train_all_models(X_train, y_train, X_test, y_test)

    for name, model in models.items():
        metrics = model.evaluate(X_test, y_test)
        print(f"{name}: RMSE={metrics.rmse:.2f}, MAE={metrics.mae:.2f}, R²={metrics.r2:.4f}")

        if name == "linear":
            errors = model.error_analysis(X_test, y_test, n_samples=5)
            print("  Top errors:")
            for _, row in errors.iterrows():
                print(f"    True={row['true']:.1f}, Pred={row['predicted']:.1f}, Resid={row['residual']:.1f}, Reason={row['error_reason']}")