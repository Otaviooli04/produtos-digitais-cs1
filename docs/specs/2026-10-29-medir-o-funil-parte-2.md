# Medir o funil, parte 2: acesso, convite e sinais de hábito

**Item do plano:** volta "medir o funil", parte 2 (seção 10.2 de `docs/produto/plano-implementacao.md`), que junta o 1.2, o G3 e o resto do 1.3, mais o filtro da trilha pela data de entrada que ficou pendente da parte 1
**Requisitos:** RF06 (mensagem pronta para divulgar a turma), RF14 (registro de acesso com origem), RF15 (retorno sem prova marcada e abertura sem aviso), RF16 (tempo até o momento de sucesso), RN05, RN09, RNF04
**Data:** 2026-10-29

## Objetivo

Registrar cada abertura do app do aluno, com a origem, e usar esse registro para medir a retenção de verdade, os sinais de hábito e o tempo até o momento de sucesso. Dar ao professor um convite com link que já leva o código da turma e gravar de onde veio cada matrícula. Corrigir a contagem da trilha, que passa a valer numa turma só a partir da matrícula do aluno nela.

## Comportamento

**Aluno**

1. Toda vez que abre o app do aluno, ou volta para a aba dele, o app avisa o servidor. Nada aparece na tela.
2. Recebe do professor uma mensagem com o link `/aluno/convite/ABC234`.
   - Já logado: o link põe o aluno na turma e abre a página dela.
   - Sem login: o link leva ao cadastro, que mostra "Depois de entrar, você vai direto para a turma." O mesmo aviso aparece no login, se ele for por "Já tenho conta". Com a conta pronta, ele entra na turma e cai na página dela, sem digitar o código.
   - Código que não existe: a página mostra "Este convite não vale mais. Peça o código ao professor." e o link "Ir para minhas turmas".
3. Quem digita o código na página de turmas continua entrando como hoje.

**Professor**

1. No bloco do código de acesso da turma, aparece o botão "Copiar convite" ao lado de "Copiar código". Ele copia a mensagem pronta:

   > Nossa turma de {nome da turma} vai usar o Analytics CS1 nas listas e no treino. Para entrar, abra {endereço do site}/aluno/convite/{CÓDIGO} e crie sua conta. Se preferir, use o código {CÓDIGO} na área do aluno.

   O botão mostra "Copiado" por um instante, como o do código. O texto de ajuda do bloco passa a ser "Passe o código ou o convite com link, que já leva o código. N já entraram com conta.", com a mesma concordância de hoje para um aluno.
2. No bloco "Funil da turma":
   - **Aquisição:** o detalhe ganha "N pelo convite, M pelo código." Sem nenhuma matrícula com origem gravada, a frase não aparece.
   - **Ativação:** ganha a linha do momento de sucesso, "Momento de sucesso: mediana de 2 h 15 min depois da matrícula. 40% chegaram na mesma sessão." Se ninguém chegou, "Momento de sucesso: ninguém corrigiu um erro ainda."
   - **Retenção:** o número passa a ser a taxa pelo acesso, com o detalhe "X de Y abriram o app na semana de dd/mm. Pelo envio, Z%."
   - **Sinais de hábito:** linha nova abaixo dos cartões de etapa, no estilo da linha de proteção, "Hábito na semana de dd/mm: X% voltaram sem prova marcada, Y% abriram sem aviso e Z% enviaram no treino."

**Equipe:** o script `scripts/funil.py` passa a mostrar a retenção pelo acesso e pelo envio, as matrículas por origem e a taxa de quem chegou ao momento de sucesso na mesma sessão.

## Definições

Detalham a seção 1 do desenho, aprovada em 28/10. Continuam valendo todas as definições da parte 1 (`docs/specs/2026-10-26-medir-o-funil.md`) que não mudam aqui.

**Acesso**

- **Acesso:** uma linha em `acessos` com o aluno, o momento (UTC sem fuso, como o resto do banco) e a origem (`via`), que pode ser nula.
- **Origens aceitas:** só `convite` por enquanto, numa constante do serviço. A `via` recebida passa por `strip().lower()`. Vazia ou fora da lista vira nula. Os tipos de aviso entram na lista nas fases 3 e 4.
- **Descarte em 30 minutos:** recentes são os acessos do aluno com momento menos de 30 minutos antes de agora. O servidor não grava o acesso novo quando uma destas condições vale:
  - o novo vem sem origem e há algum acesso recente, com qualquer origem
  - o novo vem com origem e há algum acesso recente com a mesma origem
- Assim, reabrir o app ou voltar à aba em menos de 30 minutos não conta, e abrir por um link com origem logo depois de abrir o app conta. Exatamente 30 minutos depois já grava de novo.
- O acesso não guarda IP, navegador nem página.

**Origem da matrícula**

- `enrollments.origem`: `convite` quando o aluno entrou pelo link, `codigo` quando digitou o código, nula nas matrículas de antes desta mudança.
- Só é gravada quando a matrícula é criada. Entrar de novo na mesma turma, por qualquer caminho, não muda a origem.

**Filtro pela matrícula (muda a decisão 4 da parte 1)**

- Em cada turma, as tentativas da trilha e os acessos de um aluno só contam a partir da matrícula dele nessa turma, com momento maior ou igual à entrada. Os de antes são descartados na leitura, antes de qualquer conta. Isso vale para a North Star, a ativação, a retenção, os sinais, o momento de sucesso, a proteção e a saúde.
- Os envios de lista não mudam. Eles já são da turma, e os de antes da matrícula só existem quando a conta religa envios antigos pela matrícula institucional.
- No total do script, cada aluno conta a partir da primeira matrícula dele, porque o total junta o que cada turma leu.

**Atividade anterior**

- Para a retenção pelo acesso e os sinais, o aluno tem atividade antes de um instante quando tem um acesso ou um envio (de lista ou de trilha, falha técnica incluída) com momento anterior a ele, já com o filtro acima.

**Prova que puxa**

- Entram as atividades publicadas da turma que não são de treino (`modo` diferente de "treino") e têm ao menos uma das duas datas.
- Cada uma puxa num intervalo fechado. O início é `abre_em` menos 3 dias, ou sem limite quando não há `abre_em`. O fim é `fecha_em`, ou sem limite quando não há `fecha_em`.
- Um instante está **com prova marcada** quando ao menos uma prova da turma puxa nele. Exatamente 3 dias antes de `abre_em` já puxa, e exatamente em `fecha_em` ainda puxa.
- Prova sem nenhuma data nunca puxa. Atividade de treino nunca puxa.

**Retenção, por semana**

- `base`: como na parte 1, os matriculados com entrada antes do fim da semana.
- `voltaram`: alunos da base com acesso na semana e atividade anterior ao início dela.
- `sem_prova_marcada`: alunos de `voltaram` com ao menos um acesso na semana num instante sem prova marcada.
- `sem_aviso`: alunos de `voltaram` com ao menos um acesso sem origem na semana.
- `voltaram_por_envio`: o `voltaram` da parte 1, sem mudança, com envio na semana e envio antes dela.
- `por_conta_propria`: o da parte 1, sem mudança.
- As taxas são a contagem dividida pela `base`, vezes 100, com uma casa, e ficam nulas com base zero: `taxa`, `taxa_sem_prova_marcada`, `taxa_sem_aviso`, `taxa_por_envio` e `taxa_por_conta_propria`.
- O cartão continua mostrando a última semana completa, e a meta de 50% se compara com a `taxa` pelo acesso.

**Sessão e momento de sucesso (RF16)**

- **Eventos do aluno na turma:** a matrícula, os acessos e as tentativas de lista e de trilha, já com o filtro, em ordem de momento.
- **Sessão da matrícula:** começa na matrícula e segue pelos eventos seguintes enquanto cada um vier até 30 minutos depois do anterior. O primeiro intervalo maior que 30 minutos encerra a sessão. Exatamente 30 minutos ainda é a mesma sessão.
- **Momento de sucesso:** o primeiro erro corrigido do aluno na turma, pela regra da parte 1, em lista ou trilha, com momento a partir da matrícula.
- `chegaram`: matriculados com momento de sucesso.
- `ainda_nao_chegaram`: matriculados sem momento de sucesso.
- `mediana_minutos`: a mediana, entre os que chegaram, dos minutos entre a matrícula e o momento de sucesso, com uma casa. Com quantidade par, é a média dos dois do meio. Nula quando ninguém chegou.
- `na_sessao_da_matricula`: matriculados cujo momento de sucesso caiu dentro da sessão da matrícula.
- `taxa_na_sessao_da_matricula`: `na_sessao_da_matricula / matriculados × 100`, nula sem matriculados.
- Não há meta numérica. A meta do plano de CS é "no primeiro acesso", e esta taxa é a leitura dela.

**Aquisição por origem**

- `por_origem`: `convite`, `codigo` e `sem_origem`, contando as matrículas da turma por `enrollments.origem`. Os três somam `matriculados`.

**Total de todas as turmas, no script**

- `retencao_ultima_semana` do total traz só `semana`, `base`, `voltaram`, `taxa`, `voltaram_por_envio` e `taxa_por_envio`, calculados com os acessos e as tentativas de todos os alunos, cada um a partir da primeira matrícula. Os sinais ficam de fora do total, porque a prova é de uma turma e o total junta alunos de turmas diferentes.
- Cada linha de `por_turma` ganha `taxa_retencao_envio`, `por_origem` e `taxa_sucesso_na_sessao`, e `taxa_retencao` passa a ser pelo acesso.

## Dados

- **Migração `0018_acessos_e_origem_da_matricula.py`**, com `revision = '0018'` e `down_revision = '0017'`:
  - cria `acessos` com `id` (inteiro, chave primária), `student_id` (inteiro, obrigatório, chave estrangeira para `students.id`, como na 0016), `momento` (DateTime, obrigatório) e `via` (String(32), nula permitida), mais o índice `ix_acessos_student_id_momento` em `(student_id, momento)`
  - acrescenta `enrollments.origem`, String(16), nula permitida
  - o `downgrade` remove a coluna e a tabela
- As matrículas que já existem ficam com `origem` nula. Nenhum outro dado muda.
- **ORM:** modelo `Acesso` (`__tablename__ = "acessos"`, `momento` com `default=datetime.utcnow`), relação `Student.acessos` com `cascade="all, delete-orphan"`, como `Student.enrollments`, coluna `Enrollment.origem` e as constantes `Enrollment.ORIGEM_CONVITE = "convite"` e `Enrollment.ORIGEM_CODIGO = "codigo"`, no padrão de `Exam.MODO_TREINO`.
- **Banco de teste:** aplicar `ALTER TABLE enrollments ADD COLUMN IF NOT EXISTS origem VARCHAR(16)`, porque o `create_all` do `conftest.py` não altera tabela existente. A tabela nova ele cria. Registrar no relatório da tarefa.
- O item 0.2 do plano, que tira `umap_x` e `umap_y`, passa a ser a migração 0019.

## Backend

**Esquemas (`app/models/schemas.py`)**

- `AcessoRequest` com `via: Optional[str] = Field(None, max_length=32)`.
- `TurmaEntrarRequest` ganha `origem: Literal["convite", "codigo"] = "codigo"`. O padrão mantém funcionando o cliente que não manda o campo.
- A resposta do funil muda assim:

```
AquisicaoFunil
  ... (campos da parte 1)
  por_origem: { convite: int, codigo: int, sem_origem: int }

SemanaRetencao
  semana: str
  base: int
  voltaram: int                          # pelo acesso
  taxa: float | None
  sem_prova_marcada: int
  taxa_sem_prova_marcada: float | None
  sem_aviso: int
  taxa_sem_aviso: float | None
  voltaram_por_envio: int                # o voltaram da parte 1
  taxa_por_envio: float | None
  por_conta_propria: int
  taxa_por_conta_propria: float | None

SucessoFunil
  chegaram: int
  ainda_nao_chegaram: int
  mediana_minutos: float | None
  na_sessao_da_matricula: int
  taxa_na_sessao_da_matricula: float | None

FunilTurmaResponse
  ... (campos da parte 1)
  sucesso: SucessoFunil
```

**Serviço novo `app/services/acesso_service.py`**

- `registrar_acesso(student_id: int, via: str | None, db: Session, agora: datetime | None = None) -> bool`, que normaliza a origem, aplica o descarte em 30 minutos e grava. Devolve `True` quando grava.
- Constantes `VIAS_ACEITAS = {"convite"}` e `JANELA_DO_ACESSO = timedelta(minutes=30)`.
- Uma consulta busca os acessos do aluno dentro da janela, e a regra decide em cima dela.
- Sem trava contra pedidos simultâneos. Duas linhas quase iguais não mudam nenhuma conta, porque a retenção trabalha com conjuntos de alunos por semana e a sessão com intervalos.

**Rota nova `POST /aluno/acessos`** em `app/api/routes/student.py`

- Corpo `AcessoRequest`, resposta 204 sem corpo, papel `get_current_student`.
- O aluno é sempre o do token. A rota só valida e delega para `registrar_acesso`.
- Sem token ou com token de professor, 401, que é o comportamento da dependência. `via` com mais de 32 caracteres, 422.

**Entrada na turma**

- `entrar_na_turma(student, codigo_acesso, db, origem=Enrollment.ORIGEM_CODIGO)` em `app/auth/student_service.py` grava a origem ao criar a matrícula e não mexe numa matrícula que já existe.
- `POST /aluno/turmas/entrar` repassa `body.origem`. Origem fora da lista dá 422 pelo esquema.

**Funil (`app/services/funil_service.py` e `app/services/funil_regras.py`)**

- **Registros:** `Matricula` ganha `origem: str | None = None`. Entram o registro congelado `Acesso(aluno, momento, via)` e `JanelaDeProva(inicio, fim)`, com os dois lados opcionais.
- **Leitura:** `_matriculas` lê também a origem. `_acessos(alunos, db)` lê os acessos dos matriculados numa consulta. `_datas_das_provas(turma_id, db)` lê `abre_em` e `fecha_em` das provas publicadas da turma numa consulta.
- **Filtro:** `_dados_da_turma` descarta as tentativas de trilha e os acessos de antes da matrícula de cada aluno e passa a carregar os acessos e as janelas das provas.
- **Regras puras novas**, testáveis sem banco: `janela_da_prova(abre_em, fecha_em)`, que devolve a janela ou nada para prova sem data, `com_prova_marcada(momento, janelas)`, `por_origem(matriculas)`, `fim_da_sessao(entrada, momentos)` e `sucesso(matriculas, tentativas, acessos, corrigidos)`. `retencao_da_semana` e `retencao` passam a receber os acessos e as janelas.
- **Constantes novas:** `ANTECEDENCIA_DA_PROVA = timedelta(days=3)` e `JANELA_DA_SESSAO = timedelta(minutes=30)`.
- O plano de tarefas decide se `montar_funil` passa a receber os dados da turma num registro só, em vez de argumentos soltos.
- **Saúde:** a regra não muda. Ela só passa a receber as tentativas já filtradas.
- **`funil_geral`:** junta os acessos de todas as turmas como já junta as tentativas e monta o total e as linhas por turma na forma descrita nas definições.
- A leitura do funil continua sem escrita no banco e sem chamada ao Gemini.

**Script `backend/scripts/funil.py`**

- A linha da retenção do total mostra o acesso e o envio: "Retenção na semana de {semana}: {voltaram} de {base} pelo acesso ({taxa}), {voltaram_por_envio} pelo envio ({taxa_por_envio})".
- A linha de cada turma ganha "retenção {taxa} pelo acesso e {taxa} pelo envio", "{convite} pelo convite, {codigo} pelo código e {sem_origem} sem origem" e "{taxa} chegaram ao momento de sucesso na mesma sessão".
- Continua sem nenhum nome de aluno.

## Frontend

- **`frontend/src/api/aluno.js`:** `registrarAcesso(via = null)`, que chama `POST /aluno/acessos` com `{ via }`. `entrarNaTurma(codigoAcesso, origem = 'codigo')` passa a mandar a origem.
- **`frontend/src/components/AlunoLayout.jsx`:** registra o acesso em três momentos:
  - ao montar, com a `via` da URL, se houver
  - quando aparece uma `via` nova na URL
  - quando `document.visibilityState` volta a ser `visible`, sem origem
- Depois de registrar com origem, o layout tira o `via` da URL com `replace`, mantendo os outros parâmetros. A saída do `via` da URL não dispara registro. Erro na chamada é ignorado em silêncio. O ouvinte de visibilidade sai quando o layout desmonta.
- **`frontend/src/utils/convitePendente.js`:** `guardarConvite(codigo)`, `lerConvite()` e `apagarConvite()`, sobre a chave `convite_pendente` do `sessionStorage`, cada uma dentro de `try/catch`. Sem `sessionStorage`, ler devolve nulo e as outras não fazem nada.
- **`frontend/src/pages/aluno/ConvitePage.jsx`**, na rota `aluno/convite/:codigo` do `App.jsx`, fora do `AlunoProtectedRoute`:
  1. Ao abrir, guarda o código. Guardar antes de qualquer coisa cobre o token vencido, em que o cliente do aluno manda direto para o login.
  2. Espera o `loading` do `AlunoAuthContext`.
  3. Sem login, vai para `/aluno/cadastro` com `replace`.
  4. Com login, chama `entrarNaTurma(codigo, 'convite')`. Se der certo, apaga o código guardado e vai para `/aluno/turmas/{id}?via=convite` com `replace`. Se der 404, apaga o código guardado e mostra a mensagem de convite inválido com o link "Ir para minhas turmas".
  5. Enquanto entra, mostra o logo e um spinner com "Entrando na turma...".
- **`AlunoRegisterPage.jsx` e `AlunoLoginPage.jsx`:** leem o convite guardado. Com ele, mostram "Depois de entrar, você vai direto para a turma." acima do formulário e, quando dão certo, vão para `/aluno/convite/{código}` em vez de `/aluno`. Sem convite, nada muda.
- **`TurmasPage.jsx`:** entra com `entrarNaTurma(codigo, 'codigo')`.
- **`TurmaDetailPage.jsx`:** botão "Copiar convite" ao lado de "Copiar código", com estado "Copiado" próprio, e o texto de ajuda novo. O endereço da mensagem é `window.location.origin`.
- **`FunilDaTurma.jsx`:** as mudanças de aquisição, ativação, retenção e sinais descritas no comportamento. A duração do momento de sucesso usa minutos abaixo de 60 ("45 min"), horas e minutos abaixo de 24 horas ("2 h 15 min", ou "3 h" quando os minutos dão zero) e dias inteiros, arredondados para baixo, daí em diante ("1 dia", "4 dias").
- Sem biblioteca nova. Visual dos componentes que já existem.

## Regras de uso responsável

- **RNF04:** o professor nunca vê o acesso de um aluno específico, só taxas e contagens da turma. Nenhuma rota de professor devolve acesso por aluno, e o script só mostra números. Os nomes continuam aparecendo apenas na lista de risco que já existe. O acesso não guarda IP, navegador nem página, e só aceita origem que está na lista.
- **RN05:** a North Star continua só como número da turma.
- **RN09:** a saúde continua pelos envios, e quem resolveu tudo segue fora do risco. O acesso não entra nela nesta volta.
- **Fronteira da trilha (0016):** a trilha continua entrando só como contagem agregada. O filtro desta parte só tira dela o que veio antes da matrícula.
- **Papel e posse:** `POST /aluno/acessos` só aceita token de aluno e só grava o acesso dele. A origem da matrícula só chega pelo token de aluno. O `GET /turmas/{id}/funil` continua com professor dono.
- **Abuso:** pelo descarte, cada aluno grava no máximo duas linhas a cada 30 minutos, uma sem origem e uma com `convite`.
- Para o aluno, a única novidade é o convite. Nenhum aviso nem mensagem nova.

## Testes

**Regra pura (sem banco)**

- Prova que puxa:
  - com as duas datas, puxa de 3 dias antes de `abre_em` até `fecha_em`, com os dois limites incluídos, e não puxa um segundo antes nem um segundo depois
  - só com `abre_em`, puxa de 3 dias antes em diante
  - só com `fecha_em`, puxa de sempre até ela
  - sem datas, não devolve janela
  - com duas provas, um instante numa delas está com prova marcada
- Retenção pelo acesso:
  - acesso na semana e acesso antes dela conta como voltou
  - acesso na semana e só envio antes dela também conta
  - acesso na semana sem atividade anterior não conta
  - envio na semana sem acesso não conta pelo acesso e conta pelo envio
  - `sem_prova_marcada` conta quem teve um acesso fora das janelas e não conta quem só acessou dentro delas
  - `sem_aviso` conta quem teve acesso sem origem e não conta quem só teve acesso com `convite`
  - base zero deixa todas as taxas nulas
- Sessão:
  - eventos a cada 30 minutos exatos continuam a sessão, e um intervalo de 30 minutos e 1 segundo a encerra
  - sem evento depois da matrícula, a sessão termina na própria matrícula
- Momento de sucesso:
  - aluno que corrigiu um erro na sessão da matrícula conta em `chegaram` e em `na_sessao_da_matricula`
  - aluno que corrigiu um erro em outra sessão conta só em `chegaram`
  - aluno que não corrigiu nada conta em `ainda_nao_chegaram`
  - mediana com quantidade ímpar e par, e nula sem ninguém
  - erro corrigido antes da matrícula não conta
- Aquisição por origem: as três contagens, incluindo a origem nula, somando os matriculados.

**Serviço de acesso (com banco)**

- grava o primeiro acesso
- descarta um acesso sem origem 29 minutos depois de outro sem origem e grava 30 minutos depois
- descarta um acesso sem origem 5 minutos depois de um com `convite`
- grava um acesso com `convite` 5 minutos depois de um sem origem, e descarta outro com `convite` logo em seguida
- `via` desconhecida, vazia ou com maiúsculas e espaços é normalizada, e a desconhecida vira nula
- o acesso de outro aluno não interfere no descarte

**Funil com banco**

- erro corrigido na trilha antes da matrícula fica fora da North Star e da ativação da turma
- o mesmo aluno em duas turmas, com a trilha entre as duas matrículas, conta a trilha só na turma em que já estava
- no `funil_geral`, essa trilha conta uma vez no total
- acesso de antes da matrícula não conta na retenção da turma
- prova não publicada e atividade de treino não puxam
- as linhas de `por_turma` e o total trazem os campos novos

**Rotas**

- `POST /aluno/acessos` com token de aluno devolve 204 e grava, sem token ou com token de professor devolve 401, e com `via` de 33 caracteres devolve 422
- `POST /aluno/turmas/entrar` com `origem` "convite" grava `convite`, sem o campo grava `codigo`, entrar de novo com outra origem não muda a gravada, e origem fora da lista devolve 422
- `GET /turmas/{id}/funil` traz `aquisicao.por_origem`, os campos novos da semana e o bloco `sucesso`

**Script**

- `relatorio` numa base vazia continua rodando sem erro
- com uma turma, a linha dela traz a retenção pelo acesso e pelo envio, as origens e a taxa do momento de sucesso, sem nome de aluno

**Frontend**

- O front não tem testes automatizados. `npm run build` passa e `npm run lint` não ganha erro novo.
- Conferência no navegador pelo Otávio: convite com login, sem login pelo cadastro, sem login pelo login, código inválido, mensagem copiada, painel com os números novos e tamanho de celular.

## Fora do escopo

- Avisos e novidades no app (3.1, 3.2 e fase 4) e as origens de acesso que eles vão trazer.
- A saúde do aluno pelo acesso.
- A comparação do experimento 1 entre quem recebeu novidade e quem não recebeu, que depende do 3.1.
- As matrículas nas primeiras 48 horas do experimento 6. Os dados ficam gravados, mas a conta não entra agora.
- QR code do convite.
- Os sinais de hábito no total do script.
- O 1.1 e os itens 0.2 a 0.9.
- Fuso horário. A semana continua em UTC, como na parte 1.

## Decisões

1. **Uma volta só, com uma migração**, para o acesso, o convite, os sinais, o RF16 e o filtro, porque todos mexem no mesmo serviço e o convite é pequeno. Decidido no desenho.
2. **Trilha e acessos contam numa turma só a partir da matrícula nela**, o que muda a decisão 4 da parte 1. Assim a turma não ganha trabalho feito antes de o aluno entrar. Decisão do Otávio em 28/10.
3. **Retenção pelo acesso no cartão, com a do envio ao lado**, porque o experimento 1 se mede pela volta ao app e o envio guarda o histórico de antes da tabela. Decisão do Otávio no desenho.
4. **"Sem prova marcada" pelo instante do acesso**, com a prova puxando de 3 dias antes da abertura até o fechamento, a mesma janela do aviso "Prova chegando". Prova sem data não puxa. Decisão do Otávio no desenho.
5. **Momento de sucesso contado da matrícula**, não do primeiro acesso, porque entrar na turma já é um momento no app e assim os alunos que já existem também entram na conta. Sessão encerrada por 30 minutos sem evento, a mesma janela do acesso. Decidido no desenho.
6. **Convite que entra sozinho**, com o código guardado no `sessionStorage` durante o cadastro ou o login, que é o caminho com menos atrito. Decisão do Otávio no desenho.
7. **Registro por rota própria chamada pelo `AlunoLayout`**, em vez de gravar em toda requisição, para não pôr escrita na autenticação nem contar chamada de fundo como abertura. Decisão do Otávio no desenho.
8. **Acesso sem origem descartado perto de qualquer acesso recente**, e não só de um com a mesma origem. Isso refina a regra da seção 1 do desenho, para quem entra pelo convite e volta à aba logo depois não ganhar uma "abertura sem aviso" falsa. Decisão do spec.
9. **Só a origem `convite` aceita por enquanto**, com valor desconhecido gravado como nulo, para não guardar texto livre vindo da URL. Decidido no desenho.
10. **Sem trava contra pedidos simultâneos de acesso**, porque linhas quase iguais não mudam nenhuma conta. Decidido no desenho.
11. **Atividade anterior inclui envio**, para as semanas de antes da tabela de acessos não aparecerem zeradas. Decidido no desenho.
12. **Sinais contados entre os que voltaram e taxas sobre a base**, como o "por conta própria" da parte 1, para os números serem comparáveis entre si. Decisão do spec.
13. **Total do script sem os sinais**, porque a prova pertence a uma turma e o total junta alunos de turmas diferentes. Decisão do spec.
14. **Saúde continua pelos envios**, para não mudar o risco junto com a medição. Decidido no desenho.
15. **A página do convite guarda o código antes de conferir o login**, porque com o token vencido o cliente do aluno manda direto para o login e o código se perderia. Decisão do spec.
16. **Chave estrangeira simples, como na 0016**, com a remoção em cascata pelo ORM, como as matrículas. Decisão do spec.
