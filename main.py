import pygame

BOARD_SIZES = [9, 13, 19]
CELL_SIZE = 30
MARGIN = 50
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (34, 139, 34)
STONE_RADIUS = CELL_SIZE // 2 - 2
FONT_SIZE = 24
BUTTON_WIDTH = 200
BUTTON_HEIGHT = 50
BUTTON_COLOR = (100, 100, 100)
BUTTON_TEXT_COLOR = (255, 255, 255)
MENU_COLOR = (200, 200, 200)
HOVER_COLOR = (150, 150, 150)
RULES_TEXT = [
    "Правила игры Го:",
    "1. Игроки по очереди ставят камни на доску.",
    "2. Камни захватываются, если у них нет свободных точек.",
    "3. Самоубийственные ходы (постановка камня без свободных точек) запрещены.",
    "4. Правило Ко запрещает повторение предыдущего состояния доски.",
    "5. Игрок с наибольшим количеством территории и захватов побеждает."
]

pygame.init()
screen = pygame.display.set_mode((800, 800))
pygame.display.set_caption("Го")
font = pygame.font.Font(None, FONT_SIZE)

game_started = False
board_size = 19
board = [[0 for _ in range(board_size)] for _ in range(board_size)]
current_player = 1
board_history = [[[0 for _ in range(board_size)] for _ in range(board_size)]]
captures = {1: 0, 2: 0}
last_capture_pos_black = [None, None]
last_capture_pos_white = [None, None]
show_rules = False
initial_advantage = 5.5


def draw_board():
    window_size = (board_size - 1) * CELL_SIZE + 2 * MARGIN
    screen.fill(GREEN)
    for i in range(board_size):
        for j in range(board_size):
            x = MARGIN + i * CELL_SIZE
            y = MARGIN + j * CELL_SIZE
            if i == 0 or i == board_size - 1 or j == 0 or j == board_size - 1:
                pygame.draw.circle(screen, BLACK, (x, y), 3)
            pygame.draw.line(screen, BLACK, (x, MARGIN), (x, window_size - MARGIN), 1)
            pygame.draw.line(screen, BLACK, (MARGIN, y), (window_size - MARGIN, y), 1)


def draw_stones():
    for i in range(board_size):
        for j in range(board_size):
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
    if 0 <= i < board_size and 0 <= j < board_size:
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
        if 0 <= ni < board_size and 0 <= nj < board_size:
            if board[ni][nj] == 0:
                return True
            if board[ni][nj] == color and has_liberties(ni, nj, visited):
                return True
    return False


def remove_group(i, j):
    global last_capture_pos_black, last_capture_pos_white
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
            if 0 <= ni < board_size and 0 <= nj < board_size:
                if board[ni][nj] == color:
                    stack.append((ni, nj))


def capture_stones(i, j):
    captures = 0
    for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        ni, nj = i + di, j + dj
        if 0 <= ni < board_size and 0 <= nj < board_size:
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
    territory = [[0 for _ in range(board_size)] for _ in range(board_size)]
    visited = [[False for _ in range(board_size)] for _ in range(board_size)]

    def flood_fill(i, j, color):
        stack = [(i, j)]
        territory[i][j] = color
        visited[i][j] = True
        while stack:
            ci, cj = stack.pop()
            for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ni, nj = ci + di, cj + dj
                if 0 <= ni < board_size and 0 <= nj < board_size:
                    if board[ni][nj] == 0 and not visited[ni][nj]:
                        territory[ni][nj] = color
                        visited[ni][nj] = True
                        stack.append((ni, nj))

    for i in range(board_size):
        for j in range(board_size):
            if board[i][j] == 1:
                flood_fill(i, j, 1)
            elif board[i][j] == 2:
                flood_fill(i, j, 2)

    return territory


def count_points():
    territory = calculate_territory()
    black_territory = 0
    white_territory = 0
    dead_black_stones = 0
    dead_white_stones = 0

    for i in range(board_size):
        for j in range(board_size):
            if territory[i][j] == 1:
                black_territory += 1
            elif territory[i][j] == 2:
                white_territory += 1
            elif board[i][j] == 1:
                dead_black_stones += 1
            elif board[i][j] == 2:
                dead_white_stones += 1

    black_score = black_territory - captures[2] - dead_black_stones
    white_score = initial_advantage + white_territory - captures[1] - dead_white_stones

    return black_score, white_score


def draw_scores(black_score, white_score):
    score_text = font.render(f"Черные: {black_score}  Белые: {white_score}", True, BLACK)
    screen.blit(score_text, (MARGIN, (board_size - 1) * CELL_SIZE + 2 * MARGIN + 10))


def draw_turn_indicator():
    turn_text = font.render(f"Сейчас ход: {'Черные' if current_player == 1 else 'Белые'}", True, BLACK)
    screen.blit(turn_text,
                ((board_size - 1) * CELL_SIZE + 2 * MARGIN - 200, (board_size - 1) * CELL_SIZE + 2 * MARGIN + 10))


def draw_restart_button():
    button_rect = pygame.Rect(50, 740, BUTTON_WIDTH, BUTTON_HEIGHT)
    pygame.draw.rect(screen, BUTTON_COLOR, button_rect)
    button_text = font.render("Рестарт", True, BUTTON_TEXT_COLOR)
    text_rect = button_text.get_rect(center=button_rect.center)
    screen.blit(button_text, text_rect)
    return button_rect


def draw_end_game_button():
    button_rect = pygame.Rect(300, 740, BUTTON_WIDTH, BUTTON_HEIGHT)
    pygame.draw.rect(screen, BUTTON_COLOR, button_rect)
    button_text = font.render("Закончить игру", True, BUTTON_TEXT_COLOR)
    text_rect = button_text.get_rect(center=button_rect.center)
    screen.blit(button_text, text_rect)
    return button_rect


def draw_to_main_menu_button():
    button_rect = pygame.Rect(550, 740, BUTTON_WIDTH, BUTTON_HEIGHT)
    pygame.draw.rect(screen, BUTTON_COLOR, button_rect)
    button_text = font.render("В главное меню", True, BUTTON_TEXT_COLOR)
    text_rect = button_text.get_rect(center=button_rect.center)
    screen.blit(button_text, text_rect)
    return button_rect


def draw_back_button():
    button_rect = pygame.Rect(550, 680, BUTTON_WIDTH, BUTTON_HEIGHT)
    pygame.draw.rect(screen, BUTTON_COLOR, button_rect)
    button_text = font.render("Назад", True, BUTTON_TEXT_COLOR)
    text_rect = button_text.get_rect(center=button_rect.center)
    screen.blit(button_text, text_rect)
    return button_rect


def restart_game():
    global board, current_player, board_history, captures, last_capture_pos_black, last_capture_pos_white
    board = [[0 for _ in range(board_size)] for _ in range(board_size)]
    current_player = 1
    board_history = [[[0 for _ in range(board_size)] for _ in range(board_size)]]
    captures = {1: 0, 2: 0}
    last_capture_pos_black, last_capture_pos_white = [None, None], [None, None]


def draw_main_menu():
    screen.fill(MENU_COLOR)
    title_font = pygame.font.Font(None, 48)
    title_text = title_font.render("Го", True, BLACK)
    title_rect = title_text.get_rect(center=(400, 100))
    screen.blit(title_text, title_rect)

    size_buttons = []
    for i, size in enumerate(BOARD_SIZES):
        button_rect = pygame.Rect(300, 200 + i * 70, 200, 50)
        pygame.draw.rect(screen, BUTTON_COLOR, button_rect)
        button_text = font.render(f"{size}x{size}", True, BUTTON_TEXT_COLOR)
        text_rect = button_text.get_rect(center=button_rect.center)
        screen.blit(button_text, text_rect)
        size_buttons.append(button_rect)

    rules_button = pygame.Rect(300, 500, 200, 50)
    pygame.draw.rect(screen, BUTTON_COLOR, rules_button)
    rules_text = font.render("Правила", True, BUTTON_TEXT_COLOR)
    rules_text_rect = rules_text.get_rect(center=rules_button.center)
    screen.blit(rules_text, rules_text_rect)

    return size_buttons, rules_button


def draw_rules():
    screen.fill(MENU_COLOR)
    rules_font = pygame.font.Font(None, 24)
    for i, line in enumerate(RULES_TEXT):
        rules_line = rules_font.render(line, True, BLACK)
        rules_rect = rules_line.get_rect(center=(400, 50 + i * 30))
        screen.blit(rules_line, rules_rect)

    back_button = pygame.Rect(300, 500, 200, 50)
    pygame.draw.rect(screen, BUTTON_COLOR, back_button)
    back_text = font.render("Назад", True, BUTTON_TEXT_COLOR)
    back_text_rect = back_text.get_rect(center=back_button.center)
    screen.blit(back_text, back_text_rect)

    return back_button


def draw_rules_button():
    button_rect = pygame.Rect(50, 680, BUTTON_WIDTH, BUTTON_HEIGHT)
    pygame.draw.rect(screen, BUTTON_COLOR, button_rect)
    button_text = font.render("Правила", True, BUTTON_TEXT_COLOR)
    text_rect = button_text.get_rect(center=button_rect.center)
    screen.blit(button_text, text_rect)
    return button_rect


def main():
    global game_started, current_player, board_history, captures, last_capture_pos_black, last_capture_pos_white, board_size, show_rules, initial_advantage, board
    running = True
    game_ended = False
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if not game_started:
                    if show_rules:
                        back_button = draw_rules()
                        if back_button.collidepoint(pos):
                            show_rules = False
                    else:
                        size_buttons, rules_button = draw_main_menu()
                        for i, button in enumerate(size_buttons):
                            if button.collidepoint(pos):
                                board_size = BOARD_SIZES[i]
                                game_started = True
                                restart_game()
                        if rules_button.collidepoint(pos):
                            show_rules = True
                else:
                    if show_rules:
                        back_button = draw_rules()
                        if back_button.collidepoint(pos):
                            show_rules = False
                    else:
                        if game_ended:
                            to_main_menu_button = draw_to_main_menu_button()
                            if to_main_menu_button.collidepoint(pos):
                                game_started = False
                                game_ended = False
                                restart_game()
                        else:
                            board_pos = get_board_position(pos)
                            if board_pos:
                                i, j = board_pos
                                if board[i][j] == 0:
                                    if not is_ko_violation(i, j):
                                        if not is_suicide(i, j, current_player):

                                            board_history.append(([row.copy() for row in board], captures.copy()))
                                            board[i][j] = current_player
                                            if current_player == 2:
                                                last_capture_pos_black[1] = (i, j)
                                            if current_player == 1:
                                                last_capture_pos_white[1] = (i, j)
                                            captured = capture_stones(i, j)
                                            captures[current_player] += captured
                                            current_player = 3 - current_player
                            else:
                                end_game_button = draw_end_game_button()
                                restart_button = draw_restart_button()
                                to_main_menu_button = draw_to_main_menu_button()
                                back_button = draw_back_button()
                                rules_button = draw_rules_button()
                                if end_game_button.collidepoint(pos):
                                    game_ended = True
                                elif restart_button.collidepoint(pos):
                                    restart_game()
                                elif to_main_menu_button.collidepoint(pos):
                                    game_started = False
                                    restart_game()
                                elif back_button.collidepoint(pos) and board_history:
                                    try:
                                        board, prev_captures = board_history.pop()
                                        captures = prev_captures.copy()
                                        current_player = 3 - current_player
                                    except:
                                        pass
                                elif rules_button.collidepoint(pos):
                                    show_rules = True

        if not game_started:
            if show_rules:
                back_button = draw_rules()
                if back_button.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(screen, HOVER_COLOR, back_button)
                    back_text = font.render("Назад", True, BUTTON_TEXT_COLOR)
                    back_text_rect = back_text.get_rect(center=back_button.center)
                    screen.blit(back_text, back_text_rect)
            else:
                size_buttons, rules_button = draw_main_menu()
                if rules_button.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(screen, HOVER_COLOR, rules_button)
                    rules_text = font.render("Правила", True, BUTTON_TEXT_COLOR)
                    rules_text_rect = rules_text.get_rect(center=rules_button.center)
                    screen.blit(rules_text, rules_text_rect)
        else:
            if show_rules:
                back_button = draw_rules()
                if back_button.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(screen, HOVER_COLOR, back_button)
                    back_text = font.render("Назад", True, BUTTON_TEXT_COLOR)
                    back_text_rect = back_text.get_rect(center=back_button.center)
                    screen.blit(back_text, back_text_rect)
            else:
                draw_board()
                draw_stones()
                if game_ended:
                    black_score, white_score = count_points()
                    draw_scores(black_score, white_score)
                    to_main_menu_button = draw_to_main_menu_button()
                else:
                    draw_turn_indicator()
                    draw_end_game_button()
                    draw_restart_button()
                    draw_to_main_menu_button()
                    draw_back_button()
                    draw_rules_button()

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
