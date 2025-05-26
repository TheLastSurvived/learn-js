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
from flask_cors import CORS
from flask_migrate import Migrate
import subprocess
import os
import tempfile


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
app.config['UPLOAD_FOLDER'] = 'static/img/upload'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
db = SQLAlchemy(app)
ckeditor = CKEditor(app)
CORS(app)
migrate = Migrate(app, db)

CORS(app, resources={
    r"/api/*": {"origins": "*"},  
    r"/lesson/*": {"origins": "*"}, 
    r"/task/*": {"origins": "*"}
})


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

    userSolution = db.relationship('UserSolution', backref='lesson', lazy=True)
    tasks = db.relationship('Task', backref='lesson', lazy=True)
    
    def __repr__(self):
            return 'Lesson %r' % self.id
    

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.Text, nullable=False)
    solution = db.Column(db.Text, nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'))

    def __repr__(self):
            return 'Lesson %r' % self.id

    

class UserSolution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'))
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))  # Добавляем связь с заданием
    code = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.now)
    is_correct = db.Column(db.Boolean)
    
    task = db.relationship('Task', backref='solutions')  # Добавляем связь
    
    def __repr__(self):
        return 'User Solution %r' % self.id


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    user = db.relationship('Users', backref='comments')
    lesson = db.relationship('Lesson', backref='comments')
    
    def __repr__(self):
        return 'Comment %r' % self.id
    

class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    questions = db.relationship('TestQuestion', backref='test', lazy=True)

class TestQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'))
    question = db.Column(db.Text, nullable=False)
    code_snippet = db.Column(db.Text)
    options = db.Column(db.JSON)  # {'a': 'вариант1', 'b': 'вариант2'}
    correct_answer = db.Column(db.String(1), nullable=False)  # 'a', 'b' и т.д.

class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'))
    score = db.Column(db.Integer)
    total_questions = db.Column(db.Integer)
    completed_at = db.Column(db.DateTime, default=datetime.now)



class AdminIndex(AdminIndexView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        if 'name' in session:
            user = Users.query.filter_by(email=session['name']).first()
            if user.root!=1:
                abort(403)
            else:
                return self.render('admin/dashboard_index.html')
        else:
            abort(401)

class CommentView(ModelView):
    column_display_pk = True 
    column_hide_backrefs = False
    column_list = [ 'user_id', 'lesson_id', 'content', 'created_at']


class SolutionView(ModelView):
    column_display_pk = True 
    column_hide_backrefs = False
    column_list = [ 'user_id', 'lesson_id', 'task_id', 'code', 'submitted_at', 'is_correct']


class TaskView(ModelView):
    column_display_pk = True 
    column_hide_backrefs = False
    column_list = [ 'task', 'solution', 'lesson_id']


admin = Admin(app, name='JS учебник',index_view=AdminIndex())
admin.add_view(ModelView(Users, db.session))
admin.add_view(ModelView(Lesson, db.session))
admin.add_view(SolutionView(UserSolution, db.session))
admin.add_view(CommentView(Comment, db.session))
admin.add_view(TaskView(Task, db.session))
admin.add_view(ModelView(Test, db.session))
admin.add_view(ModelView(TestQuestion, db.session))
admin.add_view(ModelView(TestResult, db.session))


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
    page = request.args.get('page', 1, type=int)
    per_page = 5  # Количество уроков на странице
    
    # Получаем уроки с пагинацией
    pagination = Lesson.query.order_by(Lesson.id).paginate(page=page, per_page=per_page, error_out=False)
    
    top_users = db.session.query(
        Users,
        db.func.count(UserSolution.lesson_id.distinct()).label('completed_count')
    ).join(
        UserSolution, Users.id == UserSolution.user_id
    ).filter(
        UserSolution.is_correct == True
    ).group_by(
        Users.id
    ).order_by(
        db.desc('completed_count')
    ).limit(5).all()

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
    
    return render_template("lessons.html", pagination=pagination, top_users=top_users)


@app.route('/lesson/<int:id>', methods=['GET', 'POST'])
def lesson(id):
    if not 'name' in session:
        flash("Для продолжения необходимо войти!", category="success")
        return redirect('/auth')

    less = Lesson.query.get(id)
    if not less:
        abort(404)
    
    comments = Comment.query.filter_by(lesson_id=id).order_by(Comment.created_at.desc()).all()
    prev_lesson = Lesson.query.filter(Lesson.id < id).order_by(Lesson.id.desc()).first()
    next_lesson = Lesson.query.filter(Lesson.id > id).order_by(Lesson.id.asc()).first()
    total_user = Users.query.filter_by(email=session['name']).first()

    # Получаем все задания для урока
    tasks = Task.query.filter_by(lesson_id=id).all()


    all_tasks_completed = True
    if 'name' in session:
        user = Users.query.filter_by(email=session['name']).first()
        for task in tasks:
            solution = UserSolution.query.filter_by(
                user_id=user.id,
                lesson_id=id,
                task_id=task.id,
                is_correct=True
            ).first()
            if not solution:
                all_tasks_completed = False
                break
   

    if request.method == 'POST':
        # Обработка добавления нового задания
        if 'new_task' in request.form:
            task_text = request.form.get('task')
            solution_text = request.form.get('solution')
            if task_text and solution_text:
                new_task = Task(task=task_text, solution=solution_text, lesson_id=id)
                db.session.add(new_task)
                db.session.commit()
                flash("Задание добавлено!", category="success")
        
        # Обработка редактирования урока
        elif 'edit_lesson' in request.form:
            less.title = request.form.get('title')
            less.description = request.form.get('description')
            less.content = request.form.get('ckeditor')
            db.session.commit()
            flash("Урок обновлен!", category="success")

        elif 'edit_task' in request.form:
            id_task = request.form.get('task_id')
            task = Task.query.get(id_task)
            task.task = request.form.get('task')
            task.solution = request.form.get('solution')
            db.session.commit()
            flash("Задание обновлено!", category="success")
        
        return redirect(url_for("lesson", id=id))

    return render_template("lesson.html", less=less, prev_lesson=prev_lesson,
                         next_lesson=next_lesson, comments=comments, tasks=tasks, all_tasks_completed=all_tasks_completed)


@app.route('/delete-task/<int:id_task>/<int:id_article>')
def delete_task(id_task,id_article):
    obj = Task.query.filter_by(id=id_task).first()
    db.session.delete(obj)
    db.session.commit()
    flash("Задание удалёно!", category="warning")
    return redirect(url_for("lesson", id=id_article))


@app.route('/delete-lesson/<int:id>')
def delete_article(id):
    obj = Lesson.query.filter_by(id=id).first()
    db.session.delete(obj)
    db.session.commit()
    flash("Урок удалён!", category="warning")
    return redirect('/lessons')

    

@app.route('/api/task/<int:id>', methods=['GET'])
def get_users(id):
    task = Task.query.get(id)
    
    response = jsonify({
        'id': task.id,
        'task': task.task,
        'solution': task.solution,
        'lesson_id': task.lesson_id
    })
    
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/api/save-solution', methods=['POST'])
def save_solution():
    try:
        data = request.get_json()
        required_fields = ['user_id', 'lesson_id', 'task_id', 'code', 'is_correct']
       
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        existing_solution = UserSolution.query.filter_by(
            user_id=data['user_id'],
            task_id=data['task_id']
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
                task_id=data['task_id'],
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
    
    user = Users.query.filter_by(email=session['name']).first()
    user_id = user.id
    
    # Получаем все уроки
    all_lessons = Lesson.query.all()
    total_lessons = len(all_lessons)
    
    # Считаем пройденные уроки (где выполнены ВСЕ задания)
    completed_lessons = 0
    lessons_progress = []
    
    for lesson in all_lessons:
        tasks = Task.query.filter_by(lesson_id=lesson.id).all()
        total_tasks = len(tasks)
        
        if total_tasks == 0:
            continue
            
        completed_tasks = 0
        for task in tasks:
            solution = UserSolution.query.filter_by(
                user_id=user_id,
                lesson_id=lesson.id,
                task_id=task.id,
                is_correct=True
            ).first()
            if solution:
                completed_tasks += 1
                
        is_lesson_completed = (completed_tasks == total_tasks)
        if is_lesson_completed:
            completed_lessons += 1
            
        lessons_progress.append({
            'lesson': lesson,
            'completed_tasks': completed_tasks,
            'total_tasks': total_tasks,
            'is_completed': is_lesson_completed
        })
    
    progress_percent = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0
    
    # Последние решения (ограничим 10 последними)
    recent_solutions = UserSolution.query.filter_by(user_id=user_id)\
        .order_by(UserSolution.submitted_at.desc())\
        .limit(10)\
        .all()
    
    return render_template("profile.html",
        progress_percent=progress_percent,
        completed_lessons=completed_lessons,
        total_lessons=total_lessons,
        recent_solutions=recent_solutions,
        lessons_progress=lessons_progress,
        now=datetime.now,
        user=user
    )


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


@app.route('/add-comment/<int:lesson_id>', methods=['POST'])
def add_comment(lesson_id):
    if not 'name' in session:
        abort(401)
    
    content = request.form.get('comment_content')
    if not content:
        flash("Комментарий не может быть пустым", "warning")
        return redirect(url_for('lesson', id=lesson_id))
    
    user = Users.query.filter_by(email=session['name']).first()
    
    new_comment = Comment(
        user_id=user.id,
        lesson_id=lesson_id,
        content=content
    )
    
    db.session.add(new_comment)
    db.session.commit()
    
    flash("Комментарий добавлен", "success")
    return redirect(url_for('lesson', id=lesson_id))



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
