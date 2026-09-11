import random
import sys

import pygame


# ===== 설정 =====
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
GRID_SIZE = 20
GRID_COUNT = SCREEN_WIDTH // GRID_SIZE

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (76, 175, 80)
DARK_GREEN = (46, 125, 50)
RED = (244, 67, 54)
BLUE = (33, 150, 243)
BACKGROUND = (20, 20, 20)


class SnakeGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("MySnake")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 24)

        self.reset()

    def reset(self):
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.snake = [
            [GRID_COUNT // 2, GRID_COUNT // 2],
            [GRID_COUNT // 2 - 1, GRID_COUNT // 2],
            [GRID_COUNT // 2 - 2, GRID_COUNT // 2],
        ]
        self.food = self.spawn_food()
        self.score = 0
        self.game_over = False
        self.pause = False
        self.move_interval = 180
        self.move_timer = 0

    def spawn_food(self):
        while True:
            position = [random.randint(0, GRID_COUNT - 1), random.randint(0, GRID_COUNT - 1)]
            if position not in self.snake:
                return position

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    return False

                if event.key == pygame.K_p:
                    if not self.game_over:
                        self.pause = not self.pause
                    continue

                if event.key == pygame.K_r:
                    self.reset()
                    continue

                if self.game_over:
                    continue

                if event.key == pygame.K_UP and self.direction != (0, 1):
                    self.next_direction = (0, -1)
                elif event.key == pygame.K_DOWN and self.direction != (0, -1):
                    self.next_direction = (0, 1)
                elif event.key == pygame.K_LEFT and self.direction != (1, 0):
                    self.next_direction = (-1, 0)
                elif event.key == pygame.K_RIGHT and self.direction != (-1, 0):
                    self.next_direction = (1, 0)

        return True

    def update(self, dt):
        if self.game_over or self.pause:
            return

        self.move_timer += dt
        if self.move_timer < self.move_interval:
            return

        self.move_timer = 0
        self.direction = self.next_direction
        head_x = self.snake[0][0] + self.direction[0]
        head_y = self.snake[0][1] + self.direction[1]

        new_head = [head_x, head_y]

        # 벽에 부딪히는 경우
        if head_x < 0 or head_x >= GRID_COUNT or head_y < 0 or head_y >= GRID_COUNT:
            self.game_over = True
            return

        # 자기 몸과 부딪히는 경우
        if new_head in self.snake:
            self.game_over = True
            return

        self.snake.insert(0, new_head)

        if new_head == self.food:
            self.score += 1
            self.food = self.spawn_food()
            self.move_interval = max(90, self.move_interval - 3)
        else:
            self.snake.pop()

    def draw_grid(self):
        for x in range(GRID_COUNT):
            for y in range(GRID_COUNT):
                rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                pygame.draw.rect(self.screen, (30, 30, 30), rect, 1)

    def draw_snake(self):
        for index, segment in enumerate(self.snake):
            x, y = segment
            rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            color = DARK_GREEN if index == 0 else GREEN
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (255, 255, 255, 20), rect, 1)

    def draw_food(self):
        x, y = self.food
        rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
        pygame.draw.rect(self.screen, RED, rect)
        pygame.draw.rect(self.screen, (255, 255, 255, 30), rect, 1)

    def draw_ui(self):
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (15, 10))

        help_text = self.small_font.render("P: Pause  R: Restart  Q: Quit", True, WHITE)
        self.screen.blit(help_text, (15, SCREEN_HEIGHT - 30))

        if self.pause:
            pause_text = self.font.render("PAUSE", True, WHITE)
            text_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(pause_text, text_rect)

        if self.game_over:
            game_over_text = self.font.render("Game Over", True, WHITE)
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
            self.screen.blit(game_over_text, text_rect)

            restart_text = self.small_font.render("Press R to restart", True, WHITE)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
            self.screen.blit(restart_text, restart_rect)

    def draw(self):
        self.screen.fill(BACKGROUND)
        self.draw_grid()
        self.draw_food()
        self.draw_snake()
        self.draw_ui()
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60)
            running = self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = SnakeGame()
    game.run()
