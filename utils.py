import json
import os

DATA_FILE = os.path.join('data', 'projects.json')

def load_projects():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_projects(projects):
    with open(DATA_FILE, 'w') as f:
        json.dump(projects, f, indent=4)

def get_project(project_id):
    projects = load_projects()
    return projects.get(project_id)

def save_project_data(project_id, project_data):
    projects = load_projects()
    projects[project_id] = project_data
    save_projects(projects)
