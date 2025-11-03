from fastapi import FastAPI, HTTPException
from datetime import datetime, UTC
import json

INV_PATH = "inventory.json"
APR_PATH = "approvals.json"

app = FastAPI(title="HITL API")

def load_json(p, d):
    try:
        with open(p, "r", encoding="utf-8") as f: return json.load(f)
    except: return d

def save_json(p, data):
    with open(p, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

def mark_approval(token: str, state: str):
    approvals = load_json(APR_PATH, [])
    rec = next((r for r in approvals if r.get("token")==token), None)
    if not rec: raise HTTPException(404, "Invalid token")
    if rec.get("state") != "pending": return rec  # قبلاً رسیدگی شده
    rec["state"] = "confirmed" if state=="approved" else "rejected"
    save_json(APR_PATH, approvals)
    return rec

def update_inventory_row(idx: int, approved: bool, token: str):
    inv = load_json(INV_PATH, [])
    if not (0 <= idx < len(inv)): raise HTTPException(404, "Row index not found")
    inv[idx]["last_checked"] = datetime.now(UTC).isoformat()
    inv[idx]["status"] = "PO sent" if approved else "Rejected"
    inv[idx]["comments"] = f"HITL via web, token={token[:8]}"
    if approved:
        inv[idx]["last_po_id"] = token[:8]

        po = (
            f"PO {token[:8]} | {inv[idx].get('item_name','')}\n"
            f"SKU: {inv[idx].get('item_sku') or inv[idx].get('sku')}\n"
            f"QTY: {inv[idx].get('reorder_qty')}\n"
            f"To:  {inv[idx].get('supplier_name')} <{inv[idx].get('supplier_email')}>"
        )
        print("\n===== PO (stub) =====\n" + po + "\n=====================\n")
    save_json(INV_PATH, inv)

@app.get("/approve/{token}")
def approve(token: str):
    rec = mark_approval(token, "approved")
    update_inventory_row(rec["idx"], True, token)
    return {"message": "Approved. PO sent (stub).", "row": rec["idx"]+1}

@app.get("/reject/{token}")
def reject(token: str):
    rec = mark_approval(token, "rejected")
    update_inventory_row(rec["idx"], False, token)
    return {"message": "Rejected and logged.", "row": rec["idx"]+1}
