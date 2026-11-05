"""Avanço entre tentativas e pausa na tentativa às cegas."""
from datetime import datetime, timedelta

from app.services.ritmo_da_tentativa import (
    EnvioDoRitmo,
    avanco,
    ritmo,
    sugerir_pausa,
    tamanho_da_mudanca,
)

T0 = datetime(2026, 11, 5, 10, 0)
CODIGO = "int main() {\n  for (i = 0; i < n; i++) soma += i;\n}"


def _envio(passados=0, total=3, codigo=CODIGO, minutos=0, passou=None):
    return EnvioDoRitmo(codigo, T0 + timedelta(minutes=minutos),
                        passados == total if passou is None else passou, passados, total)


class TestAvanco:
    def test_primeira_tentativa_nao_tem_avanco(self):
        assert avanco(None, _envio(1)) is None

    def test_conta_casos_a_mais(self):
        r = avanco(_envio(1), _envio(3))
        assert r == {"casos_a_mais": 2, "passados": 3, "passados_antes": 1, "total": 3}

    def test_conta_casos_a_menos(self):
        assert avanco(_envio(2), _envio(1))["casos_a_mais"] == -1

    def test_erro_de_compilacao_nao_compara(self):
        assert avanco(_envio(0, total=0), _envio(2)) is None
        assert avanco(_envio(2), _envio(0, total=0)) is None

    def test_anterior_que_ja_passava_nao_compara(self):
        assert avanco(_envio(3), _envio(3)) is None


class TestMudanca:
    def test_troca_de_operador_e_pequena(self):
        depois = CODIGO.replace("i < n", "i <= n")
        assert tamanho_da_mudanca(CODIGO, depois) == 1

    def test_espaco_e_linha_em_branco_nao_contam(self):
        assert tamanho_da_mudanca(CODIGO, "\n" + CODIGO.replace("  for", "    for") + "\n\n") == 0

    def test_reescrever_o_laco_e_grande(self):
        depois = "int main() {\n  int k = n;\n  while (k > 0) { soma = soma + k; k--; }\n}"
        assert tamanho_da_mudanca(CODIGO, depois) > 20


class TestPausa:
    def test_tres_envios_quase_iguais_em_poucos_minutos(self):
        envios = [_envio(1, minutos=0), _envio(1, minutos=1,
                  codigo=CODIGO.replace("i < n", "i <= n")), _envio(1, minutos=2)]
        assert sugerir_pausa(envios) is True

    def test_dois_envios_nao_bastam(self):
        assert sugerir_pausa([_envio(1), _envio(1, minutos=1)]) is False

    def test_fora_da_janela_de_cinco_minutos(self):
        assert sugerir_pausa([_envio(1), _envio(1, minutos=3), _envio(1, minutos=6)]) is False

    def test_quem_acertou_nao_recebe_pausa(self):
        assert sugerir_pausa([_envio(1), _envio(1, minutos=1), _envio(3, minutos=2)]) is False

    def test_quem_reescreveu_esta_pensando(self):
        outro = "int main() {\n  int k = n;\n  while (k > 0) { soma = soma + k; k--; }\n}"
        assert sugerir_pausa([_envio(1), _envio(1, minutos=1, codigo=outro),
                              _envio(1, minutos=2)]) is False

    def test_olha_so_os_ultimos_tres(self):
        envios = [_envio(3, minutos=0), _envio(1, minutos=10),
                  _envio(1, minutos=11), _envio(1, minutos=12)]
        assert sugerir_pausa(envios) is True

    def test_ritmo_junta_as_duas_leituras(self):
        assert ritmo([]) == {"avanco": None, "sugerir_pausa": False}
        r = ritmo([_envio(1), _envio(2, minutos=1)])
        assert r["avanco"]["casos_a_mais"] == 1
        assert r["sugerir_pausa"] is False
