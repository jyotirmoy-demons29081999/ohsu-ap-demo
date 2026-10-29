# OHSU AP Demo — Runbook

**Demo:** Thursday 30 October 2026, with AE Andrew. **Platform:** app.trailhq.com, workspace **OHSU**.

Every case in this demo has **already been run**. On the call you open the finished tasks and walk through them. You send no emails, reply to nothing in Teams, and start no agent.

## What this demo shows

Seven agents run OHSU's Accounts Payable inbox against Oracle E-Business Suite. Every email goes to one agent, **Inbox Triage**, which checks who sent it in Oracle and hands it to the right specialist. The specialists answer suppliers and staff, enter invoices in Oracle, stop fraud and chase receiving holds. They follow OHSU's written rules (the **Trail**, about 1,500 rules) and ask a person in Teams only when the rules don't settle it; that answer then becomes a new rule.

> **The "Oracle" here is a stand-in** (`oracle-mock/`) that looks and answers like Oracle R12. Every Oracle step in a task already shows its Oracle-style screen, so you **don't need it running** to show the tasks. Running it on your laptop (optional, see below) adds the Oracle screen with everything the agents did.

---

## ⭐ The main cases (show these first)

| Order | Case | Why it's the one to show | Time |
| --- | --- | --- | --- |
| 1 | **Case 1** — six invoices, a voided check, a rule learned in Teams | OHSU's first named scenario. The AP supervisor's Teams reply became a rule and retired a 2021 one, on record. The strongest moment | 8 min |
| 2 | **Case 2** — the person who has to act left OHSU | OHSU's second named scenario. Uses Case 1's rule without asking anyone | 5 min |
| 3 | **Cases 5 + 6** — the PO invoice chain | The agenda's invoice part: a clean invoice to payment-ready in Oracle, a GHX duplicate caught, then an exception where only the buyer decides and writes a rule | 8 min |

**Supporting, if time allows:** Case 4 (fraud) — the best three minutes if Tamara or Jim ask about security. Then Cases 3, 7, 8, 9, 10 as quick one-minute looks at the result. **If time runs short,** keep Case 3 (OHSU's third named scenario) as a one-minute look rather than dropping it.

---

## 🔗 Key links

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
| Teams | Team **Demo**: channel **AP Questions** (agents ask) and **AP Desk** (hand-offs) |
| Stand-in Oracle screen (optional) | http://localhost:8770 |
| The documents that came in | `samples/` in this repo |

## 🗂️ The finished tasks

Each email case has two tasks: **Triage** (who sent it, where it goes) and the **specialist** (the work). Open the specialist first; open Triage when someone asks how it got there.

| Case | Triage task | Specialist task |
| --- | --- | --- |
| ⭐ 1 | [Triage](https://app.trailhq.com/agent/0c278ec4-1bc3-4ed4-9772-7182a6019bf7/task/9486685b-e317-4b09-b6ba-4e36a60aee99) | [Supplier Inquiry](https://app.trailhq.com/agent/72cfe467-6100-4361-a8f8-cdd80d86a461/task/160f1c6c-3a40-4edb-86a4-03f471a60105) |
| ⭐ 2 | [Triage](https://app.trailhq.com/agent/0c278ec4-1bc3-4ed4-9772-7182a6019bf7/task/6bea0474-3576-46ea-8c9f-05b25b05f646) | [Supplier Inquiry](https://app.trailhq.com/agent/72cfe467-6100-4361-a8f8-cdd80d86a461/task/12142e26-e076-4953-8176-8190517b9e0e) |
| 3 | [Triage](https://app.trailhq.com/agent/0c278ec4-1bc3-4ed4-9772-7182a6019bf7/task/883574c0-6da5-4cb7-a7c0-2877bbc75295) | [Disputes & Reconciliation](https://app.trailhq.com/agent/f126014d-5026-408b-bd97-9fec2c850a5b/task/60d89da7-745f-418c-afb3-152828f9f4e7) |
| 4 | [Triage](https://app.trailhq.com/agent/0c278ec4-1bc3-4ed4-9772-7182a6019bf7/task/548e69fa-6256-48a5-8510-8ec9b29b2920) | [Supplier Security](https://app.trailhq.com/agent/8f502092-80b7-40c2-a23b-71d81f10d87e/task/5d0f3088-7620-4e7b-a41d-eed36ea64b86) |
| ⭐ 5 | [Triage](https://app.trailhq.com/agent/0c278ec4-1bc3-4ed4-9772-7182a6019bf7/task/236a67d7-5efb-4215-95ea-a37fddd6658a) | [PO Invoice Matching](https://app.trailhq.com/agent/d925a850-7d4c-477c-be2e-ae3d8444704b/task/01f13fea-5307-4669-8899-6a6bd35ba2df) |
| ⭐ 6 | [Triage](https://app.trailhq.com/agent/0c278ec4-1bc3-4ed4-9772-7182a6019bf7/task/9fac4eb1-f516-4f5a-828e-3b0c0024d47b) | [PO Invoice Matching](https://app.trailhq.com/agent/d925a850-7d4c-477c-be2e-ae3d8444704b/task/8e55bd01-baf7-492f-8241-43114a49d259) |
| 7 | [Triage](https://app.trailhq.com/agent/0c278ec4-1bc3-4ed4-9772-7182a6019bf7/task/c274a69c-d87d-44e2-9e0e-21429ff173ee) | [Non-PO & Grants](https://app.trailhq.com/agent/78c5523d-ab2f-4a4b-804b-52f34225416e/task/b714b468-0e31-4f6d-8947-2864719623e3) |
| 8 | [Triage](https://app.trailhq.com/agent/0c278ec4-1bc3-4ed4-9772-7182a6019bf7/task/0ba91614-4e7a-4803-8355-b7c8879a136d) | [Disputes & Reconciliation](https://app.trailhq.com/agent/f126014d-5026-408b-bd97-9fec2c850a5b/task/7387f531-8b53-40da-aea4-59e3df502304) |
| 9 | [Triage](https://app.trailhq.com/agent/0c278ec4-1bc3-4ed4-9772-7182a6019bf7/task/9a24c6da-05ba-4052-a7ba-62b52f4e637a) | [Non-PO & Grants](https://app.trailhq.com/agent/78c5523d-ab2f-4a4b-804b-52f34225416e/task/6df79de0-b757-49b9-b5d7-4205f2d2bf8b) |
| 10 | — (runs on a schedule, no email) | [Hold Follow-up](https://app.trailhq.com/agent/b6e826e2-1fcc-4f81-9546-8d3fa42a5025/task/1342d326-564b-48f8-bfd2-60c60ff4c8a6) |

---

## ✅ Before the call

- [ ] You can open every task link above (logged in to app.trailhq.com, workspace **OHSU**).
- [ ] Browser tabs open: the ⭐ specialist tasks (Cases 1, 2, 5, 6), the Trail, Teams (AP Questions + AP Desk).
- [ ] **Do not press Rerun / Run again** on any task. A rerun replaces the finished result and sends real emails and Teams messages.
- [ ] **Do not run Hold Follow-up**, and leave its 7:00 schedule **off**.
- [ ] Optional: the Oracle screen running on your laptop (next section).

## 🖥️ Optional — the stand-in Oracle screen on your laptop

Shows Oracle with everything the agents did: invoices 55241, 55262 and BHC-4471 created, holds placed, reminders logged. You need Python 3.9 or newer (Macs have it) and nothing else. No ngrok: the agents aren't running, so nothing needs to reach your laptop.

```bash
git clone https://github.com/jyotirmoy-demons29081999/ohsu-ap-demo.git
```

```bash
cd ohsu-ap-demo/oracle-mock
```

```bash
OHSU_DB=demo_state.db python3 server.py
```

Open http://localhost:8770 and leave the terminal open.

> ⚠️ **Never add `--reset`, and never use the screen's "Demo: Reset Data".** Either one wipes the processed data and puts back the untouched starting data. If it happens, close the terminal, run `git checkout demo_state.db`, and start again.

---

# Part 1 — Questions from suppliers and staff (Supplier Inquiry)

## ⭐ Case 1 — Six invoices, a voided check, and a rule learned in Teams

**What came in:** Dana Reyes at Pacific Northwest Surgical Supply (supplier 104882) asks about six invoices, $33,303.50, in one email.

**What to show, in the Supplier Inquiry task**

1. Each invoice looked up in Oracle, each with its Oracle screen.
2. **The Teams question** (channel **AP Questions**): the only rule on file was the 2021 rule 13, "Do not give a supplier a date for an invoice that has not been paid", which doesn't cover holds, credits or replacement payments. So the agent asked.
3. **Lena's reply** in that Teams thread, the new policy, which became a rule. Open the Trail: her rule is **approved**, and rule 13 is **retired** because the new rule won the conflict. History keeps both.
4. **The reply to Dana** — one email, every answer:

| Invoice | What Dana was told |
| --- | --- |
| 55120 | Paid 21 Oct, payment **30418822**. The first check was voided and replaced; the dead check isn't reported as paid |
| 55187 | **Expected** 13 Nov (never "promised") |
| 55203 | On hold: a receipt is missing for the full quantity (billed 20, received 12). **No OHSU staff named** |
| 55219 | Paid 23 Oct, payment **30419544**, **$3,012.50** = $3,615.00 − credit memo **CM-8812** $602.50 |
| R-2207 | Not discussed: it belongs to the sister company (supplier 104883), where Dana isn't a contact |
| 55241 | Not on file — please send a copy in this thread |

No reminder went to anyone at OHSU, because a supplier wrote.

## ⭐ Case 2 — The person who has to act left OHSU

**What came in:** Maria Chen (Radiology) asks why Northwest Imaging invoice 88412, $18,750.00, hasn't been paid.

**What to show**

1. The Rules step quotes **Lena's rule from Case 1** and asks nobody. AP wrote the rule once, and it's already working.
2. The reply to Maria: 88412 is on hold because no receipt was entered, **7 days past due**. The requester **Kevin Walsh left OHSU on 7 Oct**; **Hannah Brooks** now holds the job and must enter the receipt (Receiving > Receipts). Invoice **88507** (Q4, $18,750.00) will need the same step before 7 Nov.
3. The reminder email to Hannah (Maria copied): PO **7765310** line 1, the exact Oracle step, and why it's hers.
4. **AP Desk** in Teams: asks Sam Ortiz (buyer) to move PO 7765310 from Kevin to Hannah. The agent never changes a PO itself.

# Part 2 — Fraud (Supplier Security)

## Case 4 — A lookalike sender asks for new bank details

**What came in:** an "urgent" letter in Dana's name asking to change bank details and list all open invoices. In the story it comes from **pnw-surgical.com**; the real domain is **pnwsurgical.com**. (The task shows the test sender's domain, trailhq.com, as the fake one. That's expected.)

**What to show**

- Triage: sender **unverified** + a bank change letter → Supplier Security.
- A report to security, with the letter attached.
- **AP Desk** alert: real supplier **104882**, real domain **pnwsurgical.com**, callback **+1 503-555-0142**, the number on file and not the one in the email. **Bank details unchanged.**
- **Nothing sent to the sender.**

# Part 3 — PO invoices (PO Invoice Matching)

## ⭐ Case 5 — One PDF, three documents, one already in Oracle

**What came in:** Dana replies in Case 1's thread with `samples/pnw_reply.pdf`: invoice 55241, another invoice, and a statement in one PDF.

**What to show**

1. Split into **3 documents**: 55241, 55244, the statement (filed: a statement isn't an invoice).
2. **55244 is already in Oracle as 0055244**, loaded through GHX → **not created twice**.
3. 55241 against PO **7790415**: **9 of 9 checks passed** → created in Oracle, **$6,480.00**, Validated, no holds.
4. Reply to Dana: 55241 expected 1 Nov; 55244 already on file, expected 16 Nov; statement noted. **No question asked.**

## ⭐ Case 6 — Five cases not delivered, $8 a case too much, the buyer writes a rule

**What came in:** invoice 55262 (`samples/pnw_55262.pdf`) for the rest of the drapes on the same PO.

**What to show**

1. Match **7 of 9**. Failed *quantity received*: 25 billed, only 20 received and not yet billed. Failed *price*: $94.00 against $86.00, so 25 × $8.00 = **$200.00** over, above the **$43.00** limit (the lesser of 2% of $2,150.00 and $50.00).
2. Created **55262, $2,350.00**; Oracle placed **QTY REC** and **PRICE** holds. The agent releases neither.
3. **Teams AP Questions:** only the price went to Sam (buyer): "Did OHSU agree to the new price?" The quantity needs no person, just the receipt when the last five cases arrive.
4. **Sam's reply** became a **draft rule** in the Trail: accept this supplier's sterile drape packs at up to $94.00 a case until 31 March 2027. It stays a draft until AP approves it.
5. Reply to Dana: 55262 entered, expected 20 Nov.

# Part 4 — Quick looks at the finished results

## Case 3 — Short payment, two reasons, one is OHSU's mistake (Disputes & Reconciliation)

Columbia Lab Products says payment 30419507 was **$1,343.40** short. The agent rebuilt it from Oracle: **$103.40** was a discount OHSU took after the window closed (**OHSU's error**), and **$1,240.00** is debit memo DM-71033 for 4 cases of pipette tips returned 29 Sep (receipt 5531155, **supported**). It decided nothing: an acknowledgment with reference **AP-30419507-20261029**, a full draft reply waiting in the AP mailbox, and an **AP Desk** hand-off to **Priya Nair**. Nothing changed in Oracle.

## Case 7 — NIH symposium lunch with $540 of wine (Non-PO & Grants)

Sofia Alvarez (Neurology) asks to charge Blue Heron Catering's **$3,486.00** invoice to NIH award R01 NS112233. Lunch $2,310 + coffee $366 + staff $270 = **$2,946.00 stays on the award**. **$540.00 of wine moves to cost center 4130** (Neurology discretionary): alcohol is never charged to a federal award. BHC-4471 created in Oracle, approval routed to **Daniel Osei** (Operations Director, Neurology), Sofia told what moved and why.

> The task shows earlier attempts (the tunnel to the stand-in Oracle dropped). **Scroll to the last pass**, which starts with "Extracted data for payee Blue Heron Catering…" and ends with "Processed non-PO invoice BHC-4471…".

## Case 8 — A statement with eight lines, three really open (Disputes & Reconciliation)

Summit Biomedical's statement claims **$60,630.00** under "customer 0005521"; the agent reconciled it under supplier **109377**. Reply: **$15,735.00 owed now; $6,305.00 needs a copy.** Paid $26,790 + credited $1,920 + listed twice $9,880 + open $15,735 + not on file $6,305 = $60,630. Every line explained; a copy of **SB-880433** requested in the thread. Nothing on the statement was entered as an invoice.

## Case 9 — Honorarium for a visiting professor from Canada (Non-PO & Grants)

Nadia Rahman (Psychiatry) asks to pay Dr. Émilie Gagnon (Université de Montréal): **$2,500.00** honorarium + **$612.40** travel. She is a foreign individual with no supplier record, so **Tax & Compliance goes first**. Coded to Psychiatry **4280** (544110 honorarium, 544100 travel). **Nothing entered in Oracle.** **AP Desk** hand-off to **Grace Liu** (missing supplier record, W-8BEN, visa type and entry date, chair approval; withholding and treaty are hers); Nadia emailed the same list.

> One step in this task, the Oracle lookup of Dr. Gagnon, shows "Oracle could not be reached" (the tunnel dropped). The agent still reached the right decision from the rules. If asked: the agent never answers from guesses when Oracle doesn't answer.

## Case 10 — The morning sweep: eleven holds, four reminders, two left alone (Hold Follow-up)

Runs every morning at 7:00, no email. On 29 Oct it found **11 receiving holds older than 5 business days, $58,917.50**, and sent **4 emails covering 9 invoices, $21,417.50** — one email per person, not one per invoice:

| Who | Invoices | Total |
| --- | --- | --- |
| Central Receiving | 55203, CCD-20931 | $4,124.00 |
| Chris Dalton, Emergency Department | CCD-20977 | $2,618.50 |
| Ana Morales, Cardiology (Dr. Paul Nguyen copied: one hold is over 30 days old) | NBR-5512, NBR-5540, NBR-5561 | $4,640.00 |
| Ben Carter, Facilities Management | IHS-3307, IHS-3321, IHS-3345 | $10,035.00 |

**Left alone on purpose:** **88412** (Hannah was reminded in Case 2) and **88507** (its service period runs to January). $21,417.50 + $37,500.00 = $58,917.50. Each reminder is logged in Oracle; nothing else changed.

---

## Closing — the Trail

Open Trail **OHSU Accounts Payable** (link above):

1. About 1,500 rules, in eleven areas, that AP owns.
2. **Lena's rule** (Case 1): approved, and the 2021 rule 13 it replaced, retired, with who decided.
3. **Sam's rule** (Case 6): a draft waiting for AP's approval.
4. Any task's record: what came in, which rules each agent read, what it sent.

## ⚠️ If something looks wrong

| If you see… | It means / do this |
| --- | --- |
| "Oracle could not be reached" in a step | The tunnel to the stand-in Oracle dropped during the pre-run. The agent stopped rather than guess. Expected in Case 9's lookup step and Case 7's earlier attempts |
| A task shows several attempts | It was rerun after a dropped connection. Show the last pass |
| Staff emails go to `jyotirmoy+name@trailhq.com` | Stand-in addresses, so no email reached a real OHSU person |
| A Teams @mention isn't highlighted | The stand-in staff aren't Teams users. The message still posted |
| A Case 4 alert names trailhq.com as the fake domain | The test email came from trailhq.com; in the story it's pnw-surgical.com |
| Oracle screen at localhost is empty or looks "new" | It was reset. Close it, `git checkout demo_state.db`, start again without `--reset` |

---

## Appendix — running the cases again from scratch (not needed for Thursday)

Only for a full rebuild by JP. It needs the agents reaching the stand-in Oracle through ngrok, a persona switch before each case, and the Trail reset for Case 1. The steps, email texts and expected results are in this repo's git history (commit `9ecbaf9`, "the live-run runbook").
