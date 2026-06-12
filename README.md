# Vobiz — PIN-Based Number Masking (Single DID)

**One [Vobiz](https://vobiz.ai) number for everyone: callers dial it, enter a
PIN, and the PIN decides who they reach — the most cost-effective masking, on a
single phone number.**

Like a conference bridge or voicemail box: dial one number, a voice asks for a
code, and the code routes the call. The single DID can serve unlimited
destinations because the *PIN* is the address, not the number.

> Built and maintained by **Team Vobiz**. This is the "PIN-based, single-DID"
> flavour of Vobiz number masking.

---

## How it works (a two-step flow)

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
> numbers. Cheapest masking you can build.

---

## Configuration (everything via `.env`)

```bash
cp .env.example .env
```

```ini
VOBIZ_AUTH_ID=MA_XXXXXXXXXXXXXXXX
VOBIZ_AUTH_TOKEN=your_auth_token
VOBIZ_API_BASE=https://api.vobiz.ai/api/v1
PUBLIC_BASE_URL=https://your-tunnel.trycloudflare.com

MASKING_DID=919000000001                                  # the single number everyone dials
PIN_MAP=1234:919876511111,5678:919876522222,9012:919876533333   # pin:destination pairs
PIN_ALLOWLIST=                                            # optional: pin=num1|num2,...
```

`.env` is gitignored; placeholder defaults let the app and tests run without one.
Set `PUBLIC_BASE_URL` so the `<Gather action>` is a full HTTPS URL Vobiz can fetch.

---

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app:app --reload --port 8004
```

### Test offline

```bash
pytest -q
# step 1: answer -> Gather (asks for PIN)
curl -s -X POST localhost:8004/answer -d "From=910000000000" -d "To=919000000001"
# step 2: caller entered a PIN -> Dial (or reject)
curl -s -X POST localhost:8004/collect-pin -d "From=910000000000" -d "To=919000000001" -d "Digits=1234"
```

### Go live

```bash
uvicorn app:app --port 8004
cloudflared tunnel --url http://127.0.0.1:8004    # put URL in .env as PUBLIC_BASE_URL
./.venv/bin/python setup_live.py                  # create app + attach the single DID
```

`setup_live.py` calls **Create Application** and **Attach** for `MASKING_DID`.

---

## Project structure

| File | Purpose |
|------|---------|
| `app.py` | FastAPI `/answer` (Gather) + `/collect-pin` (resolve & Dial) + `/health`. |
| `mappings.py` | DID, PIN→destination map, optional allow-list — all from `.env`. |
| `vobiz_xml.py` | Vobiz XML builders (incl. `<Gather>`). |
| `setup_live.py` | Create Application + attach the single DID. |
| `test_flows.py` | Offline tests (prompt, valid PIN, invalid PIN, allow-list). |
| `GUIDE.md` | Beginner-friendly deep dive. |

---

## PIN security

- Make PINs unique per relationship; rotate them regularly (especially after use).
- Combine with short-lived sessions to time-bound a PIN to a delivery window.
- Use `PIN_ALLOWLIST` so even a leaked PIN only works for the intended caller.
- Use 6 digits and rate-limit wrong attempts for higher security.

---

## Pros & cons

**Pros**
- Cheapest — a single DID serves unlimited destinations.
- Works with one number you already own.
- Caller freedom — anyone with the right PIN gets through (optionally allow-listed).

**Cons**
- Callers must enter a PIN (one extra step; may need app/UX changes).
- PINs need rotation.
- Slightly more complex two-step flow.

---

## Built by Team Vobiz

[Vobiz](https://vobiz.ai) is a programmable voice & SIP-trunking platform.

Author: **Piyush Sahoo** — [LinkedIn](https://www.linkedin.com/in/piyush-s713/)

## License

[MIT](./LICENSE) © Vobiz
