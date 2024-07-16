from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, FloatField
from wtforms.validators import InputRequired, ValidationError, Optional
from flask_bootstrap import Bootstrap
# from postgresql_config_ini import config
# from sqlalchemy.sql import exists
# from datetime import datetime
import os


app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books-collection.db'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost:3307/librarydb'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1@localhost:5432/library_db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
Bootstrap(app)
# migrate = Migrate(app, db)
app.secret_key = "some secret strings go_here"
# params = config()

class SearchForm(FlaskForm):
    title = StringField(label='title', validators=[Optional()])
    author = StringField(label='author', validators=[Optional()])
    isbn = StringField(label='isbn', validators=[Optional()])
    submit = SubmitField(label='Search')

class UpdateForm(FlaskForm):
    title = StringField(label='title', validators=[InputRequired()])
    author = StringField(label='author', validators=[InputRequired()])
    first_publish = IntegerField(label='first_publish')
    isbn = StringField(label='isbn')
    rating = FloatField(label='rating')
    submit = SubmitField(label='Update')

class AddForm(FlaskForm):
    title = StringField(label='title', validators=[InputRequired()])
    author = StringField(label='author', validators=[InputRequired()])
    isbn = StringField(label='isbn')
    first_publish = IntegerField(label='first_publish', validators=[InputRequired()])
    rating = FloatField(label='rating')
    submit = SubmitField(label='Add Title')

class Books(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(14), nullable=False)
    first_publish = db.Column(db.Numeric(4), nullable=False)
    rating = db.Column(db.Float, nullable=True)

with app.app_context():
    # db.create_all()

    @app.route('/')
    def home():
        books = Books.query.order_by('author').order_by('title').all()
        total = len(books)
        return render_template('index.html', books=books, total=total)

    @app.route('/add_title', methods=['GET', 'POST'])
    def add_title():
        books = Books.query.order_by('author').order_by('title').all()
        total = len(books)
        form = AddForm()
        if request.method == 'POST':
            title = request.form['title']
            author = request.form['author']
            rating = request.form['rating']
            first_publish = int(form.first_publish.data)
            isbn = form.isbn.data
            if not Books.query.filter_by(title=title, author=author, isbn=isbn).first():
                new_book = Books(title=title, author=author, first_publish=first_publish, isbn=isbn, rating=rating)
                db.session.add(new_book)
                db.session.commit()
                redirect(url_for('home'))
            else:
                flash('That book is already in the library.')
        return render_template('add_title.html', form=form, total=total)

    @app.route('/edit_rating', methods=['GET', 'POST'])
    def edit_rating():
        books = Books.query.order_by('author').order_by('title').all()
        total = len(books)
        id = request.args.get('id')
        book = Books.query.get(id)
        if request.method == 'POST':
            book.rating = request.form['rating']
            db.session.commit()
            return redirect(url_for('home'))

        return render_template('edit_rating.html', book=book, total=total)

    @app.route('/search', methods=['GET', 'POST'])
    def search():
        books = Books.query.order_by('author').order_by('title').all()
        total = len(books)
        form = SearchForm()
        if form.validate_on_submit():
            if request.method == 'POST':
                books = Books.query.order_by('author').order_by('title').all()
                total = len(books)
                title_returned = form.title.data
                author_returned = form.author.data
                isbn_returned = form.isbn.data
                form.title.data = ''
                form.author.data = ''
                if Books.query.filter_by(title=title_returned, author=author_returned).first():
                    book = Books.query.filter_by(title=title_returned).filter_by(author=author_returned).first()
                    return redirect(url_for('edit_title', id=book.id, total=total))
                elif Books.query.filter_by(title=title_returned).first() and not Books.query.filter_by(
                        author=author_returned).first():
                    books = Books.query.filter_by(title=title_returned).all()
                    if len(books) > 1:
                        form = SearchForm()
                        return render_template('search.html', form=form, books=books, total=total)
                    else:
                        book = Books.query.filter_by(title=title_returned).first()
                        return redirect(url_for('bibliography', author=book.author, id=book.id, total=total))
                elif Books.query.filter_by(author=author_returned).first() and not Books.query.filter_by(title=title_returned).first():
                    books = Books.query.filter_by(author=author_returned).all()
                    if len(books) > 1:
                        form = SearchForm()
                        print(author_returned)
                        return redirect(url_for('bibliography', author=author_returned, form=form, books=books, total=total))
                    elif len(books) == 1:
                        book = Books.query.filter_by(author=author_returned).first()
                        return redirect(url_for('bibliography', author=author_returned, id=book.id, total=total))
                elif Books.query.filter_by(isbn=isbn_returned):
                    book = Books.query.filter_by(isbn=isbn_returned).first()
                    return redirect(url_for('bibliography', author=book.author, total=total))

                else:
                    flash('Book not found')
                    books = Books.query.order_by('author').all()
                    form = SearchForm()
                    return render_template('search.html', form=form, books=books, total=total)
        id = request.args.get('id')
        book = Books.query.get(id)
        return render_template('search.html', form=form, books=books, total=total)

    @app.route('/edit_title', methods=['GET', 'POST'])
    def edit_title():
        books = Books.query.order_by('author').order_by('title').all()
        total = len(books)
        form = UpdateForm()
        id = request.args.get('id')
        book = Books.query.get(id)
        if request.method == 'POST':
            book.title = request.form['title']
            book.author = request.form['author']
            book.isbn = request.form['isbn']
            book.first_publish = request.form['first_publish']
            book.rating = request.form['rating']
            db.session.commit()
            return redirect(url_for('home'))

        return render_template('edit_title.html', form=form, book=book, total=total)

    @app.route('/delete_title/<int:id>', methods=['GET', 'POST'])
    def delete_title(id):
        book = Books.query.get(id)
        db.session.delete(book)
        db.session.commit()
        return redirect(url_for('home'))

    @app.route('/book_details/<int:id>')
    def book_details(id):
        books = Books.query.order_by('author').order_by('title').all()
        total = len(books)
        book = Books.query.get(id)
        return render_template('book_details.html', book=book, total=total)

    @app.route('/bibliography', methods=['GET', 'POST'])
    def bibliography():
        books = Books.query.order_by('author').order_by('title').all()
        total = len(books)
        author = request.args.get('author')
        books = Books.query.filter_by(author=author).all()
        author_total = len(books)
        return render_template('bibliography.html', books=books, author=author, total=total, author_total=author_total)
# @adp.route("/login", methods=['GET', 'POST'])
# def login():
#     login_form = MyForm()
#
#     if login_form.validate_on_submit():
#         if login_form.email.data == 'admin@email.com' and login_form.pwd.data == '12345678':
#             return render_template('success.html')
#         else:
#             return render_template('denied.html')
#     return render_template('login.html', form=login_form)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
