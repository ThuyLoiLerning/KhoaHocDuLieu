"""Skill domain entity — represents a normalized skill from job postings."""

from dataclasses import dataclass, field
from typing import Optional
import uuid


# Skill synonym mapping — 35+ entries (Yêu cầu C6, E2, N2)
SKILL_SYNONYM_MAP = {
    # Programming Languages
    "js": "JavaScript",
    "javascript": "JavaScript",
    "java script": "JavaScript",
    "ecmascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "py": "Python",
    "python3": "Python",
    "python": "Python",
    "golang": "Go",
    "go lang": "Go",
    "golang": "Go",
    "cpp": "C++",
    "c++": "C++",
    "c#": "C#",
    "csharp": "C#",
    "vb.net": "VB.NET",
    "vb": "VB.NET",
    "ruby on rails": "Ruby",
    "rails": "Ruby",
    "php": "PHP",
    "scala": "Scala",
    "kotlin": "Kotlin",
    "swift": "Swift",
    "rust": "Rust",
    "r": "R",
    "matlab": "MATLAB",
    "sql": "SQL",
    "nosql": "NoSQL",
    "html": "HTML",
    "css": "CSS",
    "html5": "HTML",
    "css3": "CSS",
    "sass": "Sass",
    "scss": "Sass",
    "less": "Less",

    # Frontend Frameworks
    "reactjs": "React",
    "react.js": "React",
    "react": "React",
    "vuejs": "Vue.js",
    "vue.js": "Vue.js",
    "vue": "Vue.js",
    "angularjs": "AngularJS",
    "angular.js": "AngularJS",
    "angular": "Angular",
    "angular 2+": "Angular",
    "svelte": "Svelte",
    "nextjs": "Next.js",
    "next.js": "Next.js",
    "next": "Next.js",
    "nuxtjs": "Nuxt.js",
    "nuxt": "Nuxt.js",
    "gatsby": "Gatsby",
    "remix": "Remix",
    "jquery": "jQuery",
    "bootstrap": "Bootstrap",
    "tailwind": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",
    "material ui": "Material UI",
    "mui": "Material UI",
    "antd": "Ant Design",
    "chakra": "Chakra UI",

    # Backend Frameworks
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "node": "Node.js",
    "expressjs": "Express.js",
    "express": "Express.js",
    "nestjs": "NestJS",
    "nestjs": "NestJS",
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "spring boot": "Spring Boot",
    "spring": "Spring",
    "laravel": "Laravel",
    "symfony": "Symfony",
    "asp.net": "ASP.NET",
    "dotnet": ".NET",
    ".net core": ".NET Core",
    "rails": "Ruby on Rails",

    # Databases
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "psql": "PostgreSQL",
    "mysql": "MySQL",
    "mariadb": "MariaDB",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "elasticsearch": "Elasticsearch",
    "cassandra": "Cassandra",
    "dynamodb": "DynamoDB",
    "bigquery": "BigQuery",
    "snowflake": "Snowflake",
    "sql server": "SQL Server",
    "mssql": "SQL Server",
    "oracle": "Oracle",
    "sqlite": "SQLite",

    # Cloud & DevOps
    "aws": "AWS",
    "amazon web services": "AWS",
    "gcp": "Google Cloud",
    "google cloud platform": "Google Cloud",
    "azure": "Azure",
    "microsoft azure": "Azure",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "terraform": "Terraform",
    "ansible": "Ansible",
    "jenkins": "Jenkins",
    "gitlab ci": "GitLab CI",
    "github actions": "GitHub Actions",
    "circleci": "CircleCI",
    "nginx": "Nginx",
    "apache": "Apache",
    "linux": "Linux",
    "unix": "Unix",
    "bash": "Bash",
    "shell": "Shell",
    "vim": "Vim",
    "git": "Git",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",

    # Data Science / ML
    "machine learning": "Machine Learning",
    "ml": "Machine Learning",
    "deep learning": "Deep Learning",
    "dl": "Deep Learning",
    "tensorflow": "TensorFlow",
    "tf": "TensorFlow",
    "pytorch": "PyTorch",
    "torch": "PyTorch",
    "keras": "Keras",
    "scikit-learn": "Scikit-learn",
    "sklearn": "Scikit-learn",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "matplotlib": "Matplotlib",
    "seaborn": "Seaborn",
    "plotly": "Plotly",
    "jupyter": "Jupyter",
    "spark": "Apache Spark",
    "pyspark": "PySpark",
    "hadoop": "Hadoop",
    "kafka": "Kafka",
    "airflow": "Airflow",
    "tableau": "Tableau",
    "power bi": "Power BI",
    "powerbi": "Power BI",
    "looker": "Looker",
    "nlp": "NLP",
    "computer vision": "Computer Vision",
    "cv": "Computer Vision",
    "llm": "LLM",
    "large language model": "LLM",
    "rag": "RAG",
    "retrieval augmented generation": "RAG",

    # Mobile
    "android": "Android",
    "ios": "iOS",
    "react native": "React Native",
    "rn": "React Native",
    "flutter": "Flutter",
    "dart": "Dart",
    "xamarin": "Xamarin",
    "swift": "Swift",
    "objective-c": "Objective-C",
    "kotlin": "Kotlin",

    # Testing
    "jest": "Jest",
    "mocha": "Mocha",
    "chai": "Chai",
    "pytest": "pytest",
    "unittest": "unittest",
    "selenium": "Selenium",
    "cypress": "Cypress",
    "playwright": "Playwright",
    "junit": "JUnit",
    "testng": "TestNG",

    # English synonyms
    "english": "English",
    "tiếng anh": "English",
    "tieng anh": "English",
    "ielts": "IELTS",
    "toeic": "TOEIC",
    "communication": "Communication",
    "giao tiếp": "Communication",

    # Soft skills
    "teamwork": "Teamwork",
    "làm việc nhóm": "Teamwork",
    "leadership": "Leadership",
    "đãr lãnh đạo": "Leadership",
    "problem solving": "Problem Solving",
    "giải quyết vấn đề": "Problem Solving",
    "communication": "Communication",
    "agile": "Agile",
    "scrum": "Scrum",
    "kanban": "Kanban",
    "jira": "Jira",
    "confluence": "Confluence",
}

# Skill group mapping
SKILL_GROUP_MAP = {
    # Programming Languages
    "JavaScript": "Programming Language",
    "TypeScript": "Programming Language",
    "Python": "Programming Language",
    "Go": "Programming Language",
    "C++": "Programming Language",
    "C#": "Programming Language",
    "VB.NET": "Programming Language",
    "Ruby": "Programming Language",
    "PHP": "Programming Language",
    "Scala": "Programming Language",
    "Kotlin": "Programming Language",
    "Swift": "Programming Language",
    "Rust": "Programming Language",
    "R": "Programming Language",
    "MATLAB": "Programming Language",
    "SQL": "Programming Language",
    "NoSQL": "Programming Language",
    "HTML": "Programming Language",
    "CSS": "Programming Language",
    "Sass": "Programming Language",
    "Less": "Programming Language",

    # Frontend Frameworks
    "React": "Frontend Framework",
    "Vue.js": "Frontend Framework",
    "Angular": "Frontend Framework",
    "AngularJS": "Frontend Framework",
    "Svelte": "Frontend Framework",
    "Next.js": "Frontend Framework",
    "Nuxt.js": "Frontend Framework",
    "Gatsby": "Frontend Framework",
    "Remix": "Frontend Framework",
    "jQuery": "Frontend Framework",
    "Bootstrap": "Frontend Framework",
    "Tailwind CSS": "Frontend Framework",
    "Material UI": "Frontend Framework",
    "Ant Design": "Frontend Framework",
    "Chakra UI": "Frontend Framework",

    # Backend Frameworks
    "Node.js": "Backend Framework",
    "Express.js": "Backend Framework",
    "NestJS": "Backend Framework",
    "Django": "Backend Framework",
    "Flask": "Backend Framework",
    "FastAPI": "Backend Framework",
    "Spring Boot": "Backend Framework",
    "Spring": "Backend Framework",
    "Laravel": "Backend Framework",
    "Symfony": "Backend Framework",
    "ASP.NET": "Backend Framework",
    ".NET": "Backend Framework",
    ".NET Core": "Backend Framework",
    "Ruby on Rails": "Backend Framework",

    # Databases
    "PostgreSQL": "Database",
    "MySQL": "Database",
    "MariaDB": "Database",
    "MongoDB": "Database",
    "Redis": "Database",
    "Elasticsearch": "Database",
    "Cassandra": "Database",
    "DynamoDB": "Database",
    "BigQuery": "Database",
    "Snowflake": "Database",
    "SQL Server": "Database",
    "Oracle": "Database",
    "SQLite": "Database",

    # Cloud & DevOps
    "AWS": "Cloud",
    "Google Cloud": "Cloud",
    "Azure": "Cloud",
    "Docker": "DevOps",
    "Kubernetes": "DevOps",
    "Terraform": "DevOps",
    "Ansible": "DevOps",
    "Jenkins": "DevOps",
    "GitLab CI": "DevOps",
    "GitHub Actions": "DevOps",
    "CircleCI": "DevOps",
    "Nginx": "DevOps",
    "Apache": "DevOps",
    "Linux": "DevOps",
    "Unix": "DevOps",
    "Bash": "DevOps",
    "Shell": "DevOps",
    "Vim": "Tool",
    "Git": "Tool",
    "CI/CD": "DevOps",

    # Data Science / ML
    "Machine Learning": "Data Science",
    "Deep Learning": "Data Science",
    "TensorFlow": "Data Science",
    "PyTorch": "Data Science",
    "Keras": "Data Science",
    "Scikit-learn": "Data Science",
    "Pandas": "Data Science",
    "NumPy": "Data Science",
    "Matplotlib": "Data Science",
    "Seaborn": "Data Science",
    "Plotly": "Data Science",
    "Jupyter": "Data Science",
    "Apache Spark": "Data Science",
    "PySpark": "Data Science",
    "Hadoop": "Data Science",
    "Kafka": "Data Science",
    "Airflow": "Data Science",
    "Tableau": "Data Science",
    "Power BI": "Data Science",
    "Looker": "Data Science",
    "NLP": "Data Science",
    "Computer Vision": "Data Science",
    "LLM": "Data Science",
    "RAG": "Data Science",

    # Mobile
    "Android": "Mobile",
    "iOS": "Mobile",
    "React Native": "Mobile",
    "Flutter": "Mobile",
    "Dart": "Mobile",
    "Xamarin": "Mobile",
    "Swift": "Mobile",
    "Objective-C": "Mobile",
    "Kotlin": "Mobile",

    # Testing
    "Jest": "Testing",
    "Mocha": "Testing",
    "Chai": "Testing",
    "pytest": "Testing",
    "unittest": "Testing",
    "Selenium": "Testing",
    "Cypress": "Testing",
    "Playwright": "Testing",
    "JUnit": "Testing",
    "TestNG": "Testing",

    # Language
    "English": "Language",
    "IELTS": "Language",
    "TOEIC": "Language",

    # Soft skills
    "Teamwork": "Soft Skill",
    "Leadership": "Soft Skill",
    "Problem Solving": "Soft Skill",
    "Communication": "Soft Skill",
    "Agile": "Soft Skill",
    "Scrum": "Soft Skill",
    "Kanban": "Soft Skill",
    "Jira": "Tool",
    "Confluence": "Tool",
}


@dataclass
class Skill:
    """Kỹ năng đã chuẩn hóa từ tin tuyển dụng.

    Attributes:
        skill_name: tên chuẩn hóa (canonical) — ví dụ: "Python", "React"
        original_name: tên gốc trước khi chuẩn hóa — ví dụ: "python3", "ReactJS"
        skill_group: nhóm kỹ năng — Programming Language, Frontend Framework, Backend Framework,
                     Database, Cloud, DevOps, Data Science, Mobile, Testing, Language, Soft Skill, Tool, Other
        required_level: Required | Nice to have | Not specified
        job_id: FK đến JobPosting
    """
    skill_name: str
    original_name: str
    skill_group: str = "Other"
    required_level: str = "Not specified"
    job_id: str = ""

    def __post_init__(self):
        # Normalize skill_name using synonym map
        normalized = self._normalize_skill(self.skill_name)
        if normalized != self.skill_name:
            self.original_name = self.skill_name
            self.skill_name = normalized

        # Infer skill_group if not set or "Other"
        if self.skill_group == "Other" or not self.skill_group:
            self.skill_group = self._infer_group(self.skill_name)

        # Normalize required_level
        self.required_level = self._normalize_level(self.required_level)

    @staticmethod
    def _normalize_skill(name: str) -> str:
        """Apply synonym map to get canonical name."""
        if not name:
            return name
        lower = name.lower().strip()
        return SKILL_SYNONYM_MAP.get(lower, name)

    @staticmethod
    def _infer_group(name: str) -> str:
        """Infer skill group from canonical name."""
        return SKILL_GROUP_MAP.get(name, "Other")

    @staticmethod
    def _normalize_level(level: str) -> str:
        """Normalize required level."""
        if not level:
            return "Not specified"
        lower = level.lower().strip()
        if any(kw in lower for kw in ["required", "bắt buộc", "yêu cầu", "must", "essential"]):
            return "Required"
        if any(kw in lower for kw in ["nice", "ưu tiên", "prefer", "optional", "bonus", "plus"]):
            return "Nice to have"
        return "Not specified"

    def to_dict(self) -> dict:
        return {
            "skill_name": self.skill_name,
            "original_name": self.original_name,
            "skill_group": self.skill_group,
            "required_level": self.required_level,
            "job_id": self.job_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Skill":
        return cls(
            skill_name=data.get("skill_name", ""),
            original_name=data.get("original_name", ""),
            skill_group=data.get("skill_group", "Other"),
            required_level=data.get("required_level", "Not specified"),
            job_id=data.get("job_id", ""),
        )

    def __hash__(self):
        return hash((self.skill_name, self.job_id))

    def __eq__(self, other):
        if not isinstance(other, Skill):
            return False
        return self.skill_name == other.skill_name and self.job_id == other.job_id