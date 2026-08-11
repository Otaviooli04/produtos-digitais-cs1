from app.ml.cluster import _adaptive_min_cluster_size


class TestAdaptiveMinClusterSize:
    def test_turma_pequena_usa_minimo_2(self):
        assert _adaptive_min_cluster_size(14) == 2
        assert _adaptive_min_cluster_size(25) == 2

    def test_anchor_empirico_exp2_n56(self):
        # exp2: mcs≈5 é ótimo para n≈56
        assert _adaptive_min_cluster_size(56) == 5

    def test_cresce_em_turma_grande(self):
        # exp3 Extra (n=98) super-segmentava com mcs=2
        assert _adaptive_min_cluster_size(98) == 8

    def test_limite_superior_em_8(self):
        assert _adaptive_min_cluster_size(500) == 8

    def test_monotonico_nao_decrescente(self):
        vals = [_adaptive_min_cluster_size(n) for n in range(3, 200)]
        assert vals == sorted(vals)
