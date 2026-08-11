from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from app.models.database import Base


class Professor(Base):
    __tablename__ = "professors"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    nome = Column(String, nullable=False)
    senha_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    turmas = relationship("Turma", back_populates="professor")


class Turma(Base):
    __tablename__ = "turmas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    codigo = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    professor_id = Column(Integer, ForeignKey("professors.id"), nullable=True)

    professor = relationship("Professor", back_populates="turmas")
    exams = relationship("Exam", back_populates="turma")


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    raw_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    turma_id = Column(Integer, ForeignKey("turmas.id"), nullable=True)

    questions = relationship("Question", back_populates="exam", cascade="all, delete-orphan")
    turma = relationship("Turma", back_populates="exams")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"))
    number = Column(String)
    statement = Column(Text)
    points = Column(Float, default=1.0, server_default="1.0")  # valor da questão na nota
    required_structures = Column(JSON, default=list)
    forbidden_structures = Column(JSON, default=list)
    requires_loop = Column(Boolean, default=False)
    required_functions = Column(JSON, default=list)

    exam = relationship("Exam", back_populates="questions")
    test_cases = relationship("TestCase", back_populates="question", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="question")


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    input = Column(Text)
    expected_output = Column(Text)

    question = relationship("Question", back_populates="test_cases")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    code = Column(Text)
    compile_error = Column(Text, default="")
    warnings = Column(Text, default="")
    all_tests_passed = Column(Boolean, nullable=True)
    error_category = Column(String, default="")
    pedagogical_diagnosis = Column(Text, default="")
    actionable_feedback = Column(Text, default="")
    ast_structures = Column(JSON, default=list)
    ast_functions = Column(JSON, default=list)
    cluster_id = Column(Integer, nullable=True)
    umap_x = Column(String, nullable=True)
    umap_y = Column(String, nullable=True)
    matricula = Column(String, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    question = relationship("Question", back_populates="submissions")
    test_results = relationship("SubmissionTestResult", back_populates="submission", cascade="all, delete-orphan")


class QuestionCluster(Base):
    __tablename__ = "question_clusters"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    cluster_label = Column(Integer)
    size = Column(Integer)
    dominant_error = Column(String, default="")
    insight = Column(Text, default="")
    # Linhas (1-based) do código representativo a destacar p/ o professor: erro de
    # compilação → parse do gcc; erro de lógica → atribuição do Gemini.
    highlight_lines = Column(JSON, default=list)
    representative_submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=True)

    question = relationship("Question")
    representative = relationship("Submission", foreign_keys=[representative_submission_id])


class SubmissionTestResult(Base):
    __tablename__ = "submission_test_results"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"))
    input = Column(Text)
    expected_output = Column(Text)
    actual_output = Column(Text)
    passed = Column(Boolean)

    submission = relationship("Submission", back_populates="test_results")


class ProcessingJob(Base):
    """Rastreia tarefas longas (extração da prova via Gemini, avaliação em lote)
    executadas em segundo plano, para que o usuário acompanhe o progresso sem
    ficar preso à requisição."""
    __tablename__ = "processing_jobs"

    id = Column(Integer, primary_key=True, index=True)
    kind = Column(String)                       # 'exam_upload' | 'bulk_submit'
    status = Column(String, default="pending")  # pending | running | done | error
    stage = Column(String, default="")          # descrição legível da etapa atual
    total = Column(Integer, default=0)
    processed = Column(Integer, default=0)
    message = Column(Text, default="")
    result = Column(JSON, default=dict)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=True)
    professor_id = Column(Integer, ForeignKey("professors.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
