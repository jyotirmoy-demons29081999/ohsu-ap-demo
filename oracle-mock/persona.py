"""Make jyotirmoy@trailhq.com the sender for one test case, in the live stand-in Oracle.

JP sends every test email from one address, so before each case this script gives that address
to the case's sender. Every other OHSU staff address becomes a jyotirmoy+<name>@trailhq.com alias,
so no agent ever emails a real ohsu.edu person. It edits oracle.db in place (no reset), so
invoices, holds and reminders from earlier cases are kept. Run it again after any reset.

    python3 persona.py case1      # jyotirmoy@trailhq.com = Dana, Pacific Northwest Surgical
    python3 persona.py show

Someone else running the demo sets their own address first; staff aliases then become <name>+<staff>@<domain>:
    export OHSU_ME=you@yourcompany.com
"""
import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get("OHSU_DB", os.path.join(HERE, "oracle.db"))
ME = os.environ.get("OHSU_ME", "jyotirmoy@trailhq.com").strip().lower()

# Who sends each case's email: a supplier (by number) or an employee (by person id).
CASES = {
    "case1": ("supplier", "104882"),  # Dana Reyes
    "case2": ("employee", 41207),     # Maria Chen
    "case3": ("supplier", "106231"),  # Columbia Lab Products
    "case4": (None, None),            # the lookalike: nobody, so the sender is unknown
    "case5": ("supplier", "104882"),
    "case6": ("supplier", "104882"),
    "case7": ("employee", 43105),     # Sofia Alvarez
    "case8": ("supplier", "109377"),  # Summit Biomedical
    "case9": ("employee", 44210),     # Nadia Rahman
    "case10": (None, None),
}


def alias(email):
    local, domain = ME.split("@")
    return "%s+%s@%s" % (local.split("+")[0], email.split("@")[0].replace(".", ""), domain)


def apply(con, case):
    kind, key = CASES[case]
    seed = json.load(open(os.path.join(HERE, "seed.json")))
    for e in seed["employees"]:
        new = ME if (kind == "employee" and e["person_id"] == key) else alias(e["email"])
        con.execute("UPDATE employees SET email=? WHERE person_id=?", (new, e["person_id"]))
    for s in seed["suppliers"]:
        contacts = json.loads(con.execute("SELECT contacts FROM suppliers WHERE supplier_number=?",
                                          (s["supplier_number"],)).fetchone()[0])
        for c, orig in zip(contacts, s["contacts"]):
            c["email"] = ME if (kind == "supplier" and s["supplier_number"] == key) else orig["email"]
        con.execute("UPDATE suppliers SET contacts=? WHERE supplier_number=?",
                    (json.dumps(contacts), s["supplier_number"]))
    con.commit()


def show(con):
    owner = [r[0] for r in con.execute("SELECT full_name FROM employees WHERE email=?", (ME,))]
    for num, name, contacts in con.execute("SELECT supplier_number, supplier_name, contacts FROM suppliers"):
        if ME in contacts:
            owner.append("%s (supplier %s)" % (name, num))
    staff = [r[0] for r in con.execute("SELECT email FROM employees")]
    print("%s is now: %s" % (ME, ", ".join(owner) or "nobody (an unknown sender)"))
    print("Staff addresses at ohsu.edu: %d (should be 0)" % sum(1 for e in staff if e.endswith("@ohsu.edu")))


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "show"
    con = sqlite3.connect(DB, timeout=10)
    if arg != "show":
        apply(con, arg)
    show(con)
