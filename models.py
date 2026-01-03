from datetime import datetime

class CalculationEngine:
    @staticmethod
    def compute_metrics(project, periods):
        """
        Core logic for Burned Value.
        Aggregates period data to calculate current financial health.
        """
        if not periods:
            return {
                "ev": 0, "ac": 0, "pv": 0, 
                "cpi": 0, "spi": 0, 
                "bac": project['bac'],
                "value_density": 0,
                "percent_complete": 0
            }

        # Sort periods by date to ensure correct cumulative calc
        sorted_periods = sorted(periods, key=lambda x: x['date'])
        
        # Current Cumulative Actuals
        total_ac = sum(p['actual_cost'] for p in sorted_periods)
        total_points_completed = sum(p['points_completed'] for p in sorted_periods)
        
        # Latest Scope (Handling Volatility: Always use the latest Period's total scope)
        current_total_scope = sorted_periods[-1]['total_estimated_effort']
        if current_total_scope == 0: current_total_scope = 1 # Avoid div/0

        # 1. Start with Value Density (The Exchange Rate)
        value_density = project['bac'] / current_total_scope

        # 2. Calculate Earned Value (The Truth)
        # EV = Points Completed * Value Density
        # OR: EV = (Points / Total) * BAC
        percent_complete = total_points_completed / current_total_scope
        ev = percent_complete * project['bac']

        # 3. Calculate Planned Value (PV) - Simplified Linear Projection for now
        # In a real app, this would be based on a baseline curve. 
        # Here we assume linear burn from Start to End.
        start_date = datetime.strptime(project['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(project['end_date'], '%Y-%m-%d')
        now = datetime.now()
        
        total_duration = (end_date - start_date).total_seconds()
        elapsed = (now - start_date).total_seconds()
        
        if elapsed < 0:
            planned_percent = 0
        elif elapsed > total_duration:
            planned_percent = 1.0
        else:
            planned_percent = elapsed / total_duration
            
        pv = planned_percent * project['bac']

        # 4. Financial Metrics
        cpi = ev / total_ac if total_ac > 0 else 0.0
        spi = ev / pv if pv > 0 else 0.0
        eac = project['bac'] / cpi if cpi > 0 else project['bac']

        return {
            "ev": round(ev, 2),
            "ac": round(total_ac, 2),
            "pv": round(pv, 2),
            "cpi": round(cpi, 3),
            "spi": round(spi, 3),
            "eac": round(eac, 2),
            "bac": project['bac'],
            "value_density": round(value_density, 2),
            "percent_complete": round(percent_complete * 100, 1),
            "total_points": total_points_completed,
            "total_scope": current_total_scope
        }

class Project:
    def __init__(self, name, bac, start_date, end_date):
        self.name = name
        self.bac = float(bac)
        self.start_date = start_date
        self.end_date = end_date

class Period:
    def __init__(self, date, points_completed, labor_hours=0, labor_rate=0, non_labor_cost=0, total_scope=0):
        self.date = date
        self.points_completed = float(points_completed)
        self.labor_hours = float(labor_hours)
        self.labor_rate = float(labor_rate)
        self.non_labor_cost = float(non_labor_cost)
        self.total_estimated_effort = float(total_scope)
        
        # Computed AC
        self.actual_cost = (self.labor_hours * self.labor_rate) + self.non_labor_cost

    def to_dict(self):
        return {
            "date": self.date,
            "points_completed": self.points_completed,
            "labor_hours": self.labor_hours,
            "labor_rate": self.labor_rate,
            "non_labor_cost": self.non_labor_cost,
            "actual_cost": self.actual_cost,
            "total_estimated_effort": self.total_estimated_effort
        }
