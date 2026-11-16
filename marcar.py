#!/usr/bin/env python3
"""Marca una noticia como usada: python3 marcar.py "<texto del titulo o enlace>" """
import sys
q = sys.argv[1].strip()
lines = open("pendientes.md").read().splitlines()
hits = [l for l in lines if l.startswith("- ") and q in l]
if len(hits) != 1:
    sys.exit(f"{len(hits)} coincidencias; afina el texto")
link = hits[0].rsplit(" | ", 1)[-1].strip()
open("usadas.txt", "a").write(link + "\n")
open("pendientes.md", "w").write("\n".join(l for l in lines if l != hits[0]) + "\n")
print("marcada:", hits[0][:120])
