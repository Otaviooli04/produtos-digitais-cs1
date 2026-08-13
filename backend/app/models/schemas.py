from pydantic import BaseModel, EmailStr
from typing import List, Optional, Literal


class ProfessorCreate(BaseModel):
    email: str
    nome: str = ""
    senha: str


class ProfessorResponse(BaseModel):
    id: int
    email: str
    nome: str
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    professor: ProfessorResponse


class StudentCreate(BaseModel):
    email: str
    nome: str = ""
    matricula: str = ""
    senha: str


class StudentLogin(BaseModel):
    email: str
    senha: str


class StudentResponse(BaseModel):
    id: int
    email: str
    nome: str
    matricula: Optional[str] = None
    created_at: str


class StudentTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    aluno: StudentResponse


class StudentUpdate(BaseModel):
    nome: str
    matricula: str = ""


class TurmaEntrarRequest(BaseModel):
    codigo_acesso: str


class TurmaDoAlunoResponse(BaseModel):
    id: int
    nome: str
    codigo: str
    professor_nome: Optional[str] = None
    exam_count: int


class TurmaCreate(BaseModel):
    nome: str
    codigo: str


class TurmaUpdate(BaseModel):
    nome: str
    codigo: str


class ExamSummary(BaseModel):
    id: int
    filename: str
    created_at: str
    question_count: int
    submission_count: int


class TurmaResponse(BaseModel):
    id: int
    nome: str
    codigo: str
    codigo_acesso: Optional[str] = None
    created_at: str
    exam_count: int
    aluno_count: int = 0


class TurmaDetailResponse(BaseModel):
    id: int
    nome: str
    codigo: str
    codigo_acesso: Optional[str] = None
    created_at: str
    aluno_count: int = 0
    exams: List[ExamSummary]


class TestCase(BaseModel):
    input: str
    expected_output: str


class TestResult(BaseModel):
    input: str
    expected_output: str
    actual_output: str
    passed: bool


class StructureCheck(BaseModel):
    compliant: bool
    missing_required: List[str] = []
    found_forbidden: List[str] = []


class FunctionRequirement(BaseModel):
    name: str
    param_count: Optional[int] = None
    return_type: Optional[str] = None
    requires_recursion: bool = False
    requires_pointer_param: bool = False


class FunctionCheck(BaseModel):
    compliant: bool
    missing_functions: List[str] = []
    signature_mismatches: List[str] = []
    missing_recursion: List[str] = []
    missing_pointer_param: List[str] = []


class DiagnosisResult(BaseModel):
    error_category: str
    pedagogical_diagnosis: str
    actionable_feedback: str


class CodeQuestion(BaseModel):
    number: str
    type: Literal["code"] = "code"
    statement: str
    required_structures: List[str] = []
    forbidden_structures: List[str] = []
    requires_loop: bool = False
    required_functions: List[FunctionRequirement] = []
    test_cases: List[TestCase] = []


class ExamStructure(BaseModel):
    questions: List[CodeQuestion]


class ExamUploadResponse(BaseModel):
    raw_text: str
    structure: ExamStructure


class ExamUploadStartResponse(BaseModel):
    """Resposta imediata do upload: a prova já existe, mas as questões são
    extraídas pelo Gemini em segundo plano (acompanhar via job_id)."""
    exam_id: int
    job_id: int


class JobStartResponse(BaseModel):
    job_id: int


class JobResponse(BaseModel):
    id: int
    kind: str
    status: str
    stage: str
    total: int
    processed: int
    message: str
    result: Optional[dict] = None
    exam_id: Optional[int] = None
    created_at: str


class CodeSubmissionRequest(BaseModel):
    exam_id: int
    question_number: str
    code: str
    matricula: Optional[str] = None
    dry_run: bool = False


class BulkSubmissionItem(BaseModel):
    matricula: str
    question: Optional[str]
    file: str
    status: str
    message: str


class BulkSubmissionResponse(BaseModel):
    total: int
    processed: int
    errors: int
    items: List[BulkSubmissionItem]


class CodeSubmissionResponse(BaseModel):
    question_number: str
    compile_error: str = ""
    warnings: str = ""
    test_results: List[TestResult] = []
    all_tests_passed: Optional[bool] = None
    structure_check: Optional[StructureCheck] = None
    function_check: Optional[FunctionCheck] = None
    diagnosis: DiagnosisResult


class TestCaseAddRequest(BaseModel):
    test_cases: List[TestCase]


class TestCaseResponse(BaseModel):
    id: int
    input: str
    expected_output: str


class TestCaseUpdateRequest(BaseModel):
    input: str
    expected_output: str


class ExamUpdate(BaseModel):
    filename: Optional[str] = None
    turma_id: Optional[int] = None


class QuestionCreate(BaseModel):
    number: str
    statement: str
    points: float = 1.0
    required_structures: List[str] = []
    forbidden_structures: List[str] = []
    requires_loop: bool = False
    required_functions: List[FunctionRequirement] = []


class QuestionUpdate(BaseModel):
    number: Optional[str] = None
    statement: Optional[str] = None
    points: Optional[float] = None
    required_structures: Optional[List[str]] = None
    forbidden_structures: Optional[List[str]] = None
    requires_loop: Optional[bool] = None
    required_functions: Optional[List[FunctionRequirement]] = None


class ProfessorUpdate(BaseModel):
    nome: str


class PasswordChange(BaseModel):
    senha_atual: str
    senha_nova: str


class QuestionResponse(BaseModel):
    id: int
    number: str
    statement: str
    points: float = 1.0
    required_structures: List[str]
    forbidden_structures: List[str]
    requires_loop: bool
    required_functions: List[FunctionRequirement] = []
    test_case_count: int
    warnings: List[str] = []


class ExamResponse(BaseModel):
    id: int
    filename: str
    created_at: str
    turma_id: Optional[int] = None
    turma_nome: Optional[str] = None
    total_points: float = 0.0
    questions: List[QuestionResponse]


class SubmissionResult(BaseModel):
    id: int
    code: str
    all_tests_passed: Optional[bool]
    compile_error: str
    diagnosis: DiagnosisResult
    submitted_at: str
    matricula: Optional[str] = None
    test_results: List[TestResult] = []
    tests_passed: int = 0
    tests_total: int = 0


class QuestionSubmissionsResponse(BaseModel):
    question_number: str
    statement: str
    submissions: List[SubmissionResult]


class StudentQuestionStatus(BaseModel):
    question_number: str
    submission_id: Optional[int]
    passed: Optional[bool]
    error_category: Optional[str]
    compile_error: Optional[bool] = None


class StudentSummary(BaseModel):
    matricula: str
    questions: List[StudentQuestionStatus]
    answered_count: int
    passed_count: int
    total_questions: int


class ExamStudentsResponse(BaseModel):
    question_numbers: List[str]
    students: List[StudentSummary]


class StudentSubmissionDetail(BaseModel):
    question_number: str
    statement: str
    submission_id: Optional[int]
    code: Optional[str]
    all_tests_passed: Optional[bool]
    compile_error: str
    error_category: str
    pedagogical_diagnosis: str
    actionable_feedback: str
    submitted_at: Optional[str]
    test_results: List[TestResult]
    # Grupo de dificuldade desta submissão (presente só se o agrupamento da
    # questão já rodou). Liga o nível Aluno ao nível Questão.
    cluster_id: Optional[int] = None
    cluster_dominant_error: Optional[str] = None
    cluster_size: Optional[int] = None


class StudentDetailResponse(BaseModel):
    matricula: str
    total_questions: int
    passed_count: int
    answered_count: int
    submissions: List[StudentSubmissionDetail]


class ErrorCount(BaseModel):
    error_category: str
    count: int
    matriculas: List[str] = []


class TestCaseStat(BaseModel):
    input: str
    expected_output: str
    total: int
    failed: int
    fail_rate: int
    failed_matriculas: List[str] = []


class CompileErrorCount(BaseModel):
    message: str
    count: int
    matriculas: List[str] = []


class QuestionResults(BaseModel):
    question_number: str
    statement: str
    total_submissions: int
    passed_count: int
    partial_count: int = 0
    error_distribution: List[ErrorCount]
    testcase_stats: List[TestCaseStat] = []
    compile_errors: List[CompileErrorCount] = []
    submissions: List[SubmissionResult]


class ExamResultsResponse(BaseModel):
    exam_id: int
    filename: str
    questions: List[QuestionResults]


class ClusterInfo(BaseModel):
    cluster_id: int
    size: int
    dominant_error: str
    failing_label: Optional[str] = None
    failing_count: Optional[int] = None
    representative_submission_id: Optional[int]
    representative_matricula: Optional[str] = None
    representative_code: Optional[str]


class ScatterPoint(BaseModel):
    submission_id: int
    x: float
    y: float
    cluster_id: int
    matricula: Optional[str] = None


class ClusteringResponse(BaseModel):
    question_number: str
    total_submissions: int
    clusters: List[ClusterInfo]
    scatter: List[ScatterPoint]
    strategy: str
    silhouette_score: Optional[float] = None


class ClusterInsight(BaseModel):
    cluster_id: int
    size: int
    dominant_error: str
    insight: str
    highlight_lines: List[int] = []


class InsightsResponse(BaseModel):
    question_number: str
    insights: List[ClusterInsight]


class ExamAnalytics(BaseModel):
    id: int
    filename: str
    created_at: str
    pass_rate: Optional[float]
    total_submissoes: int
    total_alunos: int


class TurmaAnalyticsResponse(BaseModel):
    turma_id: int
    total_alunos: int
    aproveitamento_medio: Optional[float]
    total_submissoes: int
    provas: List[ExamAnalytics]
    top_erros: List[ErrorCount]
