"""Protection de la branche isolée : aucune exécution manuelle ne pousse main."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FICHIERS = (
    "chasse_hebdomadaire.yml",
    "fondamentaux_incrementaux_microcaps.yml",
    "arbitrage_mensuel.yml",
    "controle_pre_ssi_microcaps.yml",
    "preparation_filtres_microcaps.yml",
    "preparer_dossiers_ssi.yml",
)


def executer():
    for nom in FICHIERS:
        p = ROOT / ".github/workflows" / nom
        s = p.read_text(encoding="utf-8")
        assert "ref: main" not in s, nom
        assert "git push origin main" not in s, nom
        assert "git pull --rebase origin main" not in s, nom
        assert "ref: ${{ github.ref_name }}" in s, nom
        assert 'git push origin "HEAD:$GITHUB_REF_NAME"' in s, nom
        assert 'git pull --rebase origin "$GITHUB_REF_NAME"' in s, nom
    # La préparation SSI doit se relancer sur les changements de ses véritables
    # entrées, notamment les captures 07AA. Le push GITHUB_TOKEN d'un autre
    # workflow ne déclenche toutefois PAS de nouvel événement push GitHub :
    # ce contrôle couvre les commits ordinaires et les lancements manuels.
    p = ROOT / ".github/workflows/preparer_dossiers_ssi.yml"
    s = p.read_text(encoding="utf-8")
    for entree in (
        "SCRIPTS_ACTIFS/07Q_PREPARER_DOSSIERS_SSI.py",
        "SCRIPTS_ACTIFS/07Q2_AUDIT_PREUVES_SSI.py",
        "SCRIPTS_ACTIFS/preuves_ssi.py",
        "SCRIPTS_ACTIFS/07R_VALIDER_NOTES_SSI.py",
        "DONNEES/CANDIDATS_PRETS_SSI.csv",
        "DONNEES/IDENTITE_COTATIONS_MULTIPLES.csv",
        "AUDITS/SOURCES_OFFICIELLES/**",
    ):
        assert "      - '" + entree + "'" in s, "Entrée SSI non surveillée : " + entree
    assert ("  ssi:\n    if: github.ref_name == "
            "'repair/microcaps-chain-20261030'") in s, (
        "workflow_dispatch ne doit jamais exécuter le job SSI sur main"
    )
    # GitHub ne relance pas un workflow push apres un push GITHUB_TOKEN.
    # Les collecteurs 07AA doivent dispatcher 07Q uniquement si leur
    # commit de preuves a effectivement ete publie sur la branche isolee.
    groupes = {
        "collecte_icape_primaires_isolee.yml": "microcaps-icape-primaires-isolees",
        "collecte_fermentalg_primaires_isolee.yml": "microcaps-fermentalg-reprise-isolee",
        "collecte_identite_fermentalg_marche_isolee.yml": "microcaps-identite-fermentalg-marche-isolee",
    }
    for nom in groupes:
        s = (ROOT / ".github/workflows" / nom).read_text(encoding="utf-8")
        assert "permissions:\n  contents: write\n  actions: write\n" in s, nom
        assert ("jobs:\n  capture:\n    if: github.ref_name == "
                "'repair/microcaps-chain-20261030'") in s, nom
        assert "  group: " + groupes[nom] in s, nom
        assert "  cancel-in-progress: false" in s, nom
        assert "for essai in 1 2 3 4 5; do" in s, nom
        assert 'git pull --rebase origin "$GITHUB_REF_NAME"' in s, nom
        assert "ECHEC_PUBLICATION_APRES_5_TENTATIVES" in s, nom
        assert "        id: publication\n" in s, nom
        assert 'echo "published=true" >> "$GITHUB_OUTPUT"' in s, nom
        assert "steps.publication.outputs.published == 'true'" in s, nom
        assert "github.ref_name == 'repair/microcaps-chain-20261030'" in s, nom
        assert 'gh workflow run preparer_dossiers_ssi.yml --ref "$GITHUB_REF_NAME"' in s, nom
        assert s.index('git push origin "HEAD:$GITHUB_REF_NAME"') < s.index(
            'echo "published=true" >> "$GITHUB_OUTPUT"') < s.index(
            "gh workflow run preparer_dossiers_ssi.yml"), nom
        assert "git push origin main" not in s and "ref: main" not in s, nom
    # Une modification du workflow de capture ne doit pas relancer une
    # collecte de document primaire deja archive (eviter les doublons).
    transfert = (ROOT / ".github/workflows/collecte_transfert_fermentalg_2024_isolee.yml").read_text(encoding="utf-8")
    bloc_push = transfert.split("  push:\n", 1)[1].split("permissions:\n", 1)[0]
    assert "branches: [repair/microcaps-chain-20261030]" in bloc_push
    assert "      - 'AUDITS/REPARATION/REGISTRE_FERMENTALG_TRANSFERT_2024.csv'" in bloc_push
    assert "collecte_transfert_fermentalg_2024_isolee.yml" not in bloc_push, (
        "Une edition du workflow recapturerait le meme document historique"
    )
    assert "  workflow_dispatch:\n" in transfert
    assert "  contents: write" in transfert and "  actions: write" in transfert
    assert "github.ref_name == 'repair/microcaps-chain-20261030'" in transfert
    assert "git push origin main" not in transfert
    assert "  workflow_dispatch:\n" in (
        ROOT / ".github/workflows/preparer_dossiers_ssi.yml"
    ).read_text(encoding="utf-8")
    # La collecte 40 reste manuelle et bénéficie d'un déclenchement push
    # strictement borné à son propre workflow sur la branche isolée : ce
    # changement permet un essai réel sans dispatch externe. Aucun push Git,
    # aucune écriture main, aucun score si la clé ou les données manquent.
    collecte = (ROOT / ".github/workflows/collecte-40-titulaires.yml").read_text(encoding="utf-8")
    assert ("  push:\n    branches: [repair/microcaps-chain-20261030]\n"
            "    paths:\n      - '.github/workflows/collecte-40-titulaires.yml'\n"
            "      - 'SCRIPTS_ACTIFS/09D_COLLECTE_40_TITULAIRES.py'\n") in collecte
    assert "  schedule:" not in collecte
    assert "  collecter:\n    if: github.ref_name == 'repair/microcaps-chain-20261030'" in collecte
    assert "          ref: ${{ github.ref_name }}" in collecte
    assert "permissions:\n  contents: read" in collecte
    assert "continue-on-error: true" in collecte
    assert "python -B SCRIPTS_ACTIFS/09E_TEST_ACCES_EODHD.py" in collecte
    assert "python -B SCRIPTS_ACTIFS/09D_COLLECTE_40_TITULAIRES.py" in collecte
    assert collecte.index("09E_TEST_ACCES_EODHD.py") < collecte.index("09D_COLLECTE_40_TITULAIRES.py")
    assert "DONNEES/COLLECTE_DIRECTE_40_TITULAIRES.csv" in collecte
    assert "Score_SSI" in collecte and "Score_MCPA" in collecte
    assert "git push" not in collecte and "ref: main" not in collecte
    print("Sécurité des branches : workflows isolés et push sur la branche déclencheuse")


if __name__ == "__main__":
    executer()
