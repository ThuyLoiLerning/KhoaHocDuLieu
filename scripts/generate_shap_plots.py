"""Sinh SHAP plots cho Decision Tree & Linear Regression → PNG vào reports/slides/charts/.

Tái hiện pipeline từ notebook 04: load processed → features → ColumnTransformer →
train model → shap.TreeExplainer / LinearExplainer → summary plot.
Cần: pip install shap (0.52.0).
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.model_selection import train_test_split

sys.path.append(".")
from src.data.data_manager import JobDataManager
from src.features.feature_pipeline import get_default_features, prepare_features, prepare_target, build_preprocessing_pipeline
from src.ml.supervised import SalaryRegressionModel

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHARTS_DIR = PROJECT_ROOT / "reports" / "slides" / "charts"
OUTPUT = {
    "decision_tree": CHARTS_DIR / "shap_tree_summary.png",
    "linear": CHARTS_DIR / "shap_linear_summary.png",
}

plt.rcParams["figure.facecolor"] = "white"


def load_data():
    manager = JobDataManager(processed_dir="data/processed", raw_dir="data/raw")
    df = manager.load_processed()
    df_reg = df.dropna(subset=["salary_mid"]).copy()
    config = get_default_features()
    X = prepare_features(df_reg, target_col="salary_mid")
    y = prepare_target(df_reg, target_col="salary_mid")[0]
    return X, y, config


def train(model_type, X_train, y_train, preprocessor):
    params = None
    if model_type == "decision_tree":
        params = {"max_depth": 8, "min_samples_leaf": 5, "random_state": 42}
    model = SalaryRegressionModel(model_type=model_type, preprocessor=preprocessor,
                                  model_params=params)
    model.train(X_train, y_train)
    return model


def shap_plot(model, X_test, feature_names, title, out_path):
    if model.model_type == "decision_tree":
        explainer = shap.TreeExplainer(model.pipeline.named_steps["model"])
        shap_values = explainer.shap_values(X_test)
    else:
        explainer = shap.LinearExplainer(model.pipeline.named_steps["model"], X_test)
        shap_values = explainer.shap_values(X_test)

    fig = plt.figure(figsize=(11, 6))
    shap.summary_plot(shap_values, X_test, feature_names=feature_names, show=False)
    plt.title(title, fontsize=14, pad=10)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def main():
    X, y, config = load_data()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42)

    preprocessor = build_preprocessing_pipeline(
        numeric_features=config["numeric"],
        categorical_features=config["categorical"],
        ordinal_features=config["ordinal"],
        ordinal_categories=config["ordinal_categories"],
    )
    X_train_t = preprocessor.fit_transform(X_train)
    X_test_t = preprocessor.transform(X_test)
    feature_names = preprocessor.get_feature_names_out()
    X_test_df = pd.DataFrame(X_test_t, columns=feature_names)

    for mtype in ["decision_tree", "linear"]:
        model = train(mtype, X_train, y_train, preprocessor)
        shap_plot(model, X_test_df, feature_names,
                  f"SHAP Summary — {mtype.replace('_', ' ').title()} (salary_mid, triệu VND)",
                  OUTPUT[mtype])


if __name__ == "__main__":
    main()
