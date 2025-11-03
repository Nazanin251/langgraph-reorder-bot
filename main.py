from langgraph.graph import StateGraph, END
from datetime import datetime, UTC
import json, uuid, os

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
    pairs = state.get("pairs")
    idx   = state.get("idx", 0)

    if not pairs:

        pairs = [(i, it) for i, it in enumerate(inv)
                 if it.get("on_hand_qty", 0) < it.get("reorder_threshold", 0)]
        print(f"📊 low-stock items: {len(pairs)}")
        if not pairs:
            return {"next": END, "note": "no candidates"}
        idx = 0

    if idx >= len(pairs):
        return {"next": END, "note": "done"}

    row_idx, item = pairs[idx]
    return {
        "pairs": pairs,
        "idx": idx,
        "row_idx": row_idx,
        "item": item,
        "next": "approval_request"
    }

def node_approval_request(state):
    pairs = state["pairs"]
    start_idx = state.get("idx", 0)

    approvals = load_json(APR_PATH, [])
    made = 0

    print("\n================== 📧 EMAILS TO OWNER (SIMULATED) ==================")
    for j in range(start_idx, len(pairs)):
        row_idx, item = pairs[j]
        token = str(uuid.uuid4())
        approvals.append({
            "token": token,
            "sku": item.get("item_sku") or item.get("sku") or f"row#{row_idx+1}",
            "idx": row_idx,
            "created_at": datetime.now(UTC).isoformat(),
            "state": "pending"
        })

        approve_url = f"http://localhost:8000/approve/{token}"
        reject_url  = f"http://localhost:8000/reject/{token}"


        print(f"\n🔔 Approval Needed for {item.get('item_sku') or item.get('sku') or '(no sku)'} | {item.get('item_name','(no name)')}")
        # print(f"  Current Stock: {item.get('on_hand_qty')}  Threshold: {item.get('reorder_threshold')}")
        # print(f"  Supplier: {item.get('supplier_name')} <{item.get('supplier_email')}>")
        print(f"  Approve: {approve_url}")
        print(f"  Reject:  {reject_url}")
        made += 1

    save_json(APR_PATH, approvals)
    print("\n====================================================================\n")
    print(f"🟢 Created {made} approval link(s).")
    print("⏸ Waiting for human approval via web links...")


    return {"next": END}



def node_update_log(state):
    inv      = load_json(INV_PATH, [])
    row_idx  = state["row_idx"]
    pairs    = state["pairs"]
    idx      = state["idx"]
    token    = state["token"]
    approved = state["approved"]

    if 0 <= row_idx < len(inv):
        inv[row_idx]["last_checked"] = datetime.now(UTC).isoformat()
        inv[row_idx]["status"] = "PO sent" if approved else "Rejected"
        inv[row_idx]["comments"] = f"LangGraph HITL token={token[:8]}"

        if approved:
            inv[row_idx]["last_po_id"] = token[:8]
        save_json(INV_PATH, inv)
        print(f" inventory.json updated (row #{row_idx+1}) — {'approved' if approved else 'rejected'}.")
    else:
        print(f" row_idx {row_idx} out of range; skip update")

    nxt_idx = idx + 1
    if nxt_idx < len(pairs):
        return {"pairs": pairs, "idx": nxt_idx, "next": "check_inventory"}
    else:
        return {"next": END}


graph = StateGraph(dict)
graph.add_node("check_inventory", node_check_inventory)
graph.add_node("approval_request", node_approval_request)
graph.add_node("update_log", node_update_log)

graph.set_entry_point("check_inventory")
graph.add_edge("check_inventory", "approval_request")
# graph.add_edge("approval_request", "update_log")
graph.add_edge("update_log", "check_inventory")

app = graph.compile()


if __name__ == "__main__":

    if not os.path.exists(APR_PATH):
        save_json(APR_PATH, [])
    print(" Running LangGraph (loop over low-stock)")
    app.invoke({})
