"""Strategy 4 — PIN-based masking (single DID).

A single masking number is used for all calls. On answer we play a <Gather> to
collect a PIN; the PIN is POSTed to /collect-pin, where we resolve the
destination and return a <Dial>. Most cost-effective (one DID), supports
registered and non-registered callers as long as the PIN is correct.

Run:  uvicorn app:app --reload --port 8004
"""
from __future__ import annotations

import os

from fastapi import FastAPI, Form, Response

import mappings
from vobiz_xml import dial, gather, hangup, response, speak

app = FastAPI(title="Vobiz masking — PIN based")

XML = "application/xml"
PIN_LENGTH = 4
# Public base URL so the Gather action points back at THIS server when Vobiz
# fetches it. Defaults to a relative path, which Vobiz resolves against answer_url.
COLLECT_ACTION = f"{os.environ.get('PUBLIC_BASE_URL', '')}/collect-pin"


@app.post("/answer")
async def answer(
    From: str = Form(...),
    To: str = Form(...),
    CallUUID: str = Form(default=""),
    Direction: str = Form(default=""),
    CallStatus: str = Form(default=""),
) -> Response:
    """Greet the caller and collect their PIN."""
    xml = response(
        gather(
            action=COLLECT_ACTION,
            method="POST",
            input_type="dtmf",
            num_digits=PIN_LENGTH,
            finish_on_key="#",
            execution_timeout=15,
            prompt="Please enter your access PIN followed by the hash key.",
        ),
        # Fallback if the caller enters nothing.
        speak("We did not receive any input. Goodbye."),
        hangup(reason="no_input"),
    )
    return Response(content=xml, media_type=XML)


@app.post("/collect-pin")
async def collect_pin(
    From: str = Form(...),
    To: str = Form(...),
    Digits: str = Form(default=""),
    CallUUID: str = Form(default=""),
) -> Response:
    """Resolve the destination from the entered PIN and bridge the call."""
    destination = mappings.resolve(pin=Digits, from_number=From)
    if destination is None:
        xml = response(
            speak("That PIN is not valid. Goodbye."),
            hangup(reason="invalid_pin"),
        )
        return Response(content=xml, media_type=XML)

    xml = response(dial(destination, caller_id=To, timeout=30))
    return Response(content=xml, media_type=XML)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "strategy": "pin-based"}
