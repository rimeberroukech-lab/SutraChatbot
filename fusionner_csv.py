"""
Fusionne tous les CSV de data/extracted/ en un seul nomenclature_maroc.csv.

- Séparateur : |||
- Colonnes attendues :
  code_sh_10 | chapitre | position_parent | designation_article |
  designation_complete | unite | droit_importation_pourcent
- Vérifie les doublons de code_sh_10 et les lignes malformées.
- En cas de problème : affiche clairement et n'écrit PAS le fichier fusionné
  (aucune correction silencieuse des données source).
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

EXTRACTED_DIR = Path("data/extracted")
OUTPUT_FILE = Path("nomenclature_maroc.csv")
SEPARATOR = "|||"
EXPECTED_COLUMNS = [
    "code_sh_10",
    "chapitre",
    "position_parent",
    "designation_article",
    "designation_complete",
    "unite",
    "droit_importation_pourcent",
]
NB_COLONNES = len(EXPECTED_COLUMNS)
CODE_SH_REGEX = re.compile(r"^\d{10}$")


def lire_lignes_csv(chemin: Path) -> list[tuple[int, str]]:
    """Retourne (numéro_ligne, contenu) pour chaque ligne non vide."""
    # utf-8-sig gère un éventuel BOM Windows
    texte = chemin.read_text(encoding="utf-8-sig")
    resultats = []
    for i, ligne in enumerate(texte.splitlines(), start=1):
        if ligne.strip():
            resultats.append((i, ligne.rstrip("\r\n")))
    return resultats


def main() -> int:
    if not EXTRACTED_DIR.is_dir():
        print(f"ERREUR : dossier introuvable : {EXTRACTED_DIR.resolve()}")
        return 1

    fichiers = sorted(EXTRACTED_DIR.glob("*.csv"))
    if not fichiers:
        print(f"ERREUR : aucun fichier .csv dans {EXTRACTED_DIR.resolve()}")
        return 1

    print(f"Fichiers trouvés : {len(fichiers)}")
    for f in fichiers:
        print(f"  - {f.name}")

    # code_sh_10 -> liste de (fichier, ligne, contenu_ligne)
    par_code: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
    malformees: list[str] = []
    lignes_valides: list[str] = []
    total_lues = 0

    for fichier in fichiers:
        for num_ligne, contenu in lire_lignes_csv(fichier):
            total_lues += 1
            # Ignorer une éventuelle ligne d'en-tête
            if contenu.startswith("code_sh_10"):
                continue

            parties = contenu.split(SEPARATOR)
            if len(parties) != NB_COLONNES:
                malformees.append(
                    f"  [{fichier.name}:{num_ligne}] "
                    f"{len(parties)} colonnes (attendu {NB_COLONNES}) : {contenu[:120]}..."
                )
                continue

            code = parties[0].strip()
            if not CODE_SH_REGEX.match(code):
                malformees.append(
                    f"  [{fichier.name}:{num_ligne}] "
                    f"code_sh_10 invalide '{code}' : {contenu[:120]}..."
                )
                continue

            # Normaliser le code (sans espaces) dans la ligne stockée
            parties[0] = code
            ligne_norm = SEPARATOR.join(parties)
            par_code[code].append((fichier.name, num_ligne, ligne_norm))

    doublons: list[str] = []
    for code, occurrences in sorted(par_code.items()):
        if len(occurrences) > 1:
            doublons.append(f"  code_sh_10={code} ({len(occurrences)} occurrences) :")
            for fichier, num_ligne, _ in occurrences:
                doublons.append(f"    - {fichier}:{num_ligne}")
        else:
            lignes_valides.append(occurrences[0][2])

    print("\n" + "=" * 60)
    print(f"Lignes lues (hors en-têtes vides) : {total_lues}")
    print(f"Codes uniques valides             : {len(lignes_valides)}")
    print(f"Codes en doublon                  : {len(doublons) and len([c for c, o in par_code.items() if len(o) > 1])}")
    print(f"Lignes malformées                 : {len(malformees)}")
    print("=" * 60)

    if malformees:
        print("\n[!] LIGNES MALFORMEES (a verifier manuellement dans le PDF source) :")
        for msg in malformees:
            print(msg)

    if doublons:
        nb_codes_doublons = sum(1 for o in par_code.values() if len(o) > 1)
        print(f"\n[!] DOUBLONS DE code_sh_10 ({nb_codes_doublons} codes) :")
        for msg in doublons:
            print(msg)

    if malformees or doublons:
        print(
            "\n[X] Fusion annulee : corrigez les problemes ci-dessus dans "
            "data/extracted/ puis relancez. Aucune donnee n'a ete modifiee."
        )
        return 1

    en_tete = SEPARATOR.join(EXPECTED_COLUMNS)
    OUTPUT_FILE.write_text(
        en_tete + "\n" + "\n".join(lignes_valides) + "\n",
        encoding="utf-8",
    )
    print(f"\n[OK] Fichier ecrit : {OUTPUT_FILE.resolve()}")
    print(f"     {len(lignes_valides)} articles fusionnes sans doublon ni erreur.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
