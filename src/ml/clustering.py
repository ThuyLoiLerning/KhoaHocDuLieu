"""K-Means clustering — phân nhóm việc làm.

Yêu cầu A11, G5: unsupervised learning.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
import logging

logger = logging.getLogger(__name__)


@dataclass
class ClusterProfile:
    """Profile của 1 cluster."""
    cluster_id: int
    size: int
    size_pct: float
    avg_salary: float
    avg_experience: float
    top_cities: List[str]
    top_titles: List[str]
    top_skills: List[str]
    top_job_types: List[str]
    remote_ratio: float


class JobClusterer:
    """K-Means clustering for job postings.

    Phân nhóm việc làm theo lương, kinh nghiệm, kỹ năng, remote.

    Usage:
        clusterer = JobClusterer(n_clusters=5)
        clusterer.fit(X)
        labels = clusterer.predict(X)
        profiles = clusterer.get_cluster_profiles(df_with_labels)
    """

    def __init__(self, n_clusters: int = 5, random_state: int = 42, **kwargs):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10, **kwargs)
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=2, random_state=random_state)
        self.fitted = False
        self.silhouette_score_ = None

    def fit(self, X: pd.DataFrame) -> "JobClusterer":
        """Fit K-Means on feature matrix.

        Args:
            X: Feature DataFrame (numeric, scaled internally)

        Returns:
            self
        """
        # Ensure no NaN - fill with 0
        if isinstance(X, pd.DataFrame):
            X = X.fillna(0)
        else:
            X = np.nan_to_num(X)

        # Scale
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.fitted = True

        # Silhouette score
        if X_scaled.shape[0] > self.n_clusters and X_scaled.shape[1] > 1:
            try:
                self.silhouette_score_ = silhouette_score(X_scaled, self.model.labels_)
            except Exception as e:
                logger.warning(f"Cannot compute silhouette score: {e}")

        # PCA for visualization
        if X_scaled.shape[1] >= 2:
            self.pca.fit(X_scaled)

        logger.info(f"K-Means: {self.n_clusters} clusters, silhouette={self.silhouette_score_:.4f}")
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict cluster labels."""
        if not self.fitted:
            raise ValueError("Must fit before predict")

        if not isinstance(X, np.ndarray):
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X

        return self.model.predict(X_scaled)

    def fit_predict(self, X: pd.DataFrame) -> np.ndarray:
        """Fit and return cluster labels."""
        # Ensure no NaN before fitting
        if isinstance(X, pd.DataFrame):
            X = X.fillna(0)
        else:
            X = np.nan_to_num(X)
        self.fit(X)
        return self.model.labels_

    def get_cluster_profiles(self, df: pd.DataFrame, cluster_col: str = "cluster") -> List[ClusterProfile]:
        """Get detailed profiles for each cluster.

        Args:
            df: DataFrame with cluster labels
            cluster_col: column name with cluster labels

        Returns:
            List of ClusterProfile
        """
        profiles = []
        n_total = len(df)

        for cluster_id in sorted(df[cluster_col].unique()):
            cluster_df = df[df[cluster_col] == cluster_id]
            size = len(cluster_df)

            # Salary
            avg_salary = cluster_df.get("salary_mid", pd.Series([np.nan])).mean()
            if pd.isna(avg_salary):
                avg_salary = 0

            # Experience
            avg_exp = cluster_df.get("experience_years", pd.Series([np.nan])).mean()
            if pd.isna(avg_exp):
                avg_exp = 0

            # Top cities
            if "city" in cluster_df.columns:
                top_cities = cluster_df["city"].value_counts().head(3).index.tolist()
            else:
                top_cities = []

            # Top titles
            if "job_title" in cluster_df.columns:
                top_titles = cluster_df["job_title"].value_counts().head(3).index.tolist()
            else:
                top_titles = []

            # Top skills (from list column)
            if "skills" in cluster_df.columns:
                all_skills = []
                for s_list in cluster_df["skills"].dropna():
                    if isinstance(s_list, list):
                        all_skills.extend(s_list)
                    elif isinstance(s_list, str):
                        all_skills.extend(s_list.replace("[", "").replace("]", "").replace("'", "").split(", "))
                skill_counts = pd.Series(all_skills).value_counts().head(3)
                top_skills = skill_counts.index.tolist() if not skill_counts.empty else []
            else:
                top_skills = []

            # Top job types
            if "job_type" in cluster_df.columns:
                top_types = cluster_df["job_type"].value_counts().head(3).index.tolist()
            else:
                top_types = []

            # Remote ratio
            if "remote_option" in cluster_df.columns:
                remote_count = cluster_df[cluster_df["remote_option"].str.contains("Remote", na=False)].shape[0]
                remote_ratio = remote_count / size if size > 0 else 0
            else:
                remote_ratio = 0

            profiles.append(ClusterProfile(
                cluster_id=int(cluster_id),
                size=size,
                size_pct=round(size / n_total * 100, 1),
                avg_salary=round(avg_salary, 1),
                avg_experience=round(avg_exp, 2),
                top_cities=top_cities,
                top_titles=top_titles,
                top_skills=top_skills,
                top_job_types=top_types,
                remote_ratio=round(remote_ratio, 2),
            ))

        return profiles

    def plot_clusters(self, X: pd.DataFrame, labels: np.ndarray = None) -> np.ndarray:
        """Project to 2D PCA and return coordinates for plotting."""
        # Ensure no NaN
        if isinstance(X, pd.DataFrame):
            X = X.fillna(0)
        else:
            X = np.nan_to_num(X)

        if not isinstance(X, np.ndarray):
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X

        coords = self.pca.transform(X_scaled)
        return coords

    def plot_silhouette(self, X: pd.DataFrame, k_range: range = range(2, 11)) -> List[float]:
        """Tim k toi uu bang silhouette score.

        Args:
            X: feature matrix
            k_range: range of k values to try

        Returns:
            List of (k, score) tuples
        """
        # Ensure no NaN
        if isinstance(X, pd.DataFrame):
            X = X.fillna(0).values
        else:
            X = np.nan_to_num(X)

        scores = []
        for k in k_range:
            if k >= X.shape[0]:
                continue
            km = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            labels = km.fit_predict(X)
            try:
                score = silhouette_score(X, labels)
            except:
                score = -1
            scores.append((k, score))
            logger.info(f"  k={k}: silhouette={score:.4f}")

        return scores

    def get_cluster_summary(self, profiles: List[ClusterProfile]) -> str:
        """Human-readable summary of clusters."""
        lines = ["=== Cluster Summary ==="]
        for p in profiles:
            lines.append(f"\nCluster {p.cluster_id} ({p.size_pct:.0f}% - {p.size} jobs):")
            lines.append(f"  Salary: {p.avg_salary}M | Experience: {p.avg_experience:.1f}y")
            lines.append(f"  Top cities: {', '.join(p.top_cities[:3])}")
            lines.append(f"  Top titles: {', '.join(p.top_titles[:3])}")
            lines.append(f"  Top skills: {', '.join(p.top_skills[:3])}")
            lines.append(f"  Remote: {p.remote_ratio:.0%}")
        return "\n".join(lines)


def find_optimal_k(X: pd.DataFrame, max_k: int = 10) -> int:
    """Find optimal k using silhouette + elbow heuristic."""
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score

    best_k = 2
    best_score = -1
    inertias = []

    for k in range(2, min(max_k + 1, X.shape[0])):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X)
        inertias.append(km.inertia_)

        try:
            score = silhouette_score(X, labels)
            if score > best_score:
                best_score = score
                best_k = k
        except:
            pass

    return best_k


if __name__ == "__main__":
    from sklearn.datasets import make_blobs

    X, _ = make_blobs(n_samples=300, centers=4, n_features=5, random_state=42)
    df = pd.DataFrame(X, columns=[f"f{i}" for i in range(5)])
    df["salary_mid"] = np.random.lognormal(2.8, 0.3, 300)
    df["city"] = np.random.choice(["HCMC", "Hanoi", "Da Nang"], 300)
    df["job_title"] = np.random.choice(["Developer", "Tester", "Manager"], 300)

    clusterer = JobClusterer(n_clusters=4)
    labels = clusterer.fit_predict(df[["f0", "f1", "f2", "f3", "f4"]])
    df["cluster"] = labels

    profiles = clusterer.get_cluster_profiles(df)
    print(clusterer.get_cluster_summary(profiles))