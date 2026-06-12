"""In-memory mapping store for PIN-based masking (single DID).

One masking number serves everyone. The caller enters a PIN and the backend
resolves the destination from the PIN. Optionally an allow-list restricts which
source numbers may use a given PIN (defence-in-depth).

All values are loaded from the environment (a local ``.env`` is read via
python-dotenv); nothing is hardcoded. PINs should be unique and time-bound per
client policy in production; rotate them regularly.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

# The single Vobiz DID that all callers dial (E.164, no '+').
MASKING_DID = os.environ.get("MASKING_DID", "919000000001")

# PIN -> real destination, parsed from .env. Replace the defaults.
# Format: "pin1:dest1,pin2:dest2,..."
_RAW = os.environ.get(
    "PIN_MAP",
    "1234:919876511111,5678:919876522222,9012:919876533333",
)

PIN_TO_DESTINATION: dict[str, str] = {}
for _pair in _RAW.split(","):
    if ":" in _pair:
        _p, _d = _pair.split(":", 1)
        PIN_TO_DESTINATION[_p.strip()] = _d.strip()

# Optional: restrict which source numbers may use a PIN. Empty => any source.
# Format in .env: "pin1=num1|num2,pin2=num3"   (PINs omitted here => unrestricted)
PIN_ALLOWLIST: dict[str, set[str]] = {}
for _entry in os.environ.get("PIN_ALLOWLIST", "").split(","):
    if "=" in _entry:
        _p, _nums = _entry.split("=", 1)
        PIN_ALLOWLIST[_p.strip()] = {n.strip() for n in _nums.split("|") if n.strip()}


def resolve(pin: str, from_number: str) -> str | None:
    """Return the destination for a valid PIN (honouring any allow-list)."""
    destination = PIN_TO_DESTINATION.get(pin)
    if destination is None:
        return None
    allowed = PIN_ALLOWLIST.get(pin)
    if allowed and from_number not in allowed:
        return None
    return destination
