from __future__ import annotations

from collections import Counter
from datetime import datetime
from enum import Enum
from typing import List, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import MultiLabelBinarizer, OneHotEncoder
from scipy.sparse import hstack, issparse
from sqlalchemy.orm import Session, joinedload

from app.models.orm import QuestionCluster, Submission

MIN_SUBMISSIONS = 3


def _adaptive_min_cluster_size(n: int) -> int:
    """min_cluster_size proporcional ao tamanho da turma, limitado a [2, 8]."""
    return max(2, min(8, round(n / 12)))


SUBCLUSTER_MIN = 6  # tamanho mínimo da categoria para procurar sub-padrões


def _is_correct_category(cat: str) -> bool:
    return (cat or "").strip().lower().startswith("correto")


def failure_signature(sub) -> Optional[tuple]:
    """Vetor de aprovação (1) / reprovação (0) por caso de teste; None se não executou."""
    if sub.compile_error or not sub.test_results:
        return None
    return tuple(1 if tr.passed else 0 for tr in sub.test_results)


def two_level_labels(submissions: List["Submission"], error_categories: list[str]) -> np.ndarray:
    """Compatibilidade: só os rótulos. Quem precisa da identidade do grupo usa
    `two_level_grupos`."""
    labels, _ = two_level_grupos(submissions, error_categories)
    return labels


def two_level_grupos(
    submissions: List["Submission"], error_categories: list[str],
) -> tuple[np.ndarray, dict[int, str]]:
    """Nível 1: categoria de erro. Nível 2: dentro de categorias grandes, agrupa por
    assinatura de falha. Categorias pequenas e "Correto" ficam inteiras; assinaturas
    raras viram um grupo residual.

    Devolve os rótulos e, para cada rótulo, a chave estável do grupo. O rótulo é
    posicional e muda quando o grupo é refeito, a chave não: ela é feita do que
    define o grupo, então é ela que ancora o que o professor escreveu ali."""
    n = len(error_categories)
    labels = np.full(n, -1, dtype=int)
    chaves: dict[int, str] = {}
    by_cat: dict[str, list[int]] = {}
    for i, cat in enumerate(error_categories):
        by_cat.setdefault(cat or "unknown", []).append(i)

    next_label = 0
    for cat, idx in by_cat.items():
        if len(idx) < SUBCLUSTER_MIN or _is_correct_category(cat):
            for i in idx:
                labels[i] = next_label
            chaves[next_label] = f"cat:{cat}"
            next_label += 1
            continue

        # Nível 2: agrupa a categoria pela assinatura de falha dos casos de teste.
        by_sig: dict[Optional[tuple], list[int]] = {}
        for i in idx:
            by_sig.setdefault(failure_signature(submissions[i]), []).append(i)

        residual = None
        for sig, members in sorted(by_sig.items(), key=lambda kv: -len(kv[1])):
            if sig is not None and len(members) >= 2:
                for i in members:
                    labels[i] = next_label
                chaves[next_label] = f"cat:{cat}|sig:{','.join(str(v) for v in sig)}"
                next_label += 1
            else:
                if residual is None:
                    residual = next_label
                    chaves[next_label] = f"cat:{cat}|sig:residual"
                    next_label += 1
                for i in members:
                    labels[i] = residual
    return labels, chaves


class FeatureStrategy(str, Enum):
    TFIDF = "tfidf"
    TFIDF_NGRAM = "tfidf_ngram"
    TFIDF_CATEGORY = "tfidf_category"
    TFIDF_BEHAVIORAL = "tfidf_behavioral"
    TFIDF_FUNCTIONAL = "tfidf_functional"


class ClusteringResult:
    def __init__(self, clusters: list[dict]):
        self.clusters = clusters


def cluster_question(question_id: int, db: Session) -> ClusteringResult | None:
    """Agrupa a questão. É o agrupamento do TCC, sem variação: nível 1 pela
    categoria de erro das heurísticas, nível 2 pela assinatura de falha dentro
    das categorias grandes.

    Determinístico e barato, então roda a cada envio de aluno, no fim do lote e
    no botão do professor. Não existe um segundo caminho, mais rápido ou mais
    completo: é sempre este.

    UMAP e HDBSCAN não participam. Eles foram o baseline de comparação do TCC e
    ficaram de lado, e as funções de vetorização mais abaixo neste arquivo
    existem por causa daquela comparação, não do produto.
    """
    submissions: List[Submission] = (
        db.query(Submission)
        .options(joinedload(Submission.test_results))
        .filter(Submission.question_id == question_id)
        .all()
    )
    if len(submissions) < MIN_SUBMISSIONS:
        return None

    labels, chaves = two_level_grupos(
        submissions, [s.error_category or "" for s in submissions])
    _persist_results(submissions, labels, question_id, db, chaves)
    return _build_result(submissions, labels)


# ---------------------------------------------------------------------------
# Baseline do TCC — fora do caminho de execução
#
# Daqui para baixo é a vetorização que alimentava UMAP e HDBSCAN na comparação
# do TCC. Nada disso roda no produto: o agrupamento é `two_level_grupos`, logo
# no começo deste arquivo. Fica aqui pela reprodutibilidade daquele resultado.
# ---------------------------------------------------------------------------

def _build_features(
    codes: list[str],
    ast_lists: list[list[str]],
    submissions: List[Submission],
    strategy: FeatureStrategy,
) -> np.ndarray:
    if strategy == FeatureStrategy.TFIDF:
        return _build_tfidf(codes, ast_lists)
    if strategy == FeatureStrategy.TFIDF_NGRAM:
        return _build_tfidf_ngram(codes, ast_lists)
    if strategy == FeatureStrategy.TFIDF_CATEGORY:
        return _build_tfidf_category(codes, ast_lists, submissions)
    if strategy == FeatureStrategy.TFIDF_BEHAVIORAL:
        return _build_tfidf_behavioral(codes, ast_lists, submissions)
    if strategy == FeatureStrategy.TFIDF_FUNCTIONAL:
        return _build_tfidf_functional(codes, ast_lists, submissions)
    return _build_tfidf(codes, ast_lists)


def _build_tfidf(codes: list[str], ast_lists: list[list[str]]) -> np.ndarray:
    tfidf = TfidfVectorizer(
        analyzer="word", token_pattern=r"[a-zA-Z_][a-zA-Z0-9_]*"
    )
    matrix = tfidf.fit_transform(codes)
    onehot = MultiLabelBinarizer().fit_transform(ast_lists)
    return _dense(hstack([matrix, onehot]))


def _build_tfidf_ngram(codes: list[str], ast_lists: list[list[str]]) -> np.ndarray:
    tfidf = TfidfVectorizer(
        analyzer="word",
        token_pattern=r"[a-zA-Z_][a-zA-Z0-9_]*",
        ngram_range=(1, 2),
    )
    matrix = tfidf.fit_transform(codes)
    onehot = MultiLabelBinarizer().fit_transform(ast_lists)
    return _dense(hstack([matrix, onehot]))


def _build_tfidf_category(
    codes: list[str],
    ast_lists: list[list[str]],
    submissions: List[Submission],
) -> np.ndarray:
    tfidf = TfidfVectorizer(
        analyzer="word", token_pattern=r"[a-zA-Z_][a-zA-Z0-9_]*"
    )
    matrix = tfidf.fit_transform(codes)
    onehot_ast = MultiLabelBinarizer().fit_transform(ast_lists)
    onehot_cat = _category_onehot(submissions)
    return np.hstack([_dense(hstack([matrix, onehot_ast])), onehot_cat]).astype(np.float32)


def _build_tfidf_behavioral(
    codes: list[str],
    ast_lists: list[list[str]],
    submissions: List[Submission],
) -> np.ndarray:
    tfidf = TfidfVectorizer(
        analyzer="word",
        token_pattern=r"[a-zA-Z_][a-zA-Z0-9_]*",
        ngram_range=(1, 2),
    )
    matrix = tfidf.fit_transform(codes)
    onehot_ast = MultiLabelBinarizer().fit_transform(ast_lists)
    onehot_cat = _category_onehot(submissions)
    behavioral = _behavioral_features(submissions)
    return np.hstack([
        _dense(hstack([matrix, onehot_ast])),
        onehot_cat,
        behavioral,
    ]).astype(np.float32)


def _build_tfidf_functional(
    codes: list[str],
    ast_lists: list[list[str]],
    submissions: List[Submission],
) -> np.ndarray:
    tfidf = TfidfVectorizer(
        analyzer="word",
        token_pattern=r"[a-zA-Z_][a-zA-Z0-9_]*",
        ngram_range=(1, 2),
    )
    matrix = tfidf.fit_transform(codes)
    onehot_ast = MultiLabelBinarizer().fit_transform(ast_lists)
    onehot_cat = _category_onehot(submissions)
    behavioral = _behavioral_features(submissions)
    functional = _function_features(submissions)
    return np.hstack([
        _dense(hstack([matrix, onehot_ast])),
        onehot_cat,
        behavioral,
        functional,
    ]).astype(np.float32)


def _function_features(submissions: List[Submission]) -> np.ndarray:
    """Features de função (nº de funções, recursão, ponteiro, máx. parâmetros) a partir de ast_functions."""
    rows = []
    for s in submissions:
        fns = getattr(s, "ast_functions", None) or []
        user_fns = [f for f in fns if f.get("name") != "main"]
        n_user = float(len(user_fns))
        has_recursion = 1.0 if any(f.get("is_recursive") for f in fns) else 0.0
        has_pointer = 1.0 if any(f.get("has_pointer_param") for f in fns) else 0.0
        max_params = float(max((f.get("param_count", 0) for f in fns), default=0))
        rows.append([n_user, has_recursion, has_pointer, max_params])
    return np.array(rows, dtype=np.float32)


def _category_onehot(submissions: List[Submission]) -> np.ndarray:
    cats = np.array([s.error_category or "unknown" for s in submissions]).reshape(-1, 1)
    enc = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
    return enc.fit_transform(cats).astype(np.float32)


def _behavioral_features(submissions: List[Submission]) -> np.ndarray:
    rows = []
    for s in submissions:
        compila = 0.0 if s.compile_error else 1.0
        if s.test_results:
            fracao = sum(1 for tr in s.test_results if tr.passed) / len(s.test_results)
        else:
            fracao = 0.0
        rows.append([compila, fracao])
    return np.array(rows, dtype=np.float32)


def _dense(matrix) -> np.ndarray:
    if issparse(matrix):
        matrix = matrix.toarray()
    return matrix.astype(np.float32)


# ---------------------------------------------------------------------------
# Silhouette
# ---------------------------------------------------------------------------

def _compute_silhouette(embedded: np.ndarray, labels: np.ndarray) -> Optional[float]:
    mask = labels != -1
    unique = set(labels[mask])
    if mask.sum() < 2 or len(unique) < 2:
        return None
    return float(silhouette_score(embedded[mask], labels[mask]))


# ---------------------------------------------------------------------------
# Persistência e resultado
# ---------------------------------------------------------------------------

def _persist_results(
    submissions: List[Submission],
    labels: np.ndarray,
    question_id: int,
    db: Session,
    chaves: Optional[dict[int, str]] = None,
) -> None:
    """Grava o agrupamento sem destruir o que o grupo carrega.

    O caminho antigo apagava todas as linhas e recriava, o que jogava fora o
    insight a cada re-agrupamento. Como agora isso roda a cada envio de aluno,
    apagar seria perder o texto do professor o tempo todo. A linha é encontrada
    pela `chave`, que sobrevive à renumeração dos rótulos, e só o que mudou é
    atualizado. Grupo que deixou de existir é removido, e só ele."""
    chaves = chaves or {}
    agora = datetime.utcnow()

    for sub, label in zip(submissions, labels):
        sub.cluster_id = int(label)

    linhas = db.query(QuestionCluster).filter(
        QuestionCluster.question_id == question_id).all()
    existentes = {qc.chave: qc for qc in linhas if qc.chave}
    sem_chave = [qc for qc in linhas if not qc.chave]

    vivas: set[str] = set()
    for label in sorted(set(int(l) for l in labels) - {-1}):
        indices = [i for i, l in enumerate(labels) if int(l) == label]
        cluster_subs = [submissions[i] for i in indices]
        chave = chaves.get(label) or f"label:{label}"
        vivas.add(chave)

        qc = existentes.get(chave)
        if qc is None:
            qc = QuestionCluster(question_id=question_id, chave=chave)
            db.add(qc)
        qc.cluster_label = label
        qc.size = len(indices)
        qc.dominant_error = _dominant_error(cluster_subs)
        qc.representative_submission_id = _escolher_representante(
            qc.representative_submission_id, indices, submissions)
        qc.atualizado_em = agora

    for chave, qc in existentes.items():
        if chave not in vivas:
            db.delete(qc)
    # Linhas anteriores à chave estável não têm como ser reconciliadas.
    for qc in sem_chave:
        db.delete(qc)

    db.commit()


def _escolher_representante(
    atual: Optional[int],
    indices: list[int],
    submissions: List[Submission],
) -> int:
    """Mantém o representante que o professor já viu, enquanto ele continuar no
    grupo, para a tela não trocar de código a cada envio novo.

    Quando precisa escolher, pega o código mais curto do grupo. O TCC escolhia
    pelo ponto mais próximo do centroide no embedding do UMAP, que deixou de
    existir junto com o UMAP. Todo mundo no grupo falhou da mesma forma, então
    qualquer um serve de exemplo, e o mais curto é o menos ruidoso de ler."""
    no_grupo = {submissions[i].id for i in indices}
    if atual in no_grupo:
        return atual
    escolhido = min(indices, key=lambda i: (len(submissions[i].code or ""), submissions[i].id))
    return submissions[escolhido].id


def _dominant_error(subs: List[Submission]) -> str:
    errors = [s.error_category for s in subs if s.error_category]
    if not errors:
        return "unknown"
    return Counter(errors).most_common(1)[0][0]


def _find_representative(indices: list[int], embedded: np.ndarray) -> int:
    points = embedded[indices]
    centroid = points.mean(axis=0)
    dists = np.linalg.norm(points - centroid, axis=1)
    return indices[int(np.argmin(dists))]


def _build_result(submissions: List[Submission], labels: np.ndarray) -> ClusteringResult:
    clusters: dict[int, dict] = {}
    for sub, label in zip(submissions, labels):
        label = int(label)
        if label == -1:
            continue
        if label not in clusters:
            clusters[label] = {
                "cluster_id": label,
                "size": 0,
                "dominant_error": sub.error_category or "unknown",
                "representative_code": None,
                "representative_submission_id": None,
            }
        clusters[label]["size"] += 1

    return ClusteringResult(clusters=list(clusters.values()))
