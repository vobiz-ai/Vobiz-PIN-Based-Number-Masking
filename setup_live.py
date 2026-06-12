"""One-time live setup: create a Vobiz Application and attach it to your single DID.

Run this YOURSELF (it changes your live account):

    ./.venv/bin/python setup_live.py

Reads VOBIZ_AUTH_ID, VOBIZ_AUTH_TOKEN, PUBLIC_BASE_URL and MASKING_DID from .env,
creates one application whose answer_url points at PUBLIC_BASE_URL/answer, and
attaches it to the single masking DID.

Docs: https://docs.vobiz.ai/applications  |  .../applications/attach-number
"""
from __future__ import annotations

import os
import sys
import urllib.parse

import requests
from dotenv import load_dotenv

load_dotenv()

AUTH_ID = os.environ["VOBIZ_AUTH_ID"]
TOKEN = os.environ["VOBIZ_AUTH_TOKEN"]
API_BASE = os.environ.get("VOBIZ_API_BASE", "https://api.vobiz.ai/api/v1")
PUBLIC = os.environ["PUBLIC_BASE_URL"].rstrip("/")
NUMBERS = [n for n in [os.environ.get("MASKING_DID")] if n]
APP_NAME = os.environ.get("APP_NAME", "vobiz_pin_number_masking")

H = {"X-Auth-ID": AUTH_ID, "X-Auth-Token": TOKEN, "Content-Type": "application/json"}
BASE = f"{API_BASE}/Account/{AUTH_ID}"


def main() -> int:
    answer_url = f"{PUBLIC}/answer"
    print(f"[*] Creating application '{APP_NAME}' -> answer_url={answer_url}")
    body = {
        "app_name": APP_NAME,
        "answer_url": answer_url,
        "answer_method": "POST",
        "hangup_url": answer_url,
        "hangup_method": "POST",
    }
    r = requests.post(f"{BASE}/Application/", headers=H, json=body, timeout=20)
    print(f"    CREATE -> {r.status_code} {r.text}")
    if r.status_code not in (200, 201):
        return 1
    app_id = (r.json() or {}).get("app_id")
    if not app_id:
        print("[x] No app_id in response.")
        return 1
    print(f"[*] app_id = {app_id}")

    for num in NUMBERS:
        enc = urllib.parse.quote("+" + num)
        ar = requests.post(
            f"{BASE}/numbers/{enc}/application", headers=H,
            json={"application_id": app_id}, timeout=20,
        )
        print(f"    ATTACH {num} -> {ar.status_code} {ar.text[:400]}")

    print("\n[✓] Done. Dial the masking DID, enter a PIN, and you'll be bridged "
          "to that PIN's destination.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
