# Practical Lab 1 — Predictive Maintenance

## My POV (What I built)
- Built a predictive-maintenance pipeline where **baseline behavior is learned from historical training data** (Neon PostgreSQL) and **risk is detected from live deviation** (streaming synthetic test data).
- Modeled **each robot independently** and trained **axis-wise baselines (Time → Axis #1–#8)** because robots/axes have different operating profiles; a single global model increases false positives.
- Regression does not “predict failure” directly; it predicts the **expected current trend**. **Failure risk is inferred when observed current persistently exceeds the expected baseline**.

---

## 1) EDA (Exploratory Data Analysis)

### Data Quality Validation
- Validate dataset integrity per robot: **missing values, duplicates, time monotonicity**, and **axis range checks**.
- Confirm training data reflects **normal operating conditions**, since thresholds depend on a clean baseline.

### Central Tendency & Dispersion (Per Axis, Per Robot)
- Compute **mean, median** (typical current) and **std, IQR** (natural variability) for each axis (#1–#8).
- **Insight:** axes with higher dispersion are naturally noisier, so **thresholds must be data-driven**.

### Trend Understanding (Time vs Axis)
- Plot **Time vs Axis** scatter plots to inspect drift, stability, and operating modes.
- Fit a baseline regression line per axis and verify trend alignment with observed behavior.

### Residuals (Where anomalies live)
- Compute residuals: **residual = observed − predicted**.
- Plot residuals over time to detect **bursts vs sustained deviations**.
- Plot residual distributions (histogram/boxplot) to separate **normal noise envelope** from true outliers.

**EDA Insight**
- Normal behavior is not a constant value; it is a **trend + noise envelope**. Residuals quantify that envelope and make alerting explainable.

---

## 2) Regression Models (Time → Axis #1–#8) — Baseline Learning
- Train **8 univariate linear regression models** per robot: Time as input, Axis as output.
- Record **slope and intercept** per axis for reproducibility and auditability.
- Overlay regression lines on scatter plots to show the expected baseline trajectory.

**Talking Point**
- Regression provides an explainable baseline; the key signal is **unexpected deviation from the expected trend**, not raw current alone.

---

## 3) Residual Analysis — Threshold Justification
- Use training residuals to define the **normal deviation envelope** per axis.
- Focus on **positive residuals** (above regression line) as abnormal excess consumption (early symptom of friction/load/wear).
- Compare axes by residual spread and outlier frequency to identify which axes are most sensitive to anomalies.

**Talking Point**
- Residuals outperform raw thresholds because they account for drift and operating conditions (**expected vs actual monitoring**).

---

## 4) Threshold Discovery (MinC, MaxC, T) — Defensible and Evidence-Based

### Definitions (Clear and Testable)
- **MinC:** minimum deviation above baseline to trigger an **Alert** if sustained.
- **MaxC:** higher deviation above baseline to trigger an **Error** if sustained.
- **T:** minimum continuous time (seconds) the deviation must persist.

### How I derived MinC and MaxC (Quantile method)
- Compute positive training residuals (Observed − Predicted) per axis (and per robot where applicable).
- Set thresholds from the residual distribution:
  - **MinC = 95th percentile** of positive training residuals
  - **MaxC = 99th percentile** of positive training residuals

### How I chose T (anti-noise firewall)
- Measure typical residual spike durations from training residual time series.
- Set **T above normal spike duration** to reduce false positives and detect sustained abnormality.

**Threshold Insight**
- MinC = **early-warning band** (watch the machine)
- MaxC = **critical band** (act now / likely failure developing)
- T = filters transient spikes to avoid chatty monitoring

---

## 5) Alert & Error Rules
- residual(t) = observed(t) − predicted(t)
- **Alert:** residual(t) ≥ **MinC** continuously for ≥ **T seconds**
- **Error:** residual(t) ≥ **MaxC** continuously for ≥ **T seconds**
- Log every event with: **robot_id, axis, event_type, start_time, end_time, duration_sec, max_residual, avg_residual, threshold_used**

**Talking Point**
- Escalation policy is clean and interpretable: **Alert = early drift**, **Error = sustained critical deviation**.

---

## 6) Streaming Simulation (CSV/DataFrame → Scoring → Events)
- Simulate streaming by emitting one record per time step (row-by-row).
- For each incoming record:
  - Predict expected axis value using the trained regression model
  - Compute residual
  - Update continuous-duration counters (state-machine logic)
  - Emit Alert/Error when conditions persist for ≥ T seconds

**Talking Point**
- This mirrors industrial telemetry: **ingestion → real-time scoring → alerting → event logging**.

---

## 7) Synthetic Test Data (Realistic + Controlled Validation)
- Generate test data using training metadata (similar mean/std and ranges per axis).
- Normalize/standardize using **training parameters only** (no leakage):
  - Min-Max normalization or Z-score standardization based on training stats
- Inject controlled anomaly windows to validate Alert/Error behavior.

**Insight**
- Synthetic streaming validates detection logic reliably, including edge cases and sustained drift.

---

## 8) Database Integration (Neon PostgreSQL) — Reproducible Training
- Pull training data from **Neon PostgreSQL** into the application for model training.
- Use consistent schema and reproducible SQL queries.
- Log alert/error events to a structured CSV (and optionally persist into PostgreSQL).

**Talking Point**
- Training-from-DB ensures reproducibility: the baseline is sourced from a single truth system.

---

## 9) Visualization & Proof (Regression + Alert/Error Annotations)
- For each axis plot:
  - Scatter: Time vs observed
  - Regression line: predicted
  - Overlay Alert markers and Error markers
  - Annotate each event with **duration and peak deviation**

**Talking Point**
- Visual overlays make the logic reviewable: the reviewer can verify exactly why an event triggered.

---

## High-Impact Talking Points
- Trained **robot-specific, axis-specific baselines** to avoid blending operating profiles.
- Used **residuals** as the anomaly signal (expected vs actual), not raw current thresholds.
- Derived **MinC/MaxC from residual distributions**, not guesswork.
- Chose **T using run-length behavior** to filter noise and detect sustained abnormality.
- Implemented Alert/Error using a **continuous-duration state machine** with complete event logging.
- Flagged failure risk when **Error persists**, indicating sustained abnormal consumption consistent with fault development.
