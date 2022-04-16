import datetime
from flask import Flask, render_template, request
from os import getenv
from werkzeug.utils import redirect
from data import db_session
from data.news import News
from data.users import User
from forms.news import NewsForm
from forms.user import RegisterForm, LoginForm, Check, Reset_password
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_restful import abort
import socket

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = getenv('SECRET_KEY')

def abort_if_news_not_found(news_id):
    session = db_session.create_session()
    news = session.query(User).get(news_id)
    if not news:
        abort(404, message=f"Password {news_id} not found")


@app.route("/")
def index():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        news = db_sess.query(News).filter(
            (News.user == current_user) | (News.is_private != True))
    else:
        news = db_sess.query(News).filter(News.is_private != True)
    return render_template("index.html", news=news)

@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                form=form,
                                message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)




@app.route('/news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NewsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id,
                                       News.user == current_user
                                       ).first()
        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.is_private.data = news.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id,
                                       News.user == current_user
                                       ).first()
        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('news.html',
                            title='Редактирование новости',
                            form=form
                            )

@app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id,
                                News.user == current_user
                            ).first()
    if news:
        db_sess.delete(news)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')



@app.route("/reset_password", methods=['GET', 'POST'])
def reset_password():
    global a
    form = Reset_password()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('reset_password.html', title='Востановление пароля',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        user = a
        if user.check_password(form.password.data):
            return render_template('reset_password.html', title='Востановление пароля',
                                   form=form,
                                   message="Пароль не должен быть прошлым ")

        user.hashed_password = form.password.data
        # db_sess.add(user)
        db_sess.commit()
    return render_template("reset_password.html", title="Востановление пароля", form=form)

@app.route('/check', methods=['GET', 'POST'])
def check():
    form = Check()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user:
            return_email(user)
            return redirect('/reset_password')
        return render_template("check.html", title='Востановление пароля', message="Не найдена почта", form=form)
    return render_template("check.html", title='Востановление пароля', form=form)

def return_email(user):
    global a
    a = user
    print(a, "f")




@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', title='Авторизация',
                           message="Неправильный лoгин или парoль",
                           form=form)
    return render_template('login.html', title='Авторизация', form=form)

@app.route('/news', methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data
        current_user.news.append(news)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('news.html', title='Добавление новости',
    form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)

def main():
    db_session.global_init("db/blogs.db")
    app.run(host="0.0.0.0", port=5595)

if __name__ == '__main__':
    main()
