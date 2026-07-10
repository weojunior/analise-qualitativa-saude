#!/usr/bin/env python3
"""Distância intertextual de Labbé entre os grupos (textos).

Agrega o corpus em uma tabela forma × grupo e calcula a distância de Labbé
canônica (via ``distance-labbe.R`` do IRaMuTeQ). Gera a matriz de distâncias, um
heatmap e um agrupamento hierárquico dos grupos por proximidade lexical, o que
complementa a análise de saturação (quais grupos se parecem entre si).

Uso:
    python run_labbe.py --prepared OUT_DIR [--by grupo] [--rscripts DIR]
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

#: Rscripts do IRaMuTeQ (distance-labbe.R). Não redistribuídos; defina o caminho
#: por LABIIALEX_RSCRIPTS ou --rscripts. O fallback só serve com a extração local.
_FALLBACK_RSCRIPTS = (
    Path(__file__).resolve().parents[1] / "extracted" / "internal" / "Rscripts"
)
DEFAULT_RSCRIPTS = Path(os.environ.get("LABIIALEX_RSCRIPTS", str(_FALLBACK_RSCRIPTS)))
R_DRIVER = Path(__file__).resolve().parent / "r" / "labbe_reference.R"

#: Colunas do uce_meta que não são variáveis de grupo (ids e contagens n_*).
COLUNAS_NAO_VARIAVEIS = {"uce_id", "uci_id"}


def aggregate_form_by_group(prepared: Path, by: str) -> pd.DataFrame:
    """Soma a DTM (UCE×forma) por grupo -> tabela forma × grupo (contagens)."""
    dtm = pd.read_csv(prepared / "dtm.csv", sep=";", dtype=str, encoding="utf-8")
    uce_ids = dtm.iloc[:, 0].astype(str)
    forms = list(dtm.columns[1:])
    values = dtm.iloc[:, 1:].to_numpy(dtype=np.int64)

    meta = pd.read_csv(prepared / "uce_meta.csv", sep=";", dtype=str, encoding="utf-8")
    gmap = dict(zip(meta["uce_id"].astype(str), meta[by].astype(str)))
    groups = uce_ids.map(gmap)
    valid = groups.notna() & ~groups.isin(["", "nan", "None"])
    values, groups = values[valid.to_numpy()], groups[valid]

    table = pd.DataFrame(values, columns=forms)
    table[by] = groups.to_numpy()
    grouped = table.groupby(by).sum().T            # forma × grupo
    grouped = grouped.loc[grouped.sum(axis=1) > 0]  # descarta formas zeradas
    grouped.columns = [str(c) for c in grouped.columns]
    return grouped


def _variaveis_disponiveis(prepared: Path) -> list[str]:
    """Lista as variáveis de grupo do metadata (exclui ids e colunas de contagem)."""
    meta = pd.read_csv(prepared / "uce_meta.csv", sep=";", dtype=str,
                       encoding="utf-8", nrows=0)
    return [c for c in meta.columns
            if c not in COLUNAS_NAO_VARIAVEIS and not c.startswith("n_")]


def main() -> int:
    parser = argparse.ArgumentParser(description="Distância de Labbé entre grupos")
    parser.add_argument("--prepared", required=True)
    parser.add_argument("--by", default=None,
                        help="variável de grupo do metadata; se omitida, usa "
                             "'grupo' ou a primeira disponível")
    parser.add_argument("--rscripts", default=str(DEFAULT_RSCRIPTS))
    args = parser.parse_args()

    prepared = Path(args.prepared)
    out_dir = prepared / "labbe"
    out_dir.mkdir(parents=True, exist_ok=True)

    disponiveis = _variaveis_disponiveis(prepared)
    if args.by:
        by = args.by if args.by in disponiveis else None
    else:
        by = "grupo" if "grupo" in disponiveis else (disponiveis[0] if disponiveis else None)
    if by is None:
        alvo = f"'{args.by}'" if args.by else "de grupo"
        disp = ", ".join(disponiveis) or "nenhuma"
        print(f"[pulado] distância de Labbé: variável {alvo} não encontrada no "
              f"metadata (disponíveis: {disp}). Informe --by NOME.")
        return 0
    if not args.by and by != "grupo":
        print(f"Variável de grupo detectada automaticamente: '{by}'")

    table = aggregate_form_by_group(prepared, by)
    table_path = out_dir / "_labbe_table.csv"
    table.to_csv(table_path, sep=";", encoding="utf-8")
    print(f"Tabela forma × {by}: {table.shape[0]} formas × {table.shape[1]} grupos")

    out_csv = out_dir / "labbe_distance.csv"
    proc = subprocess.run(
        ["Rscript", str(R_DRIVER), str(args.rscripts), str(table_path), str(out_csv)],
        capture_output=True, text=True, encoding="utf-8",
    )
    print(proc.stdout.strip() or proc.stderr.strip()[:400])
    if not out_csv.exists():
        print("Falha ao calcular a distância de Labbé."); return 3

    # write.csv2 (R) grava decimais com vírgula -> ler com decimal=","
    dist = pd.read_csv(out_csv, sep=";", index_col=0, decimal=",", encoding="utf-8")
    dist = dist.apply(pd.to_numeric, errors="coerce").fillna(0.0)
    m = dist.to_numpy(dtype=float)
    m = m + m.T                      # simetriza (R preencheu só o triângulo inferior)
    np.fill_diagonal(m, 0.0)
    labels = [str(c) for c in dist.columns]
    sym = pd.DataFrame(m, index=labels, columns=labels)
    sym.to_csv(out_csv, sep=";", encoding="utf-8")

    # pares mais próximos / mais distantes
    iu = np.triu_indices(len(labels), k=1)
    pairs = sorted(((m[i, j], labels[i], labels[j]) for i, j in zip(*iu)))
    print("\nGrupos mais próximos (menor distância de Labbé):")
    for d, a, b in pairs[:3]:
        print(f"  {a} ~ {b}: {d:.4f}")
    print("Grupos mais distantes:")
    for d, a, b in pairs[-3:]:
        print(f"  {a} ~ {b}: {d:.4f}")

    # heatmap
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(m, cmap="viridis")
    ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels)
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, f"{m[i, j]:.2f}", ha="center", va="center",
                    color="white" if m[i, j] < m.max() * 0.6 else "black", fontsize=8)
    ax.set_title("Distância intertextual de Labbé entre grupos")
    fig.colorbar(im, ax=ax, shrink=0.8, label="distância")
    fig.tight_layout(); fig.savefig(out_dir / "labbe_heatmap.png", dpi=300); plt.close(fig)

    # agrupamento hierárquico dos grupos por proximidade lexical
    if len(labels) >= 3:
        link = linkage(squareform(m, checks=False), method="average")
        fig, ax = plt.subplots(figsize=(8, 4))
        dendrogram(link, labels=labels, ax=ax)
        ax.set_title("Agrupamento dos grupos (distância de Labbé, ligação média)")
        ax.set_ylabel("distância")
        fig.tight_layout(); fig.savefig(out_dir / "labbe_clusters.png", dpi=300); plt.close(fig)

    print(f"\nResultados em {out_dir}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
