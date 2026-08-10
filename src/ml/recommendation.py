"""Recommendation engine — content-based filtering with cosine similarity.

Yêu cầu A11, D4, F6, G6: gợi ý việc làm theo hồ sơ kỹ năng ứng viên.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)


@dataclass
class Recommendation:
    """Kết quả gợi ý 1 việc làm."""
    job_id: str
    job_title: str
    company_name: str
    city: str
    salary_mid: Optional[float]
    similarity_score: float
    matched_skills: List[str]
    missing_skills: List[str]


class RecommendationEngine:
    """Content-based recommendation using skill similarity.

    Phù hợp với yêu cầu F6: top việc làm phù hợp với hồ sơ kỹ năng.

    Usage:
        engine = RecommendationEngine()
        engine.fit(skills_df)
        recommendations = engine.recommend(
            user_skills=["Python", "SQL", "ML"],
            jobs_df=jobs_df
        )
    """

    def __init__(self, similarity_threshold: float = 0.0):
        self.mlb = MultiLabelBinarizer()
        self.job_skill_matrix = None  # job × skill matrix
        self.job_ids = None
        self.skill_names = None
        self.fitted = False

    def fit(self, skills_df: pd.DataFrame,
            job_id_col: str = "job_id",
            skill_col: str = "skill_name") -> "RecommendationEngine":
        """Build job × skill matrix from skills data.

        Args:
            skills_df: DataFrame with job_id, skill_name columns
            job_id_col: column name for job ID
            skill_col: column name for skill name

        Returns:
            self
        """
        # Group skills by job
        job_skills = skills_df.groupby(job_id_col)[skill_col].apply(list).reset_index()
        self.job_ids = job_skills[job_id_col].tolist()

        # Fit MultiLabelBinarizer & transform
        self.mlb.fit(job_skills[skill_col])
        self.job_skill_matrix = self.mlb.transform(job_skills[skill_col])
        self.skill_names = self.mlb.classes_
        self.fitted = True

        logger.info(f"RecommendationEngine fit: {self.job_skill_matrix.shape[0]} jobs × {self.job_skill_matrix.shape[1]} skills")
        return self

    def recommend(self, user_skills: List[str], jobs_df: pd.DataFrame,
                  top_n: int = 10,
                  experience_years: Optional[float] = None,
                  city: Optional[str] = None) -> List[Recommendation]:
        """Recommend jobs based on user skill profile.

        Args:
            user_skills: list of skill names the user has
            jobs_df: DataFrame with job details (job_id, job_title,
                company_name, city, salary_mid, [experience_years_parsed])
            top_n: number of top recommendations to return
            experience_years: if given, only jobs with experience_years_parsed
                within [x-0.5, x+0.5] are returned (fallback: experience_bin)
            city: if given, only jobs whose city matches (case-insensitive)
                are returned

        Returns:
            List of Recommendation, sorted by similarity score
        """
        if not self.fitted:
            raise ValueError("Must call fit() before recommend()")

        # Transform user skills into binary vector
        user_vector = self.mlb.transform([user_skills])

        # Compute cosine similarity with all jobs
        similarities = cosine_similarity(user_vector, self.job_skill_matrix).flatten()

        # Filter mask (keep = not excluded)
        job_ids_array = np.array(self.job_ids)
        keep = np.ones(len(job_ids_array), dtype=bool)

        if city is not None and str(city).strip():
            city_norm = str(city).strip().lower()
            city_vals = jobs_df.set_index("job_id")["city"].fillna("").astype(str).str.lower()
            keep &= np.array([city_vals.get(jid, "") == city_norm for jid in job_ids_array])

        if experience_years is not None:
            jobs_by_id = jobs_df.set_index("job_id")
            if "experience_years_parsed" in jobs_by_id.columns:
                exp_vals = jobs_by_id["experience_years_parsed"]
                keep &= np.array([
                    pd.notna(exp_vals.get(jid)) and
                    abs(float(exp_vals.get(jid)) - experience_years) <= 0.5
                    for jid in job_ids_array
                ])
            elif "experience_bin" in jobs_by_id.columns:
                bins = {"entry": 1.0, "junior": 2.0, "mid": 4.0, "senior": 6.0, "lead": 8.0}
                target_bin = min(bins.items(), key=lambda kv: abs(kv[1] - experience_years))[0]
                bin_vals = jobs_by_id["experience_bin"].fillna("").astype(str)
                keep &= np.array([bin_vals.get(jid, "") == target_bin for jid in job_ids_array])
            else:
                logger.warning(
                    "experience_years filter requested but neither "
                    "'experience_years_parsed' nor 'experience_bin' exists; ignoring"
                )

        # Apply filter BEFORE top-N
        candidates = np.where(keep)[0]
        if len(candidates) == 0:
            return []
        sims_filtered = similarities[candidates]
        top_indices = candidates[np.argsort(sims_filtered)[::-1][:top_n]]

        # Find matched/missing skills
        all_matched = []
        for rank_idx, idx in enumerate(top_indices):
            row = self.job_skill_matrix[idx]
            job_vector = row.toarray().flatten() if hasattr(row, 'toarray') else np.asarray(row).flatten()
            matched = [self.skill_names[i] for i in range(len(self.skill_names))
                       if job_vector[i] > 0 and self.skill_names[i] in user_skills]
            missing = [self.skill_names[i] for i in range(len(self.skill_names))
                       if job_vector[i] > 0 and self.skill_names[i] not in user_skills]
            all_matched.append(matched)

        # Build result
        recommendations = []
        for rank_idx, idx in enumerate(top_indices):
            job_id = self.job_ids[idx]
            job = jobs_df[jobs_df["job_id"] == job_id]
            if job.empty:
                continue

            job = job.iloc[0]
            rec = Recommendation(
                job_id=job_id,
                job_title=str(job.get("job_title", "")),
                company_name=str(job.get("company_name", "")),
                city=str(job.get("city", "")),
                salary_mid=float(job["salary_mid"]) if pd.notna(job.get("salary_mid")) else None,
                similarity_score=round(float(similarities[idx]), 4),
                matched_skills=all_matched[rank_idx] if rank_idx < len(all_matched) else [],
                missing_skills=[],  # computed above
            )
            # Fill missing skills
            row = self.job_skill_matrix[idx]
            job_vector = row.toarray().flatten() if hasattr(row, 'toarray') else np.asarray(row).flatten()
            rec.missing_skills = [
                self.skill_names[i] for i in range(len(self.skill_names))
                if job_vector[i] > 0 and self.skill_names[i] not in user_skills
            ]
            recommendations.append(rec)

        return recommendations

    def recommend_by_job_id(self, target_job_id: str, jobs_df: pd.DataFrame,
                            top_n: int = 10) -> List[Recommendation]:
        """Recommend similar jobs to a given job.

        Args:
            target_job_id: job ID to find similar jobs for
            jobs_df: DataFrame with job details
            top_n: number of recommendations

        Returns:
            List of Recommendation
        """
        if not self.fitted:
            raise ValueError("Must call fit() before recommend_by_job_id()")

        # Find target job vector
        if target_job_id not in self.job_ids:
            raise ValueError(f"Job ID '{target_job_id}' not found")
        target_idx = self.job_ids.index(target_job_id)
        target_vector = self.job_skill_matrix[target_idx]

        # Cosine similarity with all other jobs
        similarities = cosine_similarity(target_vector.reshape(1, -1), self.job_skill_matrix).flatten()

        # Mask self
        similarities[target_idx] = -1

        # Top N
        top_indices = np.argsort(similarities)[::-1][:top_n]

        recommendations = []
        for idx in top_indices:
            if similarities[idx] <= 0:
                continue
            job_id = self.job_ids[idx]
            job = jobs_df[jobs_df["job_id"] == job_id]
            if job.empty:
                continue
            job = job.iloc[0]

            rec = Recommendation(
                job_id=job_id,
                job_title=str(job.get("job_title", "")),
                company_name=str(job.get("company_name", "")),
                city=str(job.get("city", "")),
                salary_mid=float(job["salary_mid"]) if pd.notna(job.get("salary_mid")) else None,
                similarity_score=round(float(similarities[idx]), 4),
                matched_skills=[],
                missing_skills=[],
            )
            recommendations.append(rec)

        return recommendations

    def get_job_skill_count(self) -> int:
        """Number of unique skills in the model."""
        return len(self.skill_names) if self.fitted else 0

    def get_matrix_shape(self) -> Tuple[int, int]:
        """Shape of job × skill matrix."""
        if not self.fitted:
            return (0, 0)
        return self.job_skill_matrix.shape

    def format_recommendations(self, recs: List[Recommendation]) -> str:
        """Format recommendations as human-readable string."""
        lines = ["=== Job Recommendations ==="]
        for i, rec in enumerate(recs, 1):
            salary = f"{rec.salary_mid}M" if rec.salary_mid else "N/A"
            lines.append(f"\n#{i} [{rec.similarity_score:.1%}] {rec.job_title}")
            lines.append(f"   {rec.company_name} - {rec.city} - {salary}")
            if rec.matched_skills:
                lines.append(f"   ✅ Matched: {', '.join(rec.matched_skills[:5])}")
            if rec.missing_skills:
                lines.append(f"   ⬜ Missing: {', '.join(rec.missing_skills[:5])}")
        return "\n".join(lines)


if __name__ == "__main__":
    # Test
    np.random.seed(42)

    # Sample skills
    skills_data = pd.DataFrame({
        "job_id": ["job_1"] * 3 + ["job_2"] * 2 + ["job_3"] * 4,
        "skill_name": ["Python", "SQL", "React", "Java", "Spring",
                        "Python", "SQL", "Machine Learning", "Docker"],
    })
    skills_data["required_level"] = "Required"

    # Sample jobs
    jobs_data = pd.DataFrame({
        "job_id": ["job_1", "job_2", "job_3"],
        "job_title": ["Backend Dev", "Java Dev", "Data Scientist"],
        "company_name": ["FPT", "VNG", "VNG"],
        "city": ["HCMC", "Hanoi", "HCMC"],
        "salary_mid": [20.0, 18.0, 25.0],
    })

    # Train engine
    engine = RecommendationEngine()
    engine.fit(skills_data)

    print(f"Matrix: {engine.get_matrix_shape()[0]} jobs × {engine.get_matrix_shape()[1]} skills")

    # Recommend
    user_skills = ["Python", "SQL", "Machine Learning"]
    recs = engine.recommend(user_skills, jobs_data, top_n=3)
    print(engine.format_recommendations(recs))