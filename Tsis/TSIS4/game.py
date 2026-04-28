import json
import random
from pathlib import Path

import pygame

import db
from config import (
    CELL, DB_CONFIG, FOOD_LIFETIME, FPS_MAX, FPS_START, HEIGHT,
    POWERUP_DURATION, POWERUP_LIFETIME, SETTINGS_FILE, WIDTH,
)

pygame.init()

BLACK = (12, 12, 16)
WHITE = (240, 240, 240)
GRAY = (70, 70, 75)
DARK_GRAY = (35, 35, 40)
RED = (230, 40, 40)
DARK_RED = (120, 0, 0)
GREEN = (0, 220, 80)
YELLOW = (255, 220, 70)
BLUE = (70, 150, 255)
ORANGE = (255, 165, 0)
PURPLE = (170, 60, 255)
CYAN = (0, 220, 220)
PINK = (255, 90, 170)

DIRS = {
    pygame.K_UP: (0, -1), pygame.K_w: (0, -1),
    pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
    pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0),
    pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
}
FOODS = [
    {"name": "Light", "value": 1, "color": WHITE},
    {"name": "Medium", "value": 2, "color": ORANGE},
    {"name": "Heavy", "value": 3, "color": PURPLE},
]
POWERUPS = [
    {"kind": "speed", "name": "Speed", "color": CYAN},
    {"kind": "slow", "name": "Slow", "color": BLUE},
    {"kind": "shield", "name": "Shield", "color": YELLOW},
]
DEFAULT_SETTINGS = {"snake_color": [0, 255, 0], "grid": True, "sound": True}


def load_settings():
    path = Path(SETTINGS_FILE)
    if not path.exists():
        save_settings(DEFAULT_SETTINGS.copy())
        return DEFAULT_SETTINGS.copy()
    try:
        data = json.loads(path.read_text())
        return {**DEFAULT_SETTINGS, **data}
    except Exception:
        return DEFAULT_SETTINGS.copy()


def save_settings(data):
    Path(SETTINGS_FILE).write_text(json.dumps(data, indent=2))


class SnakeGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("TSIS 4 Snake")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18)
        self.big = pygame.font.SysFont("Arial", 46, bold=True)
        self.mid = pygame.font.SysFont("Arial", 26, bold=True)
        self.settings = load_settings()
        self.username = ""
        self.state = "menu"
        self.running = True
        self.db_error = None
        try:
            db.init_db()
        except Exception as e:
            self.db_error = str(e)
        self.reset_game()

    # ---------- small UI helpers ----------
    def text(self, msg, pos, color=WHITE, font=None, center=False):
        img = (font or self.font).render(str(msg), True, color)
        rect = img.get_rect(center=pos) if center else img.get_rect(topleft=pos)
        self.screen.blit(img, rect)
        return rect

    def button(self, label, rect, mouse_pos):
        r = pygame.Rect(rect)
        hover = r.collidepoint(mouse_pos)
        pygame.draw.rect(self.screen, (55, 55, 65) if hover else DARK_GRAY, r, border_radius=8)
        pygame.draw.rect(self.screen, GRAY, r, 2, border_radius=8)
        self.text(label, r.center, WHITE, self.font, True)
        return r

    def db_call(self, fallback, fn, *args):
        try:
            return fn(*args)
        except Exception as e:
            self.db_error = str(e)
            return fallback

    # ---------- spawning and state ----------
    def occupied(self):
        cells = set(self.snake) | self.obstacles
        if self.food:
            cells.add(self.food["pos"])
        if self.poison:
            cells.add(self.poison["pos"])
        if self.powerup:
            cells.add(self.powerup["pos"])
        return cells

    def free_pos(self, extra=()):
        used = self.occupied() | set(extra)
        while True:
            p = (random.randrange(WIDTH // CELL) * CELL, random.randrange(HEIGHT // CELL) * CELL)
            if p not in used:
                return p

    def spawn_food(self):
        f = random.choice(FOODS).copy()
        f["pos"] = self.free_pos()
        f["spawn"] = pygame.time.get_ticks()
        return f

    def spawn_poison(self):
        return {"pos": self.free_pos(), "color": DARK_RED}

    def spawn_powerup(self):
        p = random.choice(POWERUPS).copy()
        p["pos"] = self.free_pos()
        p["spawn"] = pygame.time.get_ticks()
        return p

    def reset_game(self):
        self.snake = [(100, 100), (80, 100), (60, 100), (40, 100)]
        self.direction = self.next_dir = (1, 0)
        self.score = 0
        self.level = 1
        self.eaten = 0
        self.need = 3
        self.base_speed = FPS_START
        self.obstacles = set()
        self.food = None
        self.poison = None
        self.powerup = None
        self.food = self.spawn_food()
        self.poison = self.spawn_poison()
        self.effect = None
        self.effect_until = 0
        self.shield = False
        self.next_power_time = pygame.time.get_ticks() + random.randint(3500, 7500)
        self.final_score = self.final_level = 0
        self.saved = False
        self.best = self.db_call(0, db.personal_best, self.username)

    def start_game(self):
        self.username = self.username.strip()[:50] or "Player"
        self.reset_game()
        self.state = "play"

    def level_up(self):
        self.level += 1
        self.eaten = 0
        self.need = min(8, 3 + self.level - 1)
        self.base_speed = min(FPS_START + (self.level - 1) * 2, FPS_MAX)
        if self.level >= 3:
            self.make_obstacles()

    def make_obstacles(self):
        head = self.snake[0]
        safe = {head, (head[0] + CELL, head[1]), (head[0] - CELL, head[1]),
                (head[0], head[1] + CELL), (head[0], head[1] - CELL)}
        self.obstacles = set()
        for _ in range(min(8 + self.level * 2, 35)):
            self.obstacles.add(self.free_pos(safe))

    # ---------- game logic ----------
    def current_speed(self):
        now = pygame.time.get_ticks()
        if self.effect and now >= self.effect_until:
            self.effect = None
        if self.effect == "speed":
            return min(FPS_MAX + 8, self.base_speed + 7)
        if self.effect == "slow":
            return max(5, self.base_speed - 6)
        return self.base_speed

    def update_powerup(self):
        now = pygame.time.get_ticks()
        if self.powerup and now - self.powerup["spawn"] >= POWERUP_LIFETIME:
            self.powerup = None
            self.next_power_time = now + random.randint(4000, 9000)
        if not self.powerup and now >= self.next_power_time:
            self.powerup = self.spawn_powerup()

    def crash(self):
        self.final_score, self.final_level = self.score, self.level
        if not self.saved:
            self.db_call(None, db.save_session, self.username, self.score, self.level)
            self.best = max(self.best, self.score)
            self.saved = True
        self.state = "game_over"

    def use_shield(self, new_head, reason):
        if not self.shield:
            return new_head, False
        self.shield = False
        if reason == "wall":
            return (new_head[0] % WIDTH, new_head[1] % HEIGHT), True
        if reason == "obstacle":
            self.obstacles.discard(new_head)  # shield breaks one obstacle
        return new_head, True

    def step(self):
        now = pygame.time.get_ticks()
        self.update_powerup()
        if now - self.food["spawn"] >= FOOD_LIFETIME:
            self.food = self.spawn_food()

        self.direction = self.next_dir
        hx, hy = self.snake[0]
        dx, dy = self.direction
        new = (hx + dx * CELL, hy + dy * CELL)

        if not (0 <= new[0] < WIDTH and 0 <= new[1] < HEIGHT):
            new, ok = self.use_shield(new, "wall")
            if not ok:
                self.crash(); return

        if new in self.obstacles:
            new, ok = self.use_shield(new, "obstacle")
            if not ok:
                self.crash(); return

        ate_food = new == self.food["pos"]
        ate_poison = new == self.poison["pos"]
        ate_power = self.powerup and new == self.powerup["pos"]
        self.snake.insert(0, new)

        if ate_food:
            self.score += self.food["value"] * 10
            self.eaten += 1
            self.food = self.spawn_food()
            if self.eaten >= self.need:
                self.level_up()
        else:
            self.snake.pop()

        if ate_poison:
            for _ in range(2):
                if len(self.snake) > 1:
                    self.snake.pop()
            self.poison = self.spawn_poison()
            if len(self.snake) <= 1:
                self.crash(); return

        if ate_power:
            kind = self.powerup["kind"]
            if kind == "shield":
                self.shield = True
            else:
                self.effect, self.effect_until = kind, now + POWERUP_DURATION
            self.powerup = None
            self.next_power_time = now + random.randint(5000, 10000)

        if self.snake[0] in self.snake[1:]:
            _, ok = self.use_shield(self.snake[0], "self")
            if not ok:
                self.crash()

    # ---------- drawing ----------
    def draw_grid(self):
        if not self.settings.get("grid"):
            return
        for x in range(0, WIDTH, CELL):
            pygame.draw.line(self.screen, (24, 24, 28), (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, CELL):
            pygame.draw.line(self.screen, (24, 24, 28), (0, y), (WIDTH, y))

    def draw_game(self):
        self.screen.fill(BLACK)
        self.draw_grid()
        for p in self.obstacles:
            pygame.draw.rect(self.screen, GRAY, (*p, CELL, CELL))
        pygame.draw.rect(self.screen, self.food["color"], (*self.food["pos"], CELL, CELL))
        pygame.draw.rect(self.screen, self.poison["color"], (*self.poison["pos"], CELL, CELL))
        if self.powerup:
            pygame.draw.rect(self.screen, self.powerup["color"], (*self.powerup["pos"], CELL, CELL), border_radius=6)
        color = tuple(self.settings.get("snake_color", [0, 255, 0]))
        for part in self.snake[1:]:
            pygame.draw.rect(self.screen, color, (*part, CELL, CELL))
        pygame.draw.rect(self.screen, YELLOW, (*self.snake[0], CELL, CELL))

        left = f"User: {self.username}  Score: {self.score}  Level: {self.level}  Best: {self.best}"
        remain = self.need - self.eaten
        food_s = max(0, (FOOD_LIFETIME - (pygame.time.get_ticks() - self.food["spawn"])) // 1000 + 1)
        status = f"Food: {self.food['name']} +{self.food['value']*10}, {food_s}s | Next level: {remain}"
        power = "Shield ready" if self.shield else (f"Effect: {self.effect}" if self.effect else "Power-up: none")
        self.text(left, (10, 8), WHITE)
        self.text(status, (10, 30), self.food["color"])
        self.text(power, (WIDTH - 180, 30), YELLOW if self.shield else CYAN)
        if self.db_error:
            self.text("DB offline", (WIDTH - 95, 8), RED)

    # ---------- screens ----------
    def menu(self):
        play_r = pygame.Rect(260, 190, 200, 42)
        lead_r = pygame.Rect(260, 245, 200, 42)
        sett_r = pygame.Rect(260, 300, 200, 42)
        quit_r = pygame.Rect(260, 355, 200, 42)
        while self.running and self.state == "menu":
            mouse = pygame.mouse.get_pos()
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_BACKSPACE:
                        self.username = self.username[:-1]
                    elif e.key == pygame.K_RETURN:
                        self.start_game()
                    elif e.unicode and len(self.username) < 16 and (e.unicode.isalnum() or e.unicode in "_-"):
                        self.username += e.unicode
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    if play_r.collidepoint(e.pos): self.start_game()
                    if lead_r.collidepoint(e.pos): self.state = "leaderboard"
                    if sett_r.collidepoint(e.pos): self.state = "settings"
                    if quit_r.collidepoint(e.pos): self.running = False

            self.screen.fill(BLACK)
            self.text("SNAKE", (WIDTH // 2, 70), GREEN, self.big, True)
            self.text("Type username:", (WIDTH // 2 - 150, 135), WHITE)
            pygame.draw.rect(self.screen, DARK_GRAY, (WIDTH // 2 - 25, 128, 190, 32), border_radius=6)
            self.text(self.username + "_", (WIDTH // 2 - 15, 135), YELLOW)
            self.button("Play", play_r, mouse)
            self.button("Leaderboard", lead_r, mouse)
            self.button("Settings", sett_r, mouse)
            self.button("Quit", quit_r, mouse)
            if self.db_error:
                self.text("DB: check config.py / PostgreSQL", (WIDTH // 2, 430), RED, self.font, True)
            pygame.display.flip(); self.clock.tick(30)

    def play(self):
        while self.running and self.state == "play":
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        self.state = "menu"
                    if e.key in DIRS:
                        nd = DIRS[e.key]
                        if (nd[0] + self.direction[0], nd[1] + self.direction[1]) != (0, 0):
                            self.next_dir = nd
            self.step()
            self.draw_game()
            pygame.display.flip()
            self.clock.tick(self.current_speed())

    def game_over(self):
        retry_r = pygame.Rect(250, 315, 220, 42)
        menu_r = pygame.Rect(250, 370, 220, 42)
        while self.running and self.state == "game_over":
            mouse = pygame.mouse.get_pos()
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    if retry_r.collidepoint(e.pos): self.start_game()
                    if menu_r.collidepoint(e.pos): self.state = "menu"
            self.screen.fill(BLACK)
            self.text("GAME OVER", (WIDTH // 2, 95), RED, self.big, True)
            self.text(f"Final score: {self.final_score}", (WIDTH // 2, 170), WHITE, self.mid, True)
            self.text(f"Level reached: {self.final_level}", (WIDTH // 2, 210), WHITE, self.mid, True)
            self.text(f"Personal best: {self.best}", (WIDTH // 2, 250), YELLOW, self.mid, True)
            self.button("Retry", retry_r, mouse)
            self.button("Main Menu", menu_r, mouse)
            pygame.display.flip(); self.clock.tick(30)

    def leaderboard(self):
        rows = self.db_call([], db.top_scores, 10)
        back_r = pygame.Rect(280, 415, 160, 40)
        while self.running and self.state == "leaderboard":
            mouse = pygame.mouse.get_pos()
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    self.state = "menu"
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and back_r.collidepoint(e.pos):
                    self.state = "menu"
            self.screen.fill(BLACK)
            self.text("LEADERBOARD", (WIDTH // 2, 45), YELLOW, self.mid, True)
            self.text("#   Username             Score   Level   Date", (80, 95), WHITE)
            if not rows:
                msg = "No scores yet" if not self.db_error else "Database is not connected"
                self.text(msg, (WIDTH // 2, 170), RED if self.db_error else WHITE, self.mid, True)
            for i, (user, score, lvl, date) in enumerate(rows, 1):
                self.text(f"{i:<3} {user[:18]:<18} {score:<7} {lvl:<6} {date}", (80, 95 + i * 28), WHITE)
            self.button("Back", back_r, mouse)
            pygame.display.flip(); self.clock.tick(30)

    def settings_screen(self):
        s = {**self.settings, "snake_color": list(self.settings.get("snake_color", [0, 255, 0]))}
        grid_r = pygame.Rect(250, 120, 220, 42)
        sound_r = pygame.Rect(250, 175, 220, 42)
        r_r = pygame.Rect(210, 325, 90, 40)
        g_r = pygame.Rect(315, 325, 90, 40)
        b_r = pygame.Rect(420, 325, 90, 40)
        save_r = pygame.Rect(250, 400, 220, 42)
        while self.running and self.state == "settings":
            mouse = pygame.mouse.get_pos()
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    self.state = "menu"
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    col = s["snake_color"]
                    if grid_r.collidepoint(e.pos): s["grid"] = not s["grid"]
                    if sound_r.collidepoint(e.pos): s["sound"] = not s["sound"]
                    if r_r.collidepoint(e.pos): col[0] = (col[0] + 25) % 256
                    if g_r.collidepoint(e.pos): col[1] = (col[1] + 25) % 256
                    if b_r.collidepoint(e.pos): col[2] = (col[2] + 25) % 256
                    if save_r.collidepoint(e.pos):
                        self.settings = s
                        save_settings(self.settings)
                        self.state = "menu"
            self.screen.fill(BLACK)
            self.text("SETTINGS", (WIDTH // 2, 55), YELLOW, self.mid, True)
            self.button(f"Grid: {'ON' if s['grid'] else 'OFF'}", grid_r, mouse)
            self.button(f"Sound: {'ON' if s['sound'] else 'OFF'}", sound_r, mouse)
            self.text(f"Snake RGB: {tuple(s['snake_color'])}", (WIDTH // 2, 245), WHITE, self.font, True)
            pygame.draw.rect(self.screen, tuple(s["snake_color"]), (330, 275, 60, 28), border_radius=5)
            self.button("R +", r_r, mouse)
            self.button("G +", g_r, mouse)
            self.button("B +", b_r, mouse)
            self.button("Save & Back", save_r, mouse)
            pygame.display.flip(); self.clock.tick(30)

    def run(self):
        screens = {
            "menu": self.menu,
            "play": self.play,
            "game_over": self.game_over,
            "leaderboard": self.leaderboard,
            "settings": self.settings_screen,
        }
        while self.running:
            screens[self.state]()
        pygame.quit()
