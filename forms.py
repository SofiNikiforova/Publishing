from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=150)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class RegisterForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=150)])
    email = StringField('Электронная почта', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[
        DataRequired(),
        Length(min=6),
        EqualTo('confirm_password', message='Пароли должны совпадать.')
    ])
    role = SelectField('Тип профиля', choices=[('client', 'Клиент'), ('admin', 'Администратор')],
                       validators=[DataRequired()])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')
