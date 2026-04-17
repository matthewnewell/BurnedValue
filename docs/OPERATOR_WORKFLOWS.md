# Operator Workflows

This document describes how operators use BurnedValue at each phase of a project.
It is the primary context document for the AI assistant — the AI uses this to
understand what operators are trying to accomplish and how to help them.

---

## Operator Role

An operator is a project manager, program manager, or control account manager
responsible for tracking a project's cost and schedule performance. They are
not necessarily EVM experts. The AI assistant compensates for gaps in EVM
knowledge and guides them through workflows.

---

## Workflow 1: Project Setup

**When**: New contract award or project kickoff.

**What the operator does**:
1. Creates a project (name, description, contract value, BAC, POP start/end)
2. Defines disciplines (Software, Hardware, Interconnects, Engineering)
   - Each discipline gets a charge number (from contract/accounting setup)
   - Each discipline gets an average blended rate ($/hour)
3. Sets the staffing profile: planned hours per discipline per iteration
4. Sets the iteration cadence (weekly recommended — aligns to cost report)
5. Defines the baseline scope (total feature points, even if rough at kickoff)

**AI can help with**:
- Explaining what BAC vs. contract value means
- Suggesting reasonable avg rates based on discipline type
- Flagging if planned staffing cost exceeds BAC
- Checking if POP duration is feasible given baseline scope and velocity assumption

**Output**: A project with a staffing profile and POP. Ready for release planning.

---

## Workflow 2: Release Planning

**When**: Project kickoff, or after a significant scope change.

**What the operator does**:
1. Defines Epics (major capability areas, e.g., "User Authentication", "Reporting")
2. Defines Features within each Epic (specific deliverables, feature point estimates)
3. Assigns Features to target iteration ranges (start iteration, end iteration)
4. Reviews the capacity check: total feature points vs. available capacity (velocity × iterations)
5. Resolves mismatches by adjusting scope, staffing, or dates

**Rolling wave intent**: Far-out features are rough estimates. This is intentional.
The release plan is a living document, not a contract with the future.

**AI can help with**:
- Suggesting feature breakdown from epic descriptions
- Computing capacity vs. scope feasibility
- Identifying which features can't fit in POP at current velocity
- Proposing scope priority ranking to fit within budget/schedule

**Output**: Epics and Features defined across the POP. Capacity roughly balanced.

---

## Workflow 3: Iteration Planning

**When**: 1–2 weeks before each iteration starts.

**What the operator does**:
1. Reviews the backlog: Features targeted for this iteration
2. Breaks targeted Features into Stories (if not already refined)
3. Points each Story (story points, not feature points)
4. Assigns Stories to the iteration (pulls from backlog)
5. Confirms team capacity: total story points committed vs. velocity

**Rolling wave intent**: Only refine stories for the next 2–3 iterations.
Stories beyond that should stay as Features until closer in time.

**AI can help with**:
- Breaking a Feature description into 3–8 Stories
- Writing acceptance criteria for each Story
- Checking if committed story points exceed velocity
- Flagging stories with missing acceptance criteria

**Output**: Next iteration has a full story set, pointed, and ready to execute.

---

## Workflow 4: Daily Execution (Iteration)

**When**: Throughout an active iteration.

**What the operator does**:
1. Reviews the Iteration Board (kanban: New → Active → Resolved → Done)
2. Moves Stories through status as work progresses
3. Sets blocked flag on Stories that are stalled (with reason)
4. Adds newly discovered Stories to the backlog (scope delta)
5. Communicates with team on blocked items

**AI can help with**:
- Summarizing what's blocked and why
- Suggesting resolution paths for blocked items
- Identifying stories at risk of not completing by iteration end (based on active count vs. remaining days)

**Output**: Stories completing, Feature % complete climbing, EV accruing.

---

## Workflow 5: Cost Report Entry

**When**: Weekly, after receiving cost report from accounting.

**What the operator does**:
1. Opens the cost entry form for the current iteration
2. For each discipline, enters actual dollars charged (from cost report)
   - Software: $X charged to charge number XXXX-01
   - Hardware: $Y charged to charge number XXXX-02
   - etc.
3. Reviews PV vs. AC for the period
4. Saves — the system updates EVM metrics automatically

**Source**: Weekly cost report from accounting system.
Keyed by charge number → actual dollars in period.
Individual employee hours are in the cost system but not entered here.

**AI can help with**:
- Explaining a CPI or SPI variance after cost entry
- Identifying which discipline is driving cost overrun
- Comparing this period's burn to previous periods

**Output**: AC updated. EVM metrics refresh. Dashboard reflects current performance.

---

## Workflow 6: Variance Analysis and Replanning

**When**: After cost entry, or when CPI/SPI drops below threshold.

**What the operator does**:
1. Reviews Dashboard: CPI, SPI, EAC, VAC
2. Reviews BLUF for narrative summary and risk flags
3. Identifies root cause of variance (cost? schedule? scope?)
4. Takes corrective action:
   - Scope reduction (remove or defer Features)
   - Staffing adjustment (change discipline hours in staffing profile)
   - Schedule extension (extend POP end date — requires contract action)
   - Acceptance (acknowledge overrun, no action)
5. Documents the decision

**AI can help with**:
- Diagnosing the variance ("your SPI is low because Feature X has 0 stories completed")
- Modeling replan options ("if you drop Feature Y, EAC drops by $Z")
- Drafting variance narrative for reporting

**Output**: Corrective action taken. Project reforecast updated.

---

## Workflow 7: Backlog Refinement

**When**: Mid-iteration (typically), preparing for 2+ iterations ahead.

**What the operator does**:
1. Reviews Features targeted for upcoming iterations
2. Breaks down Features that haven't been refined into Stories
3. Points stories, writes or reviews acceptance criteria
4. Reorders the backlog based on priority changes
5. Adjusts Feature point estimates if refinement reveals more/less scope

**AI can help with**:
- Suggesting story decomposition from feature descriptions
- Writing acceptance criteria
- Identifying features that are under-refined given their target iteration
- Flagging features where story points significantly exceed feature point estimate
  (scope growth signal)

**Output**: Upcoming iterations are high-fidelity and ready to plan.

---

## AI Assistant Design Intent

The AI assistant in BurnedValue is not a generic chatbot. It is a project-aware
planning partner. Its context includes:

- Full project structure (Epics, Features, Stories, status)
- EVM metrics (CPI, SPI, EAC, velocity)
- Staffing profile and cost actuals
- Open risks and blocked items

The AI should:
- Proactively surface risks without being asked
- Guide operators through workflows they haven't done before
- Help operators who don't know EVM terminology
- Offer concrete action suggestions, not just analysis
- Be able to take actions on behalf of the operator
  (mark story done, create story, update estimate) — Phase 4

The AI should NOT:
- Give generic project management advice unrelated to this project's data
- Require the operator to understand EVM formulas
- Wait to be asked before flagging a problem
