
import sys
import pygame
import chess

# ============================================================
# CHESS MASTER - Player vs Player / Player vs Computer
# Dibuat dengan pygame-ce dan python-chess
# ============================================================

pygame.init()

# ------------------------- KONFIGURASI -----------------------

WIDTH, HEIGHT = 760, 820
BOARD_SIZE = 640
SQUARE_SIZE = BOARD_SIZE // 8
BOARD_X, BOARD_Y = 60, 65
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("CHESS MASTER")
clock = pygame.time.Clock()

# Warna
BG = (24, 29, 39)
PANEL = (35, 42, 55)
LIGHT = (238, 238, 210)
DARK = (118, 150, 86)
SELECTED = (246, 214, 85)
LAST_MOVE = (205, 190, 70)
MOVE_DOT = (45, 115, 55)
WHITE = (250, 250, 242)
BLACK = (25, 27, 32)
TEXT = (235, 239, 245)
MUTED = (165, 175, 190)
BLUE = (65, 115, 190)
BLUE_HOVER = (85, 135, 210)
RED = (190, 65, 65)

# Font
title_font = pygame.font.SysFont("arial", 30, bold=True)
info_font = pygame.font.SysFont("arial", 20, bold=True)
small_font = pygame.font.SysFont("arial", 15)
button_font = pygame.font.SysFont("arial", 16, bold=True)

# Font simbol catur Windows. Jika font ini tidak tersedia, gunakan fallback.
symbol_font_path = pygame.font.match_font("seguisym")
if symbol_font_path is None:
    symbol_font_path = pygame.font.match_font("segoeuisymbol")

if symbol_font_path:
    piece_font = pygame.font.Font(symbol_font_path, 66)
else:
    piece_font = pygame.font.SysFont("dejavusans", 66)

# Simbol bidak
PIECE_GLYPHS = {
    "K": "♔", "Q": "♕", "R": "♖", "B": "♗", "N": "♘", "P": "♙",
    "k": "♚", "q": "♛", "r": "♜", "b": "♝", "n": "♞", "p": "♟"
}

# ------------------------- STATUS GAME -----------------------

board = chess.Board()
selected_square = None
selected_moves = []

# "computer" = manusia putih vs komputer hitam
# "pvp" = dua pemain bergantian
game_mode = "computer"
difficulty_names = ["Easy", "Medium", "Hard"]
difficulty_index = 1

ai_thinking = False
status_message = ""
last_move = None

# Kedalaman pencarian untuk masing-masing tingkat
AI_DEPTHS = {
    "Easy": 1,
    "Medium": 2,
    "Hard": 3
}

# Nilai material bidak untuk evaluasi AI
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0
}

MATE_SCORE = 100000


# ------------------------- FUNGSI TAMPILAN -------------------

def board_to_screen(square):
    """Mengubah kotak catur menjadi posisi tengah kotak di layar."""
    file_index = chess.square_file(square)
    rank_index = chess.square_rank(square)

    x = BOARD_X + file_index * SQUARE_SIZE + SQUARE_SIZE // 2
    y = BOARD_Y + (7 - rank_index) * SQUARE_SIZE + SQUARE_SIZE // 2
    return x, y


def draw_piece(piece, center):
    """Menggambar simbol bidak dengan garis tepi agar mudah dilihat."""
    glyph = PIECE_GLYPHS[piece.symbol()]

    if piece.color == chess.WHITE:
        fill = (255, 255, 250)
        outline = (35, 35, 35)
    else:
        fill = (25, 27, 32)
        outline = (245, 245, 235)

    x, y = center
    shadow = piece_font.render(glyph, True, outline)
    image = piece_font.render(glyph, True, fill)

    # Outline empat arah
    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
        shadow_rect = shadow.get_rect(center=(x + dx, y + dy))
        screen.blit(shadow, shadow_rect)

    image_rect = image.get_rect(center=(x, y))
    screen.blit(image, image_rect)


def draw_board():
    """Menggambar 64 kotak, koordinat, bidak, dan penanda langkah."""
    # Kotak terakhir yang bergerak
    if last_move is not None:
        last_from = last_move.from_square
        last_to = last_move.to_square
    else:
        last_from = last_to = None

    for row in range(8):
        for col in range(8):
            x = BOARD_X + col * SQUARE_SIZE
            y = BOARD_Y + row * SQUARE_SIZE
            square = chess.square(col, 7 - row)

            color = LIGHT if (row + col) % 2 == 0 else DARK
            pygame.draw.rect(
                screen, color,
                (x, y, SQUARE_SIZE, SQUARE_SIZE)
            )

            # Sorot langkah terakhir
            if square == last_from or square == last_to:
                overlay = pygame.Surface(
                    (SQUARE_SIZE, SQUARE_SIZE),
                    pygame.SRCALPHA
                )
                overlay.fill((*LAST_MOVE, 105))
                screen.blit(overlay, (x, y))

            # Sorot raja yang sedang skak
            if board.is_check() and square == board.king(board.turn):
                pygame.draw.rect(
                    screen, RED,
                    (x, y, SQUARE_SIZE, SQUARE_SIZE)
                )

            # Sorot bidak terpilih
            if square == selected_square:
                pygame.draw.rect(
                    screen, SELECTED,
                    (x, y, SQUARE_SIZE, SQUARE_SIZE), 5
                )

            # Titik tujuan langkah legal
            for move in selected_moves:
                if move.to_square == square:
                    center = (
                        x + SQUARE_SIZE // 2,
                        y + SQUARE_SIZE // 2
                    )

                    if board.piece_at(square):
                        pygame.draw.circle(
                            screen, MOVE_DOT, center, 31, 5
                        )
                    else:
                        pygame.draw.circle(
                            screen, MOVE_DOT, center, 9
                        )

            # Koordinat
            if col == 0:
                rank_label = small_font.render(
                    str(8 - row), True, (45, 50, 45)
                )
                screen.blit(rank_label, (x + 5, y + 3))

            if row == 7:
                file_label = small_font.render(
                    "abcdefgh"[col], True, (45, 50, 45)
                )
                screen.blit(
                    file_label,
                    (x + SQUARE_SIZE - 17, y + SQUARE_SIZE - 19)
                )

            piece = board.piece_at(square)
            if piece:
                draw_piece(
                    piece,
                    (x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2)
                )


def draw_button(rect, label, color=BLUE, enabled=True):
    """Menggambar tombol UI."""
    mouse_pos = pygame.mouse.get_pos()
    button_color = color

    if not enabled:
        button_color = (85, 90, 100)
    elif rect.collidepoint(mouse_pos):
        button_color = BLUE_HOVER

    pygame.draw.rect(
        screen, button_color, rect, border_radius=8
    )
    pygame.draw.rect(
        screen, (210, 220, 235), rect, 1, border_radius=8
    )

    label_surface = button_font.render(label, True, WHITE)
    screen.blit(label_surface, label_surface.get_rect(center=rect.center))


# Tombol-tombol UI
restart_button = pygame.Rect(60, 755, 125, 42)
undo_button = pygame.Rect(198, 755, 105, 42)
mode_button = pygame.Rect(316, 755, 190, 42)
difficulty_button = pygame.Rect(519, 755, 181, 42)


def game_status_text():
    """Menghasilkan status permainan berdasarkan posisi saat ini."""
    if board.is_checkmate():
        winner = "Hitam" if board.turn == chess.WHITE else "Putih"
        return f"SKAKMAT - {winner} menang!"

    if board.is_stalemate():
        return "Seri - stalemate"

    if board.is_insufficient_material():
        return "Seri - material tidak cukup"

    if board.is_seventyfive_moves():
        return "Seri - aturan 75 langkah"

    if board.is_fivefold_repetition():
        return "Seri - pengulangan posisi"

    if board.is_check():
        turn = "Putih" if board.turn == chess.WHITE else "Hitam"
        return f"SKAK! Giliran {turn}"

    if game_mode == "computer":
        if board.turn == chess.WHITE:
            return "Giliran kamu (Putih)"
        return "Giliran komputer (Hitam)"

    return (
        "Giliran Putih"
        if board.turn == chess.WHITE
        else "Giliran Hitam"
    )


def draw_interface():
    screen.fill(BG)

    title = title_font.render("CHESS MASTER", True, TEXT)
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 30)))

    draw_board()

    # Panel status
    pygame.draw.rect(
        screen, PANEL, (40, 715, 680, 31), border_radius=6
    )

    if ai_thinking:
        message = "Komputer sedang berpikir..."
    elif status_message:
        message = status_message
    else:
        message = game_status_text()

    status_surface = info_font.render(message, True, TEXT)
    screen.blit(status_surface, (52, 719))

    draw_button(restart_button, "RESTART")
    draw_button(
        undo_button, "UNDO",
        enabled=bool(board.move_stack)
    )
    draw_button(
        mode_button,
        "MODE: VS KOMPUTER"
        if game_mode == "computer"
        else "MODE: 2 PEMAIN"
    )
    draw_button(
        difficulty_button,
        "AI: " + difficulty_names[difficulty_index],
        enabled=(game_mode == "computer")
    )


# ------------------------- ATURAN DAN AI ---------------------

def evaluate_position(position):
    """
    Evaluasi posisi dari sudut pandang pemain yang sedang jalan.
    Nilai positif berarti posisi menguntungkan pihak yang jalan.
    """
    if position.is_checkmate():
        return -MATE_SCORE

    if position.is_game_over():
        return 0

    white_score = 0

    for square, piece in position.piece_map().items():
        value = PIECE_VALUES[piece.piece_type]

        # Bonus kecil untuk bidak yang menguasai pusat papan
        file_index = chess.square_file(square)
        rank_index = chess.square_rank(square)
        center_distance = (
            abs(3.5 - file_index) + abs(3.5 - rank_index)
        )
        center_bonus = int((7 - center_distance) * 3)

        if piece.piece_type in (
            chess.KNIGHT, chess.BISHOP, chess.PAWN
        ):
            value += center_bonus

        if piece.color == chess.WHITE:
            white_score += value
        else:
            white_score -= value

    return (
        white_score
        if position.turn == chess.WHITE
        else -white_score
    )


def move_order_score(position, move):
    """Mendahulukan langkah makan bidak dan promosi agar pencarian lebih efektif."""
    score = 0

    if position.is_capture(move):
        victim = position.piece_at(move.to_square)

        # En passant: bidak yang dimakan tidak berada di kotak tujuan
        if victim is None and position.is_en_passant(move):
            victim_value = PIECE_VALUES[chess.PAWN]
        else:
            victim_value = (
                PIECE_VALUES[victim.piece_type] if victim else 0
            )

        attacker = position.piece_at(move.from_square)
        attacker_value = (
            PIECE_VALUES[attacker.piece_type] if attacker else 0
        )
        score += 10 * victim_value - attacker_value

    if move.promotion:
        score += PIECE_VALUES[move.promotion]

    return score


def negamax(position, depth, alpha, beta, ply=0):
    """Minimax dengan Alpha-Beta Pruning."""
    if position.is_checkmate():
        return -MATE_SCORE + ply

    if position.is_game_over():
        return 0

    if depth == 0:
        return evaluate_position(position)

    moves = list(position.legal_moves)
    moves.sort(
        key=lambda m: move_order_score(position, m),
        reverse=True
    )

    best_score = -float("inf")

    for move in moves:
        position.push(move)
        score = -negamax(
            position, depth - 1, -beta, -alpha, ply + 1
        )
        position.pop()

        if score > best_score:
            best_score = score

        alpha = max(alpha, score)

        if alpha >= beta:
            break

    return best_score


def choose_computer_move():
    """Memilih langkah komputer berdasarkan tingkat kesulitan."""
    if board.is_game_over():
        return None

    depth = AI_DEPTHS[difficulty_names[difficulty_index]]
    moves = list(board.legal_moves)

    if not moves:
        return None

    moves.sort(
        key=lambda m: move_order_score(board, m),
        reverse=True
    )

    best_move = None
    best_score = -float("inf")
    alpha = -float("inf")
    beta = float("inf")

    for move in moves:
        board.push(move)
        score = -negamax(
            board, depth - 1, -beta, -alpha, 1
        )
        board.pop()

        if score > best_score:
            best_score = score
            best_move = move

        alpha = max(alpha, score)

    return best_move


def play_computer_turn():
    """Menjalankan giliran komputer jika mode VS Komputer aktif."""
    global ai_thinking, last_move, status_message
    global selected_square, selected_moves

    if (
        game_mode != "computer"
        or board.turn != chess.BLACK
        or board.is_game_over()
    ):
        return

    ai_thinking = True
    selected_square = None
    selected_moves = []
    draw_interface()
    pygame.display.flip()

    computer_move = choose_computer_move()

    if computer_move is not None:
        board.push(computer_move)
        last_move = computer_move
        status_message = ""

    ai_thinking = False


# ------------------------- KONTROL GAME ----------------------

def get_square_from_mouse(position):
    x, y = position

    if not (
        BOARD_X <= x < BOARD_X + BOARD_SIZE
        and BOARD_Y <= y < BOARD_Y + BOARD_SIZE
    ):
        return None

    col = (x - BOARD_X) // SQUARE_SIZE
    row = (y - BOARD_Y) // SQUARE_SIZE

    return chess.square(col, 7 - row)


def handle_board_click(position):
    global selected_square, selected_moves
    global last_move, status_message

    if board.is_game_over() or ai_thinking:
        return

    # Dalam mode komputer, manusia hanya menggerakkan putih.
    if game_mode == "computer" and board.turn == chess.BLACK:
        return

    square = get_square_from_mouse(position)

    if square is None:
        selected_square = None
        selected_moves = []
        return

    piece = board.piece_at(square)

    # Belum ada bidak yang dipilih
    if selected_square is None:
        if piece and piece.color == board.turn:
            selected_square = square
            selected_moves = [
                move for move in board.legal_moves
                if move.from_square == square
            ]
        return

    # Klik bidak sendiri untuk mengganti pilihan
    if piece and piece.color == board.turn:
        selected_square = square
        selected_moves = [
            move for move in board.legal_moves
            if move.from_square == square
        ]
        return

    # Cari langkah yang menuju kotak yang diklik
    possible_moves = [
        move for move in selected_moves
        if move.to_square == square
    ]

    if possible_moves:
        # Promosi otomatis menjadi ratu
        move = next(
            (
                candidate for candidate in possible_moves
                if candidate.promotion == chess.QUEEN
            ),
            possible_moves[0]
        )

        board.push(move)
        last_move = move
        status_message = ""

        selected_square = None
        selected_moves = []

        # Komputer langsung membalas setelah langkah putih.
        if game_mode == "computer" and not board.is_game_over():
            play_computer_turn()

    else:
        selected_square = None
        selected_moves = []


def restart_game():
    """Restart penuh: posisi, riwayat, pilihan, dan status direset."""
    global board, selected_square, selected_moves
    global last_move, status_message, ai_thinking

    board = chess.Board()
    selected_square = None
    selected_moves = []
    last_move = None
    status_message = ""
    ai_thinking = False


def undo_move():
    """
    Mode VS komputer: batalkan satu putaran (langkah komputer + manusia).
    Mode 2 pemain: batalkan satu langkah terakhir.
    """
    global selected_square, selected_moves
    global last_move, status_message

    selected_square = None
    selected_moves = []
    status_message = ""

    if not board.move_stack:
        return

    if game_mode == "computer":
        # Jika komputer sudah membalas, giliran kembali ke putih:
        # batalkan dua ply. Jika belum, batalkan satu ply saja.
        if board.turn == chess.WHITE and len(board.move_stack) >= 2:
            board.pop()
            board.pop()
        else:
            board.pop()
    else:
        board.pop()

    last_move = (
        board.peek() if board.move_stack else None
    )


def toggle_mode():
    """Ganti mode permainan dan mulai papan baru agar giliran jelas."""
    global game_mode

    game_mode = (
        "pvp" if game_mode == "computer" else "computer"
    )
    restart_game()


def change_difficulty():
    global difficulty_index

    difficulty_index = (
        difficulty_index + 1
    ) % len(difficulty_names)


# ------------------------- LOOP UTAMA ------------------------

running = True

while running:
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            mouse_pos = event.pos

            if restart_button.collidepoint(mouse_pos):
                restart_game()

            elif undo_button.collidepoint(mouse_pos):
                undo_move()

            elif mode_button.collidepoint(mouse_pos):
                toggle_mode()

            elif difficulty_button.collidepoint(mouse_pos):
                if game_mode == "computer":
                    change_difficulty()

            else:
                handle_board_click(mouse_pos)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                restart_game()

            elif event.key == pygame.K_u:
                undo_move()

            elif event.key == pygame.K_ESCAPE:
                selected_square = None
                selected_moves = []

    draw_interface()
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
