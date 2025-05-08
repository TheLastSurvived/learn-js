from flask import Flask, render_template, request, flash, redirect, session, url_for, abort, make_response,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor
from hashlib import md5
from  sqlalchemy.sql.expression import func
from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqlamodel import ModelView
from flask_admin import Admin
from datetime import datetime
import uuid
import re
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
app.config['UPLOAD_FOLDER'] = 'static/img/upload'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
db = SQLAlchemy(app)
ckeditor = CKEditor(app)


class Users(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100))
    surname = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100), unique=True)
    root = db.Column(db.Integer, default=0)
    join_date = db.Column(db.DateTime, default=datetime.now)
    avatar = db.Column(db.String(120), default='default.jpg')

    userSolution = db.relationship('UserSolution', backref='users', lazy=True)
           
    def __repr__(self):
        return 'User %r' % self.id
    

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    task = db.Column(db.Text, nullable=False)
    solution = db.Column(db.Text, nullable=False)

    userSolution = db.relationship('UserSolution', backref='lesson', lazy=True)
    
    def __repr__(self):
            return 'Lesson %r' % self.id
    

class UserSolution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'))
    code = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.now)
    is_correct = db.Column(db.Boolean)

    
    def __repr__(self):
            return 'User Solution %r' % self.id


@app.route('/', methods=['GET', 'POST'])
def index():
    lesson = Lesson.query.limit(3).all()
    return render_template("index.html",lesson=lesson)


@app.route('/about', methods=['GET', 'POST'])
def about():
    return render_template("about.html")


@app.route('/auth', methods=['GET', 'POST'])
def auth():
    session.pop('name', None)
    return render_template("auth.html")


@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = md5(request.form.get('password').encode()).hexdigest()
        user = Users.query.filter_by(email=email,password=password).first()
        if user:
            session['name'] = Users.query.filter_by(email=email).first().email
            return redirect(url_for("index"))
        else:
            flash("Неправильная почта или пароль!", category="warning")
            return redirect(url_for("auth"))
        

@app.route('/regestration', methods=['POST'])
def regestration():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            surname = request.form.get('surname')
            email = request.form.get('email')
            password = request.form.get('password')
            user = Users(name=name,surname=surname,email=email,password=md5(password.encode()).hexdigest())
            db.session.add(user)
            db.session.commit()
            session['name'] = Users.query.filter_by(email=email).first().email
            flash("Регистрация прошла успешно!", category="success")
            return redirect(url_for("index"))
        except:
            flash("Произошла ошибка! Проверьте введенные данные!", category="warning")
            db.session.rollback()
            return redirect(url_for("auth"))


@app.route('/lessons', methods=['GET', 'POST'])
def lessons():
    lesson = Lesson.query.all()
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        task = request.form.get('task')
        solution = request.form.get('solution')
        content = request.form.get('ckeditor')
        lesson = Lesson(title=title,description=description,task=task,solution=solution,content=content)
        db.session.add(lesson)
        db.session.commit()
        flash("Урок добавлен!", category="success")
        return redirect(url_for("lessons"))
    return render_template("lessons.html",lesson=lesson)


@app.route('/lesson/<int:id>', methods=['GET', 'POST'])
def lesson(id):
    if not 'name' in session:
        flash("Для продолжения  необходимо войти!", category="success")
        return redirect('/auth')

    less = Lesson.query.get(id)
    count = Lesson.query.count()
    
    prev_lesson = Lesson.query.filter(Lesson.id < id)\
                            .order_by(Lesson.id.desc()).first()
    
    
    next_lesson = Lesson.query.filter(Lesson.id > id)\
                            .order_by(Lesson.id.asc()).first()
    
    total_user = Users.query.filter_by(email=session['name']).first()


    existing_solution = UserSolution.query.filter_by(
            user_id=total_user.id,
            lesson_id=id
        ).first()


    if request.method == 'POST':
        less.title = request.form.get('title')
        less.description = request.form.get('description')
        less.task = request.form.get('task')
        less.solution = request.form.get('solution')
        less.content = request.form.get('ckeditor')
        db.session.commit()
        flash("Урок обновлен!", category="success")
        return redirect(url_for("lesson", id=less.id, index=index))

    return render_template("lesson.html",less=less,count=count,id=id,prev_lesson=prev_lesson,
                         next_lesson=next_lesson,existing_solution=existing_solution)


@app.route('/delete-lesson/<int:id>')
def delete_article(id):
    obj = Lesson.query.filter_by(id=id).first()
    db.session.delete(obj)
    db.session.commit()
    flash("Урок удалена!", category="warning")
    return redirect('/lessons')


@app.route('/api/lesson//<int:id>', methods=['GET'])
def get_users(id):
    lesson = Lesson.query.get(id)
    
    return jsonify({
        'id': lesson.id,
        'title': lesson.title,
        'content': lesson.content,
        'task': lesson.task,
        'solution' : lesson.solution
    })


@app.route('/api/save-solution', methods=['POST'])
def save_solution():
    try:
        data = request.get_json()
        required_fields = ['user_id', 'lesson_id', 'code', 'is_correct']

        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        existing_solution = UserSolution.query.filter_by(
            user_id=data['user_id'],
            lesson_id=data['lesson_id']
        ).first()

        if existing_solution:
            existing_solution.code = data['code']
            existing_solution.is_correct = data['is_correct']
            existing_solution.submitted_at = datetime.now()
            action = "updated"
        else:
            new_solution = UserSolution(
                user_id=data['user_id'],
                lesson_id=data['lesson_id'],
                code=data['code'],
                is_correct=data['is_correct'],
                submitted_at=datetime.now()
            )
            db.session.add(new_solution)
            action = "created"

        db.session.commit()

        return jsonify({
            "status": "success",
            "action": action,
            "message": f"Solution {action} successfully"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    

def normalize_code(code):
    code = re.sub(r'\s+', ' ', code) 
    code = re.sub(r'//.*?\n', '', code)
    return code.strip()


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not 'name' in session:
        abort(401)
    user_id = Users.query.filter_by(email=session['name']).first().id
    total_lessons = Lesson.query.count()
    completed_lessons = UserSolution.query.filter_by(
        user_id=user_id,
        is_correct=True
    ).distinct(UserSolution.lesson_id).count()

    progress_percent = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0

    return render_template("profile.html",
                         progress_percent=progress_percent,
                         completed_lessons=completed_lessons,
                         total_lessons=total_lessons)


@app.route('/edit_profile', methods=['POST'])
def edit_profile():
    if request.method == 'POST':
        total_user = Users.query.filter_by(email=session['name']).first()
        total_user.name = request.form.get('name')
        total_user.surname = request.form.get('surname')
        total_user.email = request.form.get('email')
        total_user.password = md5(request.form.get('password').encode()).hexdigest()
        db.session.commit()
        session.pop('name', None)
        session['name'] = request.form.get('email')
        flash("Данные обновлены!", category="success")
        
    return redirect(url_for("profile"))


@app.route('/load_avatar', methods=['POST'])
def load_avatar():
    if request.method == 'POST':
        image = request.files['avatar']
        total_user = Users.query.filter_by(email=session['name']).first()
        filename = secure_filename(image.filename)
        pic_name = str(uuid.uuid4()) + "_" + filename
        image.save("static/img/upload/" + pic_name)
        total_user.avatar = pic_name
        db.session.commit()
        flash("Аватар обновлен!", category="success")
        return redirect(url_for("profile"))


@app.errorhandler(405)
def page_not_found(e):
    return render_template('405.html'), 405


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(403)
def forbidded(e):
    return render_template('403.html'), 403


@app.errorhandler(401)
def forbidded(e):
    return render_template('401.html'), 401


@app.context_processor
def inject_user():
    def get_user_name():
        if 'name' in session:
            return Users.query.filter_by(email=session['name']).first()
    return dict(active_user=get_user_name())


@app.route('/logout')
def logout():
    session.pop('name', None)
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
