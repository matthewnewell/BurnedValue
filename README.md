# BurnedValue 🚀

### **The Lovechild of EVMS and a Release Burndown**
> *"Because you want to know how fast you’re running, but also if you can actually afford the shoes."*

**BurnedValue** is a project tracking framework designed for the "real world"—where risk is high, volatility is constant, but the budget is finite. It bridges the gap between rigid government-style accounting and fluid agile delivery.

---

## 🧬 The Genealogy of BurnedValue

Traditional metrics often suffer from a "broken home" dynamic. We brought the family back together to create a metric that actually tells the truth.

### 🛡️ The Over-Protective Parent: **EVMS** (Earned Value Management)
**EVMS** is the parent who won't let you leave the house without a detailed itinerary and a receipts envelope. It treats project management as a 7th-grade math problem, providing a level of fiscal clarity that agile "management" can't touch.

**The "Parental" Toolkit:**
* **CPI (Cost Performance Index):** The "Allowance" check. Are we getting $1.00 of work for every $1.00 we spend?
* **SPI (Schedule Performance Index):** The "Curfew" check. Are we moving as fast as we promised?
* **BAC (Budget at Completion):** The "Total Piggy Bank." The hard limit on what this whole thing is allowed to cost.
* **EAC & ETC:** The "Predictive Guilt Trip." Calculating exactly how much more money you'll need (ETC) and how much over-budget you'll eventually be (EAC) if you don't change your behavior *right now*.

**The Strength:** Unmatched fiscal discipline. You always know exactly where the money went.  
**The Flaw:** It assumes the "Plan" is perfect. If the plan changes, the math breaks.

### 🎨 The Free-Spirited Parent: **Release Burndown**
The **Release Burndown** lives in the moment. It accepts that the roadmap is a living document and focuses entirely on the remaining "pile of work" (velocity).
* **The Strength:** High transparency and adaptability to massive volatility.
* **The Flaw:** Can accidentally burn through a million dollars without realizing the "value" produced doesn't actually cover the cost.

### 🧑‍💼 The Adult Child: **BurnedValue**
**BurnedValue** is the responsible offspring. It inherited the fiscal integrity of EVMS and the agility of the Burndown. 
* **The Result:** A metric that tracks the **velocity of realized ROI.** It doesn't just tell you that you're "done" with a task; it tells you how much of your business case you've actually "unlocked" relative to your spend.

---

## ✨ Key Benefits

| Feature | The "Adult Child" Logic |
| :--- | :--- |
| **Volatility Buffer** | Unlike rigid EVMS, **BurnedValue** handles scope pivots by re-calculating the *value density* of the remaining backlog. |
| **Burn-to-Budget** | Unlike a standard Burndown, we map velocity to burn rate ($/point) so you know when you'll run out of shoes. |
| **Risk-Adjusted Delivery** | Prioritizes "burning" high-risk items first, increasing the *Earned Value* earlier in the project lifecycle. |

---

## 🛠 How it Works

1.  **Define Value:** Assign a "Business Value" weight to your items (The EVMS DNA).
2.  **Track the Burn:** Measure points completed per sprint (The Burndown DNA).
3.  **Calculate BurnedValue:** $$BV = \frac{\% \text{ Value Realized}}{\% \text{ Budget Spent}}$$

*A $BV \geq 1.0$ means you are unlocking value faster than you are spending money.*

---

## 🚀 Getting Started

```bash
# Clone the repo (In your /repos folder, NOT Google Drive!)
git clone [https://github.com/yourusername/burnedvalue.git](https://github.com/yourusername/burnedvalue.git)

# Install dependencies
npm install

# Run the tracker
npm start