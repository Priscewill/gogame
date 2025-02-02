import pygame

BOARD_SIZE = 19
CELL_SIZE = 30
MARGIN = 50
WINDOW_SIZE = (BOARD_SIZE - 1) * CELL_SIZE + 2 * MARGIN
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (34, 139, 34)
STONE_RADIUS = CELL_SIZE // 2 - 2
FONT_SIZE = 24
BUTTON_WIDTH = 120
BUTTON_HEIGHT = 40
BUTTON_COLOR = (100, 100, 100)
BUTTON_TEXT_COLOR = (255, 255, 255)

pygame.init()
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE + 100))
pygame.display.set_caption("Go Game")
font = pygame.font.Font(None, FONT_SIZE)
board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
current_player = 1
board_history = []
captures = {1: 0, 2: 0}
last_capture_pos_black = [None, None]
last_capture_pos_white = [None, None]


def draw_board():
    screen.fill(GREEN)
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            x = MARGIN + i * CELL_SIZE
            y = MARGIN + j * CELL_SIZE
            if i == 0 or i == BOARD_SIZE - 1 or j == 0 or j == BOARD_SIZE - 1:
                pygame.draw.circle(screen, BLACK, (x, y), 3)  # Star points
            pygame.draw.line(screen, BLACK, (x, MARGIN), (x, WINDOW_SIZE - MARGIN), 1)
            pygame.draw.line(screen, BLACK, (MARGIN, y), (WINDOW_SIZE - MARGIN, y), 1)


def draw_stones():
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] == 1:
                x = MARGIN + i * CELL_SIZE
                y = MARGIN + j * CELL_SIZE
                pygame.draw.circle(screen, BLACK, (x, y), STONE_RADIUS)
            elif board[i][j] == 2:
                x = MARGIN + i * CELL_SIZE
                y = MARGIN + j * CELL_SIZE
                pygame.draw.circle(screen, WHITE, (x, y), STONE_RADIUS)


def get_board_position(mouse_pos):
    x, y = mouse_pos
    i = (x - MARGIN + CELL_SIZE // 2) // CELL_SIZE
    j = (y - MARGIN + CELL_SIZE // 2) // CELL_SIZE
    if 0 <= i < BOARD_SIZE and 0 <= j < BOARD_SIZE:
        return i, j
    return None


def has_liberties(i, j, visited=None):
    if visited is None:
        visited = set()
    if (i, j) in visited:
        return False
    visited.add((i, j))
    color = board[i][j]
    for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        ni, nj = i + di, j + dj
        if 0 <= ni < BOARD_SIZE and 0 <= nj < BOARD_SIZE:
            if board[ni][nj] == 0:
                return True
            if board[ni][nj] == color and has_liberties(ni, nj, visited):
                return True
    return False


def remove_group(i, j):
    global last_capture_pos_white, last_capture_pos_black
    color = board[i][j]
    stack = [(i, j)]
    while stack:
        ci, cj = stack.pop()
        board[ci][cj] = 0
        if current_player == 1:
            last_capture_pos_black[0] = (ci, cj)
            last_capture_pos_black[1] = last_capture_pos_black[0]
        if current_player == 2:
            last_capture_pos_white[0] = (ci, cj)
            last_capture_pos_white[1] = last_capture_pos_white[0]
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = ci + di, cj + dj
            if 0 <= ni < BOARD_SIZE and 0 <= nj < BOARD_SIZE:
                if board[ni][nj] == color:
                    stack.append((ni, nj))


def capture_stones(i, j):
    captures = 0
    for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        ni, nj = i + di, j + dj
        if 0 <= ni < BOARD_SIZE and 0 <= nj < BOARD_SIZE:
            if board[ni][nj] != 0 and board[ni][nj] != board[i][j]:
                if not has_liberties(ni, nj):
                    remove_group(ni, nj)
                    captures += 1
    return captures


def is_suicide(i, j, color):
    board[i][j] = color
    if not has_liberties(i, j):
        captures = capture_stones(i, j)
        board[i][j] = 0
        if captures == 0:
            return True
    board[i][j] = 0
    return False


def is_ko_violation(i, j):
    global last_capture_pos_black, last_capture_pos_white
    if current_player == 1:
        if last_capture_pos_white[0] == (i, j) and last_capture_pos_white[1] == (i, j):
            return True
    if current_player == 2:
        if last_capture_pos_black[0] == (i, j) and last_capture_pos_black[1] == (i, j):
            return True
    return False


def calculate_territory():
    territory = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    visited = [[False for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    def flood_fill(i, j, color):
        stack = [(i, j)]
        territory[i][j] = color
        visited[i][j] = True
        while stack:
            ci, cj = stack.pop()
            for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ni, nj = ci + di, cj + dj
                if 0 <= ni < BOARD_SIZE and 0 <= nj < BOARD_SIZE:
                    if board[ni][nj] == 0 and not visited[ni][nj]:
                        territory[ni][nj] = color
                        visited[ni][nj] = True
                        stack.append((ni, nj))

    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] == 1:
                flood_fill(i, j, 1)
            elif board[i][j] == 2:
                flood_fill(i, j, 2)

    return territory


def count_points():
    territory = calculate_territory()
    black_score = captures[1]
    white_score = captures[2]
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if territory[i][j] == 1:
                black_score += 1
            elif territory[i][j] == 2:
                white_score += 1
    return black_score, white_score


def draw_scores(black_score, white_score):
    score_text = font.render(f"Black: {black_score}  White: {white_score}", True, BLACK)
    screen.blit(score_text, (MARGIN, WINDOW_SIZE + 10))


def draw_turn_indicator():
    turn_text = font.render(f"Current Turn: {'Black' if current_player == 1 else 'White'}", True, BLACK)
    screen.blit(turn_text, (WINDOW_SIZE - 200, WINDOW_SIZE + 10))


def draw_restart_button():
    button_rect = pygame.Rect(WINDOW_SIZE // 2 - BUTTON_WIDTH // 2, WINDOW_SIZE + 50, BUTTON_WIDTH, BUTTON_HEIGHT)
    pygame.draw.rect(screen, BUTTON_COLOR, button_rect)
    button_text = font.render("Restart", True, BUTTON_TEXT_COLOR)
    text_rect = button_text.get_rect(center=button_rect.center)
    screen.blit(button_text, text_rect)
    return button_rect


def restart_game():
    global board, current_player, board_history, captures, last_capture_pos_black, last_capture_pos_white
    board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    current_player = 1
    board_history = []
    captures = {1: 0, 2: 0}
    last_capture_pos_black, last_capture_pos_white = [None, None], [None, None]


def main():
    global current_player, board_history, captures, last_capture_pos_black, last_capture_pos_white
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                board_pos = get_board_position(pos)
                if board_pos:
                    i, j = board_pos
                    if board[i][j] == 0:
                        if not is_ko_violation(i, j):
                            if not is_suicide(i, j, current_player):
                                board[i][j] = current_player
                                if current_player == 2:
                                    last_capture_pos_black[1] = (i, j)
                                if current_player == 1:
                                    last_capture_pos_white[1] = (i, j)
                                captured = capture_stones(i, j)
                                captures[current_player] += captured
                                board_history.append(tuple(tuple(row) for row in board))
                                current_player = 3 - current_player
                else:
                    button_rect = draw_restart_button()
                    if button_rect.collidepoint(pos):
                        restart_game()

        draw_board()
        draw_stones()
        black_score, white_score = count_points()
        draw_scores(black_score, white_score)
        draw_turn_indicator()
        draw_restart_button()
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
