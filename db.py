"""
SQLAlchemy database setup and ORM models for Phase 1+ entities.

Existing project/period data lives in JSON (utils.py) and is untouched.
New entities (Discipline, Iteration, Epic, Feature, Story, Task) live here.
Both storage systems coexist, linked by project_id (string).

See docs/DATA_MODEL.md for entity definitions and EV flow.
"""
import os
import uuid
import sqlite3
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine


# ── SQLAlchemy instance ────────────────────────────────────────────────────────

db = SQLAlchemy()


def get_db_path():
    """SQLite file path — mirrors the DATA_DIR used by JSON storage."""
    base = os.environ.get('DATA_DIR') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, 'burnedvalue.db')


def init_db(app):
    """Bind SQLAlchemy to the Flask app and create all tables."""
    db.init_app(app)
    with app.app_context():
        db.create_all()


# ── Enable SQLite FK enforcement on every connection ──────────────────────────
# Without this, ondelete='CASCADE' is silently ignored by SQLite.

@event.listens_for(Engine, 'connect')
def _set_sqlite_pragma(dbapi_conn, connection_record):
    if isinstance(dbapi_conn, sqlite3.Connection):
        cursor = dbapi_conn.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _uuid():
    return str(uuid.uuid4())


# ── Models ────────────────────────────────────────────────────────────────────

class Discipline(db.Model):
    """
    A labor discipline / charge code on a project.
    Defines the staffing profile: planned hours per iteration × avg rate = PV contribution.
    Actual cost comes from DisciplineActual entries (weekly cost report).
    """
    __tablename__ = 'discipline'

    id                       = db.Column(db.String(36), primary_key=True, default=_uuid)
    project_id               = db.Column(db.String(36), nullable=False, index=True)
    name                     = db.Column(db.String(100), nullable=False)       # e.g. "Software"
    charge_number            = db.Column(db.String(50),  nullable=True)        # accounting charge code
    avg_rate                 = db.Column(db.Float, default=0.0)                # $/hour
    planned_hours_per_period = db.Column(db.Float, default=0.0)

    actuals = db.relationship('DisciplineActual', back_populates='discipline',
                              cascade='all, delete-orphan')

    @property
    def planned_cost_per_period(self):
        return self.avg_rate * self.planned_hours_per_period


class Iteration(db.Model):
    """
    A time-boxed execution period, aligned to the weekly accounting cost report.
    Replaces manual Period entry in Phase 2. In Phase 1, used for story allocation.
    """
    __tablename__ = 'iteration'

    id         = db.Column(db.String(36), primary_key=True, default=_uuid)
    project_id = db.Column(db.String(36), nullable=False, index=True)
    number     = db.Column(db.Integer,    nullable=False)
    start_date = db.Column(db.String(10), nullable=False)   # ISO 'YYYY-MM-DD'
    end_date   = db.Column(db.String(10), nullable=False)
    goal       = db.Column(db.Text,       nullable=True)

    actuals = db.relationship('DisciplineActual', back_populates='iteration',
                              cascade='all, delete-orphan')
    stories = db.relationship('Story', back_populates='iteration')

    __table_args__ = (
        db.UniqueConstraint('project_id', 'number', name='uq_iteration_project_number'),
    )


class DisciplineActual(db.Model):
    """
    Actual dollars charged to a discipline in an iteration.
    Entered from weekly accounting cost report. This is AC.
    """
    __tablename__ = 'discipline_actual'

    id                     = db.Column(db.String(36), primary_key=True, default=_uuid)
    iteration_id           = db.Column(db.String(36),
                                       db.ForeignKey('iteration.id', ondelete='CASCADE'),
                                       nullable=False)
    discipline_id          = db.Column(db.String(36),
                                       db.ForeignKey('discipline.id', ondelete='CASCADE'),
                                       nullable=False)
    actual_dollars_charged = db.Column(db.Float, nullable=False, default=0.0)
    entered_at             = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    notes                  = db.Column(db.Text, nullable=True)

    iteration  = db.relationship('Iteration',  back_populates='actuals')
    discipline = db.relationship('Discipline', back_populates='actuals')


class Epic(db.Model):
    """
    A major capability area. Contains Features.
    EV rolls up from Features → Epic → Project.
    """
    __tablename__ = 'epic'

    id          = db.Column(db.String(36), primary_key=True, default=_uuid)
    project_id  = db.Column(db.String(36), nullable=False, index=True)
    name        = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text,       nullable=True)
    order       = db.Column(db.Integer,    default=0)

    features = db.relationship('Feature', back_populates='epic',
                               order_by='Feature.order',
                               cascade='all, delete-orphan')

    @property
    def total_feature_points(self):
        return sum(f.feature_points for f in self.features)

    @property
    def earned_feature_points(self):
        return sum(f.earned_feature_points for f in self.features)

    @property
    def percent_complete(self):
        total = self.total_feature_points
        return (self.earned_feature_points / total * 100) if total > 0 else 0.0


class Feature(db.Model):
    """
    A specific deliverable within an Epic. Sized in feature points.
    % complete = done story points / total story points.
    Features without stories are 0% complete — EV requires defined stories.
    """
    __tablename__ = 'feature'

    id                = db.Column(db.String(36), primary_key=True, default=_uuid)
    epic_id           = db.Column(db.String(36),
                                  db.ForeignKey('epic.id', ondelete='CASCADE'),
                                  nullable=False)
    name              = db.Column(db.String(200), nullable=False)
    description       = db.Column(db.Text,        nullable=True)
    feature_points    = db.Column(db.Float,        default=0.0)
    target_start_iter = db.Column(db.Integer,      nullable=True)  # iteration number
    target_end_iter   = db.Column(db.Integer,      nullable=True)  # iteration number
    status            = db.Column(db.String(20),   default='planned')
    #                   planned | refined | active | complete
    blocked           = db.Column(db.Boolean,      default=False)
    blocked_reason    = db.Column(db.Text,         nullable=True)
    order             = db.Column(db.Integer,      default=0)

    epic    = db.relationship('Epic',  back_populates='features')
    stories = db.relationship('Story', back_populates='feature',
                              order_by='Story.order',
                              cascade='all, delete-orphan')

    @property
    def total_story_points(self):
        return sum(s.story_points for s in self.stories)

    @property
    def done_story_points(self):
        return sum(s.story_points for s in self.stories if s.status == 'done')

    @property
    def percent_complete(self):
        total = self.total_story_points
        return (self.done_story_points / total) if total > 0 else 0.0

    @property
    def earned_feature_points(self):
        return self.feature_points * self.percent_complete

    @property
    def refinement_ratio(self):
        """story points / feature points — 0 = unrefined, ~1 = fully broken down."""
        return (self.total_story_points / self.feature_points) if self.feature_points > 0 else 0.0


class Story(db.Model):
    """
    Atomic unit of EV credit. Done story → earns story_points toward parent Feature.
    Sized in story points. Allocated to an Iteration (or left in backlog).
    State machine: new → active → resolved → done.
    Blocked is a flag (attribute), not a state.
    """
    __tablename__ = 'story'

    id                  = db.Column(db.String(36), primary_key=True, default=_uuid)
    feature_id          = db.Column(db.String(36),
                                    db.ForeignKey('feature.id', ondelete='CASCADE'),
                                    nullable=False)
    iteration_id        = db.Column(db.String(36),
                                    db.ForeignKey('iteration.id', ondelete='SET NULL'),
                                    nullable=True)    # null = backlog
    name                = db.Column(db.String(200), nullable=False)
    description         = db.Column(db.Text,        nullable=True)
    acceptance_criteria = db.Column(db.Text,        nullable=True)
    story_points        = db.Column(db.Float,        default=1.0)
    status              = db.Column(db.String(20),   default='new')
    #                     new | active | resolved | done
    blocked             = db.Column(db.Boolean,      default=False)
    blocked_reason      = db.Column(db.Text,         nullable=True)
    order               = db.Column(db.Integer,      default=0)
    created_at          = db.Column(db.DateTime,     default=lambda: datetime.now(timezone.utc))
    completed_at        = db.Column(db.DateTime,     nullable=True)

    feature   = db.relationship('Feature',   back_populates='stories')
    iteration = db.relationship('Iteration', back_populates='stories')
    tasks     = db.relationship('Task',      back_populates='story',
                                cascade='all, delete-orphan')


class Task(db.Model):
    """
    Sub-item of a Story. Deferred — stub for future implementation.
    Not an EV unit. Does not affect EV calculations.
    """
    __tablename__ = 'task'

    id       = db.Column(db.String(36), primary_key=True, default=_uuid)
    story_id = db.Column(db.String(36),
                         db.ForeignKey('story.id', ondelete='CASCADE'),
                         nullable=False)
    name     = db.Column(db.String(200), nullable=False)
    status   = db.Column(db.String(20),  default='new')   # new|active|resolved|done
    order    = db.Column(db.Integer,     default=0)

    story = db.relationship('Story', back_populates='tasks')
