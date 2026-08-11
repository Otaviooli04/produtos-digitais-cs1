"""
Compara as 4 estratégias de features de clustering para uma questão.

Uso:
    cd backend
    source venv/bin/activate
    python scripts/compare_strategies.py --question_id 1 --out comparacao.png
"""
from __future__ import annotations

import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.ml.cluster import FeatureStrategy, cluster_question

STRATEGIES = [
    FeatureStrategy.TFIDF,
    FeatureStrategy.TFIDF_NGRAM,
    FeatureStrategy.TFIDF_CATEGORY,
    FeatureStrategy.TFIDF_BEHAVIORAL,
]

TITLES = {
    FeatureStrategy.TFIDF: "TF-IDF baseline",
    FeatureStrategy.TFIDF_NGRAM: "TF-IDF + bigrams",
    FeatureStrategy.TFIDF_CATEGORY: "TF-IDF + categoria",
    FeatureStrategy.TFIDF_BEHAVIORAL: "TF-IDF + comportamental",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--question_id", type=int, required=True)
    parser.add_argument("--out", default="comparacao_estrategias.png")
    args = parser.parse_args()

    engine = create_engine(os.environ["DATABASE_URL"])
    Session = sessionmaker(bind=engine)

    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    fig.suptitle(f"Comparação de Estratégias — Questão {args.question_id}", fontsize=14)

    for ax, strategy in zip(axes.flat, STRATEGIES):
        db = Session()
        try:
            result = cluster_question(args.question_id, db, strategy=strategy)
        finally:
            db.close()

        if result is None:
            ax.set_title(f"{TITLES[strategy]}\n(submissões insuficientes)")
            ax.axis("off")
            continue

        xs = np.array([p["x"] for p in result.scatter])
        ys = np.array([p["y"] for p in result.scatter])
        labels = np.array([p["cluster_id"] for p in result.scatter])

        unique = sorted(set(labels))
        cmap = plt.cm.get_cmap("tab10", len(unique))
        color_map = {lbl: cmap(i) for i, lbl in enumerate(unique)}
        colors = [color_map[l] for l in labels]

        ax.scatter(xs, ys, c=colors, s=40, alpha=0.8, edgecolors="none")

        sil = f"{result.silhouette:.3f}" if result.silhouette is not None else "N/A"
        n_clusters = len([l for l in unique if l != -1])
        n_outliers = int((labels == -1).sum())
        ax.set_title(
            f"{TITLES[strategy]}\nSilhouette={sil}  clusters={n_clusters}  outliers={n_outliers}",
            fontsize=10,
        )
        ax.set_xlabel("UMAP-1")
        ax.set_ylabel("UMAP-2")

    plt.tight_layout()
    plt.savefig(args.out, dpi=150)
    print(f"Salvo em: {args.out}")


if __name__ == "__main__":
    main()
