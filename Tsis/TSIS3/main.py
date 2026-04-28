import json, random, sys
from pathlib import Path
import pygame

pygame.init()
try:
    pygame.mixer.init()
except pygame.error:
    pass

W, H, FPS = 400, 600, 60
ROAD = pygame.Rect(0, 0, W, H)
LANES = [50, 150, 250, 350]
BASE = Path(__file__).resolve().parent
ASSETS = BASE / "assets"
SETTINGS_FILE = BASE / "settings.json"
LEADERBOARD_FILE = BASE / "leaderboard.json"
DIFFS = {"Easy": (4.2, 1.25), "Normal": (5.4, 1.0), "Hard": (6.8, .75)}
DEFAULT_SETTINGS = {"sound": True, "difficulty": "Normal"}
WHITE, BLACK, GRAY, DARK = (240, 240, 240), (0, 0, 0), (80, 80, 80), (24, 28, 34)
RED, GREEN, YELLOW, BLUE = (220, 50, 50), (70, 190, 80), (235, 200, 50), (70, 160, 250)

screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Compact Street Racer")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("Verdana", 17)
BIG = pygame.font.SysFont("Verdana", 32, True)
MID = pygame.font.SysFont("Verdana", 22, True)
SMALL = pygame.font.SysFont("Consolas", 15, True)


def load_json(path, default):
    try:
        return {**default, **json.loads(path.read_text())} if isinstance(default, dict) else json.loads(path.read_text())
    except Exception:
        return default.copy() if isinstance(default, dict) else list(default)


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def image(name, size=None, alpha=True):
    try:
        img = pygame.image.load(ASSETS / name)
        img = img.convert_alpha() if alpha else img.convert()
    except Exception:
        img = pygame.Surface(size or (50, 50), pygame.SRCALPHA)
        img.fill((120, 120, 120))
    return pygame.transform.smoothscale(img, size) if size else img


def sound(name):
    try:
        return pygame.mixer.Sound(str(ASSETS / name))
    except Exception:
        return None


def label(text, font=FONT, color=WHITE):
    return font.render(str(text), True, color)


def center(text, y, font=FONT, color=WHITE):
    surf = label(text, font, color)
    screen.blit(surf, surf.get_rect(center=(W // 2, y)))


def btn(text, rect):
    mouse = pygame.mouse.get_pos()
    r = pygame.Rect(rect)
    pygame.draw.rect(screen, (50, 56, 66) if r.collidepoint(mouse) else DARK, r, border_radius=10)
    pygame.draw.rect(screen, GRAY, r, 2, border_radius=10)
    center(text, r.centery, FONT)
    return r


def draw_icon(kind, size):
    s = pygame.Surface(size, pygame.SRCALPHA)
    w, h = size
    if kind == "oil":
        pygame.draw.ellipse(s, (15, 15, 20), (2, 8, w - 4, h - 14))
        pygame.draw.ellipse(s, (80, 80, 90), (12, 14, w // 2, 8))
    elif kind == "hole":
        pygame.draw.ellipse(s, (35, 35, 38), (2, 3, w - 4, h - 7))
        pygame.draw.ellipse(s, (5, 5, 8), (14, 14, w - 28, h - 25))
    else:
        pygame.draw.rect(s, YELLOW, (0, h // 3, w, h // 3), border_radius=5)
        for x in range(6, w, 22):
            pygame.draw.rect(s, BLACK, (x, h // 3, 10, h // 3))
    return s


class Obj(pygame.sprite.Sprite):
    def __init__(self, kind, img, x, y, speed=1, vx=0, value=0, ttl=0):
        super().__init__()
        self.kind, self.image, self.speed, self.vx, self.value, self.ttl = kind, img, speed, vx, value, ttl
        self.rect = img.get_rect(midtop=(x, y))
        self.y, self.x, self.born = float(self.rect.y), float(self.rect.x), pygame.time.get_ticks()

    def update(self, world_speed, dt):
        self.y += world_speed * self.speed * dt
        self.rect.y = int(self.y)
        if self.vx:
            self.x += self.vx * dt
            self.rect.x = int(self.x)
            if self.rect.left <= ROAD.left or self.rect.right >= ROAD.right:
                self.vx *= -1
                self.rect.clamp_ip(ROAD)
                self.x = self.rect.x
        if self.rect.top > H + 80 or (self.ttl and pygame.time.get_ticks() - self.born > self.ttl):
            self.kill()


class Game:
    def __init__(self):
        self.settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
        self.board = load_json(LEADERBOARD_FILE, [])
        self.bg = image("AnimatedStreet.png", (W, H), False)
        self.player_base = image("Player.png", (45, 88))
        self.enemy_img = image("Enemy.png", (45, 88))
        self.coin_img = image("coin.png", (32, 32))
        self.power_imgs = {
            "Nitro": image("nitro.png", (45, 45)),
            "Shield": image("shield.png", (45, 45)),
            "Repair": image("repair.png", (45, 45)),
        }
        self.barrier_img = image("barrier.png", (82, 50))
        self.hazard_imgs = {
            "oil": draw_icon("oil", (62, 36)),
            "hole": draw_icon("hole", (62, 38)),
            "bump": draw_icon("bump", (82, 30)),
            "barrier": self.barrier_img,
            "moving_barrier": self.barrier_img,
        }
        self.crash = sound("crash.wav")
        if self.settings["sound"]:
            try:
                pygame.mixer.music.load(str(ASSETS / "background.wav")); pygame.mixer.music.play(-1)
            except Exception:
                pass
        self.name, self.state, self.running = "", "name", True
        self.reset()

    def reset(self):
        self.player_img = self.player_base
        self.player = Obj("player", self.player_img, W // 2, 500)
        self.player.rect.midbottom = (W // 2, H - 20)
        self.player.x, self.player.y = self.player.rect.x, self.player.rect.y
        self.all = pygame.sprite.Group(self.player)
        self.bad = pygame.sprite.Group()
        self.slow = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.powers = pygame.sprite.Group()
        self.base_speed, self.spawn_rate = DIFFS[self.settings["difficulty"]]
        self.distance = self.coins_count = self.coin_score = self.bonus = 0
        self.bg_y = self.last_spawn = self.last_coin = self.last_power = 0
        self.active, self.active_until, self.shield_hits = None, 0, 0
        self.slow_until = 0

    def safe_lane(self):
        free = LANES[:]
        if self.player.rect.top < 150:
            free = [x for x in free if abs(x - self.player.rect.centerx) > 70] or free
        used = [s.rect.centerx for s in list(self.bad) + list(self.slow) if s.rect.top < 120]
        free = [x for x in free if all(abs(x - u) > 55 for u in used)] or LANES
        return random.choice(free)

    def add(self, group, obj):
        self.all.add(obj); group.add(obj)

    def spawn_bad(self, speed):
        kind = random.choices(["car", "barrier", "moving_barrier", "oil", "hole", "bump"], [36, 16, 10, 16, 12, 10])[0]
        x, y = self.safe_lane(), -random.randint(60, 180)
        if kind == "car":
            obj = Obj("car", self.enemy_img, x, y, random.uniform(.9, 1.15))
            self.add(self.bad, obj)
        elif kind in ("oil", "bump"):
            self.add(self.slow, Obj(kind, self.hazard_imgs[kind], x, y, .95))
        else:
            vx = random.choice([-2.2, 2.2]) if kind == "moving_barrier" else 0
            self.add(self.bad, Obj(kind, self.hazard_imgs[kind], x, y, 1, vx))

    def spawn_coin(self):
        value = random.choices([1, 2, 3], [65, 25, 10])[0]
        size = 26 + value * 6
        self.add(self.coins, Obj("coin", image("coin.png", (size, size)), self.safe_lane(), -50, .9, value=value))

    def spawn_power(self):
        kind = random.choice(["Nitro", "Shield", "Repair"])
        self.add(self.powers, Obj(kind, self.power_imgs[kind], self.safe_lane(), -50, .9, ttl=6500))

    def speed(self):
        s = self.base_speed + min(self.distance / 2200, 5)
        return s + 3 if self.active == "Nitro" else s

    def score(self):
        return int(self.distance / 10 + self.coin_score * 10 + self.bonus)

    def start_game(self):
        self.reset()
        self.state = "play"
        if self.settings["sound"]:
            try:
                pygame.mixer.music.play(-1)
            except Exception:
                pass

    def finish(self):
        if self.crash and self.settings["sound"]:
            self.crash.play()
        row = {"name": self.name or "Player", "score": self.score(), "distance": int(self.distance), "coins": self.coins_count}
        self.board = sorted(self.board + [row], key=lambda x: x["score"], reverse=True)[:10]
        save_json(LEADERBOARD_FILE, self.board)
        self.state = "over"

    def use_repair(self):
        targets = sorted(list(self.bad) + list(self.slow), key=lambda s: abs(s.rect.centery - self.player.rect.centery))
        if targets:
            targets[0].kill(); self.bonus += 25

    def update_play(self, dt):
        keys = pygame.key.get_pressed()
        move = 5.7 if pygame.time.get_ticks() > self.slow_until else 3.1
        self.player.x += ((keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])) * move * dt
        self.player.rect.x = int(max(ROAD.left, min(ROAD.right - self.player.rect.w, self.player.x)))
        self.player.x = self.player.rect.x

        now, spd = pygame.time.get_ticks(), self.speed()
        self.distance += spd * dt
        self.bg_y = (self.bg_y + spd * dt) % H
        interval = max(450, 1050 - self.distance / 5) * self.spawn_rate
        if now - self.last_spawn > interval:
            self.spawn_bad(spd); self.last_spawn = now
        if now - self.last_coin > 900:
            self.spawn_coin(); self.last_coin = now
        if now - self.last_power > 7200:
            self.spawn_power(); self.last_power = now
        for group in (self.bad, self.slow, self.coins, self.powers):
            group.update(spd, dt)

        for c in pygame.sprite.spritecollide(self.player, self.coins, True):
            self.coins_count += 1; self.coin_score += c.value
        for z in pygame.sprite.spritecollide(self.player, self.slow, True):
            if self.active == "Nitro": self.bonus += 10
            else: self.slow_until = now + (1800 if z.kind == "oil" else 900)
        for p in pygame.sprite.spritecollide(self.player, self.powers, True):
            if p.kind == "Repair":
                self.use_repair()
            elif not self.active:
                self.active, self.active_until = p.kind, now + (4000 if p.kind == "Nitro" else 1000000)
                self.shield_hits = 1 if p.kind == "Shield" else 0
        if self.active == "Nitro" and now > self.active_until:
            self.active = None
        for hit in pygame.sprite.spritecollide(self.player, self.bad, False):
            if self.active == "Nitro":
                hit.kill(); self.bonus += 35
            elif self.active == "Shield" and self.shield_hits:
                hit.kill(); self.shield_hits = 0; self.active = None; self.bonus += 40
            else:
                self.finish(); break

    def draw_play(self):
        screen.blit(self.bg, (0, int(self.bg_y) - H)); screen.blit(self.bg, (0, int(self.bg_y)))
        pygame.draw.rect(screen, (15, 15, 15), (0, 0, ROAD.left, H))
        pygame.draw.rect(screen, (15, 15, 15), (ROAD.right, 0, W - ROAD.right, H))
        for s in self.all:
            screen.blit(s.image, s.rect)
        lines = [f"{self.name or 'Player'}", f"Score: {self.score()}", f"Dist: {int(self.distance)} m", f"Coins: {self.coins_count}"]
        if self.active == "Nitro":
            lines.append(f"Nitro: {(self.active_until - pygame.time.get_ticks()) // 1000 + 1}s")
        elif self.active == "Shield":
            lines.append("Shield: 1 hit")
        for i, text in enumerate(lines):
            screen.blit(label(text, SMALL, BLACK), (8, 8 + i * 18))

    def menu(self):
        screen.fill((18, 21, 26)); center("STREET RACER", 100, BIG)
        center(f"Player: {self.name or 'Player'}", 150)
        return [("play", btn("Play", (95, 210, 210, 44))), ("leader", btn("Leaderboard", (95, 270, 210, 44))),
                ("settings", btn("Settings", (95, 330, 210, 44))), ("quit", btn("Quit", (95, 390, 210, 44)))]

    def settings_screen(self):
        screen.fill((18, 21, 26)); center("SETTINGS", 70, BIG)
        opts = [("sound", f"Sound: {'ON' if self.settings['sound'] else 'OFF'}"),
                ("diff", f"Difficulty: {self.settings['difficulty']}"), ("back", "Back")]
        return [(k, btn(t, (65, 150 + i * 65, 270, 44))) for i, (k, t) in enumerate(opts)]

    def leaderboard(self):
        screen.fill((18, 21, 26)); center("TOP 10", 55, BIG)
        if not self.board:
            center("No scores yet", 140)
        for i, r in enumerate(self.board[:10], 1):
            text = f"{i:>2}. {r['name'][:10]:<10} {r['score']:>5}  {r['distance']}m"
            screen.blit(label(text, SMALL), (45, 95 + i * 32))
        return [("back", btn("Back", (110, 535, 180, 42)))]

    def game_over(self):
        screen.fill((55, 20, 20)); center("GAME OVER", 105, BIG)
        for i, t in enumerate([f"Score: {self.score()}", f"Distance: {int(self.distance)} m", f"Coins: {self.coins_count}"]):
            center(t, 180 + i * 35, MID)
        return [("retry", btn("Retry", (95, 335, 210, 44))), ("menu", btn("Main Menu", (95, 395, 210, 44)))]

    def name_screen(self, events):
        screen.fill((18, 21, 26)); center("ENTER NAME", 130, BIG)
        pygame.draw.rect(screen, DARK, (55, 230, 290, 48), border_radius=10)
        pygame.draw.rect(screen, GRAY, (55, 230, 290, 48), 2, border_radius=10)
        center(self.name or "type here", 254, MID, WHITE if self.name else GRAY)
        center("Enter - continue", 330, FONT, GRAY)
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN:
                    self.state = "menu"
                elif e.key == pygame.K_BACKSPACE:
                    self.name = self.name[:-1]
                elif len(self.name) < 12 and e.unicode.isprintable():
                    self.name += e.unicode

    def click(self, actions, events):
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for action, rect in actions:
                    if rect.collidepoint(e.pos):
                        return action

    def handle_action(self, action):
        if action == "play" or action == "retry": self.start_game()
        elif action == "leader": self.state = "leader"
        elif action == "settings": self.state = "settings"
        elif action in ("back", "menu"): self.state = "menu"
        elif action == "quit": self.running = False
        elif action == "sound":
            self.settings["sound"] = not self.settings["sound"]
            pygame.mixer.music.play(-1) if self.settings["sound"] else pygame.mixer.music.stop()
            save_json(SETTINGS_FILE, self.settings)
        elif action == "diff":
            keys = list(DIFFS); self.settings["difficulty"] = keys[(keys.index(self.settings["difficulty"]) + 1) % len(keys)]
            save_json(SETTINGS_FILE, self.settings)

    def run(self):
        while self.running:
            dt = clock.tick(FPS) / 16.67
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    self.running = False
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    self.state = "menu" if self.state == "play" else self.state
            actions = []
            if self.state == "name": self.name_screen(events)
            elif self.state == "menu": actions = self.menu()
            elif self.state == "settings": actions = self.settings_screen()
            elif self.state == "leader": actions = self.leaderboard()
            elif self.state == "over": actions = self.game_over()
            elif self.state == "play": self.update_play(dt); self.draw_play()
            action = self.click(actions, events)
            if action: self.handle_action(action)
            pygame.display.flip()
        pygame.quit(); sys.exit()


if __name__ == "__main__":
    Game().run()
