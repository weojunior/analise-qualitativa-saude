# Pipeline de análise qualitativa em saúde (método Reinert/IRaMuTeQ) no macOS

Reimplementação limpa e auditável do método de análise textual do software
labiia_lex (Prof. Rafael Cardoso Sampaio, UFPR), derivado do IRaMuTeQ
(Pierre Ratinaud, GPL). Roda no macOS com R e Python, cruzando cada análise
entre um motor Python próprio e o código ou pacote R canônico.

## Instalação

- Python 3.12 ou superior, com as dependências de `requirements.txt`:
  ```
  python3 -m venv .venv
  ./.venv/bin/pip install -r requirements.txt
  ```
- R 4.4 ou superior, com os pacotes CRAN: ca, ade4, cluster, proxy, Matrix,
  MASS, irlba, igraph, slam, stringi, textometry, topicmodels.
- Dicionários do IRaMuTeQ apontados pela variável `LABIIALEX_DICT` e, só para a
  distância de Labbé, `LABIIALEX_RSCRIPTS`. Esses recursos não são
  redistribuídos aqui. Ver `SETUP_DICIONARIOS.md`.

Os comandos abaixo assumem que você está na raiz do repositório e usa o Python do
ambiente. Defina uma vez por sessão:

```
PY=./.venv/bin/python
export LABIIALEX_DICT=/caminho/para/dictionaries
```

## Preparação do corpus

Coloque seus documentos numa pasta. Formatos aceitos:
**.txt, .md, .pdf, .docx, .odt** (um arquivo = um documento), **.csv, .xlsx, .tsv**
(uma linha = um documento; a coluna de texto é detectada ou indicada por
`--text-column`, e as demais colunas viram variáveis) e **.zip** (extraído).

Para arquivos de documento único, um `metadata.csv` opcional na mesma pasta
atribui variáveis pelo nome do arquivo:

```
file,grupo,papel
G1_mae01.txt,G1,mae
```

O repositório traz o corpus sintético `corpus_synth` (três classes plantadas) para
teste. A preparação também exporta o corpus limpo em `corpus_iramuteq.txt`, no
formato de texto do IRaMuTeQ (linhas `**** *variavel_modalidade`).

## Fluxo (5 etapas)

A partir da raiz do repositório:

```bash
# Parte 1 — preparação (tokenização IRaMuTeQ, UCI/UCE, matriz UCE x formas)
$PY run_prepare.py --corpus corpus_synth --out output/MEU --uce-size 40 --min-freq 3

# Parte 2 — CHD de Reinert (classes lexicais), cruzamento Python x CHD.R canônico
$PY run_chd.py --prepared output/MEU --n-classes 4

# Parte 3 — AFC + especificidades (Python x ca / textometry)
$PY run_afc_spec.py --prepared output/MEU --variables grupo,papel

# Parte 4 — similitude (rede de coocorrência), cruzamento Python x igraph
$PY run_simi.py --prepared output/MEU --index cooccurrence --top 80

# Parte 5 — LDA, concordâncias e sentimento
$PY run_lda.py --prepared output/MEU --k 4 --level uce
$PY run_kwic.py --prepared output/MEU --query alimentação
$PY run_sentiment.py --prepared output/MEU --level uci

# Parte 8 — emoções NRC (8 categorias, via syuzhet)
$PY run_emotions.py --prepared output/MEU --variables grupo

# Parte 4 com layout Gephi + GEXF (abre no Gephi)
$PY run_simi.py --prepared output/MEU --layout fa2   # gera simi_graph.gexf

# Parte 9 — complementares
$PY run_extras.py --prepared output/MEU --what wordcloud
$PY run_extras.py --prepared output/MEU --what ngrams --n 2   # e --n 3
$PY run_extras.py --prepared output/MEU --what wordtree --query criança --direction right
$PY run_extras.py --prepared output/MEU --what heatmap
$PY run_extras.py --prepared output/MEU --what yake --n 3
```

## Opções de qualidade (melhorias de pré-processamento e robustez)

Na preparação (`run_prepare.py`):
- `--stopwords arq.txt` lista própria de palavras a ignorar (uma por linha)
- `--synonyms arq.csv` unificar variantes (`variante,canonico`; ex.: medicamento→remédio)
- `--expressions arq.txt` preservar expressões multipalavra (ex.: `dor abdominal`)
- `--no-adverbs` tratar advérbios como suplementares
- `--unknown-supplementary` ignorar formas fora do léxico
- `--min-token-len N` tamanho mínimo de token
- Imprime um **diagnóstico** (nº de UCEs, % de formas ativas, hapax, % retido) com
  sugestões de parâmetros, e salva `prepared_diagnostics.json` e `uce_sizes.png`.
- Exporta os textos das UCEs (`uce_texts.csv`) para os segmentos típicos.

Na CHD (`run_chd.py`):
- Fase de **realocação** ligada por padrão (mais fiel ao IRaMuTeQ); `--no-relocate` desliga.
- `--stability` estima a estabilidade das classes por subamostragem.
- Gera `typical_segments.csv` (trechos reais mais representativos de cada classe) e
  **avisos** (classes pequenas, qui-quadrado com célula esperada <5).
- A mesma configuração de pré-processamento da preparação é reusada em KWIC,
  sentimento, LDA e extras (consistência garantida).

Na LDA (`run_lda.py`): `--stability` mede a reprodutibilidade dos tópicos entre sementes.

## Atalho: pipeline completo num comando

```
$PY run_all.py --corpus corpus_synth --out output/ESTUDO \
    --stopwords config_med/stopwords.txt --n-classes 4 --k 4 --top 80 \
    --kwic sonda,querer
```

Roda todas as etapas e gera `output/ESTUDO/report.html` (relatório único com as
figuras embutidas). Cada etapa que falhar é registrada em `ESTUDO/logs/` e o
fluxo continua. A distância de Labbé exige `LABIIALEX_RSCRIPTS` e uma variável de
grupo no metadata; sem eles, essa etapa é pulada com aviso. Para o passo a passo
e a interpretação, ver `ROTEIRO.md`.

## Anonimização

Marcadores de anonimização devem começar com `anon` e conter só letras (ex.:
`anonmae`, `anoncrianca`, `anonhospital`). O pipeline ignora qualquer token com
esse prefixo automaticamente (parâmetro `--anon-prefix`, padrão `anon`).

## Cobertura das funcionalidades

Reinert (CHD+AFC), especificidades, similitude/coocorrência, rede tipo Gephi
(ForceAtlas2 + GEXF), KWIC, LDA, sentimento, emoções (NRC), nuvem de palavras,
bigramas/trigramas, árvore de palavras, heatmap, YAKE e exportação de corpus
para o IRaMuTeQ estão todos implementados. Entrada multiformato
(.txt/.md/.pdf/.docx/.odt/.csv/.xlsx/.zip) coberta.

As saídas ficam em `output/MEU/` (subpastas `chd/`, `afc_spec/`, `simi/`, `lda/`,
`kwic/`, `sentiment/`), em CSV e PNG, sempre com um `*_comparison.json`
registrando a concordância Python x R.

## Estado de validação (corpus sintético com 3 classes plantadas)

- CHD: Rand ajustado Python x CHD.R = 1,0 (partições idênticas).
- AFC: % de inércia idêntico ao pacote `ca` (0,0 pp de diferença).
- Especificidades: correlação Python x `textometry` = 1,0; sinal = 1,0.
- Similitude: árvore máxima com peso total idêntico ao `igraph`.
- Sentimento: negação corrigida ("não bom" → negativo).

## Correções aplicadas em relação ao código original

- Tokenização única Unicode (sem o defeito `[À-ÿ]` que incluía × e ÷).
- Classificação ativo/suplementar robusta (conjunção `conj`/`con` não vaza mais).
- AFC: % de inércia sobre a inércia total (não sobre eixos truncados).
- Qui-quadrado sem correção de Yates (convenção IRaMuTeQ), limiar 3,84.
- Similitude: célula `d = nrow` (UCEs), matriz binarizada.
- Sentimento: tratamento de negação; léxico embutido e editável (sem download
  remoto não verificado).

## Limitações conhecidas (ler antes de publicar)

- A CHD canônica do IRaMuTeQ inclui uma fase de **realocação** de UCEs; verifique
  o `comparison.json` da Parte 2 a cada corpus para ver o grau de concordância
  com o `CHD.R`.
- A **LDA é estocástica** e sensível ao tamanho do documento; rode várias
  sementes e compare. A baixa concordância Python x R é um alerta de instabilidade.
- O **sentimento** é um baseline lexical, não validado clinicamente; amplie o
  léxico ao seu domínio com `--lexicon`.

## Licença e créditos

GPL v3, por herança do labiia_lex e do IRaMuTeQ. Ver `LICENSE` e `NOTICE`. Ao usar
este software, cite-o (ver `CITATION.cff`) e cite também o labiia_lex e o IRaMuTeQ.
