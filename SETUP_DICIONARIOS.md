# Dicionários do IRaMuTeQ (dependência externa)

Este pipeline usa os dicionários de idioma do IRaMuTeQ (`lexique_<lang>.txt`,
`key.cfg`, `expression_<lang>.txt`) para tokenizar e classificar as formas. Esses
dicionários não são redistribuídos aqui: são parte do IRaMuTeQ (GPL) e somam
dezenas de megabytes. Cada usuário aponta o pipeline para a sua própria cópia.

## Como obter

Os dicionários vêm com qualquer instalação do IRaMuTeQ ou do software labiia_lex,
na pasta `dictionaries` (subpasta `internal`). Instale o IRaMuTeQ ou extraia o
labiia_lex e localize essa pasta.

## Como apontar o pipeline

Defina a variável de ambiente antes de rodar, uma vez por sessão de terminal:

```
export LABIIALEX_DICT=/caminho/para/dictionaries
```

Alternativa por comando, sem variável de ambiente:

```
python run_prepare.py --corpus corpus_synth --out output/teste --dictionaries /caminho/para/dictionaries
```

Se nem a variável nem a flag forem definidas, o pipeline procura em
`../extracted/internal/dictionaries` relativo ao script, e falha com
`LexiqueError` se não encontrar.

## Recurso adicional só para a distância de Labbé

A etapa de Labbé (`run_labbe.py`) reaproveita o `distance-labbe.R` do IRaMuTeQ,
que fica na pasta `Rscripts` da mesma extração. Aponte por variável de ambiente
ou por flag:

```
export LABIIALEX_RSCRIPTS=/caminho/para/Rscripts
```

Sem esse recurso, as outras doze etapas funcionam normalmente; só a distância de
Labbé é pulada com aviso. Se o corpus não tiver uma variável de grupo no
metadata, a etapa também é pulada com aviso, sem quebrar o fluxo.

## Verificação

Um teste de fumaça com o corpus sintético que acompanha o repositório:

```
export LABIIALEX_DICT=/caminho/para/dictionaries
python run_all.py --corpus corpus_synth --out output/teste --n-classes 3
```

Se `output/teste/report.html` for gerado, os dicionários estão corretos.
