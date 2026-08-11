import subprocess
from types import SimpleNamespace

from app.engine import dynamic_analyzer


class TestRunTimeout:
    """Regressão: uma submissão que trava além dos 7s de backup não pode
    derrubar a avaliação inteira. subprocess.TimeoutExpired não expõe .process —
    o handler antigo (`if e.process`) levantava AttributeError e abortava o lote.
    """

    def test_timeout_na_execucao_vira_veredito_timeout(self, monkeypatch):
        calls = {"n": 0}

        def fake_run(cmd, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:  # etapa de compilação: sucesso
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            # etapa de execução: estoura o timeout de backup
            raise subprocess.TimeoutExpired(cmd=cmd, timeout=7)

        monkeypatch.setattr(subprocess, "run", fake_run)

        result = dynamic_analyzer.compile_and_run(
            "#include <stdio.h>\nint main(){ while(1); return 0; }",
            [{"input": "1\n", "expected_output": "1"}],
        )

        assert result["success"] is True
        assert len(result["test_results"]) == 1
        assert result["test_results"][0]["actual_output"] == "TIMEOUT"
        assert result["test_results"][0]["passed"] is False
        assert result["all_tests_passed"] is False
