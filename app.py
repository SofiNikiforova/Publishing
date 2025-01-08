from flask import Flask, redirect, url_for, flash, render_template, request, send_from_directory
from flask_migrate import Migrate
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from extensions import db, login_manager
from forms import LoginForm, RegisterForm
from models import User
from models import Order
import os
from flask import jsonify
from datetime import datetime, timedelta





def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Инициализация расширений
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    # Инициализация Flask-Migrate
    migrate = Migrate(app, db)


    with app.app_context():
        from models import Order, Request  # Импорт здесь, чтобы избежать циклического импорта
        db.create_all()
    return app




@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app = create_app()

@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            if user.role == 'client':
                return redirect(url_for('about'))
            else:
                return redirect(url_for('admin_dashboard'))
        flash('Неверное имя пользователя или пароль', 'danger')
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = generate_password_hash(form.password.data)
        role = form.role.data  # 'client' или 'admin'

        # Создание нового пользователя
        new_user = User(username=username, email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash('Аккаунт успешно создан!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)
@app.route('/about')
@login_required
def about():
    if current_user.role == 'client':
        return render_template('about.html')
    return redirect(url_for('dashboard'))

# Создаем директорию для хранения загружаемых файлов
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/new_order', methods=['GET', 'POST'])
@login_required
def new_order():
    if current_user.role != 'client':
        flash('У вас нет доступа к этой странице.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        product_type = request.form.get('product_type')

        # Проверка корректности типа продукции
        if product_type not in ['book', 'magazine', 'advertisement']:
            flash('Выберите корректный тип продукции.', 'danger')
            return redirect(url_for('new_order'))

        order_data = {
            "client_id": current_user.id,
            "product_type": product_type,
            "status": 'Ожидает обработки'
        }

        try:
            file_upload = request.files.get('file_upload')
            if file_upload and file_upload.filename:
                # Используем оригинальное имя файла, безопасное для системы
                original_filename = secure_filename(file_upload.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
                file_upload.save(file_path)

                # Сохраняем имя файла в базе данных
                order_data["file_name"] = original_filename

            # Обработка данных по типу продукции
            if product_type == 'book':
                order_data.update({
                    "book_title": request.form.get('book_title'),
                    "author_name": request.form.get('author_name'),
                    "pages_count": int(request.form.get('pages_count')),
                    "binding_type": request.form.get('binding_type'),
                    "paper_type": request.form.get('paper_type'),
                    "copies_count": int(request.form.get('copies_count'))
                })

            elif product_type == 'magazine':
                order_data.update({
                    "magazine_title": request.form.get('magazine_title'),
                    "magazine_pages_count": int(request.form.get('magazine_pages')),
                    "magazine_paper_type": request.form.get('magazine_paper_type'),
                    "magazine_copies_count": int(request.form.get('magazine_copies'))
                })

            elif product_type == 'advertisement':
                if not file_upload or not file_upload.filename.endswith('.png'):
                    flash('Для рекламной продукции требуется загрузить файл в формате PNG.', 'danger')
                    return redirect(url_for('new_order'))
                order_data["advertisement_paper_type"] = request.form.get('advertisement_paper_type')

            # Создание и сохранение заявки
            order = Order(**order_data)
            db.session.add(order)
            db.session.commit()

            flash('Заявка успешно отправлена!', 'success')
            return redirect(url_for('profile'))

        except Exception as e:
            flash(f'Ошибка при отправке заявки: {e}', 'danger')
            return redirect(url_for('new_order'))

    return render_template('client_order.html')



@app.route('/edit_order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def edit_order(order_id):
    if current_user.role != 'client':
        flash('У вас нет доступа к этой странице.', 'danger')
        return redirect(url_for('profile'))

    # Получаем заявку
    order = Order.query.get_or_404(order_id)

    if order.status != 'Требуется доработка':
        flash('Вы не можете редактировать эту заявку.', 'danger')
        return redirect(url_for('profile'))

    if request.method == 'POST':
        # Обновляем только допустимые поля в зависимости от типа продукции
        if order.product_type == 'book':
            order.book_title = request.form.get('book_title')
            order.author_name = request.form.get('author_name')
            order.pages_count = int(request.form.get('pages_count'))
            order.binding_type = request.form.get('binding_type')
            order.paper_type = request.form.get('paper_type')
            order.copies_count = int(request.form.get('copies_count'))
        elif order.product_type == 'magazine':
            order.magazine_title = request.form.get('magazine_title')
            order.magazine_pages_count = int(request.form.get('magazine_pages'))
            order.magazine_paper_type = request.form.get('magazine_paper_type')
            order.magazine_copies_count = int(request.form.get('magazine_copies'))
        elif order.product_type == 'advertisement':
            file_upload = request.files.get('file_upload')
            if file_upload and file_upload.filename.endswith('.png'):
                filename = secure_filename(file_upload.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file_upload.save(file_path)
                order.advertisement_image_filename = filename
            else:
                flash('Для рекламной продукции загрузите файл в формате PNG.', 'danger')
                return redirect(url_for('edit_order', order_id=order.id))

        order.status = 'Ожидает обработки'
        db.session.commit()

        flash('Заявка обновлена и отправлена на повторную обработку.', 'success')
        return redirect(url_for('profile'))

    return render_template('edit_order.html', order=order)


@app.route('/profile')
@login_required
def profile():
    if current_user.role != 'client':
        flash('У вас нет доступа к этой странице.', 'danger')
        return redirect(url_for('index'))

    # Получаем заявки текущего клиента
    orders = Order.query.filter_by(client_id=current_user.id).all()

    return render_template('client_profile.html', orders=orders)



@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Доступ запрещен!', 'danger')
        return redirect(url_for('about'))

    orders = Order.query.all()
    return render_template('admin_dashboard.html', orders=orders)



@app.route('/uploads/<filename>')
@login_required
def download_order_file(filename):  # Изменили имя функции
    if current_user.role != 'admin':
        flash('У вас нет доступа к скачиванию файлов.', 'danger')
        return redirect(url_for('admin_dashboard'))

    # Путь к файлу
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Проверяем, существует ли файл
    if not os.path.exists(file_path):
        flash('Файл не найден.', 'danger')
        return redirect(url_for('admin_dashboard'))

    # Возвращаем файл с оригинальным именем
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename,
        as_attachment=True,
        download_name=filename
    )


@app.route('/view_order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def view_order(order_id):
    if current_user.role != 'admin':
        flash('У вас нет доступа к этой странице.', 'danger')
        return redirect(url_for('admin_dashboard'))

    # Получаем заявку
    order = Order.query.get_or_404(order_id)

    if request.method == 'POST':
        # Обновляем статус заявки
        new_status = request.form.get('status')
        if new_status:
            order.status = new_status
            db.session.commit()
            flash('Статус заявки обновлен.', 'success')
            return redirect(url_for('admin_dashboard'))

    return render_template('view_order.html', order=order)


@app.route('/analytics', methods=['GET'])
@login_required
def analytics():
    if current_user.role != 'admin':
        flash('У вас нет доступа к этой странице.', 'danger')
        return redirect(url_for('admin_dashboard'))

    # Получаем текущую дату
    today = datetime.now()

    # Статистика заявок
    weekly_data = get_analytics_data(today - timedelta(days=7), today)
    monthly_data = get_analytics_data(today - timedelta(days=30), today)
    yearly_data = get_analytics_data(today - timedelta(days=365), today)

    return render_template(
        'analytics.html',
        weekly_data=weekly_data,
        monthly_data=monthly_data,
        yearly_data=yearly_data,
    )


def get_analytics_data(start_date, end_date):
    """Вспомогательная функция для подсчета статистики заявок"""
    total_orders = Order.query.filter(Order.created_at >= start_date, Order.created_at <= end_date).count()
    statuses = db.session.query(Order.status, db.func.count(Order.status)).filter(
        Order.created_at >= start_date,
        Order.created_at <= end_date,
    ).group_by(Order.status).all()

    # Преобразуем данные в удобный для графика формат
    return {
        "total_orders": total_orders,
        "statuses": {status: count for status, count in statuses},
    }

@app.route('/admin/employees')
@login_required
def admin_employees():
    if current_user.role != 'admin':
        flash('У вас нет доступа к этой странице.', 'danger')
        return redirect(url_for('about'))

    # Список сотрудников (можно заменить на данные из базы данных)
    employees = [
        {"name": "Иван Иванов", "photo": "ivan.jpg", "position": "Менеджер", "department": "Продажи"},
        {"name": "Анна Смирнова", "photo": "anna.jpg", "position": "Дизайнер", "department": "Маркетинг"},
        {"name": "Сергей Петров", "photo": "sergey.jpg", "position": "Разработчик", "department": "ИТ"},
    ]

    return render_template('admin_employees.html', employees=employees)

@app.route('/assign_employee/<int:order_id>', methods=['POST'])
@login_required
def assign_random_employee(order_id):
    if current_user.role != 'admin':
        flash('У вас нет доступа к этому действию.', 'danger')
        return redirect(url_for('admin_dashboard'))

    order = Order.query.get_or_404(order_id)
    assigned_employee = request.form.get('assigned_employee')

    if not assigned_employee:
        flash('Выберите сотрудника.', 'danger')
        return redirect(url_for('view_order', order_id=order_id))

    # Сохраняем имя выбранного сотрудника
    order.assigned_employee = assigned_employee
    db.session.commit()

    flash(f'Сотрудник {assigned_employee} назначен на заявку #{order.id}.', 'success')
    return redirect(url_for('view_order', order_id=order_id))



@app.route('/user_dashboard')
@login_required
def user_dashboard():
    if current_user.role != 'client':
        flash('Доступ запрещен!', 'danger')
        return redirect(url_for('login'))
    return render_template('user_dashboard.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Create test admin profile
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin_user)

        # Create test client profile
        if not User.query.filter_by(username='client').first():
            client_user = User(
                username='client',
                email='client@example.com',
                password=generate_password_hash('client123'),
                role='client'
            )
            db.session.add(client_user)

        db.session.commit()

    app.run(debug=True)
