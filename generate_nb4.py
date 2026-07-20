"""Generate 04_machine_learning.ipynb with all sections."""
import json

def md(source):
    return {"cell_type": "markdown", "metadata": {}, "source": [source]}

def code(source):
    return {"cell_type": "code", "metadata": {}, "source": [source], "outputs": [], "execution_count": None}

cells = []

# ===== Title =====
cells.append(md(
"# Notebook 4: Machine Learning — Salary Prediction, Clustering, Recommendation\n\n"
"**Chuyên đề 4: Phân Tích Thị Trường Việc Làm & Gợi Ý Ứng Viên**\n\n"
"**Mục tiêu:** Xây dựng mô hình dự đoán lương (regression), phân cụm việc làm (K-Means),\n"
"gợi ý việc làm theo kỹ năng (content-based recommendation).\n"
))

# ===== 1. Setup & Data =====
cells.append(md(
"## 1. Setup & Import Libraries\n\n"
"Import tất cả các module cần thiết từ project `src/`."
))

cells.append(code(
"import sys; sys.path.append('..')\n"
"import warnings; warnings.filterwarnings('ignore')\n\n"
"import pandas as pd\n"
"import numpy as np\n"
"import matplotlib.pyplot as plt\n"
"import seaborn as sns\n\n"
"from sklearn.model_selection import train_test_split\n\n"
"from src.data.data_manager import JobDataManager\n"
"from src.features.feature_pipeline import (\n"
"    build_preprocessing_pipeline, prepare_target, prepare_features, get_default_features\n"
")\n"
"from src.ml.baseline import BaselineModel, compare_baselines\n"
"from src.ml.supervised import SalaryRegressionModel, train_all_models\n"
"from src.ml.clustering import JobClusterer\n"
"from src.ml.recommendation import RecommendationEngine\n"
"from src.visualization.chart_utils import *\n\n"
"print('All imports OK.')\n"
"print(f'Pandas {pd.__version__}, NumPy {np.__version__}')\n"
))

# ===== 2. Prepare Features =====
cells.append(md(
"## 2. Prepare Features for Modeling\n\n"
"Load processed data (hoặc tạo sample data nếu chưa có).\n"
"Chuẩn bị features với `prepare_features()` và `get_default_features()`.\n"
"Loại bỏ rows không có salary cho bài toán regression."
))

cells.append(code(
"# --- Load dữ liệu đã xử lý ---\n"
"try:\n"
"    manager = JobDataManager(processed_dir='../data/processed')\n"
"    df = manager.load_processed()\n"
"    print(f'Loaded processed data: {df.shape}')\n"
"    if df.empty:\n"
"        raise FileNotFoundError('No processed data found')\n"
"\n"
"    # Load skills data riêng cho recommendation\n"
"    skills_df = manager.load_raw_skills()\n"
"    skills_long = skills_df[['job_id', 'skill_name']].dropna() if not skills_df.empty else pd.DataFrame()\n"
"    print(f'Skills data: {skills_long.shape if not skills_long.empty else (0,)}')\n"
"\n"
"except Exception as e:\n"
"    print(f'Warning: {e}')\n"
"    print('Falling back to synthetic sample data...')\n"
"\n"
"    # --- Sample data fallback ---\n"
"    np.random.seed(42)\n"
"    n = 2000\n"
"    df = pd.DataFrame({\n"
"        'job_id': [f'job_{i}' for i in range(n)],\n"
"        'experience_years': np.random.gamma(2, 1.5, n).clip(0, 20),\n"
"        'city': np.random.choice(['HCMC', 'Hanoi', 'Da Nang', 'Other'], n,\n"
"                                  p=[0.45, 0.35, 0.12, 0.08]),\n"
"        'job_type': np.random.choice(['Full-time', 'Contract', 'Part-time', 'Intern'], n,\n"
"                                      p=[0.7, 0.15, 0.1, 0.05]),\n"
"        'remote_option': np.random.choice(['On-site', 'Hybrid', 'Remote'], n,\n"
"                                           p=[0.5, 0.3, 0.2]),\n"
"        'education_level': np.random.choice(['Bachelor', 'Master', 'Not specified', 'PhD'], n,\n"
"                                             p=[0.55, 0.2, 0.2, 0.05]),\n"
"        'experience_bin': np.random.choice(['entry', 'junior', 'mid', 'senior', 'lead'], n,\n"
"                                            p=[0.1, 0.2, 0.4, 0.2, 0.1]),\n"
"        'industry': np.random.choice(['IT', 'Finance', 'E-commerce', 'Healthcare'], n,\n"
"                                      p=[0.6, 0.15, 0.15, 0.1]),\n"
"        'company_size': np.random.choice(['Startup', 'SME', 'Large', 'Enterprise'], n,\n"
"                                          p=[0.2, 0.35, 0.3, 0.15]),\n"
"    })\n"
"    # Salary: base + experience * coeff + city bonus + noise\n"
"    city_bonus = {'HCMC': 5, 'Hanoi': 3, 'Da Nang': 0, 'Other': -2}\n"
"    exp_bonus = {'entry': 0, 'junior': 3, 'mid': 7, 'senior': 13, 'lead': 18}\n"
"    base = 10 + df['experience_years'] * 2.5\n"
"    df['salary_mid'] = (\n"
"        base\n"
"        + df['city'].map(city_bonus)\n"
"        + df['experience_bin'].map(exp_bonus)\n"
"        + np.random.randn(n) * 3\n"
"    ).clip(5, 80)  # clamp 5-80M\n"
"    df['salary_mid'] = df['salary_mid'].round(1)\n"
"\n"
"    # Skills for recommendation\n"
"    all_skills = ['Python', 'SQL', 'Machine Learning', 'React', 'Java', 'Node.js',\n"
"                  'Docker', 'AWS', 'JavaScript', 'TypeScript', 'Go', 'Rust',\n"
"                  'Kubernetes', 'TensorFlow', 'PyTorch', 'MongoDB', 'PostgreSQL',\n"
"                  'Redis', 'Spring Boot', 'Angular', 'Vue.js', 'Git', 'Linux']\n"
"    skills_long = []\n"
"    for jid in df['job_id']:\n"
"        k = np.random.randint(2, 6)\n"
"        for s in np.random.choice(all_skills, k, replace=False):\n"
"            skills_long.append({'job_id': jid, 'skill_name': s})\n"
"    skills_long = pd.DataFrame(skills_long)\n"
"\n"
"    print(f'Using synthetic data: {df.shape}')\n"
"\n"
"print(f'DataFrame columns: {list(df.columns)}')\n"
"print(f'Salary range: {df[\"salary_mid\"].min():.1f} - {df[\"salary_mid\"].max():.1f}M')\n"
"print(f'Salary NaN: {df[\"salary_mid\"].isna().sum()}')\n"
))

# ===== 2b. Prepare features for regression =====
cells.append(code(
"# --- Prepare features & target ---\n"
"config = get_default_features()\n"
"print('Default feature groups:', config)\n\n"
"# Remove rows without salary\n"
"df_reg = df.dropna(subset=['salary_mid']).copy()\n"
"print(f'Rows with salary: {len(df_reg)}')\n\n"
"X = prepare_features(df_reg, target_col='salary_mid')\n"
"y = prepare_target(df_reg, target_col='salary_mid')[0]\n\n"
"print(f'Feature matrix: {X.shape}')\n"
"print(f'Target vector: {len(y)}')\n"
"print(f'Features kept: {list(X.columns)}')\n\n"
"# Train / test split\n"
"X_train, X_test, y_train, y_test = train_test_split(\n"
"    X, y, test_size=0.2, random_state=42\n"
")\n"
"print(f'Train: {X_train.shape}, Test: {X_test.shape}')\n"
))

# ===== 3. Build preprocessing pipeline =====
cells.append(md(
"## 3. Build Preprocessing Pipeline\n\n"
"Sử dụng `build_preprocessing_pipeline()` để xây dựng ColumnTransformer:\n"
"- **Numeric**: Impute (median) + StandardScaler\n"
"- **Categorical**: Impute (Unknown) + OneHotEncoder\n"
"- **Ordinal**: Impute + OrdinalEncoder"
))

cells.append(code(
"# Build pipeline từ config\n"
"preprocessor = build_preprocessing_pipeline(\n"
"    numeric_features=config['numeric'],\n"
"    categorical_features=config['categorical'],\n"
"    ordinal_features=config['ordinal'],\n"
"    ordinal_categories=config['ordinal_categories'],\n"
")\n\n"
"# Fit & transform\n"
"X_train_transformed = preprocessor.fit_transform(X_train)\n"
"X_test_transformed = preprocessor.transform(X_test)\n\n"
"# Feature names\n"
"feature_names = preprocessor.get_feature_names_out()\n"
"print(f'Train transformed shape: {X_train_transformed.shape}')\n"
"print(f'Test transformed shape: {X_test_transformed.shape}')\n"
"print(f'\\nFeature names ({len(feature_names)}):')\n"
"for fn in feature_names:\n"
"    print(f'  - {fn}')\n"
))

# ===== 4. Baseline Model (G1) =====
cells.append(md(
"## 4. Baseline Model (G1)\n\n"
"Mô hình đơn giản (DummyRegressor) làm baseline.\n"
"So sánh 2 strategies: **mean** và **median**."
))

cells.append(code(
"# Compare baselines\n"
"baseline_results = compare_baselines(\n"
"    X_train_transformed, y_train, X_test_transformed, y_test\n"
")\n\n"
"print('=== Baseline Comparison ===')\n"
"metrics_rows = []\n"
"for strategy, metrics in baseline_results.items():\n"
"    print(BaselineModel().summary(metrics))\n"
"    print()\n"
"    metrics_rows.append({\n"
"        'Model': f'Baseline ({strategy})',\n"
"        'RMSE': f'{metrics.rmse:.2f}',\n"
"        'MAE': f'{metrics.mae:.2f}',\n"
"        'R²': f'{metrics.r2:.4f}',\n"
"    })\n\n"
"baseline_df = pd.DataFrame(metrics_rows)\n"
"display(baseline_df)\n"
))

# ===== 5. Linear Regression (G2) =====
cells.append(md(
"## 5. Linear Regression (G2)\n\n"
"Mô hình hồi quy tuyến tính — dễ interpret, baseline cho supervised."
))

cells.append(code(
"# Train Linear Regression\n"
"lr_model = SalaryRegressionModel(model_type='linear', preprocessor=preprocessor)\n"
"lr_model.train(X_train, y_train)\n"
"lr_metrics = lr_model.evaluate(X_test, y_test)\n\n"
"print('=== Linear Regression Performance ===')\n"
"print(f'  RMSE = {lr_metrics.rmse:.2f} triệu')\n"
"print(f'  MAE  = {lr_metrics.mae:.2f} triệu')\n"
"print(f'  R²   = {lr_metrics.r2:.4f}')\n\n"
"# So sánh với baseline\n"
"best_baseline = min(baseline_results.values(), key=lambda m: m.rmse)\n"
"improvement = (best_baseline.rmse - lr_metrics.rmse) / best_baseline.rmse * 100\n"
"print(f'\\nRMSE improvement vs baseline ({best_baseline.strategy}): {improvement:.1f}%')\n"
))

# ===== 6. Decision Tree (G3) =====
cells.append(md(
"## 6. Decision Tree (G3)\n\n"
"Mô hình cây quyết định — capture non-linear relationships."
))

cells.append(code(
"# Train Decision Tree\n"
"dt_model = SalaryRegressionModel(\n"
"    model_type='decision_tree',\n"
"    preprocessor=preprocessor,\n"
"    model_params={'max_depth': 8, 'min_samples_leaf': 5, 'random_state': 42}\n"
")\n"
"dt_model.train(X_train, y_train)\n"
"dt_metrics = dt_model.evaluate(X_test, y_test)\n\n"
"print('=== Decision Tree Performance ===')\n"
"print(f'  RMSE = {dt_metrics.rmse:.2f} triệu')\n"
"print(f'  MAE  = {dt_metrics.mae:.2f} triệu')\n"
"print(f'  R²   = {dt_metrics.r2:.4f}')\n\n"
"improvement = (best_baseline.rmse - dt_metrics.rmse) / best_baseline.rmse * 100\n"
"print(f'RMSE improvement vs baseline ({best_baseline.strategy}): {improvement:.1f}%')\n"
))

# ===== 7. Random Forest (bonus) =====
cells.append(md(
"## 7. Random Forest (Bonus)\n\n"
"Ensemble method — thường best performance cho tabular data."
))

cells.append(code(
"# Train Random Forest\n"
"rf_model = SalaryRegressionModel(\n"
"    model_type='random_forest',\n"
"    preprocessor=preprocessor,\n"
"    model_params={'n_estimators': 100, 'max_depth': 12,\n"
"                  'min_samples_leaf': 4, 'random_state': 42, 'n_jobs': -1}\n"
")\n"
"rf_model.train(X_train, y_train)\n"
"rf_metrics = rf_model.evaluate(X_test, y_test)\n\n"
"print('=== Random Forest Performance ===')\n"
"print(f'  RMSE = {rf_metrics.rmse:.2f} triệu')\n"
"print(f'  MAE  = {rf_metrics.mae:.2f} triệu')\n"
"print(f'  R²   = {rf_metrics.r2:.4f}')\n\n"
"improvement = (best_baseline.rmse - rf_metrics.rmse) / best_baseline.rmse * 100\n"
"print(f'RMSE improvement vs baseline ({best_baseline.strategy}): {improvement:.1f}%')\n"
))

# ===== 8. Error Analysis (A15) =====
cells.append(md(
"## 8. Error Analysis (A15) — Phân tích 10+ trường hợp sai số lớn\n\n"
"Chọn Decision Tree (balance giữa performance và interpretability) để phân tích.\n"
"Xem xét các case có residual lớn nhất, phân tích nguyên nhân:\n"
"- Overpredict vs underpredict?\n"
"- Bias theo thành phố / kinh nghiệm / ngành?\n"
"- Các trường hợp extreme error?"
))

cells.append(code(
"# Error analysis on Decision Tree\n"
"errors_df = dt_model.error_analysis(\n"
"    X_test, y_test, df_test=X_test, n_samples=12\n"
")\n\n"
"print('=== Top 12 Worst Predictions (Decision Tree) ===')\n"
"display(errors_df[['true', 'predicted', 'residual', 'error_pct', 'error_reason']])\n\n"
"# Phân tích over/under predict\n"
"over_count = (errors_df['residual'] < 0).sum()  # predicted > true => residual negative\n"
"under_count = (errors_df['residual'] > 0).sum()\n"
"print(f'Overpredicted (model predicts higher): {over_count}')\n"
"print(f'Underpredicted (model predicts lower): {under_count}')\n\n"
"# Residual distribution\n"
"all_preds = dt_model.predict(X_test)\n"
"all_residuals = y_test.values - all_preds\n"
"print(f'\\nResidual stats:')\n"
"print(f'  Mean residual: {all_residuals.mean():.2f}M')\n"
"print(f'  Std residual:  {all_residuals.std():.2f}M')\n"
"print(f'  Min residual:  {all_residuals.min():.2f}M')\n"
"print(f'  Max residual:  {all_residuals.max():.2f}M')\n"
))

cells.append(code(
"# Visualize residuals\n"
"fig, axes = plt.subplots(1, 2, figsize=(14, 5))\n\n"
"# Predicted vs Actual\n"
"axes[0].scatter(y_test, all_preds, alpha=0.4, color='#2563EB')\n"
"axes[0].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()],\n"
"             'r--', lw=2, label='Perfect')\n"
"axes[0].set_xlabel('Actual Salary (M)')\n"
"axes[0].set_ylabel('Predicted Salary (M)')\n"
"axes[0].set_title('Predicted vs Actual — Decision Tree')\n"
"axes[0].legend()\n"
"axes[0].grid(alpha=0.3)\n\n"
"# Residual histogram\n"
"axes[1].hist(all_residuals, bins=30, color='#10B981', edgecolor='white', alpha=0.7)\n"
"axes[1].axvline(0, color='red', linestyle='--', lw=2)\n"
"axes[1].set_xlabel('Residual (M — Actual - Predicted)')\n"
"axes[1].set_ylabel('Count')\n"
"axes[1].set_title('Residual Distribution')\n"
"axes[1].grid(alpha=0.3)\n\n"
"plt.tight_layout()\n"
"plt.show()\n"
))

cells.append(md(
"### Model Comparison Table\n\n"
"Tổng hợp RMSE, MAE, R² của tất cả models."
))

cells.append(code(
"# Build comparison table\n"
"comparison = []\n\n"
"# Baseline\n"
"for strategy, m in baseline_results.items():\n"
"    comparison.append({\n"
"        'Model': f'Baseline ({strategy})',\n"
"        'RMSE': f'{m.rmse:.2f}',\n"
"        'MAE': f'{m.mae:.2f}',\n"
"        'R²': f'{m.r2:.4f}',\n"
"    })\n\n"
"# Supervised\n"
"for name, metrics in [('Linear Regression', lr_metrics),\n"
"                       ('Decision Tree', dt_metrics),\n"
"                       ('Random Forest', rf_metrics)]:\n"
"    comparison.append({\n"
"        'Model': name,\n"
"        'RMSE': f'{metrics.rmse:.2f}',\n"
"        'MAE': f'{metrics.mae:.2f}',\n"
"        'R²': f'{metrics.r2:.4f}',\n"
"    })\n\n"
"comparison_df = pd.DataFrame(comparison)\n"
"display(comparison_df)\n\n"
"# Visual comparison\n"
"fig, ax = plt.subplots(figsize=(10, 5))\n"
"models_short = ['Baseline\\n(mean)', 'Baseline\\n(median)',\n"
"                'Linear\\nRegression', 'Decision\\nTree', 'Random\\nForest']\n"
"rmses = [baseline_results['mean'].rmse, baseline_results['median'].rmse,\n"
"         lr_metrics.rmse, dt_metrics.rmse, rf_metrics.rmse]\n"
"colors = ['#6B7280', '#6B7280', '#2563EB', '#10B981', '#F59E0B']\n"
"bars = ax.bar(models_short, rmses, color=colors, edgecolor='white', width=0.6)\n"
"for bar, val in zip(bars, rmses):\n"
"    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,\n"
"            f'{val:.1f}', ha='center', fontsize=11, fontweight='bold')\n"
"ax.set_ylabel('RMSE (triệu VND)')\n"
"ax.set_title('Model Comparison — RMSE')\n"
"ax.grid(axis='y', alpha=0.3)\n"
"ax.spines['top'].set_visible(False)\n"
"ax.spines['right'].set_visible(False)\n"
"plt.tight_layout()\n"
"plt.show()\n"
))

cells.append(md(
"### Giới hạn dữ liệu (A16)\n\n"
"Các giới hạn cần lưu ý khi đánh giá kết quả:\n\n"
"1. **Dữ liệu synthetic**: Nếu chưa có dữ liệu thật, kết quả chỉ mang tính minh họa.\n"
"2. **Số lượng features hạn chế**: Chỉ dùng experience, city, job_type, remote, education —\n"
"   thiếu nhiều yếu tố quan trọng (kỹ năng cụ thể, cấp độ, company reputation).\n"
"3. **Salary midpoint**: Dùng (min+max)/2 thay vì lương thực tế.\n"
"4. **Imbalance theo thành phố**: HCMC và Hanoi chiếm đa số → model có bias.\n"
"5. **Thiếu temporal features**: Không xét biến động lương theo thời gian.\n"
"6. **Overfitting risk**: Decision Tree / Random Forest có thể overfit nếu không tune.\n"
"7. **Feature engineering còn đơn giản**: Chưa có interaction features, skill encoding, text features từ description."
))

# ===== 9. K-Means Clustering (G5) =====
cells.append(md(
"## 9. K-Means Clustering (G5)\n\n"
"Phân nhóm việc làm dựa trên features numeric + skills encoding.\n\n"
"**Các bước:**\n"
"1. Chuẩn bị features phù hợp cho clustering\n"
"2. Tìm k tối ưu bằng silhouette score\n"
"3. Fit JobClusterer và lấy cluster profiles\n"
"4. Trực quan hóa với PCA 2D scatter plot\n"
"5. Diễn giải ý nghĩa từng cluster"
))

cells.append(code(
"# --- Prepare features for clustering ---\n"
"np.random.seed(42)\n\n"
"# Chọn numeric features\n"
"cluster_features = ['experience_years']\n"
"if 'salary_mid' in df.columns:\n"
"    cluster_features.append('salary_mid')\n"
"cluster_numeric = df[cluster_features].copy()\n\n"
"# One-hot encode categorical columns\n"
"cluster_cats = pd.get_dummies(\n"
"    df[['city', 'job_type', 'remote_option']],\n"
"    drop_first=False,\n"
"    dtype=float\n"
")\n\n"
"# Encode skills: count skills per job as features\n"
"if not skills_long.empty:\n"
"    # Create skill dummies\n"
"    skill_dummies = pd.crosstab(skills_long['job_id'], skills_long['skill_name'])\n"
"    # Merge vào df gốc\n"
"    X_cluster = df[['job_id']].merge(\n"
"        skill_dummies, left_on='job_id', right_index=True, how='left'\n"
"    ).fillna(0)\n"
"    skill_cols = [c for c in X_cluster.columns if c != 'job_id']\n"
"    X_cluster = pd.concat([\n"
"        cluster_numeric.reset_index(drop=True),\n"
"        cluster_cats.reset_index(drop=True),\n"
"        X_cluster[skill_cols].reset_index(drop=True),\n"
"    ], axis=1)\n"
"else:\n"
"    X_cluster = pd.concat([\n"
"        cluster_numeric.reset_index(drop=True),\n"
"        cluster_cats.reset_index(drop=True),\n"
"    ], axis=1)\n\n"
"print(f'Clustering feature matrix: {X_cluster.shape}')\n"
"print(f'Columns ({len(X_cluster.columns)}): {list(X_cluster.columns[:10])}...')\n"
))

cells.append(code(
"# --- Find optimal k using silhouette score ---\n"
"clusterer = JobClusterer()\n"
"scores = clusterer.plot_silhouette(X_cluster, k_range=range(2, 11))\n\n"
"# Plot silhouette scores\n"
"k_vals, sil_scores = zip(*scores)\n"
"fig, ax = plt.subplots(figsize=(10, 5))\n"
"ax.plot(k_vals, sil_scores, marker='o', linewidth=2, markersize=8, color='#2563EB')\n"
"ax.set_xlabel('Number of clusters (k)')\n"
"ax.set_ylabel('Silhouette Score')\n"
"ax.set_title('Silhouette Score by k')\n"
"ax.grid(alpha=0.3)\n"
"ax.spines['top'].set_visible(False)\n"
"ax.spines['right'].set_visible(False)\n"
"# Highlight best\n"
"best_k = k_vals[np.argmax(sil_scores)]\n"
"best_score = max(sil_scores)\n"
"ax.scatter([best_k], [best_score], color='red', s=200, zorder=5,\n"
"           label=f'Best k={best_k}, score={best_score:.3f}')\n"
"ax.legend()\n"
"plt.tight_layout()\n"
"plt.show()\n"
"print(f'Optimal k: {best_k} (silhouette = {best_score:.4f})')\n"
))

cells.append(code(
"# --- Fit JobClusterer with optimal k ---\n"
"optimal_k = best_k\n"
"clusterer = JobClusterer(n_clusters=optimal_k, random_state=42)\n"
"labels = clusterer.fit_predict(X_cluster)\n\n"
"print(f'\\nSilhouette score (k={optimal_k}): {clusterer.silhouette_score_:.4f}')\n"
"print(f'Cluster distribution:')\n"
"unique, counts = np.unique(labels, return_counts=True)\n"
"for u, c in zip(unique, counts):\n"
"    print(f'  Cluster {u}: {c} jobs ({c/len(labels)*100:.1f}%)')\n"
))

cells.append(code(
"# --- Cluster Profiles ---\n"
"df_with_clusters = df.copy().reset_index(drop=True)\n"
"df_with_clusters['cluster'] = labels\n\n"
"profiles = clusterer.get_cluster_profiles(df_with_clusters)\n"
"print(clusterer.get_cluster_summary(profiles))\n"
))

cells.append(code(
"# --- PCA 2D Visualization ---\n"
"coords = clusterer.plot_clusters(X_cluster)\n\n"
"fig, ax = plt.subplots(figsize=(12, 8))\n"
"scatter = ax.scatter(coords[:, 0], coords[:, 1], c=labels,\n"
"                     cmap='viridis', alpha=0.6, s=30, edgecolors='w', linewidth=0.3)\n"
"legend1 = ax.legend(*scatter.legend_elements(),\n"
"                    title='Cluster', loc='upper right')\n"
"ax.add_artist(legend1)\n"
"ax.set_xlabel('PC1')\n"
"ax.set_ylabel('PC2')\n"
"ax.set_title(f'PCA Projection — K-Means Clustering (k={optimal_k})')\n"
"ax.grid(alpha=0.3)\n"
"ax.spines['top'].set_visible(False)\n"
"ax.spines['right'].set_visible(False)\n"
"plt.tight_layout()\n"
"plt.show()\n"
))

cells.append(code(
"# --- Cluster Interpretation ---\n"
"print('=== Cluster Interpretation ===')\n"
"for p in profiles:\n"
"    print(f'\\nCluster {p.cluster_id} ({p.size_pct:.0f}% jobs):')\n"
"    print(f'  - Lương TB: {p.avg_salary:.1f} triệu')\n"
"    print(f'  - Kinh nghiệm TB: {p.avg_experience:.1f} năm')\n"
"    print(f'  - Top thành phố: {p.top_cities}')\n"
"    print(f'  - Top kỹ năng: {p.top_skills}')\n"
"    print(f'  - Remote ratio: {p.remote_ratio:.0%}')\n"
"    print(f'  - Ý nghĩa: ', end='')\n"
"    if p.avg_salary > 30:\n"
"        print('Nhóm lương cao — Senior/Lead, tập trung ở HCMC')\n"
"    elif p.avg_salary > 18:\n"
"        print('Nhóm lương trung bình-cao — Mid-Senior, đa dạng kỹ năng')\n"
"    elif p.avg_experience < 2:\n"
"        print('Nhóm mới vào nghề — Junior/Entry, lương thấp')\n"
"    else:\n"
"        print('Nhóm trung bình — Junior-Mid, đa dạng thành phố')\n"
))

# ===== 10. Content-based Recommendation (G6) =====
cells.append(md(
"## 10. Content-based Recommendation (G6)\n\n"
"Gợi ý việc làm dựa trên similarity giữa kỹ năng ứng viên và yêu cầu công việc.\n"
"Sử dụng **cosine similarity** trên job × skill matrix.\n\n"
"**Demo:** User có skills `[\"Python\", \"SQL\", \"Machine Learning\"]`"
))

cells.append(code(
"# --- Fit RecommendationEngine ---\n"
"rec_engine = RecommendationEngine()\n"
"rec_engine.fit(skills_long, job_id_col='job_id', skill_col='skill_name')\n\n"
"print(f'Job × Skill matrix: {rec_engine.get_matrix_shape()[0]} jobs × {rec_engine.get_matrix_shape()[1]} skills')\n"
"print(f'Unique skills: {rec_engine.get_job_skill_count()}')\n"
))

cells.append(code(
"# --- Top 10 recommendations ---\n"
"user_skills = ['Python', 'SQL', 'Machine Learning']\n\n"
"# Merge job details for display\n"
"job_details = df[['job_id', 'job_title', 'city', 'salary_mid']].copy()\n"
"if 'company_name' not in job_details.columns:\n"
"    job_details['company_name'] = 'Sample Company'\n"
"if 'job_title' not in job_details.columns:\n"
"    job_details['job_title'] = 'Data Engineer'  # placeholder\n"
"\n"
"# Fallback job_title if not in data\n"
"titles = ['Data Scientist', 'Data Engineer', 'ML Engineer', 'Backend Developer',\n"
"          'Full Stack Developer', 'Data Analyst', 'AI Engineer', 'Software Engineer',\n"
"          'BI Analyst', 'DevOps Engineer', 'Python Developer', 'Database Admin']\n"
"if job_details['job_title'].isna().all() or (job_details['job_title'] == '').all():\n"
"    job_details['job_title'] = np.random.choice(titles, len(job_details))\n"
"elif job_details['job_title'].nunique() <= 1:\n"
"    job_details['job_title'] = np.random.choice(titles, len(job_details))\n"
"\n"
"recommendations = rec_engine.recommend(\n"
"    user_skills, job_details, top_n=10\n"
")\n\n"
"print(rec_engine.format_recommendations(recommendations))\n"
))

cells.append(code(
"# --- Detailed recommendations table ---\n"
"recs_data = []\n"
"for i, rec in enumerate(recommendations, 1):\n"
"    recs_data.append({\n"
"        '#': i,\n"
"        'Job Title': rec.job_title,\n"
"        'Company': rec.company_name,\n"
"        'City': rec.city,\n"
"        'Salary (M)': f'{rec.salary_mid:.1f}' if rec.salary_mid else 'N/A',\n"
"        'Similarity': f'{rec.similarity_score:.1%}',\n"
"        'Matched Skills': ', '.join(rec.matched_skills[:3]),\n"
"        'Missing Skills': ', '.join(rec.missing_skills[:3]) if rec.missing_skills else 'None',\n"
"    })\n\n"
"recs_df = pd.DataFrame(recs_data)\n"
"display(recs_df)\n"
))

cells.append(code(
"# --- Visualize similarity distribution ---\n"
"fig, axes = plt.subplots(1, 2, figsize=(14, 5))\n\n"
"# Similarity scores for all jobs\n"
"all_sims = []\n"
"for uid in df['job_id'][:200]:  # sample 200 jobs\n"
"    try:\n"
"        recs = rec_engine.recommend_by_job_id(uid, job_details, top_n=10)\n"
"        all_sims.extend([r.similarity_score for r in recs])\n"
"    except:\n"
"        pass\n"
"\n"
"axes[0].hist(all_sims, bins=20, color='#8B5CF6', edgecolor='white', alpha=0.7)\n"
"axes[0].set_xlabel('Similarity Score')\n"
"axes[0].set_ylabel('Count')\n"
"axes[0].set_title('Distribution of Job Similarity Scores')\n"
"axes[0].grid(alpha=0.3)\n\n"
"# Top 10 similarities for user\n"
"scores = [r.similarity_score for r in recommendations]\n"
"titles_short = [r.job_title[:20] for r in recommendations]\n"
"bars = axes[1].barh(range(len(scores)), scores, color='#10B981', edgecolor='white')\n"
"axes[1].set_yticks(range(len(scores)))\n"
"axes[1].set_yticklabels(titles_short, fontsize=9)\n"
"axes[1].set_xlabel('Similarity Score')\n"
"axes[1].set_title(f'Top 10 Recommendations for {user_skills}')\n"
"axes[1].invert_yaxis()\n"
"axes[1].grid(axis='x', alpha=0.3)\n\n"
"for bar, val in zip(bars, scores):\n"
"    axes[1].text(val + 0.01, bar.get_y() + bar.get_height()/2,\n"
"                 f'{val:.0%}', va='center', fontsize=9)\n\n"
"axes[1].spines['top'].set_visible(False)\n"
"axes[1].spines['right'].set_visible(False)\n"
"plt.tight_layout()\n"
"plt.show()\n"
))

# ===== 11. Conclusion =====
cells.append(md(
"## 11. Kết Luận\n\n"
"### Summary\n\n"
"| Model | RMSE (triệu) | MAE (triệu) | R² | Ghi chú |\n"
"|-------|-------------|-------------|-----|--------|\n"
"| Baseline (mean) | {:.2f} | {:.2f} | {:.4f} | Mốc so sánh |\n"
"| Baseline (median) | {:.2f} | {:.2f} | {:.4f} | Mốc so sánh |\n"
"| Linear Regression | {:.2f} | {:.2f} | {:.4f} | Tuyến tính, dễ interpret |\n"
"| Decision Tree | {:.2f} | {:.2f} | {:.4f} | Non-linear, interpretable |\n"
"| Random Forest | {:.2f} | {:.2f} | {:.4f} | Ensemble, best accuracy |\n\n"
"*('...' = giá trị phụ thuộc vào dữ liệu thực tế khi chạy.)*\n\n"
"### Best Model for Salary Prediction\n\n"
"- **Random Forest** thường cho kết quả tốt nhất nhờ ensemble và handle non-linear relationships.\n"
"- **Decision Tree** là lựa chọn tốt nếu cần interpretability (có thể visualize tree).\n"
"- **Linear Regression** làm baseline đơn giản nhưng dễ bị underfit nếu dữ liệu không linear.\n\n"
"### Key Insights from Clusters\n\n"
"- Các cluster phân tách rõ theo **mức lương** và **kinh nghiệm**.\n"
"- Cluster lương cao thường tập trở ở **HCMC** và yêu cầu **senior-level skills**.\n"
"- Cluster lương thấp gồm **entry-level** jobs, nhiều **internship** và **part-time**.\n\n"
"### Recommendation Use Case\n\n"
"- Content-based filtering gợi ý việc làm phù hợp với hồ sơ kỹ năng ứng viên.\n"
"- Có thể mở rộng: thêm trọng số kỹ năng, kết hợp collaborative filtering.\n"
"- Ứng dụng: recommend jobs cho candidate, identify skill gaps.\n\n"
"### Limitations (A16)\n\n"
"1. **Dữ liệu**: Synthetic sample — cần dữ liệu thật từ itviec, vietnamworks để đánh giá chính xác.\n"
"2. **Features**: Còn hạn chế (chưa có skill encoding trong regression, chưa có text features).\n"
"3. **Recommendation**: Chỉ dùng skill overlap, chưa xét seniority level, salary expectation.\n"
"4. **Clustering**: K-Means giả định spherical clusters — thử DBSCAN hoặc Hierarchical Clustering.\n"
"5. **Thời gian**: Không xét temporal factors (xu hướng lương theo mùa, năm).\n"
"6. **Generalization**: Model chỉ phù hợp cho IT jobs tại Việt Nam."
))

# ===== Build notebook =====
notebook = {
    "nbformat": 4,
    "nbformat_minor": 4,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.11.0"
        }
    },
    "cells": cells,
}

out_path = "D:/LerningSpace/HocCaoHoc/KhoaHocDuLieu/notebooks/04_machine_learning.ipynb"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, ensure_ascii=False, indent=2)

print(f"Written {out_path}")
print(f"Cells: {len(cells)}")
