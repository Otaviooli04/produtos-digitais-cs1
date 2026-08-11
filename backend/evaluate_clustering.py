#!/usr/bin/env python3
"""
Avaliação comparativa das estratégias de clustering do sistema de Learning Analytics.

Experimentos:
  1. Comparação das 4 estratégias (principal)
  2. Sensibilidade aos parâmetros HDBSCAN
  3. Escalabilidade por tamanho de turma
  4. Estabilidade via bootstrap

Uso:
  python evaluate_clustering.py                     # todos os experimentos
  python evaluate_clustering.py --exp 1 2           # experimentos específicos
  python evaluate_clustering.py --exp 1 --seed 123  # seed customizado
  python evaluate_clustering.py --exp 4 --bootstrap 100

Saída: backend/results/  (CSVs + plots)
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import time
import warnings
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import entropy as scipy_entropy
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    normalized_mutual_info_score,
    silhouette_score,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hdbscan import HDBSCAN
import hdbscan.validity as hdbscan_validity
from umap import UMAP

from app.ml.cluster import FeatureStrategy, _build_features
from app.engine.static_analyzer import extract_control_flow

warnings.filterwarnings("ignore")

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
PLOTS_DIR = os.path.join(RESULTS_DIR, "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

STRATEGY_LABELS = {
    FeatureStrategy.TFIDF: "tfidf",
    FeatureStrategy.TFIDF_NGRAM: "tfidf_ngram",
    FeatureStrategy.TFIDF_CATEGORY: "tfidf_category",
    FeatureStrategy.TFIDF_BEHAVIORAL: "tfidf_behavioral",
    FeatureStrategy.TFIDF_FUNCTIONAL: "tfidf_functional",
}

ALL_STRATEGIES = list(STRATEGY_LABELS.keys())


# ---------------------------------------------------------------------------
# Mock objects com mesmo contrato do ORM Submission
# ---------------------------------------------------------------------------

@dataclass
class MockTestResult:
    passed: bool


@dataclass
class MockSubmission:
    code: str
    ast_structures: List[str]
    error_category: str
    compile_error: str = ""
    warnings: str = ""
    all_tests_passed: Optional[bool] = None
    test_results: List[MockTestResult] = field(default_factory=list)
    matricula: str = ""
    ast_functions: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Famílias de código sintético com ground truth controlado
# ---------------------------------------------------------------------------

_VARNAMES = ["x", "y", "z", "val", "num", "res", "tmp", "aux", "v", "data"]
_IDXNAMES = ["i", "j", "k", "n", "m", "idx", "cnt", "pos"]


def _vary(template: str, seed: int) -> str:
    rng = random.Random(seed)
    return (
        template
        .replace("{VAR}", rng.choice(_VARNAMES))
        .replace("{IDX}", rng.choice(_IDXNAMES))
    )


# Cada família: templates de código C, estruturas AST, comportamento esperado
FAMILIES: dict = {
    "Correto": {
        "ast": ["for", "printf", "scanf", "assignment"],
        "compile_error": "",
        "all_passed": True,
        "n_passed": 3,
        "n_total": 3,
        "templates": [
            "#include <stdio.h>\nint main() {\n    int {VAR};\n    scanf(\"%d\", &{VAR});\n    printf(\"%d\\n\", {VAR} * 2);\n    return 0;\n}",
            "#include <stdio.h>\nint main() {\n    int {VAR} = 0;\n    scanf(\"%d\", &{VAR});\n    int res = {VAR} + {VAR};\n    printf(\"%d\\n\", res);\n    return 0;\n}",
            "#include <stdio.h>\nint main() {\n    int {VAR}, result;\n    scanf(\"%d\", &{VAR});\n    result = 2 * {VAR};\n    printf(\"%d\\n\", result);\n    return 0;\n}",
            "#include <stdio.h>\nint main() {\n    int {VAR};\n    scanf(\"%d\", &{VAR});\n    {VAR} = {VAR} * 2;\n    printf(\"%d\\n\", {VAR});\n    return 0;\n}",
        ],
    },
    "Erro de Compilação — Variável Não Declarada": {
        "ast": ["printf"],
        "compile_error": "error: undeclared variable",
        "all_passed": False,
        "n_passed": 0,
        "n_total": 3,
        "templates": [
            "int main() {\n    printf(\"%d\\n\", {VAR});\n    return 0;\n}",
            "int main() {\n    int result = {VAR} + 1;\n    printf(\"%d\\n\", result);\n    return 0;\n}",
            "#include <stdio.h>\nint main() {\n    {VAR} = 10;\n    printf(\"%d\\n\", {VAR});\n    return 0;\n}",
            "int main() {\n    for (int {IDX} = 0; {IDX} < {VAR}; {IDX}++) printf(\"%d\\n\", {IDX});\n    return 0;\n}",
        ],
    },
    "Loop Infinito / Timeout": {
        "ast": ["while", "assignment"],
        "compile_error": "timeout",
        "all_passed": False,
        "n_passed": 0,
        "n_total": 3,
        "templates": [
            "int main() {\n    int {VAR} = 0;\n    while (1) { {VAR}++; }\n    return 0;\n}",
            "#include <stdio.h>\nint main() {\n    int {IDX} = 0;\n    while ({IDX} >= 0) { {IDX}++; }\n    printf(\"%d\\n\", {IDX});\n    return 0;\n}",
            "int main() {\n    int {VAR} = 1;\n    while ({VAR} > 0) { {VAR} = {VAR} + 1; }\n    return 0;\n}",
            "#include <stdio.h>\nint main() {\n    for (int {IDX} = 0; {IDX} != -1; {IDX}++) {}\n    return 0;\n}",
        ],
    },
    "Acesso Indevido à Memória": {
        "ast": ["pointer", "assignment"],
        "compile_error": "segmentation fault",
        "all_passed": False,
        "n_passed": 0,
        "n_total": 3,
        "templates": [
            "int main() {\n    int *{VAR} = 0;\n    *{VAR} = 42;\n    return 0;\n}",
            "#include <stdio.h>\nint main() {\n    int arr[5];\n    int {VAR} = arr[10];\n    printf(\"%d\\n\", {VAR});\n    return 0;\n}",
            "int main() {\n    int *{VAR} = (int*)0;\n    printf(\"%d\\n\", *{VAR});\n    return 0;\n}",
            "#include <stdio.h>\nint main() {\n    char *{VAR} = 0;\n    *{VAR} = 'a';\n    return 0;\n}",
        ],
    },
    "Saída Incorreta — Erro de Lógica": {
        "ast": ["printf", "scanf", "assignment"],
        "compile_error": "",
        "all_passed": False,
        "n_passed": 1,
        "n_total": 3,
        "templates": [
            "#include <stdio.h>\nint main() {\n    int {VAR};\n    scanf(\"%d\", &{VAR});\n    printf(\"%d\\n\", {VAR} + 2);\n    return 0;\n}",
            "#include <stdio.h>\nint main() {\n    int {VAR};\n    scanf(\"%d\", &{VAR});\n    printf(\"%d\\n\", {VAR} / 2);\n    return 0;\n}",
            "#include <stdio.h>\nint main() {\n    int {VAR};\n    scanf(\"%d\", &{VAR});\n    {VAR} = {VAR} - {VAR};\n    printf(\"%d\\n\", {VAR});\n    return 0;\n}",
            "#include <stdio.h>\nint main() {\n    int {VAR} = 0;\n    scanf(\"%d\", &{VAR});\n    printf(\"%d\\n\", {VAR} + {VAR} + 1);\n    return 0;\n}",
        ],
    },
    # --- Famílias de FUNÇÃO: mesmo error_category, diferem só na estrutura ---
    # Demonstram o valor das features de função: categoria/comportamento não as
    # separam (ambas compilam, passam e têm a mesma categoria); só a organização
    # em funções (n_funções, recursão) distingue.
    "Solução Monolítica (tudo no main)": {
        "ast": [],
        "error_category": "Lógica Estrutural Válida",
        "compile_error": "",
        "all_passed": True,
        "n_passed": 3,
        "n_total": 3,
        "templates": [
            "#include <stdio.h>\nint main() {\n    int {VAR}, {IDX}, fat = 1;\n    scanf(\"%d\", &{VAR});\n    for ({IDX} = 1; {IDX} <= {VAR}; {IDX}++) {\n        fat = fat * {IDX};\n    }\n    printf(\"%d\\n\", fat);\n    return 0;\n}",
            "#include <stdio.h>\nint main() {\n    int {VAR}, {IDX} = 1, res = 1;\n    scanf(\"%d\", &{VAR});\n    while ({IDX} <= {VAR}) {\n        res = res * {IDX};\n        {IDX}++;\n    }\n    printf(\"%d\\n\", res);\n    return 0;\n}",
            "#include <stdio.h>\nint main() {\n    int {VAR}, {IDX}, fat = 1;\n    scanf(\"%d\", &{VAR});\n    for ({IDX} = {VAR}; {IDX} > 1; {IDX}--) fat = fat * {IDX};\n    printf(\"%d\\n\", fat);\n    return 0;\n}",
        ],
    },
    "Função Recursiva": {
        "ast": [],
        "error_category": "Lógica Estrutural Válida",
        "compile_error": "",
        "all_passed": True,
        "n_passed": 3,
        "n_total": 3,
        "templates": [
            "#include <stdio.h>\nint fat(int {IDX}) {\n    if ({IDX} <= 1) return 1;\n    return {IDX} * fat({IDX} - 1);\n}\nint main() {\n    int {VAR};\n    scanf(\"%d\", &{VAR});\n    printf(\"%d\\n\", fat({VAR}));\n    return 0;\n}",
            "#include <stdio.h>\nint fatorial(int {VAR}) {\n    if ({VAR} == 0) return 1;\n    return {VAR} * fatorial({VAR} - 1);\n}\nint main() {\n    int {IDX};\n    scanf(\"%d\", &{IDX});\n    printf(\"%d\\n\", fatorial({IDX}));\n    return 0;\n}",
            "#include <stdio.h>\nint fat(int {IDX}) {\n    if ({IDX} <= 1) {\n        return 1;\n    }\n    return {IDX} * fat({IDX} - 1);\n}\nint main() {\n    int {VAR};\n    scanf(\"%d\", &{VAR});\n    printf(\"%d\\n\", fat({VAR}));\n    return 0;\n}",
        ],
    },
}

FAMILY_NAMES = list(FAMILIES.keys())


def generate_dataset(
    n_per_family: int,
    seed: int = 42,
    families: Optional[List[str]] = None,
) -> Tuple[List[MockSubmission], List[str]]:
    """Gera dataset sintético com ground truth controlado. Retorna (submissions, labels)."""
    rng = random.Random(seed)
    selected = families or FAMILY_NAMES
    submissions, ground_truth = [], []

    for family_name in selected:
        fam = FAMILIES[family_name]
        templates = fam["templates"]
        for i in range(n_per_family):
            code = _vary(templates[i % len(templates)], seed=rng.randint(0, 99999))
            n_p, n_t = fam["n_passed"], fam["n_total"]
            test_results = [MockTestResult(passed=(j < n_p)) for j in range(n_t)]
            # AST derivado do parser REAL (tree-sitter): fiel à produção, inclusive
            # extração parcial em código que não compila. error_category pode ser
            # sobrescrito pela família (p/ famílias que diferem só na estrutura).
            static = extract_control_flow(code)
            submissions.append(MockSubmission(
                code=code,
                ast_structures=static.get("structures", []),
                ast_functions=static.get("functions", []),
                error_category=fam.get("error_category", family_name),
                compile_error=fam["compile_error"],
                all_tests_passed=fam["all_passed"],
                test_results=test_results,
                matricula=f"sub_{len(submissions):04d}",
            ))
            ground_truth.append(family_name)

    combined = list(zip(submissions, ground_truth))
    rng.shuffle(combined)
    submissions, ground_truth = zip(*combined)
    return list(submissions), list(ground_truth)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(
    submissions: List[MockSubmission],
    strategy: FeatureStrategy,
    umap_seed: int = 42,
    min_cluster_size: int = 2,
    min_samples: int = 1,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Features → UMAP → HDBSCAN. Retorna (features, embedded, labels)."""
    n = len(submissions)
    codes = [s.code for s in submissions]
    ast_lists = [s.ast_structures for s in submissions]

    features = _build_features(codes, ast_lists, submissions, strategy)

    n_components = min(5, n - 1)
    n_neighbors = min(15, n - 1)
    umap_init = "random" if n < 10 else "spectral"

    embedded = UMAP(
        n_components=n_components,
        n_neighbors=n_neighbors,
        random_state=umap_seed,
        min_dist=0.0,
        init=umap_init,
    ).fit_transform(features)

    labels = HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
    ).fit_predict(embedded)

    return features, embedded, labels


# ---------------------------------------------------------------------------
# Métricas
# ---------------------------------------------------------------------------

def compute_metrics(
    embedded: np.ndarray,
    labels: np.ndarray,
    ground_truth: List[str],
    elapsed: float = 0.0,
) -> dict:
    """
    Calcula todas as métricas de avaliação de clustering.

    Internas:  Silhouette, DBI, CHI, DBCV
    Externas:  Purity, Entropy, ARI, NMI  (requerem ground truth)
    Operacionais: n_clusters, noise_ratio, tempo
    """
    n_total = len(labels)
    mask = labels != -1
    n_clustered = int(mask.sum())
    noise_ratio = 1.0 - (n_clustered / n_total)
    unique_clusters = sorted(set(labels[mask])) if mask.any() else []
    n_clusters = len(unique_clusters)

    m: dict = {
        "n_total": n_total,
        "n_clusters": n_clusters,
        "noise_ratio": round(noise_ratio, 4),
        "silhouette": None,
        "dbi": None,
        "chi": None,
        "dbcv": None,
        "purity": None,
        "entropy_mean": None,
        "ari": None,
        "nmi": None,
        "tempo_s": round(elapsed, 3),
    }

    if n_clustered < 2 or n_clusters < 2:
        return m

    emb_c = embedded[mask]
    lbl_c = labels[mask]
    gt_c = [ground_truth[i] for i in range(n_total) if mask[i]]

    # --- Internas ---
    m["silhouette"] = round(float(silhouette_score(emb_c, lbl_c)), 4)
    m["dbi"] = round(float(davies_bouldin_score(emb_c, lbl_c)), 4)
    m["chi"] = round(float(calinski_harabasz_score(emb_c, lbl_c)), 4)

    try:
        dbcv_val = hdbscan_validity.validity_index(
            emb_c.astype(np.float64), lbl_c, metric="euclidean"
        )
        m["dbcv"] = round(float(dbcv_val), 4)
    except Exception:
        pass

    # --- Externas ---
    purity_sum = 0
    entropies = []
    for cid in unique_clusters:
        cluster_gt = [gt_c[i] for i, l in enumerate(lbl_c) if l == cid]
        counts = Counter(cluster_gt)
        purity_sum += max(counts.values())
        probs = np.array(list(counts.values())) / len(cluster_gt)
        entropies.append(float(scipy_entropy(probs, base=2)))

    m["purity"] = round(purity_sum / n_clustered, 4)
    m["entropy_mean"] = round(float(np.mean(entropies)), 4)

    gt_unique = sorted(set(ground_truth))
    gt_int = [gt_unique.index(g) for g in gt_c]
    m["ari"] = round(float(adjusted_rand_score(gt_int, lbl_c)), 4)
    m["nmi"] = round(float(normalized_mutual_info_score(gt_int, lbl_c)), 4)

    return m


def weighted_score(m: dict) -> float:
    """
    Score composto para ranquear estratégias.
    Pesos refletem objetivo pedagógico: purity > dbcv > nmi > noise.
    """
    def safe(v, default=0.0):
        return v if v is not None else default

    score = (
        0.30 * safe(m["purity"])
        + 0.25 * safe(m["dbcv"])
        + 0.20 * safe(m["nmi"])
        + 0.15 * (1.0 - safe(m["noise_ratio"]))
        + 0.10 * safe(m["silhouette"])
    )
    return round(score, 4)


# ---------------------------------------------------------------------------
# Experimento 1 — Comparação das 4 estratégias
# ---------------------------------------------------------------------------

def experiment_1(n_per_family: int = 8, seed: int = 42) -> pd.DataFrame:
    print("\n=== Experimento 1: Comparação das 4 estratégias ===")
    print(f"  {len(FAMILY_NAMES)} famílias × {n_per_family} submissões = {len(FAMILY_NAMES) * n_per_family} total\n")

    submissions, ground_truth = generate_dataset(n_per_family=n_per_family, seed=seed)
    rows = []

    for strategy in ALL_STRATEGIES:
        label = STRATEGY_LABELS[strategy]
        print(f"  Rodando {label}...", end=" ", flush=True)
        t0 = time.perf_counter()
        _, embedded, labels = run_pipeline(submissions, strategy, umap_seed=seed)
        elapsed = time.perf_counter() - t0

        m = compute_metrics(embedded, labels, ground_truth, elapsed)
        m["estrategia"] = label
        m["score"] = weighted_score(m)
        rows.append(m)
        print(f"clusters={m['n_clusters']}, silhouette={m['silhouette']}, purity={m['purity']}, score={m['score']}")

    df = pd.DataFrame(rows).set_index("estrategia")
    df.to_csv(os.path.join(RESULTS_DIR, "exp1_estrategias.csv"))
    _plot_exp1(df)
    print(f"\n  Salvo em results/exp1_estrategias.csv")
    return df


def _plot_exp1(df: pd.DataFrame) -> None:
    metrics_to_plot = ["silhouette", "dbcv", "purity", "nmi", "noise_ratio", "n_clusters"]
    titles = ["Silhouette ↑", "DBCV ↑", "Purity ↑", "NMI ↑", "Noise Ratio ↓", "Nº Clusters"]

    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    axes = axes.flatten()
    colors = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]

    for ax, metric, title in zip(axes, metrics_to_plot, titles):
        vals = [df.loc[STRATEGY_LABELS[s], metric] if metric in df.columns else 0 for s in ALL_STRATEGIES]
        vals = [v if v is not None else 0 for v in vals]
        bars = ax.bar([STRATEGY_LABELS[s] for s in ALL_STRATEGIES], vals, color=colors)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_xticklabels([STRATEGY_LABELS[s] for s in ALL_STRATEGIES], rotation=25, ha="right", fontsize=8)
        ax.bar_label(bars, fmt="%.3f", fontsize=7, padding=2)
        ax.set_ylim(0, max(max(vals) * 1.2, 0.1))

    fig.suptitle("Experimento 1 — Comparação das Estratégias de Clustering", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "exp1_comparacao.png"), dpi=150, bbox_inches="tight")
    plt.close()

    # Score composto
    fig, ax = plt.subplots(figsize=(7, 4))
    scores = [df.loc[STRATEGY_LABELS[s], "score"] if "score" in df.columns else 0 for s in ALL_STRATEGIES]
    scores = [v if v is not None else 0 for v in scores]
    bars = ax.bar([STRATEGY_LABELS[s] for s in ALL_STRATEGIES], scores, color=colors)
    ax.bar_label(bars, fmt="%.4f", padding=3)
    ax.set_title("Score Composto Ponderado (Purity×0.3 + DBCV×0.25 + NMI×0.2 + ...)", fontsize=10)
    ax.set_ylabel("Score")
    ax.set_xticklabels([STRATEGY_LABELS[s] for s in ALL_STRATEGIES], rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "exp1_score_composto.png"), dpi=150, bbox_inches="tight")
    plt.close()


# ---------------------------------------------------------------------------
# Experimento 2 — Sensibilidade aos parâmetros HDBSCAN
# ---------------------------------------------------------------------------

def experiment_2(
    strategy: FeatureStrategy = FeatureStrategy.TFIDF_BEHAVIORAL,
    n_per_family: int = 8,
    seed: int = 42,
) -> pd.DataFrame:
    label = STRATEGY_LABELS[strategy]
    print(f"\n=== Experimento 2: Sensibilidade HDBSCAN (estratégia={label}) ===")

    submissions, ground_truth = generate_dataset(n_per_family=n_per_family, seed=seed)

    mcs_values = [2, 3, 5, 7, 10]
    ms_values = [1, 2, 3, 5]
    rows = []

    total = len(mcs_values) * len(ms_values)
    done = 0
    for mcs in mcs_values:
        for ms in ms_values:
            _, embedded, labels = run_pipeline(submissions, strategy, umap_seed=seed,
                                               min_cluster_size=mcs, min_samples=ms)
            m = compute_metrics(embedded, labels, ground_truth)
            rows.append({
                "min_cluster_size": mcs,
                "min_samples": ms,
                "n_clusters": m["n_clusters"],
                "silhouette": m["silhouette"],
                "purity": m["purity"],
                "noise_ratio": m["noise_ratio"],
                "dbcv": m["dbcv"],
            })
            done += 1
            print(f"  [{done:2d}/{total}] mcs={mcs}, ms={ms} → clusters={m['n_clusters']}, silhouette={m['silhouette']}, noise={m['noise_ratio']}")

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(RESULTS_DIR, "exp2_hdbscan_params.csv"), index=False)
    _plot_exp2(df, label)
    print(f"  Salvo em results/exp2_hdbscan_params.csv")
    return df


def _plot_exp2(df: pd.DataFrame, strategy_label: str) -> None:
    for metric in ["silhouette", "purity", "noise_ratio"]:
        pivot = df.pivot(index="min_cluster_size", columns="min_samples", values=metric)
        fig, ax = plt.subplots(figsize=(6, 4))
        im = ax.imshow(pivot.values, aspect="auto", cmap="RdYlGn" if metric != "noise_ratio" else "RdYlGn_r")
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels([f"ms={v}" for v in pivot.columns])
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels([f"mcs={v}" for v in pivot.index])
        ax.set_xlabel("min_samples")
        ax.set_ylabel("min_cluster_size")
        ax.set_title(f"Exp2 — {metric} ({strategy_label})", fontweight="bold")
        for i in range(len(pivot.index)):
            for j in range(len(pivot.columns)):
                val = pivot.values[i, j]
                ax.text(j, i, f"{val:.3f}" if val is not None else "—",
                        ha="center", va="center", fontsize=8,
                        color="black")
        plt.colorbar(im, ax=ax)
        plt.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR, f"exp2_heatmap_{metric}.png"), dpi=150, bbox_inches="tight")
        plt.close()


# ---------------------------------------------------------------------------
# Experimento 3 — Escalabilidade por tamanho de turma
# ---------------------------------------------------------------------------

def experiment_3(seed: int = 42) -> pd.DataFrame:
    print("\n=== Experimento 3: Escalabilidade por tamanho de turma ===")

    cenarios = [
        ("Pequena",  15),
        ("Média",    35),
        ("Grande",   60),
        ("Extra",   100),
    ]
    rows = []
    n_families = len(FAMILY_NAMES)

    for nome, n_alunos in cenarios:
        n_per_family = max(2, n_alunos // n_families)
        submissions, ground_truth = generate_dataset(n_per_family=n_per_family, seed=seed)
        print(f"\n  {nome} ({len(submissions)} submissões):")

        for strategy in ALL_STRATEGIES:
            label = STRATEGY_LABELS[strategy]
            t0 = time.perf_counter()
            _, embedded, labels = run_pipeline(submissions, strategy, umap_seed=seed)
            elapsed = time.perf_counter() - t0
            m = compute_metrics(embedded, labels, ground_truth, elapsed)
            rows.append({
                "cenario": nome,
                "n_total": len(submissions),
                "estrategia": label,
                "n_clusters": m["n_clusters"],
                "silhouette": m["silhouette"],
                "purity": m["purity"],
                "noise_ratio": m["noise_ratio"],
                "nmi": m["nmi"],
                "tempo_s": m["tempo_s"],
            })
            print(f"    {label:22s} → clusters={m['n_clusters']}, silhouette={m['silhouette']}, purity={m['purity']}, tempo={m['tempo_s']}s")

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(RESULTS_DIR, "exp3_escalabilidade.csv"), index=False)
    _plot_exp3(df)
    print(f"\n  Salvo em results/exp3_escalabilidade.csv")
    return df


def _plot_exp3(df: pd.DataFrame) -> None:
    metrics = ["silhouette", "purity", "noise_ratio", "tempo_s"]
    ylabels = ["Silhouette ↑", "Purity ↑", "Noise Ratio ↓", "Tempo (s)"]
    colors = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]
    strategy_names = [STRATEGY_LABELS[s] for s in ALL_STRATEGIES]
    n_sizes = sorted(df["n_total"].unique())

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes = axes.flatten()

    for ax, metric, ylabel in zip(axes, metrics, ylabels):
        for strat, color in zip(strategy_names, colors):
            sub = df[df["estrategia"] == strat].sort_values("n_total")
            vals = sub[metric].fillna(0).tolist()
            ax.plot(sub["n_total"].tolist(), vals, marker="o", label=strat, color=color, linewidth=1.8)
        ax.set_xlabel("Nº de Submissões")
        ax.set_ylabel(ylabel)
        ax.set_title(ylabel, fontweight="bold")
        ax.set_xticks(n_sizes)
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)

    fig.suptitle("Experimento 3 — Escalabilidade por Tamanho de Turma", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "exp3_escalabilidade.png"), dpi=150, bbox_inches="tight")
    plt.close()


# ---------------------------------------------------------------------------
# Experimento 4 — Estabilidade via Bootstrap
# ---------------------------------------------------------------------------

def experiment_4(
    strategy: FeatureStrategy = FeatureStrategy.TFIDF_BEHAVIORAL,
    n_per_family: int = 8,
    seed: int = 42,
    n_bootstrap: int = 50,
    sample_ratio: float = 0.80,
) -> pd.DataFrame:
    label = STRATEGY_LABELS[strategy]
    print(f"\n=== Experimento 4: Estabilidade Bootstrap (estratégia={label}, N={n_bootstrap}) ===")

    submissions, ground_truth = generate_dataset(n_per_family=n_per_family, seed=seed)
    rng = random.Random(seed)

    # Coleta (indices_usados, labels_por_indice) de cada rodada
    runs: List[dict] = []
    for b in range(n_bootstrap):
        sample_size = int(len(submissions) * sample_ratio)
        indices = sorted(rng.sample(range(len(submissions)), sample_size))
        sub_sample = [submissions[i] for i in indices]
        gt_sample = [ground_truth[i] for i in indices]

        umap_seed_b = rng.randint(0, 99999)
        try:
            _, embedded, labels = run_pipeline(sub_sample, strategy, umap_seed=umap_seed_b)
        except Exception:
            continue

        runs.append({"indices": indices, "labels": labels, "gt": gt_sample})

        if (b + 1) % 10 == 0:
            print(f"  Bootstrap {b+1}/{n_bootstrap}...")

    # Calcula ARI entre pares consecutivos via pontos comuns
    ari_scores = []
    for i in range(len(runs) - 1):
        r1, r2 = runs[i], runs[i + 1]
        common_idx_r1 = {idx: pos for pos, idx in enumerate(r1["indices"])}
        common_idx_r2 = {idx: pos for pos, idx in enumerate(r2["indices"])}
        shared = set(common_idx_r1) & set(common_idx_r2)
        if len(shared) < 2:
            continue
        lbl1 = np.array([r1["labels"][common_idx_r1[idx]] for idx in shared])
        lbl2 = np.array([r2["labels"][common_idx_r2[idx]] for idx in shared])
        if len(set(lbl1)) < 2 or len(set(lbl2)) < 2:
            continue
        ari_scores.append(adjusted_rand_score(lbl1, lbl2))

    if not ari_scores:
        print("  AVISO: nenhum par válido para ARI (clusters insuficientes).")
        return pd.DataFrame()

    ari_arr = np.array(ari_scores)
    summary = {
        "estrategia": label,
        "n_bootstrap": n_bootstrap,
        "sample_ratio": sample_ratio,
        "ari_mean": round(float(ari_arr.mean()), 4),
        "ari_std": round(float(ari_arr.std()), 4),
        "ari_min": round(float(ari_arr.min()), 4),
        "ari_max": round(float(ari_arr.max()), 4),
        "ari_q25": round(float(np.percentile(ari_arr, 25)), 4),
        "ari_q75": round(float(np.percentile(ari_arr, 75)), 4),
    }
    print(f"\n  ARI estabilidade: mean={summary['ari_mean']} ± {summary['ari_std']}")
    print(f"  [min={summary['ari_min']}, Q25={summary['ari_q25']}, Q75={summary['ari_q75']}, max={summary['ari_max']}]")

    df_scores = pd.DataFrame({"ari": ari_arr})
    df_scores.to_csv(os.path.join(RESULTS_DIR, "exp4_bootstrap_scores.csv"), index=False)
    pd.DataFrame([summary]).to_csv(os.path.join(RESULTS_DIR, "exp4_bootstrap_summary.csv"), index=False)
    _plot_exp4(ari_arr, label, summary)
    print(f"  Salvo em results/exp4_bootstrap_*.csv")
    return df_scores


def _plot_exp4(ari_scores: np.ndarray, strategy_label: str, summary: dict) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))

    ax1.hist(ari_scores, bins=15, color="#4C72B0", edgecolor="white", alpha=0.85)
    ax1.axvline(summary["ari_mean"], color="red", linestyle="--", label=f"μ={summary['ari_mean']:.3f}")
    ax1.set_xlabel("ARI entre rodadas consecutivas")
    ax1.set_ylabel("Frequência")
    ax1.set_title("Distribuição ARI (Bootstrap)", fontweight="bold")
    ax1.legend()

    ax2.boxplot(ari_scores, vert=True, patch_artist=True,
                boxprops=dict(facecolor="#4C72B0", alpha=0.7))
    ax2.set_ylabel("ARI")
    ax2.set_xticks([1])
    ax2.set_xticklabels([strategy_label])
    ax2.set_title(f"Estabilidade Bootstrap\nN={summary['n_bootstrap']}, ratio={summary['sample_ratio']}", fontweight="bold")
    ax2.grid(True, axis="y", alpha=0.4)

    plt.suptitle(f"Experimento 4 — Estabilidade ({strategy_label})", fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "exp4_estabilidade.png"), dpi=150, bbox_inches="tight")
    plt.close()


# ---------------------------------------------------------------------------
# Bônus: scatter UMAP 2D por estratégia
# ---------------------------------------------------------------------------

def plot_umap_scatter(n_per_family: int = 8, seed: int = 42) -> None:
    print("\n=== Bônus: UMAP 2D scatter por estratégia ===")
    submissions, ground_truth = generate_dataset(n_per_family=n_per_family, seed=seed)
    gt_unique = sorted(set(ground_truth))
    cmap = plt.cm.get_cmap("tab10", len(gt_unique))
    gt_color = {fam: cmap(i) for i, fam in enumerate(gt_unique)}

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for ax, strategy in zip(axes, ALL_STRATEGIES):
        label = STRATEGY_LABELS[strategy]
        codes = [s.code for s in submissions]
        ast_lists = [s.ast_structures for s in submissions]
        features = _build_features(codes, ast_lists, submissions, strategy)

        n = len(submissions)
        n_neighbors = min(15, n - 1)
        umap_init = "random" if n < 10 else "spectral"
        viz = UMAP(n_components=2, n_neighbors=n_neighbors, random_state=seed, init=umap_init).fit_transform(features)

        for fam in gt_unique:
            idxs = [i for i, g in enumerate(ground_truth) if g == fam]
            ax.scatter(viz[idxs, 0], viz[idxs, 1], c=[gt_color[fam]], label=fam[:20], s=40, alpha=0.8)

        ax.set_title(label, fontweight="bold", fontsize=10)
        ax.legend(fontsize=6, loc="upper right")
        ax.set_xlabel("UMAP-1")
        ax.set_ylabel("UMAP-2")

    fig.suptitle("UMAP 2D — Ground Truth por Família de Erro", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "bonus_umap_scatter.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Salvo em results/plots/bonus_umap_scatter.png")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _print_summary(dfs: dict) -> None:
    print("\n" + "=" * 60)
    print("RESUMO DOS RESULTADOS")
    print("=" * 60)
    if "exp1" in dfs and dfs["exp1"] is not None:
        df = dfs["exp1"]
        if "score" in df.columns:
            best = df["score"].idxmax()
            print(f"\nMelhor estratégia (score composto): {best}")
            print(df[["n_clusters", "silhouette", "purity", "nmi", "noise_ratio", "score"]].to_string())
    print(f"\nArquivos gerados em: {RESULTS_DIR}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Avaliação de estratégias de clustering")
    parser.add_argument("--exp", nargs="+", type=int, choices=[1, 2, 3, 4],
                        help="Experimentos a rodar (default: todos)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed global")
    parser.add_argument("--n-per-family", type=int, default=8,
                        help="Submissões por família de erro (default: 8)")
    parser.add_argument("--bootstrap", type=int, default=50,
                        help="Iterações de bootstrap no experimento 4 (default: 50)")
    parser.add_argument("--strategy-exp2", type=str, default="tfidf_behavioral",
                        choices=list(STRATEGY_LABELS.values()),
                        help="Estratégia para experimento 2 e 4 (default: tfidf_behavioral)")
    parser.add_argument("--scatter", action="store_true",
                        help="Gerar scatter UMAP 2D por estratégia")
    args = parser.parse_args()

    exps = args.exp or [1, 2, 3, 4]
    strategy_map = {v: k for k, v in STRATEGY_LABELS.items()}
    strategy_e24 = strategy_map[args.strategy_exp2]

    print(f"Seed: {args.seed} | n_per_family: {args.n_per_family} | Experimentos: {exps}")
    print(f"Output: {RESULTS_DIR}\n")

    dfs = {}

    if 1 in exps:
        dfs["exp1"] = experiment_1(n_per_family=args.n_per_family, seed=args.seed)

    if 2 in exps:
        dfs["exp2"] = experiment_2(strategy=strategy_e24, n_per_family=args.n_per_family, seed=args.seed)

    if 3 in exps:
        dfs["exp3"] = experiment_3(seed=args.seed)

    if 4 in exps:
        dfs["exp4"] = experiment_4(
            strategy=strategy_e24,
            n_per_family=args.n_per_family,
            seed=args.seed,
            n_bootstrap=args.bootstrap,
        )

    if args.scatter:
        plot_umap_scatter(n_per_family=args.n_per_family, seed=args.seed)

    _print_summary(dfs)


if __name__ == "__main__":
    main()
