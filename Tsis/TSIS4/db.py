from config import DB_CONFIG

try:
    import psycopg2
except ImportError:  # keeps the game window usable if driver is missing
    psycopg2 = None


def connect():
    if psycopg2 is None:
        raise RuntimeError("Install psycopg2-binary first: pip install psycopg2-binary")
    return psycopg2.connect(**DB_CONFIG)


def init_db():
    sql = """
    CREATE TABLE IF NOT EXISTS players (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL
    );
    CREATE TABLE IF NOT EXISTS game_sessions (
        id SERIAL PRIMARY KEY,
        player_id INTEGER REFERENCES players(id) ON DELETE CASCADE,
        score INTEGER NOT NULL,
        level_reached INTEGER NOT NULL,
        played_at TIMESTAMP DEFAULT NOW()
    );
    """
    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql)


def player_id(username):
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO players(username) VALUES(%s)
            ON CONFLICT(username) DO UPDATE SET username = EXCLUDED.username
            RETURNING id;
            """,
            (username,),
        )
        return cur.fetchone()[0]


def save_session(username, score, level):
    pid = player_id(username)
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO game_sessions(player_id, score, level_reached) VALUES(%s, %s, %s)",
            (pid, score, level),
        )


def personal_best(username):
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT COALESCE(MAX(gs.score), 0)
            FROM game_sessions gs
            JOIN players p ON p.id = gs.player_id
            WHERE p.username = %s;
            """,
            (username,),
        )
        return cur.fetchone()[0]


def top_scores(limit=10):
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT p.username, gs.score, gs.level_reached,
                   TO_CHAR(gs.played_at, 'YYYY-MM-DD HH24:MI')
            FROM game_sessions gs
            JOIN players p ON p.id = gs.player_id
            ORDER BY gs.score DESC, gs.level_reached DESC, gs.played_at ASC
            LIMIT %s;
            """,
            (limit,),
        )
        return cur.fetchall()
