
from langgraph.graph import StateGraph, END
from datetime import datetime
import json, uuid

INV_PATH = "inventory.json"
APR_PATH = "approvals.json"

def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def node_check_inventory(state):
    inv = load_json(INV_PATH, [])
    low = [it for it in inv if it.get("on_hand_qty", 0) < it.get("reorder_threshold", 0)]
    print(f"📊 low-stock items: {len(low)}")
    if not low:
        return {"next": END, "note": "no candidates"}

    item = low[0]
    return {"item": item, "next": "approval_request"}

def node_approval_request(state):
    item = state["item"]
    token = str(uuid.uuid4())
    approvals = load_json(APR_PATH, [])
    approvals.append({
        "token": token,
        "sku": item["item_sku"],
        "created_at": datetime.utcnow().isoformat(),
        "state": "pending"
    })
    save_json(APR_PATH, approvals)
    approve_url = f"http://localhost:8000/approve/{token}"
    reject_url  = f"http://localhost:8000/reject/{token}"
    print(f"\n🔔 Approval Needed for {item['item_sku']} | {item['item_name']}")
    print(f"Approve: {approve_url}")
    print(f"Reject:  {reject_url}")
    ans = input("\n(H) Approve or (R) Reject? ").strip().lower()
    approved = (ans == "h")
    return {"item": item, "token": token, "approved": approved, "next": "update_log"}

def node_update_log(state):
    inv = load_json(INV_PATH, [])
    sku = state["item"]["item_sku"]
    for it in inv:
        if it.get("sku") == sku:
            it["last_checked"] = datetime.utcnow().isoformat()
            it["status"] = "PO sent" if state["approved"] else "Rejected"
            it["comments"] = f"LangGraph HITL token={state['token'][:8]}"
            it["last_po_id"] = state["token"][:8] if state["approved"] else it.get("last_po_id", "")
    save_json(INV_PATH, inv)
    print(f"✅ inventory.json updated for {sku} ({'approved' if state['approved'] else 'rejected'}).")
    return {"next": END}


graph = StateGraph(dict)
graph.add_node("check_inventory", node_check_inventory)
graph.add_node("approval_request", node_approval_request)
graph.add_node("update_log", node_update_log)

graph.set_entry_point("check_inventory")
graph.add_edge("check_inventory", "approval_request")
graph.add_edge("approval_request", "update_log")
graph.add_edge("update_log", END)

app = graph.compile()

if __name__ == "__main__":
    print(" Running LangGraph (step 3a)")
    result = app.invoke({})