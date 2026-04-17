# BurnedValue — AI Developer Context

This file is the primary context document for AI-assisted development sessions.
Read this before making any changes to the codebase.

---

## What This Is

**BurnedValue** is an Earned Value Management (EVM) web application for project operators
managing government or commercial contracts. It tracks cost performance (CPI), schedule
performance (SPI), and provides AI-assisted analysis and planning.

The app is built for non-expert operators — the AI assistant is a first-class feature,
not an add-on. Operators may not read documentation; the AI guides them through workflows.

Live: `https://burned-value-demo.uc.r.appspot.com`
Domain: `https://mwooc.com` serves a separate app (mwooc-492213 GCloud project).

---

## Tech Stack

- **Backend**: Python 3.12 / Flask
- **Storage**: JSON flat files (`data/projects.json`) — no database yet
- **Frontend**: Vanilla JS, Chart.js, server-rendered Jinja2 templates
- **AI**: Anthropic Claude API (`ai_client.py`)
- **Hosting**: Google Cloud App Engine (`burned-value-demo` project)
- **Deployment**: `wsl -d Ubuntu bash -c "cd /home/matthew/BurnedValue && /home/matthew/google-cloud-sdk/bin/gcloud app deploy --project=burned-value-demo --quiet"`
- **Local dev**: `wsl -d Ubuntu bash -c "cd /home/matthew/BurnedValue && .venv/bin/flask run --host=0.0.0.0 --port=5000"`

---

## Current State (What Exists)

### Working Features
- Project CRUD (create, update, delete)
- Manual period entry: operator enters actual_cost, points_completed, scope_delta per period
- EVM dashboard: CPI, SPI, EAC, ETC, VAC, percent complete, scope coverage ratio
- BLUF (Bottom Line Up Front): AI-generated executive summary with charts
- AI chat assistant: project-aware, answers EVM analysis questions
- SPA navigation: Dashboard ↔ BLUF swap without page reload (chat pane preserved)
- Demo project: session-isolated, resettable from index page

### Storage Model (Current — JSON)
```json
{
  "id": "uuid",
  "name": "...",
  "bac": 250000,
  "start_date": "2026-02-01",
  "end_date": "2026-07-04",
  "baseline_scope": 200,
  "interval_unit": "weeks",
  "interval_size": 2,
  "periods": [
    {
      "period_id": "uuid",
      "date": "2026-02-15",
      "actual_cost": 16000,
      "points_completed": 32,
      "scope_delta": 0
    }
  ]
}
```

### Key Files
| File | Purpose |
|---|---|
| `app.py` | Flask routes |
| `models.py` | EVM calculation engine (CalculationEngine class) |
| `utils.py` | JSON storage, demo project seed |
| `ai_client.py` | Anthropic API wrapper, project context builder |
| `templates/_chat_pane.html` | AI chat pane + SPA navigation logic |
| `templates/dashboard.html` | Main EVM dashboard |
| `templates/bluf.html` | Executive summary |
| `templates/index.html` | Project listing |
| `static/css/style.css` | All styles |

---

## What Is Being Built Next

See `docs/ARCHITECTURE.md` for full design. Summary of phases:

### Phase 1 — Work Structure (Epic/Feature/Story)
New entities replacing manual period entry as the source of EV truth.
Requires migrating from JSON flat files to SQLite (SQLAlchemy).

### Phase 2 — Connect Work to EV Engine
- Story completions → points_completed (automatic)
- Scope changes → scope_delta (automatic)
- Discipline cost entries replace manual actual_cost

### Phase 3 — Gantt / WBS Schedule View
Visual release plan driven by feature points ÷ velocity. Bars computed,
not manually placed. Flags where scope won't fit POP at current staffing.

### Phase 4 — AI Planning Assistant
Story definition, acceptance criteria, replan suggestions, capacity analysis.

---

## Key Architecture Decisions

1. **Story is the atomic EV unit.** A done Story earns credit for its Feature.
   EV credit does not go below Feature level.

2. **Feature % complete = done story points / total story points.**
   Features without stories are 0% complete.

3. **Iterations = reporting periods.** One iteration = one cost report period (weekly).
   This aligns with the accounting system's charge-number reporting cadence.

4. **Staffing profile lives at project level.** Disciplines (Software, Hardware,
   Interconnects, Engineering) are defined per project with charge numbers and avg rates.
   Planned cost = planned hours × avg rate. Actual cost = dollars charged to charge number
   per period (entered from weekly cost report).

5. **Rolling wave planning.** Near iterations have defined Stories. Far iterations
   intentionally have Features only (goals, not stories). The system tracks refinement
   readiness.

6. **No individual resource tracking (yet).** Disciplines are the resource abstraction.
   Individual hour tracking is a future feature (over/undercharge analysis).

7. **Blocked is a Story/Feature attribute (flag), not a state.** The state machine is:
   New → Active → Resolved → Done.

8. **Storage migration required.** The JSON flat-file model cannot support the
   relational hierarchy needed for Phase 1. Target: SQLite via SQLAlchemy, preserving
   the existing project/period data.

---

## EVM Business Rules

See `docs/EVM_THEORY.md` for full formulas. Quick reference:

```
EV = (done_story_points / total_story_points) × BAC
PV = cumulative planned discipline cost through current date
AC = cumulative actual discipline cost (from cost reports)

CPI = EV / AC          (>1.0 = under budget)
SPI = EV / PV          (>1.0 = ahead of schedule)
EAC = BAC / CPI        (forecast final cost)
ETC = EAC - AC         (remaining work cost estimate)
VAC = BAC - EAC        (variance at completion — negative = overrun)
```

---

## DO NOT

- Break the existing demo project (session-isolated, seed in `utils.py`)
- Remove SPA navigation behavior in `_chat_pane.html`
- Store secrets in code (API keys are in environment variables / app.yaml)
- Commit or deploy without operator instruction
