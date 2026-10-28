# Oracle EBS R12 mock — OHSU demo

> **Running the demo? Follow the runbook in the repo's main [README](../README.md).** It supersedes the start-up, demo-date and email-address notes below (use `OHSU_DEMO_DATE=2026-10-30` and `persona.py`, never edit `seed.json`). The rest of this file describes how the stand-in Oracle works.

A stand-in for OHSU's Oracle E-Business Suite R12 (Payables + Purchasing). The agents call its API;
the browser screen copies the R12.2 Forms layout from real screenshots (State of Rhode Island's Oracle 12.2
AP training guide): Navigator, Invoice Workbench with its six tabs, Invoice Actions, Match to Purchase Orders,
Distributions, Invoice Overview, Payments, Purchase Orders, Receipts and Receiving Transactions Summary.
A small footer says it is a demo stand-in, not an Oracle product.

**Standard library only — nothing to install.** Every supplier, person and number is invented (see `seed.json`).

## Start it

Two terminal windows, left open for the whole session.

```bash
python3 /Users/jyotirmoypathak/nanonets/assign/demo/oregon-health-and-science-university/oracle-mock/server.py
```

```bash
ngrok http --url=compost-traffic-uproot.ngrok-free.dev 8770
```

This is a different ngrok address from the RentWorks mock, so both can run at once.

**Check it is reachable:** open https://compost-traffic-uproot.ngrok-free.dev/api/health. It should say `"ok": true`.

**Show the screen from `http://localhost:8770`**, not the ngrok address. The agents use the ngrok address.
The screen re-queries every 4 seconds, so an invoice the agent creates appears by itself and flashes green.

## Before every rehearsal and before the call

| | Do this |
| --- | --- |
| Reset | File menu → **Reset demo data**, or `python3 server.py --reset`. Removes 55241 and 55262, puts PO 7790415 back to $86.00, removes any receipt Kevin entered |
| Set the demo date | `OHSU_DEMO_DATE=2026-11-04 python3 server.py --reset`. Every seeded date moves so the demo day reads like 23 October 2026 in the storyline: 88412 is 8 days late, 55187 is due in 14 days |
| Use real email addresses | The live cases are checked against the contact emails in `seed.json`. Change `dreyes@pnwsurgical.com` (Cases 1, 4, 5) and `mchen@ohsu.edu` (Case 2) to addresses you can send from, then reset |

## What the seed gives each case (storyline v4: ten cases, seven agents)

| Case | In Oracle at the start |
| --- | --- |
| 1 | Supplier 104882: 55120 paid by ACH 30418822 on 14 Oct after check 118144 was **voided** (returned undeliverable); 55187 validated, due 6 Nov; 55203 on QTY REC hold (20 billed, 12 received); 55219 paid by ACH 30419544 **net of credit memo CM-8812** ($3,615.00 − $602.50 = $3,012.50). **55241 does not exist.** R-2207 ($3,150.00) belongs to sister supplier **104883** (contact billing@pnwsurgicalrentals.com only) |
| 2 | 88412 ($18,750.00, Q3) and 88507 ($18,750.00, Q4) on PO 7765310, both on QTY REC hold. Requester Kevin Walsh is **Inactive since 30 Sep**; Hannah Brooks holds the same role from 1 Oct, so holds name her as who must act |
| 3 | Columbia terms **2% 10, Net 30**. Payment 30419507, $8,306.60 = 71019 $5,066.60 (**$103.40 discount taken 22 days after the window closed on 24 Sep**) + 71033 $4,480.00 − debit memo DM-71033 $1,240.00 (return on receipt 5531155) |
| 4 | Nothing: pnw-surgical.com matches no supplier, domain or employee, so the lookup says `unknown` |
| 5 | **0055244** ($2,214.00, 36 bx skin markers) already loaded from **GHX** on 10 Oct; the duplicate check finds it for "55244". PO 7790415: 65 drape packs ordered, 60 received, nothing billed |
| 6 | After Case 5: PO 7790415 line 1 has 20 received-and-unbilled. Billing 25 at $94.00 places **QTY REC and PRICE** holds; Central Receiving's receipt of 5 clears one, Sam's PO price change the other |
| 7 | Supplier 112410 Blue Heron Catering (Net 15) and NIH award **R01 NS112233** (`GET /api/awards/R01%20NS112233`, federal). No invoice yet: the Non-PO & Grants agent creates BHC-4471 with split `distribution`s and `approver_email: dosei@ohsu.edu`, which starts the approval. Daniel approves it in **Worklist** |
| 8 | Summit Biomedical 109377: SB-880214 and SB-880402 paid; SB-880415 fully credited by SB-CM-0912; SB-880377 validated, due 16 Nov; **SB-880451 waiting for approval (leave it unapproved)**; SB-880460 arrived by GHX "this morning", Never Validated; SB-880433 not in Oracle |
| 9 | Nothing: there is no supplier record for Dr. Gagnon. That absence is the case |
| 10 | `GET /api/holds?older_than_business_days=5` returns **12 holds, $59,557.50**, each with who must act, the director for holds over 30 days (NBR-5512, 34 days), and `service_period_ended` (false for 88507). The reminder log lives on the platform, not here |


**Run order before the call.** Case 10 says it runs the morning after Case 2. Pre-run Case 2 in rehearsal so its reminder to Hannah is in the Hold Follow-up agent's log, then pre-run Case 10, then reset Oracle for the live cases. The log is on the platform, so the reset doesn't clear it.

The sender check can answer per invoice: `GET /api/directory/lookup?email=...&invoice_num=R-2207` returns
`authorized_for_invoice: false` without saying anything about the invoice.

## Where things are on screen

| To show | Responsibility (File > Switch Responsibility) | Navigator path |
| --- | --- | --- |
| Invoices, holds, lines, payments of an invoice | OHSU Payables Manager | Invoices Entry > Invoices |
| One invoice's status, holds and payments on one page | OHSU Payables Manager | Workbench, then Tools > View Invoice Overview |
| A payment and the invoices and debit memo inside it (Case 3) | OHSU Payables Manager | Payments Inquiry > Payments |
| What the invoice matched on the PO | OHSU Payables Manager | Workbench, **Match** button |
| **Hannah enters the receipt (Case 2, after the demo's reply)** | OHSU Purchasing Super User | Receiving > Receipts. Find PO 7765310, tick line 1, File > Save. Received By defaults to Hannah, because Kevin is inactive |
| **Central Receiving enters the last 5 drape packs (Case 6)** | OHSU Purchasing Super User | Receiving > Receipts. Find PO 7790415, tick line 1, quantity 5, File > Save |
| **Daniel approves BHC-4471 (Case 7)** | OHSU Payables Manager | Worklist > Approve |
| **Sam changes the PO price (Case 6)** | OHSU Purchasing Super User | Purchase Orders > Purchase Orders. View > Find, PO 7790415, change line 1 price to 94.00, File > Save |

Saving a receipt or a PO price change revalidates every open invoice on that PO, so the hold releases by itself,
as Oracle does (Release Name "Matched" or "Variance Corrected", Released By "System").
The Invoice Workbench requeries every 4 seconds: an invoice the agent creates appears on top and flashes green,
and the status bar reads "Invoice … received from Payables Open Interface".
File > **Demo: Activity Log** lists every create, hold, release, receipt and PO change. It is not an Oracle screen.

## How it behaves like Oracle

- **Creating an invoice** runs the three-way match: each line is checked against the PO line (ordered, price)
  and the receipts (received, net of returns). Holds: `QTY REC`, `QTY ORD`, `PRICE`, `DIST VARIANCE`.
  No holds → `Validated`, ready to pay. Approval reads `Not Required` for PO-matched invoices (the PO was approved), `Workflow Approved` for the rest.
- **Price tolerance** is 2%, matching the Trail rule (`OHSU_PRICE_TOLERANCE_PCT` changes it). Case 5 is 9.30% over, so it is held.
- **The same invoice number for the same supplier is refused (409).** The duplicate-check endpoint also
  finds the number in other forms: `055241`, `55241-A`, `55241R`.
- **Expected payment date** is the due date. If the invoice is already past due, it is the next weekly
  payment run (Thursday; `OHSU_PAYMENT_RUN_WEEKDAY`, 0 = Monday).
- **Who must act** on each hold: `QTY REC` → the PO requester; `PRICE` and `QTY ORD` → the buyer.
- Every create, hold, release, receipt and PO change is written to the activity log with who did it.

## The API — what the agents' configured tools call

Optional auth: start with `OHSU_API_KEY=...` and the agents must send header `X-API-Key`. Send `X-Actor`
(or `"actor"` in the body) to name who did a write. It defaults to `NANONETS_AGENT`.

| Agent tool (storyline name) | Method | Path | Returns |
| --- | --- | --- | --- |
| `oracle_supplier_lookup` / `oracle_employee_lookup` | GET | `/api/directory/lookup?email=` | `match`: `supplier_contact`, `supplier_domain`, `employee`, `ohsu_domain_not_in_hr` or `unknown`; `verified`; the supplier or employee record |
| | GET | `/api/suppliers/{number}` · `/api/suppliers?q=` · `/api/employees?email=` | Supplier with contacts and open POs; employee |
| `oracle_invoice_status` | GET | `/api/invoices/{invoice_num}?supplier_number=` | Full invoice: lines, holds (with `who_must_act` and `next_step`), payments, `status_summary` (`paid` / `approved_unpaid` / `on_hold`), `payment_date` + `payment_date_type` (`confirmed` / `expected` / `none`), `days_past_due`. **404** if Oracle has never seen it |
| | GET | `/api/invoices?supplier_number=&amount=&po_number=&on_hold=true` | Search, e.g. a missing invoice by amount |
| | GET | `/api/invoices/duplicate-check?supplier_number=&invoice_num=` | `is_duplicate`, `matches` with the reason, `variants_checked` |
| | GET | `/api/payments/{number}` · `/api/payments?supplier_number=&date_from=` | Payment with every invoice and debit memo applied |
| `oracle_po_receipt_lookup` | GET | `/api/purchase-orders/{po}` | Lines with ordered / received / billed / left to bill, receipts, matched invoices, requester and buyer |
| `oracle_create_invoice` | POST | `/api/invoices` | Body below. **201** with the validated invoice and any holds; **409** duplicate; **422** unknown supplier, PO or PO line |
| (staff, from the screen) | POST | `/api/receipts` | `{po_number, lines: [{line_num, quantity}], received_by}` (or one `line_num` + `quantity`) → revalidates the PO's invoices |
| (staff, from the screen) | PATCH | `/api/purchase-orders/{po}/lines/{n}` | `{unit_price, actor}` → revalidates |
| `oracle_hold_list` (Hold Follow-up) | GET | `/api/holds?older_than_business_days=5` | Every receiving hold: age in days and business days, who must act, director, `service_period_ended` |
| (Non-PO & Grants) | GET | `/api/awards/{award_number}` | Sponsor, federal or not, project, task, period |
| (approver, from the screen) | POST | `/api/invoices/{invoice_id}/approve` | Worklist approval of a non-PO invoice: Initiated → Workflow Approved |
| | GET | `/api/worklist` | Invoices waiting for approval |
| | POST | `/api/admin/reset` | Reloads `seed.json` |
| | GET | `/api/events` | The activity log |

`POST /api/invoices` body:

```json
{
  "supplier_number": "104882",
  "invoice_num": "55241",
  "invoice_date": "2026-10-02",
  "invoice_amount": 6480.00,
  "po_number": "7790415",
  "source": "EMAIL",
  "description": "OR drapes, gowns, sutures",
  "attachment_url": "https://...pdf",
  "lines": [
    {"po_line_num": 1, "description": "Sterile drape packs", "quantity": 40, "unit_price": 86.00},
    {"po_line_num": 2, "description": "Surgical gowns, large", "quantity": 25, "unit_price": 72.00},
    {"po_line_num": 3, "description": "Suture kits", "quantity": 20, "unit_price": 62.00}
  ]
}
```

A non-PO invoice adds `approver_email` (starts the approval in Oracle workflow) and a `distribution` per line, for example
`"Award R01 NS112233 / Project 1027734 / Task 1.1 / 523120 Catering"` or `"Cost center 4130 Neurology / Discretionary"`.

Data lives in `oracle.db` next to `server.py`. Deleting it is the same as Reset.
