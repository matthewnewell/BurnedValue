from datetime import datetime

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
                "value_density": 0,
                "percent_complete": 0,
                "total_points": 0,
                "total_scope": 0
            }

        sorted_periods = sorted(periods, key=lambda x: x['date'])

        total_ac = sum(p['actual_cost'] for p in sorted_periods)
        total_points_completed = sum(p['points_completed'] for p in sorted_periods)

        current_total_scope = sorted_periods[-1]['total_estimated_effort']
        if current_total_scope == 0:
            current_total_scope = 1

        # Value Density: the dollar exchange rate per point
        value_density = project['bac'] / current_total_scope

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

        now = datetime.now()
        total_duration = (end_date - start_date).total_seconds()
        elapsed = (now - start_date).total_seconds()

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
            "value_density": round(value_density, 2),
            "percent_complete": round(percent_complete * 100, 1),
            "total_points": total_points_completed,
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

        for i, p in enumerate(sorted_periods):
            cum_ac += p['actual_cost']
            cum_points += p['points_completed']
            scope = p['total_estimated_effort'] if p['total_estimated_effort'] > 0 else 1

            percent = cum_points / scope
            ev = percent * project['bac']
            cpi = round(ev / cum_ac, 2) if cum_ac > 0 else 0
            value_density = round(project['bac'] / scope, 2)

            scope_delta = 0
            scope_changed = False
            if i > 0:
                prev_scope = sorted_periods[i - 1]['total_estimated_effort']
                if scope != prev_scope:
                    scope_changed = True
                    scope_delta = int(scope - prev_scope)

            details.append({
                'period_id': p.get('period_id', ''),
                'date': p['date'],
                'period_points': p['points_completed'],
                'cum_points': cum_points,
                'scope': scope,
                'scope_delta': scope_delta,
                'scope_changed': scope_changed,
                'value_density': value_density,
                'period_ac': p['actual_cost'],
                'cum_ac': round(cum_ac, 2),
                'ev': round(ev, 2),
                'cpi': cpi
            })

        return details

    @staticmethod
    def generate_narrative(project, periods, metrics):
        """
        Produces a plain-English interpretation of project health.
        This is the seam where Claude API will plug in for richer AI analysis.
        """
        if not periods or metrics['cpi'] == 0:
            return None

        sorted_periods = sorted(periods, key=lambda x: x['date'])

        # Detect scope creep events
        scope_creep_events = []
        initial_scope = sorted_periods[0]['total_estimated_effort']
        for i in range(1, len(sorted_periods)):
            prev = sorted_periods[i - 1]['total_estimated_effort']
            curr = sorted_periods[i]['total_estimated_effort']
            if curr > prev:
                pct = round((curr - prev) / prev * 100, 1)
                scope_creep_events.append({
                    'date': sorted_periods[i]['date'],
                    'added': int(curr - prev),
                    'pct': pct
                })

        cpi = metrics['cpi']
        spi = metrics['spi']
        eac = metrics['eac']
        bac = project['bac']
        overrun = round(eac - bac, 2)
        initial_vd = round(bac / initial_scope, 2)
        current_vd = metrics['value_density']
        vd_dilution_pct = round((initial_vd - current_vd) / initial_vd * 100, 1) if initial_vd > 0 else 0

        if cpi >= 1.05:
            status = 'success'
        elif cpi >= 0.95:
            status = 'warning'
        else:
            status = 'danger'

        # Build the headline
        if status == 'success':
            headline = f"Project is running under budget (CPI: {cpi}). Efficient delivery."
        elif status == 'warning':
            headline = f"Minor cost variance detected (CPI: {cpi}). Monitor closely."
        else:
            headline = f"Project is over budget (CPI: {cpi}). Corrective action needed."

        # Build supporting lines
        lines = []
        if scope_creep_events:
            event_strs = [f"{e['date']} (+{e['added']} pts, +{e['pct']}%)" for e in scope_creep_events]
            lines.append(f"{len(scope_creep_events)} scope creep event(s): {', '.join(event_strs)}.")
        if vd_dilution_pct > 0:
            lines.append(
                f"Value Density diluted from ${initial_vd:,.2f}/pt \u2192 ${current_vd:,.2f}/pt "
                f"({vd_dilution_pct}% loss in point value)."
            )
        if overrun > 0:
            lines.append(f"At current CPI, EAC is ${eac:,.0f} \u2014 ${overrun:,.0f} over the ${bac:,.0f} budget.")
        elif overrun < 0:
            lines.append(f"At current CPI, EAC is ${eac:,.0f} \u2014 ${abs(overrun):,.0f} under budget.")

        if spi < 0.95:
            lines.append(f"Schedule is also behind plan (SPI: {spi}).")
        elif spi > 1.05:
            lines.append(f"Ahead of schedule (SPI: {spi}).")

        return {
            'status': status,
            'headline': headline,
            'lines': lines,
            'scope_creep_count': len(scope_creep_events)
        }


class Project:
    def __init__(self, name, description, bac, start_date, end_date):
        self.name = name
        self.description = description
        self.bac = float(bac)
        self.start_date = start_date
        self.end_date = end_date


class Period:
    def __init__(self, date, points_completed, labor_hours=0, labor_rate=0,
                 non_labor_cost=0, total_scope=0, scope_delta=0, period_id=None):
        import uuid
        self.period_id = period_id or str(uuid.uuid4())
        self.date = date
        self.points_completed = float(points_completed)
        self.labor_hours = float(labor_hours)
        self.labor_rate = float(labor_rate)
        self.non_labor_cost = float(non_labor_cost)
        self.scope_delta = float(scope_delta)
        self.total_estimated_effort = float(total_scope)
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
            "scope_delta": self.scope_delta,
            "total_estimated_effort": self.total_estimated_effort
        }
