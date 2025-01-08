from extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    role = db.Column(db.String(50), nullable=False)  # admin или client


class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_title = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default='В ожидании')  # "В ожидании", "Принято", "Отклонено"


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    client = db.relationship('User', backref='orders', lazy=True)  # Добавлено

    product_type = db.Column(db.String(50), nullable=False)

    # Поля для книги
    book_title = db.Column(db.String(200), nullable=True)
    author_name = db.Column(db.String(100), nullable=True)
    pages_count = db.Column(db.Integer, nullable=True)
    binding_type = db.Column(db.String(50), nullable=True)
    paper_type = db.Column(db.String(50), nullable=True)
    copies_count = db.Column(db.Integer, nullable=True)

    # Поля для журнала
    magazine_title = db.Column(db.String(200), nullable=True)
    magazine_pages_count = db.Column(db.Integer, nullable=True)
    magazine_paper_type = db.Column(db.String(50), nullable=True)
    magazine_copies_count = db.Column(db.Integer, nullable=True)

    # Поля для рекламы
    advertisement_paper_type = db.Column(db.String(50), nullable=True)
    advertisement_image_filename = db.Column(db.String(200), nullable=True)

    # Общее поле для файла
    file_name = db.Column(db.String(200), nullable=True)

    # Временные метки
    status = db.Column(db.String(50), default="Ожидает обработки")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assigned_employee = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f'<Order {self.id}>'


