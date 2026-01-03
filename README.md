# Burned Value 🚀

### **The Lovechild of EVMS and a Release Burndown**

**Burned Value** is project governance for the unpredictable. By combining fiscal discipline with agile flexibility, we ensure every dollar is an intentional investment in the right outcomes—navigating constant volatility while keeping delivery anchored to contractual intent and true value.  

It uses the **Agile Release Burndown** as the **Quantifiable Backup Data (QBD)** to strictly drive EVMS calculations. It replaces "Manager Guesses" with "Working Software" (Points) as the only measure of Earned Value. 

---

## 🧬 The Genealogy


### 🛡️ The Over-Protective Parent: **EVMS** (Earned Value Management)
**EVMS** is the parent who won't let you leave the house without a detailed itinerary and a receipts envelope.
*   **The Strength:** Unmatched fiscal discipline. You always know exactly where the money went (CPI/SPI/BAC).
*   **The Flaw (The Liar's Percent):** It relies on a subjective "Percent Complete." If the PM *guesses* they are 50% done, EVMS cheerfully reports you are on budget—right up until you aren't.

### 🎨 The Free-Spirited Parent: **Release Burndown**
The **Release Burndown** lives in the moment. It accepts that the roadmap is a living document.
*   **The Strength:** High transparency and adaptability. Tracks *real* work (Points/Velocity).
*   **The Flaw:** Can accidentally burn through a million dollars without realizing the "velocity" produced doesn't actually cover the cost.

### 🧑‍💼 The Adult Child: **Burned Value**
**Burned Value** is the responsible offspring. It inherited the fiscal integrity of EVMS and the honesty of the Burndown.

In other words, 

$$ \text{Percent Complete} = \frac{\text{Completed Points}}{\text{Total Scope Points}} $$

$$ \text{Earned Value (EV)} = \text{Percent Complete} \times \text{Budget at Completion (BAC)} $$

If you spend 50% of your budget but have only finished 10% of your Story Points, **Burned Value** shows a **CPI of 0.2**. No hiding.

---

## � Value Density

**Value Density** is the "Exchange Rate" between estimated Effort (Points) and your Budget.

$$ \text{Value Density} = \frac{\text{Total Budget (BAC)}}{\text{Total Estimated Effort (Points)}} $$

It answers the question: **"How much Earned Value do I unlock for every Story Point I complete?"**

### The "Volatility" Effect
Without a real-time link between budget and scope, the cost of additional work remains hidden until the point of financial exhaustion. In **Burned Value**, scope creep immediately dilutes your Value Density.

**Example:**
*   You have **$100,000** and **100 Points**.
*   **Value Density = $1,000 / point.** (Every point you finish earns you $1,000 in value).

**Scenario: Scope Creep**
*   You add **50 Points** of new features (Total 150), but the Budget stays **$100,000**.
*   **New Value Density = $666 / point.**

**The Consequence: Dilution of Value**  
When scope increases without a budget adjustment, your work is instantly "worth less." To earn the same $1,000 of Value, you must now deliver 1.5 points of effort. Your CPI (Cost Performance Index) craters because you are burning resources to unlock "diluted" value.

Value Density replaces optimistic "hope" with fiscal reality. Unless velocity scales perfectly with scope, you have created a mathematical gap that cannot be closed through effort alone.

### The Scope-Value Trade-off
Unfunded scope is a mathematical dilution of value; maintaining project integrity requires a deliberate choice between budget, timeline, or trade-offs.

* **Fund the Scope:** Increase the budget to maintain **Value Density** and keep the project on track.
* **Reject the Change:** Maintain the current budget and schedule by keeping the scope locked to the original agreement.
* **Accept the Variance:** Acknowledge that the project will now result in a budget overrun and a slipped schedule as a mathematical certainty.
* **Increase Velocity:** Bet on a sudden, sustained increase in team output.   
*Velocity is a trailing indicator of team health, not a dial that can be turned on command. This is almost never a viable recovery strategy.*

---

## ✨ Key Features

*   **Financials:** The full EVMS suite (CPI, SPI, EAC) driven by real velocity.
*   **Volatility Buffer:** Handles scope pivots by re-calculating the value density of the remaining backlog.
*   **QBD "Bridge:** A dual-axis chart correlating Burndown with Earned Value. 
*   **Input:** Supports manual entry or hooks for JSON/CSV imports.
*   **Scope Volatility:** Handles adding/removing points from the backlog without breaking the financial model (re-baselining).
