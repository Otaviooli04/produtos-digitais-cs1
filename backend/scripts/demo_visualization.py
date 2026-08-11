"""
Gera visualização comparativa das 4 estratégias de clustering com dados sintéticos.
Não precisa de banco de dados.

Uso:
    cd backend
    source venv/bin/activate
    python scripts/demo_visualization.py --out comparacao_demo.png
"""
from __future__ import annotations

import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from hdbscan import HDBSCAN
from sklearn.metrics import silhouette_score
from umap import UMAP

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.ml.cluster import FeatureStrategy, _build_features


# ---------------------------------------------------------------------------
# Dados sintéticos
# ---------------------------------------------------------------------------

class FakeTestResult:
    def __init__(self, passed: bool):
        self.passed = passed


class FakeSub:
    def __init__(self, code, ast_structures, error_category, compile_error, passed_fraction):
        self.code = code
        self.ast_structures = ast_structures
        self.error_category = error_category
        self.compile_error = compile_error
        n_tc = 5
        n_pass = round(passed_fraction * n_tc)
        self.test_results = [FakeTestResult(i < n_pass) for i in range(n_tc)]


def _make_dataset():
    subs = []

    # Grupo 1 — solução correta com for (5 submissões)
    for_codes = [
        "int main(){int i,s=0;for(i=1;i<=10;i++)s+=i;printf(\"%d\\n\",s);}",
        "int main(){int i,soma=0;for(i=1;i<=10;i++)soma=soma+i;printf(\"%d\\n\",soma);}",
        "int main(){int n=10,i,res=0;for(i=1;i<=n;i++)res+=i;printf(\"%d\\n\",res);}",
        "int main(){int soma=0,i;for(i=1;i<=10;i++){soma+=i;}printf(\"%d\\n\",soma);}",
        "int main(){int total=0;for(int i=1;i<=10;i++)total+=i;printf(\"%d\\n\",total);}",
    ]
    for c in for_codes:
        subs.append(FakeSub(c, ["For"], "Correto", "", 1.0))

    # Grupo 2 — solução correta com while (5 submissões)
    while_codes = [
        "int main(){int i=1,s=0;while(i<=10){s+=i;i++;}printf(\"%d\\n\",s);}",
        "int main(){int i=1,soma=0;while(i<=10){soma+=i;i++;}printf(\"%d\\n\",soma);}",
        "int main(){int cnt=1,acc=0;while(cnt<=10){acc=acc+cnt;cnt=cnt+1;}printf(\"%d\\n\",acc);}",
        "int main(){int x=1,total=0;while(x<=10){total+=x;x++;}printf(\"%d\\n\",total);}",
        "int main(){int val=1,result=0;while(val<=10)result+=val++;printf(\"%d\\n\",result);}",
    ]
    for c in while_codes:
        subs.append(FakeSub(c, ["While"], "Correto", "", 1.0))

    # Grupo 3 — saída incorreta: lógica errada (5 submissões)
    wrong_codes = [
        "int main(){int i,s=0;for(i=0;i<=10;i++)s+=i;printf(\"%d\\n\",s);}",
        "int main(){int i,s=1;for(i=1;i<=10;i++)s+=i;printf(\"%d\\n\",s);}",
        "int main(){int i,s=0;for(i=1;i<10;i++)s+=i;printf(\"%d\\n\",s);}",
        "int main(){int i,s=0;for(i=1;i<=10;i++)s*=i;printf(\"%d\\n\",s);}",
        "int main(){int i,s=0;for(i=1;i<=10;i++)s+=i*2;printf(\"%d\\n\",s);}",
    ]
    for c in wrong_codes:
        subs.append(FakeSub(c, ["For"], "Saída Incorreta", "", 0.2))

    # Grupo 4 — erro de compilação (5 submissões)
    compile_codes = [
        "int main(){int i,s=0 for(i=1;i<=10;i++)s+=i;printf(\"%d\\n\",s);}",
        "int main(){int i,soma=0;for(i=1;i<=10;i++)soma+=i printf(\"%d\\n\",soma);}",
        "int main(){int i s=0;for(i=1;i<=10;i++)s+=i;printf(\"%d\\n\",s);}",
        "int main(int i,s=0;for(i=1;i<=10;i++)s+=i;printf(\"%d\\n\",s);}",
        "int main(){int i,s=0;for(i=1 i<=10;i++)s+=i;printf(\"%d\\n\",s);}",
    ]
    for c in compile_codes:
        subs.append(FakeSub(c, [], "Erro de Compilação", "error: expected ';'", 0.0))

    # Grupo 5 — solução recursiva (5 submissões)
    rec_codes = [
        "int soma(int n){return n<=0?0:n+soma(n-1);}int main(){printf(\"%d\\n\",soma(10));}",
        "int f(int n){if(n==0)return 0;return n+f(n-1);}int main(){printf(\"%d\\n\",f(10));}",
        "int acc(int n,int s){return n==0?s:acc(n-1,s+n);}int main(){printf(\"%d\\n\",acc(10,0));}",
        "int s(int n){return n<1?0:s(n-1)+n;}int main(){printf(\"%d\\n\",s(10));}",
        "int r(int x){if(x<=0)return 0;return x+r(x-1);}int main(){printf(\"%d\\n\",r(10));}",
    ]
    for c in rec_codes:
        subs.append(FakeSub(c, ["If", "FuncDecl"], "Correto", "", 1.0))

    return subs


# ---------------------------------------------------------------------------
# Clustering por estratégia
# ---------------------------------------------------------------------------

STRATEGY_TITLES = {
    FeatureStrategy.TFIDF: "TF-IDF baseline",
    FeatureStrategy.TFIDF_NGRAM: "TF-IDF + bigrams",
    FeatureStrategy.TFIDF_CATEGORY: "TF-IDF + categoria de erro",
    FeatureStrategy.TFIDF_BEHAVIORAL: "TF-IDF + comportamental",
}

ERROR_COLORS = {
    "Correto": "#2ecc71",
    "Saída Incorreta": "#e67e22",
    "Erro de Compilação": "#e74c3c",
}


def _run(subs, strategy):
    codes = [s.code for s in subs]
    ast_lists = [s.ast_structures for s in subs]

    features = _build_features(codes, ast_lists, subs, strategy)

    n = len(subs)
    n_comp = min(5, n - 1)
    n_neigh = min(15, n - 1)
    init = "random" if n < 10 else "spectral"

    emb_cluster = UMAP(n_components=n_comp, n_neighbors=n_neigh, random_state=42,
                       min_dist=0.0, init=init).fit_transform(features)
    emb_viz = UMAP(n_components=2, n_neighbors=n_neigh, random_state=42,
                   init=init).fit_transform(features)

    labels = HDBSCAN(min_cluster_size=2).fit_predict(emb_cluster)

    mask = labels != -1
    unique = set(labels[mask])
    silhouette = None
    if mask.sum() >= 2 and len(unique) >= 2:
        silhouette = float(silhouette_score(emb_cluster[mask], labels[mask]))

    return emb_viz, labels, silhouette


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="comparacao_demo.png")
    args = parser.parse_args()

    subs = _make_dataset()
    error_cats = [s.error_category for s in subs]

    true_groups = (
        ["For — Correto"] * 5
        + ["While — Correto"] * 5
        + ["Saída Incorreta"] * 5
        + ["Erro de Compilação"] * 5
        + ["Recursivo — Correto"] * 5
    )
    group_colors = {
        "For — Correto": "#2980b9",
        "While — Correto": "#8e44ad",
        "Saída Incorreta": "#e67e22",
        "Erro de Compilação": "#e74c3c",
        "Recursivo — Correto": "#27ae60",
    }

    strategies = list(STRATEGY_TITLES.keys())

    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    fig.suptitle(
        "Comparação de Estratégias de Features — Dados Sintéticos\n"
        "Cor de borda = grupo real  |  Cor de preenchimento = cluster HDBSCAN",
        fontsize=12,
    )

    cmap_cluster = matplotlib.colormaps.get_cmap("tab10")

    for ax, strategy in zip(axes.flat, strategies):
        emb, labels, silhouette = _run(subs, strategy)

        xs, ys = emb[:, 0], emb[:, 1]

        unique_labels = sorted(set(labels))
        fill_colors = {
            lbl: cmap_cluster(i) if lbl != -1 else "#cccccc"
            for i, lbl in enumerate(unique_labels)
        }

        for i, (x, y) in enumerate(zip(xs, ys)):
            ax.scatter(
                x, y,
                c=[fill_colors[labels[i]]],
                edgecolors=group_colors[true_groups[i]],
                linewidths=1.5,
                s=80,
                alpha=0.9,
            )

        sil_str = f"{silhouette:.3f}" if silhouette is not None else "N/A"
        n_clusters = len([l for l in unique_labels if l != -1])
        n_outliers = int((labels == -1).sum())
        ax.set_title(
            f"{STRATEGY_TITLES[strategy]}\n"
            f"Silhouette = {sil_str}   clusters = {n_clusters}   outliers = {n_outliers}",
            fontsize=10,
        )
        ax.set_xlabel("UMAP-1")
        ax.set_ylabel("UMAP-2")

    # Legenda de grupos reais
    legend_handles = [
        plt.Line2D([0], [0], marker="o", color="w",
                   markerfacecolor="white", markeredgecolor=c,
                   markeredgewidth=2, markersize=10, label=g)
        for g, c in group_colors.items()
    ]
    legend_handles.append(
        plt.Line2D([0], [0], marker="o", color="w",
                   markerfacecolor="#cccccc", markersize=10, label="outlier (HDBSCAN)")
    )
    fig.legend(handles=legend_handles, loc="lower center", ncol=3,
               title="Grupo real (cor da borda)", fontsize=9, bbox_to_anchor=(0.5, 0.0))

    plt.tight_layout(rect=[0, 0.07, 1, 1])
    plt.savefig(args.out, dpi=150)
    print(f"Salvo em: {args.out}")


if __name__ == "__main__":
    main()
