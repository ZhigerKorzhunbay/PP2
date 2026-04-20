import pygame
import random

pygame.init()

# Размеры окна
WIDTH, HEIGHT = 720, 480
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Game")

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Начальные параметры
snake_speed = 15
cell_size = 10
clock = pygame.time.Clock()

# Начальная позиция змейки
snake_head = [100, 50]
snake_body = [[100, 50], [90, 50], [80, 50], [70, 50]]
direction = 'RIGHT'
next_direction = 'RIGHT'

# Очки и уровни
score = 0
level = 1
foods_eaten_this_level = 0
foods_required_for_next = 3
MAX_SPEED = 30

def get_free_position():
    """Генерирует случайную позицию, не занятую змейкой"""
    while True:
        x = random.randrange(0, WIDTH // cell_size) * cell_size
        y = random.randrange(0, HEIGHT // cell_size) * cell_size
        if [x, y] not in snake_body:
            return [x, y]

# Первая еда
food_pos = get_free_position()

def level_up():
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
    """Показывает счёт, уровень и сколько осталось до следующего уровня"""
    font = pygame.font.SysFont("Arial", 20)
    
    score_text = font.render(f"Score: {score}", True, WHITE)
    level_text = font.render(f"Level: {level}", True, YELLOW)
    remaining = foods_required_for_next - foods_eaten_this_level
    need_text = font.render(f"Next: {remaining} food", True, BLUE)
    
    window.blit(score_text, (10, 10))
    window.blit(level_text, (WIDTH - 100, 10))
    window.blit(need_text, (WIDTH // 2 - 60, 10))

def game_over_screen():
    """Экран окончания игры"""
    font_big = pygame.font.SysFont("Arial", 50)
    font_small = pygame.font.SysFont("Arial", 30)
    
    game_over_msg = font_big.render(f"Game Over! Score: {score}", True, RED)
    restart_msg = font_small.render("Press R to restart, Q to quit", True, WHITE)
    
    window.blit(game_over_msg, (WIDTH//2 - 200, HEIGHT//2 - 50))
    window.blit(restart_msg, (WIDTH//2 - 180, HEIGHT//2 + 20))
    pygame.display.flip()
    
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_r:
                    return True
                if ev.key == pygame.K_q:
                    return False
        clock.tick(10)

def reset_game():
    global snake_head, snake_body, direction, next_direction, score, level
    global snake_speed, foods_eaten_this_level, foods_required_for_next, food_pos
    
    snake_head = [100, 50]
    snake_body = [[100, 50], [90, 50], [80, 50], [70, 50]]
    direction = 'RIGHT'
    next_direction = 'RIGHT'
    score = 0
    level = 1
    snake_speed = 15
    foods_eaten_this_level = 0
    foods_required_for_next = 3
    food_pos = get_free_position()
    pygame.display.set_caption("Snake Game")

# Главный игровой цикл
running = True
while running:
    for ev in pygame.event.get():
        if ev.type == pygame.KEYDOWN:
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
    
    # Движение головы
    if direction == 'UP':
        snake_head[1] -= cell_size
    elif direction == 'DOWN':
        snake_head[1] += cell_size
    elif direction == 'LEFT':
        snake_head[0] -= cell_size
    elif direction == 'RIGHT':
        snake_head[0] += cell_size
    
    # Проверка съедания еды
    if snake_head == food_pos:
        score += 10
        foods_eaten_this_level += 1
        food_pos = get_free_position()
        
        if foods_eaten_this_level >= foods_required_for_next:
            level_up()
    else:
        snake_body.pop()
    
    snake_body.insert(0, list(snake_head))
    
    # Проверка столкновений
    # Со стенами
    if (snake_head[0] < 0 or snake_head[0] >= WIDTH or
        snake_head[1] < 0 or snake_head[1] >= HEIGHT):
        if game_over_screen():
            reset_game()
        else:
            running = False
    
    # С самим собой
    for segment in snake_body[1:]:
        if snake_head == segment:
            if game_over_screen():
                reset_game()
            else:
                running = False
    
    # Отрисовка
    window.fill(BLACK)
    for segment in snake_body:
        pygame.draw.rect(window, GREEN, (segment[0], segment[1], cell_size, cell_size))
    pygame.draw.rect(window, YELLOW, (snake_head[0], snake_head[1], cell_size, cell_size))
    pygame.draw.rect(window, WHITE, (food_pos[0], food_pos[1], cell_size, cell_size))
    
    show_info()
    pygame.display.update()
    clock.tick(snake_speed)

pygame.quit()