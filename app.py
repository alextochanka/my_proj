import os
import mysql.connector as mysql
from mysql.connector import Error
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import hashlib
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_default_secret_key')

# Прямо в коде задаём необходимые параметры подключения к базе данных
HOST = 'localhost'          # Адрес сервера баз данных
PORT = 3306                 # Порт подключения
USER = 'root'               # Имя пользователя базы данных
PASSWORD = 'Tochankau110574' # Пароль пользователя
DATABASE_NAME = 'Football'   # Название вашей базы данных

def get_db_connection():
    """
    Функция возвращает соединение с базой данных MySQL.
    Возвращает объект соединения или None в случае неудачи.
    """
    try:
        connection = mysql.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD,
            database=DATABASE_NAME
        )
        return connection
    except Error as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None

def test_connection():
    """
    Тестирует работоспособность подключения к базе данных.
    Возвращает True, если успешно подключился, иначе False.
    """
    try:
        conn = get_db_connection()
        if conn and conn.is_connected():
            conn.close()
            return True
        else:
            return False
    except Error:
        return False

def login_required(role='user'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Требуется авторизация', 'error')
                return redirect(url_for('login'))
            if role == 'admin' and session.get('role') != 'admin':
                flash('Доступ запрещен. Требуются права администратора.', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)

        return decorated_function

    return decorator

def initialize_database():
    if not test_connection():
        print("Не удалось подключиться к MySQL. Проверьте пароль root и запуск сервера.")
        return False
    try:
        temp_conn = mysql.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', 'Tochankau110574')
        )
        with temp_conn.cursor() as temp_cursor:
            temp_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME}")
        temp_conn.close()
        print(f"База данных {DATABASE_NAME} создана или уже существует.")

        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                tables = [  # Список таблиц
                    'CREATE TABLE IF NOT EXISTS gentleman_coefficient (id INT PRIMARY KEY AUTO_INCREMENT, coefficient FLOAT NOT NULL, footballer VARCHAR(255) NOT NULL);',
                    'CREATE TABLE IF NOT EXISTS golden_ball (id INT PRIMARY KEY AUTO_INCREMENT, holder VARCHAR(255) NOT NULL);',
                    'CREATE TABLE IF NOT EXISTS players (id INT PRIMARY KEY AUTO_INCREMENT, victories INT NOT NULL DEFAULT 0, losses INT NOT NULL DEFAULT 0, draws INT NOT NULL DEFAULT 0, player_name VARCHAR(255) NOT NULL);',
                    'CREATE TABLE IF NOT EXISTS clubs (id INT PRIMARY KEY AUTO_INCREMENT, champion_league INT NOT NULL DEFAULT 0, national_championship INT NOT NULL DEFAULT 0, cup INT NOT NULL DEFAULT 0, super_cup INT NOT NULL DEFAULT 0, victories INT NOT NULL DEFAULT 0, losses INT NOT NULL DEFAULT 0, draws INT NOT NULL DEFAULT 0, club_name VARCHAR(255) NOT NULL);',
                    'CREATE TABLE IF NOT EXISTS personal_stats (id INT PRIMARY KEY AUTO_INCREMENT, player_name VARCHAR(255) NOT NULL, goals INT NOT NULL DEFAULT 0, assists INT NOT NULL DEFAULT 0, clean_sheets INT NOT NULL DEFAULT 0);',
                    'CREATE TABLE IF NOT EXISTS awards (id INT PRIMARY KEY AUTO_INCREMENT, top_scorer VARCHAR(255) NOT NULL, top_assist VARCHAR(255) NOT NULL);',
                    'CREATE TABLE IF NOT EXISTS trophies (id INT PRIMARY KEY AUTO_INCREMENT, club_name VARCHAR(255) NOT NULL, trophy_type VARCHAR(100) NOT NULL);',
                    'CREATE TABLE IF NOT EXISTS footballers (id INT PRIMARY KEY AUTO_INCREMENT, first_name VARCHAR(100) NOT NULL, last_name VARCHAR(100) NOT NULL, age INT NOT NULL, club VARCHAR(255) NOT NULL);',
                    'CREATE TABLE IF NOT EXISTS logs (id INT PRIMARY KEY AUTO_INCREMENT, text TEXT NOT NULL);',
                    'CREATE TABLE IF NOT EXISTS users (id INT PRIMARY KEY AUTO_INCREMENT, login VARCHAR(100) NOT NULL UNIQUE, password_hash VARCHAR(255) NOT NULL, role VARCHAR(50) DEFAULT \'user\');'
                ]
                for table_sql in tables:
                    cursor.execute(table_sql)
                cursor.execute("SELECT COUNT(*) FROM users WHERE login = %s;", ('admin',))
                if cursor.fetchone()[0] == 0:
                    admin_password = hashlib.sha256("Админчик".encode()).hexdigest()
                    cursor.execute("INSERT INTO users(login, password_hash, role) VALUES (%s, %s, %s);",
                                   ('admin', admin_password, 'admin'))
                connection.commit()
                return True
    except Error as e:
        print(f"Ошибка инициализации: {e}")
        return False

def encrypt_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def write_log(text):
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                cursor.execute("INSERT INTO logs(text) VALUES (%s);", (f'{timestamp}: {text}',))
                connection.commit()
    except Error as e:
        print(f"Ошибка записи лога: {e}")

# Маршрут Flask
@app.route('/')
def index():
    current_year = datetime.now().year
    return render_template('index.html', current_year=current_year)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form['login']
        password = request.form['password']

        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT id, password_hash, role FROM users WHERE login = %s;", (login_input,))
            user = cursor.fetchone()
            cursor.close()
            connection.close()

            if user and user[1] == encrypt_password(password):
                session['user_id'] = user[0]
                session['login'] = login_input
                session['role'] = user[2]  # Важно: сохраняем роль в сессии
                write_log(f"Пользователь {login_input} вошел в систему с ролью {user[2]}")
                flash('Успешный вход в систему', 'success')
                return redirect(url_for('index'))
            else:
                flash('Неверный логин или пароль', 'error')
        except Error as e:
            flash(f'Ошибка подключения к БД: {str(e)}', 'error')
            print(f"Ошибка в login: {e}")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login_input = request.form['login']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Пароли не совпадают', 'error')
            return render_template('register.html')

        if len(password) < 4:
            flash('Пароль должен быть не менее 4 символов', 'error')
            return render_template('register.html')

        hashed_password = encrypt_password(password)

        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("INSERT INTO users (login, password_hash) VALUES (%s, %s)", (login_input, hashed_password))
            connection.commit()
            flash('Регистрация успешна. Теперь вы можете войти.', 'success')
            write_log(f"Зарегистрирован новый пользователь: {login_input}")
            return redirect(url_for('login'))
        except Error as e:
            if connection:
                connection.rollback()
            if "Duplicate entry" in str(e):
                flash('Пользователь с таким логином уже существует', 'error')
            else:
                flash('Ошибка регистрации', 'error')
                print(f"Ошибка в register: {e}")
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    return render_template('register.html')

@app.route('/logout')
def logout():
    if 'login' in session:
        write_log(f"Пользователь {session.get('login')} вышел из системы")
    session.clear()
    flash('Вы вышли из системы', 'success')
    return redirect(url_for('index'))

@app.route('/vote/player', methods=['GET', 'POST'])
@login_required()
def vote_player():
    if request.method == 'POST':
        # Валидация данных
        first_name = request.form['first_name'].strip()
        last_name = request.form['last_name'].strip()
        age = request.form['age'].strip()
        club = request.form['club'].strip()
        wins = request.form.get('wins', '0').strip()
        losses = request.form.get('losses', '0').strip()
        draws = request.form.get('draws', '0').strip()
        goals = request.form.get('goals', '0').strip()
        assists = request.form.get('assists', '0').strip()
        clean_sheets = request.form.get('clean_sheets', '0').strip()
        gentleman_coef = request.form.get('gentleman_coef', '1.0').strip()

        # Проверка обязательных полей
        if not all([first_name, last_name, age, club]):
            flash('Заполните все обязательные поля', 'error')
            return render_template('vote_player.html')

        try:
            # Преобразование и валидация числовых значений
            age_value = int(age)
            wins_value = int(wins) if wins else 0
            losses_value = int(losses) if losses else 0
            draws_value = int(draws) if draws else 0
            goals_value = int(goals) if goals else 0
            assists_value = int(assists) if assists else 0
            clean_sheets_value = int(clean_sheets) if clean_sheets else 0
            gentleman_coef_value = float(gentleman_coef) if gentleman_coef else 1.0

            # Проверка диапазонов
            validations = [
                (0 <= age_value <= 100, "Возраст должен быть от 0 до 100 лет"),
                (0 <= wins_value <= 100, "Количество побед должно быть от 0 до 100"),
                (0 <= losses_value <= 100, "Количество поражений должно быть от 0 до 100"),
                (0 <= draws_value <= 100, "Количество ничьих должно быть от 0 до 100"),
                (0 <= goals_value <= 100, "Количество голов должно быть от 0 до 100"),
                (0 <= assists_value <= 100, "Количество ассистов должно быть от 0 до 100"),
                (0 <= clean_sheets_value <= 100, "Количество сухих матчей должно быть от 0 до 100"),
                (1 <= gentleman_coef_value <= 5, "Джентльменский коэффициент должен быть от 1 до 5")
            ]

            for condition, error_msg in validations:
                if not condition:
                    flash(error_msg, 'error')
                    return render_template('vote_player.html')

        except ValueError:
            flash('Некорректные числовые значения', 'error')
            return render_template('vote_player.html')

        # Проверка максимального количества футболистов
        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM footballers;")
            count = cursor.fetchone()[0]
            if count >= 30:
                flash('Достигнуто максимальное количество футболистов (30)', 'error')
                return render_template('vote_player.html')

            # Добавление футболиста в базу
            cursor.execute('''INSERT INTO footballers(first_name, last_name, age, club) VALUES (%s, %s, %s, %s);''',
                           (first_name, last_name, age_value, club))
            cursor.execute(
                '''INSERT INTO personal_stats(player_name, goals, assists, clean_sheets) VALUES (%s, %s, %s, %s);''',
                (last_name, goals_value, assists_value, clean_sheets_value))
            cursor.execute('''INSERT INTO players(player_name, victories, losses, draws) VALUES (%s, %s, %s, %s);''',
                           (last_name, wins_value, losses_value, draws_value))

            # Обновление коэффициента джентльменства
            cursor.execute("INSERT INTO gentleman_coefficient(coefficient, footballer) VALUES (%s, %s);",
                           (gentleman_coef_value, f"{first_name} {last_name}"))

            # Обновление статистики клуба
            cursor.execute("SELECT id, victories, losses, draws FROM clubs WHERE club_name = %s;", (club,))
            club_data = cursor.fetchone()
            if club_data:
                club_id, club_victories, club_losses, club_draws = club_data
                new_victories = club_victories + wins_value
                new_losses = club_losses + losses_value
                new_draws = club_draws + draws_value
                cursor.execute("UPDATE clubs SET victories = %s, losses = %s, draws = %s WHERE id = %s;",
                               (new_victories, new_losses, new_draws, club_id))
            else:
                cursor.execute('''INSERT INTO clubs(champion_league, national_championship, cup, super_cup, victories, losses, draws, club_name) 
                              VALUES (0, 0, 0, 0, %s, %s, %s, %s);''', (wins_value, losses_value, draws_value, club))

            connection.commit()
            write_log(f"Добавлен футболист: {first_name} {last_name}, клуб: {club}, возраст: {age_value}")
            flash('Футболист успешно добавлен', 'success')

        except Error as e:
            if connection:
                connection.rollback()
            flash(f'Ошибка при добавлении футболиста: {str(e)}', 'error')
            print(f"Ошибка в vote_player: {e}")
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    return render_template('vote_player.html')

@app.route('/vote/team', methods=['GET', 'POST'])
@login_required()
def vote_team():
    if request.method == 'POST':
        club_name = request.form['club_name'].strip()
        super_cup = request.form.get('super_cup', '0').strip()
        champion_league = request.form.get('champion_league', '0').strip()
        national_championship = request.form.get('national_championship', '0').strip()
        cup = request.form.get('cup', '0').strip()

        if not club_name:
            flash('Название клуба обязательно для заполнения', 'error')
            return render_template('vote_team.html')

        try:
            super_cup_value = int(super_cup) if super_cup else 0
            champion_league_value = int(champion_league) if champion_league else 0
            national_championship_value = int(national_championship) if national_championship else 0
            cup_value = int(cup) if cup else 0

            # Проверка диапазонов
            for val, name in [(super_cup_value, "суперкубков"), (champion_league_value, "лиг чемпионов"),
                              (national_championship_value, "чемпионатов страны"), (cup_value, "кубков")]:
                if val < 0 or val > 2:
                    flash(f'Количество {name} должно быть от 0 до 2', 'error')
                    return render_template('vote_team.html')

        except ValueError:
            flash('Поля статистики должны быть числовыми', 'error')
            return render_template('vote_team.html')

        # Добавление клуба в базу
        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute("SELECT id FROM clubs WHERE club_name = %s;", (club_name,))
            club_id_result = cursor.fetchone()

            if club_id_result:
                club_id = club_id_result[0]
                cursor.execute(
                    "SELECT super_cup, champion_league, national_championship, cup FROM clubs WHERE club_name = %s;",
                    (club_name,))
                old = cursor.fetchone()
                super_cup_total = old[0] + super_cup_value
                champion_league_total = old[1] + champion_league_value
                national_championship_total = old[2] + national_championship_value
                cup_total = old[3] + cup_value
                cursor.execute(
                    '''UPDATE clubs SET super_cup=%s, champion_league=%s, national_championship=%s, cup=%s WHERE club_name=%s;''',
                    (super_cup_total, champion_league_total, national_championship_total, cup_total, club_name))
            else:
                cursor.execute('''INSERT INTO clubs(super_cup, champion_league, national_championship, cup, victories, losses, draws, club_name) 
                              VALUES (%s, %s, %s, %s, 0, 0, 0, %s);''',
                               (super_cup_value, champion_league_value, national_championship_value, cup_value, club_name))
                club_id = cursor.lastrowid

            # Добавление трофеев
            trophy_map = {
                "super_cup": super_cup_value,
                "champion_league": champion_league_value,
                "national_championship": national_championship_value,
                "cup": cup_value
            }
            for trophy_type, count in trophy_map.items():
                for _ in range(count):
                    cursor.execute('INSERT INTO trophies(club_name, trophy_type) VALUES (%s, %s);',
                                   (club_name, trophy_type))

            connection.commit()
            write_log(
                f"Добавлен клуб: {club_name}, Суперкубки: {super_cup_value}, Лига Чемпионов: {champion_league_value}, Чемпионат: {national_championship_value}, Кубок: {cup_value}")
            flash('Клуб успешно добавлен', 'success')

        except Error as e:
            if connection:
                connection.rollback()
            flash(f'Ошибка при добавлении клуба: {str(e)}', 'error')
            print(f"Ошибка в vote_team: {e}")
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    return render_template('vote_team.html')

@app.route('/admin')
@login_required('admin')
def admin_panel():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Получаем статистику
        cursor.execute("SELECT COUNT(*) FROM users;")
        users_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM footballers;")
        players_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM clubs;")
        clubs_count = cursor.fetchone()[0]

        # Получаем последние логи (последние 5 записей)
        cursor.execute("SELECT text FROM logs ORDER BY id DESC LIMIT 5;")
        logs_data = cursor.fetchall()

        cursor.close()
        connection.close()

        # Парсим логи для отображения
        recent_logs = []
        for log in logs_data:
            if ': ' in log[0]:
                timestamp, message = log[0].split(': ', 1)
                recent_logs.append({'timestamp': timestamp, 'message': message})
            else:
                recent_logs.append({'timestamp': 'N/A', 'message': log[0]})

        return render_template('admin_panel.html',
                               users_count=users_count,
                               players_count=players_count,
                               clubs_count=clubs_count,
                               recent_logs=recent_logs)
    except Error as e:
        flash(f'Ошибка загрузки панели: {str(e)}', 'error')
        print(f"Ошибка в admin_panel: {e}")
        return redirect(url_for('index'))

@app.route('/admin/users')
@login_required('admin')
def admin_users():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id, login, role FROM users;")
        users = cursor.fetchall()
        cursor.close()
        connection.close()
        return render_template('admin_users.html', users=users)
    except Error as e:
        flash(f'Ошибка загрузки пользователей: {str(e)}', 'error')
        print(f"Ошибка в admin_users: {e}")
        return redirect(url_for('admin_panel'))

@app.route('/admin/add_user', methods=['POST'])
@login_required('admin')
def admin_add_user():
    login = request.form['login']
    password = request.form['password']
    role = request.form.get('role', 'user')

    if not login or not password:
        flash('Введите логин и пароль', 'error')
        return redirect(url_for('admin_users'))

    if len(password) < 4:
        flash('Пароль должен быть не менее 4 символов', 'error')
        return redirect(url_for('admin_users'))

    hashed = encrypt_password(password)
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO users(login, password_hash, role) VALUES (%s, %s, %s);", (login, hashed, role))
        connection.commit()
        flash('Пользователь успешно добавлен', 'success')
        write_log(f"Администратор добавил пользователя: {login}")
    except Error as e:
        if connection:
            connection.rollback()
        if "Duplicate entry" in str(e):
            flash('Такой логин уже существует', 'error')
        else:
            flash(f'Ошибка добавления пользователя: {str(e)}', 'error')
            print(f"Ошибка в admin_add_user: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return redirect(url_for('admin_users'))

@app.route('/admin/delete_user/<int:user_id>')
@login_required('admin')
def admin_delete_user(user_id):
    if user_id == session.get('user_id'):
        flash('Нельзя удалить самого себя', 'error')
        return redirect(url_for('admin_users'))

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s;", (user_id,))
        connection.commit()
        flash('Пользователь удален', 'success')
        write_log(f"Администратор удалил пользователя с ID: {user_id}")
    except Error as e:
        if connection:
            connection.rollback()
        flash(f'Ошибка удаления пользователя: {str(e)}', 'error')
        print(f"Ошибка в admin_delete_user: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return redirect(url_for('admin_users'))

@app.route('/admin/awards')
@login_required('admin')
def admin_awards():
    calculate_awards_and_winner()
    flash('Награды и победитель Золотого мяча обновлены', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/golden_ball')
@login_required('admin')
def admin_golden_ball():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT holder FROM golden_ball;")
        holders = cursor.fetchall()
        cursor.close()
        connection.close()
        return render_template('admin_golden_ball.html', holders=holders)
    except Error as e:
        flash(f'Ошибка загрузки Золотого мяча: {str(e)}', 'error')
        print(f"Ошибка в admin_golden_ball: {e}")
        return redirect(url_for('admin_panel'))

@app.route('/admin/query', methods=['GET', 'POST'])
@login_required('admin')
def admin_query():
    if request.method == 'POST':
        query = request.form['query']
        if not query:
            flash('Введите SQL-запрос', 'error')
            return render_template('admin_query.html')

        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute(query)
            if query.lower().strip().startswith('select'):
                rows = cursor.fetchall()
                headers = [description[0] for description in cursor.description] if cursor.description else []
                result = {
                    'headers': headers,
                    'rows': rows
                }
                write_log(f"Администратор выполнил запрос: {query}")
                return render_template('admin_query.html', result=result)
            else:
                connection.commit()
                flash('Запрос выполнен успешно', 'success')
                write_log(f"Администратор выполнил запрос: {query}")
        except Error as e:
            if connection:
                connection.rollback()
            flash(f'Ошибка выполнения запроса: {str(e)}', 'error')
            print(f"Ошибка в admin_query: {e}")
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    return render_template('admin_query.html')

@app.route('/admin/delete_record', methods=['POST'])
@login_required('admin')
def admin_delete_record():
    table = request.form['table']
    record_id = request.form['record_id']

    if not record_id.isdigit():
        flash('ID записи должен быть числом', 'error')
        return redirect(url_for('admin_panel'))

    record_id = int(record_id)
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE id = %s;", (record_id,))
        count = cursor.fetchone()[0]
        if count == 0:
            flash(f'Запись с id={record_id} не найдена в таблице {table}', 'error')
            return redirect(url_for('admin_panel'))

        if table == "footballers":
            cursor.execute("SELECT last_name, first_name, club FROM footballers WHERE id = %s;", (record_id,))
            player_data = cursor.fetchone()
            if player_data:
                last_name, first_name, club = player_data
                cursor.execute("DELETE FROM footballers WHERE id = %s;", (record_id,))
                cursor.execute("DELETE FROM personal_stats WHERE player_name = %s;", (last_name,))
                cursor.execute("DELETE FROM players WHERE player_name = %s;", (last_name,))
                full_name = f"{first_name} {last_name}"
                cursor.execute("DELETE FROM gentleman_coefficient WHERE footballer = %s;", (full_name,))
        elif table == "clubs":
            cursor.execute("SELECT club_name FROM clubs WHERE id = %s;", (record_id,))
            club_data = cursor.fetchone()
            if club_data:
                club_name = club_data[0]
                cursor.execute("DELETE FROM clubs WHERE id = %s;", (record_id,))
                cursor.execute("DELETE FROM trophies WHERE club_name = %s;", (club_name,))
                cursor.execute("UPDATE footballers SET club='' WHERE club = %s;", (club_name,))
        else:
            cursor.execute(f"DELETE FROM {table} WHERE id = %s;", (record_id,))

        connection.commit()
        flash(f'Запись с id={record_id} из таблицы {table} успешно удалена', 'success')
        write_log(f"Удалена запись id={record_id} из таблицы {table}")

    except Error as e:
        if connection:
            connection.rollback()
        flash(f'Не удалось удалить запись: {str(e)}', 'error')
        print(f"Ошибка в admin_delete_record: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return redirect(url_for('admin_panel'))

def calculate_awards_and_winner():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("DELETE FROM awards;")
        cursor.execute("DELETE FROM golden_ball;")

        # Найти лучшего бомбардира (игрок с максимальным goals)
        cursor.execute("SELECT player_name FROM personal_stats WHERE goals = (SELECT MAX(goals) FROM personal_stats) LIMIT 1;")
        top_scorer_data = cursor.fetchone()
        top_scorer = top_scorer_data[0] if top_scorer_data else None

        # Найти лучшего ассистента (игрок с максимальным assists)
        cursor.execute("SELECT player_name FROM personal_stats WHERE assists = (SELECT MAX(assists) FROM personal_stats) LIMIT 1;")
        top_assist_data = cursor.fetchone()
        top_assist = top_assist_data[0] if top_assist_data else None

        if top_scorer and top_assist:
            cursor.execute("INSERT INTO awards(top_scorer, top_assist) VALUES (%s, %s);", (top_scorer, top_assist))
            write_log(f"Обновлены награды: лучший бомбардир - {top_scorer}, лучший ассистент - {top_assist}")

        query = '''
            SELECT f.first_name, f.last_name, f.club,
                   ps.goals, ps.assists, ps.clean_sheets,
                   p.victories, p.draws, p.losses,
                   c.victories, c.draws, c.losses,
                   COALESCE(fc.coefficient, 1.0) as gentleman_coef
            FROM footballers f
            JOIN personal_stats ps ON ps.player_name = f.last_name
            JOIN players p ON p.player_name = f.last_name
            JOIN clubs c ON c.club_name = f.club
            LEFT JOIN gentleman_coefficient fc ON fc.footballer = CONCAT(f.first_name, ' ', f.last_name)
        '''
        cursor.execute(query)
        players = cursor.fetchall()

        best_score = None
        best_player = None
        for player in players:
            (first_name, last_name, club,
             goals, assists, clean_sheets,
             p_victories, p_draws, p_losses,
             c_victories, c_draws, c_losses,
             gentleman_coef_val) = player

            score = (goals + assists + clean_sheets +
                     c_victories + c_draws +
                     p_victories + p_draws -
                     c_losses - p_losses) * gentleman_coef_val

            if best_score is None or score > best_score:
                best_score = score
                best_player = f"{first_name} {last_name}"

        if best_player:
            cursor.execute("INSERT INTO golden_ball(holder) VALUES (%s);", (best_player,))
            write_log(f"Объявлен победитель Золотого мяча: {best_player} с очками {best_score}")
            write_log(f"Победителем Золотого мяча стал {best_player} с очками {best_score}.")

        connection.commit()

    except Error as e:
        if connection:
            connection.rollback()
        print(f"Ошибка в calculate_awards_and_winner: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

if __name__ == '__main__':
    success = initialize_database()
    if success:
        print("Flask приложение инициализировано и запущено.")
        app.run(host='0.0.0.0', port=5000, debug=True)  # Запуск на всех интерфейсах
    else:
        print("Инициализация БД failed. Приложение не запустится.")
        exit(1)