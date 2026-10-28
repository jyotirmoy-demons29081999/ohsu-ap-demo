"""Oracle E-Business Suite R12 mock for the OHSU demo.

A stand-in for OHSU's Oracle EBS R12 Payables and Purchasing: a JSON API the agents call, and a browser
screen styled on the R12 Forms (Invoice Workbench, Purchase Orders, Receipts, Payments, Suppliers).
Standard library only - nothing to install.

Run:     python3 server.py                          # http://localhost:8770
         python3 server.py --reset                  # wipe and reload seed.json first
Dates:   OHSU_DEMO_DATE=2026-11-04 python3 server.py --reset
         shifts every seeded date so the demo day reads like 23 October 2026 does in the storyline
Tunnel:  ngrok http --url=<your-static-domain> 8770
"""
import datetime as dt
import json, os, re, sqlite3, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("OHSU_PORT", "8770"))
DB = os.environ.get("OHSU_DB", os.path.join(HERE, "oracle.db"))
SEED = os.environ.get("OHSU_SEED", os.path.join(HERE, "seed.json"))
API_KEY = os.environ.get("OHSU_API_KEY", "")            # if set, /api/* needs header X-API-Key (the UI is exempt)
PRICE_TOLERANCE_PCT = float(os.environ.get("OHSU_PRICE_TOLERANCE_PCT", "2"))   # matches the Trail rule (2%)
PAYMENT_RUN_WEEKDAY = int(os.environ.get("OHSU_PAYMENT_RUN_WEEKDAY", "3"))   # 0=Mon .. 3=Thu: the weekly payment run
LOCK = threading.Lock()

HOLD_INFO = {
    "QTY REC": ("Quantity billed exceeds quantity received", "requester",
                "Enter the receipt in Oracle Purchasing (Receiving > Receipts) for the quantity actually delivered."),
    "QTY ORD": ("Quantity billed exceeds quantity ordered", "buyer",
                "Confirm the extra quantity and change the PO, or ask the supplier for a corrected invoice."),
    "PRICE": ("Invoice price exceeds purchase order price", "buyer",
              "Confirm the price. Change the PO line price, or ask the supplier for a corrected invoice."),
    "DIST VARIANCE": ("Invoice amount does not equal the sum of its lines", "ap",
                      "AP to correct the invoice lines or the invoice amount."),
}


# ------------------------------------------------------------------ helpers
def db():
    con = sqlite3.connect(DB, timeout=10)
    con.row_factory = sqlite3.Row
    return con


def now():
    return dt.datetime.now().isoformat(timespec="seconds")


def today():
    return dt.date.today()


def money(x):
    return round(float(x or 0) + 0.0, 2)


def next_payment_run(after):
    """First weekly payment run on or after a date."""
    return after + dt.timedelta(days=(PAYMENT_RUN_WEEKDAY - after.weekday()) % 7)


def terms_days(terms):
    m = re.search(r"net\s*(\d+)", terms or "", re.I) or re.search(r"(\d+)", terms or "")
    return int(m.group(1)) if m else 30


def discount_terms(terms):
    """(percent, days) for terms like '2% 10, Net 30'; None when the terms carry no discount."""
    m = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(\d+)", terms or "")
    return (float(m.group(1)), int(m.group(2))) if m else None


def norm_inv(num):
    """Invoice number key for duplicate search: alphanumerics only, upper case, leading zeros and a
    trailing revision suffix (-A, -R, -1, REV) removed. '055241', '55241-A' and '55241' share one key."""
    s = re.sub(r"[^A-Za-z0-9]", "", str(num or "")).upper()
    m = re.fullmatch(r"(.*\d)(?:REV\d*|R\d?|[A-Z])", s)
    if m:
        s = m.group(1)
    return s.lstrip("0") or s


def log(con, kind, ref, message, actor="SYSADMIN"):
    con.execute("INSERT INTO events(at, kind, ref, actor, message) VALUES (?,?,?,?,?)", (now(), kind, ref, actor, message))


def init():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS employees (person_id INTEGER PRIMARY KEY, full_name TEXT, email TEXT, job_title TEXT, department TEXT, org_code TEXT,
          status TEXT, start_date TEXT, end_date TEXT, role_key TEXT, supervisor_id INTEGER, receives_own_goods INTEGER);
        CREATE TABLE IF NOT EXISTS suppliers (supplier_number TEXT PRIMARY KEY, supplier_name TEXT, site TEXT, address TEXT, terms TEXT,
          payment_method TEXT, status TEXT, contacts TEXT);
        CREATE TABLE IF NOT EXISTS po_headers (po_number TEXT PRIMARY KEY, supplier_number TEXT, status TEXT, created TEXT, buyer_id INTEGER,
          requester_id INTEGER, description TEXT);
        CREATE TABLE IF NOT EXISTS po_lines (po_number TEXT, line_num INTEGER, description TEXT, uom TEXT, quantity REAL, unit_price REAL,
          service_end TEXT, PRIMARY KEY (po_number, line_num));
        CREATE TABLE IF NOT EXISTS awards (award_number TEXT PRIMARY KEY, sponsor TEXT, federal INTEGER, project TEXT, task TEXT, department TEXT,
          start_date TEXT, end_date TEXT, title TEXT);
        CREATE TABLE IF NOT EXISTS receipts (id INTEGER PRIMARY KEY AUTOINCREMENT, receipt_num TEXT, po_number TEXT, line_num INTEGER,
          type TEXT, quantity REAL, date TEXT, received_by INTEGER, note TEXT);
        CREATE TABLE IF NOT EXISTS invoices (invoice_id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_num TEXT, supplier_number TEXT, type TEXT,
          invoice_date TEXT, received_date TEXT, gl_date TEXT, invoice_amount REAL, terms TEXT, due_date TEXT, po_number TEXT, source TEXT,
          description TEXT, attachment_url TEXT, validation_status TEXT, approval_status TEXT, payment_status TEXT, amount_paid REAL,
          created_by TEXT, created_at TEXT, approver_id INTEGER, approval_override TEXT, UNIQUE (supplier_number, invoice_num));
        CREATE TABLE IF NOT EXISTS invoice_lines (invoice_id INTEGER, line_num INTEGER, po_line_num INTEGER, description TEXT,
          quantity REAL, unit_price REAL, amount REAL, distribution TEXT, PRIMARY KEY (invoice_id, line_num));
        CREATE TABLE IF NOT EXISTS holds (id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id INTEGER, hold_name TEXT, hold_reason TEXT,
          line_num INTEGER, held_at TEXT, released_at TEXT, release_reason TEXT);
        CREATE TABLE IF NOT EXISTS payments (payment_number TEXT PRIMARY KEY, supplier_number TEXT, date TEXT, method TEXT, amount REAL, status TEXT,
          void_date TEXT, void_reason TEXT);
        CREATE TABLE IF NOT EXISTS payment_invoices (payment_number TEXT, invoice_id INTEGER, amount REAL, discount REAL);
        CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT, kind TEXT, ref TEXT, actor TEXT, message TEXT);
        CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_num TEXT, sent_to TEXT, sent_at TEXT, by_agent TEXT);
        """)


# ------------------------------------------------------------------ seed
def reset():
    seed = json.load(open(SEED))
    base = dt.date.fromisoformat(seed.get("base_date", "2026-10-23"))
    demo = os.environ.get("OHSU_DEMO_DATE")
    shift = (dt.date.fromisoformat(demo) - base).days if demo else 0

    def d(s):
        return (dt.date.fromisoformat(s) + dt.timedelta(days=shift)).isoformat() if s else s

    with LOCK, db() as con:
        for t in ("employees", "suppliers", "po_headers", "po_lines", "receipts", "invoices", "invoice_lines", "holds",
                  "payments", "payment_invoices", "events", "meta", "awards", "reminders"):
            con.execute("DELETE FROM " + t)
        con.execute("DELETE FROM sqlite_sequence")
        for e in seed["employees"]:
            con.execute("INSERT INTO employees VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (e["person_id"], e["full_name"], e["email"].lower(),
                        e["job_title"], e["department"], e["org_code"], e.get("status", "Active"), d(e.get("start_date")),
                        d(e.get("end_date")), e.get("role_key") or (e["org_code"] + ":" + e["job_title"]), e.get("supervisor_id"),
                        1 if e.get("receives_own_goods") else 0))
        for a in seed.get("awards", []):
            con.execute("INSERT INTO awards VALUES (?,?,?,?,?,?,?,?,?)", (a["award_number"], a["sponsor"], 1 if a["federal"] else 0, a["project"],
                        a["task"], a["department"], d(a["start_date"]), d(a["end_date"]), a["title"]))
        for s in seed["suppliers"]:
            con.execute("INSERT INTO suppliers VALUES (?,?,?,?,?,?,?,?)", (s["supplier_number"], s["supplier_name"], s["site"],
                        s["address"], s["terms"], s["payment_method"], s["status"], json.dumps(s["contacts"])))
        for p in seed["purchase_orders"]:
            con.execute("INSERT INTO po_headers VALUES (?,?,?,?,?,?,?)", (p["po_number"], p["supplier_number"], p["status"],
                        d(p["created"]), p["buyer_id"], p["requester_id"], p["description"]))
            for l in p["lines"]:
                con.execute("INSERT INTO po_lines VALUES (?,?,?,?,?,?,?)", (p["po_number"], l["line_num"], l["description"],
                            l["uom"], l["quantity"], l["unit_price"], d(l.get("service_end"))))
        for r in seed["receipts"]:
            con.execute("INSERT INTO receipts(receipt_num, po_number, line_num, type, quantity, date, received_by, note) VALUES (?,?,?,?,?,?,?,?)",
                        (r["receipt_num"], r["po_number"], r["line_num"], r["type"], r["quantity"], d(r["date"]), r["received_by"], r.get("note")))
        for inv in seed["invoices"]:
            body = dict(inv, invoice_date=d(inv["invoice_date"]), received_date=d(inv.get("received_date")))
            create_invoice(con, body, actor="CONVERSION", seeding=True)
        for r in con.execute("SELECT invoice_id FROM invoices WHERE validation_status != 'Never Validated' ORDER BY invoice_id").fetchall():
            validate(con, r[0], "CONVERSION")
        for p in seed["payments"]:
            total = money(sum(i["amount"] for i in p["invoices"]))
            voided = p.get("status") == "Voided"
            con.execute("INSERT INTO payments VALUES (?,?,?,?,?,?,?,?)", (p["payment_number"], p["supplier_number"], d(p["date"]),
                        p["method"], total, "Voided" if voided else "Negotiable", d(p.get("void_date")), p.get("void_reason")))
            for i in p["invoices"]:
                iid = con.execute("SELECT invoice_id FROM invoices WHERE supplier_number=? AND invoice_num=?",
                                  (p["supplier_number"], i["invoice_num"])).fetchone()[0]
                disc = money(i.get("discount") or 0)
                con.execute("INSERT INTO payment_invoices VALUES (?,?,?,?)", (p["payment_number"], iid, i["amount"], disc))
                if voided:      # a voided payment pays nothing
                    continue
                con.execute("UPDATE invoices SET amount_paid=COALESCE(amount_paid,0)+?, payment_status='Yes' WHERE invoice_id=?", (i["amount"], iid))
        # seeded records look as if they were entered when the invoice arrived, not when the demo was loaded
        con.execute("UPDATE invoices SET created_at = received_date || 'T09:14:00'")
        con.execute("""UPDATE holds SET held_at = (SELECT received_date || 'T09:15:00' FROM invoices i WHERE i.invoice_id = holds.invoice_id)""")
        con.execute("DELETE FROM events")
        con.execute("INSERT INTO meta VALUES ('date_shift_days', ?)", (str(shift),))
        con.execute("INSERT INTO meta VALUES ('loaded_at', ?)", (now(),))
        log(con, "system", None, "Demo data loaded from seed.json (dates shifted %+d days)." % shift)
        n = con.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
    return n


# ------------------------------------------------------------------ invoice validation (the 3-way match)
def po_line_position(con, po_number, line_num, upto_invoice_id=None):
    """Ordered, received (net of returns) and billed (net of debit memos) for one PO line."""
    pl = con.execute("SELECT * FROM po_lines WHERE po_number=? AND line_num=?", (po_number, line_num)).fetchone()
    if not pl:
        return None
    received = con.execute("SELECT COALESCE(SUM(quantity),0) FROM receipts WHERE po_number=? AND line_num=?",
                           (po_number, line_num)).fetchone()[0]
    sql = """SELECT COALESCE(SUM(il.quantity),0) FROM invoice_lines il JOIN invoices i ON i.invoice_id=il.invoice_id
             WHERE i.po_number=? AND il.po_line_num=? AND i.validation_status!='Cancelled'"""
    args = [po_number, line_num]
    if upto_invoice_id is not None:   # later standard invoices don't count against this one; debit and credit memos always do
        sql += " AND (i.invoice_id<=? OR i.type!='STANDARD')"; args.append(upto_invoice_id)
    billed = con.execute(sql, args).fetchone()[0]
    return {"line_num": line_num, "description": pl["description"], "uom": pl["uom"], "unit_price": pl["unit_price"],
            "quantity_ordered": pl["quantity"], "quantity_received": received, "quantity_billed": billed,
            "quantity_left_to_bill": max(0, min(pl["quantity"], received) - billed)}


def validate(con, invoice_id, actor="SYSADMIN"):
    inv = con.execute("SELECT * FROM invoices WHERE invoice_id=?", (invoice_id,)).fetchone()
    if inv["validation_status"] == "Cancelled":
        return
    lines = con.execute("SELECT * FROM invoice_lines WHERE invoice_id=? ORDER BY line_num", (invoice_id,)).fetchall()
    wanted = []                                                    # (hold_name, line_num, reason)
    if abs(money(sum(l["amount"] for l in lines)) - money(inv["invoice_amount"])) > 0.005:
        wanted.append(("DIST VARIANCE", None, "Invoice amount %.2f, lines total %.2f" % (inv["invoice_amount"], sum(l["amount"] for l in lines))))
    if inv["po_number"] and inv["type"] == "STANDARD":
        for l in lines:
            if not l["po_line_num"]:
                continue
            pos = po_line_position(con, inv["po_number"], l["po_line_num"], upto_invoice_id=invoice_id)
            if pos is None:
                continue
            if pos["quantity_billed"] > pos["quantity_ordered"] + 1e-9:
                wanted.append(("QTY ORD", l["line_num"], "Billed %g, ordered %g on PO line %d" % (pos["quantity_billed"], pos["quantity_ordered"], l["po_line_num"])))
            if pos["quantity_billed"] > pos["quantity_received"] + 1e-9:
                wanted.append(("QTY REC", l["line_num"], "Billed %g, received %g on PO line %d" % (pos["quantity_billed"], pos["quantity_received"], l["po_line_num"])))
            limit = pos["unit_price"] * (1 + PRICE_TOLERANCE_PCT / 100.0)
            if l["unit_price"] > limit + 0.005:
                wanted.append(("PRICE", l["line_num"], "Invoice price %.2f, PO price %.2f on PO line %d" % (l["unit_price"], pos["unit_price"], l["po_line_num"])))
    active = {(h["hold_name"], h["line_num"]): h for h in con.execute(
        "SELECT * FROM holds WHERE invoice_id=? AND released_at IS NULL", (invoice_id,))}
    wanted_keys = {(w[0], w[1]) for w in wanted}
    for key, h in active.items():
        if key not in wanted_keys:
            con.execute("UPDATE holds SET released_at=?, release_reason=? WHERE id=?", (now(), "Revalidated - condition resolved", h["id"]))
            log(con, "hold_released", inv["invoice_num"], "Invoice %s: %s hold released on revalidation." % (inv["invoice_num"], key[0]), actor)
    for name, line_num, reason in wanted:
        if (name, line_num) not in active:
            con.execute("INSERT INTO holds(invoice_id, hold_name, hold_reason, line_num, held_at) VALUES (?,?,?,?,?)",
                        (invoice_id, name, reason, line_num, now()))
            log(con, "hold_placed", inv["invoice_num"], "Invoice %s: %s hold placed. %s." % (inv["invoice_num"], name, reason), actor)
    held = bool(wanted)
    # PO-matched invoices need no invoice approval workflow (the PO was approved); others go through workflow
    approval = "Not Required" if inv["po_number"] else (inv["approval_override"] or ("Required" if held else "Workflow Approved"))
    con.execute("UPDATE invoices SET validation_status=?, approval_status=? WHERE invoice_id=?",
                ("Needs Revalidation" if held else "Validated", approval, invoice_id))


def revalidate_po(con, po_number, actor):
    for r in con.execute("SELECT invoice_id FROM invoices WHERE po_number=? AND payment_status!='Yes' ORDER BY invoice_id", (po_number,)).fetchall():
        validate(con, r[0], actor)


def create_invoice(con, body, actor="NANONETS_AGENT", seeding=False):
    """Payables Open Interface import, simplified: insert header + lines, then validate (match to PO and receipts)."""
    sup = con.execute("SELECT * FROM suppliers WHERE supplier_number=?", (str(body.get("supplier_number") or ""),)).fetchone()
    if not sup:
        return 422, {"error": "unknown_supplier", "message": "No supplier %s." % body.get("supplier_number")}
    num = str(body.get("invoice_num") or "").strip()
    if not num:
        return 422, {"error": "missing_invoice_num"}
    dup = con.execute("SELECT invoice_id FROM invoices WHERE supplier_number=? AND invoice_num=?", (sup["supplier_number"], num)).fetchone()
    if dup:
        return 409, {"error": "duplicate_invoice", "message": "Invoice %s already exists for supplier %s." % (num, sup["supplier_number"]),
                     "invoice": invoice_out(con, dup[0])}
    po = body.get("po_number")
    if po:
        ph = con.execute("SELECT * FROM po_headers WHERE po_number=?", (str(po),)).fetchone()
        if not ph:
            return 422, {"error": "unknown_po", "message": "No PO %s." % po}
        if ph["supplier_number"] != sup["supplier_number"]:
            return 422, {"error": "po_supplier_mismatch", "message": "PO %s belongs to supplier %s." % (po, ph["supplier_number"])}
    lines = body.get("lines") or []
    if not lines:
        return 422, {"error": "missing_lines"}
    for l in lines:
        if po and l.get("po_line_num") and not con.execute("SELECT 1 FROM po_lines WHERE po_number=? AND line_num=?", (str(po), int(l["po_line_num"]))).fetchone():
            return 422, {"error": "unknown_po_line", "message": "PO %s has no line %s." % (po, l["po_line_num"])}
    total = money(sum(float(l.get("quantity") or 0) * float(l.get("unit_price") or 0) for l in lines))
    amount = money(body["invoice_amount"]) if body.get("invoice_amount") is not None else total
    terms = body.get("terms") or sup["terms"]
    inv_date = body.get("invoice_date") or today().isoformat()
    due = (dt.date.fromisoformat(inv_date) + dt.timedelta(days=terms_days(terms))).isoformat()
    cur = con.execute("""INSERT INTO invoices(invoice_num, supplier_number, type, invoice_date, received_date, gl_date, invoice_amount, terms,
                         due_date, po_number, source, description, attachment_url, validation_status, approval_status, payment_status,
                         amount_paid, created_by, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                      (num, sup["supplier_number"], body.get("type") or "STANDARD", inv_date, body.get("received_date") or today().isoformat(),
                       inv_date, amount, terms, due, str(po) if po else None, body.get("source") or "NANONETS",
                       body.get("description"), body.get("attachment_url"), "Never Validated", "Required", "No", 0, actor, now()))
    iid = cur.lastrowid
    for n, l in enumerate(lines, 1):
        q, p = float(l.get("quantity") or 0), float(l.get("unit_price") or 0)
        con.execute("INSERT INTO invoice_lines VALUES (?,?,?,?,?,?,?,?)", (iid, n, l.get("po_line_num"), l.get("description"), q, p, money(q * p),
                    l.get("distribution")))
    approver = body.get("approver_email") or body.get("approver_id")
    if approver and not po:
        a = con.execute("SELECT person_id, full_name FROM employees WHERE email=? OR person_id=?", (str(approver).lower(), approver)).fetchone()
        if not a:
            return 422, {"error": "unknown_approver", "message": "No employee %s." % approver}
        con.execute("UPDATE invoices SET approver_id=?, approval_override=? WHERE invoice_id=?", (a["person_id"], body.get("approval") or "Initiated", iid))
        if not seeding:
            log(con, "approval", num, "Invoice %s: approval initiated, routed to %s in Oracle workflow." % (num, a["full_name"]), actor)
    if seeding and body.get("unvalidated"):
        return 201, None
    if not seeding:
        log(con, "invoice_created", num, "Invoice %s created for %s, %s, $%s%s (source %s)." % (
            num, sup["supplier_name"], body.get("type") or "STANDARD", "{:,.2f}".format(amount),
            ", matched to PO %s" % po if po else "", body.get("source") or "NANONETS"), actor)
    validate(con, iid, actor if not seeding else "CONVERSION")
    return 201, invoice_out(con, iid)


# ------------------------------------------------------------------ read models
def employee(con, pid):
    r = con.execute("SELECT * FROM employees WHERE person_id=?", (pid,)).fetchone()
    if not r:
        return None
    e = dict(r)
    if e.get("supervisor_id"):
        sup = con.execute("SELECT person_id, full_name, email, job_title FROM employees WHERE person_id=?", (e["supervisor_id"],)).fetchone()
        e["supervisor"] = dict(sup) if sup else None
    if e.get("status") != "Active":
        cur = con.execute("SELECT * FROM employees WHERE role_key=? AND status='Active' AND person_id!=? ORDER BY start_date DESC",
                          (e["role_key"], e["person_id"])).fetchone()
        e["current_holder"] = dict(cur) if cur else None
    return e


def supplier_out(con, r):
    d = dict(r); d["contacts"] = json.loads(d["contacts"] or "[]")
    d["open_po_numbers"] = [x[0] for x in con.execute("SELECT po_number FROM po_headers WHERE supplier_number=? AND status='APPROVED'", (r["supplier_number"],))]
    return d


def invoice_out(con, iid, brief=False):
    i = con.execute("""SELECT i.*, s.supplier_name, s.site, s.payment_method FROM invoices i JOIN suppliers s ON s.supplier_number=i.supplier_number
                       WHERE invoice_id=?""", (iid,)).fetchone()
    d = dict(i)
    holds = [dict(h) for h in con.execute("SELECT * FROM holds WHERE invoice_id=? ORDER BY id", (iid,))]
    active = [h for h in holds if not h["released_at"]]
    pays = [dict(p) for p in con.execute("""SELECT p.payment_number, p.date AS payment_date, p.method, pi.amount AS amount_applied,
                                             COALESCE(pi.discount,0) AS discount_taken, p.amount AS payment_amount, p.status AS payment_status,
                                             p.void_date, p.void_reason
                                             FROM payment_invoices pi JOIN payments p ON p.payment_number=pi.payment_number
                                             WHERE pi.invoice_id=? ORDER BY p.date""", (iid,))]
    live = [p for p in pays if p["payment_status"] != "Voided"]
    d["holds_count"] = len(active)
    d["discount_taken"] = money(sum(p["discount_taken"] for p in live))
    d["amount_remaining"] = money(d["invoice_amount"] - (d["amount_paid"] or 0) - d["discount_taken"])
    dt_terms = discount_terms(d["terms"])
    if dt_terms:
        d["discount_terms"] = {"percent": dt_terms[0], "days": dt_terms[1],
                               "discount_date": (dt.date.fromisoformat(d["invoice_date"]) + dt.timedelta(days=dt_terms[1])).isoformat(),
                               "basis": "invoice date"}
    for p in pays:
        if dt_terms and p["discount_taken"] and p["payment_date"] > d["discount_terms"]["discount_date"]:
            p["discount_after_window_days"] = (dt.date.fromisoformat(p["payment_date"]) - dt.date.fromisoformat(d["discount_terms"]["discount_date"])).days
        # every document settled by the same payment, so a net amount can be explained
        p["documents_in_payment"] = [dict(x) for x in con.execute("""SELECT i.invoice_num, i.type, i.invoice_amount, pi.amount AS amount_applied,
                                        COALESCE(pi.discount,0) AS discount_taken FROM payment_invoices pi JOIN invoices i ON i.invoice_id=pi.invoice_id
                                        WHERE pi.payment_number=?""", (p["payment_number"],))]
    if d["payment_status"] == "Yes":
        d["status_summary"], d["payment_date_type"] = "paid", "confirmed"
        d["payment_date"] = live[-1]["payment_date"] if live else None
        d["paid_by"] = live[-1]["payment_number"] if live else None
        d["voided_payments"] = [p["payment_number"] for p in pays if p["payment_status"] == "Voided"]
    elif active:
        d["status_summary"], d["payment_date_type"], d["payment_date"] = "on_hold", "none", None
    elif d["validation_status"] == "Validated" and d["approval_status"] in ("Initiated", "Required"):
        d["status_summary"], d["payment_date_type"], d["payment_date"] = "awaiting_approval", "none", None
    elif d["validation_status"] == "Validated":
        due = dt.date.fromisoformat(d["due_date"])
        d["status_summary"], d["payment_date_type"] = "approved_unpaid", "expected"
        d["payment_date"] = (due if due > today() else next_payment_run(today() + dt.timedelta(days=1))).isoformat()
        d["payment_date_basis"] = "due date" if due > today() else "next weekly payment run (already past due)"
    else:
        d["status_summary"], d["payment_date_type"], d["payment_date"] = "not_validated", "none", None
    due = dt.date.fromisoformat(d["due_date"])
    d["days_past_due"] = max(0, (today() - due).days) if d["payment_status"] != "Yes" else 0
    if brief:
        return d
    d["lines"] = [dict(l) for l in con.execute("SELECT * FROM invoice_lines WHERE invoice_id=? ORDER BY line_num", (iid,))]
    for l in d["lines"]:
        l["match_basis"] = "Quantity" if l["po_line_num"] else ""
        l["po_shipment"] = 1 if l["po_line_num"] else None
        l["po_distribution"] = 1 if l["po_line_num"] else None
    d["payments"] = pays
    d["approver"] = employee(con, d["approver_id"]) if d.get("approver_id") else None
    d["accounted"] = "Yes" if d["payment_status"] == "Yes" or d["validation_status"] == "Validated" else "No"
    d["payment_status_label"] = {"Yes": "Fully Paid"}.get(d["payment_status"], "Not Paid")
    d["scheduled_payments"] = [{"payment_num": 1, "due_date": d["due_date"], "gross_amount": d["invoice_amount"],
                                "amount_remaining": d["amount_remaining"], "hold": bool(active),
                                "payment_method": con.execute("SELECT payment_method FROM suppliers WHERE supplier_number=?",
                                                              (d["supplier_number"],)).fetchone()[0], "payment_priority": 99}]
    ph = con.execute("SELECT * FROM po_headers WHERE po_number=?", (d["po_number"],)).fetchone() if d["po_number"] else None
    req, buyer = (employee(con, ph["requester_id"]), employee(con, ph["buyer_id"])) if ph else (None, None)
    for h in holds:
        info = HOLD_INFO.get(h["hold_name"], ("", "ap", ""))
        h["description"] = info[0]
        h["held_by"] = "System"
        if h["released_at"]:   # Oracle's own release lookup names for holds released by revalidation
            h["release_name"] = {"PRICE": "Variance Corrected", "DIST VARIANCE": "Variance Corrected"}.get(h["hold_name"], "Matched")
            h["release_reason"] = {"PRICE": "Invoice variance corrected", "DIST VARIANCE": "Invoice variance corrected"}.get(
                h["hold_name"], "Passed matching condition")
            h["released_by"] = "System"
        if not h["released_at"]:
            who = {"requester": req, "buyer": buyer}.get(info[1])
            if h["hold_name"] == "QTY REC" and ph:
                # goods are received by Central Receiving at the dock; services by the PO requester (Trail rule 9)
                il = con.execute("SELECT po_line_num FROM invoice_lines WHERE invoice_id=? AND line_num=?", (iid, h["line_num"])).fetchone()
                pl = con.execute("SELECT uom FROM po_lines WHERE po_number=? AND line_num=?", (ph["po_number"], il[0] if il else 0)).fetchone()
                dock = con.execute("SELECT person_id FROM employees WHERE org_code='SCM-RCV' AND status='Active'").fetchone()
                own = req and req.get("receives_own_goods") and req.get("status") == "Active"
                if pl and pl["uom"] != "EA" and dock and not own:
                    who = employee(con, dock[0])
                    h["next_step"] = "Central Receiving enters the receipt in Oracle Purchasing when the goods arrive."
            if who and who.get("status") != "Active":
                # the person on the PO has left: the job's current holder acts instead
                h["named_on_po"] = dict(who, role_on_po=info[1])
                who = who.get("current_holder") or who
            h["who_must_act"] = dict(who, role_on_po=info[1]) if who else {"role_on_po": "ap", "department": "Accounts Payable"}
            h.setdefault("next_step", info[2])
    d["holds"] = holds
    d["po"] = {"po_number": ph["po_number"], "description": ph["description"], "requester": req, "buyer": buyer} if ph else None
    return d


def po_out(con, po_number):
    ph = con.execute("SELECT p.*, s.supplier_name FROM po_headers p JOIN suppliers s ON s.supplier_number=p.supplier_number WHERE po_number=?",
                     (po_number,)).fetchone()
    if not ph:
        return None
    d = dict(ph)
    d["requester"], d["buyer"] = employee(con, ph["requester_id"]), employee(con, ph["buyer_id"])
    d["lines"] = [po_line_position(con, po_number, r[0]) for r in con.execute("SELECT line_num FROM po_lines WHERE po_number=? ORDER BY line_num", (po_number,))]
    for l in d["lines"]:
        l["amount"] = money(l["quantity_ordered"] * l["unit_price"])
    d["po_total"] = money(sum(l["amount"] for l in d["lines"]))
    d["revision"] = con.execute("SELECT COUNT(*) FROM events WHERE kind='po_change' AND ref=?", (po_number,)).fetchone()[0]
    sup = con.execute("SELECT site, terms FROM suppliers WHERE supplier_number=?", (ph["supplier_number"],)).fetchone()
    d["supplier_site"], d["terms"] = sup["site"], sup["terms"]
    d["receipts"] = [dict(r, received_by_name=(employee(con, r["received_by"]) or {}).get("full_name")) for r in
                     con.execute("SELECT * FROM receipts WHERE po_number=? ORDER BY date, id", (po_number,))]
    d["invoices"] = [invoice_out(con, r[0], brief=True) for r in con.execute("SELECT invoice_id FROM invoices WHERE po_number=? ORDER BY invoice_id", (po_number,))]
    return d


def lookup_sender(con, email):
    """Who is this email address? A named supplier contact, someone at a supplier's domain, an OHSU employee, or unknown."""
    email = (email or "").strip().lower()
    domain = email.split("@")[-1] if "@" in email else ""
    emp = con.execute("SELECT * FROM employees WHERE email=?", (email,)).fetchone()
    if emp and emp["status"] == "Active":
        return {"email": email, "match": "employee", "verified": True, "employee": dict(emp)}
    if emp:
        return {"email": email, "match": "employee_inactive", "verified": False, "note": "Former employee; left %s." % emp["end_date"]}
    hits_contact, hits_domain = [], []
    for s in con.execute("SELECT * FROM suppliers"):
        contacts = json.loads(s["contacts"] or "[]")
        if any(c["email"].lower() == email for c in contacts):
            hits_contact.append(supplier_out(con, s))
        elif domain and any(c["email"].lower().split("@")[-1] == domain for c in contacts):
            hits_domain.append(supplier_out(con, s))
    if hits_contact:
        return {"email": email, "match": "supplier_contact", "verified": True, "supplier": hits_contact[0]}
    if hits_domain:
        return {"email": email, "match": "supplier_domain", "verified": True, "supplier": hits_domain[0],
                "note": "Address is not a named contact on the supplier record, but its domain matches one."}
    if domain == "ohsu.edu":
        return {"email": email, "match": "ohsu_domain_not_in_hr", "verified": False,
                "note": "ohsu.edu address with no employee record."}
    return {"email": email, "match": "unknown", "verified": False}


# ------------------------------------------------------------------ HTTP
class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, (bytes, bytearray)) else json.dumps(body, default=str, indent=1).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-API-Key, ngrok-skip-browser-warning")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS")
        self.end_headers()
        self.wfile.write(data)

    def _json(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            return json.loads(self.rfile.read(n).decode() or "{}")
        except ValueError:
            return None

    def _authed(self, path):
        if not API_KEY or not path.startswith("/api/") or path == "/api/health":
            return True
        if self.headers.get("X-API-Key") == API_KEY or self.headers.get("Referer", "").startswith("http://localhost"):
            return True
        self._send(401, {"error": "unauthorized", "message": "Send header X-API-Key."})
        return False

    def _actor(self, body=None):
        return (body or {}).get("actor") or self.headers.get("X-Actor") or "NANONETS_AGENT"

    def do_OPTIONS(self):
        self._send(204, b"", "text/plain")

    # ---- GET
    def do_GET(self):
        u = urlparse(self.path); q = {k: v[0] for k, v in parse_qs(u.query).items()}; p = u.path.rstrip("/") or "/"
        if p == "/":
            return self._send(200, open(os.path.join(HERE, "ui.html"), "rb").read(), "text/html; charset=utf-8")
        if not self._authed(p):
            return
        with db() as con:
            if p == "/api/health":
                n = con.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
                shift = con.execute("SELECT value FROM meta WHERE key='date_shift_days'").fetchone()
                return self._send(200, {"ok": True, "service": "Oracle EBS R12 mock (OHSU demo)", "invoices": n,
                                        "date_shift_days": int(shift[0]) if shift else 0, "today": today().isoformat()})
            if p == "/api/directory/lookup":
                out = lookup_sender(con, q.get("email"))
                if q.get("invoice_num"):
                    # May this sender be told about this invoice? Answers yes/no and why, never the invoice's details.
                    rows = con.execute("SELECT supplier_number FROM invoices WHERE invoice_num=?", (q["invoice_num"],)).fetchall()
                    sup = (out.get("supplier") or {}).get("supplier_number")
                    if out.get("match") == "employee":
                        out["authorized_for_invoice"], out["reason"] = True, "OHSU employee"
                    elif sup and any(r[0] == sup for r in rows):
                        out["authorized_for_invoice"], out["reason"] = True, "invoice belongs to the sender's supplier"
                    elif not rows and sup:
                        # nothing on file under this number for any supplier: there is nothing to disclose, so the sender may be told it isn't on file
                        out["authorized_for_invoice"], out["not_on_file"] = True, True
                        out["reason"] = "not on file for any supplier; say so and ask for a copy"
                    else:
                        out["authorized_for_invoice"] = False
                        out["reason"] = "sender is not a contact for the supplier that billed this invoice, or it is not on file"
                return self._send(200, out)
            if p == "/api/suppliers":
                sql, args = "SELECT * FROM suppliers WHERE 1=1", []
                if q.get("q"):
                    sql += " AND (supplier_name LIKE ? OR supplier_number LIKE ?)"; args += ["%" + q["q"].upper() + "%", "%" + q["q"] + "%"]
                return self._send(200, {"suppliers": [supplier_out(con, r) for r in con.execute(sql + " ORDER BY supplier_name", args)]})
            m = re.fullmatch(r"/api/suppliers/(\w+)", p)
            if m:
                r = con.execute("SELECT * FROM suppliers WHERE supplier_number=?", (m.group(1),)).fetchone()
                return self._send(200, supplier_out(con, r)) if r else self._send(404, {"error": "not_found", "message": "No supplier %s." % m.group(1)})
            if p == "/api/employees":
                sql, args = "SELECT * FROM employees WHERE 1=1", []
                if q.get("email"):
                    sql += " AND email=?"; args.append(q["email"].lower())
                if q.get("q"):
                    sql += " AND full_name LIKE ?"; args.append("%" + q["q"] + "%")
                return self._send(200, {"employees": [dict(r) for r in con.execute(sql, args)]})
            if p == "/api/invoices/duplicate-check":
                sup, num = q.get("supplier_number"), q.get("invoice_num")
                if not sup or not num:
                    return self._send(400, {"error": "supplier_number and invoice_num are required"})
                key, amt = norm_inv(num), q.get("amount")
                hits = []
                for r in con.execute("SELECT invoice_id, invoice_num, invoice_amount, invoice_date FROM invoices WHERE supplier_number=?", (sup,)):
                    reasons = []
                    if r["invoice_num"] == num:
                        reasons.append("same invoice number")
                    elif norm_inv(r["invoice_num"]) == key:
                        reasons.append("same number in a different form (%s)" % r["invoice_num"])
                    if amt and abs(money(r["invoice_amount"]) - money(amt)) < 0.005 and q.get("invoice_date") == r["invoice_date"]:
                        reasons.append("same amount and invoice date")
                    if reasons:
                        hits.append(dict(invoice_out(con, r["invoice_id"], brief=True), match_reasons=reasons))
                return self._send(200, {"supplier_number": sup, "invoice_num": num, "normalized_key": key,
                                        "variants_checked": list(dict.fromkeys([num, key, "0" + key, key + "-A", key + "-R"])),
                                        "is_duplicate": bool(hits), "matches": hits})
            if p == "/api/invoices":
                sql, args = "SELECT invoice_id FROM invoices WHERE 1=1", []
                for k in ("supplier_number", "invoice_num", "po_number", "validation_status", "source"):
                    if q.get(k):
                        sql += " AND %s=?" % k; args.append(q[k])
                if q.get("amount"):
                    sql += " AND ABS(invoice_amount-?)<0.005"; args.append(float(q["amount"]))
                if q.get("on_hold") in ("true", "1"):
                    sql += " AND invoice_id IN (SELECT invoice_id FROM holds WHERE released_at IS NULL)"
                sql += " ORDER BY invoice_date DESC, invoice_id DESC"
                rows = [invoice_out(con, r[0], brief=q.get("detail") not in ("true", "1")) for r in con.execute(sql, args)]
                return self._send(200, {"invoices": rows, "count": len(rows)})
            m = re.fullmatch(r"/api/invoices/([\w.-]+)", p)
            if m:
                key = m.group(1)
                sql, args = "SELECT invoice_id FROM invoices WHERE (invoice_num=? OR CAST(invoice_id AS TEXT)=?)", [key, key]
                if q.get("supplier_number"):
                    sql += " AND supplier_number=?"; args.append(q["supplier_number"])
                rows = con.execute(sql, args).fetchall()
                if not rows:
                    return self._send(404, {"error": "not_found", "message": "No invoice %s%s in Oracle." % (
                        key, " for supplier %s" % q["supplier_number"] if q.get("supplier_number") else "")})
                if len(rows) > 1:
                    return self._send(300, {"error": "ambiguous", "message": "More than one supplier has invoice %s. Pass supplier_number." % key,
                                            "invoices": [invoice_out(con, r[0], brief=True) for r in rows]})
                return self._send(200, invoice_out(con, rows[0][0]))
            m = re.fullmatch(r"/api/purchase-orders/(\w+)", p)
            if m:
                d = po_out(con, m.group(1))
                return self._send(200, d) if d else self._send(404, {"error": "not_found", "message": "No PO %s." % m.group(1)})
            if p == "/api/purchase-orders":
                sql, args = "SELECT po_number FROM po_headers WHERE 1=1", []
                if q.get("supplier_number"):
                    sql += " AND supplier_number=?"; args.append(q["supplier_number"])
                return self._send(200, {"purchase_orders": [po_out(con, r[0]) for r in con.execute(sql + " ORDER BY po_number", args)]})
            if p == "/api/payments":
                sql, args = "SELECT * FROM payments WHERE 1=1", []
                if q.get("supplier_number"):
                    sql += " AND supplier_number=?"; args.append(q["supplier_number"])
                if q.get("date_from"):
                    sql += " AND date>=?"; args.append(q["date_from"])
                out = []
                for r in con.execute(sql + " ORDER BY date DESC", args):
                    out.append(payment_out(con, r))
                return self._send(200, {"payments": out})
            m = re.fullmatch(r"/api/payments/(\w+)", p)
            if m:
                r = con.execute("SELECT * FROM payments WHERE payment_number=?", (m.group(1),)).fetchone()
                return self._send(200, payment_out(con, r)) if r else self._send(404, {"error": "not_found"})
            if p == "/api/holds":
                # Every invoice on an active receiving hold, with its age, who must act, and whether its service period has ended.
                min_bd = int(q.get("older_than_business_days") or 0)
                out = []
                for r in con.execute("""SELECT DISTINCT i.invoice_id FROM invoices i JOIN holds h ON h.invoice_id=i.invoice_id
                                        WHERE h.released_at IS NULL AND h.hold_name='QTY REC' ORDER BY i.invoice_id""").fetchall():
                    inv = invoice_out(con, r[0])
                    h = [x for x in inv["holds"] if not x["released_at"] and x["hold_name"] == "QTY REC"][0]
                    held = dt.date.fromisoformat(h["held_at"][:10])
                    bd = sum(1 for k in range(1, (today() - held).days + 1) if (held + dt.timedelta(days=k)).weekday() < 5)
                    if bd <= min_bd:
                        continue
                    line = next((l for l in inv["lines"] if l["line_num"] == h["line_num"]), None)
                    pl = con.execute("SELECT service_end FROM po_lines WHERE po_number=? AND line_num=?",
                                     (inv["po_number"], line["po_line_num"] if line else 0)).fetchone() if inv["po_number"] else None
                    se = pl["service_end"] if pl else None
                    who = h["who_must_act"]
                    last = con.execute("SELECT sent_at, sent_to FROM reminders WHERE invoice_num=? ORDER BY sent_at DESC LIMIT 1",
                                       (inv["invoice_num"],)).fetchone()
                    out.append({"last_reminded_at": last["sent_at"] if last else None, "last_reminded_to": last["sent_to"] if last else None,"invoice_num": inv["invoice_num"], "supplier_number": inv["supplier_number"], "supplier_name": inv["supplier_name"],
                                "invoice_amount": inv["invoice_amount"], "po_number": inv["po_number"], "held_since": h["held_at"][:10],
                                "days_held": (today() - held).days, "business_days_held": bd,
                                "service_period_end": se, "service_period_ended": (se is None) or (dt.date.fromisoformat(se) < today()),
                                "who_must_act": {k: who.get(k) for k in ("full_name", "email", "job_title", "department")},
                                "director": (who.get("supervisor") or {}) if isinstance(who, dict) else {},
                                "named_on_po": (h.get("named_on_po") or {}).get("full_name")})
                return self._send(200, {"as_of": today().isoformat(), "count": len(out), "total": money(sum(x["invoice_amount"] for x in out)), "holds": out})
            m = re.fullmatch(r"/api/awards/([\w .%-]+)", p)
            if m:
                key = unquote(m.group(1))
                r = con.execute("SELECT * FROM awards WHERE award_number=? OR REPLACE(award_number,' ','')=?", (key, key.replace(" ", ""))).fetchone()
                if not r:
                    return self._send(404, {"error": "not_found", "message": "No award %s." % key})
                a = dict(r); a["federal"] = bool(a["federal"])
                return self._send(200, a)
            if p == "/api/reminders":
                # Demo helper: the reminder log the Supplier Inquiry and Hold Follow-up agents share. Not an Oracle table.
                rows = [dict(r) for r in con.execute("SELECT * FROM reminders ORDER BY sent_at DESC LIMIT 200")]
                return self._send(200, {"reminders": rows})
            if p == "/api/worklist":
                rows = [invoice_out(con, r[0]) for r in con.execute("SELECT invoice_id FROM invoices WHERE approval_override='Initiated' ORDER BY invoice_id")]
                return self._send(200, {"items": rows})
            if p == "/api/events":
                after = int(q.get("after") or 0)
                rows = [dict(r) for r in con.execute("SELECT * FROM events WHERE id>? ORDER BY id DESC LIMIT 100", (after,))]
                return self._send(200, {"events": rows})
        return self._send(404, {"error": "not_found"})

    # ---- POST
    def do_POST(self):
        p = urlparse(self.path).path.rstrip("/")
        if not self._authed(p):
            return
        body = self._json()
        if body is None:
            return self._send(400, {"error": "invalid_json"})
        if p == "/api/invoices":
            with LOCK, db() as con:
                code, out = create_invoice(con, body, actor=self._actor(body))
            return self._send(code, out)
        m = re.fullmatch(r"/api/invoices/(\d+)/validate", p)
        if m:
            with LOCK, db() as con:
                if not con.execute("SELECT 1 FROM invoices WHERE invoice_id=?", (int(m.group(1)),)).fetchone():
                    return self._send(404, {"error": "not_found"})
                validate(con, int(m.group(1)), self._actor(body))
                return self._send(200, invoice_out(con, int(m.group(1))))
        m = re.fullmatch(r"/api/invoices/(\d+)/approve", p)
        if m:
            with LOCK, db() as con:
                iid = int(m.group(1))
                inv = con.execute("SELECT * FROM invoices WHERE invoice_id=?", (iid,)).fetchone()
                if not inv or inv["approval_override"] != "Initiated":
                    return self._send(409, {"error": "not_awaiting_approval"})
                con.execute("UPDATE invoices SET approval_override='Workflow Approved' WHERE invoice_id=?", (iid,))
                validate(con, iid, self._actor(body))
                ap = employee(con, inv["approver_id"]) or {}
                log(con, "approval", inv["invoice_num"], "Invoice %s approved in Oracle workflow by %s." % (inv["invoice_num"], ap.get("full_name", self._actor(body))), ap.get("full_name", self._actor(body)))
                return self._send(200, invoice_out(con, iid))
        if p == "/api/receipts":
            # One receipt can cover several lines: {"po_number", "lines": [{"line_num", "quantity"}], "received_by"}
            # The single-line form {"po_number", "line_num", "quantity"} still works.
            po = str(body.get("po_number") or "")
            lines = body.get("lines") or [{"line_num": body.get("line_num"), "quantity": body.get("quantity")}]
            with LOCK, db() as con:
                checked = []
                for l in lines:
                    line, qty = int(l.get("line_num") or 0), float(l.get("quantity") or 0)
                    pos = po_line_position(con, po, line)
                    if not pos:
                        return self._send(404, {"error": "not_found", "message": "No PO %s line %d." % (po, line)})
                    if qty <= 0 or pos["quantity_received"] + qty > pos["quantity_ordered"]:
                        return self._send(422, {"error": "invalid_quantity", "message": "PO %s line %d: ordered %g, already received %g." % (
                            po, line, pos["quantity_ordered"], pos["quantity_received"])})
                    checked.append((line, qty, pos))
                emp = con.execute("SELECT person_id, full_name FROM employees WHERE email=? OR person_id=?",
                                  (str(body.get("received_by") or "").lower(), body.get("received_by"))).fetchone()
                last = con.execute("SELECT MAX(CAST(receipt_num AS INTEGER)) FROM receipts").fetchone()[0] or 5533400
                rnum = str(max(int(last), 5533400) + 1)
                who = emp["full_name"] if emp else self._actor(body)
                for line, qty, pos in checked:
                    con.execute("INSERT INTO receipts(receipt_num, po_number, line_num, type, quantity, date, received_by, note) VALUES (?,?,?,?,?,?,?,?)",
                                (rnum, po, line, "RECEIVE", qty, today().isoformat(), emp["person_id"] if emp else None, body.get("note")))
                    log(con, "receipt", po, "Receipt %s: %g %s received on PO %s line %d by %s." % (rnum, qty, pos["uom"], po, line, who), who)
                revalidate_po(con, po, who)
                return self._send(201, dict(po_out(con, po), receipt_num=rnum))
        if p == "/api/reminders":
            nums = body.get("invoice_nums") or ([body["invoice_num"]] if body.get("invoice_num") else [])
            if not nums or not body.get("sent_to"):
                return self._send(422, {"error": "invoice_nums and sent_to are required"})
            with LOCK, db() as con:
                for n in nums:
                    con.execute("INSERT INTO reminders(invoice_num, sent_to, sent_at, by_agent) VALUES (?,?,?,?)",
                                (str(n), body["sent_to"], body.get("sent_at") or now(), self._actor(body)))
                log(con, "reminder", ",".join(map(str, nums)), "Reminder logged to %s for %s." % (body["sent_to"], ", ".join(map(str, nums))), self._actor(body))
            return self._send(201, {"ok": True, "logged": len(nums)})
        if p == "/api/admin/reset":
            return self._send(200, {"ok": True, "invoices": reset()})
        return self._send(404, {"error": "not_found"})

    # ---- PATCH (a buyer changing a PO line price)
    def do_PATCH(self):
        p = urlparse(self.path).path.rstrip("/")
        if not self._authed(p):
            return
        m = re.fullmatch(r"/api/purchase-orders/(\w+)/lines/(\d+)", p)
        body = self._json()
        if not m or body is None:
            return self._send(404 if not m else 400, {"error": "not_found" if not m else "invalid_json"})
        po, line = m.group(1), int(m.group(2))
        with LOCK, db() as con:
            pl = con.execute("SELECT * FROM po_lines WHERE po_number=? AND line_num=?", (po, line)).fetchone()
            if not pl:
                return self._send(404, {"error": "not_found"})
            who = self._actor(body)
            changes = []
            if body.get("unit_price") is not None:
                con.execute("UPDATE po_lines SET unit_price=? WHERE po_number=? AND line_num=?", (float(body["unit_price"]), po, line))
                changes.append("price %.2f -> %.2f" % (pl["unit_price"], float(body["unit_price"])))
            if body.get("quantity") is not None:
                con.execute("UPDATE po_lines SET quantity=? WHERE po_number=? AND line_num=?", (float(body["quantity"]), po, line))
                changes.append("quantity %g -> %g" % (pl["quantity"], float(body["quantity"])))
            if changes:
                log(con, "po_change", po, "PO %s line %d changed: %s (revision by %s)." % (po, line, ", ".join(changes), who), who)
                revalidate_po(con, po, who)
            return self._send(200, po_out(con, po))


def payment_out(con, r):
    d = dict(r)
    sup = con.execute("SELECT supplier_name, site FROM suppliers WHERE supplier_number=?", (r["supplier_number"],)).fetchone()
    d["supplier_name"], d["supplier_site"] = sup["supplier_name"], sup["site"]
    d["invoices"] = [dict(x) for x in con.execute("""SELECT i.invoice_num, i.type, i.invoice_date, i.invoice_amount, pi.amount AS amount_applied,
                                                       COALESCE(pi.discount,0) AS discount_taken, i.description
                                                       FROM payment_invoices pi JOIN invoices i ON i.invoice_id=pi.invoice_id
                                                       WHERE pi.payment_number=?""", (r["payment_number"],))]
    return d


if __name__ == "__main__":
    init()
    with db() as con:
        empty = con.execute("SELECT COUNT(*) FROM invoices").fetchone()[0] == 0
    if "--reset" in sys.argv or empty:
        print("loaded %d invoices from seed.json" % reset())
    print("Oracle EBS R12 mock (OHSU) listening on http://localhost:%d" % PORT)
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
