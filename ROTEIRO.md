# Roteiro de análise textual qualitativa (método Reinert/IRaMuTeQ)

Guia prático para rodar a análise no macOS, tanto para os grupos focais quanto
para outros corpora qualitativos (entrevistas, respostas abertas, documentos).
Todos os comandos partem da pasta `~/Documents/labiia_lex`. O Python do ambiente
é `.venv/bin/python` (abreviado abaixo como `PY`). Defina antes, uma vez por sessão:

```
cd ~/Documents/labiia_lex
PY=.venv/bin/python
```

## Visão geral do fluxo

1. Montar o corpus numa pasta.
2. Preparar e curar as stopwords de forma iterativa, lendo o diagnóstico.
3. Rodar a análise (um comando único, ou passo a passo).
4. Interpretar os resultados e escolher o número de classes.

## Passo 0. Anonimização (antes de tudo)

Anonimize os arquivos originais. Substitua nomes de pessoas, da criança,
profissionais, instituições, cidades e datas que identifiquem, por marcadores
que comecem com `anon` e contenham só letras (sem números, espaços, colchetes
ou parênteses): por exemplo `anonmae`, `anonpai`, `anoncrianca`, `anonmedico`,
`anonhospital`, `anoncidade`. O pipeline ignora automaticamente qualquer token
iniciado por `anon`. Guarde a chave (marcador para nome real) em arquivo
separado e seguro, fora da pasta do corpus.

## Passo 1. Montar o corpus

Crie uma pasta (por exemplo `meu_corpus/`) e coloque os documentos. Formatos
aceitos: `.txt`, `.md`, `.pdf`, `.docx`, `.odt` (um arquivo por documento) e
`.csv`/`.xlsx` (uma linha por documento). Opcional: um `metadata.csv` com a
coluna `file` e demais colunas como variáveis (por exemplo grupo, sexo, idade).

```
file,grupo
grupo1.docx,G1
```

Sem `metadata.csv`, cada arquivo recebe a variável `source` igual ao nome do
arquivo, útil para comparar documentos.

## Passo 2. Preparar e curar as stopwords

Rode a preparação:

```
$PY pipeline/run_prepare.py --corpus meu_corpus --out pipeline/output/ESTUDO \
    --stopwords pipeline/config_med/stopwords.txt
```

Leia o bloco "Diagnóstico da preparação". Use as referências: UCEs em quantidade
suficiente (idealmente acima de algumas centenas), proporção de formas ativas e
percentual de UCEs retidas. Em seguida inspecione as formas mais frequentes:

```
$PY -c "import pandas as pd; d=pd.read_csv('pipeline/output/ESTUDO/forms.csv',sep=';'); print(d.sort_values('frequencia',ascending=False).head(30).to_string(index=False))"
```

Acrescente à lista de stopwords (`pipeline/config_med/stopwords.txt`, sempre em
texto puro, edite no VS Code) o que for ruído no seu contexto: marcações de
transcrição, muletas da fala, verbos de baixo conteúdo e termos ubíquos que não
diferenciam (por exemplo, num grupo de mães, `mãe` e `filho`). Re-rode a
preparação e repita até a lista das formas frequentes ficar temática.

Parâmetros úteis do `run_prepare`:
`--uce-size` (tamanho do segmento, padrão 40), `--min-freq` (frequência mínima,
padrão 3), `--no-adverbs` (advérbios como suplementares), `--synonyms arq.csv`
(unificar variantes), `--expressions arq.txt` (preservar expressões multipalavra),
`--keep-all-speakers` (não filtrar turnos, ver adaptação adiante).

## Passo 3. Rodar a análise

### Opção A: um comando (recomendado depois de calibrar)

```
$PY pipeline/run_all.py --corpus meu_corpus --out pipeline/output/ESTUDO \
    --stopwords pipeline/config_med/stopwords.txt \
    --n-classes 4 --k 4 --top 80 --kwic sonda,querer,suplemento
```

Roda preparação, CHD, AFC e especificidades, similitude, LDA, emoções,
complementares (nuvem, n-gramas, heatmap, YAKE), KWIC dos termos indicados e
gera `pipeline/output/ESTUDO/report.html`, um relatório único com as figuras.

### Opção B: passo a passo (para interpretar com calma)

```
$PY pipeline/run_chd.py       --prepared pipeline/output/ESTUDO --n-classes 4 --stability
$PY pipeline/run_afc_spec.py  --prepared pipeline/output/ESTUDO
$PY pipeline/run_simi.py      --prepared pipeline/output/ESTUDO --top 80 --layout fa2
$PY pipeline/run_lda.py       --prepared pipeline/output/ESTUDO --k 4 --level uce --stability
$PY pipeline/run_emotions.py  --prepared pipeline/output/ESTUDO
$PY pipeline/run_kwic.py      --prepared pipeline/output/ESTUDO --query PALAVRA
$PY pipeline/run_extras.py    --prepared pipeline/output/ESTUDO --what wordcloud
$PY pipeline/run_extras.py    --prepared pipeline/output/ESTUDO --what ngrams --n 2
$PY pipeline/run_extras.py    --prepared pipeline/output/ESTUDO --what wordtree --query PALAVRA
$PY pipeline/run_extras.py    --prepared pipeline/output/ESTUDO --what heatmap
$PY pipeline/run_extras.py    --prepared pipeline/output/ESTUDO --what yake --n 3
$PY pipeline/report.py        --prepared pipeline/output/ESTUDO
```

## Passo 4. Escolher o número de classes da CHD

Rode a CHD para alguns valores e compare tamanhos das classes, concordância
Python versus R e estabilidade:

```
for k in 2 3 4 5; do $PY pipeline/run_chd.py --prepared pipeline/output/ESTUDO --n-classes $k --stability 2>&1 | grep -E "classes:|Rand|Estabilidade"; done
```

Prefira a solução com classes não minúsculas, maior concordância com o R e maior
estabilidade, e cujas palavras e segmentos típicos sejam interpretáveis.

## Passo 5. Interpretar

- CHD: `chd/characteristic_terms.csv` (palavras por classe) e
  `chd/typical_segments.csv` (trechos reais para nomear cada classe).
- AFC: `afc_spec/afc_plane.png` (oposições entre classes e palavras).
- Especificidades: `afc_spec/specificities_<variavel>.csv` (o que distingue cada
  grupo ou modalidade).
- Similitude: `simi/simi_graph.png` e `simi/simi_graph.gexf` (rede temática; o
  GEXF abre no Gephi).
- LDA: tópicos no terminal e em `lda/`.
- KWIC: `kwic/kwic_<palavra>.csv` (contextos de uso).
- Emoções: `emotions/`. Complementares: `extras/`.

## Adaptar para outros textos qualitativos

- Textos sem marcação de quem fala (respostas abertas, documentos): use
  `--keep-all-speakers` na preparação para não tentar filtrar turnos.
- Cada domínio tem o seu ruído: mantenha uma lista de stopwords por projeto
  (copie `config_med/stopwords.txt` e adapte).
- Planilhas: aponte a coluna de texto com `--text-column NOME` se a detecção
  automática não acertar.
- Para comparar grupos, condições ou tempos, registre-os como variáveis no
  `metadata.csv` e use as especificidades.

## Boas práticas e limitações

- Triangulação: confie mais nos achados que aparecem em vários métodos
  (similitude, LDA, KWIC) do que em uma única partição.
- A CHD é sensível ao pré-processamento. Para a CHD, uma lista de stopwords mais
  leve costuma dar classes mais ricas; para similitude, nuvem e LDA, uma limpeza
  mais agressiva ajuda.
- LDA, emoções e sentimento são exploratórios; emoções pelo léxico NRC são
  traduzidas automaticamente.
- Em corpora pequenos e homogêneos, espere classes da CHD menos estáveis;
  registre a estabilidade e trate como exploratório.
- A validação cruzada Python versus R fica em cada `*_comparison.json`.
- Reprodutibilidade: a configuração de cada estudo fica em `prepared.json`.
