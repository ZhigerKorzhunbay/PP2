import math
import sys
import pygame

pygame.init()

# -----------------------------
# Window settings
# -----------------------------
W, H = 900, 650
PANEL_HEIGHT = 70
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Simple Painter")

# -----------------------------
# Colors
# -----------------------------
BG_COLOR = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (200, 200, 200)
DARK_GRAY = (90, 90, 90)

# -----------------------------
# Tool settings
# -----------------------------
color_list = [BLACK, RED, GREEN, BLUE]
current_color = BLACK
current_tool = 'brush'
brush_radius = 5
eraser_radius = 20
line_width = 2

# Drawing surface where finished figures are stored.
canvas = pygame.Surface((W, H))
canvas.fill(BG_COLOR)

font = pygame.font.SysFont("Arial", 16)
small_font = pygame.font.SysFont("Arial", 14)

# State variables used while drawing.
is_drawing = False
start_point = (0, 0)

# Toolbar items required by the task.
tool_items = [
    ("Brush", 200, 'brush'),
    ("Rect", 270, 'rect'),
    ("Circle", 330, 'circle'),
    ("Square", 405, 'square'),
    ("RightTri", 485, 'right_triangle'),
    ("EqTri", 585, 'equilateral_triangle'),
    ("Rhombus", 660, 'rhombus'),
    ("Eraser", 760, 'eraser'),
]


def draw_interface():
    """Draw top toolbar with colors, tools and help text."""
    pygame.draw.rect(screen, GRAY, (0, 0, W, PANEL_HEIGHT))

    # Draw color buttons.
    for i, col in enumerate(color_list):
        btn_rect = pygame.Rect(10 + i * 45, 15, 40, 40)
        pygame.draw.rect(screen, col, btn_rect)
        pygame.draw.rect(screen, BLACK, btn_rect, 1)
        if col == current_color and current_tool != 'eraser':
            pygame.draw.rect(screen, BG_COLOR, btn_rect, 3)
            pygame.draw.rect(screen, BLACK, btn_rect, 1)

    # Draw tool labels.
    for txt, x, tool_name in tool_items:
        col = RED if current_tool == tool_name else BLACK
        label = font.render(txt, True, col)
        screen.blit(label, (x, 25))

    help_text = small_font.render("Task 11 shapes: square, right triangle, equilateral triangle, rhombus", True, DARK_GRAY)
    screen.blit(help_text, (10, 54))


# ---------- shape helper functions ----------
def get_square_rect(start, end):
    """Return a square rect based on mouse drag direction."""
    sx, sy = start
    ex, ey = end
    side = min(abs(ex - sx), abs(ey - sy))
    x = sx if ex >= sx else sx - side
    y = sy if ey >= sy else sy - side
    return pygame.Rect(x, y, side, side)



def get_right_triangle_points(start, end):
    """Return vertices of a right triangle inside the drag area."""
    sx, sy = start
    ex, ey = end
    return [(sx, sy), (sx, ey), (ex, ey)]



def get_equilateral_triangle_points(start, end):
    """Return vertices of an equilateral triangle.

    The side is estimated from drag width, then the third point is computed
    using h = side * sqrt(3) / 2.
    """
    sx, sy = start
    ex, ey = end
    side = max(10, abs(ex - sx))
    height = side * math.sqrt(3) / 2

    # Place the base between start and horizontal drag position.
    x1 = sx
    x2 = sx + side if ex >= sx else sx - side
    base_y = ey

    # Apex direction depends on whether user dragged upward or downward.
    apex_y = base_y - height if ey <= sy else base_y + height
    apex_x = (x1 + x2) / 2
    return [(x1, base_y), (x2, base_y), (apex_x, apex_y)]



def get_rhombus_points(start, end):
    """Return 4 vertices of a rhombus inside the drag area."""
    sx, sy = start
    ex, ey = end
    left = min(sx, ex)
    right = max(sx, ex)
    top = min(sy, ey)
    bottom = max(sy, ey)
    cx = (left + right) // 2
    cy = (top + bottom) // 2
    return [(cx, top), (right, cy), (cx, bottom), (left, cy)]



def draw_shape(surface, tool, start, end, color):
    """Draw the selected geometric shape on the given surface."""
    if tool == 'rect':
        rect = pygame.Rect(start[0], start[1], end[0] - start[0], end[1] - start[1])
        rect.normalize()
        pygame.draw.rect(surface, color, rect, line_width)

    elif tool == 'circle':
        radius = int(((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5)
        pygame.draw.circle(surface, color, start, radius, line_width)

    elif tool == 'square':
        pygame.draw.rect(surface, color, get_square_rect(start, end), line_width)

    elif tool == 'right_triangle':
        pygame.draw.polygon(surface, color, get_right_triangle_points(start, end), line_width)

    elif tool == 'equilateral_triangle':
        pygame.draw.polygon(surface, color, get_equilateral_triangle_points(start, end), line_width)

    elif tool == 'rhombus':
        pygame.draw.polygon(surface, color, get_rhombus_points(start, end), line_width)


running = True
while running:
    screen.blit(canvas, (0, 0))
    mouse_x, mouse_y = pygame.mouse.get_pos()

    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False

        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if mouse_y < PANEL_HEIGHT:
                # Color selection.
                for i, col in enumerate(color_list):
                    if 10 + i * 45 <= mouse_x <= 50 + i * 45 and 15 <= mouse_y <= 55:
                        current_color = col
                        if current_tool == 'eraser':
                            current_tool = 'brush'

                # Tool selection.
                for _, x, tool_name in tool_items:
                    if x <= mouse_x <= x + 70:
                        current_tool = tool_name
                        break
            else:
                # Start free drawing or start figure preview.
                is_drawing = True
                start_point = (mouse_x, mouse_y)

        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1 and is_drawing:
            is_drawing = False
            end_point = (mouse_x, mouse_y)

            # Save finished figure on the canvas.
            if current_tool in {'rect', 'circle', 'square', 'right_triangle', 'equilateral_triangle', 'rhombus'}:
                draw_shape(canvas, current_tool, start_point, end_point, current_color)

        elif ev.type == pygame.MOUSEMOTION and is_drawing:
            # Brush and eraser work continuously while the mouse moves.
            if current_tool == 'brush':
                pygame.draw.circle(canvas, current_color, ev.pos, brush_radius)
            elif current_tool == 'eraser':
                pygame.draw.circle(canvas, BG_COLOR, ev.pos, eraser_radius)

    # Draw live preview for geometric figures.
    if is_drawing and mouse_y >= PANEL_HEIGHT and current_tool in {
        'rect', 'circle', 'square', 'right_triangle', 'equilateral_triangle', 'rhombus'
    }:
        draw_shape(screen, current_tool, start_point, (mouse_x, mouse_y), current_color)

    draw_interface()
    pygame.display.flip()

pygame.quit()
sys.exit()