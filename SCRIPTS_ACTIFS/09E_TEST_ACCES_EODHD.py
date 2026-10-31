import os
import requests

token = os.environ.get("EODHD_API_TOKEN")
if not token:
    raise SystemExit("API_TOKEN_ABSENT")
tests = [
    ("compte", "user"),
    ("cours_AAPL", "eod/AAPL.US"),
    ("fondamentaux_AAPL", "fundamentals/AAPL.US"),
]
for name, endpoint in tests:
    try:
        response = requests.get(
            "https://eodhd.com/api/" + endpoint,
            params={"api_token": token, "fmt": "json"},
            timeout=20,
        )
        print("DIAGNOSTIC", name, "HTTP", response.status_code)
    except requests.RequestException as exc:
        print("DIAGNOSTIC", name, "ERREUR", type(exc).__name__)
