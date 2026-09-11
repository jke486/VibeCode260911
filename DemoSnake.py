import random
import sys

import pygame


# ===== 기본 설정 =====
COLS = 10
ROWS = 20
BLOCK_SIZE = 30
PREVIEW_BLOCK_SIZE = 24

WINDOW_WIDTH = COLS * BLOCK_SIZE + 260
WINDOW_HEIGHT = ROWS * BLOCK_SIZE

BOARD_X = 20
BOARD_Y = 20

# 색상
BLACK = (10, 10, 15)
BOARD_BG = (11, 17, 32)
PANEL_BG = (17, 24, 39)
TEXT = (229, 231, 235)
MUTED = (148, 163, 184)
ACCENT = (56, 189, 248)
BUTTON = (37, 99, 235)
BUTTON_HOVER = (29, 78, 216)
BORDER = (148, 163, 184)

SHAPES = {
    "I": {"color": (56, 189, 248), "matrix": [[1, 1, 1, 1]]},
    "O": {"color": (250, 204, 21), "matrix": [[1, 1], [1, 1]]},
    "T": {"color": (192, 132, 252), "matrix": [[0, 1, 0], [1, 1, 1]]},
    "S": {"color": (34, 197, 94), "matrix": [[0, 1, 1], [1, 1, 0]]},
    "Z": {"color": (248, 113, 113), "matrix": [[1, 1, 0], [0, 1, 1]]},
    "J": {"color": (96, 165, 250), "matrix": [[1, 0, 0], [1, 1, 1]]},
    "L": {"color": (251, 146, 60), "matrix": [[0, 0, 1], [1, 1, 1]]},
}

LINE_SCORES = [0, 100, 300, 500, 800]


# ===== 게임 상태 =====
class GameState:
    def __init__(self):
        self.board = self.create_board()
        self.current_piece = None
        self.next_piece = None
        self.score = 0
        self.lines = 0
        self.level = 1
        self.selected_level = 1
        self.drop_interval = self.get_drop_interval(self.level)
        self.game_over = False
        self.paused = False
        self.running = True
        self.drop_accumulator = 0
        self.last_time = 0

    @staticmethod
    def create_board():
        return [[None for _ in range(COLS)] for _ in range(ROWS)]

    @staticmethod
    def get_drop_interval(level):
        return max(120, 800 - (level - 1) * 60)


state = GameState()


# ===== 유틸 함수 =====

def clone_matrix(matrix):
    return [row[:] for row in matrix]


def random_type():
    return random.choice(list(SHAPES.keys()))


def create_piece(piece_type):
    matrix = clone_matrix(SHAPES[piece_type]["matrix"])
    return {
        "type": piece_type,
        "matrix": matrix,
        "x": (COLS - len(matrix[0])) // 2,
        "y": -1,
        "color": SHAPES[piece_type]["color"],
    }


def collides(piece, offset_x=0, offset_y=0, matrix=None):
    if matrix is None:
        matrix = piece["matrix"]

    for y, row in enumerate(matrix):
        for x, value in enumerate(row):
            if not value:
                continue

            new_x = piece["x"] + x + offset_x
            new_y = piece["y"] + y + offset_y

            if new_x < 0 or new_x >= COLS or new_y >= ROWS:
                return True

            if new_y >= 0 and state.board[new_y][new_x] is not None:
                return True

    return False


def rotate_matrix(matrix):
    return [list(row) for row in zip(*matrix[::-1])]


def spawn_piece():
    state.current_piece = state.next_piece or create_piece(random_type())
    state.current_piece["x"] = (COLS - len(state.current_piece["matrix"][0])) // 2
    state.current_piece["y"] = -1

    state.next_piece = create_piece(random_type())

    if collides(state.current_piece):
        state.game_over = True
        state.running = False


def merge_piece():
    piece = state.current_piece

    for y, row in enumerate(piece["matrix"]):
        for x, value in enumerate(row):
            if not value:
                continue

            board_y = piece["y"] + y
            board_x = piece["x"] + x

            if board_y >= 0:
                state.board[board_y][board_x] = piece["color"]

    clear_lines()
    spawn_piece()
    update_hud()


def clear_lines():
    cleared = 0

    y = ROWS - 1
    while y >= 0:
        if all(cell is not None for cell in state.board[y]):
            del state.board[y]
            state.board.insert(0, [None for _ in range(COLS)])
            cleared += 1
            continue
        y -= 1

    if cleared > 0:
        state.lines += cleared
        state.score += LINE_SCORES[cleared] * state.level
        state.level = state.selected_level + (state.lines // 10)
        state.drop_interval = state.get_drop_interval(state.level)


def move_piece(dx, dy):
    if state.current_piece is None or state.paused or state.game_over:
        return False

    candidate = {
        "type": state.current_piece["type"],
        "matrix": state.current_piece["matrix"],
        "x": state.current_piece["x"] + dx,
        "y": state.current_piece["y"] + dy,
        "color": state.current_piece["color"],
    }

    if not collides(candidate):
        state.current_piece = candidate
        return True

    return False


def try_rotate():
    if state.current_piece is None or state.paused or state.game_over:
        return

    rotated = rotate_matrix(state.current_piece["matrix"])
    kicks = [0, -1, 1, -2, 2]

    for kick in kicks:
        candidate = {
            "type": state.current_piece["type"],
            "matrix": rotated,
            "x": state.current_piece["x"] + kick,
            "y": state.current_piece["y"],
            "color": state.current_piece["color"],
        }

        if not collides(candidate):
            state.current_piece = candidate
            return


def hard_drop():
    if state.current_piece is None or state.paused or state.game_over:
        return

    distance = 0
    while not collides(state.current_piece, 0, 1):
        state.current_piece["y"] += 1
        distance += 1

    state.score += distance * 2
    merge_piece()
    update_hud()


def soft_drop():
    if state.current_piece is None or state.paused or state.game_over:
        return

    if move_piece(0, 1):
        state.score += 1
    else:
        merge_piece()

    update_hud()


def reset_game():
    state.board = state.create_board()
    state.score = 0
    state.lines = 0
    state.level = state.selected_level
    state.drop_interval = state.get_drop_interval(state.level)
    state.game_over = False
    state.paused = False
    state.running = True
    state.drop_accumulator = 0
    state.last_time = 0

    state.next_piece = create_piece(random_type())
    spawn_piece()
    update_hud()


def toggle_pause():
    if state.game_over:
        return

    state.paused = not state.paused


def update_hud():
    pass


# ===== 렌더링 =====

def draw_cell(surface, x, y, color, size):
    rect = pygame.Rect(BOARD_X + x * size, BOARD_Y + y * size, size, size)
    pygame.draw.rect(surface, color, rect)
    pygame.draw.rect(surface, (255, 255, 255, 50), rect, 1)


def draw_board(surface):
    pygame.draw.rect(surface, BOARD_BG, (BOARD_X, BOARD_Y, COLS * BLOCK_SIZE, ROWS * BLOCK_SIZE))
    pygame.draw.rect(surface, (255, 255, 255, 40), (BOARD_X, BOARD_Y, COLS * BLOCK_SIZE, ROWS * BLOCK_SIZE), 1)

    for y in range(ROWS):
        for x in range(COLS):
            cell = state.board[y][x]
            if cell is not None:
                draw_cell(surface, x, y, cell, BLOCK_SIZE)

    if state.current_piece is not None:
        for y, row in enumerate(state.current_piece["matrix"]):
            for x, value in enumerate(row):
                if value:
                    draw_y = state.current_piece["y"] + y
                    draw_x = state.current_piece["x"] + x
                    if draw_y >= 0:
                        draw_cell(surface, draw_x, draw_y, state.current_piece["color"], BLOCK_SIZE)

    if state.game_over:
        overlay = pygame.Surface((COLS * BLOCK_SIZE, ROWS * BLOCK_SIZE), pygame.SRCALPHA)
        overlay.fill((2, 6, 23, 180))
        surface.blit(overlay, (BOARD_X, BOARD_Y))

        font = pygame.font.SysFont(None, 42, bold=True)
        text = font.render("Game Over", True, TEXT)
        text_rect = text.get_rect(center=(BOARD_X + (COLS * BLOCK_SIZE) / 2, BOARD_Y + ROWS * BLOCK_SIZE / 2 - 10))
        surface.blit(text, text_rect)

        small_font = pygame.font.SysFont(None, 24)
        small_text = small_font.render("R or 1~9 to restart", True, TEXT)
        small_rect = small_text.get_rect(center=(BOARD_X + (COLS * BLOCK_SIZE) / 2, BOARD_Y + ROWS * BLOCK_SIZE / 2 + 24))
        surface.blit(small_text, small_rect)


def draw_next_piece(surface):
    preview_rect = pygame.Rect(BOARD_X + COLS * BLOCK_SIZE + 30, BOARD_Y + 110, 150, 150)
    pygame.draw.rect(surface, PANEL_BG, preview_rect)
    pygame.draw.rect(surface, BORDER, preview_rect, 1)

    if state.next_piece is None:
        return

    matrix = state.next_piece["matrix"]
    offset_x = (4 - len(matrix[0])) // 2
    offset_y = (4 - len(matrix)) // 2

    for y, row in enumerate(matrix):
        for x, value in enumerate(row):
            if value:
                draw_rect_x = preview_rect.x + (offset_x + x) * PREVIEW_BLOCK_SIZE
                draw_rect_y = preview_rect.y + (offset_y + y) * PREVIEW_BLOCK_SIZE
                pygame.draw.rect(surface, state.next_piece["color"], (draw_rect_x, draw_rect_y, PREVIEW_BLOCK_SIZE, PREVIEW_BLOCK_SIZE))
                pygame.draw.rect(surface, (255, 255, 255, 70), (draw_rect_x, draw_rect_y, PREVIEW_BLOCK_SIZE, PREVIEW_BLOCK_SIZE), 1)



def draw_side_panel(surface):
    panel_x = BOARD_X + COLS * BLOCK_SIZE + 30
    panel_y = BOARD_Y

    pygame.draw.rect(surface, PANEL_BG, (panel_x, panel_y, 180, 560))
    pygame.draw.rect(surface, BORDER, (panel_x, panel_y, 180, 560), 1)

    title_font = pygame.font.SysFont(None, 42, bold=True)
    title = title_font.render("Tetris", True, TEXT)
    surface.blit(title, (panel_x + 20, panel_y + 15))

    # 스탯 박스
    stats = [
        ("Score", str(state.score), panel_x + 18, panel_y + 90),
        ("Lines", str(state.lines), panel_x + 18, panel_y + 150),
        ("Level", str(state.level), panel_x + 18, panel_y + 210),
    ]

    for label, value, x, y in stats:
        box = pygame.Rect(x, y, 140, 45)
        pygame.draw.rect(surface, (31, 41, 55), box)
        pygame.draw.rect(surface, BORDER, box, 1)

        font = pygame.font.SysFont(None, 24)
        label_surf = font.render(label, True, MUTED)
        value_surf = font.render(value, True, TEXT)
        surface.blit(label_surf, (x + 12, y + 8))
        surface.blit(value_surf, (x + 98, y + 8))

    # 컨트롤 안내
    controls_y = panel_y + 285
    control_font = pygame.font.SysFont(None, 22)
    help_lines = [
        "Left / Right : Move",
        "Up : Rotate",
        "Down : Soft Drop",
        "Space : Hard Drop",
        "P : Pause",
        "R : Restart",
        "1~9 : Level",
    ]

    for idx, line in enumerate(help_lines):
        text = control_font.render(line, True, TEXT)
        surface.blit(text, (panel_x + 18, controls_y + idx * 24))

    draw_next_piece(surface)


def draw(surface):
    surface.fill(BLACK)
    draw_board(surface)
    draw_side_panel(surface)


# ===== 게임 루프 =====

pygame.init()
pygame.display.set_caption("Tetris Python Port")
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 32)


# 초기 설정
state.next_piece = create_piece(random_type())
spawn_piece()
update_hud()


running = True
while running:
    dt = clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9):
                state.selected_level = event.key - pygame.K_0
                state.level = state.selected_level
                state.drop_interval = state.get_drop_interval(state.level)
                reset_game()
                continue

            if event.key == pygame.K_r:
                reset_game()
                continue

            if event.key == pygame.K_p:
                toggle_pause()
                continue

            if state.paused or state.game_over:
                continue

            if event.key == pygame.K_LEFT:
                move_piece(-1, 0)
            elif event.key == pygame.K_RIGHT:
                move_piece(1, 0)
            elif event.key == pygame.K_DOWN:
                soft_drop()
            elif event.key == pygame.K_UP:
                try_rotate()
            elif event.key == pygame.K_SPACE:
                hard_drop()

    if state.running and not state.paused and not state.game_over:
        state.drop_accumulator += dt
        while state.drop_accumulator >= state.drop_interval:
            if not move_piece(0, 1):
                merge_piece()
            state.drop_accumulator -= state.drop_interval

    draw(screen)
    pygame.display.flip()

pygame.quit()
sys.exit()
