# Architecture

---

## System Overview

BurnedValue is a web-based EVM (Earned Value Management) application for project
operators. It has two primary user-facing roles:

- **Operator**: defines work, manages execution, enters cost data, reviews performance
- **AI Assistant**: embedded in every view, context-aware, guides operators through
  workflows, provides analysis and planning support

The system is intentionally operator-facing (not a large multi-user enterprise tool).
It is designed to be used by a small team managing one or more contracts.

---

## Current Architecture

```
Browser
  └── Jinja2 templates (server-rendered HTML)
       ├── Vanilla JS (Chart.js, SPA navigation)
       └── AI Chat Pane (persistent across SPA navigations)

Flask App (app.py)
  ├── Routes → render_template
  ├── CalculationEngine (models.py) — pure EVM math
  ├── Storage layer (utils.py) — JSON flat files
  └── AI client (ai_client.py) — Anthropic API

Data: data/projects.json (flat file, no database)
Hosting: Google Cloud App Engine (burned-value-demo)
```

### SPA Navigation
Dashboard and BLUF pages use SPA navigation (`data-spa` links) to swap `.content`
innerHTML without a full page reload. The AI chat pane lives outside `.content` and
persists across navigations. See `templates/_chat_pane.html`.

---

## Target Architecture (Phase 1+)

```
Browser
  └── Jinja2 templates
       ├── Chart.js (EVM charts, Gantt — Phase 3)
       ├── Kanban board (Phase 2)
       └── AI Chat Pane (enhanced with planning context)

Flask App
  ├── Routes (app.py)
  ├── CalculationEngine (models.py) — extended for new EV flow
  ├── SQLAlchemy ORM (new: db.py)
  ├── AI client (ai_client.py) — extended with planning workflows
  └── Cost report ingestion

Data: SQLite (development) / Cloud SQL (production consideration)
```

---

## Module Descriptions

### Module 0 — EVM Engine (exists today)
Core calculation engine. Inputs: project, periods. Outputs: CPI, SPI, EAC, etc.
Will be refactored in Phase 2 to accept the new entity model as input.

### Module 1 — Work Structure
**Epic → Feature → Story → Task** hierarchy.

Responsibilities:
- Operator defines Epics and Features (release planning)
- Operator refines Features into Stories (iteration planning — rolling wave)
- Stories move through status: New → Active → Resolved → Done
- Story completions automatically update Feature % complete and EV
- Blocked flag on Stories and Features surfaces as risk indicators

Key views:
- **Backlog**: all stories across features, filterable by iteration/epic/status
- **Iteration Board**: kanban view for current iteration stories
- **Release Plan**: features laid out across iterations with point estimates
- **Feature Detail**: stories within a feature, refinement status

### Module 2 — WBS / Gantt Schedule (Phase 3)
Visual release plan. Bars are computed from feature points ÷ velocity, not manually placed.

WBS levels:
- Level 1: Project
- Level 2: Epic
- Level 3: Feature
- Level 4: Story (rolled up, not individually displayed on Gantt)

Key behaviors:
- Bar duration = feature_points / team_velocity (in iterations)
- Operator can set target start/end iterations — system flags if scope won't fit
- Dependencies between features shown as risk/blocker indicators
- Critical path: deferred to future phase

The core planning tension surfaced by Module 2:
> "Feature X has 100 feature points. At current velocity (50 pts/iteration),
> it requires 2 iterations. Your target is 1 iteration. Risk flag."

### AI Planning Assistant (Phase 4, but groundwork in all phases)
The AI assistant becomes increasingly capable as data matures:

| Phase | AI Can Do |
|---|---|
| Today | Analyze EVM metrics, answer questions about project health |
| Phase 1 | Help define Stories, write acceptance criteria, suggest story splitting |
| Phase 2 | Flag capacity mismatches, identify blocked dependencies |
| Phase 3 | Replan suggestions (drop scope, extend date, increase velocity) |
| Phase 4 | Full planning partner: story generation, backlog refinement facilitation |

---

## Build Phases

### Phase 1 — Work Structure
- Database migration: JSON → SQLite/SQLAlchemy
- New entities: Discipline, Iteration, Epic, Feature, Story
- Project setup flow: add disciplines + staffing profile
- Release planning view: Epics/Features with point estimates
- Iteration allocation: drag/assign stories to iterations

### Phase 2 — EV Goes Live
- Story completion → automatic points_completed
- Scope changes → automatic scope_delta
- Weekly cost report entry (DisciplineActual per iteration)
- Retire manual period entry form
- Dashboard and BLUF driven by real work data

### Phase 3 — Gantt / WBS
- Visual release plan with computed bars
- Velocity-driven scheduling
- Capacity mismatch flags
- Feature dependency visualization

### Phase 4 — AI Planning Assistant
- Story definition and acceptance criteria generation
- Backlog refinement facilitation
- Replan suggestions
- Natural language data entry ("mark Story X as done")

---

## Integration Points

### Accounting System (Cost Reports)
- **Today**: operator manually enters actual dollars per discipline per iteration
- **Future**: API integration with cost accounting system
- **Seam**: `DisciplineActual` table, keyed by charge_number + period date
- Individual employee hours exist in cost system but are not consumed today
  (future: over/undercharge detection)

### Version Control / Project History
- No audit log today
- Phase 2 consideration: snapshot EV state at iteration close

---

## Design Principles

1. **Operator-first UX**: The system guides operators; operators don't fight the system.
2. **AI as co-pilot**: Every view should have an AI entry point. The AI knows the context.
3. **Rolling wave by design**: The system expects far iterations to be undefined.
   Undefined is not an error state — it is the plan.
4. **Computed over manual**: Whenever a value can be derived from work data, derive it.
   Manual entry is a last resort (currently: actual cost dollars).
5. **Fail visible**: Capacity mismatches, blocked items, and off-track features are
   surfaced proactively, not buried in reports.
6. **No individual tracking (yet)**: Disciplines are the resource abstraction boundary.
   Individual hours stay in the accounting system.
