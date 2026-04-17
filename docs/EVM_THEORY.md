# EVM Theory of Operations

This document defines the Earned Value Management model used by BurnedValue.
It is the authoritative reference for all calculation logic.

---

## What is EVM?

Earned Value Management is a project performance measurement technique that
integrates scope, schedule, and cost into a single quantitative framework.
It answers three questions at any point in time:

1. **How much work was planned?** (Planned Value)
2. **How much work was actually done?** (Earned Value)
3. **How much did the work cost?** (Actual Cost)

From these three numbers, all performance indices and forecasts are derived.

---

## The Three Pillars

### Planned Value (PV)
The authorized budget for work scheduled to be completed by a given date.

```
PV at time T = cumulative planned discipline cost through period T
             = sum(discipline.planned_hours_per_period × discipline.avg_rate)
               for all periods up to and including T
```

### Earned Value (EV)
The authorized budget for work actually completed, regardless of actual cost.

```
EV = percent_complete × BAC

percent_complete = earned_feature_points / total_feature_points

earned_feature_points = sum over all features:
    feature.feature_points × feature.percent_complete

feature.percent_complete = done_story_points / total_story_points
    (0% if no stories exist for the feature)
```

### Actual Cost (AC)
Total cost actually incurred for work performed in a given period.

```
AC for a period = sum of actual_dollars_charged per discipline
                  (entered from weekly accounting cost report)

Cumulative AC = sum of all period ACs to date
```

---

## Performance Indices

### Cost Performance Index (CPI)
```
CPI = EV / AC

CPI > 1.0  → Under budget (good)
CPI = 1.0  → On budget
CPI < 1.0  → Over budget (bad)
```

### Schedule Performance Index (SPI)
```
SPI = EV / PV

SPI > 1.0  → Ahead of schedule (good)
SPI = 1.0  → On schedule
SPI < 1.0  → Behind schedule (bad)
```

---

## Forecasts

### Estimate at Completion (EAC)
Forecast of the total cost of the project at completion.
```
EAC = BAC / CPI
```

### Estimate to Complete (ETC)
How much more money is needed to finish the project.
```
ETC = EAC - AC
```

### Variance at Completion (VAC)
Projected overrun (negative) or underrun (positive) at completion.
```
VAC = BAC - EAC
```

### To-Complete Performance Index (TCPI)
The CPI that must be sustained for the remainder of the project to meet BAC.
```
TCPI = (BAC - EV) / (BAC - AC)
```

---

## Budget at Completion (BAC)

BAC is the total authorized budget for the project. It is set at project creation
and represents the total planned value of all work.

```
BAC = total_feature_points × budget_per_point

budget_per_point = BAC / total_feature_points  (derived, used for display)
```

BAC does NOT change unless a formal rebaseline occurs (scope change + budget change).
Scope changes (scope_delta) affect total_feature_points but not BAC unless rebaselined.

---

## EV Flow — Bottom Up

EV credit originates at the Story level and rolls up through the hierarchy:

```
Task (deferred — not an EV unit)
  ↑
Story  ←  status = Done  →  credits story_points to parent Feature
  ↑
Feature  ←  pct_complete = done_story_pts / total_story_pts
          ←  earned_fp = feature_points × pct_complete
  ↑
Epic  ←  earned_fp = sum(feature.earned_fp)
       ←  pct_complete = sum(feature.earned_fp) / sum(feature.feature_points)
  ↑
Project  ←  total_earned_fp = sum(epic.earned_fp)
          ←  pct_complete = total_earned_fp / total_feature_points
          ←  EV = pct_complete × BAC
```

**Key rule:** A Feature with no Stories is 0% complete. EV credit requires defined
and completed Stories.

**Key rule:** Story is the atomic unit of EV credit. Partial task completion
within a Story does not earn partial EV. A Story is either Done or not.

---

## Two-Tier Planning Model

### Release Plan (Program Increment Level)
- Horizon: full Period of Performance (POP)
- Units: Feature Points (coarse estimates)
- Purpose: feasibility — can we do this scope in this time with this staffing?
- Output: staffing profile, velocity targets, budget allocation per Epic

### Iteration Plan (Sprint Level)
- Horizon: 1–3 iterations (rolling wave)
- Units: Story Points (refined estimates)
- Purpose: execution — what do we build this sprint?
- Output: stories allocated to iteration, team capacity commitment

The ratio of story points to feature points (refinement ratio) is tracked per Feature.
Near iterations are fully refined. Far iterations are intentionally vague
(Goals and Features defined, Stories not yet written).

---

## Staffing / Discipline Cost Model

Labor cost is tracked by discipline (charge code), not by individual.

### Disciplines
Defined at project level. Each discipline has:
- `name`: e.g., Software, Hardware, Interconnects, Engineering
- `charge_number`: maps to accounting system charge code
- `avg_rate`: blended hourly rate for this discipline ($/hour)
- `planned_hours_per_period`: from staffing profile

### Planned Value (PV) Computation
```
PV for period = sum over disciplines:
    discipline.planned_hours_per_period × discipline.avg_rate
```

### Actual Cost (AC) Input
Weekly cost report from accounting provides:
- Charge number
- Actual dollars charged in the period

Operator enters actual dollars per discipline per period.
Individual employee hours are not tracked at this time.

### Velocity and Capacity
```
team_velocity = story_points_completed / iteration  (rolling average)

capacity_check = (total_story_points_remaining / team_velocity) vs. iterations_remaining

feature_feasibility:
    required_velocity = feature.story_points / target_duration_in_iterations
    if required_velocity > team_velocity → RISK FLAG
```

---

## Scope Change Handling

When a Feature is added, removed, or re-pointed after project start:
- `scope_delta` = change in total feature points for that period
- `total_feature_points` = baseline_scope + sum(scope_delta)
- BAC is unchanged unless a formal rebaseline is approved
- Scope Coverage Ratio = baseline_scope / current_total_feature_points
  (indicates how much of current scope was covered by original budget)

---

## BLUF (Bottom Line Up Front)

An AI-generated executive summary computed on demand. Contains:
- RAG status (Red/Amber/Green) based on CPI and SPI thresholds
- Verdict narrative (AI-generated)
- Key metrics strip: % complete, CPI, SPI, EAC, schedule slip
- Cost & budget narrative
- Schedule narrative
- Scope integrity summary
- Risks and recommended actions

RAG thresholds:
```
Green:  CPI >= 1.0 AND SPI >= 1.0
Yellow: CPI >= 0.9 OR SPI >= 0.9  (either is marginal)
Red:    CPI < 0.9 OR SPI < 0.9   (either is critical)
```
