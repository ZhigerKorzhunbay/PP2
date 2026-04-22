import random
import time
import pygame
from pygame.locals import K_LEFT, K_RIGHT, QUIT

pygame.init()
pygame.mixer.init()

# -----------------------------
# Window and game configuration
# -----------------------------
WIDTH, HEIGHT = 400, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Street Racer")
clock = pygame.time.Clock()
FPS = 60

# -----------------------------
# Colors and fonts
# -----------------------------
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
DARK_GREEN = (0, 120, 0)

font_main = pygame.font.SysFont("Verdana", 60)
font_small = pygame.font.SysFont("Verdana", 20)
font_info = pygame.font.SysFont("Verdana", 16)

# -----------------------------
# Game balance settings
# -----------------------------
BASE_SPEED = 5
PLAYER_MOVE_STEP = 5
COINS_TO_SPEED_UP = 5  # Enemy speed increases every N collected coins
MAX_ENEMY_SPEED = 18

# -----------------------------
# Assets
# -----------------------------
background_img = pygame.image.load("AnimatedStreet.png").convert()
player_img = pygame.image.load("Player.png").convert_alpha()
enemy_img = pygame.image.load("Enemy.png").convert_alpha()
coin_img_raw = pygame.image.load("coin.png").convert_alpha()
crash_sound = pygame.mixer.Sound("crash.wav")

pygame.mixer.music.load("background.wav")
pygame.mixer.music.play(-1)


def get_coin_data():
    """Return random coin parameters.

    Each coin has a different 'weight' (value):
    - Bronze: 1 point
    - Silver: 2 points
    - Gold: 3 points

    Weight is visualized by coin size, so heavier coins are bigger.
    """
    coin_types = [
        {"name": "Bronze", "value": 1, "size": 24},
        {"name": "Silver", "value": 2, "size": 32},
        {"name": "Gold", "value": 3, "size": 40},
    ]
    return random.choice(coin_types)


class Car(pygame.sprite.Sprite):
    """Base class for player and enemy cars."""

    def __init__(self, image_surface, x, y):
        super().__init__()
        self.image = image_surface
        self.rect = self.image.get_rect(center=(x, y))

    def move_left(self):
        """Move car left without leaving the road."""
        if self.rect.left > 0:
            self.rect.move_ip(-PLAYER_MOVE_STEP, 0)

    def move_right(self):
        """Move car right without leaving the road."""
        if self.rect.right < WIDTH:
            self.rect.move_ip(PLAYER_MOVE_STEP, 0)


class EnemyCar(Car):
    """Enemy car that moves downward and respawns at the top."""

    def __init__(self):
        super().__init__(enemy_img, random.randint(40, WIDTH - 40), -100)
        self.speed = BASE_SPEED

    def update(self):
        """Move enemy down. If it leaves screen, respawn it."""
        self.rect.move_ip(0, self.speed)
        if self.rect.top > HEIGHT:
            self.reset()

    def reset(self):
        """Place enemy at random x position above the window."""
        self.rect.top = -random.randint(120, 300)
        self.rect.centerx = random.randint(40, WIDTH - 40)

    def increase_speed(self):
        """Increase enemy speed gradually up to a safe maximum."""
        self.speed = min(self.speed + 1, MAX_ENEMY_SPEED)


class Coin(pygame.sprite.Sprite):
    """Coin with random weight/value and matching size."""

    def __init__(self):
        super().__init__()
        self.value = 1
        self.kind = "Bronze"
        self.image = None
        self.rect = None
        self.fall_speed = BASE_SPEED
        self.reset()

    def update(self):
        """Move coin down. If it leaves the screen, respawn it."""
        self.rect.move_ip(0, self.fall_speed)
        if self.rect.top > HEIGHT:
            self.reset()

    def reset(self):
        """Create a new random coin type and respawn it above the window."""
        data = get_coin_data()
        self.value = data["value"]
        self.kind = data["name"]
        self.image = pygame.transform.smoothscale(coin_img_raw, (data["size"], data["size"]))
        self.rect = self.image.get_rect()
        self.rect.top = -random.randint(60, 220)
        self.rect.centerx = random.randint(40, WIDTH - 40)
        # Coin falls a little slower/faster for visual variation.
        self.fall_speed = BASE_SPEED + random.randint(0, 2)


# -----------------------------
# Create objects and groups
# -----------------------------
player = Car(player_img, WIDTH // 2, 520)
enemy = EnemyCar()
coin = Coin()

all_sprites = pygame.sprite.Group(player, enemy, coin)
enemies_group = pygame.sprite.Group(enemy)
coins_group = pygame.sprite.Group(coin)

# -----------------------------
# Game statistics
# -----------------------------
enemies_passed = 0
coins_collected = 0          # number of collected coins
coin_points = 0              # weighted score based on coin value
last_speedup_at = 0          # remembers when enemy speed was last increased


game_over_text = font_main.render("Game Over", True, BLACK)

running = True
while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False

    # Read keyboard state for smooth movement.
    keys = pygame.key.get_pressed()
    if keys[K_LEFT]:
        player.move_left()
    if keys[K_RIGHT]:
        player.move_right()

    # Update moving objects before drawing.
    enemy.update()
    coin.update()

    # If enemy left the screen, count it as passed.
    if enemy.rect.top > HEIGHT:
        enemies_passed += 1

    # Collision with coin: add weighted score, then respawn the coin.
    collected_coin = pygame.sprite.spritecollideany(player, coins_group)
    if collected_coin:
        coins_collected += 1
        coin_points += collected_coin.value
        collected_coin.reset()

        # Requirement: increase enemy speed when player earns N coins.
        if coins_collected // COINS_TO_SPEED_UP > last_speedup_at:
            enemy.increase_speed()
            last_speedup_at = coins_collected // COINS_TO_SPEED_UP

    # Draw background and all game objects.
    screen.blit(background_img, (0, 0))
    for sprite in all_sprites:
        screen.blit(sprite.image, sprite.rect)

    # Draw game statistics.
    stats = [
        f"Enemies: {enemies_passed}",
        f"Coins: {coins_collected}",
        f"Points: {coin_points}",
        f"Enemy speed: {enemy.speed}",
        f"Next speed up in: {COINS_TO_SPEED_UP - (coins_collected % COINS_TO_SPEED_UP or COINS_TO_SPEED_UP)} coins",
        f"Current coin: {coin.kind} (+{coin.value})",
    ]
    for i, text in enumerate(stats):
        label = font_info.render(text, True, BLACK)
        screen.blit(label, (10, 10 + i * 22))

    # Check collision with enemy car.
    if pygame.sprite.spritecollideany(player, enemies_group):
        pygame.mixer.music.stop()
        crash_sound.play()
        time.sleep(0.4)

        screen.fill(RED)
        screen.blit(game_over_text, (30, 250))
        final_score = font_small.render(f"Weighted points: {coin_points}", True, WHITE)
        final_coins = font_small.render(f"Collected coins: {coins_collected}", True, WHITE)
        screen.blit(final_score, (90, 340))
        screen.blit(final_coins, (100, 375))
        pygame.display.update()
        time.sleep(2)
        running = False

    pygame.display.update()
    clock.tick(FPS)

pygame.quit()
