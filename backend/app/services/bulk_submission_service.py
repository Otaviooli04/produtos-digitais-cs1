import io
import re
import zipfile
from sqlalchemy.orm import Session
from app.models.orm import ProcessingJob
from app.services.submission_service import evaluate_submission
from app.services.job_service import create_job, run_in_background, update_job


def _extract_question_number(name: str) -> str | None:
    """Extrai número da questão de strings como Q1, Questao2, 1, questão 3."""
    cleaned = name.strip().lower()
    cleaned = re.sub(r'[àáâãä]', 'a', cleaned)
    cleaned = re.sub(r'[çć]', 'c', cleaned)
    cleaned = cleaned.replace(' ', '')
    m = re.search(r'(?:questao|question|q)?(\d+)$', cleaned)
    return m.group(1) if m else None


def _strip_wrapper_folder(names: list[str]) -> list[str]:
    """Remove pasta wrapper se o ZIP tiver uma pasta raiz única."""
    with_slash = [n for n in names if '/' in n]
    if not with_slash:
        return names
    tops = set(n.split('/')[0] for n in with_slash)
    if len(tops) == 1:
        prefix = tops.pop() + '/'
        return [n[len(prefix):] for n in names]
    return names


def _enumerate_submissions(zip_bytes: bytes, fmt: str) -> list[dict]:
    """Lê o ZIP e identifica (aluno, questão, código) de cada arquivo .c.

    fmt='by_student': pastas = aluno, arquivos = Q1.c
    fmt='by_question': pastas = Q1, arquivos = aluno.c
    Itens sem questão identificável já vêm marcados como erro (não vão ao Docker).
    """
    entries = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        raw_names = [n for n in zf.namelist() if not n.endswith('/') and n.lower().endswith('.c')]
        normalized = _strip_wrapper_folder(raw_names)

        for raw_name, norm_name in zip(raw_names, normalized):
            parts = [p for p in norm_name.split('/') if p]
            if len(parts) < 2:
                continue

            if fmt == 'by_student':
                matricula = parts[0].strip()
                question_number = _extract_question_number(parts[-1][:-2])
            else:
                question_number = _extract_question_number(parts[0])
                matricula = parts[-1][:-2].strip()

            if not question_number:
                entries.append({
                    'matricula': matricula, 'question': None, 'file': norm_name,
                    'code': None, 'status': 'error',
                    'message': 'Não foi possível identificar o número da questão pelo nome do arquivo/pasta.',
                })
                continue

            entries.append({
                'matricula': matricula, 'question': question_number, 'file': norm_name,
                'code': zf.read(raw_name).decode('utf-8', errors='replace'),
                'status': None, 'message': '',
            })
    return entries


def start_bulk_processing(zip_bytes: bytes, exam_id: int, fmt: str, db: Session,
                          professor_id=None) -> ProcessingJob:
    """Enumera os arquivos do ZIP imediatamente e dispara a avaliação (Docker) em
    segundo plano, com progresso por arquivo. Retorna o job para acompanhamento."""
    entries = _enumerate_submissions(zip_bytes, fmt)
    job = create_job(
        db, "bulk_submit", exam_id=exam_id, professor_id=professor_id,
        total=len(entries), stage="Avaliando submissões",
    )
    run_in_background(job.id, lambda bg, jid: _process_bulk_job(bg, jid, exam_id, entries))
    return job


def _process_bulk_job(db: Session, job_id: int, exam_id: int, entries: list[dict]) -> None:
    items = []
    for i, e in enumerate(entries, 1):
        if e['status'] == 'error':  # questão não identificada na enumeração
            items.append({k: e[k] for k in ('matricula', 'question', 'file', 'status', 'message')})
        else:
            try:
                evaluate_submission(exam_id, e['question'], e['code'], db, matricula=e['matricula'])
                items.append({'matricula': e['matricula'], 'question': e['question'],
                              'file': e['file'], 'status': 'ok', 'message': ''})
            except ValueError as ex:
                items.append({'matricula': e['matricula'], 'question': e['question'],
                              'file': e['file'], 'status': 'error', 'message': str(ex)})
            except Exception as ex:  # noqa: BLE001
                items.append({'matricula': e['matricula'], 'question': e['question'],
                              'file': e['file'], 'status': 'error', 'message': f'Erro interno: {ex}'})

        processed = sum(1 for it in items if it['status'] == 'ok')
        errors = sum(1 for it in items if it['status'] == 'error')
        update_job(db, job_id, processed=i,
                   result={'total': len(entries), 'processed': processed,
                           'errors': errors, 'items': items})

    # Agrupamento automático por questão (best-effort; insights ficam sob demanda).
    update_job(db, job_id, stage="Agrupando por dificuldade")
    _cluster_exam_questions(db, exam_id)

    processed = sum(1 for it in items if it['status'] == 'ok')
    errors = sum(1 for it in items if it['status'] == 'error')
    update_job(db, job_id, status="done", stage="Concluído",
               message=f"{processed} avaliadas, {errors} com erro.",
               result={'total': len(entries), 'processed': processed,
                       'errors': errors, 'items': items})


def _cluster_exam_questions(db: Session, exam_id: int) -> None:
    """Agrupa cada questão da prova com submissões suficientes. Best-effort."""
    from app.models.orm import Exam
    from app.ml.cluster import cluster_question, FeatureStrategy

    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        return
    for q in exam.questions:
        if len(q.submissions) < 3:
            continue
        try:
            cluster_question(q.id, db, strategy=FeatureStrategy.TFIDF_BEHAVIORAL)
        except Exception:  # noqa: BLE001 — agrupamento não pode quebrar o lote
            db.rollback()
