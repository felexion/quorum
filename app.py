import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quorum.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

# --- MODELS ---

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    primary_role = db.Column(db.String(100))
    secondary_role = db.Column(db.String(100))

class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, default=datetime.now)
    meeting_type = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200))
    quorum_required = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='Ongoing')
    ended_at = db.Column(db.DateTime)

    # Relationships
    attendances = db.relationship('Attendance', backref='meeting', lazy=True, cascade="all, delete-orphan")
    motions = db.relationship('Motion', backref='meeting', lazy=True, cascade="all, delete-orphan")
    statements = db.relationship('Statement', backref='meeting', lazy=True, cascade="all, delete-orphan")
    agenda_items = db.relationship('AgendaItem', backref='meeting', lazy=True, cascade="all, delete-orphan")

class AgendaItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    
    # Items linked to this agenda point
    motions = db.relationship('Motion', backref='agenda_item', lazy=True)
    statements = db.relationship('Statement', backref='agenda_item', lazy=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    status = db.Column(db.String(20), default='Absent')

class Motion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False)
    agenda_item_id = db.Column(db.Integer, db.ForeignKey('agenda_item.id'))
    
    proposer_id = db.Column(db.Integer, db.ForeignKey('member.id'))
    seconder_id = db.Column(db.Integer, db.ForeignKey('member.id'))
    text = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    vote_results = db.Column(db.String(100))

class Statement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False)
    agenda_item_id = db.Column(db.Integer, db.ForeignKey('agenda_item.id'))
    speaker_id = db.Column(db.Integer, db.ForeignKey('member.id'))
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)

class AppSetting(db.Model):
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.String(255))

@app.context_processor
def inject_settings():
    # Fetch settings safely with defaults
    def get_setting(key, default):
        item = db.session.get(AppSetting, key) 
        return item.value if item else default

    return dict(
        org_name=get_setting('org_name', 'My Organization'),
        org_logo=get_setting('org_logo', None),
        theme_color=get_setting('theme_color', '#0d6efd'),
        github_link=get_setting('github_link', 'https://github.com/felexion/quorum'),
        app_version="0.1",
        app_author="Rexvictor"
    )

# --- ROUTES ---

@app.route('/')
def home():
    ongoing_meetings = Meeting.query.filter_by(status='Ongoing').order_by(Meeting.date.desc()).all()
    finished_meetings = Meeting.query.filter_by(status='Finished').order_by(Meeting.date.desc()).all()
    return render_template('home.html', ongoing=ongoing_meetings, finished=finished_meetings)

@app.route('/members')
def members():
    all_members = Member.query.all()
    all_roles = Role.query.all()
    return render_template('members.html', members=all_members, roles=all_roles)

@app.route('/members/add', methods=['POST'])
def add_member():
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    primary_role = request.form.get('primary_role')
    secondary_role = request.form.get('secondary_role')
    new_member = Member(first_name=first_name, last_name=last_name, primary_role=primary_role, secondary_role=secondary_role)
    db.session.add(new_member)
    db.session.commit()
    return redirect(url_for('members'))

@app.route('/members/delete/<int:id>')
def delete_member(id):
    member = Member.query.get_or_404(id)
    db.session.delete(member)
    db.session.commit()
    return redirect(url_for('members'))

@app.route('/settings')
def settings():
    roles = Role.query.all()
    current_settings = {
        'org_name': db.session.get(AppSetting, 'org_name'),
        'theme_color': db.session.get(AppSetting, 'theme_color')
    }
    return render_template('settings.html', roles=roles, settings=current_settings)

@app.route('/settings/update_app', methods=['POST'])
def update_app_settings():
    name = request.form.get('org_name')
    theme = request.form.get('theme_color')

    for key, val in [('org_name', name), ('theme_color', theme)]:
        setting = db.session.get(AppSetting, key)
        
        if not setting:
            setting = AppSetting(key=key, value=val)
            db.session.add(setting)
        else:
            setting.value = val

    if 'org_logo' in request.files:
        file = request.files['org_logo']
        if file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            logo_setting = db.session.get(AppSetting, 'org_logo')
            
            if not logo_setting:
                db.session.add(AppSetting(key='org_logo', value=filename))
            else:
                logo_setting.value = filename

    db.session.commit()
    return redirect(url_for('settings'))

@app.route('/meetings')
def meetings():
    all_meetings = Meeting.query.order_by(Meeting.date.desc()).all()
    return render_template('meetings.html', meetings=all_meetings)

@app.route('/meetings/add', methods=['POST'])
def add_meeting():
    title = request.form.get('title')
    meeting_type = request.form.get('meeting_type')
    location = request.form.get('location')
    quorum_req = request.form.get('quorum_required')
    date_str = request.form.get('date')
    
    # Handle Agenda Input (Split by new lines)
    agenda_text = request.form.get('initial_agenda')
    
    try:
        meeting_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
    except ValueError:
        meeting_date = datetime.now()

    new_meeting = Meeting(
        title=title,
        meeting_type=meeting_type,
        location=location,
        quorum_required=int(quorum_req) if quorum_req else 0,
        date=meeting_date
    )
    db.session.add(new_meeting)
    db.session.commit() # Commit first to get the ID

    # Process Agenda Items
    if agenda_text:
        items = agenda_text.split('\n')
        for item in items:
            clean_item = item.strip()
            if clean_item:
                db.session.add(AgendaItem(meeting_id=new_meeting.id, title=clean_item))
        db.session.commit()

    return redirect(url_for('meetings'))

@app.route('/meetings/delete/<int:id>')
def delete_meeting(id):
    meeting = Meeting.query.get_or_404(id)
    db.session.delete(meeting) # Cascade handles children
    db.session.commit()
    return redirect(url_for('meetings'))

@app.route('/meeting/<int:meeting_id>')
def meeting_details(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    all_members = Member.query.all()
    
    attendance_records = Attendance.query.filter_by(meeting_id=meeting_id).all()
    attendance_map = {att.member_id: att.status for att in attendance_records}
    present_count = sum(1 for status in attendance_map.values() if status == 'Present')
    quorum_met = present_count >= meeting.quorum_required

    motions = Motion.query.filter_by(meeting_id=meeting_id).all()
    statements = Statement.query.filter_by(meeting_id=meeting_id).order_by(Statement.timestamp.desc()).all()
    
    # NEW: Fetch Agenda Items
    agenda_items = AgendaItem.query.filter_by(meeting_id=meeting_id).all()

    return render_template('active_meeting.html', 
                           meeting=meeting, 
                           members=all_members, 
                           attendance_map=attendance_map,
                           present_count=present_count,
                           quorum_met=quorum_met,
                           motions=motions,
                           statements=statements,
                           agenda_items=agenda_items) # Pass to template

# --- ACTION ROUTES ---

@app.route('/meeting/<int:meeting_id>/add_agenda_item', methods=['POST'])
def add_agenda_item(meeting_id):
    title = request.form.get('title')
    if title:
        db.session.add(AgendaItem(meeting_id=meeting_id, title=title))
        db.session.commit()
    return redirect(url_for('meeting_details', meeting_id=meeting_id))

@app.route('/meeting/<int:meeting_id>/attendance', methods=['POST'])
def take_attendance(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    all_members = Member.query.all()
    for member in all_members:
        form_key = f"status_{member.id}"
        new_status = request.form.get(form_key)
        attendance = Attendance.query.filter_by(meeting_id=meeting_id, member_id=member.id).first()
        if attendance:
            attendance.status = new_status
        else:
            db.session.add(Attendance(meeting_id=meeting_id, member_id=member.id, status=new_status))
    db.session.commit()
    return redirect(url_for('meeting_details', meeting_id=meeting_id))

@app.route('/meeting/<int:meeting_id>/motion', methods=['POST'])
def add_motion(meeting_id):
    text = request.form.get('text')
    proposer_id = request.form.get('proposer_id')
    seconder_id = request.form.get('seconder_id')
    status = request.form.get('status')
    vote_results = request.form.get('vote_results')
    # NEW: Capture Agenda Link
    agenda_item_id = request.form.get('agenda_item_id')

    new_motion = Motion(
        meeting_id=meeting_id,
        text=text,
        proposer_id=proposer_id if proposer_id else None,
        seconder_id=seconder_id if seconder_id else None,
        status=status,
        vote_results=vote_results,
        agenda_item_id=agenda_item_id if agenda_item_id else None
    )
    db.session.add(new_motion)
    db.session.commit()
    return redirect(url_for('meeting_details', meeting_id=meeting_id))

@app.route('/meeting/<int:meeting_id>/statement', methods=['POST'])
def add_statement(meeting_id):
    speaker_id = request.form.get('speaker_id')
    content = request.form.get('content')
    # NEW: Capture Agenda Link
    agenda_item_id = request.form.get('agenda_item_id')

    new_statement = Statement(
        meeting_id=meeting_id,
        speaker_id=speaker_id if speaker_id else None,
        content=content,
        agenda_item_id=agenda_item_id if agenda_item_id else None,
        timestamp=datetime.now()
    )
    db.session.add(new_statement)
    db.session.commit()
    return redirect(url_for('meeting_details', meeting_id=meeting_id))

@app.route('/meeting/<int:id>/adjourn', methods=['POST'])
def adjourn_meeting(id):
    meeting = Meeting.query.get_or_404(id)
    meeting.status = 'Finished'
    meeting.ended_at = datetime.now()
    db.session.commit()
    return redirect(url_for('meetings')) # Go back to dashboard on finish

# --- DELETE ROUTES (Keep existing delete routes for motion/statement) ---
@app.route('/motion/delete/<int:id>')
def delete_motion(id):
    motion = Motion.query.get_or_404(id)
    mid = motion.meeting_id
    db.session.delete(motion)
    db.session.commit()
    return redirect(url_for('meeting_details', meeting_id=mid))

@app.route('/statement/delete/<int:id>')
def delete_statement(id):
    stmt = Statement.query.get_or_404(id)
    mid = stmt.meeting_id
    db.session.delete(stmt)
    db.session.commit()
    return redirect(url_for('meeting_details', meeting_id=mid))

@app.route('/meeting/<int:meeting_id>/report')
def generate_report(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    all_members = Member.query.all()
    attendance_records = Attendance.query.filter_by(meeting_id=meeting_id).all()
    attendance_map = {att.member_id: att.status for att in attendance_records}
    present_count = sum(1 for status in attendance_map.values() if status == 'Present')
    quorum_met = present_count >= meeting.quorum_required
    
    # We pass raw lists, grouping happens in HTML for simplicity or via a smart loop
    agenda_items = AgendaItem.query.filter_by(meeting_id=meeting_id).all()
    # Helper: Get motions/statements that have NO agenda link
    general_motions = Motion.query.filter_by(meeting_id=meeting_id, agenda_item_id=None).all()
    general_statements = Statement.query.filter_by(meeting_id=meeting_id, agenda_item_id=None).order_by(Statement.timestamp).all()

    return render_template('report.html', meeting=meeting, members=all_members, 
                           attendance_map=attendance_map, present_count=present_count, quorum_met=quorum_met,
                           agenda_items=agenda_items, general_motions=general_motions, general_statements=general_statements)

# --- ROLE MANAGEMENT ROUTES ---

@app.route('/settings/add_role', methods=['POST'])
def add_role():
    role_name = request.form.get('role_name')
    # Check if name exists and isn't empty
    if role_name and not Role.query.filter_by(name=role_name).first():
        db.session.add(Role(name=role_name))
        db.session.commit()
    return redirect(url_for('settings'))

@app.route('/settings/delete_role/<int:id>')
def delete_role(id):
    # We use db.session.get for specific IDs
    role = db.session.get(Role, id)
    if role:
        db.session.delete(role)
        db.session.commit()
    return redirect(url_for('settings'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)