import os
import mysql.connector as mysql
from mysql.connector import Error
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import telebot
from datetime import datetime
import json
import logging
from dotenv import load_dotenv
import re
import random
import time
from random import choice

load_dotenv()

# Настройка логирования на русском
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

token = os.getenv('TELEGRAM_TOKEN')
if not token:
    logger.error("Токен Telegram не найден в переменных окружения")
    token = '8315061997:AAFEeHeoS16xB119HDNk5AMQwCKeZ64Y1ek'

bot = telebot.TeleBot(token)

# Конфигурация БД Gold_medal
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', 'Tochankau110574'),
    'database': os.getenv('MYSQL_DATABASE', 'Gold_medal')
}

# Расширенные списки случайных футболистов (50 игроков)
RANDOM_TASKS_PLAYERS = [
    {'first_name': 'Erling', 'last_name': 'Haaland', 'age': 23, 'club': 'Manchester City', 'goals': 36, 'assists': 8,
     'clean_sheets': 0, 'victories': 28, 'losses': 5, 'draws': 5, 'gentleman_coef': 4.2},
    {'first_name': 'Giovanni', 'last_name': 'Di Lorenzo', 'age': 30, 'club': 'Napoli', 'goals': 2, 'assists': 5,
     'clean_sheets': 12, 'victories': 24, 'losses': 6, 'draws': 8, 'gentleman_coef': 4.5},
    {'first_name': 'Kylian', 'last_name': 'Mbappé', 'age': 24, 'club': 'Paris Saint-Germain', 'goals': 44,
     'assists': 10, 'clean_sheets': 0, 'victories': 26, 'losses': 4, 'draws': 8, 'gentleman_coef': 3.8},
    {'first_name': 'Lionel', 'last_name': 'Messi', 'age': 36, 'club': 'Inter Miami', 'goals': 20, 'assists': 15,
     'clean_sheets': 0, 'victories': 22, 'losses': 8, 'draws': 8, 'gentleman_coef': 4.8},
    {'first_name': 'Cristiano', 'last_name': 'Ronaldo', 'age': 38, 'club': 'Al Nassr', 'goals': 35, 'assists': 3,
     'clean_sheets': 0, 'victories': 25, 'losses': 7, 'draws': 6, 'gentleman_coef': 4.0},
    {'first_name': 'Virgil', 'last_name': 'van Dijk', 'age': 32, 'club': 'Liverpool', 'goals': 1, 'assists': 2,
     'clean_sheets': 20, 'victories': 23, 'losses': 9, 'draws': 6, 'gentleman_coef': 4.3},
    {'first_name': 'Kevin', 'last_name': 'De Bruyne', 'age': 32, 'club': 'Manchester City', 'goals': 10, 'assists': 16,
     'clean_sheets': 0, 'victories': 28, 'losses': 5, 'draws': 5, 'gentleman_coef': 4.6},
    {'first_name': 'Robert', 'last_name': 'Lewandowski', 'age': 35, 'club': 'Barcelona', 'goals': 48, 'assists': 9,
     'clean_sheets': 0, 'victories': 24, 'losses': 6, 'draws': 8, 'gentleman_coef': 4.1},
    {'first_name': 'Harry', 'last_name': 'Kane', 'age': 30, 'club': 'Bayern Munich', 'goals': 32, 'assists': 8,
     'clean_sheets': 0, 'victories': 24, 'losses': 4, 'draws': 10, 'gentleman_coef': 4.4},
    {'first_name': 'Mohamed', 'last_name': 'Salah', 'age': 31, 'club': 'Liverpool', 'goals': 25, 'assists': 12,
     'clean_sheets': 0, 'victories': 23, 'losses': 9, 'draws': 6, 'gentleman_coef': 4.2},
    {'first_name': 'Karim', 'last_name': 'Benzema', 'age': 36, 'club': 'Al Ittihad', 'goals': 18, 'assists': 7,
     'clean_sheets': 0, 'victories': 20, 'losses': 10, 'draws': 8, 'gentleman_coef': 4.1},
    {'first_name': 'Neymar', 'last_name': 'Jr', 'age': 32, 'club': 'Al Hilal', 'goals': 15, 'assists': 14,
     'clean_sheets': 0, 'victories': 22, 'losses': 6, 'draws': 10, 'gentleman_coef': 3.9},
    {'first_name': 'Luka', 'last_name': 'Modric', 'age': 38, 'club': 'Real Madrid', 'goals': 3, 'assists': 9,
     'clean_sheets': 0, 'victories': 26, 'losses': 6, 'draws': 6, 'gentleman_coef': 4.7},
    {'first_name': 'Thibaut', 'last_name': 'Courtois', 'age': 31, 'club': 'Real Madrid', 'goals': 0, 'assists': 0,
     'clean_sheets': 18, 'victories': 26, 'losses': 6, 'draws': 6, 'gentleman_coef': 4.3},
    {'first_name': 'Manuel', 'last_name': 'Neuer', 'age': 37, 'club': 'Bayern Munich', 'goals': 0, 'assists': 0,
     'clean_sheets': 15, 'victories': 24, 'losses': 4, 'draws': 10, 'gentleman_coef': 4.5},
    {'first_name': 'Toni', 'last_name': 'Kroos', 'age': 34, 'club': 'Real Madrid', 'goals': 2, 'assists': 8,
     'clean_sheets': 0, 'victories': 26, 'losses': 6, 'draws': 6, 'gentleman_coef': 4.8},
    {'first_name': 'Joshua', 'last_name': 'Kimmich', 'age': 29, 'club': 'Bayern Munich', 'goals': 4, 'assists': 11,
     'clean_sheets': 0, 'victories': 24, 'losses': 4, 'draws': 10, 'gentleman_coef': 4.4},
    {'first_name': 'Bruno', 'last_name': 'Fernandes', 'age': 29, 'club': 'Manchester United', 'goals': 14,
     'assists': 15,
     'clean_sheets': 0, 'victories': 20, 'losses': 12, 'draws': 6, 'gentleman_coef': 4.1},
    {'first_name': 'Bernardo', 'last_name': 'Silva', 'age': 29, 'club': 'Manchester City', 'goals': 7, 'assists': 8,
     'clean_sheets': 0, 'victories': 28, 'losses': 5, 'draws': 5, 'gentleman_coef': 4.6},
    {'first_name': 'Ruben', 'last_name': 'Dias', 'age': 26, 'club': 'Manchester City', 'goals': 1, 'assists': 1,
     'clean_sheets': 16, 'victories': 28, 'losses': 5, 'draws': 5, 'gentleman_coef': 4.4},
    {'first_name': 'Marcus', 'last_name': 'Rashford', 'age': 26, 'club': 'Manchester United', 'goals': 17, 'assists': 5,
     'clean_sheets': 0, 'victories': 20, 'losses': 12, 'draws': 6, 'gentleman_coef': 3.9},
    {'first_name': 'Jude', 'last_name': 'Bellingham', 'age': 20, 'club': 'Real Madrid', 'goals': 19, 'assists': 6,
     'clean_sheets': 0, 'victories': 26, 'losses': 6, 'draws': 6, 'gentleman_coef': 4.3},
    {'first_name': 'Victor', 'last_name': 'Osimhen', 'age': 25, 'club': 'Napoli', 'goals': 26, 'assists': 4,
     'clean_sheets': 0, 'victories': 24, 'losses': 6, 'draws': 8, 'gentleman_coef': 4.2},
    {'first_name': 'Khvicha', 'last_name': 'Kvaratskhelia', 'age': 23, 'club': 'Napoli', 'goals': 12, 'assists': 13,
     'clean_sheets': 0, 'victories': 24, 'losses': 6, 'draws': 8, 'gentleman_coef': 4.0},
    {'first_name': 'Lautaro', 'last_name': 'Martinez', 'age': 26, 'club': 'Inter Milan', 'goals': 24, 'assists': 6,
     'clean_sheets': 0, 'victories': 23, 'losses': 7, 'draws': 8, 'gentleman_coef': 4.2},
    {'first_name': 'Son', 'last_name': 'Heung-min', 'age': 31, 'club': 'Tottenham', 'goals': 14, 'assists': 8,
     'clean_sheets': 0, 'victories': 18, 'losses': 11, 'draws': 9, 'gentleman_coef': 4.5},
    {'first_name': 'Bukayo', 'last_name': 'Saka', 'age': 22, 'club': 'Arsenal', 'goals': 15, 'assists': 11,
     'clean_sheets': 0, 'victories': 25, 'losses': 6, 'draws': 7, 'gentleman_coef': 4.3},
    {'first_name': 'Martin', 'last_name': 'Odegaard', 'age': 25, 'club': 'Arsenal', 'goals': 8, 'assists': 10,
     'clean_sheets': 0, 'victories': 25, 'losses': 6, 'draws': 7, 'gentleman_coef': 4.4},
    {'first_name': 'Phil', 'last_name': 'Foden', 'age': 23, 'club': 'Manchester City', 'goals': 11, 'assists': 7,
     'clean_sheets': 0, 'victories': 28, 'losses': 5, 'draws': 5, 'gentleman_coef': 4.2},
    {'first_name': 'Jack', 'last_name': 'Grealish', 'age': 28, 'club': 'Manchester City', 'goals': 5, 'assists': 11,
     'clean_sheets': 0, 'victories': 28, 'losses': 5, 'draws': 5, 'gentleman_coef': 4.1},
    {'first_name': 'Rodri', 'last_name': '', 'age': 27, 'club': 'Manchester City', 'goals': 4, 'assists': 7,
     'clean_sheets': 0, 'victories': 28, 'losses': 5, 'draws': 5, 'gentleman_coef': 4.6},
    {'first_name': 'Antonio', 'last_name': 'Rudiger', 'age': 30, 'club': 'Real Madrid', 'goals': 1, 'assists': 1,
     'clean_sheets': 14, 'victories': 26, 'losses': 6, 'draws': 6, 'gentleman_coef': 4.2},
    {'first_name': 'David', 'last_name': 'Alaba', 'age': 31, 'club': 'Real Madrid', 'goals': 2, 'assists': 3,
     'clean_sheets': 12, 'victories': 26, 'losses': 6, 'draws': 6, 'gentleman_coef': 4.4},
    {'first_name': 'Federico', 'last_name': 'Valverde', 'age': 25, 'club': 'Real Madrid', 'goals': 7, 'assists': 5,
     'clean_sheets': 0, 'victories': 26, 'losses': 6, 'draws': 6, 'gentleman_coef': 4.3},
    {'first_name': 'Vinicius', 'last_name': 'Junior', 'age': 23, 'club': 'Real Madrid', 'goals': 10, 'assists': 9,
     'clean_sheets': 0, 'victories': 26, 'losses': 6, 'draws': 6, 'gentleman_coef': 3.8},
    {'first_name': 'Rodrygo', 'last_name': '', 'age': 23, 'club': 'Real Madrid', 'goals': 9, 'assists': 8,
     'clean_sheets': 0, 'victories': 26, 'losses': 6, 'draws': 6, 'gentleman_coef': 4.0},
    {'first_name': 'Jamal', 'last_name': 'Musiala', 'age': 20, 'club': 'Bayern Munich', 'goals': 12, 'assists': 10,
     'clean_sheets': 0, 'victories': 24, 'losses': 4, 'draws': 10, 'gentleman_coef': 4.2},
    {'first_name': 'Leroy', 'last_name': 'Sane', 'age': 28, 'club': 'Bayern Munich', 'goals': 10, 'assists': 11,
     'clean_sheets': 0, 'victories': 24, 'losses': 4, 'draws': 10, 'gentleman_coef': 4.1},
    {'first_name': 'Kingsley', 'last_name': 'Coman', 'age': 27, 'club': 'Bayern Munich', 'goals': 8, 'assists': 7,
     'clean_sheets': 0, 'victories': 24, 'losses': 4, 'draws': 10, 'gentleman_coef': 4.0},
    {'first_name': 'Serge', 'last_name': 'Gnabry', 'age': 28, 'club': 'Bayern Munich', 'goals': 11, 'assists': 6,
     'clean_sheets': 0, 'victories': 24, 'losses': 4, 'draws': 10, 'gentleman_coef': 3.9},
    {'first_name': 'Achraf', 'last_name': 'Hakimi', 'age': 25, 'club': 'Paris Saint-Germain', 'goals': 4, 'assists': 6,
     'clean_sheets': 8, 'victories': 26, 'losses': 4, 'draws': 8, 'gentleman_coef': 4.1},
    {'first_name': 'Marquinhos', 'last_name': '', 'age': 29, 'club': 'Paris Saint-Germain', 'goals': 2, 'assists': 1,
     'clean_sheets': 10, 'victories': 26, 'losses': 4, 'draws': 8, 'gentleman_coef': 4.3},
    {'first_name': 'Marco', 'last_name': 'Verratti', 'age': 31, 'club': 'Al Arabi', 'goals': 1, 'assists': 8,
     'clean_sheets': 0, 'victories': 22, 'losses': 6, 'draws': 10, 'gentleman_coef': 4.4},
    {'first_name': 'Alexandre', 'last_name': 'Lacazette', 'age': 32, 'club': 'Lyon', 'goals': 27, 'assists': 5,
     'clean_sheets': 0, 'victories': 16, 'losses': 12, 'draws': 10, 'gentleman_coef': 4.2},
    {'first_name': 'Nicolo', 'last_name': 'Barella', 'age': 26, 'club': 'Inter Milan', 'goals': 6, 'assists': 9,
     'clean_sheets': 0, 'victories': 23, 'losses': 7, 'draws': 8, 'gentleman_coef': 4.5},
    {'first_name': 'Fikayo', 'last_name': 'Tomori', 'age': 25, 'club': 'AC Milan', 'goals': 1, 'assists': 1,
     'clean_sheets': 11, 'victories': 20, 'losses': 8, 'draws': 10, 'gentleman_coef': 4.3},
    {'first_name': 'Mike', 'last_name': 'Maignan', 'age': 28, 'club': 'AC Milan', 'goals': 0, 'assists': 0,
     'clean_sheets': 14, 'victories': 20, 'losses': 8, 'draws': 10, 'gentleman_coef': 4.4},
    {'first_name': 'Theo', 'last_name': 'Hernandez', 'age': 26, 'club': 'AC Milan', 'goals': 4, 'assists': 5,
     'clean_sheets': 8, 'victories': 20, 'losses': 8, 'draws': 10, 'gentleman_coef': 4.1}
]

# Расширенные списки случайных клубов (40 клубов)
RANDOM_TASKS_CLUBS = [
    {'name': 'Manchester City', 'super_cup': 1, 'champion_league': 1, 'national_championship': 2, 'cup': 2,
     'victories': 28, 'losses': 5, 'draws': 5},
    {'name': 'Real Madrid', 'super_cup': 1, 'champion_league': 1, 'national_championship': 1, 'cup': 2, 'victories': 26,
     'losses': 6, 'draws': 6},
    {'name': 'Bayern Munich', 'super_cup': 1, 'champion_league': 0, 'national_championship': 0, 'cup': 1,
     'victories': 24, 'losses': 4, 'draws': 10},
    {'name': 'Paris Saint-Germain', 'super_cup': 1, 'champion_league': 0, 'national_championship': 1, 'cup': 1,
     'victories': 26, 'losses': 4, 'draws': 8},
    {'name': 'Liverpool', 'super_cup': 0, 'champion_league': 0, 'national_championship': 0, 'cup': 0, 'victories': 23,
     'losses': 9, 'draws': 6},
    {'name': 'Juventus', 'super_cup': 2, 'champion_league': 1, 'national_championship': 2, 'cup': 1, 'victories': 22,
     'losses': 8, 'draws': 8},
    {'name': 'Chelsea', 'super_cup': 2, 'champion_league': 2, 'national_championship': 2, 'cup': 2, 'victories': 21,
     'losses': 10, 'draws': 7},
    {'name': 'Barcelona', 'super_cup': 1, 'champion_league': 0, 'national_championship': 1, 'cup': 0, 'victories': 24,
     'losses': 6, 'draws': 8},
    {'name': 'Manchester United', 'super_cup': 0, 'champion_league': 0, 'national_championship': 0, 'cup': 1,
     'victories': 20, 'losses': 12, 'draws': 6},
    {'name': 'Arsenal', 'super_cup': 0, 'champion_league': 0, 'national_championship': 0, 'cup': 0, 'victories': 25,
     'losses': 6, 'draws': 7},
    {'name': 'Tottenham', 'super_cup': 0, 'champion_league': 0, 'national_championship': 0, 'cup': 0, 'victories': 18,
     'losses': 11, 'draws': 9},
    {'name': 'AC Milan', 'super_cup': 0, 'champion_league': 0, 'national_championship': 0, 'cup': 0, 'victories': 20,
     'losses': 8, 'draws': 10},
    {'name': 'Inter Milan', 'super_cup': 1, 'champion_league': 0, 'national_championship': 0, 'cup': 1, 'victories': 23,
     'losses': 7, 'draws': 8},
    {'name': 'Napoli', 'super_cup': 0, 'champion_league': 0, 'national_championship': 1, 'cup': 0, 'victories': 24,
     'losses': 6, 'draws': 8},
    {'name': 'Atletico Madrid', 'super_cup': 0, 'champion_league': 0, 'national_championship': 0, 'cup': 1,
     'victories': 22, 'losses': 8, 'draws': 8},
    {'name': 'Borussia Dortmund', 'super_cup': 0, 'champion_league': 0, 'national_championship': 0, 'cup': 1,
     'victories': 21, 'losses': 6, 'draws': 11},
    {'name': 'RB Leipzig', 'super_cup': 0, 'champion_league': 0, 'national_championship': 0, 'cup': 1, 'victories': 19,
     'losses': 8, 'draws': 11},
    {'name': 'Newcastle United', 'super_cup': 0, 'champion_league': 0, 'national_championship': 0, 'cup': 0,
     'victories': 18, 'losses': 10, 'draws': 10},
    {'name': 'Aston Villa', 'super_cup': 0, 'champion_league': 0, 'national_championship': 0, 'cup': 0, 'victories': 17,
     'losses': 12, 'draws': 9},
    {'name': 'Brighton', 'super_cup': 0, 'champion_league': 0, 'national_championship': 0, 'cup': 0, 'victories': 16,
     'losses': 13, 'draws': 9},
    {'name': 'West Ham', 'super_cup': 0, 'champion_league': 0, 'national_championship': 0, 'cup': 1, 'victories': 15,
     'losses': 14, 'draws': 9},
    {'name': 'Sevilla', 'super_cup': 0, 'champion_league': 0, 'national_championship': 0, 'cup': 1, 'victories': 14,
     'losses': 15, 'draws': 9},
    {'name': 'Villarreal', 'super_cup': 0, 'champion_league': 0, 'national_championship': 0, 'cup': 0, 'victories': 16,
     'losses': 12, 'draws': 10},
    {'name': 'Real Sociedad', 'super_cup': 0, 'champion_league': 0, 'national_championship': 0, 'cup': 0,
     'victories': 18, 'losses': 10, 'draws': 10},
    {'name': 'Benfica', 'super_cup': 0, 'champion_league': 0, 'national_championship': 1, 'cup': 1, 'victories': 25,
     'losses': 3, 'draws': 10},
    {'name': 'Porto', 'super_cup': 0, 'champion_league': 0, 'national_championship': 0, 'cup': 1, 'victories': 24,
     'losses': 4, 'draws': 10},
    {'name': 'Sporting Lisbon', 'super_cup': 0, 'champion_league': 0, 'national_championship': 0, 'cup': 0,
     'victories': 23, 'losses': 5, 'draws': 10},
    {'name': 'Ajax', 'super_cup': 0, 'champion_league': 0, 'national_championship': 1, 'cup': 1, 'victories': 22,
     'losses': 6, 'draws': 10},
    {'name': 'PSV Eindhoven', 'super_cup': 0, 'champion_league': 0, 'national_championship': 0, 'cup': 0,
     'victories': 21, 'losses': 7, 'draws': 10},
    {'name': 'Feyenoord', 'super_cup': 0, 'champion_league': 0, 'national_championship': 1, 'cup': 0, 'victories': 20,
     'losses': 8, 'draws': 10},
    {'name': 'Celtic', 'super_cup': 0, 'champion_league': 0, 'national_championship': 1, 'cup': 1, 'victories': 26,
     'losses': 2, 'draws': 10},
    {'name': 'Rangers', 'super_cup': 0, 'champion_league': 0, 'national_championship': 0, 'cup': 0, 'victories': 24,
     'losses': 4, 'draws': 10},
    {'name': 'Galatasaray', 'super_cup': 0, 'champion_league': 0, 'national_championship': 1, 'cup': 1, 'victories': 23,
     'losses': 5, 'draws': 10},
    {'name': 'Fenerbahce', 'super_cup': 0, 'champion_league': 0, 'national_championship': 0, 'cup': 0, 'victories': 22,
     'losses': 6, 'draws': 10},
    {'name': 'Besiktas', 'super_cup': 0, 'champion_league': 0, 'national_championship': 0, 'cup': 0, 'victories': 20,
     'losses': 8, 'draws': 10},
    {'name': 'Shakhtar Donetsk', 'super_cup': 0, 'champion_league': 0, 'national_championship': 1, 'cup': 1,
     'victories': 19, 'losses': 9, 'draws': 10},
    {'name': 'Dinamo Zagreb', 'super_cup': 0, 'champion_league': 0, 'national_championship': 1, 'cup': 0,
     'victories': 21, 'losses': 7, 'draws': 10},
    {'name': 'Red Bull Salzburg', 'super_cup': 0, 'champion_league': 0, 'national_championship': 1, 'cup': 1,
     'victories': 22, 'losses': 6, 'draws': 10},
    {'name': 'Bayer Leverkusen', 'super_cup': 0, 'champion_league': 0, 'national_championship': 0, 'cup': 0,
     'victories': 20, 'losses': 8, 'draws': 10},
    {'name': 'Wolfsburg', 'super_cup': 0, 'champion_league': 0, 'national_championship': 0, 'cup': 0, 'victories': 18,
     'losses': 10, 'draws': 10}
]

# Ссылки на приложение
GUI_APP_PATHS = [
    'http://192.168.1.105:5000',
    'http://127.0.0.1:5000'
]


def get_db_connection():
    """Получение подключения к БД с повторными попытками"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            connection = mysql.connect(**DB_CONFIG)
            if connection.is_connected():
                logger.info(f"Успешное подключение к БД Gold_medal (попытка {attempt + 1})")
                return connection
        except Error as e:
            logger.error(f"Попытка {attempt + 1} подключения к БД не удалась: {e}")
            if attempt == max_retries - 1:
                raise e
            time.sleep(2)
    return None


def check_database_connection():
    """Проверка подключения к БД и существования таблиц"""
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                # Проверяем существование основных таблиц
                tables = ['bot_users', 'bot_logs', 'footballers', 'clubs']
                for table in tables:
                    cursor.execute(f"SHOW TABLES LIKE '{table}'")
                    if not cursor.fetchone():
                        logger.warning(f"Таблица {table} не существует")
        logger.info("Проверка БД завершена успешно")
        return True
    except Error as e:
        logger.error(f"Ошибка проверки БД: {e}")
        return False


def register_bot_user(user_id, username, first_name, last_name):
    """Регистрация пользователя бота в БД"""
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO bot_users (telegram_id, username, first_name, last_name) 
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                    username = COALESCE(VALUES(username), username),
                    first_name = COALESCE(VALUES(first_name), first_name),
                    last_name = COALESCE(VALUES(last_name), last_name)""",
                    (user_id, username, first_name, last_name)
                )
                connection.commit()
                logger.info(f"Зарегистрирован/обновлен пользователь бота: {user_id}")
    except Error as e:
        logger.error(f"Ошибка регистрации пользователя бота: {e}")


def log_bot_action(user_id, action, details=""):
    """Логирование действий пользователя бота на русском"""
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO bot_logs (telegram_id, action, details) VALUES (%s, %s, %s)",
                    (user_id, action, details)
                )
                connection.commit()
    except Error as e:
        logger.error(f"Ошибка записи лога бота: {e}")


def save_bot_session(user_id, session_data):
    """Сохранение сессии пользователя"""
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                # Проверяем существование пользователя
                cursor.execute("SELECT 1 FROM bot_users WHERE telegram_id = %s", (user_id,))
                user_exists = cursor.fetchone()

                if not user_exists:
                    register_bot_user(user_id, None, None, None)

                cursor.execute(
                    """INSERT INTO bot_sessions (telegram_id, session_data) 
                    VALUES (%s, %s) 
                    ON DUPLICATE KEY UPDATE session_data = VALUES(session_data), last_activity = NOW()""",
                    (user_id, json.dumps(session_data))
                )
                connection.commit()
    except Error as e:
        logger.error(f"Ошибка сохранения сессии: {e}")


def get_bot_session(user_id):
    """Загрузка сессии пользователя"""
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT session_data FROM bot_sessions WHERE telegram_id = %s",
                    (user_id,)
                )
                result = cursor.fetchone()
                return json.loads(result[0]) if result else {}
    except Error as e:
        logger.error(f"Ошибка загрузки сессии: {e}")
        return {}


def clear_bot_session(user_id):
    """Очистка сессии пользователя"""
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM bot_sessions WHERE telegram_id = %s",
                    (user_id,)
                )
                connection.commit()
    except Error as e:
        logger.error(f"Ошибка очистки сессии: {e}")


# Клавиатуры с эмодзи
def get_main_menu():
    menu = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    menu.add(
        KeyboardButton('🎲 Случайный футболист'),
        KeyboardButton('🎯 Случайный клуб'),
        KeyboardButton('📊 Моя статистика'),
        KeyboardButton('👑 Топ игроки'),
        KeyboardButton('🌐 Открыть приложение'),
        KeyboardButton('ℹ️ Помощь')
    )
    return menu


WELCOME_TEXT = """
⚽ Добро пожаловать в Футбольный бот! 🎉

Этот бот предназначен для голосования в номинации "Золотой мяч".
Он нужен для отслеживания и управления статистикой футболистов и клубов.

Основные возможности:
• 🎲 Получить случайного футболиста
• 🎯 Получить случайный клуб  
• 💾 Сохранять данные в базу
• 📊 Просматривать свою статистику
• 👑 Смотреть топ игроков

Выберите действие из меню ниже 👇
"""

HELP_TEXT = """
🆘 Справка по боту

Случайный футболист:
• Нажмите "🎲 Случайный футболиста"
• Бот выберет случайного игрока из базы
• Игрок автоматически добавится в базу

Случайный клуб:
• Нажмите "🎯 Случайный клуб"  
• Бот выберет случайный клуб из базы
• Клуб автоматически добавится в базу

Функционал:
• Все данные сохраняются в базу
• Просмотр вашей статистики
• Топ игроков по голам и ассистам
• Логирование всех действий

Используйте кнопки меню для навигации!
"""


@bot.message_handler(commands=['start', 'help'])
def start_help_command(message):
    user = message.from_user
    register_bot_user(user.id, user.username, user.first_name, user.last_name)
    log_bot_action(user.id, "Запуск бота")

    if message.text == '/start':
        bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=get_main_menu())
    else:
        bot.send_message(message.chat.id, HELP_TEXT, reply_markup=get_main_menu())


@bot.message_handler(func=lambda message: message.text == '🎲 Случайный футболист')
def get_random_player(message):
    user_id = message.from_user.id

    # Выбираем случайного игрока
    selected_player = random.choice(RANDOM_TASKS_PLAYERS)

    try:
        # Показываем полную информацию
        player_info = f"""
📋 СЛУЧАЙНЫЙ ФУТБОЛИСТ:

👤 Имя: {selected_player['first_name']} {selected_player['last_name']}
🎂 Возраст: {selected_player['age']}
🏢 Клуб: {selected_player['club']}
⚽ Голы: {selected_player['goals']}
🎯 Ассисты: {selected_player['assists']}
🧤 Сухие матчи: {selected_player['clean_sheets']}
✅ Победы: {selected_player['victories']}
❌ Поражения: {selected_player['losses']}
🤝 Ничьи: {selected_player['draws']}
🎩 Коэффициент: {selected_player['gentleman_coef']}
        """

        bot.send_message(message.chat.id, player_info)

        # Сохраняем в базу
        save_player_to_db(user_id, selected_player)

        confirmation = f"""
✅ ФУТБОЛИСТ УСПЕШНО СОХРАНЕН В БАЗУ ДАННЫХ!

💾 Данные футболиста {selected_player['first_name']} {selected_player['last_name']} 
были успешно добавлены в базу данных Gold_medal.
        """

        bot.send_message(message.chat.id, confirmation, reply_markup=get_main_menu())
        log_bot_action(user_id, "Случайный футболист добавлен",
                       f"{selected_player['first_name']} {selected_player['last_name']}")

    except Error as e:
        logger.error(f"Ошибка добавления футболиста: {e}")
        bot.send_message(message.chat.id,
                         "❌ Ошибка при добавлении футболиста.",
                         reply_markup=get_main_menu())


@bot.message_handler(func=lambda message: message.text == '🎯 Случайный клуб')
def get_random_club(message):
    user_id = message.from_user.id

    # Выбираем случайный клуб
    selected_club = random.choice(RANDOM_TASKS_CLUBS)

    try:
        # Показываем полную информацию
        club_info = f"""
🏢 СЛУЧАЙНЫЙ КЛУБ:

🏷️ Название: {selected_club['name']}
🏆 Суперкубки: {selected_club['super_cup']}
⭐ Лиги чемпионов: {selected_club['champion_league']}
🥇 Чемпионаты: {selected_club['national_championship']}
🏅 Кубки: {selected_club['cup']}
✅ Победы: {selected_club['victories']}
❌ Поражения: {selected_club['losses']}
🤝 Ничьи: {selected_club['draws']}
        """

        bot.send_message(message.chat.id, club_info)

        # Сохраняем в базу
        save_club_to_db(user_id, selected_club)

        confirmation = f"""
✅ КЛУБ УСПЕШНО СОХРАНЕН В БАЗУ ДАННЫХ!

💾 Данные клуба {selected_club['name']} 
были успешно добавлены в базу данных Gold_medal.
        """

        bot.send_message(message.chat.id, confirmation, reply_markup=get_main_menu())
        log_bot_action(user_id, "Случайный клуб добавлен", selected_club['name'])

    except Error as e:
        logger.error(f"Ошибка добавления клуба: {e}")
        bot.send_message(message.chat.id,
                         "❌ Ошибка при добавлении клуба.",
                         reply_markup=get_main_menu())


def save_player_to_db(user_id, player_data):
    """Сохранение футболиста в базу данных Gold_medal"""
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                # Вставляем футболиста
                cursor.execute(
                    """INSERT INTO footballers(first_name, last_name, age, club, image_path) 
                    VALUES (%s, %s, %s, %s, NULL)""",
                    (player_data['first_name'], player_data['last_name'], player_data['age'], player_data['club'])
                )

                # Вставляем статистику
                cursor.execute(
                    "INSERT INTO personal_stats(player_name, goals, assists, clean_sheets) VALUES (%s, %s, %s, %s)",
                    (player_data['last_name'], player_data.get('goals', 0), player_data.get('assists', 0),
                     player_data.get('clean_sheets', 0))
                )

                # Вставляем результаты матчей
                cursor.execute(
                    "INSERT INTO players(player_name, victories, losses, draws) VALUES (%s, %s, %s, %s)",
                    (player_data['last_name'], player_data.get('victories', 0), player_data.get('losses', 0),
                     player_data.get('draws', 0))
                )

                # Вставляем коэффициент джентльмена
                cursor.execute(
                    "INSERT INTO gentleman_coefficient(coefficient, footballer) VALUES (%s, %s)",
                    (player_data.get('gentleman_coef', 1.0), f"{player_data['first_name']} {player_data['last_name']}")
                )

                connection.commit()
                logger.info(f"Футболист {player_data['first_name']} {player_data['last_name']} сохранен в БД")
                log_bot_action(user_id, "Сохранение футболиста в БД",
                               f"{player_data['first_name']} {player_data['last_name']}")
    except Error as e:
        logger.error(f"Ошибка сохранения футболиста в БД: {e}")
        log_bot_action(user_id, "Ошибка сохранения футболиста", str(e))
        raise e


def save_club_to_db(user_id, club_data):
    """Сохранение клуба в базу данных Gold_medal"""
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id FROM clubs WHERE club_name = %s", (club_data['name'],))
                club_exists = cursor.fetchone()

                if club_exists:
                    club_id = club_exists[0]
                    cursor.execute(
                        """UPDATE clubs SET 
                        super_cup = %s, 
                        champion_league = %s,
                        national_championship = %s, 
                        cup = %s,
                        victories = %s,
                        losses = %s,
                        draws = %s
                        WHERE id = %s""",
                        (club_data.get('super_cup', 0), club_data.get('champion_league', 0),
                         club_data.get('national_championship', 0), club_data.get('cup', 0),
                         club_data.get('victories', 0), club_data.get('losses', 0),
                         club_data.get('draws', 0), club_id)
                    )
                else:
                    cursor.execute(
                        """INSERT INTO clubs(super_cup, champion_league, national_championship, cup,
                        victories, losses, draws, club_name, image_path)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NULL)""",
                        (club_data.get('super_cup', 0), club_data.get('champion_league', 0),
                         club_data.get('national_championship', 0), club_data.get('cup', 0),
                         club_data.get('victories', 0), club_data.get('losses', 0),
                         club_data.get('draws', 0), club_data['name'])
                    )
                    club_id = cursor.lastrowid

                connection.commit()
                logger.info(f"Клуб {club_data['name']} сохранен в БД")
                log_bot_action(user_id, "Сохранение клуба в БД", club_data['name'])
    except Error as e:
        logger.error(f"Ошибка сохранения клуба в БД: {e}")
        log_bot_action(user_id, "Ошибка сохранения клуба", str(e))
        raise e


@bot.message_handler(func=lambda message: message.text == '👑 Топ игроки')
def show_top_players(message):
    user_id = message.from_user.id
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                # Проверяем существование таблицы golden_ball и получаем текущего победителя
                cursor.execute("SHOW TABLES LIKE 'golden_ball'")
                golden_ball_table_exists = cursor.fetchone()

                current_golden_ball_winner = None
                if golden_ball_table_exists:
                    cursor.execute("""
                        SELECT holder, created_at 
                        FROM golden_ball 
                        ORDER BY created_at DESC 
                        LIMIT 1
                    """)
                    current_golden_ball_winner = cursor.fetchone()

                # Лучший бомбардир
                cursor.execute("""
                    SELECT f.first_name, f.last_name, f.club, ps.goals, ps.assists, ps.clean_sheets
                    FROM footballers f
                    JOIN personal_stats ps ON f.last_name = ps.player_name
                    WHERE ps.goals > 0
                    ORDER BY ps.goals DESC, ps.assists DESC
                    LIMIT 3
                """)
                top_scorers = cursor.fetchall()

                # Лучший ассистент
                cursor.execute("""
                    SELECT f.first_name, f.last_name, f.club, ps.assists, ps.goals, ps.clean_sheets
                    FROM footballers f
                    JOIN personal_stats ps ON f.last_name = ps.player_name
                    WHERE ps.assists > 0
                    ORDER BY ps.assists DESC, ps.goals DESC
                    LIMIT 3
                """)
                top_assistants = cursor.fetchall()

                # Лучший по чистым матчам (вратари/защитники)
                cursor.execute("""
                    SELECT f.first_name, f.last_name, f.club, ps.clean_sheets, ps.goals, ps.assists
                    FROM footballers f
                    JOIN personal_stats ps ON f.last_name = ps.player_name
                    WHERE ps.clean_sheets > 0
                    ORDER BY ps.clean_sheets DESC, ps.goals DESC
                    LIMIT 3
                """)
                top_clean_sheets = cursor.fetchall()

                # Кандидаты на Золотой мяч (по комбинированной статистике)
                cursor.execute("""
                    SELECT f.first_name, f.last_name, f.club, 
                           (COALESCE(ps.goals, 0) * 2 + COALESCE(ps.assists, 0) * 1.5 + 
                            COALESCE(ps.clean_sheets, 0) * 1.2 + COALESCE(gc.coefficient, 1)) as score,
                           COALESCE(ps.goals, 0) as goals, 
                           COALESCE(ps.assists, 0) as assists, 
                           COALESCE(ps.clean_sheets, 0) as clean_sheets, 
                           COALESCE(gc.coefficient, 1) as coef
                    FROM footballers f
                    LEFT JOIN personal_stats ps ON f.last_name = ps.player_name
                    LEFT JOIN gentleman_coefficient gc ON f.first_name = SUBSTRING_INDEX(gc.footballer, ' ', 1) 
                                                  AND f.last_name = SUBSTRING_INDEX(gc.footballer, ' ', -1)
                    WHERE ps.goals > 0 OR ps.assists > 0 OR ps.clean_sheets > 0
                    ORDER BY score DESC
                    LIMIT 5
                """)
                golden_ball_candidates = cursor.fetchall()

                # Топ по коэффициенту джентльмена
                cursor.execute("""
                    SELECT f.first_name, f.last_name, f.club, gc.coefficient
                    FROM footballers f
                    JOIN gentleman_coefficient gc ON f.first_name = SUBSTRING_INDEX(gc.footballer, ' ', 1) 
                                              AND f.last_name = SUBSTRING_INDEX(gc.footballer, ' ', -1)
                    WHERE gc.coefficient > 0
                    ORDER BY gc.coefficient DESC
                    LIMIT 3
                """)
                top_gentlemen = cursor.fetchall()

                # История победителей Золотого мяча (если таблица существует)
                golden_ball_history = []
                if golden_ball_table_exists:
                    cursor.execute("""
                        SELECT holder, created_at 
                        FROM golden_ball 
                        ORDER BY created_at DESC 
                        LIMIT 5
                    """)
                    golden_ball_history = cursor.fetchall()

                # Подсчет общего количества игроков
                cursor.execute("SELECT COUNT(*) FROM footballers")
                total_players = cursor.fetchone()[0]

        response = "🏆 ТОП ИГРОКИ СЕЗОНА 🏆\n\n"

        # Текущий обладатель Золотого мяча (из таблицы golden_ball)
        if current_golden_ball_winner:
            holder, created_at = current_golden_ball_winner
            # Форматируем дату для лучшего отображения
            created_date = created_at.strftime("%d.%m.%Y") if created_at else "Неизвестно"
            response += "🏅 ТЕКУЩИЙ ОБЛАДАТЕЛЬ ЗОЛОТОГО МЯЧА:\n"
            response += f"👤 {holder}\n"
            response += f"📅 Получен: {created_date}\n\n"
        else:
            response += "🏅 Обладатель Золотого мяча: определяется по итогам сезона\n\n"

        # Кандидаты на Золотой мяч в текущем сезоне
        if golden_ball_candidates:
            response += "🔥 КАНДИДАТЫ НА ЗОЛОТОЙ МЯЧ В ТЕКУЩЕМ СЕЗОНЕ:\n"
            for i, (first_name, last_name, club, score, goals, assists, clean_sheets, coef) in enumerate(
                    golden_ball_candidates[:3]):
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
                response += f"{medal} {first_name} {last_name} - {club}\n"
                response += f"   ⭐ Рейтинг: {score:.1f} | ⚽ {goals} | 🎯 {assists} | 🧤 {clean_sheets} | 🎩 {coef:.1f}\n"

            # Показать остальных кандидатов (4-5 места)
            if len(golden_ball_candidates) > 3:
                response += "\n📊 Также в топе:\n"
                for i in range(3, min(5, len(golden_ball_candidates))):
                    first_name, last_name, club, score, goals, assists, clean_sheets, coef = golden_ball_candidates[i]
                    response += f"#{i + 1} {first_name} {last_name} - {club} ({score:.1f})\n"
            response += "\n"
        else:
            response += "🔥 Кандидаты на Золотой мяч: статистика отсутствует\n\n"

        # Топ бомбардиры
        if top_scorers:
            response += "⚽ ТОП БОМБАРДИРЫ:\n"
            for i, (first_name, last_name, club, goals, assists, clean_sheets) in enumerate(top_scorers[:3]):
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
                response += f"{medal} {first_name} {last_name} - {club}\n"
                response += f"   ⚽ Голы: {goals} | 🎯 Ассисты: {assists} | 🧤 Чистые: {clean_sheets}\n"
            response += "\n"
        else:
            response += "⚽ Топ бомбардиры: статистика отсутствует\n\n"

        # Топ ассистенты
        if top_assistants:
            response += "🎯 ТОП АССИСТЕНТЫ:\n"
            for i, (first_name, last_name, club, assists, goals, clean_sheets) in enumerate(top_assistants[:3]):
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
                response += f"{medal} {first_name} {last_name} - {club}\n"
                response += f"   🎯 Ассисты: {assists} | ⚽ Голы: {goals} | 🧤 Чистые: {clean_sheets}\n"
            response += "\n"
        else:
            response += "🎯 Топ ассистенты: статистика отсутствует\n\n"

        # Топ по чистым матчам
        if top_clean_sheets:
            response += "🧤 ТОП ПО ЧИСТЫМ МАТЧАМ:\n"
            for i, (first_name, last_name, club, clean_sheets, goals, assists) in enumerate(top_clean_sheets[:3]):
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
                response += f"{medal} {first_name} {last_name} - {club}\n"
                response += f"   🧤 Чистые матчи: {clean_sheets} | ⚽ Голы: {goals} | 🎯 Ассисты: {assists}\n"
            response += "\n"
        else:
            response += "🧤 Топ по чистым матчам: статистика отсутствует\n\n"

        # Топ джентльмены
        if top_gentlemen:
            response += "🎩 ТОП ДЖЕНТЛЬМЕНЫ:\n"
            for i, (first_name, last_name, club, coefficient) in enumerate(top_gentlemen[:3]):
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
                response += f"{medal} {first_name} {last_name} - {club}\n"
                response += f"   🎩 Коэффициент: {coefficient:.1f}\n"
            response += "\n"
        else:
            response += "🎩 Топ джентльмены: статистика отсутствует\n\n"

        # История Золотого мяча
        if golden_ball_history:
            response += "📜 ИСТОРИЯ ЗОЛОТОГО МЯЧА (последние награждения):\n"
            for holder, created_at in golden_ball_history:
                created_date = created_at.strftime("%d.%m.%Y") if created_at else "Неизвестно"
                response += f"🏆 {created_date}: {holder}\n"
            response += "\n"

        # Информация об обновлении
        response += f"🔄 Рейтинги обновляются автоматически"
        response += f"\n📊 Всего игроков в базе: {total_players}"

        if current_golden_ball_winner:
            response += f"\n⭐ Текущий победитель: {current_golden_ball_winner[0]}"

        # Проверяем длину сообщения (ограничение Telegram ~4096 символов)
        if len(response) > 4000:
            response = response[:3990] + "\n\n... (сообщение сокращено)"

        bot.send_message(message.chat.id, response, reply_markup=get_main_menu())
        log_bot_action(user_id, "Просмотр топа игроков")

    except Error as e:
        logger.error(f"Ошибка получения топ игроков: {e}")
        bot.send_message(message.chat.id,
                         "❌ Ошибка при получении данных о топ игроках.",
                         reply_markup=get_main_menu())

@bot.message_handler(func=lambda message: message.text == '📊 Моя статистика')
def show_user_stats(message):
    user_id = message.from_user.id

    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT action, COUNT(*) FROM bot_logs WHERE telegram_id = %s GROUP BY action",
                    (user_id,)
                )
                actions = cursor.fetchall() or []

                cursor.execute(
                    "SELECT action, details, created_at FROM bot_logs WHERE telegram_id = %s ORDER BY created_at DESC LIMIT 5",
                    (user_id,)
                )
                recent_actions = cursor.fetchall() or []

                cursor.execute(
                    "SELECT COUNT(*) FROM bot_logs WHERE telegram_id = %s AND action IN ('Сохранение футболиста в БД', 'Сохранение клуба в БД', 'Случайный футболист добавлен', 'Случайный клуб добавлен')",
                    (user_id,)
                )
                added_records_result = cursor.fetchone()
                added_records = added_records_result[0] if added_records_result else 0

        stats_text = "📊 Ваша статистика:\n\n"

        if actions:
            stats_text += "📈 Количество действий:\n"
            for action, count in actions:
                stats_text += f"• {action}: {count}\n"
        else:
            stats_text += "📭 У вас пока нет действий.\n"

        stats_text += f"\n💾 Всего добавлено записей: {added_records}\n"

        if recent_actions:
            stats_text += "\n🕒 Последние действия:\n"
            for action, details, created_at in recent_actions:
                time_str = created_at.strftime('%d.%m %H:%M') if created_at else 'N/A'
                details_text = f": {details}" if details else ""
                stats_text += f"• {action}{details_text} ({time_str})\n"

        bot.send_message(message.chat.id, stats_text)
        log_bot_action(user_id, "Просмотр статистики")

    except Error as e:
        logger.error(f"Ошибка получения статистики: {e}")
        bot.send_message(message.chat.id,
                         "❌ Ошибка при получении статистики.",
                         reply_markup=get_main_menu())


@bot.message_handler(func=lambda message: message.text == '🌐 Открыть приложение')
def show_app_link(message):
    user_id = message.from_user.id

    app_links = "🌐 Веб-приложение доступно по ссылкам:\n\n"
    for i, link in enumerate(GUI_APP_PATHS, 1):
        app_links += f"{i}. {link}\n"

    app_links += "\nТам вы найдете расширенный функционал и статистику!"

    bot.send_message(message.chat.id, app_links, reply_markup=get_main_menu())
    log_bot_action(user_id, "Просмотр ссылок на приложение")


@bot.message_handler(func=lambda message: message.text == 'ℹ️ Помощь')
def show_help(message):
    bot.send_message(message.chat.id, HELP_TEXT, reply_markup=get_main_menu())
    log_bot_action(message.from_user.id, "Просмотр справки")


@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id

    try:
        user = message.from_user
        register_bot_user(user.id, user.username, user.first_name, user.last_name)

        bot.send_message(message.chat.id,
                         "Используйте кнопки меню для навигации.",
                         reply_markup=get_main_menu())

    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {e}")
        bot.send_message(message.chat.id,
                         "Произошла ошибка. Попробуйте еще раз.",
                         reply_markup=get_main_menu())


def start_bot():
    """Запуск бота"""
    try:
        logger.info("Запуск Telegram бота...")
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")


if __name__ == '__main__':
    logger.info("Запуск проверки подключения к БД Gold_medal...")
    if check_database_connection():
        logger.info("Подключение к БД Gold_medal успешно. Запуск бота...")
        start_bot()
    else:
        logger.error("Не удалось подключиться к БД Gold_medal. Запуск бота отменен.")
        time.sleep(5)