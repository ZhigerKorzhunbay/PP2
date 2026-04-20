import pygame
import sys

pygame.init()

# Размеры окна
W, H = 800, 600
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Simple Painter")

# Цвета
BG_COLOR = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (200, 200, 200)

# Инструменты
color_list = [BLACK, RED, GREEN, BLUE]
current_color = BLACK
tools = ['brush', 'rect', 'circle', 'eraser']
current_tool = 'brush'
brush_radius = 5
eraser_radius = 20

# Холст (на нём сохраняется рисунок)
canvas = pygame.Surface((W, H))
canvas.fill(BG_COLOR)

# Шрифт для интерфейса
font = pygame.font.SysFont("Arial", 16)

# Переменные для рисования фигур
is_drawing = False
start_point = (0, 0)

def draw_interface():
    """Рисует верхнюю панель с кнопками"""
    pygame.draw.rect(screen, GRAY, (0, 0, W, 60))
    
    # Кнопки цветов
    for i, col in enumerate(color_list):
        btn_rect = pygame.Rect(10 + i * 45, 10, 40, 40)
        pygame.draw.rect(screen, col, btn_rect)
        if col == current_color and current_tool != 'eraser':
            pygame.draw.rect(screen, BG_COLOR, btn_rect, 3)
            pygame.draw.rect(screen, BLACK, btn_rect, 1)
    
    # Кнопки инструментов
    tool_items = [
        ("Brush", 200, 'brush'),
        ("Rect", 270, 'rect'),
        ("Circle", 330, 'circle'),
        ("Eraser", 400, 'eraser')
    ]
    
    for txt, x, tool_name in tool_items:
        col = RED if current_tool == tool_name else BLACK
        label = font.render(txt, True, col)
        screen.blit(label, (x, 22))

# Главный цикл
running = True
while running:
    screen.blit(canvas, (0, 0))
    mouse_x, mouse_y = pygame.mouse.get_pos()
    
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False
        
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if mouse_y < 60:  # Клик по панели
                # Выбор цвета
                for i, col in enumerate(color_list):
                    if 10 + i * 45 <= mouse_x <= 50 + i * 45:
                        current_color = col
                        if current_tool == 'eraser':
                            current_tool = 'brush'
                
                # Выбор инструмента
                if 190 <= mouse_x <= 250:
                    current_tool = 'brush'
                elif 260 <= mouse_x <= 310:
                    current_tool = 'rect'
                elif 320 <= mouse_x <= 380:
                    current_tool = 'circle'
                elif 390 <= mouse_x <= 460:
                    current_tool = 'eraser'
            else:
                # Начинаем рисовать фигуру
                is_drawing = True
                start_point = (mouse_x, mouse_y)
        
        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1 and is_drawing:
            is_drawing = False
            end_x, end_y = mouse_x, mouse_y
            sx, sy = start_point
            
            if current_tool == 'rect':
                rect = pygame.Rect(sx, sy, end_x - sx, end_y - sy)
                rect.normalize()
                pygame.draw.rect(canvas, current_color, rect, 2)
            
            elif current_tool == 'circle':
                radius = int(((end_x - sx)**2 + (end_y - sy)**2)**0.5)
                pygame.draw.circle(canvas, current_color, start_point, radius, 2)
        
        elif ev.type == pygame.MOUSEMOTION and is_drawing:
            if current_tool == 'brush':
                pygame.draw.circle(canvas, current_color, ev.pos, brush_radius)
            elif current_tool == 'eraser':
                pygame.draw.circle(canvas, BG_COLOR, ev.pos, eraser_radius)
    
    # Показываем предпросмотр фигуры (не сохраняем на холст)
    if is_drawing and mouse_y >= 60:
        if current_tool == 'rect':
            preview_rect = pygame.Rect(start_point[0], start_point[1],
                                        mouse_x - start_point[0], mouse_y - start_point[1])
            preview_rect.normalize()
            pygame.draw.rect(screen, current_color, preview_rect, 2)
        elif current_tool == 'circle':
            r = int(((mouse_x - start_point[0])**2 + (mouse_y - start_point[1])**2)**0.5)
            pygame.draw.circle(screen, current_color, start_point, r, 2)
    
    draw_interface()
    pygame.display.flip()

pygame.quit()
sys.exit()