# 📦 Automated Re-Order Concierge (LangGraph + HITL)

This project is a small demo of an **automated re-order assistant** for small online retailers.

It uses:

- **LangGraph** to orchestrate the workflow as a **state machine**
- **Human-in-the-loop (HITL)** step via one-click **Approve / Reject** links
- Simple **JSON files** instead of a real database / Google Sheets
- **FastAPI** to simulate emails and confirmation links

The goal is to reduce stockouts by automatically detecting low stock items and asking the owner to approve a purchase order before it is sent to the supplier.

---

## 🎯 Problem

Small online retailers often lose sales because stockouts are not noticed early enough.  
Orders get cancelled, revenue is lost, and customer trust is damaged.

This project implements a background workflow that:

- Monitors inventory
- Detects low-stock items
- Asks the owner for approval (HITL)
- Sends a simulated PO (Purchase Order) to the supplier
- Logs the action back into the inventory data

---

## 🧠 Architecture Overview

**Main pieces:**

1. `main.py`  
   - Implements the **LangGraph state machine**
   - Reads `inventory.json`
   - Finds low-stock items (`on_hand_qty < reorder_threshold`)
   - Creates approval tokens and links
   - Writes pending approvals to `approvals.json`
   - Prints simulated “email to owner” with Approve/Reject links  
   - Stops and waits for human approval via web

2. `hitl_api.py`  
   - A **FastAPI** app exposing:
     - `GET /approve/{token}`
     - `GET /reject/{token}`
   - When a link is opened:
     - Updates the matching row in `inventory.json`
     - Changes `status`, `last_checked`, `comments`, `last_po_id`
     - On **Approve**: prints a simulated **email to supplier** (with SKU, qty, address…)  
     - On **Reject**: just logs that it was rejected

3. `inventory.json`  
   - Simulates the **Google Sheet** with inventory:
     - `item_sku` / `sku`
     - `item_name`
     - `on_hand_qty`
     - `reorder_threshold`
     - `reorder_qty`
     - `supplier_name`
     - `supplier_email`
     - `delivery_address`
     - `last_checked`
     - `status`
     - `comments`
     - `last_po_id`

4. `approvals.json`  
   - Stores **pending** approval records:
     ```json
     {
       "token": "uuid",
       "sku": "F-001",
       "idx": 3,
       "created_at": "2025-11-02T10:15:00+00:00",
       "state": "pending / confirmed / rejected"
     }
     ```

---

## 🛠 Tech Stack

- Python 3.10+
- [LangGraph](https://github.com/langchain-ai/langgraph)
- FastAPI
- Uvicorn


