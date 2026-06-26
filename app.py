import os
import json
import random
import uuid
from threading import Lock
from flask import Flask, render_template, request, session, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from models import db, GameSession, Player, Task, ChatMessage
from data.roles import get_role, get_starting_roles
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-for-company-sim'
db_uri = os.environ.get('DATABASE_URL')
if db_uri:
    if db_uri.startswith("postgres://"):
        db_uri = db_uri.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///company_sim.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


with open('data/questions.json', 'r') as f:
    QUESTIONS = json.load(f)


thread_lock = Lock()
background_thread = None

def generate_join_code():
    return str(random.randint(100000, 999999))

GLOBAL_NEWS = []

def add_news(session_id, company_name, category, content):
    from datetime import datetime
    timestamp = datetime.utcnow().strftime("%H:%M:%S")
    item = {
        'timestamp': timestamp,
        'session_id': session_id,
        'company_name': company_name,
        'category': category, 
        'content': content
    }
    GLOBAL_NEWS.append(item)
    if len(GLOBAL_NEWS) > 20:
        GLOBAL_NEWS.pop(0)
    socketio.emit('market_news_update', GLOBAL_NEWS)

def background_task_loop():
    """Background thread to process continuous game mechanics"""
    while True:
        socketio.sleep(10) 
        
        with app.app_context():
            active_sessions = GameSession.query.filter_by(status='active').all()
            for session in active_sessions:
                
                
                base_growth = 0.005 + (session.customer_satisfaction / 100.0) * 0.015 + (session.product_quality / 100.0) * 0.01
                tech_debt_penalty = (session.tech_debt / 100.0) * 0.015
                uptime_scaling = session.server_uptime / 100.0
                user_change = int(session.user_base * (base_growth - tech_debt_penalty) * uptime_scaling) + random.randint(-5, 10)
                session.user_base = max(100, session.user_base + user_change)

                
                passive_rev = session.user_base * (session.product_quality / 100.0) * (session.server_uptime / 100.0) * random.uniform(1.0, 3.0)
                prev_rev = session.company_revenue
                session.company_revenue = round(session.company_revenue + passive_rev, 2)

                
                prev_pct = prev_rev / session.goal_revenue
                curr_pct = session.company_revenue / session.goal_revenue
                for milestone in [0.25, 0.50, 0.75, 1.0]:
                    if prev_pct < milestone <= curr_pct:
                        add_news(session.id, session.name, 'success', f"Milestone: {session.name} reached {int(milestone*100)}% of their goal!")

                
                target_csat = int((session.product_quality + session.server_uptime) / 2)
                csat_change = int((target_csat - session.customer_satisfaction) * 0.1) + random.choice([-1, 0, 1])
                session.customer_satisfaction = max(10, min(100, session.customer_satisfaction + csat_change))

                
                tech_debt_change = random.choice([0, 0, 1])
                session.tech_debt = max(0, min(100, session.tech_debt + tech_debt_change))

                
                morale_change = random.choice([-1, 0, 1])
                if session.tech_debt > 60: morale_change -= 1
                session.employee_morale = max(10, min(100, session.employee_morale + morale_change))

                
                quality_change = random.choice([-1, 0, 1])
                if session.tech_debt > 70: quality_change -= 1
                session.product_quality = max(5, min(100, session.product_quality + quality_change))

                
                if random.random() < 0.12:
                    penalty = random.choice([
                        {'msg': 'Server Outage! Uptime dropped.', 'kpi': 'server_uptime', 'change': -random.randint(5,12)},
                        {'msg': 'Data Breach! Market share dropping.', 'kpi': 'market_share', 'change': -random.randint(2,6)},
                        {'msg': 'Bug Escape! Quality dropping.', 'kpi': 'product_quality', 'change': -random.randint(4,8)},
                    ])
                    current_val = getattr(session, penalty['kpi'])
                    setattr(session, penalty['kpi'], max(0, current_val + penalty['change']))
                    session.company_revenue = max(0, session.company_revenue - 30000)
                    socketio.emit('chat_message', {
                        'is_system': True,
                        'content': f"[ALERT] {penalty['msg']}",
                        'is_penalty': True
                    }, to=session.id)
                    add_news(session.id, session.name, 'alert', f"ALERT: {session.name} suffered a {penalty['msg'].split('!')[0]}!")

                
                if session.server_uptime < 99.9:
                    session.server_uptime = min(99.9, session.server_uptime + random.uniform(0.2, 0.5))

                
                from datetime import datetime
                players = Player.query.filter_by(session_id=session.id).all()
                for p in players:
                    if p.status == 'active':
                        s_hist = json.loads(p.score_history) if p.score_history else []
                        s_hist.append({'timestamp': datetime.utcnow().strftime("%H:%M:%S"), 'score': p.score, 'savings': p.savings})
                        if len(s_hist) > 30: s_hist = s_hist[-30:]
                        p.score_history = json.dumps(s_hist)
                        
                        emit_personal_update(p)

                emit_kpis(session.id)
            db.session.commit()
            update_admin_players()
            emit_global_leaderboard()

@socketio.on('buy_gadget')
def buy_gadget(data):
    player_id = data.get('player_id')
    gadget = data.get('gadget')
    cost = data.get('cost', 0)
    
    player = Player.query.get(player_id)
    if player and player.status == 'active':
        gadgets = json.loads(player.gadgets_owned) if player.gadgets_owned else []
        if gadget in gadgets:
            emit('gadget_bought', {'success': False, 'error': f'You already own the {gadget}!'})
            return
            
        if player.savings >= cost:
            player.savings -= cost
            gadgets.append(gadget)
            player.gadgets_owned = json.dumps(gadgets)
            
            
            player.score += 50
            db.session.commit()
            emit_personal_update(player)
            
            socketio.emit('chat_message', {
                'is_system': True,
                'content': f'{player.name} upgraded their workspace with a {gadget}!',
                'is_victory': True
            }, to=player.session_id)
            
            emit('gadget_bought', {'success': True, 'savings': player.savings, 'gadgets': gadgets, 'score': player.score})
            update_admin_players()
            add_news(player.session_id, player.session.name, 'info', f"UPGRADE: {player.name} purchased a {gadget}!")
        else:
            emit('gadget_bought', {'success': False, 'error': 'Insufficient savings'})

def emit_kpis(session_id):
    
    g_session = GameSession.query.get(session_id)
    if not g_session: return
    
    from datetime import datetime
    
    
    history = json.loads(g_session.kpi_history) if g_session.kpi_history else []
    growth_rate = 0.0
    if len(history) >= 3:
        old_rev = history[-3].get('company_revenue', 0.0)
        if old_rev > 0:
            growth_rate = round(((g_session.company_revenue - old_rev) / old_rev) * 100.0, 1)
            
    revenue_prog = min(100.0, (g_session.company_revenue / max(1.0, g_session.goal_revenue)) * 100.0)
    health_score = (g_session.employee_morale + g_session.product_quality + g_session.customer_satisfaction + g_session.server_uptime - g_session.tech_debt) / 5.0
    perf_score = round((revenue_prog * 0.6) + (health_score * 0.4), 1)
    perf_score = max(0.0, min(100.0, perf_score))

    data = {
        'company_revenue': g_session.company_revenue,
        'goal_revenue': g_session.goal_revenue,
        'employee_morale': g_session.employee_morale,
        'product_quality': g_session.product_quality,
        'server_uptime': g_session.server_uptime,
        'customer_satisfaction': g_session.customer_satisfaction,
        'market_share': g_session.market_share,
        'tech_debt': g_session.tech_debt,
        'user_base': g_session.user_base,
        'growth_rate': growth_rate,
        'performance_score': perf_score,
        'timestamp': datetime.utcnow().strftime("%H:%M:%S")
    }
    
    
    history.append(data)
    
    if len(history) > 30:
        history = history[-30:]
    g_session.kpi_history = json.dumps(history)
    db.session.commit()
    
    socketio.emit('update_kpis', {'current': data, 'history': history}, to=session_id)

def emit_personal_update(player):
    if not player: return
    
    role = get_role(player.role_id)
    next_role = get_role(role.get('next_role')) if role and role.get('next_role') else None
    
    target_score = 0
    if role:
        if "Junior" in role['title']:
            target_score = 200
        elif "Mid" in role['title']:
            target_score = 500
        elif "Senior" in role['title']:
            target_score = 1000
        elif "CTO" in role['title'] or "CPO" in role['title'] or "Chief" in role['title']:
            target_score = 2000
            
    s_hist = json.loads(player.score_history) if player.score_history else []
    gadgets = json.loads(player.gadgets_owned) if player.gadgets_owned else []
    
    socketio.emit('personal_update', {
        'savings': player.savings,
        'score': player.score,
        'salary': player.salary,
        'role_title': role['title'] if role else "Unknown",
        'role_dept': role['department'] if role else "Unknown",
        'next_role_title': next_role['title'] if next_role else "None",
        'next_role_req': target_score,
        'tasks_completed': player.tasks_completed,
        'history': s_hist,
        'gadgets': gadgets
    }, to=player.socket_id if player.socket_id else player.session_id)


@app.route('/')
def index():
    response = app.make_response(render_template('index.html'))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route('/create_session', methods=['POST'])
def create_session():
    
    goal = request.json.get('goal_revenue', 10000000) if request.json else 10000000
    session_id = str(uuid.uuid4())
    
    company_names = [
        "Acme Corp", "Globex", "Initech", "Umbrella Corp", "Stark Ind.", "Wayne Ent.", 
        "Cyberdyne", "Massive Dynamic", "Hooli", "Pied Piper", "Soylent", "Dunder Mifflin",
        "Vandelay Ind.", "Bluth Co.", "Wonka Ind.", "Oscorp", "LexCorp", "Tyrell Corp",
        "Weyland-Yutani", "Omni Consumer", "Virtucon", "Buy n Large", "Aperture Sci.", "Black Mesa",
        "Gekko & Co.", "Nakatomi", "Prestige", "Strickland", "Trek", "Spacely", 
        "Cogswell", "Macmillan", "Goliath", "Zorin", "Spectre", "Monsters Inc.",
        "Blue Sun", "Tessier-Ashpool", "CHOAM", "Sirius", "MomCorp", "Planet Express",
        "Krusty Krab", "Chum Bucket", "Los Pollos", "GNB", "Pierce & Pierce", "Ewing Oil",
        "Duff Beer", "Slurm"
    ]
    random_name = random.choice(company_names)
    
    new_session = GameSession(id=session_id, name=random_name, goal_revenue=goal, join_code=generate_join_code(), status='waiting')
    db.session.add(new_session)
    db.session.commit()
    socketio.emit('admin_state_update', get_full_admin_state(), to='admin_room')
    return jsonify({"success": True, "session_id": session_id})

@app.route('/admin')
def admin_dashboard():
    response = app.make_response(render_template('admin.html'))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route('/api/check_player', methods=['POST'])
def check_player():
    data = request.json or {}
    join_code = str(data.get('join_code', '')).strip()
    name = str(data.get('name', '')).strip()
    
    if not join_code or not name:
        return jsonify({"valid_session": False, "exists": False})
        
    g_session = GameSession.query.filter_by(join_code=join_code).first()
    if not g_session or g_session.status == 'ended':
        return jsonify({"valid_session": False, "exists": False})
        
    existing_player = Player.query.filter_by(session_id=g_session.id, name=name).first()
    return jsonify({
        "valid_session": True,
        "exists": existing_player is not None
    })

@app.route('/join', methods=['POST'])
def join_game():
    data = request.json or {}
    join_code = str(data.get('join_code', '')).strip()
    name = str(data.get('name', '')).strip()
    role_id = data.get('role_id')
    password = str(data.get('password', '')).strip()
    confirm_password = str(data.get('confirm_password', '')).strip()
    
    print(f"[DEBUG] Attempting to join with code: '{join_code}' for player: '{name}'")
    
    g_session = GameSession.query.filter_by(join_code=join_code).first()
    if not g_session:
        return jsonify({"success": False, "error": "Invalid join code."})
    
    if g_session.status == 'ended':
        return jsonify({"success": False, "error": "Session has ended."})
        
    
    existing_player = Player.query.filter_by(session_id=g_session.id, name=name).first()
    if existing_player:
        if existing_player.status == 'fired':
            return jsonify({"success": False, "error": "This player has been fired from the company."})
        
        
        if existing_player.password_hash:
            if not password:
                return jsonify({"success": False, "error": "Password is required to sign in."})
            if not check_password_hash(existing_player.password_hash, password):
                return jsonify({"success": False, "error": "Incorrect password. Please try again."})
        else:
            
            if password:
                existing_player.password_hash = generate_password_hash(password)
                db.session.commit()
                
        session['player_id'] = existing_player.id
        return jsonify({"success": True, "session_id": g_session.id, "player_id": existing_player.id})
        
    
    if not password:
        return jsonify({"success": False, "error": "Password is required for first-time joining."})
    if password != confirm_password:
        return jsonify({"success": False, "error": "Passwords do not match."})
        
    current_players = Player.query.filter_by(session_id=g_session.id).count()
    if current_players >= 6:
        return jsonify({"success": False, "error": "Company is at max capacity (6 players)."})
        
    role = get_role(role_id)
    if not role:
        return jsonify({"success": False, "error": "Invalid role."})
        
    new_player = Player(
        session_id=g_session.id,
        name=name,
        role_id=role_id,
        salary=role['salary'],
        password_hash=generate_password_hash(password)
    )
    db.session.add(new_player)
    db.session.commit()
    
    session['player_id'] = new_player.id
    
    return jsonify({"success": True, "session_id": g_session.id, "player_id": new_player.id})

@app.route('/game')
def game():
    player_id = session.get('player_id')
    if not player_id:
        return redirect(url_for('index'))
    player = Player.query.get(player_id)
    if not player:
        return redirect(url_for('index'))
    if player.status == 'fired':
        return redirect(url_for('fired'))
    g_session = GameSession.query.get(player.session_id)
    role = get_role(player.role_id)
    return render_template('game.html', player=player, session=g_session, role=role)

@app.route('/api/roles')
def api_roles():
    return jsonify(get_starting_roles())

@app.route('/fired')
def fired():
    return render_template('fired.html')





@socketio.on('connect')
def handle_connect():
    global background_thread
    with thread_lock:
        if background_thread is None:
            background_thread = socketio.start_background_task(background_task_loop)

def update_admin_players():
    
    socketio.emit('admin_state_update', get_full_admin_state(), to='admin_room')

@socketio.on('join')
def on_join_room(data):
    player_id = data.get('player_id')
    is_admin = data.get('is_admin')
    
    if is_admin:
        join_room('admin_room')
        emit('admin_state_update', get_full_admin_state())
        emit('market_news_update', GLOBAL_NEWS)
        return
        
    player = Player.query.get(player_id)
    if player:
        join_room(player.session_id)
        join_room(player.id) 
        player.socket_id = request.sid
        db.session.commit()
        update_admin_players()
        emit_kpis(player.session_id)
        emit_global_leaderboard()
        emit('market_news_update', GLOBAL_NEWS)
        emit_personal_update(player)
        socketio.emit('chat_message', {
            'is_system': True,
            'content': f'{player.name} joined the company.',
            'is_victory': False
        }, to=player.session_id)

@socketio.on('admin_start_all')
def admin_start_all():
    sessions = GameSession.query.filter_by(status='waiting').all()
    for s in sessions:
        s.status = 'active'
        emit_kpis(s.id)
        socketio.emit('game_started', {}, to=s.id)
        socketio.emit('chat_message', {
            'is_system': True,
            'content': '[SYS] COMPETITION INITIATED. RACE TO THE GOAL!',
            'is_victory': True
        }, to=s.id)
    db.session.commit()
    update_admin_players()

@socketio.on('admin_start_company')
def admin_start_company(data):
    session_id = data.get('session_id')
    s = GameSession.query.get(session_id)
    if s and s.status == 'waiting':
        s.status = 'active'
        db.session.commit()
        emit_kpis(s.id)
        socketio.emit('game_started', {}, to=s.id)
        socketio.emit('chat_message', {
            'is_system': True,
            'content': '[SYS] SIMULATION INITIATED FOR YOUR COMPANY. START WORKING!',
            'is_victory': True
        }, to=s.id)
        update_admin_players()

@socketio.on('admin_pause_company')
def admin_pause_company(data):
    session_id = data.get('session_id')
    s = GameSession.query.get(session_id)
    if s and s.status == 'active':
        s.status = 'paused'
        db.session.commit()
        socketio.emit('game_paused', {}, to=s.id)
        update_admin_players()

@socketio.on('admin_resume_company')
def admin_resume_company(data):
    session_id = data.get('session_id')
    s = GameSession.query.get(session_id)
    if s and s.status == 'paused':
        s.status = 'active'
        db.session.commit()
        socketio.emit('game_started', {}, to=s.id)
        update_admin_players()

@socketio.on('admin_pause_all')
def admin_pause_all():
    sessions = GameSession.query.filter_by(status='active').all()
    for s in sessions:
        s.status = 'paused'
        socketio.emit('game_paused', {}, to=s.id)
    db.session.commit()
    update_admin_players()

@socketio.on('admin_resume_all')
def admin_resume_all():
    sessions = GameSession.query.filter_by(status='paused').all()
    for s in sessions:
        s.status = 'active'
        socketio.emit('game_started', {}, to=s.id)
    db.session.commit()
    update_admin_players()

@socketio.on('admin_kill_all')
def admin_kill_all():
    sessions = GameSession.query.all()
    for s in sessions:
        socketio.emit('game_killed', {}, to=s.id)
        
        Task.query.filter_by(session_id=s.id).delete()
        ChatMessage.query.filter_by(session_id=s.id).delete()
        Player.query.filter_by(session_id=s.id).delete()
        GameSession.query.filter_by(id=s.id).delete()
    db.session.commit()
    update_admin_players()

@socketio.on('admin_delete_company')
def admin_delete_company(data):
    session_id = data.get('session_id')
    if session_id:
        Task.query.filter_by(session_id=session_id).delete()
        ChatMessage.query.filter_by(session_id=session_id).delete()
        Player.query.filter_by(session_id=session_id).delete()
        GameSession.query.filter_by(id=session_id).delete()
        db.session.commit()
        socketio.emit('you_are_fired', {}, to=session_id) 
        update_admin_players()

@socketio.on('admin_kick_player')
def admin_kick_player(data):
    player_id = data.get('player_id')
    player = Player.query.get(player_id)
    if player:
        player.status = 'fired'
        db.session.commit()
        socketio.emit('chat_message', {
            'is_system': True,
            'content': f'[SYS] {player.name} was kicked by Admin.',
            'is_penalty': True
        }, to=player.session_id)
        update_admin_players()
        socketio.emit('you_are_fired', {}, to=player.socket_id)

@socketio.on('admin_kill')
def admin_kill(data):
    session_id = data.get('session_id')
    g_session = GameSession.query.get(session_id)
    if g_session:
        socketio.emit('game_killed', {}, to=session_id)
        
        Task.query.filter_by(session_id=session_id).delete()
        ChatMessage.query.filter_by(session_id=session_id).delete()
        Player.query.filter_by(session_id=session_id).delete()
        GameSession.query.filter_by(id=session_id).delete()
        db.session.commit()
        update_admin_players()

def get_full_admin_state():
    sessions = GameSession.query.all()
    data = []
    for s in sessions:
        players = Player.query.filter_by(session_id=s.id, status='active').all()
        history = json.loads(s.kpi_history) if s.kpi_history else []
        growth_rate = 0.0
        if len(history) >= 3:
            old_rev = history[-3].get('company_revenue', 0.0)
            if old_rev > 0:
                growth_rate = round(((s.company_revenue - old_rev) / old_rev) * 100.0, 1)
        
        revenue_prog = min(100.0, (s.company_revenue / max(1.0, s.goal_revenue)) * 100.0)
        health_score = (s.employee_morale + s.product_quality + s.customer_satisfaction + s.server_uptime - s.tech_debt) / 5.0
        perf_score = round((revenue_prog * 0.6) + (health_score * 0.4), 1)
        perf_score = max(0.0, min(100.0, perf_score))

        data.append({
            'id': s.id,
            'name': s.name,
            'join_code': s.join_code,
            'status': s.status,
            'revenue': s.company_revenue,
            'goal': s.goal_revenue,
            'history': history,
            'players': [{
                'id': p.id,
                'name': p.name,
                'role_id': p.role_id,
                'role_title': get_role(p.role_id)['title'] if get_role(p.role_id) else 'Unknown',
                'score': p.score,
                'strikes': p.strikes,
                'status': p.status,
                'salary': p.salary,
                'savings': p.savings,
                'tasks_completed': p.tasks_completed,
                'gadgets': json.loads(p.gadgets_owned) if p.gadgets_owned else []
            } for p in players],
            'growth_rate': growth_rate,
            'performance_score': perf_score
        })
    return data

def emit_global_leaderboard():
    sessions = GameSession.query.filter(GameSession.status != 'ended').all()
    leaderboard = []
    for s in sessions:
        history = json.loads(s.kpi_history) if s.kpi_history else []
        growth_rate = 0.0
        if len(history) >= 3:
            old_rev = history[-3].get('company_revenue', 0.0)
            if old_rev > 0:
                growth_rate = round(((s.company_revenue - old_rev) / old_rev) * 100.0, 1)
        
        revenue_prog = min(100.0, (s.company_revenue / max(1.0, s.goal_revenue)) * 100.0)
        health_score = (s.employee_morale + s.product_quality + s.customer_satisfaction + s.server_uptime - s.tech_debt) / 5.0
        perf_score = round((revenue_prog * 0.6) + (health_score * 0.4), 1)
        perf_score = max(0.0, min(100.0, perf_score))
        
        leaderboard.append({
            'id': s.id,
            'name': s.name,
            'revenue': s.company_revenue,
            'goal': s.goal_revenue,
            'growth_rate': growth_rate,
            'performance_score': perf_score
        })
    leaderboard.sort(key=lambda x: x['revenue'], reverse=True)
    socketio.emit('global_leaderboard', leaderboard)

@socketio.on('send_chat')
def on_send_chat(data):
    session_id = data.get('session_id')
    player_id = data.get('player_id')
    content = data.get('content')
    
    player = Player.query.get(player_id)
    if player and content:
        msg = ChatMessage(session_id=session_id, sender_id=player.id, sender_name=player.name, content=content)
        db.session.add(msg)
        db.session.commit()
        
        socketio.emit('chat_message', {
            'sender_name': player.name,
            'content': content,
            'is_system': False
        }, to=session_id)

@socketio.on('send_support_msg')
def on_send_support_msg(data):
    player_id = data.get('player_id')
    content = str(data.get('content', '')).strip()
    is_admin = data.get('is_admin', False)
    
    if not player_id or not content:
        return
        
    player = Player.query.get(player_id)
    if not player:
        return
        
    sender_id = f"admin_{player.id}" if is_admin else player.id
    sender_name = "Admin" if is_admin else player.name
    
    msg = ChatMessage(
        session_id=player.session_id,
        sender_id=sender_id,
        sender_name=sender_name,
        content=content,
        is_support=True
    )
    db.session.add(msg)
    db.session.commit()
    
    msg_data = {
        "id": msg.id,
        "player_id": player.id,
        "sender_name": sender_name,
        "sender_id": sender_id,
        "content": content,
        "timestamp": msg.timestamp.strftime("%H:%M:%S")
    }
    
    socketio.emit('receive_support_msg', msg_data, to=player.id)
    socketio.emit('receive_support_msg', msg_data, to='admin_room')

@socketio.on('send_chat_msg')
def on_send_chat_msg(data):
    player_id = data.get('player_id')
    content = str(data.get('content', '')).strip()
    channel = data.get('channel', 'team')
    
    if not player_id or not content:
        return
        
    player = Player.query.get(player_id)
    if not player:
        return
        
    role = get_role(player.role_id)
    role_title = role['title'] if role else ''
    
    msg = ChatMessage(
        session_id=player.session_id,
        sender_id=player.id,
        sender_name=player.name,
        content=content,
        is_global=(channel == 'global'),
        is_support=False,
        is_system=False
    )
    db.session.add(msg)
    db.session.commit()
    
    msg_data = {
        "id": msg.id,
        "sender_id": player.id,
        "sender_name": player.name,
        "role_title": role_title,
        "content": content,
        "channel": channel,
        "timestamp": msg.timestamp.strftime("%H:%M:%S")
    }
    
    if channel == 'team':
        socketio.emit('new_chat_msg', msg_data, to=player.session_id)
    else:
        socketio.emit('new_chat_msg', msg_data)

@socketio.on('get_question')
def get_question(data):
    player_id = data.get('player_id')
    difficulty = data.get('difficulty')
    player = Player.query.get(player_id)
    
    q_pool = QUESTIONS
    if player:
        if player.session.status != 'active': return
        role = get_role(player.role_id)
        if role:
            department = role['department']
            domain_qs = [q for q in QUESTIONS if q['domain'] == department]
            if domain_qs:
                q_pool = domain_qs
                
    mapped_difficulty = difficulty
    mapped_type = None

    if difficulty == 'scenario':
        mapped_difficulty = 'hotfix'
        mapped_type = 'scenario_based'
    elif difficulty == 'calculation':
        mapped_difficulty = 'refactor'
        mapped_type = 'calculation'
    elif difficulty == 'match':
        mapped_difficulty = 'bonding'
        mapped_type = 'match_following'
    elif difficulty == 'news_quiz':
        mapped_difficulty = 'marketing'
        mapped_type = 'news_quiz'
    elif difficulty == 'prompt':
        mapped_difficulty = 'refactor'
        mapped_type = 'prompt_engineering'
    elif difficulty == 'architecture':
        mapped_difficulty = 'refactor'
        mapped_type = 'calculation'
    elif difficulty == 'security':
        mapped_difficulty = 'hotfix'
        mapped_type = 'scenario_based'
    elif difficulty == 'refactor' or difficulty == 'hotfix':
        mapped_difficulty = 'bugs'
    elif difficulty == 'bonding':
        mapped_difficulty = 'work'
    elif difficulty == 'marketing':
        mapped_difficulty = 'mcqs'

    if mapped_difficulty:
        diff_qs = [q for q in q_pool if q.get('difficulty') == mapped_difficulty]
        if diff_qs:
            q_pool = diff_qs
            
    if mapped_type:
        type_qs = [q for q in q_pool if q.get('type') == mapped_type]
        if type_qs:
            q_pool = type_qs
                
    q = random.choice(q_pool)
    emit('receive_question', {
        'id': q['id'],
        'domain': q['domain'],
        'question': q['question'],
        'type': q.get('type', 'mcq'),
        'difficulty': difficulty,
        'options': q.get('options', []),
        'hint': q.get('hint', '')
    })

@socketio.on('answer_question')
def answer_question(data):
    player_id = data.get('player_id')
    q_id = data.get('question_id')
    answer_input = data.get('answer_input') 
    task_difficulty = data.get('task_difficulty')
    
    player = Player.query.get(player_id)
    if not player or player.status == 'fired': return
    g_session = GameSession.query.get(player.session_id)
    if g_session.status != 'active': return
    
    q = next((x for x in QUESTIONS if x['id'] == q_id), None)
    if q:
        is_correct = False
        if q.get('type') == 'fill_in_the_blank':
            is_correct = str(answer_input).strip().lower() == str(q['correct_answer']).strip().lower()
        else:
            is_correct = q.get('correct_index') == int(answer_input)

        diff = task_difficulty if task_difficulty else q.get('difficulty', 'mcqs')
        points_map = {
            'work': {'win': 10, 'lose': -5},
            'mcqs': {'win': 20, 'lose': -10},
            'bugs': {'win': 30, 'lose': -15},
            'q_and_a': {'win': 50, 'lose': -25},
            'refactor': {'win': 40, 'lose': -20},
            'hotfix': {'win': 45, 'lose': -22},
            'bonding': {'win': 25, 'lose': -12},
            'marketing': {'win': 35, 'lose': -18},
            'scenario': {'win': 45, 'lose': -22},
            'calculation': {'win': 40, 'lose': -20},
            'match': {'win': 25, 'lose': -12},
            'news_quiz': {'win': 35, 'lose': -18},
            'prompt': {'win': 50, 'lose': -25},
            'architecture': {'win': 55, 'lose': -28},
            'security': {'win': 60, 'lose': -30}
        }
        rewards = points_map.get(diff, points_map['mcqs'])

        if is_correct:
            
            gadgets = json.loads(player.gadgets_owned) if player.gadgets_owned else []
            gadget_multipliers = {
                'Mechanical Keyboard': 0.10,
                'Noise Cancelling Headphones': 0.12,
                'Coffee Espresso Machine': 0.15,
                'VR Headset': 0.18,
                'Ergonomic Chair': 0.20,
                'Standing Desk': 0.25,
                'Dual 4K Monitors': 0.30,
                'High-End Dev Rig': 0.40
            }
            total_multiplier = 1.0
            for g in gadgets:
                if g in gadget_multipliers:
                    total_multiplier += gadget_multipliers[g]

            base_win = rewards['win']
            points_gained = int(base_win * total_multiplier)
            player.score += points_gained
            player.tasks_completed += 1
            
            base_revenue_gain = base_win * 5000
            revenue_gain = int(base_revenue_gain * total_multiplier)
            g_session.company_revenue += revenue_gain
            
            
            base_cash_earned = base_win * 20.0
            cash_earned = base_cash_earned * total_multiplier
            player.savings += cash_earned
            
            
            kpi_msg = ""
            if diff == 'refactor' or diff == 'calculation':
                g_session.tech_debt = max(0, g_session.tech_debt - 15)
                g_session.product_quality = min(100, g_session.product_quality + 5)
                kpi_msg = " | Tech Debt decreased, Quality increased!"
                socketio.emit('chat_message', {
                    'is_system': True,
                    'content': f"[SYSTEM] {player.name} successfully optimized the system! Tech Debt reduced and Product Quality boosted.",
                    'is_victory': True
                }, to=g_session.id)
                add_news(g_session.id, g_session.name, 'success', f"OPTIMIZE: {player.name} reduced tech debt at {g_session.name}!")
            elif diff == 'hotfix' or diff == 'scenario':
                g_session.server_uptime = min(100.0, round(g_session.server_uptime + 8.0, 1))
                g_session.tech_debt = max(0, g_session.tech_debt - 3)
                kpi_msg = " | Server Uptime restored!"
                socketio.emit('chat_message', {
                    'is_system': True,
                    'content': f"[SYSTEM] {player.name} successfully deployed a hotfix! Server Uptime restored.",
                    'is_victory': True
                }, to=g_session.id)
                add_news(g_session.id, g_session.name, 'success', f"HOTFIX: {player.name} restored server uptime at {g_session.name}!")
            elif diff == 'bonding' or diff == 'match':
                g_session.employee_morale = min(100, g_session.employee_morale + 15)
                kpi_msg = " | Employee Morale boosted!"
                socketio.emit('chat_message', {
                    'is_system': True,
                    'content': f"[SYSTEM] {player.name} organized a team bonding event! Morale improved.",
                    'is_victory': True
                }, to=g_session.id)
                add_news(g_session.id, g_session.name, 'success', f"MORALE: {player.name} hosted team bonding at {g_session.name}!")
            elif diff == 'marketing' or diff == 'news_quiz':
                user_gain = int(g_session.user_base * 0.15)
                g_session.user_base += user_gain
                g_session.customer_satisfaction = min(100, g_session.customer_satisfaction + 5)
                kpi_msg = f" | User base +{user_gain}!"
                socketio.emit('chat_message', {
                    'is_system': True,
                    'content': f"[SYSTEM] {player.name} launched a marketing push! User base grew by 15%.",
                    'is_victory': True
                }, to=g_session.id)
                add_news(g_session.id, g_session.name, 'success', f"MARKETING: {player.name} grew user base by 15% at {g_session.name}!")
            elif diff == 'prompt':
                g_session.product_quality = min(100, g_session.product_quality + 8)
                g_session.tech_debt = max(0, g_session.tech_debt - 5)
                kpi_msg = " | Quality boosted, Tech Debt decreased!"
                socketio.emit('chat_message', {
                    'is_system': True,
                    'content': f"[SYSTEM] {player.name} completed a prompt engineering task! Quality boosted.",
                    'is_victory': True
                }, to=g_session.id)
                add_news(g_session.id, g_session.name, 'success', f"PROMPT: {player.name} optimized prompts at {g_session.name}!")
            elif diff == 'architecture':
                g_session.server_uptime = min(100.0, round(g_session.server_uptime + 10.0, 1))
                g_session.product_quality = min(100, g_session.product_quality + 8)
                g_session.tech_debt = max(0, g_session.tech_debt - 8)
                kpi_msg = " | Architecture optimized: Uptime, Quality, and Tech Debt improved!"
                socketio.emit('chat_message', {
                    'is_system': True,
                    'content': f"[SYSTEM] {player.name} optimized the system architecture! Uptime and Quality boosted.",
                    'is_victory': True
                }, to=g_session.id)
                add_news(g_session.id, g_session.name, 'success', f"ARCH: {player.name} optimized architecture at {g_session.name}!")
            elif diff == 'security':
                g_session.tech_debt = max(0, g_session.tech_debt - 10)
                g_session.server_uptime = min(100.0, round(g_session.server_uptime + 6.0, 1))
                g_session.customer_satisfaction = min(100, g_session.customer_satisfaction + 6)
                kpi_msg = " | Security audited: Tech Debt, Uptime, and CSAT improved!"
                socketio.emit('chat_message', {
                    'is_system': True,
                    'content': f"[SYSTEM] {player.name} conducted a security audit! System vulnerabilities patched.",
                    'is_victory': True
                }, to=g_session.id)
                add_news(g_session.id, g_session.name, 'success', f"SECURITY: {player.name} patched vulnerabilities at {g_session.name}!")
            
            
            role = get_role(player.role_id)
            if role and role.get('next_role'):
                can_promote = False
                if "Junior" in role['title'] and player.score >= 200:
                    can_promote = True
                elif "Mid" in role['title'] and player.score >= 500:
                    can_promote = True
                elif "Senior" in role['title'] and player.score >= 1000:
                    can_promote = True
                elif ("CTO" in role['title'] or "CPO" in role['title'] or "Chief" in role['title']) and player.score >= 2000:
                    can_promote = True
                
                if can_promote:
                    player.role_id = role['next_role']
                    new_role = get_role(player.role_id)
                    player.salary = new_role['salary']
                    socketio.emit('chat_message', {
                        'is_system': True,
                        'content': f"[PROMOTION] {player.name} has been promoted to {new_role['title']}!",
                        'is_victory': True
                    }, to=g_session.id)
                    add_news(g_session.id, g_session.name, 'success', f"PROMOTION: {player.name} promoted to {new_role['title']} at {g_session.name}!")
            
            db.session.commit()
            emit_personal_update(player)
            boost_text = f" (x{total_multiplier:.2f} Boost!)" if total_multiplier > 1.0 else ""
            emit('answer_result', {
                'correct': True, 
                'score': player.score, 
                'strikes': player.strikes,
                'message': f'Success! +{points_gained} points{boost_text} | Earned: ${cash_earned:,.2f}{kpi_msg}'
            })
            update_admin_players()
            emit_kpis(player.session_id)
            emit_global_leaderboard()
            
            if (g_session.company_revenue >= g_session.goal_revenue and 
                g_session.employee_morale >= 80 and 
                g_session.product_quality >= 80 and 
                g_session.server_uptime >= 99.0 and 
                g_session.tech_debt <= 15):
                
                
                active_sessions = GameSession.query.all()
                company_scores = []
                for s in active_sessions:
                    company_players = Player.query.filter_by(session_id=s.id).all()
                    total_points = sum(p.score for p in company_players)
                    company_scores.append({
                        'session': s,
                        'points': total_points
                    })
                
                company_scores.sort(key=lambda x: x['points'], reverse=True)
                winner_data = company_scores[0] if company_scores else {'session': g_session, 'points': sum(p.score for p in g_session.players)}
                winner = winner_data['session']
                winner_points = winner_data['points']
                
                
                for s in active_sessions:
                    is_winner = (s.id == winner.id)
                    if s.id == g_session.id:
                        trigger_msg = f"SUCCESS! {g_session.name} met all Victory Goal Metrics and triggered game over!"
                    else:
                        trigger_msg = f"GAME OVER! Rival company {g_session.name} met all Victory Goal Metrics and triggered game over!"
                        
                    msg_content = f"{trigger_msg} Overall Winner: {winner.name} with {winner_points} total points!"
                    
                    socketio.emit('chat_message', {
                        'is_system': True,
                        'content': msg_content,
                        'is_victory': is_winner,
                        'is_penalty': not is_winner
                    }, to=s.id)
                    
                    
                    add_news(s.id, s.name, 'success' if is_winner else 'alert', f"VICTORY: {winner.name} won the game with {winner_points} points!")
                    
                    
                    socketio.emit('game_killed', {}, to=s.id)

                
                for s in active_sessions:
                    Task.query.filter_by(session_id=s.id).delete()
                    ChatMessage.query.filter_by(session_id=s.id).delete()
                    Player.query.filter_by(session_id=s.id).delete()
                    GameSession.query.filter_by(id=s.id).delete()
                
                db.session.commit()
                update_admin_players()
        else:
            
            player.score += rewards['lose']
            g_session.company_revenue = max(0.0, g_session.company_revenue + (rewards['lose'] * 5000))
            
            
            player.strikes += 1
            
            
            if diff == 'refactor' or diff == 'calculation':
                g_session.tech_debt = min(100, g_session.tech_debt + 8)
                g_session.product_quality = max(5, g_session.product_quality - 3)
            elif diff == 'hotfix' or diff == 'scenario':
                g_session.server_uptime = max(50.0, round(g_session.server_uptime - 5.0, 1))
                g_session.tech_debt = min(100, g_session.tech_debt + 4)
            elif diff == 'bonding' or diff == 'match':
                g_session.employee_morale = max(10, g_session.employee_morale - 6)
            elif diff == 'marketing' or diff == 'news_quiz':
                g_session.customer_satisfaction = max(10, g_session.customer_satisfaction - 5)
            elif diff == 'prompt':
                g_session.tech_debt = min(100, g_session.tech_debt + 5)
                g_session.product_quality = max(5, g_session.product_quality - 2)
            elif diff == 'architecture':
                g_session.server_uptime = max(50.0, round(g_session.server_uptime - 6.0, 1))
                g_session.tech_debt = min(100, g_session.tech_debt + 6)
            elif diff == 'security':
                g_session.customer_satisfaction = max(10, g_session.customer_satisfaction - 8)
                g_session.server_uptime = max(50.0, round(g_session.server_uptime - 4.0, 1))
            else:
                
                g_session.employee_morale = max(10, g_session.employee_morale - 3)
                g_session.product_quality = max(5, g_session.product_quality - 3)
                g_session.tech_debt = min(100, g_session.tech_debt + 4)
            
            db.session.commit()
            
            if player.strikes >= 3:
                
                g_session.employee_morale = max(10, g_session.employee_morale - 15)
                g_session.product_quality = max(5, g_session.product_quality - 15)
                g_session.server_uptime = max(50.0, round(g_session.server_uptime - 10.0, 1))
                g_session.customer_satisfaction = max(10, g_session.customer_satisfaction - 15)
                g_session.tech_debt = min(100, g_session.tech_debt + 20)
                
                
                player.strikes = 0
                db.session.commit()
                
                
                socketio.emit('chat_message', {
                    'is_system': True,
                    'content': f"[CRITICAL FAILURE] {player.name} triggered a major production incident! Company stats penalized.",
                    'is_penalty': True
                }, to=g_session.id)
                add_news(g_session.id, g_session.name, 'alert', f"CRASH: {player.name} caused an incident at {g_session.name}! Stats penalized.")
                
                emit('answer_result', {
                    'correct': False, 
                    'score': player.score, 
                    'strikes': 0,
                    'message': f'CRITICAL FAILURE! Strikes reset to 0. Company stats penalized.'
                })
            else:
                emit('answer_result', {
                    'correct': False, 
                    'score': player.score, 
                    'strikes': player.strikes,
                    'message': f'Failed. {rewards["lose"]} points. Strike {player.strikes}/3!'
                })
                add_news(g_session.id, g_session.name, 'info', f"WARNING: {player.name} received strike {player.strikes} at {g_session.name}!")
                
            emit_personal_update(player)
            update_admin_players()
            emit_kpis(player.session_id)
            emit_global_leaderboard()


@app.route('/api/change_password', methods=['POST'])
def change_password():
    player_id = session.get('player_id')
    if not player_id:
        return jsonify({"success": False, "error": "Not authenticated"})
    player = Player.query.get(player_id)
    if not player:
        return jsonify({"success": False, "error": "Player not found"})
    
    data = request.json or {}
    new_password = str(data.get('password', '')).strip()
    if not new_password:
        return jsonify({"success": False, "error": "Password cannot be empty"})
        
    player.password_hash = generate_password_hash(new_password)
    db.session.commit()
    return jsonify({"success": True})

@app.route('/api/change_username', methods=['POST'])
def change_username():
    player_id = session.get('player_id')
    if not player_id:
        return jsonify({"success": False, "error": "Not authenticated"})
    player = Player.query.get(player_id)
    if not player:
        return jsonify({"success": False, "error": "Player not found"})
    
    data = request.json or {}
    new_name = str(data.get('name', '')).strip()
    if not new_name:
        return jsonify({"success": False, "error": "Username cannot be empty"})
        
    if new_name == player.name:
        return jsonify({"success": True, "name": new_name})
        
    exists = Player.query.filter_by(session_id=player.session_id, name=new_name).first()
    if exists:
        return jsonify({"success": False, "error": "Username is already taken"})
        
    old_name = player.name
    player.name = new_name
    db.session.commit()
    
    
    socketio.emit('chat_message', {
        'is_system': True,
        'content': f"[SYS] {old_name} changed their username to {new_name}.",
        'is_victory': False
    }, to=player.session_id)
    
    emit_personal_update(player)
    update_admin_players()
    return jsonify({"success": True, "name": new_name})

@app.route('/api/support_history', methods=['GET'])
def support_history():
    target_player_id = request.args.get('player_id')
    player_id = session.get('player_id')
    
    is_admin = request.args.get('is_admin') == 'true' or not player_id
    if not is_admin and player_id != target_player_id:
        target_player_id = player_id
        
    if not target_player_id:
        return jsonify([])
        
    player = Player.query.get(target_player_id)
    if not player:
        return jsonify([])
        
    player_admin_id = f"admin_{player.id}"
    support_messages = ChatMessage.query.filter(
        ChatMessage.session_id == player.session_id,
        ChatMessage.is_support == True,
        ((ChatMessage.sender_id == player.id) | (ChatMessage.sender_id == player_admin_id))
    ).order_by(ChatMessage.timestamp.asc()).all()
    
    return jsonify([{
        "id": m.id,
        "sender_name": m.sender_name,
        "sender_id": m.sender_id,
        "content": m.content,
        "timestamp": m.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    } for m in support_messages])

@app.route('/api/chat_history', methods=['GET'])
def chat_history():
    player_id = request.args.get('player_id')
    channel = request.args.get('channel', 'team')
    
    if not player_id:
        return jsonify([])
        
    player = Player.query.get(player_id)
    if not player:
        return jsonify([])
        
    if channel == 'team':
        chat_messages = ChatMessage.query.filter_by(
            session_id=player.session_id,
            is_global=False,
            is_support=False,
            is_system=False
        ).order_by(ChatMessage.timestamp.asc()).all()
    else:
        chat_messages = ChatMessage.query.filter_by(
            is_global=True,
            is_support=False,
            is_system=False
        ).order_by(ChatMessage.timestamp.asc()).all()
        
    result = []
    for m in chat_messages:
        role_title = ""
        if m.sender_id:
            sender = Player.query.get(m.sender_id)
            if sender:
                role = get_role(sender.role_id)
                role_title = role['title'] if role else ''
        result.append({
            "id": m.id,
            "sender_name": m.sender_name,
            "sender_id": m.sender_id,
            "role_title": role_title,
            "content": m.content,
            "timestamp": m.timestamp.strftime("%H:%M:%S")
        })
        
    return jsonify(result)

@app.route('/api/admin/support_players', methods=['GET'])
def admin_support_players():
    players = Player.query.filter_by(status='active').all()
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "company_name": p.session.name,
        "role_title": get_role(p.role_id)['title'] if get_role(p.role_id) else 'Unknown'
    } for p in players])


def setup_database():
    with app.app_context():
        
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if db_uri.startswith('sqlite:'):
            try:
                import sqlite3
                import os
                db_path = os.path.join(app.instance_path, 'company_sim.db')
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("PRAGMA table_info(player)")
                    columns = [info[1] for info in cursor.fetchall()]
                    if 'password_hash' not in columns:
                        cursor.execute("ALTER TABLE player ADD COLUMN password_hash TEXT")
                        conn.commit()
                        print("[Database] Successfully added password_hash column to player table.")
                    
                    cursor.execute("PRAGMA table_info(chat_message)")
                    chat_columns = [info[1] for info in cursor.fetchall()]
                    if 'is_support' not in chat_columns:
                        cursor.execute("ALTER TABLE chat_message ADD COLUMN is_support INTEGER DEFAULT 0")
                        conn.commit()
                        print("[Database] Successfully added is_support column to chat_message table.")
                    if 'is_global' not in chat_columns:
                        cursor.execute("ALTER TABLE chat_message ADD COLUMN is_global INTEGER DEFAULT 0")
                        conn.commit()
                        print("[Database] Successfully added is_global column to chat_message table.")
                    conn.close()
            except Exception as e:
                print(f"[Database] Error running SQLite migrations: {e}")

        db.create_all()
        try:
            ended_sessions = GameSession.query.filter_by(status='ended').all()
            if ended_sessions:
                for s in ended_sessions:
                    Task.query.filter_by(session_id=s.id).delete()
                    ChatMessage.query.filter_by(session_id=s.id).delete()
                    Player.query.filter_by(session_id=s.id).delete()
                    GameSession.query.filter_by(id=s.id).delete()
                db.session.commit()
                print(f"[Database] Cleaned up {len(ended_sessions)} ended sessions.")
        except Exception as e:
            print(f"[Database] Error cleaning up ended sessions: {e}")


setup_database()

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)
