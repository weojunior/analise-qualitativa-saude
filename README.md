# Pipeline labiia_lex (método Reinert/IRaMuTeQ) no macOS

Reimplementação limpa e auditável do método de análise textual do software
labiia_lex (Prof. Rafael Cardoso Sampaio, UFPR), derivado do IRaMuTeQ
(Pierre Ratinaud, GPL). Roda no macOS com R + Python, cruzando cada análise
entre um motor Python próprio e o código/pacote R canônico.

## Pré-requisitos (já instalados nesta máquina)

- R 4.4.3 com pacotes CRAN: ca, ade4, cluster, proxy, Matrix, MASS, irlba,
  igraph, slam, stringi, textometry, topicmodels (e dependências).
- Ambiente Python isolado em `../.venv` (Python 3.12) com numpy, scipy, pandas,
  scikit-learn, python-igraph, networkx, matplotlib, python-docx.
- Dicionários do IRaMuTeQ em `../extracted/internal/dictionaries/`.

Sempre use o Python do ambiente: `../.venv/bin/python` (a partir de `pipeline/`),
ou `~/Documents/labiia_lex/.venv/bin/python` (caminho absoluto).

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

A preparação também exporta o corpus limpo em `corpus_iramuteq.txt`, no formato
de texto do IRaMuTeQ (linhas `**** *variavel_modalidade`).

## Fluxo (5 etapas)

A partir de `~/Documents/labiia_lex/`:

```bash
PY=.venv/bin/python

# Parte 1 — preparação (tokenização IRaMuTeQ, UCI/UCE, matriz UCE x formas)
$PY pipeline/run_prepare.py --corpus CAMINHO/DO/CORPUS --out pipeline/output/MEU --uce-size 40 --min-freq 3

# Parte 2 — CHD de Reinert (classes lexicais), cruzamento Python x CHD.R canônico
$PY pipeline/run_chd.py --prepared pipeline/output/MEU --n-classes 4

# Parte 3 — AFC + especificidades (Python x ca / textometry)
$PY pipeline/run_afc_spec.py --prepared pipeline/output/MEU --variables grupo,papel

# Parte 4 — similitude (rede de coocorrência), cruzamento Python x igraph
$PY pipeline/run_simi.py --prepared pipeline/output/MEU --index cooccurrence --top 80

# Parte 5 — LDA, concordâncias e sentimento
$PY pipeline/run_lda.py --prepared pipeline/output/MEU --k 4 --level uce
$PY pipeline/run_kwic.py --prepared pipeline/output/MEU --query alimentação
$PY pipeline/run_sentiment.py --prepared pipeline/output/MEU --level uci

# Parte 8 — emoções NRC (8 categorias, via syuzhet)
$PY pipeline/run_emotions.py --prepared pipeline/output/MEU --variables grupo

# Parte 4 com layout Gephi + GEXF (abre no Gephi)
$PY pipeline/run_simi.py --prepared pipeline/output/MEU --layout fa2   # gera simi_graph.gexf

# Parte 9 — complementares
$PY pipeline/run_extras.py --prepared pipeline/output/MEU --what wordcloud
$PY pipeline/run_extras.py --prepared pipeline/output/MEU --what ngrams --n 2   # e --n 3
$PY pipeline/run_extras.py --prepared pipeline/output/MEU --what wordtree --query criança --direction right
$PY pipeline/run_extras.py --prepared pipeline/output/MEU --what heatmap
$PY pipeline/run_extras.py --prepared pipeline/output/MEU --what yake --n 3
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
.venv/bin/python pipeline/run_all.py --corpus PASTA --out pipeline/output/ESTUDO \
    --stopwords pipeline/config_med/stopwords.txt --n-classes 4 --k 4 --top 80 \
    --kwic sonda,querer
```

Roda todas as etapas e gera `pipeline/output/ESTUDO/report.html` (relatório único
com as figuras embutidas). Cada etapa que falhar é registrada em `ESTUDO/logs/` e
o fluxo continua. Para o passo a passo e a interpretação, ver `ROTEIRO.md`.

## Anonimização

Marcadores de anonimização devem começar com `anon` e conter só letras (ex.:
`anonmae`, `anoncrianca`, `anonhospital`). O pipeline ignora qualquer token com
esse prefixo automaticamente (parâmetro `--anon-prefix`, padrão `anon`).

## Cobertura das funcionalidades anunciadas no site

Reinert (CHD+AFC), especificidades, similitude/coocorrência, rede tipo Gephi
(ForceAtlas2 + GEXF), KWIC, LDA, sentimento, emoções (NRC), nuvem de palavras,
bigramas/trigramas, árvore de palavras, heatmap, YAKE e exportação de corpus
para o IRaMuTeQ estão todos implementados no Mac. Entrada multiformato
(.txt/.md/.pdf/.docx/.odt/.csv/.xlsx/.zip) coberta.

As saídas ficam em `pipeline/output/MEU/` (subpastas `chd/`, `afc_spec/`,
`simi/`, `lda/`, `kwic/`, `sentiment/`), em CSV e PNG, sempre com um
`*_comparison.json` registrando a concordância Python x R.

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

- A CHD canônica do IRaMuTeQ inclui uma fase de **realocação** de UCEs que o
  motor Python ainda não replica; verifique o `comparison.json` da Parte 2 a
  cada corpus para ver o grau de concordância com o `CHD.R`.
- A **LDA é estocástica** e sensível ao tamanho do documento; rode várias
  sementes e compare. A baixa concordância Python x R é um alerta de instabilidade.
- O **sentimento** é um baseline lexical, não validado clinicamente; amplie o
  léxico ao seu domínio com `--lexicon`.
