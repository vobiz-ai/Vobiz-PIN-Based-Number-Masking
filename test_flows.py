from fastapi.testclient import TestClient

import mappings
from app import app

client = TestClient(app)

DID = "918076665555"


def test_answer_prompts_for_pin():
    r = client.post("/answer", data={"From": "910000000000", "To": DID})
    assert "<Gather" in r.text
    assert "/collect-pin" in r.text
    assert 'numDigits="4"' in r.text


def test_valid_pin_bridges_to_destination():
    pin, dest = next(iter(mappings.PIN_TO_DESTINATION.items()))
    r = client.post("/collect-pin", data={"From": "910000000000", "To": DID, "Digits": pin})
    assert f"<Number>{dest}</Number>" in r.text
    assert f'callerId="{DID}"' in r.text


def test_invalid_pin_rejected():
    r = client.post("/collect-pin", data={"From": "910000000000", "To": DID, "Digits": "0000"})
    assert "<Hangup" in r.text
    assert "<Dial" not in r.text


def test_allowlist_blocks_wrong_source():
    pin = "1234"
    mappings.PIN_ALLOWLIST[pin] = {"919999900001"}
    try:
        r = client.post("/collect-pin", data={"From": "910000000000", "To": DID, "Digits": pin})
        assert "<Hangup" in r.text
        ok = client.post("/collect-pin", data={"From": "919999900001", "To": DID, "Digits": pin})
        assert "<Dial" in ok.text
    finally:
        mappings.PIN_ALLOWLIST.pop(pin, None)
