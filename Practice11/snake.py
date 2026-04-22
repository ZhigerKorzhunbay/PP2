import random
import pygame

pygame.init()

# -----------------------------
# Window and basic settings
# -----------------------------
WIDTH, HEIGHT = 720, 480
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Game")
clock = pygame.time.Clock()

# -----------------------------
# Colors
# -----------------------------
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (180, 0, 255)

# -----------------------------
# Game settings
# -----------------------------
CELL_SIZE = 10
START_SPEED = 15
MAX_SPEED = 30
FOOD_LIFETIME_MS = 7000  # food disappears after 7 seconds

# Snake state
snake_speed = START_SPEED
snake_head = [100, 50]
snake_body = [[100, 50], [90, 50], [80, 50], [70, 50]]
direction = 'RIGHT'
next_direction = 'RIGHT'

# Progress state
score = 0
level = 1
foods_eaten_this_level = 0
foods_required_for_next = 3


def get_free_position():
    """Generate a random grid position not occupied by the snake."""
    while True:
        x = random.randrange(0, WIDTH // CELL_SIZE) * CELL_SIZE
        y = random.randrange(0, HEIGHT // CELL_SIZE) * CELL_SIZE
        if [x, y] not in snake_body:
            return [x, y]


def create_food():
    """Create food with random 'weight' (value) and a timer.

    The requirement says food must have different weights and disappear after time.
    Weight is represented by:
    - value: points awarded
    - color: visual difference
    - lifetime: all food disappears after several seconds
    """
    food_types = [
        {"value": 1, "color": WHITE, "label": "Light"},
        {"value": 2, "color": ORANGE, "label": "Medium"},
        {"value": 3, "color": PURPLE, "label": "Heavy"},
    ]
    food = random.choice(food_types).copy()
    food["pos"] = get_free_position()
    food["spawn_time"] = pygame.time.get_ticks()
    return food


food = create_food()


def level_up():
    """Increase level and snake speed after enough food has been eaten."""
    global level, snake_speed, foods_required_for_next, foods_eaten_this_level

    level += 1
    snake_speed = min(snake_speed + 2, MAX_SPEED)

    if level <= 5:
        foods_required_for_next = 3 + (level - 1)
    else:
        foods_required_for_next = 8

    foods_eaten_this_level = 0
    pygame.display.set_caption(f"Snake Game - Level {level}")


def show_info():
    """Draw score, level, required food and food timer."""
    font = pygame.font.SysFont("Arial", 20)

    score_text = font.render(f"Score: {score}", True, WHITE)
    level_text = font.render(f"Level: {level}", True, YELLOW)
    remaining = foods_required_for_next - foods_eaten_this_level
    need_text = font.render(f"Next level in: {remaining} food", True, BLUE)

    time_left_ms = max(0, FOOD_LIFETIME_MS - (pygame.time.get_ticks() - food["spawn_time"]))
    seconds_left = time_left_ms // 1000 + (1 if time_left_ms % 1000 else 0)
    timer_text = font.render(
        f"Food: {food['label']} (+{food['value']}) | disappears in {seconds_left}s",
        True,
        food["color"],
    )

    window.blit(score_text, (10, 10))
    window.blit(level_text, (WIDTH - 120, 10))
    window.blit(need_text, (WIDTH // 2 - 95, 10))
    window.blit(timer_text, (10, 35))



def game_over_screen():
    """Show game over screen and let player restart or quit."""
    font_big = pygame.font.SysFont("Arial", 50)
    font_small = pygame.font.SysFont("Arial", 30)

    game_over_msg = font_big.render(f"Game Over! Score: {score}", True, RED)
    restart_msg = font_small.render("Press R to restart, Q to quit", True, WHITE)

    window.blit(game_over_msg, (WIDTH // 2 - 200, HEIGHT // 2 - 50))
    window.blit(restart_msg, (WIDTH // 2 - 180, HEIGHT // 2 + 20))
    pygame.display.flip()

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_r:
                    return True
                if ev.key == pygame.K_q:
                    return False
        clock.tick(10)



def reset_game():
    """Reset all game variables to initial state."""
    global snake_head, snake_body, direction, next_direction
    global score, level, snake_speed, foods_eaten_this_level
    global foods_required_for_next, food

    snake_head = [100, 50]
    snake_body = [[100, 50], [90, 50], [80, 50], [70, 50]]
    direction = 'RIGHT'
    next_direction = 'RIGHT'
    score = 0
    level = 1
    snake_speed = START_SPEED
    foods_eaten_this_level = 0
    foods_required_for_next = 3
    food = create_food()
    pygame.display.set_caption("Snake Game")


running = True
while running:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False
        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_UP and direction != 'DOWN':
                next_direction = 'UP'
            if ev.key == pygame.K_DOWN and direction != 'UP':
                next_direction = 'DOWN'
            if ev.key == pygame.K_LEFT and direction != 'RIGHT':
                next_direction = 'LEFT'
            if ev.key == pygame.K_RIGHT and direction != 'LEFT':
                next_direction = 'RIGHT'
            if ev.key == pygame.K_ESCAPE:
                if not game_over_screen():
                    running = False

    direction = next_direction

    # Move snake head one cell in the current direction.
    if direction == 'UP':
        snake_head[1] -= CELL_SIZE
    elif direction == 'DOWN':
        snake_head[1] += CELL_SIZE
    elif direction == 'LEFT':
        snake_head[0] -= CELL_SIZE
    elif direction == 'RIGHT':
        snake_head[0] += CELL_SIZE

    # If food expired, replace it with a new random one.
    if pygame.time.get_ticks() - food["spawn_time"] >= FOOD_LIFETIME_MS:
        food = create_food()

    # If snake eats food, grow it and earn points according to food weight.
    if snake_head == food["pos"]:
        score += 10 * food["value"]
        foods_eaten_this_level += 1
        food = create_food()

        if foods_eaten_this_level >= foods_required_for_next:
            level_up()
    else:
        snake_body.pop()

    snake_body.insert(0, list(snake_head))

    # Collision with walls.
    if (snake_head[0] < 0 or snake_head[0] >= WIDTH or
            snake_head[1] < 0 or snake_head[1] >= HEIGHT):
        if game_over_screen():
            reset_game()
            continue
        running = False

    # Collision with itself.
    for segment in snake_body[1:]:
        if snake_head == segment:
            if game_over_screen():
                reset_game()
                break
            running = False
            break
    if not running:
        break

    # Draw scene.
    window.fill(BLACK)
    for segment in snake_body[1:]:
        pygame.draw.rect(window, GREEN, (segment[0], segment[1], CELL_SIZE, CELL_SIZE))
    pygame.draw.rect(window, YELLOW, (snake_head[0], snake_head[1], CELL_SIZE, CELL_SIZE))
    pygame.draw.rect(window, food["color"], (food["pos"][0], food["pos"][1], CELL_SIZE, CELL_SIZE))

    show_info()
    pygame.display.update()
    clock.tick(snake_speed)

pygame.quit()
