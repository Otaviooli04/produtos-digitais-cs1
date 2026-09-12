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


class TestChaveEstavelDoGrupo:
    """`cluster_label` é posicional e muda quando o grupo é refeito. A `chave` é
    feita do que define o grupo, então sobrevive. É ela que ancora o insight e,
    depois, a resposta que o professor escreve para o grupo."""

    def test_chave_descreve_categoria_e_assinatura(self):
        from app.ml.cluster import two_level_grupos

        subs = [_sub_fake("Correto", [1, 1]) for _ in range(3)]
        labels, chaves = two_level_grupos(subs, ["Correto"] * 3)
        assert set(labels) == {0}
        assert chaves[0] == "cat:Correto"

    def test_mesma_chave_mesmo_grupo_em_ordens_diferentes(self):
        """A ordem de chegada muda o rótulo, mas não pode mudar a identidade."""
        from app.ml.cluster import two_level_grupos

        off = [_sub_fake("Off-by-One", [1, 0]) for _ in range(6)]
        outros = [_sub_fake("Saída Incorreta", [0, 0]) for _ in range(2)]

        _, chaves_a = two_level_grupos(off + outros, ["Off-by-One"] * 6 + ["Saída Incorreta"] * 2)
        _, chaves_b = two_level_grupos(outros + off, ["Saída Incorreta"] * 2 + ["Off-by-One"] * 6)
        assert set(chaves_a.values()) == set(chaves_b.values())

    def test_rotulo_muda_mas_chave_nao(self):
        from app.ml.cluster import two_level_grupos

        off = [_sub_fake("Off-by-One", [1, 0]) for _ in range(6)]
        outros = [_sub_fake("Saída Incorreta", [0, 0]) for _ in range(2)]

        labels_a, chaves_a = two_level_grupos(
            off + outros, ["Off-by-One"] * 6 + ["Saída Incorreta"] * 2)
        labels_b, chaves_b = two_level_grupos(
            outros + off, ["Saída Incorreta"] * 2 + ["Off-by-One"] * 6)

        chave_do_off_a = chaves_a[int(labels_a[0])]
        chave_do_off_b = chaves_b[int(labels_b[-1])]
        assert chave_do_off_a == chave_do_off_b
        assert int(labels_a[0]) != int(labels_b[-1])  # o rótulo, sim, mudou


class _ResultadoFake:
    def __init__(self, passed):
        self.passed = passed


def _sub_fake(categoria, assinatura):
    class S:
        pass
    s = S()
    s.error_category = categoria
    s.compile_error = ""
    s.test_results = [_ResultadoFake(bool(v)) for v in assinatura]
    s.code = "int main(){return 0;}"
    s.id = id(s)
    return s
