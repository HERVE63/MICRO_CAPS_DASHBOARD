# -*- coding: utf-8 -*-

"""
MICRO CAPS — Génération automatique du tableau de bord
Le moteur de calcul reste indépendant.
Ce script met à jour l'affichage GitHub Pages à partir des données validées.
"""

from pathlib import Path
import shutil

BASE = Path(__file__).resolve().parents[1]

APPLICATION = BASE / "APPLICATION"
INDEX_APPLICATION = APPLICATION / "index.html"
INDEX_PUBLIC = BASE / "index.html"

print("=== MICRO CAPS : MISE A JOUR DU TABLEAU DE BORD ===")

if not INDEX_APPLICATION.exists():
    raise FileNotFoundError(
        f"Tableau de bord source introuvable : {INDEX_APPLICATION}"
    )

# Publication du tableau de bord validé vers la racine GitHub Pages.
shutil.copy2(INDEX_APPLICATION, INDEX_PUBLIC)

print(f"Source : {INDEX_APPLICATION}")
print(f"Publication : {INDEX_PUBLIC}")
print("✅ TABLEAU DE BORD MICRO CAPS PUBLIE")
