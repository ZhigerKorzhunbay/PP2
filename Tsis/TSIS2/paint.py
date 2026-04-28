import math, sys, pygame
from datetime import datetime
from collections import deque

pygame.init()

W, H = 1000, 700
PANEL_H = 95
BG = (255, 255, 255)
BLACK, RED, GREEN, BLUE = (0,0,0), (255,0,0), (0,180,0), (0,0,255)
GRAY, DARK = (210,210,210), (80,80,80)

screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Simple Painter")
canvas = pygame.Surface((W, H))
canvas.fill(BG)

font = pygame.font.SysFont("Arial", 16)
small = pygame.font.SysFont("Arial", 13)

colors = [BLACK, RED, GREEN, BLUE]
current_color = BLACK
tool = "pencil"
sizes = [2, 5, 10]
size_id = 1
thickness = sizes[size_id]

drawing = False
start = (0, 0)
last_pos = None

text_mode = False
text_pos = (0, 0)
text_value = ""

tools = [
    ("Pencil", 10, "pencil"), ("Line", 85, "line"), ("Rect", 145, "rect"),
    ("Circle", 205, "circle"), ("Square", 280, "square"),
    ("RightTri", 365, "right_triangle"), ("EqTri", 465, "equilateral_triangle"),
    ("Rhombus", 545, "rhombus"), ("Fill", 635, "fill"),
    ("Text", 690, "text"), ("Eraser", 745, "eraser")
]


def square_rect(a, b):
    sx, sy = a; ex, ey = b
    side = min(abs(ex - sx), abs(ey - sy))
    return pygame.Rect(sx if ex >= sx else sx - side,
                       sy if ey >= sy else sy - side, side, side)


def right_tri(a, b):
    sx, sy = a; ex, ey = b
    return [(sx, sy), (sx, ey), (ex, ey)]


def eq_tri(a, b):
    sx, sy = a; ex, ey = b
    side = max(5, abs(ex - sx))
    h = side * math.sqrt(3) / 2
    x2 = sx + side if ex >= sx else sx - side
    base_y = ey
    apex_y = base_y - h if ey >= sy else base_y + h
    return [(sx, base_y), (x2, base_y), ((sx + x2) / 2, apex_y)]


def rhombus(a, b):
    sx, sy = a; ex, ey = b
    l, r = min(sx, ex), max(sx, ex)
    t, bot = min(sy, ey), max(sy, ey)
    cx, cy = (l + r) // 2, (t + bot) // 2
    return [(cx, t), (r, cy), (cx, bot), (l, cy)]


def draw_shape(surface, name, a, b, color, width):
    if name == "line":
        pygame.draw.line(surface, color, a, b, width)

    elif name == "rect":
        rect = pygame.Rect(a[0], a[1], b[0] - a[0], b[1] - a[1])
        rect.normalize()
        pygame.draw.rect(surface, color, rect, width)

    elif name == "circle":
        radius = int(math.dist(a, b))
        if radius > 0:
            pygame.draw.circle(surface, color, a, radius, width)

    elif name == "square":
        pygame.draw.rect(surface, color, square_rect(a, b), width)

    elif name == "right_triangle":
        pygame.draw.polygon(surface, color, right_tri(a, b), width)

    elif name == "equilateral_triangle":
        pygame.draw.polygon(surface, color, eq_tri(a, b), width)

    elif name == "rhombus":
        pygame.draw.polygon(surface, color, rhombus(a, b), width)


def flood_fill(surface, pos, new_color):
    if pos[1] < PANEL_H:
        return

    target = surface.get_at(pos)[:3]
    if target == new_color:
        return

    q = deque([pos])
    while q:
        x, y = q.popleft()
        if x < 0 or x >= W or y < PANEL_H or y >= H:
            continue
        if surface.get_at((x, y))[:3] != target:
            continue

        surface.set_at((x, y), new_color)
        q.extend([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])


def save_canvas():
    name = "canvas_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
    pygame.image.save(canvas, name)
    print("Saved:", name)


def draw_ui():
    pygame.draw.rect(screen, GRAY, (0, 0, W, PANEL_H))

    for i, c in enumerate(colors):
        rect = pygame.Rect(820 + i * 42, 12, 34, 34)
        pygame.draw.rect(screen, c, rect)
        pygame.draw.rect(screen, BLACK, rect, 1)
        if c == current_color and tool != "eraser":
            pygame.draw.rect(screen, BG, rect, 3)

    for name, x, value in tools:
        color = RED if tool == value else BLACK
        screen.blit(font.render(name, True, color), (x, 18))

    for i, s in enumerate(sizes):
        rect = pygame.Rect(820 + i * 50, 55, 42, 25)
        pygame.draw.rect(screen, BG if i == size_id else (235,235,235), rect)
        pygame.draw.rect(screen, BLACK, rect, 1)
        screen.blit(small.render(str(s), True, BLACK), (rect.x + 15, rect.y + 5))

    help1 = "Keys: 1/2/3 size | Ctrl+S save | Enter confirm text | Esc cancel text"
    help2 = f"Tool: {tool} | Size: {thickness}px"
    screen.blit(small.render(help1, True, DARK), (10, 55))
    screen.blit(small.render(help2, True, DARK), (10, 73))


running = True
while running:
    screen.blit(canvas, (0, 0))
    mx, my = pygame.mouse.get_pos()

    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False

        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                save_canvas()

            elif ev.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                size_id = ev.key - pygame.K_1
                thickness = sizes[size_id]

            elif text_mode:
                if ev.key == pygame.K_RETURN:
                    img = font.render(text_value, True, current_color)
                    canvas.blit(img, text_pos)
                    text_mode = False
                    text_value = ""

                elif ev.key == pygame.K_ESCAPE:
                    text_mode = False
                    text_value = ""

                elif ev.key == pygame.K_BACKSPACE:
                    text_value = text_value[:-1]

                else:
                    text_value += ev.unicode

        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if my < PANEL_H:
                for i, c in enumerate(colors):
                    if pygame.Rect(820 + i * 42, 12, 34, 34).collidepoint(mx, my):
                        current_color = c
                        if tool == "eraser":
                            tool = "pencil"

                for name, x, value in tools:
                    if x <= mx <= x + 75 and 10 <= my <= 45:
                        tool = value

                for i in range(3):
                    if pygame.Rect(820 + i * 50, 55, 42, 25).collidepoint(mx, my):
                        size_id = i
                        thickness = sizes[i]

            else:
                if tool == "fill":
                    flood_fill(canvas, (mx, my), current_color)

                elif tool == "text":
                    text_mode = True
                    text_pos = (mx, my)
                    text_value = ""

                else:
                    drawing = True
                    start = (mx, my)
                    last_pos = (mx, my)

        elif ev.type == pygame.MOUSEMOTION and drawing:
            if tool == "pencil":
                pygame.draw.line(canvas, current_color, last_pos, ev.pos, thickness)
                last_pos = ev.pos

            elif tool == "eraser":
                pygame.draw.line(canvas, BG, last_pos, ev.pos, thickness * 2)
                last_pos = ev.pos

        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1 and drawing:
            drawing = False
            end = (mx, my)
            if tool in {"line", "rect", "circle", "square", "right_triangle", "equilateral_triangle", "rhombus"}:
                draw_shape(canvas, tool, start, end, current_color, thickness)

    if drawing and my >= PANEL_H and tool in {"line", "rect", "circle", "square", "right_triangle", "equilateral_triangle", "rhombus"}:
        draw_shape(screen, tool, start, (mx, my), current_color, thickness)

    if text_mode:
        preview = font.render(text_value + "|", True, current_color)
        screen.blit(preview, text_pos)

    draw_ui()
    pygame.display.flip()

pygame.quit()
sys.exit()