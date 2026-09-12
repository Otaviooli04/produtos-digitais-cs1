"""Trilha de treino: exercício gerado para o erro que o aluno repete.

O Gemini é mockado em tudo. O que importa testar aqui é a regra de produto:
o que entra na trilha, quando gera e quando reaproveita, o teto de custo, e a
fronteira entre treino e nota.
"""
from datetime import datetime, timedelta

import pytest

from app.models.orm import ExercicioGerado, Student, Submission, TentativaDeTreino

CADASTRO = {"email": "treino@aluno.com", "nome": "Aluno Treino", "senha": "senha12345"}

EXERCICIO_FAKE = {
    "titulo": "Soma até o limite",
    "enunciado": "Leia n e some os n primeiros inteiros positivos. Imprima a soma.",
    "casos_teste": [
        {"input": "3", "expected_output": "6"},
        {"input": "1", "expected_output": "1"},
        {"input": "0", "expected_output": "0"},
    ],
    "required_structures": ["For"],
}


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def aluno(db):
    from app.auth.service import hash_password

    s = Student(email=CADASTRO["email"], nome=CADASTRO["nome"],
                senha_hash=hash_password(CADASTRO["senha"]), matricula="2026999")
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@pytest.fixture()
def erros_do_aluno(db, aluno, exam_factory):
    """Três erros de off-by-one e um de outra categoria, que é o que a trilha lê."""
    exam = exam_factory(questions=[{"number": "1"}])
    questao = exam.questions[0]
    for i, cat in enumerate(
        ["Acesso Fora dos Limites: Off-by-One"] * 3 + ["Tudo no Main"]
    ):
        db.add(Submission(
            question_id=questao.id, code=f"int main(){{return {i};}}",
            error_category=cat, all_tests_passed=False,
            pedagogical_diagnosis="diag", actionable_feedback="troque <= por <",
            student_id=aluno.id, submitted_at=datetime.utcnow(),
        ))
    db.commit()
    return exam


@pytest.fixture()
def gemini_ok(monkeypatch):
    chamadas = []

    def fake(categoria, diagnostico, exemplos):
        chamadas.append((categoria, diagnostico, list(exemplos)))
        return dict(EXERCICIO_FAKE)

    monkeypatch.setattr("app.services.treino_service.gerar_exercicio", fake)
    return chamadas


class TestOQueEntraNaTrilha:
    def test_categorias_saem_dos_erros_reais_do_aluno(self, db, aluno, erros_do_aluno):
        from app.services.treino_service import categorias_para_treinar

        categorias = categorias_para_treinar(aluno, db)
        assert [c["error_category"] for c in categorias] == [
            "Acesso Fora dos Limites: Off-by-One", "Tudo no Main"]
        assert categorias[0]["ocorrencias"] == 3
        assert categorias[0]["o_que_fazer"] == "troque <= por <"

    def test_acerto_nao_vira_categoria_de_treino(self, db, aluno, exam_factory):
        from app.services.treino_service import categorias_para_treinar

        exam = exam_factory(questions=[{"number": "1"}])
        db.add(Submission(
            question_id=exam.questions[0].id, code="int main(){}",
            error_category="Correto", all_tests_passed=True,
            student_id=aluno.id, submitted_at=datetime.utcnow(),
        ))
        db.commit()
        assert categorias_para_treinar(aluno, db) == []

    def test_aluno_sem_erro_recebe_motivo_em_texto(self, db, aluno):
        from app.services.treino_service import TreinoIndisponivel, gerar_para_categoria

        with pytest.raises(TreinoIndisponivel) as e:
            gerar_para_categoria(aluno, None, db)
        assert "ainda não tem erros" in str(e.value)


class TestGeracao:
    def test_gera_para_a_categoria_mais_frequente(self, db, aluno, erros_do_aluno, gemini_ok):
        from app.services.treino_service import gerar_para_categoria

        exercicio = gerar_para_categoria(aluno, None, db)
        assert exercicio["error_category"] == "Acesso Fora dos Limites: Off-by-One"
        assert exercicio["titulo"] == "Soma até o limite"
        assert exercicio["total_testes"] == 3
        assert gemini_ok[0][0] == "Acesso Fora dos Limites: Off-by-One"

    def test_reaproveita_o_pendente_em_vez_de_gastar_geracao(
        self, db, aluno, erros_do_aluno, gemini_ok
    ):
        """Treinar o que está aberto vale mais do que acumular exercício novo, e
        é de graça."""
        from app.services.treino_service import gerar_para_categoria

        primeiro = gerar_para_categoria(aluno, "Acesso Fora dos Limites: Off-by-One", db)
        segundo = gerar_para_categoria(aluno, "Acesso Fora dos Limites: Off-by-One", db)

        assert segundo["id"] == primeiro["id"]
        assert segundo["reaproveitado"] is True
        assert len(gemini_ok) == 1, "não pode ter chamado o Gemini de novo"

    def test_resolvido_libera_geracao_nova(self, db, aluno, erros_do_aluno, gemini_ok):
        from app.services.treino_service import gerar_para_categoria

        primeiro = gerar_para_categoria(aluno, "Acesso Fora dos Limites: Off-by-One", db)
        db.get(ExercicioGerado, primeiro["id"]).resolvido = True
        db.commit()

        segundo = gerar_para_categoria(aluno, "Acesso Fora dos Limites: Off-by-One", db)
        assert segundo["id"] != primeiro["id"]
        assert len(gemini_ok) == 2

    def test_teto_diario_bloqueia_a_geracao_mas_nao_o_treino(
        self, db, aluno, erros_do_aluno, gemini_ok
    ):
        from app.llm.exercise_generator import GERACOES_POR_DIA
        from app.services.treino_service import TreinoIndisponivel, gerar_para_categoria

        for i in range(GERACOES_POR_DIA):
            db.add(ExercicioGerado(
                student_id=aluno.id, error_category="Acesso Fora dos Limites: Off-by-One",
                titulo=f"gerado {i}", enunciado="x" * 30, casos_teste=[{"input": "", "expected_output": "1"}],
                resolvido=True, created_at=datetime.utcnow(),
            ))
        db.commit()

        with pytest.raises(TreinoIndisponivel) as e:
            gerar_para_categoria(aluno, "Acesso Fora dos Limites: Off-by-One", db)
        assert "24 horas" in str(e.value)

    def test_geracao_antiga_nao_conta_no_teto(self, db, aluno, erros_do_aluno, gemini_ok):
        from app.llm.exercise_generator import GERACOES_POR_DIA
        from app.services.treino_service import gerar_para_categoria

        ontem = datetime.utcnow() - timedelta(days=2)
        for i in range(GERACOES_POR_DIA):
            db.add(ExercicioGerado(
                student_id=aluno.id, error_category="Acesso Fora dos Limites: Off-by-One",
                titulo=f"antigo {i}", enunciado="x" * 30,
                casos_teste=[{"input": "", "expected_output": "1"}],
                resolvido=True, created_at=ontem,
            ))
        db.commit()

        exercicio = gerar_para_categoria(aluno, "Acesso Fora dos Limites: Off-by-One", db)
        assert exercicio["titulo"] == "Soma até o limite"

    def test_exercicio_invalido_do_modelo_nao_vira_exercicio(
        self, db, aluno, erros_do_aluno, monkeypatch
    ):
        from app.llm.exercise_generator import ExercicioInvalido
        from app.services.treino_service import TreinoIndisponivel, gerar_para_categoria

        def explode(*a, **k):
            raise ExercicioInvalido("sem caso de teste")

        monkeypatch.setattr("app.services.treino_service.gerar_exercicio", explode)
        with pytest.raises(TreinoIndisponivel):
            gerar_para_categoria(aluno, None, db)
        assert db.query(ExercicioGerado).count() == 0


class TestTreino:
    def _exercicio(self, db, aluno):
        e = ExercicioGerado(
            student_id=aluno.id, error_category="Acesso Fora dos Limites: Off-by-One",
            titulo="Soma", enunciado="Some os n primeiros inteiros.",
            casos_teste=[{"input": "3", "expected_output": "6"}],
            required_structures=["For"], created_at=datetime.utcnow(),
        )
        db.add(e)
        db.commit()
        db.refresh(e)
        return e

    def _resultado(self, passou):
        return {
            "compile_error": "", "warnings": "",
            "all_tests_passed": passou,
            "diagnosis": {
                "error_category": "Correto" if passou else "Saída Incorreta",
                "pedagogical_diagnosis": "diag", "actionable_feedback": "faça assim",
            },
            "test_results": [
                {"input": "3", "expected_output": "6",
                 "actual_output": "6" if passou else "7", "passed": passou},
            ],
            "structure_check": None,
        }

    def test_tentativas_sao_ilimitadas(self, db, aluno, monkeypatch):
        from app.services import treino_service

        exercicio = self._exercicio(db, aluno)
        monkeypatch.setattr(treino_service, "evaluate_code",
                            lambda *a, **k: self._resultado(False))

        for esperado in range(1, 6):
            r = treino_service.treinar(aluno, exercicio.id, "int main(){}", db)
            assert r["tentativas"] == esperado
            assert r["tentativa"]["attempt_number"] == esperado
        assert db.query(TentativaDeTreino).count() == 5

    def test_acertar_marca_o_exercicio_como_resolvido(self, db, aluno, monkeypatch):
        from app.services import treino_service

        exercicio = self._exercicio(db, aluno)
        monkeypatch.setattr(treino_service, "evaluate_code",
                            lambda *a, **k: self._resultado(True))
        r = treino_service.treinar(aluno, exercicio.id, "int main(){}", db)
        assert r["resolvido"] is True
        assert db.get(ExercicioGerado, exercicio.id).resolvido is True

    def test_exercicio_de_outro_aluno_nao_abre(self, db, aluno, monkeypatch):
        from app.auth.service import hash_password
        from app.services import treino_service

        exercicio = self._exercicio(db, aluno)
        outro = Student(email="outro@aluno.com", nome="Outro",
                        senha_hash=hash_password("senha12345"))
        db.add(outro)
        db.commit()

        with pytest.raises(ValueError):
            treino_service.detalhe(outro, exercicio.id, db)

    def test_treino_nao_entra_nas_submissoes_da_turma(self, db, aluno, monkeypatch):
        """A fronteira que justifica a tabela separada: o gerado nunca vale nota
        nem contamina a análise do professor."""
        from app.services import treino_service

        exercicio = self._exercicio(db, aluno)
        monkeypatch.setattr(treino_service, "evaluate_code",
                            lambda *a, **k: self._resultado(False))
        treino_service.treinar(aluno, exercicio.id, "int main(){}", db)

        assert db.query(Submission).filter(Submission.student_id == aluno.id).count() == 0


class TestReportar:
    def test_reportado_sai_da_trilha_mas_guarda_o_motivo(self, db, aluno, erros_do_aluno, gemini_ok):
        from app.services.treino_service import gerar_para_categoria, reportar, trilha

        exercicio = gerar_para_categoria(aluno, None, db)
        reportar(aluno, exercicio["id"], "O enunciado não diz o formato da saída.", db)

        salvo = db.get(ExercicioGerado, exercicio["id"])
        assert salvo.reportado is True
        assert salvo.reportado_motivo == "O enunciado não diz o formato da saída."
        assert trilha(aluno, db)["exercicios"] == []

    def test_reportado_nao_aceita_mais_tentativa(self, db, aluno, erros_do_aluno, gemini_ok):
        from app.services.treino_service import gerar_para_categoria, reportar, treinar

        exercicio = gerar_para_categoria(aluno, None, db)
        reportar(aluno, exercicio["id"], "ruim", db)
        with pytest.raises(ValueError):
            treinar(aluno, exercicio["id"], "int main(){}", db)


class TestValidacaoDoQueOModeloDevolve:
    def test_cerca_de_markdown_nao_quebra(self):
        import json

        from app.llm.exercise_generator import _validar

        bruto = "```json\n" + json.dumps(EXERCICIO_FAKE) + "\n```"
        assert _validar(bruto)["titulo"] == "Soma até o limite"

    def test_sem_caso_de_teste_e_recusado(self):
        import json

        from app.llm.exercise_generator import ExercicioInvalido, _validar

        dados = dict(EXERCICIO_FAKE, casos_teste=[])
        with pytest.raises(ExercicioInvalido):
            _validar(json.dumps(dados))

    def test_estrutura_inventada_e_descartada(self):
        import json

        from app.llm.exercise_generator import _validar

        dados = dict(EXERCICIO_FAKE, required_structures=["For", "Blockchain"])
        assert _validar(json.dumps(dados))["required_structures"] == ["For"]

    def test_resposta_que_nao_e_json_e_recusada(self):
        from app.llm.exercise_generator import ExercicioInvalido, _validar

        with pytest.raises(ExercicioInvalido):
            _validar("Claro! Aqui está o exercício que você pediu.")
