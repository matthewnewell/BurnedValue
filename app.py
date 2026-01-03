from flask import Flask, render_template, request, redirect, url_for, jsonify
from models import CalculationEngine, Period
import utils
import uuid
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    # For now, just load the first project or redirect to creation
    projects = utils.load_projects()
    if not projects:
        return redirect(url_for('create_project'))
    
    # Default to first available project
    project_id = list(projects.keys())[0]
    return redirect(url_for('dashboard', project_id=project_id))

@app.route('/create', methods=['GET', 'POST'])
def create_project():
    if request.method == 'POST':
        project_id = str(uuid.uuid4())
        data = {
            "id": project_id,
            "name": request.form['name'],
            "bac": float(request.form['bac']),
            "start_date": request.form['start_date'],
            "end_date": request.form['end_date'],
            "periods": []
        }
        utils.save_project_data(project_id, data)
        return redirect(url_for('dashboard', project_id=project_id))
    return render_template('create_project.html')

@app.route('/dashboard/<project_id>')
def dashboard(project_id):
    project = utils.get_project(project_id)
    if not project:
        return "Project not found", 404
    
    metrics = CalculationEngine.compute_metrics(project, project['periods'])
    return render_template('dashboard.html', project=project, metrics=metrics)

@app.route('/project/<project_id>/add_period', methods=['GET', 'POST'])
def add_period(project_id):
    project = utils.get_project(project_id)
    if request.method == 'POST':
        # Default previous total scope if not provided (to avoid manual re-entry every time)
        last_scope = 0
        if project['periods']:
             last_scope = project['periods'][-1]['total_estimated_effort']

        scope_input = request.form.get('total_scope')
        total_scope = float(scope_input) if scope_input else last_scope

        # Handle Cost Input Options
        # If user provides explicit Total AC, we use that. 
        # Otherwise we calculate from Labor + ODC.
        labor_hours = float(request.form.get('labor_hours', 0))
        labor_rate = float(request.form.get('labor_rate', 0))
        non_labor = float(request.form.get('non_labor', 0))
        
        # Create Period Object
        period = Period(
            date=request.form['date'],
            points_completed=float(request.form['points']),
            labor_hours=labor_hours,
            labor_rate=labor_rate,
            non_labor_cost=non_labor,
            total_scope=total_scope
        )
        
        project['periods'].append(period.to_dict())
        utils.save_project_data(project_id, project)
        return redirect(url_for('dashboard', project_id=project_id))
        
    return render_template('entry.html', project=project)

@app.route('/api/project/<project_id>')
def project_api(project_id):
    """API endpoint for chart data"""
    project = utils.get_project(project_id)
    # Recalculate metrics for every point in time to draw the curves?
    # For MVP, we pass the raw periods and let Client-side JS or specific helper do the time-series calc.
    # We'll just return the full project JSON.
    return jsonify(project)

if __name__ == '__main__':
    app.run(debug=True)
