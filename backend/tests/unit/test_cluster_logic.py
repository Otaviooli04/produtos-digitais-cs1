import numpy as np
import pytest
from unittest.mock import MagicMock

from app.ml.cluster import (
    FeatureStrategy,
    _build_features,
    _dominant_error,
    _find_representative,
)


def _make_subs(n):
    subs = []
    for _ in range(n):
        s = MagicMock()
        s.error_category = "Correto"
        s.compile_error = False
        s.test_results = []
        subs.append(s)
    return subs


class TestBuildFeatures:
    def test_shape_correto(self):
        codes = ["int main(){return 0;}", "int x=1; while(x){x--;}", "int main(){}"]
        asts = [["If"], ["While"], []]
        features = _build_features(codes, asts, _make_subs(3), FeatureStrategy.TFIDF)
        assert features.shape[0] == 3

    def test_retorna_float32(self):
        codes = ["int main(){}", "int x;"]
        asts = [[], []]
        features = _build_features(codes, asts, _make_subs(2), FeatureStrategy.TFIDF)
        assert features.dtype == np.float32

    def test_ast_vazia_nao_quebra(self):
        codes = ["int main(){return 0;}"] * 3
        asts = [[], [], []]
        features = _build_features(codes, asts, _make_subs(3), FeatureStrategy.TFIDF)
        assert features.shape[0] == 3

    def test_codigos_diferentes_geram_vetores_diferentes(self):
        codes = ["int main(){return 0;}", "while(1){ printf(42); }"]
        asts = [[], ["While"]]
        features = _build_features(codes, asts, _make_subs(2), FeatureStrategy.TFIDF)
        assert not np.array_equal(features[0], features[1])


class TestDominantError:
    def _make_sub(self, error_category):
        from unittest.mock import MagicMock
        s = MagicMock()
        s.error_category = error_category
        return s

    def test_retorna_erro_mais_comum(self):
        subs = [
            self._make_sub("Saída Incorreta"),
            self._make_sub("Saída Incorreta"),
            self._make_sub("Erro de Compilação"),
        ]
        assert _dominant_error(subs) == "Saída Incorreta"

    def test_lista_vazia_retorna_unknown(self):
        assert _dominant_error([]) == "unknown"

    def test_todos_sem_categoria_retorna_unknown(self):
        subs = [self._make_sub(""), self._make_sub("")]
        assert _dominant_error(subs) == "unknown"

    def test_empate_retorna_um_dos_mais_comuns(self):
        subs = [self._make_sub("A"), self._make_sub("B")]
        result = _dominant_error(subs)
        assert result in ("A", "B")


class TestFindRepresentative:
    def test_encontra_ponto_mais_proximo_do_centroide(self):
        indices = [0, 1, 2]
        embedded = np.array([
            [0.0, 0.0],
            [1.0, 1.0],
            [10.0, 10.0],
        ])
        result = _find_representative(indices, embedded)
        assert result == 1

    def test_unico_ponto_retorna_ele_mesmo(self):
        indices = [3]
        embedded = np.array([
            [0.0, 0.0],
            [1.0, 1.0],
            [2.0, 2.0],
            [5.0, 5.0],
        ])
        assert _find_representative(indices, embedded) == 3

    def test_dois_pontos_retorna_o_mais_proximo_da_media(self):
        indices = [0, 1]
        embedded = np.array([
            [0.0, 0.0],
            [2.0, 0.0],
        ])
        result = _find_representative(indices, embedded)
        assert result in (0, 1)
