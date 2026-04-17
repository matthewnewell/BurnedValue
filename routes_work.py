"""
Blueprint: work structure routes (Phase 1).

Covers:
  - Project setup: Disciplines and Iterations  (/project/<id>/work/setup)
  - Epics + Features — release plan view       (/project/<id>/work/plan)
  - Feature detail + Stories                   (/project/<id>/work/feature/<fid>)
  - Backlog view                                (/project/<id>/work/backlog)
"""
from flask import Blueprint, render_template, redirect, url_for, request, abort, jsonify
from db import db, Discipline, Iteration, Epic, Feature, Story

work_bp = Blueprint('work', __name__)


def _get_project(project_id):
    """Load project JSON, 404 if missing. Lazy import avoids circular dependency."""
    from app import get_project_for_request
    p = get_project_for_request(project_id)
    if not p:
        abort(404)
    return p


# ── Setup: Disciplines + Iterations ───────────────────────────────────────────

@work_bp.route('/project/<project_id>/work/setup', methods=['GET'])
def setup(project_id):
    project = _get_project(project_id)
    disciplines = Discipline.query.filter_by(project_id=project_id).order_by(Discipline.name).all()
    iterations  = Iteration.query.filter_by(project_id=project_id).order_by(Iteration.number).all()
    return render_template(
        'work/setup.html',
        project=project,
        disciplines=disciplines,
        iterations=iterations,
    )


# ── Disciplines ────────────────────────────────────────────────────────────────

@work_bp.route('/project/<project_id>/work/discipline/add', methods=['POST'])
def add_discipline(project_id):
    _get_project(project_id)   # 404 guard
    disc = Discipline(
        project_id               = project_id,
        name                     = request.form['name'].strip(),
        charge_number            = request.form.get('charge_number', '').strip() or None,
        avg_rate                 = float(request.form.get('avg_rate', 0) or 0),
        planned_hours_per_period = float(request.form.get('planned_hours_per_period', 0) or 0),
    )
    db.session.add(disc)
    db.session.commit()
    return redirect(url_for('work.setup', project_id=project_id))


@work_bp.route('/project/<project_id>/work/discipline/<disc_id>/delete', methods=['POST'])
def delete_discipline(project_id, disc_id):
    _get_project(project_id)
    disc = Discipline.query.get_or_404(disc_id)
    if disc.project_id != project_id:
        abort(403)
    db.session.delete(disc)
    db.session.commit()
    return redirect(url_for('work.setup', project_id=project_id))


@work_bp.route('/project/<project_id>/work/discipline/<disc_id>/edit', methods=['POST'])
def edit_discipline(project_id, disc_id):
    _get_project(project_id)
    disc = Discipline.query.get_or_404(disc_id)
    if disc.project_id != project_id:
        abort(403)
    disc.name                     = request.form['name'].strip()
    disc.charge_number            = request.form.get('charge_number', '').strip() or None
    disc.avg_rate                 = float(request.form.get('avg_rate', 0) or 0)
    disc.planned_hours_per_period = float(request.form.get('planned_hours_per_period', 0) or 0)
    db.session.commit()
    return redirect(url_for('work.setup', project_id=project_id))


# ── Iterations ─────────────────────────────────────────────────────────────────

@work_bp.route('/project/<project_id>/work/iteration/add', methods=['POST'])
def add_iteration(project_id):
    _get_project(project_id)
    # Auto-assign next iteration number
    last = Iteration.query.filter_by(project_id=project_id).order_by(Iteration.number.desc()).first()
    next_num = (last.number + 1) if last else 1
    it = Iteration(
        project_id = project_id,
        number     = next_num,
        start_date = request.form['start_date'],
        end_date   = request.form['end_date'],
        goal       = request.form.get('goal', '').strip() or None,
    )
    db.session.add(it)
    db.session.commit()
    return redirect(url_for('work.setup', project_id=project_id))


@work_bp.route('/project/<project_id>/work/iteration/<iter_id>/delete', methods=['POST'])
def delete_iteration(project_id, iter_id):
    _get_project(project_id)
    it = Iteration.query.get_or_404(iter_id)
    if it.project_id != project_id:
        abort(403)
    db.session.delete(it)
    db.session.commit()
    return redirect(url_for('work.setup', project_id=project_id))


@work_bp.route('/project/<project_id>/work/iteration/<iter_id>/edit', methods=['POST'])
def edit_iteration(project_id, iter_id):
    _get_project(project_id)
    it = Iteration.query.get_or_404(iter_id)
    if it.project_id != project_id:
        abort(403)
    it.start_date = request.form['start_date']
    it.end_date   = request.form['end_date']
    it.goal       = request.form.get('goal', '').strip() or None
    db.session.commit()
    return redirect(url_for('work.setup', project_id=project_id))


# ── Release Plan: Epics + Features ────────────────────────────────────────────

@work_bp.route('/project/<project_id>/work/plan', methods=['GET'])
def plan(project_id):
    project    = _get_project(project_id)
    epics      = Epic.query.filter_by(project_id=project_id).order_by(Epic.order, Epic.name).all()
    iterations = Iteration.query.filter_by(project_id=project_id).order_by(Iteration.number).all()
    return render_template(
        'work/plan.html',
        project=project,
        epics=epics,
        iterations=iterations,
    )


# ── Epics ──────────────────────────────────────────────────────────────────────

@work_bp.route('/project/<project_id>/work/epic/add', methods=['POST'])
def add_epic(project_id):
    _get_project(project_id)
    last = Epic.query.filter_by(project_id=project_id).order_by(Epic.order.desc()).first()
    epic = Epic(
        project_id  = project_id,
        name        = request.form['name'].strip(),
        description = request.form.get('description', '').strip() or None,
        order       = (last.order + 1) if last else 0,
    )
    db.session.add(epic)
    db.session.commit()
    return redirect(url_for('work.plan', project_id=project_id))


@work_bp.route('/project/<project_id>/work/epic/<epic_id>/edit', methods=['POST'])
def edit_epic(project_id, epic_id):
    _get_project(project_id)
    epic = Epic.query.get_or_404(epic_id)
    if epic.project_id != project_id:
        abort(403)
    epic.name        = request.form['name'].strip()
    epic.description = request.form.get('description', '').strip() or None
    db.session.commit()
    return redirect(url_for('work.plan', project_id=project_id))


@work_bp.route('/project/<project_id>/work/epic/<epic_id>/delete', methods=['POST'])
def delete_epic(project_id, epic_id):
    _get_project(project_id)
    epic = Epic.query.get_or_404(epic_id)
    if epic.project_id != project_id:
        abort(403)
    db.session.delete(epic)
    db.session.commit()
    return redirect(url_for('work.plan', project_id=project_id))


# ── Features ───────────────────────────────────────────────────────────────────

@work_bp.route('/project/<project_id>/work/epic/<epic_id>/feature/add', methods=['POST'])
def add_feature(project_id, epic_id):
    _get_project(project_id)
    epic = Epic.query.get_or_404(epic_id)
    if epic.project_id != project_id:
        abort(403)
    last = Feature.query.filter_by(epic_id=epic_id).order_by(Feature.order.desc()).first()

    tsi_raw = request.form.get('target_start_iter', '').strip()
    tei_raw = request.form.get('target_end_iter', '').strip()
    feat = Feature(
        epic_id           = epic_id,
        name              = request.form['name'].strip(),
        description       = request.form.get('description', '').strip() or None,
        feature_points    = float(request.form.get('feature_points', 0) or 0),
        target_start_iter = int(tsi_raw) if tsi_raw else None,
        target_end_iter   = int(tei_raw) if tei_raw else None,
        status            = request.form.get('status', 'planned'),
        order             = (last.order + 1) if last else 0,
    )
    db.session.add(feat)
    db.session.commit()
    return redirect(url_for('work.plan', project_id=project_id))


@work_bp.route('/project/<project_id>/work/feature/<feat_id>/edit', methods=['POST'])
def edit_feature(project_id, feat_id):
    _get_project(project_id)
    feat = Feature.query.get_or_404(feat_id)
    if feat.epic.project_id != project_id:
        abort(403)
    tsi_raw = request.form.get('target_start_iter', '').strip()
    tei_raw = request.form.get('target_end_iter', '').strip()
    feat.name              = request.form['name'].strip()
    feat.description       = request.form.get('description', '').strip() or None
    feat.feature_points    = float(request.form.get('feature_points', 0) or 0)
    feat.target_start_iter = int(tsi_raw) if tsi_raw else None
    feat.target_end_iter   = int(tei_raw) if tei_raw else None
    feat.status            = request.form.get('status', feat.status)
    feat.blocked           = bool(request.form.get('blocked'))
    feat.blocked_reason    = request.form.get('blocked_reason', '').strip() or None
    db.session.commit()
    return redirect(url_for('work.plan', project_id=project_id))


@work_bp.route('/project/<project_id>/work/feature/<feat_id>/delete', methods=['POST'])
def delete_feature(project_id, feat_id):
    _get_project(project_id)
    feat = Feature.query.get_or_404(feat_id)
    if feat.epic.project_id != project_id:
        abort(403)
    db.session.delete(feat)
    db.session.commit()
    return redirect(url_for('work.plan', project_id=project_id))


# ── Feature Detail + Stories ───────────────────────────────────────────────────

@work_bp.route('/project/<project_id>/work/feature/<feat_id>', methods=['GET'])
def feature_detail(project_id, feat_id):
    project    = _get_project(project_id)
    feat       = Feature.query.get_or_404(feat_id)
    if feat.epic.project_id != project_id:
        abort(403)
    iterations = Iteration.query.filter_by(project_id=project_id).order_by(Iteration.number).all()
    iter_map   = {it.id: it for it in iterations}

    # Build groups: each group is {'iteration': Iteration|None, 'stories': [...]}
    sorted_stories = sorted(feat.stories, key=lambda s: (
        iter_map[s.iteration_id].number if s.iteration_id and s.iteration_id in iter_map else 9999,
        s.order
    ))
    groups = []
    for story in sorted_stories:
        it = iter_map.get(story.iteration_id) if story.iteration_id else None
        if groups and groups[-1]['iteration'] is it:
            groups[-1]['stories'].append(story)
        else:
            groups.append({'iteration': it, 'stories': [story]})

    return render_template(
        'work/feature.html',
        project=project,
        feat=feat,
        groups=groups,
        iterations=iterations,
        iter_map=iter_map,
    )


# ── Stories ────────────────────────────────────────────────────────────────────

_STORY_STATUS_FLOW = ['new', 'active', 'resolved', 'done']


@work_bp.route('/project/<project_id>/work/feature/<feat_id>/story/add', methods=['POST'])
def add_story(project_id, feat_id):
    _get_project(project_id)
    feat = Feature.query.get_or_404(feat_id)
    if feat.epic.project_id != project_id:
        abort(403)
    last     = Story.query.filter_by(feature_id=feat_id).order_by(Story.order.desc()).first()
    iter_raw = request.form.get('iteration_id', '').strip()
    story = Story(
        feature_id          = feat_id,
        iteration_id        = iter_raw if iter_raw else None,
        name                = request.form['name'].strip(),
        description         = request.form.get('description', '').strip() or None,
        acceptance_criteria = request.form.get('acceptance_criteria', '').strip() or None,
        story_points        = float(request.form.get('story_points', 1) or 1),
        status              = 'new',
        order               = (last.order + 1) if last else 0,
    )
    db.session.add(story)
    db.session.commit()
    return redirect(url_for('work.feature_detail', project_id=project_id, feat_id=feat_id))


@work_bp.route('/project/<project_id>/work/story/<story_id>/edit', methods=['POST'])
def edit_story(project_id, story_id):
    _get_project(project_id)
    story = Story.query.get_or_404(story_id)
    if story.feature.epic.project_id != project_id:
        abort(403)
    iter_raw = request.form.get('iteration_id', '').strip()
    story.name                = request.form['name'].strip()
    story.description         = request.form.get('description', '').strip() or None
    story.acceptance_criteria = request.form.get('acceptance_criteria', '').strip() or None
    story.story_points        = float(request.form.get('story_points', 1) or 1)
    story.iteration_id        = iter_raw if iter_raw else None
    story.blocked             = bool(request.form.get('blocked'))
    story.blocked_reason      = request.form.get('blocked_reason', '').strip() or None
    db.session.commit()
    return redirect(url_for('work.feature_detail', project_id=project_id, feat_id=story.feature_id))


@work_bp.route('/project/<project_id>/work/story/<story_id>/status', methods=['POST'])
def story_status(project_id, story_id):
    """Advance or set story status. Accepts ?action=advance|set&status=<val>."""
    from datetime import datetime
    _get_project(project_id)
    story  = Story.query.get_or_404(story_id)
    if story.feature.epic.project_id != project_id:
        abort(403)
    action = request.form.get('action', 'set')
    if action == 'advance':
        idx = _STORY_STATUS_FLOW.index(story.status) if story.status in _STORY_STATUS_FLOW else 0
        if idx < len(_STORY_STATUS_FLOW) - 1:
            story.status = _STORY_STATUS_FLOW[idx + 1]
    else:
        story.status = request.form.get('status', story.status)
    if story.status == 'done' and not story.completed_at:
        story.completed_at = datetime.utcnow()
    elif story.status != 'done':
        story.completed_at = None
    db.session.commit()
    return redirect(url_for('work.feature_detail', project_id=project_id, feat_id=story.feature_id))


@work_bp.route('/project/<project_id>/work/story/<story_id>/delete', methods=['POST'])
def delete_story(project_id, story_id):
    _get_project(project_id)
    story = Story.query.get_or_404(story_id)
    if story.feature.epic.project_id != project_id:
        abort(403)
    feat_id = story.feature_id
    db.session.delete(story)
    db.session.commit()
    return redirect(url_for('work.feature_detail', project_id=project_id, feat_id=feat_id))


# ── Backlog ────────────────────────────────────────────────────────────────────

@work_bp.route('/project/<project_id>/work/backlog', methods=['GET'])
def backlog(project_id):
    project    = _get_project(project_id)
    show_all   = request.args.get('show_all', '0') == '1'
    epics      = Epic.query.filter_by(project_id=project_id).order_by(Epic.order, Epic.name).all()
    iterations = Iteration.query.filter_by(project_id=project_id).order_by(Iteration.number).all()
    iter_map   = {it.id: it for it in iterations}

    # Build a flat list of (epic, feature, story) for display, filtered as needed
    rows = []
    for epic in epics:
        for feat in sorted(epic.features, key=lambda f: f.order):
            for story in sorted(feat.stories, key=lambda s: s.order):
                if show_all or story.iteration_id is None:
                    rows.append({'epic': epic, 'feat': feat, 'story': story})

    # Summary counts (always over ALL stories)
    all_stories   = [r['story'] for epic in epics for feat in epic.features for story in feat.stories for r in [{'story': story}]]
    total_stories = sum(1 for epic in epics for feat in epic.features for s in feat.stories)
    unassigned    = sum(1 for epic in epics for feat in epic.features for s in feat.stories if s.iteration_id is None)
    unassigned_sp = sum(s.story_points for epic in epics for feat in epic.features for s in feat.stories if s.iteration_id is None)

    return render_template(
        'work/backlog.html',
        project=project,
        epics=epics,
        rows=rows,
        iterations=iterations,
        iter_map=iter_map,
        show_all=show_all,
        total_stories=total_stories,
        unassigned=unassigned,
        unassigned_sp=unassigned_sp,
    )


@work_bp.route('/project/<project_id>/work/backlog/story/add', methods=['POST'])
def add_story_from_backlog(project_id):
    """Add a new story directly from the backlog (epic+feature selected inline)."""
    _get_project(project_id)
    feat_id  = request.form.get('feature_id', '').strip()
    if not feat_id:
        abort(400)
    feat = Feature.query.get_or_404(feat_id)
    if feat.epic.project_id != project_id:
        abort(403)
    last     = Story.query.filter_by(feature_id=feat_id).order_by(Story.order.desc()).first()
    iter_raw = request.form.get('iteration_id', '').strip()
    story = Story(
        feature_id          = feat_id,
        iteration_id        = iter_raw if iter_raw else None,
        name                = request.form['name'].strip(),
        description         = request.form.get('description', '').strip() or None,
        acceptance_criteria = request.form.get('acceptance_criteria', '').strip() or None,
        story_points        = float(request.form.get('story_points', 1) or 1),
        status              = 'new',
        order               = (last.order + 1) if last else 0,
    )
    db.session.add(story)
    db.session.commit()
    return redirect(url_for('work.backlog', project_id=project_id))


@work_bp.route('/project/<project_id>/work/story/<story_id>/assign', methods=['POST'])
def assign_story(project_id, story_id):
    """Quick-assign a story to an iteration (or remove from iteration)."""
    _get_project(project_id)
    story = Story.query.get_or_404(story_id)
    if story.feature.epic.project_id != project_id:
        abort(403)
    iter_raw         = request.form.get('iteration_id', '').strip()
    story.iteration_id = iter_raw if iter_raw else None
    db.session.commit()
    show_all = request.form.get('show_all', '0')
    return redirect(url_for('work.backlog', project_id=project_id, show_all=show_all))
