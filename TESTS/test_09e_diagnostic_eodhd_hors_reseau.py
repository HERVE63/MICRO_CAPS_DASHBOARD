"""Diagnostic 09E : erreurs visibles, secrets caches, collecte 09D independante."""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
from unittest.mock import patch

import requests

SCRIPT = Path(__file__).resolve().parents[1] / "SCRIPTS_ACTIFS/09E_TEST_ACCES_EODHD.py"


def executer():
    spec = importlib.util.spec_from_file_location("diagnostic_09e_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    with patch.dict(os.environ, {}, clear=True):
        with patch.object(module.requests, "get", side_effect=AssertionError("reseau interdit")):
            sortie = io.StringIO()
            with contextlib.redirect_stdout(sortie):
                code = module.verifier()
            assert code == 2 and "API_TOKEN_ABSENT" in sortie.getvalue()

    class Reponse:
        def __init__(self, code):
            self.status_code = code

    appels = []
    def faux_get(url, params, timeout):
        assert params["api_token"] == "CLE_TEST_PRIVEE"
        assert timeout == 20
        appels.append(url)
        if url.endswith("/user"):
            return Reponse(200)
        if url.endswith("/eod/AAPL.US"):
            return Reponse(403)
        raise requests.Timeout("CLE_TEST_PRIVEE dans URL, a ne pas divulguer")

    with patch.dict(os.environ, {"EODHD_API_TOKEN": "CLE_TEST_PRIVEE"}, clear=True):
        with patch.object(module.requests, "get", side_effect=faux_get):
            sortie = io.StringIO()
            with contextlib.redirect_stdout(sortie):
                code = module.verifier()
    assert code == 1 and len(appels) == 3
    assert "HTTP 403" in sortie.getvalue()
    assert "Timeout" in sortie.getvalue()
    assert "CLE_TEST_PRIVEE" not in sortie.getvalue()

    with patch.dict(os.environ, {"EODHD_API_KEY": "CLE_TEST_PRIVEE"}, clear=True):
        with patch.object(module.requests, "get", return_value=Reponse(200)):
            sortie = io.StringIO()
            with contextlib.redirect_stdout(sortie):
                code = module.verifier()
    assert code == 0 and "DIAGNOSTIC_EODHD_ECHECS 0 SUR 3" in sortie.getvalue()
    print("09E: cle absente=2, HTTP403/timeout=1, 3 HTTP200=0, aucun secret affiche")


if __name__ == "__main__":
    executer()
