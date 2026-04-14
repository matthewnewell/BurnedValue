# Burned Value 🚀

### **Earned Value Management + Agile Release Burndown Lovechild**

**Burned Value** is an experiment in project governance for unpredictable projects. By combining EVMS's fiscal discipline with Burndown's agility, we ensure every dollar is an intentional investment in the right outcomes—navigating constant volatility while keeping delivery anchored to contractual intent and true value.  

We use the **Agile Release Burndown** as **Quantifiable Backup Data (QBD)** to drive EVMS calculations. It replaces "Manager Guesses" with "Working Software" (Points). 

---



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



### 📊 Percent Complete
$$ \text{Percent Complete} = \frac{\text{Completed Points}}{\text{Total Scope Points}} $$

$$ \text{Earned Value (EV)} = \text{Percent Complete} \times \text{Budget at Completion (BAC)} $$

If you spend 50% of your budget but have only finished 10% of your Story Points, **Burned Value** shows a **CPI of 0.2**. No hiding.

---

### 💎 Value Density - price per point

**Value Density** is the "Exchange Rate" between estimated Effort (Points) and your Budget.

$$ \text{Value Density} = \frac{\text{Total Budget (BAC)}}{\text{Total Estimated Effort (Points)}} $$

It answers the question: **"How much Earned Value do I unlock for every Story Point I complete?"**

### 🌪️ The "Volatility" Effect
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

### ⚖️ Scope-Value Trade-off
Unfunded scope is a mathematical dilution of value; maintaining project integrity requires a deliberate choice between budget, timeline, or trade-offs.

* **Fund the Scope:** Increase the budget to maintain **Value Density** and keep the project on track.
* **Reject the Change:** Maintain the current budget and schedule by keeping the scope locked to the original agreement.
* **Accept the Variance:** Acknowledge that the project will now result in a budget overrun and a slipped schedule as a mathematical certainty.
* **Increase Velocity:** Bet on a sudden, sustained increase in team output.   
*Velocity is a trailing indicator of team health, not a dial that can be turned on command. This is almost never a viable recovery strategy.*

By unifying budget, scope, and velocity into a single source of truth, the BurnedValue dashboard provides the visibility necessary for leadership to move beyond guesswork and make effective, data-driven decisions.

---

## Deployment

### Local Development
```bash
pip install -r requirements.txt
python app.py
# Visit http://localhost:8080
```

### Google App Engine (Cloud)
```bash
gcloud app deploy --project burned-value-demo
```
Live at: `https://burned-value-demo.uc.r.appspot.com`

---

### Docker (On-Premise / Behind Firewall)

**Requirements:** Docker Desktop or Docker Engine + Docker Compose

#### Quick Start
```bash
git clone https://github.com/matthewnewell/BurnedValue.git
cd BurnedValue
docker compose up -d
# Visit http://localhost:8080
```

Project data is stored in `./data/projects.json` on your host machine and persists across container restarts.

#### AI Integration

Burned Value supports pluggable AI backends via environment variables. Edit `docker-compose.yml` to configure:

**Option A — Claude (Anthropic cloud):**
```yaml
environment:
  AI_PROVIDER: "claude"
  AI_MODEL: "claude-opus-4-5"
  AI_API_KEY: "sk-ant-..."
```

**Option B — Ollama (on-premise LLM):**
```yaml
environment:
  AI_PROVIDER: "ollama"
  AI_BASE_URL: "http://your-ollama-host:11434"
  AI_MODEL: "llama3"
```

**Option C — No AI (default):**
```yaml
environment:
  AI_PROVIDER: "none"
```
All core EVM/burndown features work without AI. AI features will be disabled but the app runs fully.

#### Production Notes
- Change `SECRET_KEY` in `docker-compose.yml` before deploying
- To expose on your network: change `"8080:8080"` to `"0.0.0.0:8080:8080"` or put Nginx in front
- To update: `git pull && docker compose up -d --build`