import os
import sys
import csv
import json
import math
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def calculate_pearson_and_spearman(x, y):
    n = len(x)
    if n < 2:
        return {"error": "Need at least 2 data points"}

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    diff_x = [val - mean_x for val in x]
    diff_y = [val - mean_y for val in y]

    sum_sq_x = sum(d ** 2 for d in diff_x)
    sum_sq_y = sum(d ** 2 for d in diff_y)

    # Pearson r
    cov = sum(dx * dy for dx, dy in zip(diff_x, diff_y))
    denominator = math.sqrt(sum_sq_x * sum_sq_y)
    r = cov / denominator if denominator > 0 else 0.0

    # Spearman rank correlation
    def get_ranks(seq):
        sorted_indices = sorted(range(len(seq)), key=lambda k: seq[k])
        ranks = [0.0] * len(seq)
        i = 0
        while i < len(seq):
            j = i
            while j < len(seq) - 1 and seq[sorted_indices[j]] == seq[sorted_indices[j + 1]]:
                j += 1
            avg_rank = (i + j + 2) / 2.0
            for k in range(i, j + 1):
                ranks[sorted_indices[k]] = avg_rank
            i = j + 1
        return ranks

    rank_x = get_ranks(x)
    rank_y = get_ranks(y)

    mean_rx = sum(rank_x) / n
    mean_ry = sum(rank_y) / n

    diff_rx = [val - mean_rx for val in rank_x]
    diff_ry = [val - mean_ry for val in rank_y]

    cov_r = sum(dx * dy for dx, dy in zip(diff_rx, diff_ry))
    denom_r = math.sqrt(sum(d ** 2 for d in diff_rx) * sum(d ** 2 for d in diff_ry))
    rho = cov_r / denom_r if denom_r > 0 else 0.0

    # t-statistic for significance
    if abs(r) < 1.0:
        t_stat = r * math.sqrt((n - 2) / (1 - r ** 2))
    else:
        t_stat = float("inf")

    return {
        "sample_size": n,
        "pearson_r": round(r, 4),
        "spearman_rho": round(rho, 4),
        "t_statistic": round(t_stat, 4),
        "clip_mean": round(mean_x, 4),
        "clip_std": round(math.sqrt(sum_sq_x / n), 4),
        "human_mean": round(mean_y, 4),
        "human_std": round(math.sqrt(sum_sq_y / n), 4)
    }

def main():
    csv_path = BASE_DIR / "evidence" / "human_ratings_template.csv"
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])

    if not csv_path.exists():
        print(f"Error: Ratings file not found at {csv_path}")
        sys.exit(1)

    print(f"Loading ratings from: {csv_path}")
    clip_scores = []
    human_ratings = []
    rows = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                score = float(row["clip_relevance_score"])
                rating = float(row["human_rating_1_to_5"])
                clip_scores.append(score)
                human_ratings.append(rating)
                rows.append(row)
            except Exception as e:
                continue

    print(f"Loaded {len(clip_scores)} rated scene pairs.")
    stats = calculate_pearson_and_spearman(clip_scores, human_ratings)

    print("\n--- Correlation Analysis Results ---")
    print(f"Sample Count (N):          {stats['sample_size']}")
    print(f"Pearson Correlation (r):   {stats['pearson_r']}")
    print(f"Spearman Rank (rho):       {stats['spearman_rho']}")
    print(f"CLIP Score Mean:           {stats['clip_mean']} (std: {stats['clip_std']})")
    print(f"Human Rating Mean (1-5):   {stats['human_mean']} (std: {stats['human_std']})")

    out_json = BASE_DIR / "evidence" / "correlation_analysis.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    print(f"\nSaved analysis to: {out_json}")

if __name__ == "__main__":
    main()
