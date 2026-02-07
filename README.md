
# 🤖 Robot Predictive Maintenance — Neon + Live Streaming Alerts + Dashboard (Workshop)#**

> **Executive Intent:** Turn raw robot telemetry into **actionable predictive maintenance signals** — with **trained thresholds**, **live-stream visualization**, **event logging**, and a **dashboard** backed by **Neon Postgres**.

This project builds a clean end-to-end workflow:  
1) **Train models + learn thresholds** from historical robot data  
2) **Stream live data** per robot and detect **ALERT / ERROR** events in real-time  
3) Persist everything to **Neon** and visualize outcomes in a **dashboard**

---

## 🧠 What Problem Are We Solving?

Industrial robots generate continuous sensor signals. Failures are expensive, disruptive, and often discovered too late.  
This system watches live signals and raises early warnings:

- ⚠️ **ALERT** = abnormal behavior emerging (maintenance soon)
- 🛑 **ERROR** = high-risk abnormality (maintenance urgent)

The project follows a **predictive maintenance mindset**: detect abnormal trends early, log events, and make the system easy to operationalize.

---

## ✅ Deliverables (What You Can Demo)

### ✅ Notebook 1 — Model Training + Threshold Learning (Neon)
- Loads raw dataset
- Prepares per-robot training sets
- Fits **Linear Regression baseline**
- Computes residual-based thresholds:
  - `residual_alert`
  - `residual_error`
- Stores trained parameters + thresholds into Neon table: `linear_regression.models`

### ✅ Notebook 2 — Live Streaming + Alerting + Events Log (Neon)
- Streams recent points for each robot (fast + smooth)
- Shows 4 plots (one per robot)  
- Displays:
  - Observed waveform
  - Smoothed waveform
  - Regression baseline
  - Threshold reference bands
  - Symbol markers for **ALERT** and **ERROR**
- Saves events to:
  - `experiments/events.log`
  - `linear_regression.events` table in Neon

### ✅ Dashboard (Streamlit)
- Pulls latest stream + events from Neon
- Shows per-robot panels
- Summarizes events in a lookback window
- Enables quick “operator view” monitoring

---

## 🧱 Architecture (High-Level)

**Raw CSV → Training pipeline → Models in Neon → Streaming detector → Events in Neon → Dashboard**

- **Data layer:** Raw CSV + Neon Postgres  
- **Model layer:** Linear Regression baseline per robot  
- **Detection layer:** Residual thresholding + cooldown to reduce spam  
- **Observability layer:** events.log + events table + dashboard panels  

This is intentionally designed like a real-world pipeline: modular, logged, and demo-ready.

---

## ⚙️ Environment Setup

### 1) Create & activate virtual environment
```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\activate
````

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Configure Neon connection

Create `.env` in the project root:

```env
PGHOST=xxxxx.neon.tech
PGDATABASE=xxxx
PGUSER=xxxx
PGPASSWORD=xxxx
PGPORT=5432
PGSSLMODE=require
```

---

## ▶️ How to Run (Correct Order)

### Step 1 — Train models + save thresholds to Neon

Open and run:

* `notebooks/01_train_models_thresholds_neon.ipynb`

Expected output:

* ✅ models saved into `linear_regression.models`
* You should see 4 rows (robot 1–4)

---

### Step 2 — Run live streaming + generate events + save logs

Open and run:

* `notebooks/02_streaming_alerts_dashboard_neon.ipynb`

Expected output:

* 4 live plots (Robot 1–4)
* Visible threshold reference lines
* ⚠️ + 🛑 symbols plotted when events occur
* `experiments/events.log` filled with events
* `linear_regression.events` populated

---

### Step 3 — Launch the Dashboard

```bash
streamlit run dashboard/app.py
```

Expected output:

* Robot panels
* Latest stream lookback
* Event summaries pulled from Neon

---

## 📌 Key Technical Design Choices (Why This Is “Engineer-Grade”)

### ✅ Why Linear Regression baseline?

It’s a strong baseline for workshop-grade predictive maintenance:

* interpretable
* fast
* stable
* easy to validate

### ✅ Why residual-based thresholds?

Residuals quantify deviation from expected behavior.
Thresholds convert residual severity into actionable events:

* `residual_alert` captures early abnormality
* `residual_error` captures critical abnormality

### ✅ Why cooldown logic?

Streaming detectors can spam events. Cooldown enforces:

* fewer duplicate alerts
* better signal-to-noise ratio
* cleaner operator experience

### ✅ Why Neon DB?

Because production-grade pipelines don’t keep data in notebook memory:

* persistent storage
* dashboard-ready
* real operational flow

---

## 📊 Outputs & Evidence

This project produces:

* Live streaming plots per robot
* Logged events (`events.log`)
* Structured Neon tables:

  * `training_points`
  * `stream_points`
  * `models`
  * `events`

---

## 🧪 Quality Checks (Before Submission)

Run these checks to confirm you’re “10/10-ready”:

✅ **Database sanity**

* `models` table has 4 rows
* `events` table gets populated after streaming

✅ **Plot sanity**

* Each robot shows:

  * observed waveform
  * regression baseline
  * threshold reference
  * ALERT/ERROR markers visible at least once

✅ **Reproducibility**

* Fresh clone + install + run works end-to-end

✅ **Clean storytelling**

* Notebook markdown explains what each step does (short, clear)

---

---

## 

**Sumanth Reddy K**
Repository: `LinearRegressionWorkshop-1`
Course: Workshop / Predictive Maintenance + Streaming Analytics

```
