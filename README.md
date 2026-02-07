# Practical Lab 1 — Predictive Maintenance

## My Approach
- Developed a predictive-maintenance pipeline that **learns normal behavior from historical training data** (Neon PostgreSQL) and **detects anomalies in live data streams**.
- Modeled each robot independently and trained **per-axis regression models (Axis #1–#8)** because different axes have unique operational characteristics.
- Instead of predicting failures directly, the models forecast the **expected current**, and **risk is inferred when observed values consistently exceed expectations**.

---

## 1) Exploratory Data Analysis (EDA)

### Data Validation
- Checked **data completeness, duplicate entries, monotonic timestamps, and axis value ranges** for each robot.
- Ensured the training set represents **normal operating conditions**, as thresholds depend on a clean baseline.

### Summary Statistics
- Computed **mean, median, standard deviation, and IQR** for each axis.
- Observed that **some axes naturally fluctuate more**, meaning threshold setting must account for per-axis variability.

### Trend Analysis
- Plotted **Time vs Axis** to examine drift and stability.
- Fitted baseline regression lines for each axis to visualize expected behavior.

### Residual Inspection
- Calculated **residuals = observed − predicted**.
- Visualized residuals over time and with histograms/boxplots to separate **normal noise from anomalies**.

**Insight:** Residuals provide a **trend-aware noise envelope**, which makes alerting more precise.

---

## 2) Regression Models — Baseline Learning
- Trained **8 linear regression models per robot** (one for each axis).
- Documented **slope and intercept** for reproducibility.
- Overlaid regression lines on scatter plots to visualize the expected trajectory.

**Takeaway:** Regression serves as an explainable baseline; the focus is on **unexpected deviations**, not raw values.

---

## 3) Residual Analysis — Setting Thresholds
- Defined the **normal deviation envelope** using training residuals.
- Positive residuals (above the regression line) signal **excess consumption**, potential early fault indicators.
- Compared axes by residual spread and frequency of deviations.

**Takeaway:** Residuals are superior to static thresholds because they **adjust for normal drift and operating conditions**.

---

## 4) Threshold Discovery (MinC, MaxC, T)

### Definitions
- **MinC:** minimum deviation triggering an **Alert** if sustained.
- **MaxC:** higher deviation triggering an **Error** if sustained.
- **T:** minimum duration the deviation must persist.

### Derivation
- Computed positive residuals per axis.
- **MinC = 95th percentile**, **MaxC = 99th percentile** of residuals.
- Chose **T** based on typical transient spikes to filter noise.

**Insight:**  
- MinC: early warning  
- MaxC: critical condition  
- T: prevents false positives

---

## 5) Alert & Error Rules
- Compute residual(t) = observed(t) − predicted(t)
- **Alert:** residual ≥ MinC for ≥ T seconds  
- **Error:** residual ≥ MaxC for ≥ T seconds  
- Log events with robot_id, axis, event type, start/end time, duration, max/avg residual, and threshold used.

**Takeaway:** Clear escalation: **Alert = early deviation**, **Error = sustained critical anomaly**.

---

## 6) Streaming Simulation
- Simulate real-time data by processing one row at a time.
- For each record:
  - Predict expected axis value
  - Calculate residual
  - Track continuous deviations
  - Emit Alert/Error when duration exceeds T

**Takeaway:** Mirrors real-world telemetry pipelines.

---

## 7) Synthetic Test Data
- Generate realistic test data based on training stats.
- Normalize using only training parameters.
- Inject controlled anomalies to validate detection logic.

**Insight:** Synthetic data ensures thorough testing of **detection thresholds and event handling**.

---

## 8) Database Integration
- Pull training data from **Neon PostgreSQL**.
- Log alerts/errors into structured CSV or DB tables.
- Ensures **reproducibility and traceability**.

---

## 9) Visualization
- For each axis:
  - Scatter plot: observed vs time
  - Regression line: expected baseline
  - Overlay Alert/Error markers
  - Annotate events with duration and peak deviation

**Takeaway:** Visual proof makes monitoring **transparent and verifiable**.

---

## Key Takeaways
- Robot- and axis-specific baselines avoid blending different operational profiles.
- Residual-based anomaly detection adjusts for natural drift.
- Thresholds (MinC/MaxC) are **data-driven**, not arbitrary.
- Continuous-duration logic (T) filters noise effectively.
- Alert/Error events are fully logged, supporting actionable monitoring.
