# Data Model

---

## Storage Migration

**Current**: JSON flat files (`data/projects.json`)
**Target**: SQLite via SQLAlchemy (required for Phase 1 relational hierarchy)

The migration must preserve existing project and period data.
The demo project seed in `utils.py` must continue to function.

---

## Current Model (JSON — in production today)

```
Project {
    id:               string (uuid or "demo")
    name:             string
    description:      string
    is_demo:          bool
    bac:              float   — Budget at Completion
    contract_value:   float   — optional, for margin tracking
    start_date:       date    — POP start
    end_date:         date    — POP end
    baseline_scope:   float   — original story/feature points at project start
    interval_unit:    string  — "weeks" | "days" | "months"
    interval_size:    int     — e.g., 2 (bi-weekly periods)

    periods: [Period]
}

Period {
    period_id:          string (uuid)
    date:               date
    actual_cost:        float  — total actual cost, manually entered
    points_completed:   float  — manually entered
    scope_delta:        float  — manually entered, change in total scope
    labor_hours:        float  — informational only
    labor_rate:         float  — informational only
    non_labor_cost:     float  — informational only
}
```

---

## Target Model (SQLAlchemy — Phase 1+)

### Project
```
Project
    id:               UUID (PK)
    name:             string
    description:      text
    is_demo:          bool
    bac:              float
    contract_value:   float (nullable)
    start_date:       date
    end_date:         date
    baseline_scope:   float   — total feature points at project kickoff
    interval_unit:    string  — "weeks" (aligns to accounting report cadence)
    interval_size:    int     — typically 1 (weekly)
    created_at:       datetime

    → disciplines[]
    → epics[]
    → iterations[]
```

### Discipline (charge code / staffing)
```
Discipline
    id:                       UUID (PK)
    project_id:               FK → Project
    name:                     string  — e.g., "Software", "Hardware"
    charge_number:            string  — maps to accounting charge code
    avg_rate:                 float   — blended $/hour
    planned_hours_per_period: float   — from staffing profile

    → discipline_actuals[]

Computed:
    planned_cost_per_period = planned_hours_per_period × avg_rate
```

### Iteration (= reporting period, aligned to weekly cost report)
```
Iteration
    id:             UUID (PK)
    project_id:     FK → Project
    number:         int     — sequential (1, 2, 3...)
    start_date:     date
    end_date:       date
    goal:           text    — high-level intent for this iteration

    → discipline_actuals[]
    → stories[]

Computed:
    planned_cost = sum(discipline.planned_cost_per_period for all disciplines)
    actual_cost  = sum(discipline_actuals.actual_dollars)
    points_completed = sum(story.story_points where story.status = 'done')
    scope_delta  = sum(story.story_points added/removed this iteration)
```

### DisciplineActual (cost report entry)
```
DisciplineActual
    id:                    UUID (PK)
    iteration_id:          FK → Iteration
    discipline_id:         FK → Discipline
    actual_dollars_charged: float  — from weekly accounting cost report
    entered_at:            datetime
    notes:                 text (nullable)
```

### Epic
```
Epic
    id:           UUID (PK)
    project_id:   FK → Project
    name:         string
    description:  text
    order:        int     — display ordering

    → features[]

Computed:
    total_feature_points = sum(feature.feature_points)
    earned_feature_points = sum(feature.earned_feature_points)
    percent_complete = earned_feature_points / total_feature_points
```

### Feature
```
Feature
    id:                    UUID (PK)
    epic_id:               FK → Epic
    name:                  string
    description:           text
    feature_points:        float   — release-level estimate (coarse)
    target_start_iter:     int     — target iteration number to start
    target_end_iter:       int     — target iteration number to complete
    status:                enum    — planned | refined | active | complete
    blocked:               bool
    blocked_reason:        text (nullable)
    order:                 int

    → stories[]

Computed:
    total_story_points = sum(story.story_points)
    done_story_points  = sum(story.story_points where status = 'done')
    percent_complete   = done_story_points / total_story_points  (0 if no stories)
    earned_feature_points = feature_points × percent_complete
    refinement_ratio   = total_story_points / feature_points
        (0 = unrefined, ~1 = fully broken down, >1 = scope grew in refinement)
```

### Story
```
Story
    id:                UUID (PK)
    feature_id:        FK → Feature
    iteration_id:      FK → Iteration (nullable — backlog if null)
    name:              string
    description:       text
    acceptance_criteria: text
    story_points:      float
    status:            enum  — new | active | resolved | done
    blocked:           bool
    blocked_reason:    text (nullable)
    order:             int
    created_at:        datetime
    completed_at:      datetime (nullable — set when status → done)

    → tasks[]  (deferred)
```

### Task (deferred — stub for future)
```
Task
    id:           UUID (PK)
    story_id:     FK → Story
    name:         string
    status:       enum  — new | active | resolved | done
    assignee:     string (nullable — deferred)
    order:        int
```

---

## EV Flow Diagram

```
Story.status = 'done'
    → credits Story.story_points to Feature

Feature.percent_complete = done_story_points / total_story_points
Feature.earned_feature_points = Feature.feature_points × pct_complete

Epic.earned_fp = Σ Feature.earned_feature_points
Epic.pct_complete = Epic.earned_fp / Epic.total_feature_points

Project.total_earned_fp = Σ Epic.earned_fp
Project.pct_complete = total_earned_fp / baseline_scope (+ scope_deltas)
Project.EV = pct_complete × BAC

Project.PV = Σ (Discipline.planned_cost_per_period) through current iteration
Project.AC = Σ DisciplineActual.actual_dollars through current iteration
```

---

## Key Constraints and Rules

- A Feature without Stories is 0% complete (no EV credit)
- Story points do NOT have to equal Feature points (refinement may reveal more/less scope)
- Scope delta is auto-computed when stories are added to or removed from an iteration
- Blocked is a flag (attribute), NOT a status — a blocked story still has a status
- Completing a Story sets completed_at timestamp (used for velocity trending)
- An Iteration is "closed" when cost report entry is complete — stories can still be moved after close but EV snapshot is taken at close time (future: audit log)
