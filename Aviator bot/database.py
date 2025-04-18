import psycopg2
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    """Устанавливает соединение с базой данных и проверяет/создает таблицу users."""
    try:
        logger.info("Connecting to DB")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        logger.info("DB connected")
        # Проверяем и создаем таблицу users
        if ensure_users_table(conn):
            logger.info("Table 'users' is ready")
        else:
            logger.error("Failed to ensure 'users' table")
            conn.close()
            return None
        return conn
    except Exception as e:
        logger.error(f"DB connection error: {e}")
        return None

def ensure_users_table(conn):
    """Проверяет наличие таблицы users и создает её, если она отсутствует."""
    try:
        with conn.cursor() as cur:
            # Проверяем, существует ли таблица
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                )
            """)
            table_exists = cur.fetchone()[0]
            logger.info(f"Table 'users' exists: {table_exists}")

            if not table_exists:
                logger.info("Creating table 'users'")
                cur.execute("""
                    CREATE TABLE users (
                        telegram_id BIGINT PRIMARY KEY,
                        username VARCHAR(255),
                        phone VARCHAR(50),
                        country VARCHAR(100)
                    )
                """)
                conn.commit()
                logger.info("Table 'users' created successfully")
            return True
    except Exception as e:
        logger.error(f"Error ensuring 'users' table: {e}")
        return False

def save_user(telegram_id, username, phone, country):
    """Сохраняет пользователя в базу данных."""
    logger.info(f"Saving user_id={telegram_id}")
    conn = get_db_connection()
    if not conn:
        logger.error(f"No DB for user_id={telegram_id}")
        return False
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (telegram_id, username, phone, country) VALUES (%s, %s, %s, %s) ON CONFLICT (telegram_id) DO NOTHING",
                (telegram_id, username, phone, country)
            )
            conn.commit()
            logger.info(f"User {telegram_id} saved")
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"Save error for user_id={telegram_id}: {e}")
        return False
    finally:
        conn.close()

def get_user(telegram_id):
    """Получает данные пользователя по telegram_id."""
    logger.info(f"Fetching user_id={telegram_id}")
    conn = get_db_connection()
    if not conn:
        logger.error(f"No DB for user_id={telegram_id}")
        return None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT telegram_id, username, phone, country FROM users WHERE telegram_id = %s", (telegram_id,))
            user = cur.fetchone()
            logger.info(f"User {telegram_id}: {user}")
            return user
    except Exception as e:
        logger.error(f"Fetch error for user_id={telegram_id}: {e}")
        return None
    finally:
        conn.close()

def check_user_registration(telegram_id):
    """Проверяет, зарегистрирован ли пользователь."""
    logger.info(f"Checking user_id={telegram_id}")
    conn = get_db_connection()
    if not conn:
        logger.error(f"No DB for user_id={telegram_id}")
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE telegram_id = %s", (telegram_id,))
            exists = cur.fetchone() is not None
            logger.info(f"Registration for user_id={telegram_id}: {exists}")
            return exists
    except Exception as e:
        logger.error(f"Check error for user_id={telegram_id}: {e}")
        return False
    finally:
        conn.close()

def get_all_users():
    """Получает список всех пользователей."""
    logger.info("Fetching all users")
    conn = get_db_connection()
    if not conn:
        logger.error("No DB connection")
        return []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT telegram_id, username, phone, country FROM users")
            users = cur.fetchall()
            logger.info(f"Found {len(users)} users")
            return users
    except Exception as e:
        logger.error(f"Users fetch error: {e}")
        return []
    finally:
        conn.close()

def get_all_countries():
    """Получает список уникальных стран из базы данных."""
    logger.info("Fetching all countries")
    conn = get_db_connection()
    if not conn:
        logger.error("No DB connection")
        return []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT country FROM users WHERE country IS NOT NULL AND country != 'Unknown'")
            countries = [row[0] for row in cur.fetchall()]
            logger.info(f"Found {len(countries)} countries: {countries}")
            return countries
    except Exception as e:
        logger.error(f"Countries fetch error: {e}")
        return []
    finally:
        conn.close()

def get_users_by_country(country):
    """Получает список telegram_id пользователей для указанной страны."""
    logger.info(f"Fetching users for country={country}")
    conn = get_db_connection()
    if not conn:
        logger.error("No DB connection")
        return []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT telegram_id FROM users WHERE country = %s", (country,))
            user_ids = [row[0] for row in cur.fetchall()]
            logger.info(f"Found {len(user_ids)} users for country={country}")
            return user_ids
    except Exception as e:
        logger.error(f"Users fetch error for country={country}: {e}")
        return []
    finally:
        conn.close()