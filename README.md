# Vobiz — PIN-Based Number Masking (Single DID)

**One [Vobiz](https://vobiz.ai) number for everyone: callers dial it, enter a PIN, and the PIN decides who they reach — the most number-efficient masking, on a single phone number.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-3776ab.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![Docs](https://img.shields.io/badge/Docs-docs.vobiz.ai-1f8b4c.svg)](https://docs.vobiz.ai)

> This is the **PIN-based, single-DID** flavour of Vobiz number masking, one of
> four reference implementations built and maintained by the Vobiz team. See
> [Choosing a masking strategy](#choosing-a-masking-strategy) to compare all four
> and pick the right one.

---

## Overview

Number masking lets two people speak on a real phone call without either of them
learning the other's phone number. A platform-owned number — a DID — sits in the
middle. Callers dial the masking number, and the platform places a second call to
the real destination and bridges the two legs together, presenting the masking
number as the caller ID so the real numbers never reach either handset.

This repository implements the flavour where the *PIN* is the address rather
than the number. A single DID serves every destination. On answer, the backend
returns a `<Gather>` that plays a prompt and collects four DTMF digits; Vobiz
POSTs those digits to a second endpoint, which looks up the PIN and returns the
`<Dial>` that bridges the call. Because routing is decided by what the caller
types rather than by which number they rang, adding a destination means adding a
row to a table — never renting another number.

It behaves much like a conference bridge or a voicemail system: dial one number,
a voice asks for a code, and the code routes you. That two-step flow is the one
piece of extra complexity compared with the other flavours, and it buys two
things. The DID count is fixed at one no matter how many destinations you serve,
and the caller does not need to be on a phone you know about — anyone holding a
valid PIN gets through. An optional per-PIN allow-list is available when you want
both factors: the right PIN *and* a known caller ID.

The moving parts are small. Vobiz owns the DID, terminates the inbound call,
plays the prompt, collects the digits and performs the bridging. A FastAPI
backend of about a hundred lines holds the PIN table and answers two webhooks
with short XML documents. There is no database and no per-call state, so requests
are independent and idempotent. By the end of the setup below you will have a
Vobiz Application created over the REST API, your DID attached to it, a local
server exposed over an HTTPS tunnel, and a real call routed by PIN.

---

## Choosing a masking strategy

Four sibling repositories implement the same idea with different trade-offs. They
share the same `vobiz_xml.py` helpers and the same `setup_live.py` shape, so
moving between them is cheap. **This repository is the highlighted row.**

| Strategy | DIDs required | Who may call | State needed | Best for |
|----------|---------------|--------------|--------------|----------|
| **PIN-based, single DID (this repo)** | **Exactly one, for everybody** | **Anyone who knows a valid PIN, optionally allow-listed** | **None — PIN table** | **Many destinations reachable through one advertised number** |
| [One-way (destination-based)](https://github.com/vobiz-ai/Vobiz-One-Way-Number-Masking) | One per destination | Anyone, from any phone | None — stateless lookup | A small, fixed set of protected people reachable by the general public |
| [Two-way (client-hosted)](https://github.com/vobiz-ai/Vobiz-Two-Way-Number-Masking) | Two per pairing — one per direction | Only the two registered real numbers | None — static table | Long-lived agent ↔ customer relationships where both sides must initiate |
| [Session-based two-way](https://github.com/vobiz-ai/Vobiz-Session-Based-Number-Masking) | A pool sized to peak concurrent conversations | Only the two numbers bound to the live session | Session store with a TTL | High volume, short-lived jobs — deliveries, rides, viewings |

A quick way to choose: if the *PIN* is the address, use PIN-based. If the number
**is** the address, use one-way. If the *pair* is the address, use two-way. If
the *job* is the address, use sessions.

### Pros and cons of PIN-based masking

**Pros**
- Fewest numbers — a single DID serves an unlimited number of destinations.
- Works with one number you already own; adding destinations costs nothing.
- Caller freedom — anyone holding the right PIN gets through, from any phone.
- Optional per-PIN allow-list gives you two factors when you want them.

**Cons**
- Callers must enter a PIN, which is an extra step and may need UX changes in
  whatever surface hands out the number.
- PINs are shared secrets and need rotation.
- The flow is two requests rather than one, so there is slightly more to debug.

---

## What you can build with it

- **Support and escalation routing on one published number.** Print one number
  everywhere; the PIN on a customer's account page routes them to their assigned
  representative without exposing that person's direct line.
- **Ticketed or booking-based call-backs.** Issue the caller a PIN with their
  booking confirmation. It routes them to the right practitioner, agent or
  engineer for that booking, and you can retire the PIN when the booking closes.
- **Anonymous tip or whistleblowing lines.** Different PINs route to different
  case handlers behind a single public number, and no caller registration is
  required, so people can ring from any phone.
- **Multi-tenant contact numbers.** One DID serves many client organisations,
  each with its own PIN range, without renting a number per tenant.
- **Field access lines for contractors.** Hand a contractor a PIN for the site
  they are attending; the PIN reaches that site's contact, and the allow-list can
  restrict it to the contractor's own mobile.
- **Low-volume international presence.** Where DIDs are expensive or slow to
  provision, a single number plus a PIN table gives you reach immediately.

---

## How it works

Unlike the other flavours, this is a **two-step** flow. Vobiz calls your backend
twice: once to find out what to do with the call, and again to hand over the
digits the caller typed.

```
caller ──dial DID──► Vobiz ──POST /answer──► backend
                                             └─ return <Gather action=/collect-pin>
caller hears "enter your PIN", types 1234#
                       Vobiz ──POST /collect-pin {Digits=1234}──► backend
                                             └─ look up PIN -> destination
caller ◄══ bridged ══ Vobiz ◄── <Dial callerId=DID><Number>destination</> ──┘
```

- `POST /answer` → returns a `<Gather>` that collects the PIN (DTMF, `#` to finish)
- `POST /collect-pin` → reads `Digits`, resolves PIN→destination, returns `<Dial>`
- Optional allow-list restricts which caller numbers may use a PIN

> **Numbers needed: exactly one.** Add destinations by adding PINs — never new
> numbers.

The `<Gather>` is configured for exactly four DTMF digits, finishing on `#`, with
a fifteen-second execution timeout. The elements that follow the `<Gather>` in
the same `<Response>` — a `<Speak>` and a `<Hangup reason="no_input"/>` — are the
fallback: they run only if the caller enters nothing, so a silent call ends
politely instead of hanging.

The `<Gather>` `action` is built at import time as
`f"{os.environ.get('PUBLIC_BASE_URL', '')}/collect-pin"`. With `PUBLIC_BASE_URL`
set it is an absolute HTTPS URL; with the variable unset it degrades to the
relative path `/collect-pin`, which Vobiz resolves against the Application's
`answer_url`. Both work, but setting the variable is the clearer configuration.

On the second request, `mappings.resolve(pin, from_number)` performs two checks
in order. The PIN must exist in `PIN_TO_DESTINATION`; and if that PIN has an
entry in `PIN_ALLOWLIST`, the caller's number must appear in it. Failing either
check produces the same spoken rejection and
`<Hangup reason="invalid_pin"/>`, so a caller probing the line cannot tell a
wrong PIN from a right PIN dialled from the wrong phone.

One detail worth knowing: the allow-list comparison is an exact string match on
`From`, whereas the PIN lookup is an exact match on `Digits`. Neither is
normalised, so allow-list entries must be written in the same E.164 form Vobiz
reports on the webhook.

---

## Architecture

| File | Responsibility |
|------|----------------|
| `app.py` | FastAPI application. `POST /answer` returns the `<Gather>` prompt; `POST /collect-pin` resolves the PIN and returns the `<Dial>`; `GET /health` is a liveness probe returning `{"status": "ok", "strategy": "pin-based"}`. Also holds `PIN_LENGTH` (4) and builds `COLLECT_ACTION`. |
| `mappings.py` | The routing brain. Parses `MASKING_DID`, `PIN_MAP` and `PIN_ALLOWLIST` from the environment and exposes `resolve(pin, from_number)`. |
| `vobiz_xml.py` | Builders that emit Vobiz XML strings — `response()`, `dial()`, `gather()`, `speak()`, `hangup()` — with attribute quoting and text escaping handled via `xml.sax.saxutils`. |
| `setup_live.py` | One-time live provisioning. Creates a Vobiz Application pointing at `PUBLIC_BASE_URL/answer` and attaches it to `MASKING_DID`. |
| `test_flows.py` | Offline tests driving the app through `fastapi.testclient.TestClient` — the prompt, a valid PIN, an invalid PIN, and the allow-list. No calls, no credentials, no network. |
| `.env.example` | Template for the six environment variables the code reads. Copy to `.env`, which is gitignored. |
| `GUIDE.md` | A long, beginner-friendly walkthrough of the same flow, including wire-level message examples and a glossary. |

### Where state lives

| Concern | Owner |
|---------|-------|
| The phone number (one DID) | Vobiz |
| `answer_url` routing (the Application object) | Vobiz |
| Prompt playback and DTMF collection | Vobiz (driven by your `<Gather>`) |
| `PIN -> destination` table and the allow-list | **Your backend** (`mappings.py`, loaded from `.env`) |
| Call bridging and media | Vobiz |
| Per-call state between the two requests | **None** — the PIN arrives with the second request, so nothing is carried across |

The two-step flow does not require a session, because Vobiz carries the call
context between the requests: `/collect-pin` receives `From`, `To`, `Digits` and
`CallUUID` for the same call. That keeps the backend stateless, safe to retry and
safe to run behind a load balancer with any number of replicas.

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| A Vobiz account | Sign up at [vobiz.ai](https://vobiz.ai). You need your Auth ID and Auth Token from the [console](https://console.vobiz.ai). |
| One Vobiz DID | A single voice-enabled number on your account is all this flavour needs. |
| A real phone to receive the call | The destination behind the PIN you test rings for real. |
| A phone that can send DTMF | Any ordinary handset; the caller has to key in the PIN during the call. |
| Python 3.9 or newer | Every module uses `from __future__ import annotations`, so PEP 604 (`str \| None`) syntax is fine on 3.9. Developed against 3.11. |
| An HTTPS tunnel | [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) or [ngrok](https://ngrok.com/), so Vobiz can reach a locally running server. Vobiz needs a publicly resolvable HTTPS URL. |
| `curl` (optional) | For poking the two webhooks by hand. |

You do **not** need a database, a message queue, or any cloud account beyond
Vobiz to run this example.

---

## Setup

1. **Clone the repository and enter it.**

   ```bash
   git clone https://github.com/vobiz-ai/Vobiz-PIN-Based-Number-Masking.git
   cd Vobiz-PIN-Based-Number-Masking
   ```

2. **Create a virtual environment and install the dependencies.**

   ```bash
   python -m venv .venv
   source .venv/bin/activate          # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Install `httpx` if you intend to run the test suite.** `TestClient` needs
   it and it is not listed in `requirements.txt`.

   ```bash
   pip install httpx
   ```

4. **Create your `.env`.**

   ```bash
   cp .env.example .env
   ```

   Fill in `VOBIZ_AUTH_ID` and `VOBIZ_AUTH_TOKEN`, set `MASKING_DID` to your
   number, and replace the `PIN_MAP` entries with your own PIN and destination
   pairs. Every variable is documented under
   [Configuration](#configuration).

5. **Confirm the routing logic before touching your live account.**

   ```bash
   pytest -q
   ```

6. **Start the server.**

   ```bash
   uvicorn app:app --reload --port 8004
   ```

7. **Expose it over HTTPS.** In a second terminal:

   ```bash
   cloudflared tunnel --url http://127.0.0.1:8004
   ```

   Copy the printed `https://….trycloudflare.com` URL into `.env` as
   `PUBLIC_BASE_URL`, then **restart the server** — `COLLECT_ACTION` is built
   once at import time, so a running process will not pick up the new value.

8. **Provision your live Vobiz account.** This creates an Application and
   attaches it to your DID, so run it deliberately:

   ```bash
   ./.venv/bin/python setup_live.py
   ```

9. **Place a real call.** Dial the masking DID from any phone, key in a PIN
   followed by `#`, and the destination for that PIN rings, showing the masking
   number as the caller ID.

> A `trycloudflare.com` hostname is ephemeral. If the tunnel restarts and the URL
> changes, update `PUBLIC_BASE_URL`, restart the server and re-run
> `setup_live.py`, or point the Application at a stable domain you control.

---

## Configuration

Everything is read from the environment. `python-dotenv` loads a local `.env`
automatically at import time, and `.env` is gitignored. No phone number, PIN or
credential is hardcoded in source.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VOBIZ_AUTH_ID` | Yes, for `setup_live.py` | none | Your Vobiz Auth ID, sent as the `X-Auth-ID` header and used in the account path of every REST call. `setup_live.py` reads it with `os.environ[...]` and raises `KeyError` if it is absent. Not read by `app.py`. |
| `VOBIZ_AUTH_TOKEN` | Yes, for `setup_live.py` | none | Your Vobiz Auth Token, sent as the `X-Auth-Token` header. Also mandatory in `setup_live.py`. Not read by `app.py`. |
| `VOBIZ_API_BASE` | No | `https://api.vobiz.ai/api/v1` | Base URL for the Vobiz REST API. Override only to target a different environment. |
| `PUBLIC_BASE_URL` | Yes for `setup_live.py`; recommended for `app.py` | empty string in `app.py`; mandatory in `setup_live.py` | The public HTTPS origin of *this* backend. `setup_live.py` registers `<PUBLIC_BASE_URL>/answer` as the Application's `answer_url` and `hangup_url`. `app.py` also uses it to build the absolute `<Gather action>`; if unset, the action degrades to the relative path `/collect-pin`. Read once at import time. |
| `MASKING_DID` | Yes in practice | `919000000001` | The single DID everyone dials, in E.164 without a leading `+`. `setup_live.py` attaches the Application to it. Note that `app.py` sets `callerId` from the webhook's `To` field rather than from this variable, so it is used for provisioning and documentation. |
| `PIN_MAP` | Yes in practice | `1234:919876511111,5678:919876522222,9012:919876533333` | The routing table: comma-separated `pin:destination` pairs. `mappings.py` splits on `,` then on the first `:`, trims whitespace, and skips any fragment without a colon. PINs are matched as exact strings against the collected `Digits`, so they should be the same length as `PIN_LENGTH`. |
| `PIN_ALLOWLIST` | No | empty — every PIN is unrestricted | Optional second factor. Format `pin1=num1\|num2,pin2=num3`: entries are split on `,`, then on the first `=`, and the numbers on `\|`. A PIN absent from this map accepts any caller. Comparison against `From` is an exact string match with no normalisation. |
| `APP_NAME` | No | `vobiz_pin_number_masking` | Name given to the Vobiz Application created by `setup_live.py`. Useful when you provision more than one environment against the same account. |

Two constants live in `app.py` rather than the environment: `PIN_LENGTH` is `4`,
which sets the `<Gather numDigits>`, and the `<Gather>` execution timeout is
fifteen seconds. Change the PIN length in both `PIN_LENGTH` and your `PIN_MAP`
together, or the collected digits will never match a row.

Notes on the defaults: the placeholder values let `uvicorn` start and `pytest`
pass with no `.env` at all, which is what makes the offline test loop possible.
They are not routable numbers and the sample PINs are sequential and guessable —
replace both before going live.

---

## Running it

Start the webhook server:

```bash
uvicorn app:app --reload --port 8004
```

You should see uvicorn bind to `127.0.0.1:8004`. Confirm it is alive:

```bash
curl -s localhost:8004/health
# {"status":"ok","strategy":"pin-based"}
```

Step one — simulate what Vobiz POSTs when someone dials the DID:

```bash
curl -s -X POST localhost:8004/answer -d "From=910000000000" -d "To=919000000001"
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response><Gather action="/collect-pin" method="POST" inputType="dtmf" numDigits="4" finishOnKey="#" executionTimeout="15"><Speak>Please enter your access PIN followed by the hash key.</Speak></Gather><Speak>We did not receive any input. Goodbye.</Speak><Hangup reason="no_input"/></Response>
```

With `PUBLIC_BASE_URL` set, the `action` is the absolute HTTPS URL instead of the
relative path shown above.

Step two — simulate the caller keying in a PIN:

```bash
curl -s -X POST localhost:8004/collect-pin -d "From=910000000000" -d "To=919000000001" -d "Digits=1234"
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response><Dial callerId="919000000001" timeout="30"><Number>919876511111</Number></Dial></Response>
```

And a PIN that is not in the table:

```bash
curl -s -X POST localhost:8004/collect-pin -d "From=910000000000" -d "To=919000000001" -d "Digits=0000"
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response><Speak>That PIN is not valid. Goodbye.</Speak><Hangup reason="invalid_pin"/></Response>
```

Run the offline suite, which covers the prompt, a valid PIN, an invalid PIN and
the allow-list blocking a wrong source number:

```bash
pytest -q
# 4 passed
```

When you run `setup_live.py`, expect a `201` from the create call, an `app_id`,
then a single attach line:

```
[*] Creating application 'vobiz_pin_number_masking' -> answer_url=https://….trycloudflare.com/answer
    CREATE -> 201 {"app_id": …}
[*] app_id = …
    ATTACH 919000000001 -> 200 …
```

On a live call you will hear the prompt, key in the PIN and `#`, then hear
ringing while Vobiz places the B-leg. The destination handset displays the
masking number.

---

## Reference

### HTTP surface of this backend

| Method | Path | Called by | Input | Response |
|--------|------|-----------|-------|----------|
| `POST` | `/answer` | Vobiz, on every inbound call to the attached DID | Form fields `From`, `To` (both required), plus optional `CallUUID`, `Direction`, `CallStatus` | `application/xml` — `<Gather>` followed by the no-input fallback |
| `POST` | `/collect-pin` | Vobiz, once the caller finishes entering digits | Form fields `From`, `To` (both required), plus optional `Digits`, `CallUUID` | `application/xml` — either `<Dial>` or `<Speak>` + `<Hangup>` |
| `GET` | `/health` | You, or your monitoring | none | `{"status": "ok", "strategy": "pin-based"}` |

`From` and `To` are declared with `Form(...)` on both webhooks, so a request
missing either one gets a `422` from FastAPI rather than reaching the handler.
`Digits` defaults to an empty string, which never matches a PIN and so falls
through to the rejection path.

### Vobiz XML elements used

| Element | Attributes used here | Purpose |
|---------|----------------------|---------|
| [`<Response>`](https://docs.vobiz.ai/xml/overview/how-it-works) | — | Root element of every reply. |
| [`<Gather>`](https://docs.vobiz.ai/xml/gather) | `action`, `method`, `inputType`, `numDigits`, `finishOnKey`, `executionTimeout` | Plays the nested prompt and collects four DTMF digits, finishing on `#`, then POSTs `Digits` to `action`. |
| [`<Speak>`](https://docs.vobiz.ai/xml/speak) | — | The PIN prompt nested inside `<Gather>`, and the two rejection messages. |
| [`<Dial>`](https://docs.vobiz.ai/xml/dial) | `callerId`, `timeout` | Places the B-leg and bridges it to the A-leg. `callerId` is set to the dialled masking DID, which is what makes the destination see the mask instead of the caller. `timeout` is 30 seconds. |
| `<Number>` | — | Nested inside `<Dial>`; the real destination to ring. |
| [`<Hangup>`](https://docs.vobiz.ai/xml/hangup) | `reason` | Ends the call. This example uses `reason="no_input"` and `reason="invalid_pin"`. |

### Vobiz REST calls made by `setup_live.py`

Both requests carry the headers `X-Auth-ID`, `X-Auth-Token` and
`Content-Type: application/json`, with a 20-second timeout.

| Call | Request | Body |
|------|---------|------|
| [Create Application](https://docs.vobiz.ai/applications) | `POST {VOBIZ_API_BASE}/Account/{auth_id}/Application/` | `app_name`, `answer_url`, `answer_method: POST`, `hangup_url`, `hangup_method: POST` |
| [Attach number](https://docs.vobiz.ai/applications) | `POST {VOBIZ_API_BASE}/Account/{auth_id}/numbers/{%2BDID}/application` | `{"application_id": …}` |

The DID in the attach path is URL-encoded with its `+` prefix — `919000000001`
becomes `%2B919000000001`.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Caller hears "That PIN is not valid. Goodbye." for a PIN you know is correct. | `resolve()` returned `None`. Either the PIN is not in `PIN_MAP`, or it *is* but `PIN_ALLOWLIST` has an entry for it and the caller's number is not in that entry. Both produce the same message by design. | Check the pair exists in `PIN_MAP`, then check `PIN_ALLOWLIST` for that PIN. Restart the server — both tables are parsed once at import time. |
| The caller's PIN is rejected only from one particular phone. | The allow-list comparison against `From` is an exact string match with no normalisation, so `918888800001` and `8888800001` are different values. | Write allow-list numbers in exactly the E.164 form Vobiz reports on the webhook. |
| Caller hears the prompt, enters the PIN, and nothing happens. | The `<Gather action>` is unreachable: `PUBLIC_BASE_URL` was set after the process started, so `COLLECT_ACTION` still holds the old value or the bare relative path. | Set `PUBLIC_BASE_URL` in `.env` and restart the server; `COLLECT_ACTION` is built at import time. |
| Caller hears "We did not receive any input. Goodbye." | No digits arrived within the fifteen-second execution timeout, or the caller's handset did not send DTMF. | Confirm the caller pressed `#` to finish, and raise `execution_timeout` in `app.py` if fifteen seconds is too tight for your prompt. |
| A four-digit PIN never matches even though it is in `PIN_MAP`. | `PIN_LENGTH` in `app.py` and the PIN length in `PIN_MAP` disagree, so `<Gather numDigits>` collects the wrong number of digits and the exact string match fails. | Keep `PIN_LENGTH` and every PIN in `PIN_MAP` the same length. |
| `pytest` aborts with `RuntimeError: The starlette.testclient module requires the httpx package to be installed.` | `requirements.txt` does not list `httpx`, which `fastapi.testclient.TestClient` needs. | `pip install httpx`, then re-run `pytest -q`. |
| `POST /answer` or `/collect-pin` returns `422 Unprocessable Entity`. | `From` or `To` was absent from the form body, or `python-multipart` is not installed so FastAPI cannot parse `application/x-www-form-urlencoded`. | Send both fields, and confirm `pip install -r requirements.txt` completed — `python-multipart` is pinned there. |
| `setup_live.py` exits immediately with `KeyError: 'VOBIZ_AUTH_ID'`. | `load_dotenv()` reads `.env` relative to the working directory and found nothing, or the variable is missing from the file. | Run the script from the repository root and confirm `.env` exists with all three mandatory variables. |
| `CREATE -> 401` (or any non-`200`/`201`) and the script returns exit code 1. | Wrong Auth ID or Auth Token, or `VOBIZ_API_BASE` points somewhere unexpected. | Re-copy both credentials from the console; leave `VOBIZ_API_BASE` at its default unless you were told otherwise. |
| `ATTACH … -> 404`, or no `ATTACH` line at all. | The number is not on your account, it was written with a `+` or spaces — `setup_live.py` prepends the `+` itself — or `MASKING_DID` is unset, in which case the attach loop has nothing to iterate over. | Use bare E.164 digits with country code and no `+`, and confirm the DID is listed on your account. |
| Vobiz reports the answer URL is unreachable, or calls simply hang up. | The tunnel restarted and issued a new hostname, so the Application's `answer_url` points at a dead origin. | Update `PUBLIC_BASE_URL`, restart the server, and re-run `setup_live.py`, or move to a stable HTTPS domain. |

---

## Security notes

- **PINs are shared secrets, and the PIN table is the sensitive asset.**
  `PIN_MAP` pairs a guessable-length code with a real personal phone number.
  Keep it in a secret manager rather than a checked-in file or a container image
  layer, and keep `.env` gitignored — it already is.
- **If the PIN table leaks, every destination in it is exposed.** An attacker
  learns both the real numbers and the codes that reach them. Treat it as a
  personal-data breach: rotate every PIN, re-point the table, consider retiring
  the DID, and notify the people whose numbers were exposed under whatever regime
  applies to you.
- **Four digits is a small keyspace and nothing rate-limits guesses.** A caller
  can redial and try again indefinitely, and there is no lockout, no attempt
  counter and no delay in this example. Before running it anywhere real, make
  PINs longer, make them unique per relationship rather than per destination,
  rotate them after use, and rate-limit wrong attempts per caller and per DID.
- **Use `PIN_ALLOWLIST` when you can.** It turns a single shared secret into two
  factors, so a leaked PIN is useless from an unknown handset. It is off by
  default because it costs you caller freedom, which is the main reason to pick
  this flavour in the first place — decide deliberately.
- **PIN entry is audible and recordable.** DTMF tones travel in the audio path.
  If you add call recording anywhere in this flow, ensure the digits are
  suppressed from the recording, and remember that a caller keying a PIN in
  public can be overheard.
- **Both webhooks are unauthenticated in this example.** Anyone who discovers the
  tunnel URL can POST directly to `/collect-pin` and brute-force the PIN space
  without ever placing a call. Restrict both endpoints — an IP allow-list for
  Vobiz's egress, a shared secret in the path, mutual TLS, or a signature check —
  and serve them over HTTPS only.
- **Minimise what you retain.** This example logs nothing. If you add logging,
  never write `Digits` to a log at all, avoid writing `From` and the resolved
  destination in clear text, keep `CallUUID` for correlation, and set a retention
  window rather than keeping call metadata indefinitely.
- **Real numbers travel in the XML response.** The `<Dial>` body carries the
  destination in the clear, so the tunnel or load balancer terminating TLS is
  inside your trust boundary. Do not proxy the webhooks through a third party you
  would not trust with the PIN table itself.
- **Credentials in `setup_live.py` are account-wide.** The Auth Token can create
  Applications and re-point numbers. Scope, store and rotate it accordingly, and
  never paste live values into an issue or a pull request.

---

## Roadmap

> Planned improvements to this example. Ideas and pull requests are welcome —
> open an issue to discuss anything here.

- [ ] Move `PIN_MAP` and `PIN_ALLOWLIST` out of environment variables into a
      datastore, so PINs can be issued and revoked at runtime instead of
      requiring a process restart.
- [ ] Give PINs an expiry so a code can be time-bound to a booking or a job, and
      expire automatically rather than living until someone edits the table.
- [ ] Add attempt limiting and lockout — count wrong PINs per caller and per DID,
      back off, and stop the current unlimited retry loop.
- [ ] Store PINs hashed rather than in plain text, and add an issue-and-revoke
      admin API so the clear-text code exists only at the moment it is handed out.
- [ ] Authenticate both webhooks so `/answer` and `/collect-pin` accept requests
      only from Vobiz, closing the direct brute-force path.
- [ ] Emit structured call records and metrics — masked-call volume, PIN success
      and failure rates, no-input rates — behind a `/metrics` endpoint, with
      digits never logged.
- [ ] Make `PIN_LENGTH` and the `<Gather>` timeout configurable from the
      environment, and validate at startup that every PIN in `PIN_MAP` matches
      the configured length.
- [ ] Broaden `test_flows.py` beyond the four existing cases to cover the
      no-input fallback, malformed `PIN_MAP` entries and empty configuration, and
      run it in CI on every push.
- [ ] Pin the test dependencies (`httpx`) in `requirements.txt` so a fresh clone
      can run `pytest` without an extra install step.

---

## Contributing

Issues and pull requests are welcome — bug reports, corrections to the docs, and
additional test coverage all help.

Before opening a pull request:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt httpx
pytest -q
```

Please keep changes grounded in the Vobiz XML and REST behaviour documented at
[docs.vobiz.ai](https://docs.vobiz.ai), keep real phone numbers, PINs and
credentials out of commits, and describe how you verified a change — offline
tests, a live call, or both.

## License

Released under the [MIT License](./LICENSE) © Vobiz.

MIT is permissive: you may use, modify, and redistribute this code, including in
closed-source commercial products, provided the copyright notice and licence text
are retained. There is no warranty. If your organisation needs a different
licensing arrangement, contact [piyush@vobiz.ai](mailto:piyush@vobiz.ai).

## Built by Team Vobiz

[Vobiz](https://vobiz.ai) is a programmable voice and SIP-trunking platform for
voice APIs, SIP trunking, and AI voice agents. This repository is built and
maintained by the Vobiz team.

**Maintainer:** Piyush Sahoo — [piyush@vobiz.ai](mailto:piyush@vobiz.ai) · [LinkedIn](https://www.linkedin.com/in/piyush-s713/)

Questions, or want to talk through an integration? Open an issue on this repo,
or reach out directly at [piyush@vobiz.ai](mailto:piyush@vobiz.ai).

**Useful links:** [Docs](https://docs.vobiz.ai) · [API reference](https://docs.vobiz.ai/api-reference) · [Sign up](https://vobiz.ai)
