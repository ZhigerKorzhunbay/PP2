from config import DB_CONFIG

try:
    import psycopg2
except ImportError:
    psycopg2 = None


def connect():
    if not psycopg2:
        raise RuntimeError("Install: pip install psycopg2-binary")
    return psycopg2.connect(**DB_CONFIG)


def run(sql, params=(), fetch=False):
    with connect() as con, con.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall() if fetch else None


def init_db():
    run("""
    CREATE TABLE IF NOT EXISTS players(
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL
    );
    CREATE TABLE IF NOT EXISTS game_sessions(
        id SERIAL PRIMARY KEY,
        player_id INTEGER REFERENCES players(id) ON DELETE CASCADE,
        score INTEGER NOT NULL,
        level_reached INTEGER NOT NULL,
        played_at TIMESTAMP DEFAULT NOW()
    );
    """)


def player_id(username):
    return run("""
        INSERT INTO players(username) VALUES(%s)
        ON CONFLICT(username) DO UPDATE SET username = EXCLUDED.username
        RETURNING id
    """, (username,), True)[0][0]


def save_session(username, score, level):
    run("INSERT INTO game_sessions(player_id, score, level_reached) VALUES(%s,%s,%s)",
        (player_id(username), score, level))


def personal_best(username):
    return run("""
        SELECT COALESCE(MAX(gs.score), 0)
        FROM game_sessions gs JOIN players p ON p.id = gs.player_id
        WHERE p.username = %s
    """, (username,), True)[0][0]


def top_scores(limit=10):
    return run("""
        SELECT p.username, gs.score, gs.level_reached,
               TO_CHAR(gs.played_at, 'YYYY-MM-DD HH24:MI')
        FROM game_sessions gs JOIN players p ON p.id = gs.player_id
        ORDER BY gs.score DESC, gs.level_reached DESC, gs.played_at ASC
        LIMIT %s
    """, (limit,), True)
