# server.py
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
import sqlite3
import json
import asyncio
import uuid
import datetime
import os

app = FastAPI(title="Enterprise Small Business Inventory & Agentic MCP Server", version="9.0.0")
DB_NAME = "inventory.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit TEXT NOT NULL,
            reorder_threshold INTEGER NOT NULL,
            daily_burn_rate INTEGER NOT NULL,
            expiry_date TEXT NOT NULL,
            supplier TEXT NOT NULL,
            unit_cost REAL DEFAULT 5.0
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM inventory")
    if cursor.fetchone()[0] == 0:
        seed_file = os.path.join(os.path.dirname(__file__), "inventory_seed.json")
        if os.path.exists(seed_file):
            with open(seed_file, "r") as f:
                seed_data = json.load(f)
            for item in seed_data:
                cursor.execute("""
                    INSERT OR IGNORE INTO inventory 
                    (item_name, category, quantity, unit, reorder_threshold, daily_burn_rate, expiry_date, supplier, unit_cost) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (item["item_name"], item["category"], item["quantity"], item["unit"], item["reorder_threshold"], item["daily_burn_rate"], item["expiry_date"], item["supplier"], item["unit_cost"]))
            conn.commit()
    conn.close()

init_db()

def get_inventory_items():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT item_name, category, quantity, unit, reorder_threshold, daily_burn_rate, expiry_date, supplier, unit_cost FROM inventory")
    rows = cursor.fetchall()
    conn.close()
    return [{
        "item_name": r[0], "category": r[1], "quantity": r[2], 
        "unit": r[3], "reorder_threshold": r[4], "daily_burn_rate": r[5], "expiry_date": r[6], "supplier": r[7], "unit_cost": r[8]
    } for r in rows]

def update_stock(item_name: str, qty_change: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE inventory SET quantity = quantity + ? WHERE LOWER(item_name) = LOWER(?)", (qty_change, item_name))
    conn.commit()
    conn.close()

@app.get("/", response_class=FileResponse)
def web_dashboard():
    return FileResponse(os.path.join(os.path.dirname(__file__), "index.html"))

@app.get("/api/inventory")
def api_inventory():
    return {"items": get_inventory_items()}

@app.api_route("/mcp", methods=["GET", "POST"])
async def mcp_endpoint(request: Request):
    if request.method == "GET":
        return StreamingResponse(iter([f"event: endpoint\ndata: /mcp\n\n".encode()]), media_type="text/event-stream")

    body = await request.json()
    method = body.get("method")
    params = body.get("params", {})
    req_id = body.get("id")

    if method == "initialize":
        return JSONResponse(content={
            "jsonrpc": "2.0",
            "result": {
                "protocolVersion": "2025-11-25",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "enterprise-inventory-mcp", "version": "9.0.0"}
            },
            "id": req_id
        }, headers={"MCP-Session-Id": str(uuid.uuid4())})

    if method == "tools/list":
        return JSONResponse(content={
            "jsonrpc": "2.0",
            "result": {
                "tools": [
                    {"name": "check_stock_level", "description": "Check item stock", "inputSchema": {"type": "object", "properties": {"item_name": {"type": "string"}}, "required": ["item_name"]}},
                    {"name": "reorder_item", "description": "Reorder item quantity", "inputSchema": {"type": "object", "properties": {"item_name": {"type": "string"}, "quantity": {"type": "integer"}}, "required": ["item_name", "quantity"]}},
                    {"name": "predict_stockouts", "description": "Predict stockouts based on burn rate", "inputSchema": {"type": "object", "properties": {}}},
                    {"name": "bulk_reorder_low_stock", "description": "Bulk reorder low stock items", "inputSchema": {"type": "object", "properties": {}}},
                    {"name": "audit_expiring_goods", "description": "Audit expiring perishables", "inputSchema": {"type": "object", "properties": {}}},
                    {"name": "generate_purchase_order", "description": "Generate formatted PO payload for a supplier", "inputSchema": {"type": "object", "properties": {"supplier_name": {"type": "string"}}, "required": ["supplier_name"]}},
                    {"name": "suggest_clearance_promos", "description": "Suggest clearance promos for near-expiry goods", "inputSchema": {"type": "object", "properties": {}}},
                    {"name": "simulate_reorder_budget", "description": "Prioritize and pack reorders under a cash budget constraint", "inputSchema": {"type": "object", "properties": {"max_budget": {"type": "number"}}, "required": ["max_budget"]}},
                    {"name": "add_new_item", "description": "Add a new item to the inventory database", "inputSchema": {"type": "object", "properties": {"item_name": {"type": "string"}, "category": {"type": "string"}, "quantity": {"type": "integer"}, "unit": {"type": "string"}, "reorder_threshold": {"type": "integer"}, "daily_burn_rate": {"type": "integer"}, "expiry_date": {"type": "string"}, "supplier": {"type": "string"}, "unit_cost": {"type": "number"}}, "required": ["item_name", "category", "quantity", "unit", "reorder_threshold", "daily_burn_rate", "expiry_date", "supplier", "unit_cost"]}},
                    {"name": "update_unit_cost", "description": "Update the wholesale cost of an existing item", "inputSchema": {"type": "object", "properties": {"item_name": {"type": "string"}, "new_cost": {"type": "number"}}, "required": ["item_name", "new_cost"]}},
                    {"name": "generate_inventory_report", "description": "Generate a high-level summary of total inventory value and risk", "inputSchema": {"type": "object", "properties": {}}},
                    {"name": "remove_item", "description": "Delete an item from the inventory database completely", "inputSchema": {"type": "object", "properties": {"item_name": {"type": "string"}}, "required": ["item_name"]}},
                    {"name": "export_inventory_csv", "description": "Generate a raw CSV export string of all inventory items", "inputSchema": {"type": "object", "properties": {}}},
                    {"name": "calculate_potential_profit", "description": "Calculate projected profit margin", "inputSchema": {"type": "object", "properties": {"markup_percentage": {"type": "number"}}, "required": ["markup_percentage"]}}
                ]
            },
            "id": req_id
        })

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        items = get_inventory_items()
        res = {"error": "Tool execution failed or tool not found."}
        
        if tool_name == "check_stock_level":
            name = arguments.get("item_name", "").lower()
            match = next((i for i in items if name in i["item_name"].lower()), None)
            res = {"message": f"Found {match['item_name']}: {match['quantity']} {match['unit']} left."} if match else {"message": "Item not found."}
            
        elif tool_name == "reorder_item":
            name = arguments.get("item_name", "")
            qty = arguments.get("quantity", 10)
            update_stock(name, qty)
            res = {"message": f"Successfully reordered {qty} units of {name}."}
            
        elif tool_name == "predict_stockouts":
            predictions = [f"{i['item_name']} (~{i['quantity'] // i['daily_burn_rate']} days left)" for i in items if i["daily_burn_rate"] > 0 and (i["quantity"] // i["daily_burn_rate"]) <= 3]
            res = {"message": f"⚠️ Predictive Stockout Alert: Immediate restock needed for {', '.join(predictions)}!"} if predictions else {"message": "✅ All items have safe runway."}
                
        elif tool_name == "bulk_reorder_low_stock":
            reordered = []
            for i in items:
                if i["quantity"] <= i["reorder_threshold"]:
                    update_stock(i["item_name"], 30)
                    reordered.append(f"30 {i['unit']} of {i['item_name']}")
            res = {"message": f"🚀 Bulk Reorder Executed: Restocked {', '.join(reordered)}."} if reordered else {"message": "✅ No items require reordering."}
                
        elif tool_name == "audit_expiring_goods":
            today = datetime.date.today()
            exp = [f"{i['item_name']} ({i['expiry_date']})" for i in items if (datetime.date.fromisoformat(i['expiry_date']) - today).days <= 7]
            res = {"message": f"⚠️ Perishables expiring soon: {', '.join(exp)}"} if exp else {"message": "✅ No perishables expiring soon."}

        elif tool_name == "generate_purchase_order":
            supplier = arguments.get("supplier_name", "").strip()
            sup_items = [i for i in items if supplier.lower() in i["supplier"].lower() and i["quantity"] <= i["reorder_threshold"]]
            sup_items = sup_items or [i for i in items if supplier.lower() in i["supplier"].lower()][:2]
            res = {"message": f"📋 PO Generated for {supplier}: {', '.join([f'{i['item_name']} (Qty: 50)' for i in sup_items])}. Ready for dispatch."} if sup_items else {"message": "No items found for supplier."}

        elif tool_name == "suggest_clearance_promos":
            today = datetime.date.today()
            promos = [f"30% OFF {i['item_name']} (Expires {i['expiry_date']})" for i in items if 0 <= (datetime.date.fromisoformat(i['expiry_date']) - today).days <= 3]
            res = {"message": f"🏷️ Clearance Promos Suggested: {', '.join(promos)}"} if promos else {"message": "✅ No items require clearance."}

        elif tool_name == "simulate_reorder_budget":
            budget = float(arguments.get("max_budget", 100.0))
            spent, ordered = 0.0, []
            for i in sorted([x for x in items if x["quantity"] <= x["reorder_threshold"]], key=lambda x: x["quantity"]):
                if spent + (30 * i["unit_cost"]) <= budget:
                    spent += (30 * i["unit_cost"])
                    ordered.append(f"30 {i['item_name']}")
            res = {"message": f"💰 Budget Simulation (${budget:.2f}): Prioritized {', '.join(ordered)}. Spent: ${spent:.2f}."} if ordered else {"message": "No critical items within budget."}

        elif tool_name == "add_new_item":
            try:
                conn = sqlite3.connect(DB_NAME)
                conn.execute("INSERT INTO inventory (item_name, category, quantity, unit, reorder_threshold, daily_burn_rate, expiry_date, supplier, unit_cost) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                             (arguments['item_name'], arguments['category'], arguments['quantity'], arguments['unit'], arguments['reorder_threshold'], arguments['daily_burn_rate'], arguments['expiry_date'], arguments['supplier'], arguments['unit_cost']))
                conn.commit()
                conn.close()
                res = {"message": f"✨ Success! Added new item: {arguments['item_name']} to the inventory."}
            except sqlite3.IntegrityError:
                res = {"message": f"❌ Error: {arguments['item_name']} already exists in the database."}

        elif tool_name == "update_unit_cost":
            conn = sqlite3.connect(DB_NAME)
            conn.execute("UPDATE inventory SET unit_cost = ? WHERE LOWER(item_name) LIKE ?", (arguments['new_cost'], f"%{arguments['item_name'].lower()}%"))
            conn.commit()
            conn.close()
            res = {"message": f"💵 Price Updated: {arguments['item_name']} is now ${arguments['new_cost']:.2f}."}

        elif tool_name == "generate_inventory_report":
            total_items = len(items)
            total_value = sum(i['quantity'] * i['unit_cost'] for i in items)
            low_stock = sum(1 for i in items if i['quantity'] <= i['reorder_threshold'])
            res = {"message": f"📊 EXECUTIVE REPORT:\n• Total SKUs: {total_items}\n• Total Capital Tied in Stock: ${total_value:,.2f}\n• Action Required: {low_stock} items are currently at low stock."}

        elif tool_name == "remove_item":
            name = arguments.get("item_name", "")
            conn = sqlite3.connect(DB_NAME)
            conn.execute("DELETE FROM inventory WHERE LOWER(item_name) = LOWER(?)", (name,))
            conn.commit()
            conn.close()
            res = {"message": f"🗑️ Success: Removed '{name}' entirely from the database."}

        elif tool_name == "export_inventory_csv":
            csv_data = "Item Name,Category,Quantity,Unit,Threshold,Burn Rate,Expiry,Supplier,Unit Cost\n"
            for i in items:
                csv_data += f"{i['item_name']},{i['category']},{i['quantity']},{i['unit']},{i['reorder_threshold']},{i['daily_burn_rate']},{i['expiry_date']},{i['supplier']},{i['unit_cost']}\n"
            res = {"message": f"📄 CSV Export Generated:\n\n```csv\n{csv_data}```"}

        elif tool_name == "calculate_potential_profit":
            markup = float(arguments.get("markup_percentage", 40.0)) / 100.0
            total_cost = sum(i['quantity'] * i['unit_cost'] for i in items)
            projected_rev = total_cost * (1 + markup)
            profit = projected_rev - total_cost
            res = {"message": f"📈 Profit Projection ({markup*100}% retail markup):\n• Total Cost Value: ${total_cost:,.2f}\n• Projected Revenue: ${projected_rev:,.2f}\n• Potential Profit Margin: ${profit:,.2f}"}

        return JSONResponse(content={
            "jsonrpc": "2.0",
            "result": {"content": [{"type": "text", "text": json.dumps(res)}]},
            "id": req_id
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)