from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class GameSession(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), default="Acme Corp")
    join_code = db.Column(db.String(6), unique=True, nullable=False)
    status = db.Column(db.String(20), default="waiting") 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    
    company_revenue = db.Column(db.Float, default=0.0) 
    goal_revenue = db.Column(db.Float, default=1000000.0) 
    employee_morale = db.Column(db.Integer, default=100) 
    product_quality = db.Column(db.Integer, default=50) 
    server_uptime = db.Column(db.Float, default=99.9) 
    customer_satisfaction = db.Column(db.Integer, default=50) 
    market_share = db.Column(db.Float, default=1.0) 
    tech_debt = db.Column(db.Integer, default=0) 
    user_base = db.Column(db.Integer, default=1000)
    
    
    kpi_history = db.Column(db.Text, default="[]") 
    
    
    players = db.relationship('Player', backref='session', lazy=True)
    tasks = db.relationship('Task', backref='session', lazy=True)
    messages = db.relationship('ChatMessage', backref='session', lazy=True)

class Player(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey('game_session.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    role_id = db.Column(db.Integer, nullable=False)
    socket_id = db.Column(db.String(100), nullable=True)
    
    
    salary = db.Column(db.Float, default=0.0)
    savings = db.Column(db.Float, default=0.0)
    score = db.Column(db.Integer, default=0)
    tasks_completed = db.Column(db.Integer, default=0)
    score_history = db.Column(db.Text, default="[]") 
    strikes = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active')
    gadgets_owned = db.Column(db.String(500), default="[]") 
    password_hash = db.Column(db.String(256), nullable=True)

class Task(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey('game_session.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    product_line = db.Column(db.String(50), nullable=False)
    required_department = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.Integer, default=1) 
    status = db.Column(db.String(20), default="todo") 
    assigned_to = db.Column(db.String(36), db.ForeignKey('player.id'), nullable=True)
    
    reward_revenue = db.Column(db.Float, default=0.0)
    penalty_revenue = db.Column(db.Float, default=0.0)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey('game_session.id'), nullable=False)
    sender_id = db.Column(db.String(36), nullable=True) 
    sender_name = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_system = db.Column(db.Boolean, default=False)
    is_support = db.Column(db.Boolean, default=False)
    is_global = db.Column(db.Boolean, default=False)
