import json, random
from pathlib import Path

import pygame

import db
from config import *

pygame.init()

C = {
    "bg": (12, 12, 16), "panel": (35, 35, 40), "border": (75, 75, 85),
    "white": (240, 240, 240), "red": (230, 40, 40), "poison": (120, 0, 0),
    "green": (0, 220, 80), "yellow": (255, 220, 70), "blue": (70, 150, 255),
    "orange": (255, 165, 0), "purple": (170, 60, 255), "cyan": (0, 220, 220),
}
DIRS = {
    pygame.K_UP: (0, -1), pygame.K_w: (0, -1), pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
    pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0), pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
}
FOODS = [("Light", 1, C["white"]), ("Medium", 2, C["orange"]), ("Heavy", 3, C["purple"])]
POWERUPS = [("speed", C["cyan"]), ("slow", C["blue"]), ("shield", C["yellow"])]
DEFAULT_SETTINGS = {"snake_color": [0, 255, 0], "grid": True, "sound": True}


def load_settings():
    try:
        return {**DEFAULT_SETTINGS, **json.loads(Path(SETTINGS_FILE).read_text())}
    except Exception:
        save_settings(DEFAULT_SETTINGS.copy())
        return DEFAULT_SETTINGS.copy()


def save_settings(data):
    Path(SETTINGS_FILE).write_text(json.dumps(data, indent=2))


class SnakeGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("TSIS 4 Snake")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18)
        self.mid = pygame.font.SysFont("Arial", 26, bold=True)
        self.big = pygame.font.SysFont("Arial", 46, bold=True)
        self.settings, self.username, self.state, self.running = load_settings(), "", "menu", True
        self.db_error = self.safe(None, db.init_db)
        self.reset()

    # ---------- helpers ----------
    def safe(self, fallback, fn, *args):
        try:
            return fn(*args)
        except Exception as e:
            self.db_error = str(e)
            return fallback

    def text(self, msg, pos, color=None, font=None, center=False):
        img = (font or self.font).render(str(msg), True, color or C["white"])
        self.screen.blit(img, img.get_rect(center=pos) if center else img.get_rect(topleft=pos))

    def button(self, label, rect):
        rect, mouse = pygame.Rect(rect), pygame.mouse.get_pos()
        pygame.draw.rect(self.screen, (55, 55, 65) if rect.collidepoint(mouse) else C["panel"], rect, border_radius=8)
        pygame.draw.rect(self.screen, C["border"], rect, 2, border_radius=8)
        self.text(label, rect.center, C["white"], self.font, True)
        return rect

    def buttons(self, data):
        return {name: self.button(label, rect) for name, label, rect in data}

    def occupied(self):
        used = set(self.snake) | self.obstacles
        for item in (self.food, self.poison, self.powerup):
            if item:
                used.add(item["pos"])
        return used

    def free(self, extra=()):
        used = self.occupied() | set(extra)
        while True:
            p = (random.randrange(WIDTH // CELL) * CELL, random.randrange(HEIGHT // CELL) * CELL)
            if p not in used:
                return p

    def spawn_food(self):
        name, value, color = random.choice(FOODS)
        return {"name": name, "value": value, "color": color, "pos": self.free(), "spawn": pygame.time.get_ticks()}

    def spawn_poison(self):
        return {"pos": self.free(), "color": C["poison"]}

    def spawn_powerup(self):
        kind, color = random.choice(POWERUPS)
        return {"kind": kind, "color": color, "pos": self.free(), "spawn": pygame.time.get_ticks()}

    # ---------- game state ----------
    def reset(self):
        self.snake = [(100, 100), (80, 100), (60, 100), (40, 100)]
        self.direction = self.next_dir = (1, 0)
        self.score = self.eaten = self.final_score = self.final_level = 0
        self.level, self.need, self.base_speed = 1, 3, FPS_START
        self.obstacles, self.food, self.poison, self.powerup = set(), None, None, None
        self.effect, self.effect_until, self.shield, self.saved = None, 0, False, False
        self.food, self.poison = self.spawn_food(), self.spawn_poison()
        self.next_power = pygame.time.get_ticks() + random.randint(3500, 7500)
        self.best = self.safe(0, db.personal_best, self.username)

    def start(self):
        self.username = (self.username.strip() or "Player")[:50]
        self.reset()
        self.state = "play"

    def level_up(self):
        self.level, self.eaten = self.level + 1, 0
        self.need = min(8, self.level + 2)
        self.base_speed = min(FPS_START + (self.level - 1) * 2, FPS_MAX)
        if self.level >= 3:
            self.make_obstacles()

    def make_obstacles(self):
        x, y = self.snake[0]
        safe = {(x, y), (x + CELL, y), (x - CELL, y), (x, y + CELL), (x, y - CELL)}
        self.obstacles = {self.free(safe) for _ in range(min(8 + self.level * 2, 35))}

    def speed(self):
        if self.effect and pygame.time.get_ticks() >= self.effect_until:
            self.effect = None
        return min(FPS_MAX + 8, self.base_speed + 7) if self.effect == "speed" else max(5, self.base_speed - 6) if self.effect == "slow" else self.base_speed

    def die(self):
        self.final_score, self.final_level = self.score, self.level
        if not self.saved:
            self.safe(None, db.save_session, self.username, self.score, self.level)
            self.best, self.saved = max(self.best, self.score), True
        self.state = "game_over"

    def shield_hit(self, head, kind):
        if not self.shield:
            return head, False
        self.shield = False
        if kind == "wall":
            return (head[0] % WIDTH, head[1] % HEIGHT), True
        if kind == "obstacle":
            self.obstacles.discard(head)
        return head, True

    def update_powerup(self):
        now = pygame.time.get_ticks()
        if self.powerup and now - self.powerup["spawn"] >= POWERUP_LIFETIME:
            self.powerup, self.next_power = None, now + random.randint(4000, 9000)
        if not self.powerup and now >= self.next_power:
            self.powerup = self.spawn_powerup()

    def step(self):
        now = pygame.time.get_ticks()
        self.update_powerup()
        if now - self.food["spawn"] >= FOOD_LIFETIME:
            self.food = self.spawn_food()

        self.direction = self.next_dir
        hx, hy = self.snake[0]
        dx, dy = self.direction
        head = (hx + dx * CELL, hy + dy * CELL)

        if not (0 <= head[0] < WIDTH and 0 <= head[1] < HEIGHT):
            head, ok = self.shield_hit(head, "wall")
            if not ok:
                self.die(); return
        if head in self.obstacles:
            head, ok = self.shield_hit(head, "obstacle")
            if not ok:
                self.die(); return

        ate_food = head == self.food["pos"]
        ate_poison = head == self.poison["pos"]
        ate_power = self.powerup and head == self.powerup["pos"]
        self.snake.insert(0, head)

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
                self.die(); return

        if ate_power:
            if self.powerup["kind"] == "shield":
                self.shield = True
            else:
                self.effect, self.effect_until = self.powerup["kind"], now + POWERUP_DURATION
            self.powerup, self.next_power = None, now + random.randint(5000, 10000)

        if self.snake[0] in self.snake[1:]:
            _, ok = self.shield_hit(self.snake[0], "self")
            if not ok:
                self.die()

    # ---------- drawing ----------
    def draw_grid(self):
        if self.settings.get("grid"):
            for x in range(0, WIDTH, CELL):
                pygame.draw.line(self.screen, (24, 24, 28), (x, 0), (x, HEIGHT))
            for y in range(0, HEIGHT, CELL):
                pygame.draw.line(self.screen, (24, 24, 28), (0, y), (WIDTH, y))

    def draw_game(self):
        self.screen.fill(C["bg"]); self.draw_grid()
        for p in self.obstacles:
            pygame.draw.rect(self.screen, C["border"], (*p, CELL, CELL))
        for item in (self.food, self.poison, self.powerup):
            if item:
                pygame.draw.rect(self.screen, item["color"], (*item["pos"], CELL, CELL), border_radius=5)
        snake_color = tuple(self.settings.get("snake_color", [0, 255, 0]))
        for p in self.snake[1:]:
            pygame.draw.rect(self.screen, snake_color, (*p, CELL, CELL))
        pygame.draw.rect(self.screen, C["yellow"], (*self.snake[0], CELL, CELL))

        food_left = max(0, (FOOD_LIFETIME - (pygame.time.get_ticks() - self.food["spawn"])) // 1000 + 1)
        power = "Shield ready" if self.shield else f"Effect: {self.effect}" if self.effect else "Power-up: none"
        self.text(f"User: {self.username}  Score: {self.score}  Level: {self.level}  Best: {self.best}", (10, 8))
        self.text(f"Food: {self.food['name']} +{self.food['value']*10}, {food_left}s | Next level: {self.need - self.eaten}", (10, 30), self.food["color"])
        self.text(power, (WIDTH - 180, 30), C["yellow"] if self.shield else C["cyan"])
        if self.db_error:
            self.text("DB offline", (WIDTH - 95, 8), C["red"])

    # ---------- screens ----------
    def menu(self):
        data = [("play", "Play", (260, 190, 200, 42)), ("leaderboard", "Leaderboard", (260, 245, 200, 42)),
                ("settings", "Settings", (260, 300, 200, 42)), ("quit", "Quit", (260, 355, 200, 42))]
        while self.running and self.state == "menu":
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_BACKSPACE:
                        self.username = self.username[:-1]
                    elif e.key == pygame.K_RETURN:
                        self.start()
                    elif e.unicode and len(self.username) < 16 and (e.unicode.isalnum() or e.unicode in "_-"):
                        self.username += e.unicode
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for name, _, r in data:
                        if pygame.Rect(r).collidepoint(e.pos):
                            self.start() if name == "play" else setattr(self, "running", False) if name == "quit" else setattr(self, "state", name)
            self.screen.fill(C["bg"])
            self.text("SNAKE", (WIDTH // 2, 70), C["green"], self.big, True)
            self.text("Type username:", (WIDTH // 2 - 150, 135))
            pygame.draw.rect(self.screen, C["panel"], (WIDTH // 2 - 25, 128, 190, 32), border_radius=6)
            self.text(self.username + "_", (WIDTH // 2 - 15, 135), C["yellow"])
            self.buttons(data)
            if self.db_error:
                self.text("DB: check config.py / PostgreSQL", (WIDTH // 2, 430), C["red"], self.font, True)
            pygame.display.flip(); self.clock.tick(30)

    def play(self):
        while self.running and self.state == "play":
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        self.state = "menu"
                    if e.key in DIRS and tuple(a + b for a, b in zip(DIRS[e.key], self.direction)) != (0, 0):
                        self.next_dir = DIRS[e.key]
            self.step(); self.draw_game(); pygame.display.flip(); self.clock.tick(self.speed())

    def game_over(self):
        data = [("retry", "Retry", (250, 315, 220, 42)), ("menu", "Main Menu", (250, 370, 220, 42))]
        while self.running and self.state == "game_over":
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    if pygame.Rect(data[0][2]).collidepoint(e.pos): self.start()
                    if pygame.Rect(data[1][2]).collidepoint(e.pos): self.state = "menu"
            self.screen.fill(C["bg"])
            self.text("GAME OVER", (WIDTH // 2, 95), C["red"], self.big, True)
            for i, line in enumerate((f"Final score: {self.final_score}", f"Level reached: {self.final_level}", f"Personal best: {self.best}")):
                self.text(line, (WIDTH // 2, 170 + i * 40), C["yellow"] if i == 2 else C["white"], self.mid, True)
            self.buttons(data); pygame.display.flip(); self.clock.tick(30)

    def leaderboard(self):
        rows = self.safe([], db.top_scores, 10)
        while self.running and self.state == "leaderboard":
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    self.state = "menu"
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and pygame.Rect(280, 415, 160, 40).collidepoint(e.pos):
                    self.state = "menu"
            self.screen.fill(C["bg"])
            self.text("LEADERBOARD", (WIDTH // 2, 45), C["yellow"], self.mid, True)
            self.text("#   Username             Score   Level   Date", (80, 95))
            if not rows:
                self.text("Database is not connected" if self.db_error else "No scores yet", (WIDTH // 2, 170), C["red"] if self.db_error else C["white"], self.mid, True)
            for i, (user, score, lvl, date) in enumerate(rows, 1):
                self.text(f"{i:<3} {user[:18]:<18} {score:<7} {lvl:<6} {date}", (80, 95 + i * 28))
            self.button("Back", (280, 415, 160, 40)); pygame.display.flip(); self.clock.tick(30)

    def settings_screen(self):
        s = {**self.settings, "snake_color": list(self.settings.get("snake_color", [0, 255, 0]))}
        data = [("grid", "Grid", (250, 120, 220, 42)), ("sound", "Sound", (250, 175, 220, 42)),
                ("r", "R +", (210, 325, 90, 40)), ("g", "G +", (315, 325, 90, 40)),
                ("b", "B +", (420, 325, 90, 40)), ("save", "Save & Back", (250, 400, 220, 42))]
        while self.running and self.state == "settings":
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    self.state = "menu"
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for name, _, r in data:
                        if pygame.Rect(r).collidepoint(e.pos):
                            if name in ("grid", "sound"):
                                s[name] = not s[name]
                            elif name in "rgb":
                                s["snake_color"]["rgb".index(name)] = (s["snake_color"]["rgb".index(name)] + 25) % 256
                            elif name == "save":
                                self.settings = s; save_settings(s); self.state = "menu"
            self.screen.fill(C["bg"])
            self.text("SETTINGS", (WIDTH // 2, 55), C["yellow"], self.mid, True)
            shown = [("grid", f"Grid: {'ON' if s['grid'] else 'OFF'}", data[0][2]), ("sound", f"Sound: {'ON' if s['sound'] else 'OFF'}", data[1][2])] + data[2:]
            self.buttons(shown)
            self.text(f"Snake RGB: {tuple(s['snake_color'])}", (WIDTH // 2, 245), center=True)
            pygame.draw.rect(self.screen, tuple(s["snake_color"]), (330, 275, 60, 28), border_radius=5)
            pygame.display.flip(); self.clock.tick(30)

    def run(self):
        screens = {"menu": self.menu, "play": self.play, "game_over": self.game_over, "leaderboard": self.leaderboard, "settings": self.settings_screen}
        while self.running:
            screens[self.state]()
        pygame.quit()
