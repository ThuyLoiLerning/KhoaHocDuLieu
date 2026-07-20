import pandas as pd
import numpy as np

df = pd.read_parquet('data/processed/combined_20260720_205842.parquet')

print("=== CHECKLIST VERIFICATION ===")
print()

# J1: Raw + processed data
print(f"[J1] Rows: {df.shape[0]} (req >= 1000)")
print(f"[J1] Cols: {df.shape[1]} (req >= 12)")
print(f"[J1] Cities: {sorted(df['city'].unique())}")

# Salary
print()
print("=== SALARY ===")
print(f"salary_mid NaN: {df['salary_mid'].isna().sum()}/{len(df)} = {df['salary_mid'].isna().mean()*100:.1f}%")
print(f"salary_min NaN: {df['salary_min'].isna().sum()}/{len(df)}")
print(f"salary_max NaN: {df['salary_max'].isna().sum()}/{len(df)}")
print(f"salary_hidden: {df['salary_hidden'].sum()}")

# Skills
print()
print("=== SKILLS ===")
print(f"Jobs with skills: {df['skills'].notna().sum()}/{len(df)}")
print(f"Skill groups: {df['skill_groups'].explode().dropna().unique() if df['skill_groups'].notna().any() else 'N/A'}")

# Experience
print()
print("=== EXPERIENCE ===")
print(f"Exp bins: {df['experience_bin'].value_counts().to_dict()}")

# City
print()
print("=== CITY ===")
print(df['city'].value_counts().to_dict())

# Null rates
print()
print("=== NULL RATES ===")
null_pct = df.isna().mean().sort_values(ascending=False)
for col, pct in null_pct[null_pct > 0].items():
    print(f"  {col}: {pct*100:.1f}%")

# Sources
print()
print("=== SOURCES ===")
print(f"source_site: {df['source_site'].value_counts().to_dict()}")

print()
print("DONE")
