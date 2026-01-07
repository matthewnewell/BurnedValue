# Burned Value Requirements

## 1. Core Philosophy
**Burned Value** is a project governance framework that uses **Agile Release Burndowns** as the **Quantifiable Backup Data (QBD)** to drive strictly factual **Earned Value Management (EVMS)** metrics.

It solves the "PM Delusion" by mathematically linking Scope Volatility to Cost Efficiency using **Value Density**.

## 2. Key Formulas & Logic

### 2.1 Value Density (The "Exchange Rate")
The central metric defining the value of work relative to the investment.
$$ \text{Value Density} = \frac{\text{Budget at Completion (BAC)}}{\text{Total Estimated Effort (Points)}} $$
*   **Metric:** $/Point.
*   **Behavior:** If Scope increases (Points added) without Budget increase, **Value Density decreases**. This mathematically "dilutes" the value of every point earned, forcing a drop in CPI.

### 2.2 The Scope-Value Trade-off
The application must visualize the mathematical certainty of "Dilution". When scope is added, the distinct choices must be apparent in the data:
*   **Fund the Scope:** Increase BAC to maintain Value Density.
*   **Reject the Change:** Maintain current BAC and Scope.
*   **Accept Variance:** Keep BAC constant, forcing CPI < 1.0 (Variance).

### 2.3 The Bridge (QBD to EV)
Agile data drives the Financials.
$$ \text{Percent Complete} = \frac{\text{Completed Points}}{\text{Total Estimated Effort}} $$
$$ \text{Earned Value (EV)} = \text{Percent Complete} \times \text{Budget at Completion (BAC)} $$

## 3. Functional Requirements

### 3.1 Data Management
*   **Project Setup:** Define Name, Description, BAC, Start Date, End Date.
*   **Periodic Entry (Sprint/Week):**
    *   **Points Completed:** Velocity for the period.
    *   **Actual Cost (AC) Calculation:** 
        *   Option A: Direct Total Entry ($).
        *   Option B: Labor (`Hours` $\times$ `Avg Rate`) + Non-Labor (`Materials/Capex`).
    *   **Total Estimated Effort:** *Crucial Input.* Must allow updating total scope to capture volatility.

### 3.2 Dashboard (The "Single Pane of Truth")
*   **Financial Cards:** CPI, SPI, EAC, **Current Value Density**.
*   **The Bridge Chart:** Dual-Axis Chart correlating Burndown (Points) with Earned Value ($).
*   **Value Density Tracker:** Trend line showing dilution over time (Scope Creep).

## 4. Technical Constraints
*   **Stack:** Python (Flask).
*   **Storage:** Local JSON (`projects.json`).
*   **Frontend:** Vanilla CSS (Glassmorphism), Chart.js.
