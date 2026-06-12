"""Vobiz XML response builders.

Vobiz drives a call by POSTing call details to your ``answer_url`` and expecting
a small XML document back (root ``<Response>``). These helpers return XML
*strings* so each FastAPI handler can wrap them in a
``Response(content=..., media_type="application/xml")``.

Reference: https://docs.vobiz.ai/xml/overview/how-it-works
  - <Dial>   https://docs.vobiz.ai/xml/dial
  - <Gather> https://docs.vobiz.ai/xml/gather
  - <Speak>  https://docs.vobiz.ai/xml/speak
  - <Hangup> https://docs.vobiz.ai/xml/hangup
"""
from __future__ import annotations

from xml.sax.saxutils import escape, quoteattr

XML_DECL = '<?xml version="1.0" encoding="UTF-8"?>'


def _attrs(pairs: dict) -> str:
    """Render attributes, skipping ``None`` values. Uses quoteattr for safety."""
    out = []
    for key, value in pairs.items():
        if value is None:
            continue
        if isinstance(value, bool):
            value = "true" if value else "false"
        out.append(f"{key}={quoteattr(str(value))}")
    return (" " + " ".join(out)) if out else ""


def response(*children: str) -> str:
    """Wrap one or more XML fragments in the <Response> root element."""
    body = "".join(children)
    return f"{XML_DECL}<Response>{body}</Response>"


def speak(text: str, voice: str | None = None, language: str | None = None,
          loop: int | None = None) -> str:
    attrs = _attrs({"voice": voice, "language": language, "loop": loop})
    return f"<Speak{attrs}>{escape(text)}</Speak>"


def hangup(reason: str | None = None) -> str:
    return f"<Hangup{_attrs({'reason': reason})}/>"


def dial(
    numbers: str | list[str],
    *,
    caller_id: str | None = None,
    caller_name: str | None = None,
    action: str | None = None,
    method: str | None = None,
    timeout: int | None = None,
    time_limit: int | None = None,
    dial_music: str | None = None,
    redirect: bool | None = None,
    callback_url: str | None = None,
) -> str:
    """Build a <Dial> that bridges the inbound caller to ``numbers``.

    ``caller_id`` is what the *called* party (the B-leg) sees — for masking this
    is always the masking number, never the real caller's number.
    """
    if isinstance(numbers, str):
        numbers = [numbers]
    attrs = _attrs({
        "callerId": caller_id,
        "callerName": caller_name,
        "action": action,
        "method": method,
        "timeout": timeout,
        "timeLimit": time_limit,
        "dialMusic": dial_music,
        "redirect": redirect,
        "callbackUrl": callback_url,
    })
    inner = "".join(f"<Number>{escape(n)}</Number>" for n in numbers)
    return f"<Dial{attrs}>{inner}</Dial>"


def gather(
    *,
    action: str,
    prompt: str | None = None,
    method: str | None = None,
    input_type: str | None = None,
    num_digits: int | None = None,
    finish_on_key: str | None = None,
    execution_timeout: int | None = None,
    language: str | None = None,
) -> str:
    """Build a <Gather> that collects DTMF/speech and POSTs it to ``action``.

    The action URL receives ``Digits`` (DTMF) / ``Speech`` (transcript) /
    ``InputType``. A nested <Speak> ``prompt`` is played while collecting.
    """
    attrs = _attrs({
        "action": action,
        "method": method,
        "inputType": input_type,
        "numDigits": num_digits,
        "finishOnKey": finish_on_key,
        "executionTimeout": execution_timeout,
        "language": language,
    })
    inner = speak(prompt) if prompt else ""
    return f"<Gather{attrs}>{inner}</Gather>"
