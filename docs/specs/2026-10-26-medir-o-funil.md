# Medir o funil, parte 1: North Star e funil da turma

**Item do plano:** volta "medir o funil", parte 1 (seção 10.1 de `docs/produto/plano-implementacao.md`), que junta G1, G2, G4, a parte do 1.3 que sai dos envios e a saúde do 1.4
**Requisitos:** RF09, RF10 (ativação e alunos em vermelho), RF15 (retorno e envio no treino, pelos envios), RF16 (taxa de ativação da primeira semana), RN05, RN09, RNF04
**Data:** 2026-10-26

## Objetivo

Mostrar ao professor, na página da turma, a North Star do produto (erros corrigidos por semana), o funil de aquisição, ativação e retenção contra as metas do piloto e os alunos em risco pelo nome, tudo calculado na hora com o que o banco já guarda. Dar à equipe um script que mostra o mesmo funil para todas as turmas, só com números.

## Comportamento

**Professor**

1. Ao criar uma turma e ao editá-la (`TurmaListPage`), vê o campo "Alunos na turma (opcional)". Preenche com o tamanho da turma, de 1 a 1000, ou deixa em branco.
2. Na página da turma, logo abaixo dos cartões de resumo, aparece o bloco "Funil da turma", com:
   - **Erros corrigidos:** o número desta semana, o total desde o início e barras das últimas 8 semanas.
   - **Aquisição:** matriculados contra os alunos na turma, a taxa da primeira semana e a meta de 80%. Sem o campo preenchido, mostra só os matriculados e a frase "Informe quantos alunos a turma tem para ver a taxa de entrada."
   - **Ativação:** quantos matriculados corrigiram o primeiro erro até 7 dias depois de entrar, a taxa e a meta de 60%. Abaixo, quantos fizeram ao menos um envio.
   - **Retenção:** a taxa da última semana completa, a taxa por conta própria da mesma semana e a meta de 50%.
   - **Alunos em risco:** os vermelhos e depois os amarelos, cada um com nome, motivo e data do último envio, mais a taxa de vermelho contra a meta de menos de 15%. Sem ninguém em risco, mostra "Nenhum aluno em risco agora."
   - **Proteção:** uma linha com a média de tentativas até acertar e a porcentagem de acerto de primeira.
3. Turma sem matriculados mostra no bloco só a frase "O funil aparece quando os alunos entrarem pelo código da turma."
4. Se a chamada do funil falhar, o resto da página continua normal e o bloco mostra "Não foi possível carregar o funil."
5. Excluir uma atividade na página recarrega o funil junto com a analytics.

**Aluno:** nada muda.

**Equipe:** roda `cd backend && venv/bin/python scripts/funil.py` e lê no terminal a North Star das últimas 8 semanas e o funil de cada turma e do total.

## Definições

As regras abaixo detalham a seção 1 do desenho, que já foi aprovada.

**O que entra na conta**

- **Item:** uma questão de atividade publicada da turma, no par de aluno e questão, ou um exercício da trilha, no par de aluno e exercício gerado.
- **Envio de lista:** `Submission` com `student_id` de aluno matriculado na turma, numa questão de `Exam` com o `turma_id` da turma e `publicada` verdadeiro. Envio sem `student_id` (os do TCC, importados em lote só com matrícula) fica fora.
- **Envio de trilha:** `TentativaDeTreino` de aluno matriculado na turma. Como `ExercicioGerado` não tem `turma_id`, o treino do aluno conta em todas as turmas em que ele está matriculado.
- **Matriculado:** aluno com linha em `enrollments` para a turma. A data de entrada é o `created_at` da matrícula.
- **Acerto:** no envio de lista, `error_category` igual a "Correto", a mesma regra de `_resolvida`. No envio de trilha, `all_tests_passed` verdadeiro, a mesma regra que marca o exercício como resolvido.
- **Falha técnica:** tentativa que não é acerto e tem `error_category` igual a "Erro Desconhecido" ou vazio, como quando o Docker está fora do ar. Conta como envio, porque o aluno voltou e enviou, mas não conta como erro nem como acerto.
- **Erro:** tentativa que não é acerto nem falha técnica.
- **Ordem:** as tentativas de um item seguem `submitted_at` e depois `id`. Tentativa sem `submitted_at` fica fora de tudo.
- **Semana:** de segunda a domingo, pela data UTC gravada no banco, com a regra de `_semana`, em que a segunda-feira em ISO identifica a semana. A resposta traz sempre 8 semanas, a atual e as 7 anteriores, em ordem cronológica e com zero onde não houve nada.

**North Star, erro corrigido**

- Um item conta um erro corrigido quando tem ao menos um erro antes do primeiro acerto. Conta na semana do primeiro acerto.
- É um por item e para sempre: errar, acertar, errar e acertar de novo conta um.
- Acertar de primeira não conta e vai para o acerto de primeira. Ter só falha técnica antes do acerto também não conta.
- O total soma todos os itens, sem limite de data.

**Aquisição**

- `matriculados`: as matrículas da turma.
- `alunos_previstos`: o campo novo, que pode ser nulo.
- `primeira_semana`: as matrículas com `created_at` até 7 dias depois da primeira matrícula da turma, que marca a divulgação do código.
- `taxa_matriculados` é `matriculados / alunos_previstos × 100` e `taxa_primeira_semana` é `primeira_semana / alunos_previstos × 100`. As duas ficam nulas sem o campo e podem passar de 100 se entrar mais gente do que o previsto. A meta de 80% se compara com a taxa da primeira semana.

**Ativação**

- `com_primeiro_envio`: matriculados com ao menos um envio de lista ou de trilha, falha técnica incluída.
- `ativados`: matriculados com algum erro corrigido cujo primeiro acerto caiu entre a matrícula e 7 dias depois dela.
- `taxa`: `ativados / matriculados × 100`, com meta de 60%.

**Retenção, por semana**

- `base`: matriculados com matrícula antes do fim da semana.
- `voltaram`: alunos da base com envio na semana e com envio antes do início dela.
- `por_conta_propria`: alunos da base com envio na semana em atividade de `modo` "treino" ou na trilha, e com qualquer envio antes do início dela.
- `taxa` é `voltaram / base × 100` e `taxa_por_conta_propria` é `por_conta_propria / base × 100`. As duas ficam nulas com base zero.
- O cartão mostra a última semana completa, a anterior à atual, porque a semana atual ainda está pela metade. A meta é 50%.

**Saúde (RF09 e RN09)**

- **Questão em aberto:** questão sem acerto do aluno numa atividade publicada da turma cuja situação é "aberta" pela regra de `_situacao`, e em que o aluno ainda pode enviar. Quem já usou o `max_tentativas` da atividade naquela questão, contando todas as tentativas como faz `submeter`, não tem mais o que fazer nela, então ela deixa de estar em aberto para ele.
- **Pendente:** o aluno tem ao menos uma questão em aberto. A trilha não deixa ninguém pendente, porque é treino opcional.
- **Dias sem envio:** tempo desde o último envio do aluno, de lista ou de trilha, falha técnica incluída. Quem nunca enviou conta desde a matrícula.
- Quem não está pendente fica fora do risco, mesmo parado há muito tempo (RN09).
- **Vermelho**, se pendente e com uma destas condições:
  - mais de 14 dias sem envio, com o motivo "Mais de 14 dias sem envio"
  - mais de 7 dias sem envio e o último envio do aluno é um erro de lista numa questão em aberto, com o motivo "Parou depois de errar"
- **Amarelo**, se pendente, não vermelho e com uma destas condições:
  - 7 dias ou mais sem envio, com o motivo "7 a 14 dias sem envio"
  - uma questão em aberto com 5 erros ou mais, com o motivo "5 erros seguidos na mesma questão". Como a questão não tem acerto, os erros dela são seguidos por definição.
- Se mais de uma condição vale, o motivo é o da primeira na ordem acima.
- Cada lista vem ordenada por dias sem envio, do maior para o menor, e depois por nome.
- `taxa_vermelho`: `vermelhos / matriculados × 100`, com meta de menos de 15%.

**Proteção**

- `media_tentativas_ate_acertar`: média, entre os itens com acerto, do número de tentativas até o primeiro acerto, contando o acerto e sem contar falha técnica. Nula sem item com acerto.
- `acerto_de_primeira`: itens cuja primeira tentativa que não é falha técnica é um acerto, divididos pelos itens com ao menos uma tentativa que não é falha técnica, vezes 100. Nulo sem esses itens.
- As duas olham todo o histórico da turma.

**Total de todas as turmas, no script**

- A North Star geral conta cada item uma vez. Questão já pertence a uma turma só, e o treino de cada aluno entra uma vez, mesmo que ele esteja em várias turmas. Por isso o total não é a soma das turmas.
- `professores_com_turma`: professores com ao menos uma turma. `turmas_com_matricula`: turmas com ao menos uma matrícula.
- `matriculados` e `ativados` do total contam alunos distintos. Ativado no total é quem está ativado em ao menos uma turma.
- A retenção do total, na última semana completa, usa os envios de cada aluno em qualquer turma e na trilha, sobre os alunos distintos matriculados até o fim da semana.

**Números:** taxas e médias com uma casa decimal. Taxas em porcentagem.

## Dados

- **Migração `0017_alunos_previstos_da_turma.py`**, com `revision = '0017'` e `down_revision = '0016'`. Acrescenta `turmas.alunos_previstos`, inteiro e nulo permitido. O `downgrade` remove a coluna. As turmas que já existem ficam com nulo.
- **ORM:** `Turma.alunos_previstos = Column(Integer, nullable=True)`, com um comentário curto dizendo que é o tamanho da turma informado pelo professor e o denominador da aquisição.
- **Banco de teste:** aplicar com `ALTER TABLE turmas ADD COLUMN IF NOT EXISTS alunos_previstos INTEGER`, porque o `create_all` do `conftest.py` não altera tabela existente. Registrar no relatório da tarefa.
- Nenhuma tabela nova. Nenhum dado existente muda.

## Backend

**Esquemas (`app/models/schemas.py`)**

- `TurmaCreate` e `TurmaUpdate` ganham `alunos_previstos: Optional[int] = Field(None, ge=1, le=1000)`.
- `TurmaResponse` e `TurmaDetailResponse` ganham `alunos_previstos: Optional[int] = None`.
- `FunilTurmaResponse`, com submodelos, nesta forma:

```
FunilTurmaResponse
  turma_id: int
  gerado_em: str                      # ISO, o "agora" do cálculo
  north_star:
    semana_atual: int
    total: int
    semanas: [{ semana: str, erros_corrigidos: int }]          # 8 entradas
  aquisicao:
    matriculados: int
    alunos_previstos: int | None
    taxa_matriculados: float | None
    primeira_semana: int
    taxa_primeira_semana: float | None
    meta: float                                                # 80
  ativacao:
    matriculados: int
    com_primeiro_envio: int
    ativados: int
    taxa: float | None
    meta: float                                                # 60
  retencao:
    semanas: [{ semana: str, base: int, voltaram: int, por_conta_propria: int,
                taxa: float | None, taxa_por_conta_propria: float | None }]  # 8 entradas
    ultima_completa: (mesma forma de uma semana)
    meta: float                                                # 50
  saude:
    vermelho: [AlunoEmRisco]
    amarelo: [AlunoEmRisco]
    taxa_vermelho: float | None
    meta: float                                                # 15
  protecao:
    media_tentativas_ate_acertar: float | None
    acerto_de_primeira: float | None
    itens_com_acerto: int

AlunoEmRisco
  student_id: int
  nome: str
  motivo: str
  dias_sem_envio: int                 # dias inteiros, arredondados para baixo
  ultimo_envio: str | None            # ISO, nulo para quem nunca enviou
```

**Turma (`app/services/turma_service.py` e `app/api/routes/turma.py`)**

- `create_turma` recebe `alunos_previstos` opcional e grava.
- No `PUT /turmas/{id}`, nome e código continuam sendo substituídos como hoje. O `alunos_previstos` só muda quando vem no corpo (`model_fields_set`), e `null` limpa o campo. Assim um cliente que manda só nome e código não apaga o tamanho da turma.
- `list_turmas` e `get_turma_detail` devolvem `alunos_previstos`.

**Serviço novo `app/services/funil_service.py`**

- `funil_da_turma(turma: Turma, db: Session, agora: datetime | None = None) -> dict`, que devolve a forma de `FunilTurmaResponse`.
- `funil_geral(db: Session, agora: datetime | None = None) -> dict`, que devolve `total` (North Star das 8 semanas e total, professores com turma, turmas com matrícula, matriculados, ativados, taxa de ativação e retenção da última semana completa) e `por_turma` (para cada turma, id, nome, nome do professor, matriculados, alunos previstos, taxa de ativação, taxa de retenção da última semana completa, North Star da semana atual e total e quantos vermelhos).
- `agora` é datetime UTC sem fuso, como o resto do banco. O padrão é `datetime.utcnow()`.
- **Leitura:** poucas consultas em lote por turma (matrículas com o nome do aluno, envios de lista com as colunas que a conta usa, por junção com `Question` e `Exam`, tentativas de trilha dos matriculados e as questões das atividades publicadas da turma com a situação de cada atividade). Nada de carregar relação preguiçosa dentro de laço. O resultado vira registros simples, um por tentativa, com aluno, item, momento, resultado (acerto, erro ou falha técnica), origem (lista ou trilha) e se a atividade é de treino.
- **Regra:** funções puras sobre esses registros, testáveis sem banco, uma por bloco (erros corrigidos, aquisição, ativação, retenção, saúde e proteção).
- **Reaproveitamento:** usa `_semana` e `_situacao` de `student_activity_service`. O plano de tarefas decide se elas mudam para um módulo comum.
- **Constantes no serviço:** as metas (80, 60, 50 e 15), a janela da primeira semana e da ativação (7 dias), os limites da saúde (7 e 14 dias e 5 erros) e o número de semanas (8). A resposta devolve as metas para o painel e o script usarem os mesmos números.

**Rota nova**

- `GET /turmas/{turma_id}/funil` em `app/api/routes/turma.py`, com `response_model=FunilTurmaResponse`.
- Papel: `get_current_professor`. Sem token ou com token de aluno, 401, que é o comportamento de hoje dessa dependência.
- Posse: `_get_turma_or_404`. Turma de outro professor ou inexistente dá 404 com "Turma não encontrada.".
- A rota só valida e delega para `funil_da_turma`. Só lê, sem efeito no banco e sem chamada ao Gemini.

**Script `backend/scripts/funil.py`**

- Docstring com o uso, no estilo de `compare_strategies.py`. Carrega o `.env` e ajusta o `sys.path` como ele.
- Função `relatorio(db: Session, agora: datetime | None = None) -> str`, que monta o texto a partir de `funil_geral`, separada do `if __name__ == "__main__"`, que abre `SessionLocal`, imprime e fecha a sessão.
- O texto traz a North Star geral das 8 semanas, uma linha com o total e uma linha por turma. Nenhum nome de aluno aparece, só números. O nome da turma e do professor aparecem.
- Base vazia imprime o cabeçalho com zeros e a frase "Nenhuma turma cadastrada.", sem erro.

## Frontend

- **`frontend/src/api/exam.js`:** `getTurmaFunil(id)`, que chama `GET /turmas/${id}/funil`. `createTurma(nome, codigo, alunosPrevistos = null)` e `updateTurma(id, nome, codigo, alunosPrevistos = null)` passam a mandar `alunos_previstos`.
- **`frontend/src/pages/TurmaListPage.jsx`:** campo numérico "Alunos na turma (opcional)", de 1 a 1000, no formulário de criação e no modal de edição. O modal abre com o valor atual. Campo vazio manda `null`.
- **`frontend/src/components/FunilDaTurma.jsx`:** recebe `turmaId` e uma chave de recarga, faz a própria chamada e mostra os estados de carregando, erro, turma vazia e cheio. Segue o visual dos cartões da página (fundo branco, borda cinza, títulos em `text-sm font-semibold`). As 8 semanas usam o `BarList` que já existe, com o rótulo `dd/mm` da segunda-feira. Cada cartão de etapa mostra a meta ao lado do número, em verde quando atingida e em cinza quando não. Os alunos em risco usam o `Badge` que já existe para vermelho e amarelo. Sem biblioteca nova.
- **`frontend/src/pages/TurmaDetailPage.jsx`:** renderiza `<FunilDaTurma>` logo abaixo dos cartões de resumo e troca a chave de recarga depois de excluir uma atividade.

## Regras de uso responsável

- **RN05:** a North Star aparece só como número da turma, sem contagem por aluno e sem ranking. A lista de risco traz nome, motivo e último envio, nunca quantos erros cada aluno corrigiu.
- **RN09:** quem não tem questão em aberto fica fora do risco, mesmo parado. O motivo separa quem parou depois de errar de quem só está sem enviar.
- **RNF04:** nomes de aluno só saem na rota do professor dono da turma, com a posse conferida por `_get_turma_or_404`. O script da equipe mostra só números agregados.
- **Fronteira da trilha:** a migração 0016 deixou a trilha fora do painel do professor. Aqui ela entra só como contagem agregada (erros corrigidos, ativação e retenção) e como sinal de que o aluno está ativo nos dias sem envio. O professor nunca vê o que um aluno fez na trilha, e a trilha nunca vira motivo de risco.
- Nesta parte nada aparece para o aluno, então nenhuma regra de aviso ou de mensagem ao aluno se aplica.

## Testes

**Regra pura (sem banco)**

- Erro corrigido:
  - errou e acertou conta um, na semana do acerto
  - acertou de primeira não conta
  - errou, acertou, errou e acertou de novo conta um
  - só errou não conta
  - falha técnica e depois acerto não conta
  - erro na trilha e depois acerto na trilha conta
  - as 8 semanas vêm sempre, com zero onde não houve nada
- Aquisição: com e sem `alunos_previstos`, matrícula no sétimo dia entra na primeira semana e no oitavo não entra.
- Ativação: primeiro acerto depois de erro no sétimo dia ativa e no oitavo não ativa, e quem só enviou sem corrigir conta em `com_primeiro_envio` e não em `ativados`.
- Retenção:
  - envio antes e na semana conta como voltou
  - primeiro envio do aluno na semana não conta
  - por conta própria só com envio em atividade de treino ou na trilha
  - quem entrou depois do fim da semana fica fora da base
  - base zero dá taxa nula
- Saúde:
  - pendente com 15 dias sem envio é vermelho
  - pendente com 8 dias sem envio e último envio errado numa questão em aberto é vermelho por "Parou depois de errar"
  - pendente com 8 dias sem envio e último envio certo é amarelo
  - pendente com 3 dias sem envio e 5 erros numa questão em aberto é amarelo
  - matriculado há 15 dias que nunca enviou e está pendente é vermelho, e há 8 dias é amarelo
  - quem resolveu todas as questões abertas fica fora, mesmo 30 dias parado
  - questão sem acerto só em atividade encerrada ou agendada não deixa pendente
  - questão sem acerto em que o aluno já usou o `max_tentativas` não deixa pendente
  - envio na trilha conta para os dias sem envio, e 5 erros na trilha não viram motivo
- Proteção: média de tentativas até acertar e acerto de primeira, com a falha técnica ignorada nas duas.

**Serviço com banco**

- `funil_da_turma` ignora envio sem `student_id` e envio em atividade não publicada.
- O treino de um aluno em duas turmas aparece nas duas turmas e uma vez só em `funil_geral`.

**Rota e turma**

- O dono recebe 200 com a forma de `FunilTurmaResponse`.
- Outro professor recebe 404. Token de aluno e falta de token recebem 401.
- `alunos_previstos` igual a 0 ou a 1001 é recusado com 422.
- Criar com o campo devolve o campo em `POST /turmas` e em `GET /turmas`.
- `PUT` sem o campo mantém o valor, e `PUT` com `null` limpa.

**Script**

- `relatorio` numa base vazia roda sem erro e traz "Nenhuma turma cadastrada.".
- Com uma turma, o texto traz a linha dela e nenhum nome de aluno.

**Frontend**

- O front não tem testes automatizados. `npm run build` passa e `npm run lint` não ganha erro novo. Conferência no navegador com a turma de demonstração: o bloco com dados, a turma vazia e o campo novo na criação e na edição.

## Fora do escopo

- Registro de acesso, origem do cadastro, link de convite, abertura sem aviso e retorno medido pelo acesso, que são a parte 2.
- Tempo até o momento de sucesso do RF16, que precisa da sessão de acesso da parte 2.
- O 1.1 nas páginas do aluno, que vira volta própria.
- Grupos sem retorno há 14 dias, do 1.5 e do RF10.
- Receita e indicação, medidas fora do produto durante o piloto.
- Proporção de envios às cegas e aprovação contra a linha de base, as outras métricas de proteção do Plano de Growth.
- Foto semanal em tabela, view no Postgres e cache do cálculo.
- Aviso ao professor ou ao aluno, e qualquer mudança na área do aluno.

## Decisões

1. **Duas partes.** A parte 1 usa só o que o banco já guarda, e a parte 2 traz o registro de acesso. Decidido no desenho.
2. **Tamanho da turma como campo opcional que o professor preenche**, de 1 a 1000, porque o sistema não sabe quantos alunos a turma tem de verdade. Decidido no desenho.
3. **Cálculo na hora num serviço.** A foto semanal em tabela pede agendador, e a view no Postgres foge do padrão e não roda nos testes com `create_all`. Decidido no desenho.
4. **Treino conta em todas as turmas do aluno e uma vez no total**, porque `ExercicioGerado` não tem `turma_id`. Decidido no desenho.
5. **Falha técnica conta como envio e não como erro**, para uma queda do Docker não inflar a North Star nem marcar aluno como parado depois de errar. Decisão do spec.
6. **Acerto pela regra que cada lado já usa:** "Correto" na lista e `all_tests_passed` na trilha. Decisão do spec.
7. **Retenção pelos envios** até a parte 2 trazer o acesso. Decidido no desenho.
8. **O cartão de retenção mostra a última semana completa**, porque a taxa da semana atual sobe ao longo dos dias e parece queda na segunda-feira. Decisão do spec.
9. **A trilha não deixa aluno pendente nem vira motivo de risco**, para respeitar a fronteira da 0016 e porque a trilha é opcional. Ela só tira o aluno da contagem de dias sem envio. Decisão do spec.
10. **O `PUT` só mexe em `alunos_previstos` quando o campo vem no corpo**, para um cliente que manda só nome e código não apagar o tamanho da turma. Decisão do spec.
11. **Metas como constantes no serviço e devolvidas na resposta**, para o painel e o script usarem os mesmos números. Decisão do spec.
12. **Semana pela data UTC**, como todo o banco grava. Um envio de domingo às 22h em Brasília cai na segunda-feira seguinte. A diferença é pequena e não justifica fuso só nesta conta. Decisão do spec.
13. **Script no lugar de rota de administrador**, para a equipe acompanhar o total sem criar papel novo. Decidido no desenho.
