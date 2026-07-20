"""Baseline model — DummyRegressor (mean/median).

Yêu cầu A9, G1: mô hình đơn giản làm mốc so sánh.
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


@dataclass
class BaselineMetrics:
    """Metrics của baseline model."""
    rmse: float
    mae: float
    r2: float
    strategy: str
    n_train: int
    n_test: int
    target_mean: float
    target_std: float


class BaselineModel:
    """Baseline model using sklearn DummyRegressor.

    Dùng làm baseline để so sánh với các mô hình phức tạp hơn.
    """

    def __init__(self, strategy: str = "mean"):
        """Initialize baseline.

        Args:
            strategy: "mean" | "median"
        """
        self.strategy = strategy
        self.model = DummyRegressor(strategy=strategy)
        self._target_mean = None
        self._target_std = None

    def fit(self, X, y):
        """Fit baseline model."""
        self.model.fit(X, y)
        self._target_mean = y.mean() if hasattr(y, "mean") else np.mean(y)
        self._target_std = y.std() if hasattr(y, "std") else np.std(y)
        return self

    def predict(self, X):
        """Predict using baseline (constant value)."""
        return self.model.predict(X)

    def evaluate(self, y_true, y_pred) -> Dict[str, float]:
        """Evaluate predictions.

        Returns:
            Dict with rmse, mae, r2
        """
        return {
            "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
            "mae": float(mean_absolute_error(y_true, y_pred)),
            "r2": float(r2_score(y_true, y_pred)),
        }

    def get_metrics(self, X_train, y_train, X_test, y_test) -> BaselineMetrics:
        """Fit on train, predict on test, return metrics."""
        self.fit(X_train, y_train)
        y_pred = self.predict(X_test)
        diff = y_pred.mean() if hasattr(y_pred, "mean") else np.mean(y_pred)

        metrics = self.evaluate(y_test, y_pred)
        return BaselineMetrics(
            rmse=metrics["rmse"],
            mae=metrics["mae"],
            r2=metrics["r2"],
            strategy=self.strategy,
            n_train=len(y_train),
            n_test=len(y_test),
            target_mean=self._target_mean,
            target_std=self._target_std,
        )

    def summary(self, metrics: BaselineMetrics) -> str:
        """Human-readable summary."""
        return (
            f"Baseline ({metrics.strategy}):\n"
            f"  RMSE = {metrics.rmse:.2f} triệu\n"
            f"  MAE  = {metrics.mae:.2f} triệu\n"
            f"  R²   = {metrics.r2:.4f}\n"
            f"  Target: mean={metrics.target_mean:.1f}, std={metrics.target_std:.1f}\n"
            f"  Train: {metrics.n_train}, Test: {metrics.n_test}"
        )


def compare_baselines(X_train, y_train, X_test, y_test) -> Dict[str, BaselineMetrics]:
    """So sánh cả 2 baseline strategies.

    Returns:
        Dict: {"mean": BaselineMetrics, "median": BaselineMetrics}
    """
    results = {}
    for strategy in ["mean", "median"]:
        model = BaselineModel(strategy=strategy)
        metrics = model.get_metrics(X_train, y_train, X_test, y_test)
        results[strategy] = metrics

    return results


if __name__ == "__main__":
    from sklearn.model_selection import train_test_split
    import numpy as np

    # Sample data
    np.random.seed(42)
    n = 1000
    X = np.random.randn(n, 5)
    y = 10 + 3 * X[:, 0] + np.random.randn(n) * 2

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    results = compare_baselines(X_train, y_train, X_test, y_test)
    for strategy, metrics in results.items():
        print(BaselineModel().summary(metrics))
        print()