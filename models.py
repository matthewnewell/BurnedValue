from datetime import datetime, timedelta

class CalculationEngine:
    @staticmethod
    def compute_metrics(project, periods):
        """
        Core EVM logic. Aggregates period data to calculate current financial health.
        """
        if not periods:
            return {
                "ev": 0, "ac": 0, "pv": 0,
                "cpi": 0, "spi": 0, "eac": 0,
                "bac": project['bac'],
                "scope_coverage_ratio": 100.0,
                "budget_per_point": 0,
                "actual_cost_per_point": 0,
                "avg_velocity": 0,
                "percent_complete": 0,
                "completed_points": 0,
                "total_scope": 0
            }

        sorted_periods = sorted(periods, key=lambda x: x['date'])

        total_ac = sum(p['actual_cost'] for p in sorted_periods)
        total_points_completed = sum(p['points_completed'] for p in sorted_periods)

        baseline = project.get('baseline_scope', 0.0) or 0.0
        current_total_scope = baseline + sum(p.get('scope_delta', 0.0) for p in sorted_periods)
        if current_total_scope <= 0:
            return {
                "ev": 0, "ac": total_ac, "pv": 0,
                "cpi": 0, "spi": 0, "eac": 0,
                "bac": project['bac'],
                "scope_coverage_ratio": 0.0,
                "budget_per_point": 0,
                "actual_cost_per_point": 0,
                "avg_velocity": round(total_points_completed / len(sorted_periods), 1),
                "percent_complete": 0,
                "completed_points": total_points_completed,
                "total_scope": 0
            }

        # Scope Coverage Ratio: percentage of current scope covered by original budget
        baseline_scope = project.get('baseline_scope') or current_total_scope
        scope_coverage_ratio = round((baseline_scope / current_total_scope) * 100, 1)
        # budget_per_point: non-user-facing, BAC / total scope (formerly "value_density")
        budget_per_point = project['bac'] / current_total_scope

        # Earned Value
        percent_complete = total_points_completed / current_total_scope
        ev = percent_complete * project['bac']

        # Planned Value — linear projection from start to end
        try:
            start_date = datetime.strptime(project['start_date'], '%Y-%m-%d')
            end_date = datetime.strptime(project['end_date'], '%Y-%m-%d')
        except ValueError:
            start_date = datetime.now()
            end_date = datetime.now()

        # PV at the last period date — consistent with EV which is also cumulative to that point
        last_period_date = datetime.strptime(sorted_periods[-1]['date'], '%Y-%m-%d')
        total_duration = (end_date - start_date).total_seconds()
        elapsed = (last_period_date - start_date).total_seconds()

        if elapsed < 0:
            planned_percent = 0
        elif elapsed > total_duration or total_duration == 0:
            planned_percent = 1.0
        else:
            planned_percent = elapsed / total_duration

        pv = planned_percent * project['bac']

        cpi = ev / total_ac if total_ac > 0 else 0.0
        spi = ev / pv if pv > 0 else 0.0
        eac = project['bac'] / cpi if cpi > 0 else project['bac']

        return {
            "ev": round(ev, 2),
            "ac": round(total_ac, 2),
            "pv": round(pv, 2),
            "cpi": round(cpi, 2),
            "spi": round(spi, 2),
            "eac": round(eac, 2),
            "bac": project['bac'],
            "scope_coverage_ratio": scope_coverage_ratio,
            "budget_per_point": round(budget_per_point, 2),
            "actual_cost_per_point": round(total_ac / total_points_completed, 2) if total_points_completed > 0 else 0,
            "avg_velocity": round(total_points_completed / len(sorted_periods), 1),
            "percent_complete": round(percent_complete * 100, 1),
            "completed_points": total_points_completed,
            "total_scope": current_total_scope
        }

    @staticmethod
    def compute_period_details(project, periods):
        """
        Returns per-period cumulative metrics for the history table.
        Flags rows where scope changed (scope creep events).
        """
        if not periods:
            return []

        sorted_periods = sorted(periods, key=lambda x: x['date'])
        details = []
        cum_ac = 0.0
        cum_points = 0.0

        baseline = project.get('baseline_scope', 0.0) or 0.0
        running_scope = baseline

        for i, p in enumerate(sorted_periods):
            running_scope += p.get('scope_delta', 0.0)
            cum_ac += p['actual_cost']
            cum_points += p['points_completed']
            scope = running_scope if running_scope > 0 else None
            if scope is None:
                details.append({'period': p, 'scope_warning': True})
                continue

            percent = cum_points / scope
            ev = percent * project['bac']
            cpi = round(ev / cum_ac, 2) if cum_ac > 0 else 0
            baseline_scope = project.get('baseline_scope') or scope
            scope_coverage_ratio = round((baseline_scope / scope) * 100, 1)
            budget_per_point = round(project['bac'] / scope, 2)

            scope_delta = p.get('scope_delta', 0.0)
            scope_changed = scope_delta != 0

            details.append({
                'period_id': p.get('period_id', ''),
                'date': p['date'],
                'period_points': p['points_completed'],
                'cum_points': cum_points,
                'scope': scope,
                'scope_delta': scope_delta,
                'scope_changed': scope_changed,
                'scope_coverage_ratio': scope_coverage_ratio,
                'budget_per_point': budget_per_point,
                'period_ac': p['actual_cost'],
                'cum_ac': round(cum_ac, 2),
                'ev': round(ev, 2),
                'cpi': cpi
            })

        return details

    @staticmethod
    def _project_finish(project, sorted_periods, avg_velocity):
        """
        Mirrors the burndown chart forecast exactly:
        projects finish date using remaining scope / avg velocity,
        advancing by one interval at a time from the last period date.
        Returns (projected_end datetime, days_slip int) or (None, 0) on error.
        """
        try:
            interval_unit = project.get('interval_unit', 'weeks')
            interval_size = int(project.get('interval_size', 2))
            if interval_unit == 'months':
                interval_days = interval_size * 30
            elif interval_unit == 'weeks':
                interval_days = interval_size * 7
            else:
                interval_days = interval_size

            cum_pts       = sum(p['points_completed'] for p in sorted_periods)
            baseline_scope = project.get('baseline_scope', 0.0) or 0.0
            last_scope = baseline_scope + sum(p.get('scope_delta', 0.0) for p in sorted_periods)
            remaining     = last_scope - cum_pts
            last_dt       = datetime.strptime(sorted_periods[-1]['date'], '%Y-%m-%d')
            end_dt        = datetime.strptime(project['end_date'], '%Y-%m-%d')

            if avg_velocity <= 0 or remaining <= 0:
                return end_dt, 0

            intervals_needed  = remaining / avg_velocity
            projected_end     = last_dt + timedelta(days=intervals_needed * interval_days)
            days_slip         = (projected_end - end_dt).days
            return projected_end, days_slip
        except (ValueError, KeyError, ZeroDivisionError):
            return None, 0

    @staticmethod
    def generate_glimpse(project, periods, metrics):
        """
        Produces a 2–3 sentence executive Glimpse summary.
        Fully rule-based — no AI endpoint required.
        Covers CPI, SPI with days-late quantification, Scope Coverage Ratio,
        and EAC vs Contract Value (or BAC when no Contract Value is set).
        """
        if not periods or metrics['cpi'] == 0:
            return None

        sorted_periods = sorted(periods, key=lambda x: x['date'])
        cpi  = metrics['cpi']
        spi  = metrics['spi']
        bac  = project['bac']
        eac  = metrics['eac']
        cv   = project.get('contract_value')
        scr  = metrics['scope_coverage_ratio']
        baseline_scope = project.get('baseline_scope', 0) or 0
        total_scope    = metrics['total_scope']
        unfunded_pts   = max(0, int(round(total_scope - baseline_scope)))

        # Schedule projection (same math as burndown chart)
        projected_end, days_slip = CalculationEngine._project_finish(
            project, sorted_periods, metrics['avg_velocity']
        )
        try:
            end_dt = datetime.strptime(project['end_date'], '%Y-%m-%d')
            planned_end_str = end_dt.strftime('%m/%d/%Y')
        except (ValueError, KeyError):
            planned_end_str = None
        projected_end_str = projected_end.strftime('%m/%d/%Y') if projected_end else None

        # ── Sentence 1: Cost + Schedule ──────────────────────────────────
        cost_word = 'under' if cpi >= 1.0 else 'over'
        if days_slip > 0:
            sched_clause = f"running {days_slip} days late (SPI {spi})"
        elif days_slip < 0:
            sched_clause = f"running {abs(days_slip)} days early (SPI {spi})"
        else:
            sched_clause = f"on schedule (SPI {spi})"

        s1 = (f"Project is {cost_word} Budget at Completion (BAC) with a CPI of {cpi} "
              f"and {sched_clause}.")

        # ── Sentence 2: Scope Coverage Ratio ─────────────────────────────
        if unfunded_pts > 0:
            s2 = (f"Scope Coverage Ratio is {scr}% — only {scr}% of the current "
                  f"{int(total_scope)}-point scope is funded by the original BAC of "
                  f"${bac:,.0f}; the remaining {unfunded_pts} points represent "
                  f"uncompensated scope growth.")
        else:
            s2 = (f"Scope Coverage Ratio is 100% — all {int(total_scope)} points are "
                  f"funded by the original BAC of ${bac:,.0f}; no uncompensated scope growth.")

        # ── Sentence 3: EAC vs Contract Value (or BAC) ───────────────────
        if cv:
            diff = abs(round(eac - cv, 0))
            rel  = 'under' if eac <= cv else 'over'
            s3   = (f"EAC is ${eac:,.0f}, which is {rel} the Contract Value of "
                    f"${cv:,.0f} by ${diff:,.0f}.")
        else:
            diff = abs(round(eac - bac, 0))
            rel  = 'under' if eac <= bac else 'over'
            s3   = f"EAC is ${eac:,.0f}, {rel} the BAC of ${bac:,.0f} by ${diff:,.0f}."

        # ── Overall status for colour coding ─────────────────────────────
        if cpi >= 1.0 and spi >= 1.0:
            status = 'success'
        elif cpi >= 0.9 and spi >= 0.9:
            status = 'warning'
        else:
            status = 'danger'

        return {
            'status':            status,
            'sentences':         [s1, s2, s3],
            'days_slip':         days_slip,
            'projected_end_str': projected_end_str,
            'planned_end_str':   planned_end_str,
        }
    @staticmethod
    def _scope_creep_events(project, sorted_periods):
        """
        Returns list of scope creep events (periods where scope_delta > 0).
        Each entry: {date, added (int pts), pct (% of scope at that point)}.
        """
        events = []
        running_scope = project.get('baseline_scope', 0.0) or 0.0
        for p in sorted_periods:
            delta = p.get('scope_delta', 0.0)
            if delta > 0:
                events.append({
                    'date':  p['date'],
                    'added': int(delta),
                    'pct':   round(delta / running_scope * 100, 1) if running_scope > 0 else 0,
                })
            running_scope += delta
        return events

    @staticmethod
    def _cpi_trend(project, sorted_periods):
        """
        Returns 'improving', 'degrading', or 'stable' based on the last 3 cumulative CPIs.
        Uses cumulative (not period) CPI to match the BLUF chart.
        """
        bac = project['bac']
        baseline = project.get('baseline_scope', 0.0) or 0.0
        running_scope = baseline
        cum_ac = 0.0
        cum_pts = 0.0
        cpis = []
        for p in sorted_periods:
            running_scope += p.get('scope_delta', 0.0)
            cum_ac  += p['actual_cost']
            cum_pts += p['points_completed']
            sc = running_scope or 1
            ev = (cum_pts / sc) * bac
            cpis.append(round(ev / cum_ac, 2) if cum_ac else 0)

        if len(cpis) >= 3:
            if cpis[-1] > cpis[-3] + 0.02:
                return 'improving'
            if cpis[-1] < cpis[-3] - 0.02:
                return 'degrading'
        elif len(cpis) == 2:
            diff = cpis[-1] - cpis[-2]
            if diff > 0.02:
                return 'improving'
            if diff < -0.02:
                return 'degrading'
        return 'stable'

    @staticmethod
    def generate_bluf(project, periods, metrics):
        """
        C-Suite executive brief. Pure rule-based, no AI required.
        Returns a structured dict consumed by the BLUF template.
        """
        if not periods or metrics['cpi'] == 0:
            return None

        sorted_periods = sorted(periods, key=lambda x: x['date'])
        cpi   = metrics['cpi']
        spi   = metrics['spi']
        eac   = metrics['eac']
        bac   = project['bac']
        cv    = project.get('contract_value')

        # ── Scope creep ──────────────────────────────────────────────────
        scope_creep_events = CalculationEngine._scope_creep_events(project, sorted_periods)
        initial_scope      = project.get('baseline_scope', 0.0) or 0.0
        total_scope_added  = sum(e['added'] for e in scope_creep_events)
        current_scope      = metrics['total_scope']
        scope_growth_pct   = round(total_scope_added / initial_scope * 100, 1) if initial_scope else 0
        initial_vd         = round(bac / initial_scope, 2) if initial_scope else 0
        current_vd         = metrics['budget_per_point']
        vd_dilution_pct    = round((initial_vd - current_vd) / initial_vd * 100, 1) if initial_vd else 0

        # ── Budget ───────────────────────────────────────────────────────
        overrun_amt = round(eac - bac, 0)
        overrun_pct = round((eac - bac) / bac * 100, 1) if bac else 0
        margin_remaining = round(cv - eac, 0) if cv else None

        # ── Schedule — same math as the burndown chart ───────────────────
        try:
            end_dt          = datetime.strptime(project['end_date'], '%Y-%m-%d')
            planned_end_str = end_dt.strftime('%m/%d/%Y')
        except (ValueError, KeyError):
            end_dt          = None
            planned_end_str = None

        projected_end, days_slip = CalculationEngine._project_finish(
            project, sorted_periods, metrics['avg_velocity']
        )
        projected_end_str = projected_end.strftime('%m/%d/%Y') if projected_end else None

        # ── CPI trend ────────────────────────────────────────────────────
        cpi_trend = CalculationEngine._cpi_trend(project, sorted_periods)

        # ── Overall RAG ──────────────────────────────────────────────────
        if cpi >= 1.0 and spi >= 1.0:
            rag = 'green'
        elif cpi >= 0.9 and spi >= 0.9:
            rag = 'yellow'
        else:
            rag = 'red'

        # ── Verdict sentence ─────────────────────────────────────────────
        if rag == 'green':
            if cpi >= 1.05:
                verdict = (f"This project is healthy — delivering ${cpi:.2f} in earned value for every dollar spent "
                           f"and tracking to complete by {planned_end_str} within budget.")
            else:
                verdict = (f"Project is on budget (CPI {cpi}) and on schedule (SPI {spi}). "
                           f"Delivery is performing as planned.")
        elif rag == 'yellow':
            if cpi < 1.0 and spi >= 1.0:
                verdict = (f"Early cost pressure detected. CPI of {cpi} means every dollar is returning only "
                           f"${cpi:.2f} in value — if this holds, the project will finish over budget.")
            elif spi < 1.0 and cpi >= 1.0:
                verdict = (f"Schedule is slipping. The team is delivering at {round(spi * 100)}% of planned velocity. "
                           f"Budget is intact for now, but the delay is widening.")
            else:
                verdict = (f"Both cost and schedule show early variance (CPI {cpi}, SPI {spi}). "
                           f"Neither is critical yet, but both trends require active management.")
        else:
            if cpi < 0.9 and spi < 0.9:
                verdict = (f"This project is over budget and behind schedule. At CPI {cpi} and SPI {spi}, "
                           f"the Estimate at Completion is ${eac:,.0f} — ${abs(overrun_amt):,.0f} over the "
                           f"approved budget. Without intervention, the overrun will compound toward completion.")
            elif cpi < 0.9:
                verdict = (f"Project is in cost overrun. At CPI {cpi}, the Estimate at Completion is "
                           f"${eac:,.0f} — ${abs(overrun_amt):,.0f} ({abs(overrun_pct)}%) over the ${bac:,.0f} budget.")
            else:
                verdict = (f"Project is behind schedule (SPI {spi}). Budget is holding, but at current velocity "
                           f"the delivery date will slip by approximately {days_slip} days.")

        # ── Narrative paragraphs ─────────────────────────────────────────
        if overrun_amt > 0:
            budget_narrative = (
                f"At the current Cost Performance Index of {cpi}, the Estimate at Completion is "
                f"${eac:,.0f} — ${overrun_amt:,.0f} ({overrun_pct}%) over the approved budget of ${bac:,.0f}."
            )
            if margin_remaining is not None:
                if margin_remaining < 0:
                    budget_narrative += (f" Projected costs now exceed the contract value of ${cv:,.0f} "
                                         f"by ${abs(margin_remaining):,.0f}. The project is operating at a loss.")
                else:
                    budget_narrative += f" ${margin_remaining:,.0f} of contract margin remains."
            if cpi_trend == 'degrading':
                budget_narrative += " The CPI trend is worsening — the overrun is expanding, not stabilizing."
            elif cpi_trend == 'improving':
                budget_narrative += " The CPI trend is improving, suggesting recent corrective actions may be taking effect."
        else:
            budget_narrative = (
                f"The project is tracking ${abs(overrun_amt):,.0f} ({abs(overrun_pct)}%) under budget. "
                f"EAC of ${eac:,.0f} versus a BAC of ${bac:,.0f}."
            )
            if cpi_trend == 'degrading':
                budget_narrative += " Note: cost efficiency has been slipping in recent periods — watch this trend."

        if days_slip > 7:
            schedule_narrative = (
                f"With an SPI of {spi}, the team is delivering at {round(spi * 100)}% of planned velocity. "
                f"If this pace holds, the project will complete around {projected_end_str} — "
                f"approximately {days_slip} days after the planned {planned_end_str}."
            )
        elif days_slip < -7:
            schedule_narrative = (
                f"The project is ahead of schedule. At SPI {spi}, projected completion is {projected_end_str}, "
                f"approximately {abs(days_slip)} days ahead of the planned {planned_end_str}."
            )
        else:
            schedule_narrative = (
                f"Schedule is on track. SPI of {spi} indicates delivery at {round(spi * 100)}% of planned velocity, "
                f"with projected completion near the planned date of {planned_end_str}."
            )

        if scope_creep_events:
            event_strs = [f"{'/'.join(e['date'].split('-')[1:])} (+{e['added']} pts)" for e in scope_creep_events]
            scope_narrative = (
                f"Scope has grown {scope_growth_pct}% above baseline — from {int(initial_scope)} to "
                f"{int(current_scope)} story points — across {len(scope_creep_events)} unplanned "
                f"addition(s): {', '.join(event_strs)}. None of these additions were accompanied by a "
                f"budget increase. Scope Coverage Ratio has eroded {vd_dilution_pct}%: each story point worth "
                f"${initial_vd:,.2f} at project start is now worth ${current_vd:,.2f}."
            )
        else:
            scope_narrative = (
                f"Scope has held at baseline ({int(initial_scope)} story points) with no unplanned additions. "
                f"Scope Coverage Ratio is stable at 100% (${current_vd:,.2f}/pt). This is a meaningful positive signal — "
                f"disciplined scope management is protecting both budget and schedule."
            )

        # ── Risk flags ───────────────────────────────────────────────────
        risks = []
        if cpi < 0.9:
            risks.append(
                f"Budget overrun trajectory: EAC ${eac:,.0f} is ${abs(overrun_amt):,.0f} "
                f"({abs(overrun_pct)}%) above the ${bac:,.0f} BAC."
            )
        if spi < 0.9:
            risks.append(
                f"Schedule slip: project is delivering at {round(spi * 100)}% of planned pace — "
                f"tracking approximately {days_slip} days late."
            )
        if scope_creep_events:
            risks.append(
                f"Scope grew {scope_growth_pct}% above baseline ({int(initial_scope)} → "
                f"{int(current_scope)} pts) across {len(scope_creep_events)} unfunded addition(s)."
            )
        if vd_dilution_pct > 15:
            risks.append(
                f"Scope Coverage Ratio eroded {vd_dilution_pct}%: budget per point is now "
                f"${current_vd:,.2f}, down from ${initial_vd:,.2f} at project start."
            )
        if cpi_trend == 'degrading' and cpi < 1.0:
            risks.append(
                "CPI trend is downward across recent periods — the overrun is widening, not stabilizing."
            )
        if cv and eac > cv:
            risks.append(
                f"Projected costs (${eac:,.0f}) exceed contract value (${cv:,.0f}). Margin is fully consumed."
            )

        # ── Recommended actions ───────────────────────────────────────────
        actions = []
        if cpi < 0.9:
            actions.append(
                "Conduct an immediate cost-cause analysis. Identify which work packages are driving "
                "the overrun and evaluate whether any remaining scope can be cut without impacting delivery."
            )
        if scope_creep_events and vd_dilution_pct > 0:
            actions.append(
                f"Freeze scope or secure a formal budget amendment for the {total_scope_added}-point addition. "
                "Every new point added without funding dilutes the value of work already completed."
            )
        if spi < 0.9:
            actions.append(
                "Review the delivery schedule with the team. If velocity cannot be increased, "
                "the project end date must be renegotiated before it becomes a contractual exposure."
            )
        if cpi_trend == 'degrading':
            actions.append(
                "Increase reporting cadence to weekly. The trend is moving in the wrong direction — "
                "earlier detection preserves more options for correction."
            )
        if cv and margin_remaining is not None and margin_remaining < cv * 0.05:
            actions.append(
                f"Alert the contract owner. With only ${margin_remaining:,.0f} of margin remaining, "
                "any further cost growth will result in a loss position."
            )
        if not actions:
            actions.append(
                "Maintain current delivery discipline. The project is performing well — protect scope "
                "and budget from informal additions and stay the course."
            )

        return {
            'rag':               rag,
            'rag_label':         {'green': 'ON TRACK', 'yellow': 'MONITOR', 'red': 'ACTION REQUIRED'}[rag],
            'verdict':           verdict,
            'pct_complete':      metrics['percent_complete'],
            'cpi':               cpi,
            'spi':               spi,
            'eac':               eac,
            'bac':               bac,
            'contract_value':    cv,
            'overrun_amt':       overrun_amt,
            'overrun_pct':       overrun_pct,
            'margin_remaining':  margin_remaining,
            'days_slip':         days_slip,
            'projected_end_str': projected_end_str,
            'planned_end_str':   planned_end_str,
            'cpi_trend':         cpi_trend,
            'avg_velocity':      metrics['avg_velocity'],
            'scope_creep_events':   scope_creep_events,
            'total_scope_added':    total_scope_added,
            'scope_growth_pct':     scope_growth_pct,
            'initial_scope':        initial_scope,
            'current_scope':        current_scope,
            'initial_vd':           initial_vd,
            'current_vd':           current_vd,
            'vd_dilution_pct':      vd_dilution_pct,
            'budget_narrative':     budget_narrative,
            'schedule_narrative':   schedule_narrative,
            'scope_narrative':      scope_narrative,
            'risks':                risks,
            'actions':              actions,
        }


class Period:
    def __init__(self, date, points_completed, labor_hours=0, labor_rate=0,
                 non_labor_cost=0, scope_delta=0, period_id=None):
        import uuid
        self.period_id = period_id or str(uuid.uuid4())
        self.date = date
        self.points_completed = float(points_completed)
        self.labor_hours = float(labor_hours)
        self.labor_rate = float(labor_rate)
        self.non_labor_cost = float(non_labor_cost)
        self.scope_delta = float(scope_delta)
        self.actual_cost = (self.labor_hours * self.labor_rate) + self.non_labor_cost

    def to_dict(self):
        return {
            "period_id": self.period_id,
            "date": self.date,
            "points_completed": self.points_completed,
            "labor_hours": self.labor_hours,
            "labor_rate": self.labor_rate,
            "non_labor_cost": self.non_labor_cost,
            "actual_cost": self.actual_cost,
            "scope_delta": self.scope_delta
        }
