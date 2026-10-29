# OHSU AP Demo — Runbook

How to run the OHSU Accounts Payable demo from your own computer: set up the stand-in Oracle, run the main cases, and know which agent does what.

## What this demo shows

Seven agents run OHSU's Accounts Payable inbox against Oracle E-Business Suite. Every email goes to one agent, **Inbox Triage**, which checks who sent it in Oracle and hands it to the right specialist. The specialists answer suppliers and staff, enter invoices in Oracle, stop fraud and chase receiving holds. They follow OHSU's written rules (the **Trail**, about 1,500 rules) and ask a person in Teams only when the rules don't settle it; that answer then becomes a new rule.

- **Main cases, run live:** 1, 2, 4, 5, 6, then 10.
- **Already run and shown as finished tasks:** 3, 7, 8, 9.

> **The "Oracle" here is a stand-in** (`oracle-mock/`): a small program on your computer that looks and answers like Oracle R12. The agents reach it over the internet through **ngrok**. If your laptop sleeps or loses internet, the agents stop. Keep it plugged in and awake.

---

## 🔗 Key links & assets

| What | Where |
| --- | --- |
| AP Inbox Triage (every email starts here) | https://app.trailhq.com/agent/0c278ec4-1bc3-4ed4-9772-7182a6019bf7 |
| Supplier Inquiry | https://app.trailhq.com/agent/72cfe467-6100-4361-a8f8-cdd80d86a461 |
| Disputes & Reconciliation | https://app.trailhq.com/agent/f126014d-5026-408b-bd97-9fec2c850a5b |
| Supplier Security | https://app.trailhq.com/agent/8f502092-80b7-40c2-a23b-71d81f10d87e |
| PO Invoice Matching | https://app.trailhq.com/agent/d925a850-7d4c-477c-be2e-ae3d8444704b |
| Non-PO & Grants | https://app.trailhq.com/agent/78c5523d-ab2f-4a4b-804b-52f34225416e |
| Hold Follow-up | https://app.trailhq.com/agent/b6e826e2-1fcc-4f81-9546-8d3fa42a5025 |
| Trail "OHSU Accounts Payable" | https://app.trailhq.com/brain/dcd9ca5f-66b9-493f-900c-ede0d07e363b |
| Send every test email to | `ohsu-ap-inbox-triage-agent@inbound.agents.nanonets.com` |
| Send test emails from | **[YOUR EMAIL]** — the address you set as `OHSU_ME` below |
| Agents send email from | `jyotirmoy.nanonets@outlook.com` |
| Teams | Team **Demo**: channel **AP Questions** (agents ask) and **AP Desk** (hand-offs) |
| Stand-in Oracle screen (show this) | http://localhost:8770 |
| Stand-in Oracle public address (agents use it) | https://compost-traffic-uproot.ngrok-free.dev |
| Attachments | `samples/` in this repo |

---

## ✅ One-time setup on your computer (Mac)

You need: access to workspace **OHSU** on app.trailhq.com, membership of the Teams team **Demo**, and the **ngrok authtoken from JP** (he sends it privately; it is never stored in this repo).

### 1. Get the files

```bash
git clone https://github.com/jyotirmoy-demons29081999/ohsu-ap-demo.git
```

```bash
cd ohsu-ap-demo/oracle-mock
```

### 2. Check Python (3.9 or newer; nothing else to install)

```bash
python3 --version
```

### 3. Install ngrok and add the authtoken

```bash
brew install ngrok
```

```bash
ngrok config add-authtoken [NGROK AUTHTOKEN FROM JP]
```

### 4. Start the stand-in Oracle (Terminal 1 — leave it open)

The first start loads the demo data. `OHSU_DEMO_DATE` lines the invented dates up with the demo day.

```bash
OHSU_DEMO_DATE=2026-10-30 python3 server.py --reset
```

### 5. Open it to the internet (Terminal 2 — leave it open)

> ⚠️ **Only one computer can use this address at a time.** Ask JP to stop his ngrok first, or this command fails with "already online".

```bash
ngrok http --url=compost-traffic-uproot.ngrok-free.dev 8770
```

### 6. Check it works

- [ ] https://compost-traffic-uproot.ngrok-free.dev/api/health shows `"ok": true`
- [ ] http://localhost:8770 shows the Oracle screen

### 7. Tell the stand-in Oracle who you are (Terminal 3)

The agents check every sender against Oracle. This script makes **your** address the sender for the case you're about to run, and turns every OHSU staff address into a `+alias` of yours, so no email reaches a real OHSU person.

```bash
cd ohsu-ap-demo/oracle-mock
export OHSU_ME=[YOUR EMAIL]
python3 persona.py case1
```

- [ ] It prints `[YOUR EMAIL] is now: PACIFIC NORTHWEST SURGICAL SUPPLY (supplier 104882)` and **`Staff addresses at ohsu.edu: 0`**.

> In every new terminal, run `export OHSU_ME=[YOUR EMAIL]` again before `persona.py`. Staff emails from the agents (reminders, Case 2) will arrive at `[YOUR EMAIL]` with `+name` added, e.g. `you+hbrooks@…`.

---

## ✅ Before each demo

- [ ] Terminals 1 and 2 running; the health link shows `"ok": true`.
- [ ] **Fresh data** (only before a full run-through, never mid-demo):

```bash
curl -s -X POST http://127.0.0.1:8770/api/admin/reset
```

- [ ] **Right after any reset**, run `python3 persona.py case1`. A reset brings back the real-looking `@ohsu.edu` addresses until persona.py runs again.
- [ ] **Trail ready for Case 1** (in the app, Trail "OHSU Accounts Payable"): the rule *"For paid invoices, provide the payment date and payment number to suppliers…"* is **retired**, and rule 13 *"Do not give a supplier a date for an invoice that has not been paid."* is **approved**. Otherwise Case 1 won't ask in Teams.
- [ ] The Hold Follow-up schedule is **off** (it must not run before the demo).
- [ ] Browser tabs open: Inbox Triage, Supplier Inquiry, PO Invoice Matching, Hold Follow-up, the Trail, Teams (AP Questions + AP Desk), your inbox, http://localhost:8770.

**Before each case, run its persona line**, and wait until the previous case's specialist task has moved past its first step:

| Case | Persona command |
| --- | --- |
| 1 | `python3 persona.py case1` |
| 2 | `python3 persona.py case2` |
| 4 | `python3 persona.py case4` |
| 5 and 6 | `python3 persona.py case5` |
| 10 | none |

---

# Part 1 — Questions from suppliers and staff (Inbox Triage → Supplier Inquiry)

## Case 1 — Six invoices, a voided check, and a rule learned live

The agent answers five of six invoices, refuses the sister company's, asks the AP supervisor in Teams because the 2021 rule doesn't cover holds or credits, and her answer becomes a new rule.

> **Precondition:** Trail ready (see checklist). Persona `case1`.

**Send** from [YOUR EMAIL] to `ohsu-ap-inbox-triage-agent@inbound.agents.nanonets.com`, no attachment.

Subject: `Open invoices — Pacific Northwest Surgical Supply / OHSU-00417`

```
Hello OHSU Accounts Payable,

I'm closing our books for October and have six invoices showing open for OHSU. Could you tell us the status of each and when we can expect payment?

- 55120 — $4,812.50
- 55187 — $12,306.00
- 55203 — $2,940.00
- 55219 — $3,615.00
- R-2207 — $3,150.00 (this one is from our rentals division)
- 55241 — $6,480.00

Total $33,303.50. Thank you!

Dana Reyes
Accounts Receivable, Pacific Northwest Surgical Supply
(503) 555-0142
```

**During the run**

1. Triage verifies the sender and hands over to Supplier Inquiry (about a minute).
2. Supplier Inquiry looks up all six in Oracle; each Oracle step shows an Oracle-style screen.
3. A question appears in Teams **AP Questions**, quoting rule 13. **Reply in its thread, as Lena (AP supervisor):**

```
That 2021 rule is gone. Suppliers get the payment date and payment number for paid invoices, and the credit memo number when we paid short. For approved unpaid invoices give the due date and call it expected, never promised. For held invoices say what is missing, but never name OHSU staff. OHSU employees get the full picture, including who has to act, and you can email that person a reminder.
```

4. The reply becomes a **draft rule** in the Trail. **Approve it**; when the Trail flags the clash with rule 13, choose **the new rule wins**.

**Expect** one reply to [YOUR EMAIL]:

- 55120 paid 14 Oct, ACH **30418822** (the voided check is not reported as paid)
- 55219 paid 16 Oct, ACH **30419544**, **$3,012.50** = $3,615.00 − credit memo **CM-8812** $602.50
- 55187 **expected** 6 Nov
- 55203 on hold until OHSU confirms receipt — **no staff names**
- 55241 not on file — please send a copy in this thread
- R-2207 can't be discussed from this address (it belongs to sister supplier 104883)
- **No reminder to anyone at OHSU** (a supplier wrote)

> **After the case:** the new rule must be **approved** before Case 2.

## Case 2 — The person who has to act left OHSU

A staff member gets the full story with nobody asked; the reminder goes to whoever holds the job now, and the buyer is asked to fix the PO.

> **Precondition:** Case 1's rule approved. Persona `case2` (you are Maria Chen, Radiology).

**Send**, no attachment. Subject: `Why hasn't Northwest Imaging invoice 88412 been paid?`

```
Hi AP,

Northwest Imaging Services called this morning about invoice 88412 for $18,750.00, our CT scanner service contract for July to September. They say it's past due and they may pause service on our scanners. Can you tell me why it hasn't been paid and what we need to do on our side?

Thanks,
Maria Chen
Department Administrator, Radiology
```

**During the run:** nothing to do. The Rules step quotes the Case 1 rule and **asks nobody**.

**Expect**

- Reply to you: 88412 on a **QTY REC hold** (receipt never entered), days past due; requester **Kevin Walsh left OHSU on 7 Oct**; **Hannah Brooks** (Operations Manager, acting) must enter the receipt; **88507** (Q4, $18,750.00) will need the same step but isn't late; reminder sent, buyer asked.
- Reminder to `you+hbrooks@…`, you copied: PO **7765310** line 1, $18,750.00, the Oracle step (Receiving > Receipts).
- **AP Desk** in Teams: asks Sam Ortiz to move PO 7765310 from Kevin to Hannah (invoices 88412 and 88507).

---

# Part 2 — Fraud (Inbox Triage → Supplier Security)

## Case 4 — A lookalike sender asks for new bank details

Nothing is told to the sender; security and AP are alerted with the real supplier's phone number on file.

> **Precondition:** persona `case4` (your address becomes an **unknown** sender). In the story the email comes from dana.reyes@**pnw-surgical.com**; from your address the alert names your domain as the fake one — expected.

**Send** with **`samples/bank_change_letter.pdf`** attached. Subject: `URGENT — updated remittance details for Pacific Northwest Surgical Supply`

```
Hello,

Please see the attached letter. We are moving our receivables to a new bank, and our old account closes this Friday. Could you update our vendor record before your next payment run and send us a list of all open invoices with their payment dates, so we can reconcile?

If you need to confirm, please call our treasury desk at (971) 555-0199.

Thank you,
Dana Reyes
Accounts Receivable & Treasury
Pacific Northwest Surgical Supply
```

**Expect**

- Triage: sender **unverified** + a **bank change letter** → Supplier Security.
- A report email to the security address, with the letter attached.
- **AP Desk** alert to AP and Supplier Maintenance: real supplier **104882**, real domain **pnwsurgical.com**, callback **+1 503-555-0142** (the number on file, not the one in the email), **bank details unchanged**.
- **Nothing sent to the sender.**

---

# Part 3 — PO invoices (Inbox Triage → PO Invoice Matching)

## Case 5 — One PDF, three documents, one already in Oracle

The file is split, the copy that came through GHX isn't entered twice, and the new invoice posts clean.

> **Precondition:** Case 1 has run. Persona `case5` (you are Dana again).

**Send** with **`samples/pnw_reply.pdf`** attached. Subject: `RE: Open invoices — Pacific Northwest Surgical Supply / OHSU-00417`

```
Thanks for the quick answer. Here is 55241 as requested. Our system also attached our other open invoice and a statement — hope that helps.

Dana
```

**Expect**

- Split into **3 documents**: 55241, 55244, statement.
- **55244 = 0055244**, already in Oracle from GHX → **not created**.
- 55241 against PO **7790415**: **9 of 9 checks passed** → created **$6,480.00**, Validated, no holds, due 1 Nov.
- Reply to you: 55241 created, expected 1 Nov; 55244 already on file, expected 16 Nov; statement noted. **No question asked.**

## Case 6 — Five cases not delivered, $8 a case too much, the buyer writes a rule

The invoice is entered with Oracle's own holds, only the price goes to the buyer, and his answer becomes a draft rule.

> **Precondition:** Case 5 done. Persona stays `case5` (same supplier).

**Send** with **`samples/pnw_55262.pdf`** attached. Subject: `Invoice 55262 — PO 7790415`

```
Hello,

Attached is invoice 55262 for the balance of the sterile drape packs on PO 7790415. Please note our price list changed on October 1.

Dana Reyes
Accounts Receivable, Pacific Northwest Surgical Supply
```

**During the run:** Teams **AP Questions** asks **"Did OHSU agree to the new price?"** **Reply in its thread, as Sam (buyer):**

```
Yes. Their price list went up on 1 October and I agreed it. I'll change the PO line to $94.00 today. Until 31 March 2027, accept their sterile drape packs at up to $94.00 a case without asking me.
```

**Expect**

- Match **7 of 9**: failed *quantity received* (25 billed, 20 received and not yet billed) and *price* ($94.00 vs $86.00: 25 × $8.00 = **$200.00** over; limit **$43.00** = lesser of 2% of $2,150.00 and $50.00).
- Created **55262, $2,350.00** with **QTY REC** and **PRICE** holds. The agent releases neither.
- After Sam's reply: a **draft** rule in the Trail, *"Until 31 March 2027, accept sterile drape packs from PACIFIC NORTHWEST SURGICAL SUPPLY at up to $94.00 per case…"*. **Leave it as a draft.**
- Reply to you: 55262 received and entered.

---

# Part 4 — The morning sweep (Hold Follow-up)

## Case 10 — Twelve receiving holds, four reminders, two left alone

> **Precondition:** Case 2 ran today (that's why 88412 is left alone). No email starts this case.

**Run:** open **Hold Follow-up** → **Run**, with the prompt:

```
Run the morning receiving-hold sweep.
```

**Expect** (on 30 Oct)

- **12 holds, $59,557.50**, older than 5 business days.
- **4 emails covering 10 invoices, $22,057.50:**

| Who | Invoices | Total |
| --- | --- | --- |
| Central Receiving | 55203, CCD-20931 | $4,124.00 |
| Chris Dalton, Emergency Department | CCD-20977 | $2,618.50 |
| Ana Morales, Cardiology (Dr. Paul Nguyen copied) | NBR-5512, NBR-5540, NBR-5561 | $4,640.00 |
| Ben Carter, Facilities Management | IHS-3307, IHS-3321, IHS-3345, IHS-3360 | $10,675.00 |

- **Left alone:** 88412 (Hannah reminded in Case 2) and 88507 (service period runs to January).
- $22,057.50 + $37,500.00 = $59,557.50. Nothing changes in Oracle.

---

# Part 5 — Finished cases to show (already run)

Open each agent's task list and walk through the completed task. You don't send anything.

| Case | Agent | What to point at |
| --- | --- | --- |
| 3 — Columbia Lab short payment | Disputes & Reconciliation | $1,343.40 gap = $103.40 discount taken 22 days late (OHSU's error) + $1,240.00 return credit (supported). Acknowledgment only; draft reply for Priya Nair; nothing changed in Oracle |
| 7 — NIH symposium lunch | Non-PO & Grants | $2,946.00 stays on award R01 NS112233; $540.00 of wine moved to cost center 4130; approval routed to Daniel Osei |
| 8 — Summit statement | Disputes & Reconciliation | $60,630.00 claimed, **$15,735.00** owed now, $6,305.00 needs a copy; every line explained |
| 9 — Visiting professor honorarium | Non-PO & Grants | Foreign individual, no supplier record → Tax & Compliance (Grace Liu) first; nothing entered in Oracle; the department told exactly what's missing |

---

## ⚠️ Known gotchas

| If you see… | It means / do this |
| --- | --- |
| A step says "Oracle could not be reached" | ngrok or your laptop dropped. Check the health link, then rerun the task from the start |
| ngrok says the address is "already online" | JP's ngrok is still running. Ask him to stop it |
| Sender checks look wrong | Persona not switched, or `OHSU_ME` not set in that terminal: run `python3 persona.py show` |
| Case 1 answers without asking Lena | The Trail isn't ready: the Case 1 rule is still approved, or rule 13 still retired |
| Case 2 asks AP in Teams | The Case 1 rule isn't approved yet. Approve it, then send Case 2 again |
| Case 5 or 6 says "already in Oracle" | That case already ran on this data. Reset (see "Before each demo"), then run persona.py again |
| Case 10 shows fewer than 12 holds | Not 30 Oct, or a reminder from an earlier run is under 2 business days old |
| A reply arrives as a new email, not in your thread | Known limit: replies come from the Outlook mailbox. The "RE:" subject keeps them together |
| A Teams @mention isn't highlighted | The stand-in staff aren't Teams users. The message still posts |

## Placeholders to fill

- **[YOUR EMAIL]** — the address you send test emails from (set as `OHSU_ME`).
- **[NGROK AUTHTOKEN FROM JP]** — sent privately by JP; never commit it.
