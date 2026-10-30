"""Protection de la branche isolée : aucune exécution manuelle ne pousse main."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FICHIERS = (
    "chasse_hebdomadaire.yml",
    "fondamentaux_incrementaux_microcaps.yml",
    "arbitrage_mensuel.yml",
    "controle_pre_ssi_microcaps.yml",
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
    print("Sécurité des branches : workflows isolés et push sur la branche déclencheuse")


if __name__ == "__main__":
    executer()
