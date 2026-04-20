import pygame
import random
import time
from pygame.locals import *

pygame.init()

# Настройки экрана
WIDTH, HEIGHT = 400, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Street Racer")
clock = pygame.time.Clock()
FPS = 60

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# Переменные игры
speed = 5
enemies_passed = 0
coins_collected = 0

# Шрифты
font_main = pygame.font.SysFont("Verdana", 60)
font_small = pygame.font.SysFont("Verdana", 20)

# Фон и звуки
background_img = pygame.image.load("AnimatedStreet.png")
pygame.mixer.music.load('background.wav')
pygame.mixer.music.play(-1)

# Текст "Game Over"
game_over_text = font_main.render("Game Over", True, BLACK)

class Car(pygame.sprite.Sprite):
    def __init__(self, image_path, x, y):
        super().__init__()
        self.image = pygame.image.load(image_path)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
    
    def move_left(self):
        if self.rect.left > 0:
            self.rect.move_ip(-5, 0)
    
    def move_right(self):
        if self.rect.right < WIDTH:
            self.rect.move_ip(5, 0)

class EnemyCar(Car):
    def __init__(self):
        super().__init__("Enemy.png", random.randint(40, WIDTH - 40), 0)
    
    def update(self):
        global enemies_passed
        self.rect.move_ip(0, speed)
        if self.rect.top > HEIGHT:
            enemies_passed += 1
            self.reset()
    
    def reset(self):
        self.rect.top = 0
        self.rect.center = (random.randint(40, WIDTH - 40), 0)

class Coin(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        raw_img = pygame.image.load("coin.png").convert_alpha()
        self.image = pygame.transform.scale(raw_img, (35, 35))
        self.rect = self.image.get_rect()
        self.reset()
    
    def update(self):
        self.rect.move_ip(0, speed)
        if self.rect.top > HEIGHT:
            self.reset()
    
    def reset(self):
        self.rect.top = 0
        self.rect.center = (random.randint(40, WIDTH - 40), 0)

# Создание объектов
player = Car("Player.png", 160, 520)
enemy = EnemyCar()
coin = Coin()

# Группы спрайтов
all_sprites = pygame.sprite.Group()
all_sprites.add(player, enemy, coin)

enemies_group = pygame.sprite.Group()
enemies_group.add(enemy)

coins_group = pygame.sprite.Group()
coins_group.add(coin)

# Таймер для увеличения сложности
SPEED_UP_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(SPEED_UP_EVENT, 1000)

# Главный игровой цикл
running = True
while running:
    for event in pygame.event.get():
        if event.type == SPEED_UP_EVENT:
            speed += 0.5
        if event.type == QUIT:
            running = False
    
    # Управление
    keys = pygame.key.get_pressed()
    if keys[K_LEFT]:
        player.move_left()
    if keys[K_RIGHT]:
        player.move_right()
    
    # Отрисовка фона
    screen.blit(background_img, (0, 0))
    
    # Отображение статистики
    enemy_counter = font_small.render("Enemies: " + str(enemies_passed), True, BLACK)
    coin_counter = font_small.render("Coins: " + str(coins_collected), True, BLACK)
    screen.blit(enemy_counter, (10, 10))
    screen.blit(coin_counter, (WIDTH - 100, 10))
    
    # Движение и отрисовка всех объектов
    for sprite in all_sprites:
        screen.blit(sprite.image, sprite.rect)
        if hasattr(sprite, 'update'):
            sprite.update()
    
    # Сбор монет
    if pygame.sprite.spritecollideany(player, coins_group):
        coins_collected += 1
        coin.reset()
    
    # Столкновение с врагом
    if pygame.sprite.spritecollideany(player, enemies_group):
        pygame.mixer.music.stop()
        crash_sound = pygame.mixer.Sound('crash.wav')
        crash_sound.play()
        time.sleep(0.5)
        
        screen.fill(RED)
        screen.blit(game_over_text, (30, 250))
        pygame.display.update()
        time.sleep(2)
        running = False
    
    pygame.display.update()
    clock.tick(FPS)

pygame.quit()