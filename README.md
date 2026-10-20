# 🧠 Alexa+ Enterprise Hub (Small Business Inventory MCP)

Built for the **Build, Ship, Shape: Amazon Developer Hackathon (Alexa+ Track)**. 

The **Alexa+ Enterprise Hub** is a self-hosted Model Context Protocol (MCP) server and simulated Alexa+ web client. It is engineered to bring enterprise-grade supply chain intelligence to small shopkeepers, hawker stalls, and local cafe owners through intuitive conversational AI.

---

## 🌟 Inspiration & What It Does

Small businesses constantly fight a battle against dead capital and inventory spoilage. Relying on manual tracking makes predicting stockouts difficult and time-consuming. 

The **Alexa+ Enterprise Hub** acts as an autonomous supply chain assistant. It tracks dynamic daily burn rates, predicts imminent stockouts, and proactively helps manage vendor relationships through simple conversational commands.

---

## ✨ Key Features (MCP Tools)

* **Predictive Stockouts & Spoilage Logging:** Tracks dynamic daily burn rates and warns owners before high-velocity staples run out or perishables expire.
* **Automated Purchase Orders:** Automatically aggregates low-stock items by supplier and generates dispatch-ready Purchase Order (PO) payloads.
* **Smart Budget Planning:** Simulates the most critical reorders needed to stay operational under strict cash-flow constraints.
* **Clearance Engine:** Scans for near-expiry items and automatically generates promotional markdown strategies to recoup costs.
* **Profit Projections & Custom Items:** Seamlessly adds new items directly to the database and calculates projected profit margins based on wholesale costs and retail markups.

---

## 🏗️ Architecture & Compliance

This project strictly adheres to the official hackathon requirements for the Alexa+ simulated experience path:

* **`server.py` (Backend):** A FastAPI server fully compliant with the **2025-11-25 Streamable HTTP MCP specification**. It exposes over 15 specialized enterprise tools via JSON-RPC.
* **`index.html` (Simulated Client):** A browser-based Agentic Chat Simulator and GUI dashboard that executes conversational commands against the backend tools in real-time.
* **`inventory_seed.json`:** A flexible data seed file that automatically populates the live SQLite database (`inventory.db`) on the first boot.

---

## 🚀 Quick Start Instructions

### 1. Install Dependencies
Ensure you have Python installed, then install the required FastAPI and Uvicorn packages:
```bash
pip install fastapi uvicorn
```

### 2. Run the Server
Launch the MCP server and web dashboard:
```bash
python server.py
```

### 3. Open the Dashboard
Open your web browser and navigate to:
```url
http://127.0.0.1:8000
```

### 4. Test the Agent
Try typing these sample prompts into the **Agentic Chat Simulator**, or click the guided prompt cards on the user interface:
* *"Add new item KFC Bucket, Fast Food, 15, buckets, 5, 2, 2026-10-31, KFC Corp, $12.50"*
* *"Simulate reorder budget for $150"*
* *"Calculate profit projection at 40% markup"*

---

## 📄 License

This project is licensed under the **MIT License**.
