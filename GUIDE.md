# Strategy 4 — PIN-Based Masking with a Single Number: The Complete Beginner Guide

> ⭐ **This is the strategy you can run TODAY with your one Vobiz number
> `+91 90000 00001`.** All the others need two or more numbers. This one needs
> exactly **one**. Read Strategy 1's guide first for the basics (masking number,
> Answer URL, `<Dial>`, bridging); here we add **two** new ideas — a *menu that
> asks for a PIN* (`<Gather>`) and *using the PIN to choose the destination*.

---

## Table of contents

1. [The big idea: one number for everyone, a PIN decides the rest](#1-the-big-idea)
2. [Why a single number can serve thousands of people](#2-why-a-single-number-works)
3. [The cast and numbers](#3-the-cast-and-numbers)
4. [How many phone numbers do you need? (the happy answer: one)](#4-how-many-numbers-do-you-need)
5. [The new ingredient: collecting a PIN with `<Gather>`](#5-the-new-ingredient-gather)
6. [The end-to-end story, told step by step](#6-the-end-to-end-story)
7. [Pictures of the flow](#7-pictures-of-the-flow)
8. [The exact messages on the wire](#8-the-exact-messages-on-the-wire)
9. [The code, line by line](#9-the-code-line-by-line)
10. [How to run it](#10-how-to-run-it)
11. [Connecting to your real Vobiz number (full walkthrough)](#11-connecting-to-your-real-vobiz-number)
12. [Testing without real calls](#12-testing-without-real-calls)
13. [PIN security: rotation, expiry, allow-lists](#13-pin-security)
14. [What can go wrong](#14-what-can-go-wrong)
15. [Pros, cons, and when to choose this](#15-pros-cons-and-when-to-choose-this)
16. [FAQ](#16-faq)
17. [Glossary](#17-glossary)

---

## 1. The big idea

In the other strategies, the **number** told the system who to connect. Here we
flip it: there is **only one** masking number, and everyone dials the same one.
The system then **asks the caller to type a PIN**, and the **PIN** tells the
system who to connect to.

A real-world analogy: think of a **conference bridge** or a **voicemail box**. You
call one phone number, and then a voice says "please enter your access code." The
code you type decides which room (or which mailbox) you reach. Same number for
everyone; the code does the routing.

PIN-based masking is exactly that idea applied to connecting two real people while
hiding their numbers:

> Everyone dials the single Vobiz number. A voice asks for a PIN. The PIN maps to
> a real destination. The system dials that destination (showing the Vobiz number
> as the caller ID) and bridges the two parties.

---

## 2. Why a single number works

In one-way mapping (Strategy 3), the *number* was the address, so you needed one
number per person. Here, the **PIN** is the address. And PINs are free — you can
mint as many as you like. So a single phone number can route to thousands of
different destinations, each behind its own PIN.

That is why this strategy is the **most cost-effective**: you rent **one** DID and
support unlimited destinations through it. For a business watching costs, this is
the cheapest masking you can build.

---

## 3. The cast and numbers

```
The single Vobiz masking number (your DID):
   +91 90000 00001        (code: 919000000001)   <-- YOU OWN THIS ONE

Destinations behind PINs:
   PIN 1234 -> Customer A   +91 98765 11111   (code: 919876511111)
   PIN 5678 -> Customer B   +91 98765 22222   (code: 919876522222)
   PIN 9012 -> Customer C   +91 98765 33333   (code: 919876533333)
```

Notice: there is just one phone number. Everything else is PINs pointing at
destinations. Add a new destination = add a new PIN row. No new phone number ever
needed.

---

## 4. How many numbers do you need?

> **Exactly one. The one you already own: `+91 90000 00001`.**

This is the whole reason this guide marks Strategy 4 as "runnable today" for you.
The other three need 2+ numbers; this needs 1. You can do a complete, real,
end-to-end live demo right now with your single DID. See section 11.

---

## 5. The new ingredient: `<Gather>`

So far we only used `<Dial>` (call someone and bridge) and `<Speak>`/`<Hangup>`.
PIN-based masking needs one more XML instruction: **`<Gather>`**.

`<Gather>` means: **"play a prompt and then collect the digits the caller presses
on their keypad."** It is how the phone system asks a question and waits for the
caller to type an answer (their PIN).

Key parts of a `<Gather>`:
- a **prompt** (a `<Speak>` inside it) — "Please enter your access PIN followed by
  the hash key."
- `numDigits` — how many digits to expect (we use 4 for a 4-digit PIN).
- `finishOnKey` — which key means "I'm done" (we use `#`, the hash key).
- `action` — **where to send the typed digits**. When the caller finishes typing,
  Vobiz makes a **second** request to this URL, including the digits as a field
  called `Digits`.

So PIN-based masking is a **two-step conversation** with Vobiz:
1. **Step one — `/answer`:** Vobiz says "someone called." We reply with a
   `<Gather>` asking for the PIN.
2. **Step two — `/collect-pin`:** the caller types the PIN; Vobiz sends it to us;
   we look up the destination and reply with a `<Dial>`.

The other strategies were one step (just `/answer`). This one is two steps because
we have to pause and ask a question in the middle.

---

## 6. The end-to-end story

Let's walk a caller through it, slowly.

1. A customer wants to reach their delivery agent. They were told: "Call
   `+91 90000 00001` and enter PIN `1234`." (The app shows this, or an SMS does.)
2. The customer dials `+91 90000 00001`. The call reaches **Vobiz** (which owns
   that number).
3. Vobiz asks your **Answer URL** (`/answer`): "someone called your number, what
   do I do?"
4. Your server replies with a `<Gather>`: *"Please enter your access PIN followed
   by the hash key."* and tells Vobiz "when they finish typing, send the digits to
   `/collect-pin`."
5. Vobiz **plays the voice prompt** to the customer. The customer types `1 2 3 4`
   then `#`.
6. Vobiz sends those digits to your **`/collect-pin`** URL: `Digits=1234`.
7. Your server looks up PIN `1234` in its table → it maps to Customer A's agent
   `919876511111`. It replies with a `<Dial>`: *"call `919876511111`, show
   `919000000001` (the Vobiz number) as the caller ID."*
8. Vobiz calls the destination, the destination answers (seeing the Vobiz number,
   not the caller's real number), and Vobiz **bridges** the two. They talk. 🎉

If the customer types a wrong PIN (say `0000`), step 7 finds nothing in the table,
so your server replies "that PIN is not valid, goodbye" and hangs up.

---

## 7. Pictures of the flow

```
  Caller (any phone)        Vobiz (owns 919000000001)        Your server
       |                            |                              |
   1.  | dial 919000000001          |                              |
       |--------------------------->|                              |
   2.  |                            |  POST /answer                |
       |                            |----------------------------->|
   3.  |                            |  <Gather action="/collect-pin"
       |                            |    numDigits=4 finishOnKey="#">
       |                            |    <Speak>Enter your PIN...</Speak>
       |                            |  </Gather>                   |
       |                            |<-----------------------------|
   4.  |   "Please enter your PIN"  |                              |
       |<---------------------------|                              |
   5.  |   types 1 2 3 4 #          |                              |
       |--------------------------->|                              |
   6.  |                            |  POST /collect-pin           |
       |                            |  Digits=1234                 |
       |                            |----------------------------->|
   7.  |                            |        look up PIN 1234 -> 919876511111
       |                            |  <Dial callerId="919000000001">
       |                            |    <Number>919876511111</Number></Dial>
       |                            |<-----------------------------|
   8.  |                            |  call destination AS 919000000001, BRIDGE
       |========== BRIDGED: caller <-> 919000000001 <-> destination ==========|
```

---

## 8. The exact messages on the wire

### Step 1 — Vobiz → `/answer`

```
From=<any caller>&To=919000000001&CallUUID=abc&Direction=inbound&CallStatus=ringing
```

Your reply:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather action="https://your-server/collect-pin" method="POST"
          inputType="dtmf" numDigits="4" finishOnKey="#" executionTimeout="15">
    <Speak>Please enter your access PIN followed by the hash key.</Speak>
  </Gather>
  <Speak>We did not receive any input. Goodbye.</Speak>
  <Hangup reason="no_input"/>
</Response>
```

(The `<Speak>`+`<Hangup>` after the `<Gather>` is the fallback if the caller types
nothing — the call doesn't hang silently.)

### Step 2 — Vobiz → `/collect-pin`

After the caller types their PIN:

```
From=<any caller>&To=919000000001&Digits=1234&CallUUID=abc
```

Your reply (valid PIN):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Dial callerId="919000000001" timeout="30">
    <Number>919876511111</Number>
  </Dial>
</Response>
```

Your reply (invalid PIN):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Speak>That PIN is not valid. Goodbye.</Speak>
  <Hangup reason="invalid_pin"/>
</Response>
```

---

## 9. The code, line by line

Two files: `mappings.py` (PIN → destination table) and `app.py` (the two-step web
server).

### `mappings.py`

```python
MASKING_DID = "919000000001"   # your single Vobiz number, dialled by everyone

PIN_TO_DESTINATION = {
    "1234": "919876511111",  # Customer A's agent
    "5678": "919876522222",  # Customer B's agent
    "9012": "919876533333",  # Customer C's agent
}

PIN_ALLOWLIST = {}   # optional: restrict which caller numbers may use a PIN
```

The brain: one number, a table of PIN→destination, and an optional safety list.

```python
def resolve(pin, from_number):
    destination = PIN_TO_DESTINATION.get(pin)
    if destination is None:
        return None                         # unknown PIN -> reject
    allowed = PIN_ALLOWLIST.get(pin)
    if allowed and from_number not in allowed:
        return None                         # PIN restricted and caller not on list
    return destination
```

`resolve` returns the destination if the PIN is valid (and, if an allow-list
exists for that PIN, the caller is on it), otherwise `None`.

### `app.py`

**Step one — ask for the PIN:**

```python
@app.post("/answer")
async def answer(From=Form(...), To=Form(...), ...):
    xml = response(
        gather(
            action=COLLECT_ACTION,          # where to send the typed digits
            method="POST",
            input_type="dtmf",              # keypad digits (not speech)
            num_digits=PIN_LENGTH,          # 4
            finish_on_key="#",
            execution_timeout=15,
            prompt="Please enter your access PIN followed by the hash key.",
        ),
        speak("We did not receive any input. Goodbye."),  # fallback
        hangup(reason="no_input"),
    )
    return Response(content=xml, media_type="application/xml")
```

When Vobiz says "someone called", we reply with a `<Gather>` that plays the prompt
and will POST the digits to `/collect-pin`.

**Step two — use the PIN:**

```python
@app.post("/collect-pin")
async def collect_pin(From=Form(...), To=Form(...), Digits=Form(default=""), ...):
    destination = mappings.resolve(pin=Digits, from_number=From)
    if destination is None:
        return Response(response(speak("That PIN is not valid. Goodbye."),
                                 hangup(reason="invalid_pin")), media_type=XML)
    return Response(response(dial(destination, caller_id=To, timeout=30)),
                    media_type=XML)
```

Vobiz sends us the typed `Digits`. We look up the destination; if valid, we dial
it (showing the Vobiz number `To` as caller ID) and bridge. If not, we say so and
hang up.

That's the whole strategy: ask, then route.

---

## 10. How to run it

```bash
cd "number-masking-python"
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd 4_pin_based
uvicorn app:app --reload --port 8004
```

---

## 11. Connecting to your real Vobiz number

This is the full live walkthrough — you can do every step with your single number.

**Step A — edit the table for your real destinations.**
Open `4_pin_based/mappings.py`. `MASKING_DID` is already your number
(`919000000001`). Put **real test phone numbers** you can answer into
`PIN_TO_DESTINATION`, e.g.:

```python
PIN_TO_DESTINATION = {
    "1234": "91XXXXXXXXXX",   # a phone you can pick up to test
}
```

**Step B — start the server.**
```bash
cd 4_pin_based
uvicorn app:app --reload --port 8004
```

**Step C — open a public HTTPS doorway with ngrok.**
In a second terminal:
```bash
ngrok http 8004
```
Copy the `https://....ngrok-free.app` URL it shows.

**Step D — set `PUBLIC_BASE_URL` so the Gather action is a full URL.**
In your `.env`, set:
```
PUBLIC_BASE_URL=https://<your-ngrok>.ngrok-free.app
```
Restart uvicorn so it picks up the value. (This makes the `<Gather action>` point
back at your public server when Vobiz fetches it.)

**Step E — point the number at your server in the Vobiz dashboard.**
1. Log in to the Vobiz dashboard.
2. Open **Phone Numbers** → `+91 90000 00001`.
3. Set its **Answer URL** to `https://<your-ngrok>.ngrok-free.app/answer`
   (method **POST**).
4. Save.

> There is no documented REST endpoint to set a number's Answer URL for this
> account right now (the number-list API returns "Unauthorised" with your token),
> so use the dashboard. Your *account* credentials are valid — we confirmed the
> account API returns 200 for `MA_XXXXXXXXXXXXXXXX` — they just don't grant the
> number-config endpoint.

**Step F — call it!**
Dial `+91 90000 00001` from any phone. You'll hear "Please enter your access PIN".
Type `1234#`. You'll be connected to the destination, which sees your Vobiz number
as the caller ID. 🎉

---

## 12. Testing without real calls

You can prove the whole two-step flow locally:

```bash
# Step 1: Vobiz asks what to do -> we return a Gather
python - <<'PY'
import requests
print(requests.post("http://localhost:8004/answer",
      data={"From":"910000000000","To":"919000000001"}).text)
PY

# Step 2: caller typed a PIN -> Vobiz sends it -> we return a Dial (or reject)
python - <<'PY'
import requests
print(requests.post("http://localhost:8004/collect-pin",
      data={"From":"910000000000","To":"919000000001","Digits":"1234"}).text)  # valid
print(requests.post("http://localhost:8004/collect-pin",
      data={"From":"910000000000","To":"919000000001","Digits":"0000"}).text)  # invalid
PY
```

Automated tests cover: the prompt is a `<Gather>`, a valid PIN bridges, an invalid
PIN is rejected, and the allow-list blocks the wrong caller:

```bash
pytest -q
```

---

## 13. PIN security

A PIN is a key, so treat it like one.

- **Make PINs unique per relationship.** Don't reuse `1234` for many people.
- **Rotate PINs.** Change them regularly, and immediately after a delivery is
  done, so an old PIN can't be reused later. (The PDF calls this "PIN rotation".)
- **Time-bound PINs.** Combine with sessions (Strategy 2's idea) so a PIN only
  works during the delivery window.
- **Use the allow-list for extra safety.** `PIN_ALLOWLIST` lets you say "PIN 1234
  only works if the caller is *this* known number." This is defence-in-depth: even
  if a PIN leaks, only the intended caller can use it.
- **Keep PINs long enough.** 4 digits = 10,000 combinations; for higher security
  use 6 digits and rate-limit wrong attempts.

The trade-off of this strategy (its only real downside) is that callers must
**enter a PIN**, which is one extra step and may need a small change to your app's
UI or to how you instruct customers.

---

## 14. What can go wrong

| Symptom | Cause | Fix |
|---------|-------|-----|
| Caller hears nothing / silence | `<Gather>` `action` is a relative path Vobiz can't resolve | Set `PUBLIC_BASE_URL` so the action is a full HTTPS URL |
| "That PIN is not valid" for a good PIN | PIN not in `PIN_TO_DESTINATION`, or extra characters | Check the table; ensure 4 digits, no `#` in the stored key |
| Prompt repeats / no digits captured | `numDigits`/`finishOnKey` mismatch with how the caller types | Tell callers to press `#` after the PIN; keep `numDigits=4` |
| Allow-list blocks everyone | An allow-list entry exists but the caller isn't on it | Remove the entry or add the caller's number |
| Works locally, not on a real call | Used http not https, or dashboard Answer URL wrong | Use the ngrok HTTPS URL ending in `/answer` |

---

## 15. Pros, cons, and when to choose this

**Pros**
- **Cheapest** — a single DID serves unlimited destinations.
- **Works with the number you already own** — no extra purchases.
- **Caller freedom** — registered or not, anyone with the right PIN gets through;
  optionally tightened with an allow-list.

**Cons**
- **Callers must enter a PIN** — one extra step; may need app/UX changes.
- **PINs need rotation** — operational overhead to keep them fresh and safe.
- **Slightly more complex flow** — two steps (`/answer` then `/collect-pin`)
  instead of one.

**Choose this when:** you want the lowest cost, you only have one number (your
situation today), and a short PIN-entry step is acceptable to your users.

---

## 16. FAQ

**Q: Why does this take two requests (`/answer` and `/collect-pin`)?**
A: Because we pause to ask a question. `/answer` plays the prompt and starts
collecting; `/collect-pin` receives the typed PIN. The other strategies don't ask
anything, so they finish in one request.

**Q: Can the same single number serve both inbound and outbound masking?**
A: Yes. Whoever dials the number gets the PIN prompt and is routed by PIN. You can
give agents one set of PINs and customers another.

**Q: What if two people use the same PIN at the same time?**
A: They both reach the same destination — which is fine if the PIN *is* that
destination. For per-call privacy, combine PINs with sessions (rotate per
delivery).

**Q: Is 4 digits secure enough?**
A: For low-risk routing, yes, especially with rotation and an allow-list. For
higher security, use 6 digits and limit wrong attempts.

**Q: This is the one I can run today, right?**
A: Yes — it needs exactly one number, and you own `+91 90000 00001`. Follow
section 11 for the full live walkthrough.

---

## 17. Glossary

- **PIN:** a short secret code the caller types; it selects the destination.
- **`<Gather>`:** the XML instruction that plays a prompt and collects keypad
  digits, then POSTs them to an `action` URL.
- **DTMF:** the technical name for keypad tones (the beeps when you press digits).
- **`Digits`:** the form field Vobiz sends to your `action` URL containing what
  the caller typed.
- **Two-step flow:** `/answer` (ask for PIN) then `/collect-pin` (route by PIN).
- **Allow-list:** an optional list restricting which caller numbers may use a PIN.
- **PIN rotation:** regularly changing PINs so old ones stop working.
- **MASKING_DID:** the single Vobiz number everyone dials (`919000000001`).
- (All Strategy-1 terms — Answer URL, `<Dial>`, `callerId`, bridge, E.164, ngrok,
  idempotent — still apply; see Strategy 1's glossary.)
