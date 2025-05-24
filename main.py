import pygame
import sys
import random
import time

# Pygameの初期化
pygame.init()

# 画面設定
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ワニワニパニック風ゲーム")

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# フォント設定
font = pygame.font.SysFont(None, 36)

# ゲーム変数
score = 0
game_time = 30  # ゲーム時間（秒）
start_time = None
holes = []  # 穴の位置リスト
active_holes = {}  # アクティブな穴（ワニが出ている穴）
hole_radius = 40
hole_positions = [
    (200, 200), (400, 200), (600, 200),
    (200, 350), (400, 350), (600, 350),
    (200, 500), (400, 500), (600, 500)
]

# ワニのステータス
HIDDEN = 0
APPEARING = 1
VISIBLE = 2
DISAPPEARING = 3

# ワニの設定
wani_speed = 1.5  # ワニの出現・消失速度
wani_visible_time = 1.0  # ワニが見える時間
wani_probability = 0.05  # ワニが出現する確率（フレームごと）

# ゲームの状態
STATE_TITLE = 0
STATE_PLAYING = 1
STATE_GAMEOVER = 2
game_state = STATE_TITLE

# 穴を初期化
for pos in hole_positions:
    holes.append(pos)

# ゲームループ
clock = pygame.time.Clock()
running = True

def draw_hole(pos, is_active=False, progress=0):
    """穴を描画する"""
    pygame.draw.circle(screen, BLACK, pos, hole_radius)
    if is_active:
        # ワニを描画（簡易版）
        wani_height = int(hole_radius * 1.5 * progress)
        if wani_height > 0:
            # ワニの体（緑）
            pygame.draw.rect(screen, GREEN, 
                            (pos[0] - hole_radius//2, pos[1] - wani_height, 
                             hole_radius, wani_height))
            
            # ワニの目（白と黒）
            eye_size = max(5, int(hole_radius * 0.2 * progress))
            pygame.draw.circle(screen, WHITE, 
                              (pos[0] - hole_radius//4, pos[1] - wani_height + eye_size), 
                              eye_size)
            pygame.draw.circle(screen, WHITE, 
                              (pos[0] + hole_radius//4, pos[1] - wani_height + eye_size), 
                              eye_size)
            
            pygame.draw.circle(screen, BLACK, 
                              (pos[0] - hole_radius//4, pos[1] - wani_height + eye_size), 
                              eye_size//2)
            pygame.draw.circle(screen, BLACK, 
                              (pos[0] + hole_radius//4, pos[1] - wani_height + eye_size), 
                              eye_size//2)
            
            # ワニの口（赤）
            mouth_height = max(3, int(hole_radius * 0.3 * progress))
            pygame.draw.rect(screen, RED, 
                            (pos[0] - hole_radius//2, pos[1] - mouth_height, 
                             hole_radius, mouth_height))

def update_wani():
    """ワニの状態を更新する"""
    global active_holes
    
    # 新しいワニを出現させる可能性
    if len(active_holes) < 3 and random.random() < wani_probability:
        available_holes = [h for h in holes if h not in active_holes]
        if available_holes:
            new_hole = random.choice(available_holes)
            active_holes[new_hole] = {
                'state': APPEARING,
                'progress': 0,
                'time': 0
            }
    
    # 既存のワニを更新
    holes_to_remove = []
    for hole, data in active_holes.items():
        if data['state'] == APPEARING:
            data['progress'] += wani_speed * 0.02
            if data['progress'] >= 1:
                data['state'] = VISIBLE
                data['progress'] = 1
                data['time'] = time.time()
        
        elif data['state'] == VISIBLE:
            if time.time() - data['time'] > wani_visible_time:
                data['state'] = DISAPPEARING
        
        elif data['state'] == DISAPPEARING:
            data['progress'] -= wani_speed * 0.02
            if data['progress'] <= 0:
                holes_to_remove.append(hole)
    
    # 消えたワニを削除
    for hole in holes_to_remove:
        del active_holes[hole]

def check_hit(pos):
    """クリック位置がワニに当たったかチェック"""
    global score, active_holes
    
    for hole, data in list(active_holes.items()):
        dx = pos[0] - hole[0]
        dy = pos[1] - hole[1]
        distance = (dx*dx + dy*dy) ** 0.5
        
        if distance <= hole_radius and data['state'] in [APPEARING, VISIBLE]:
            score += 1
            active_holes[hole]['state'] = DISAPPEARING
            return True
    
    return False

def draw_title():
    """タイトル画面を描画"""
    screen.fill(BLUE)
    title = font.render("ワニワニパニック風ゲーム", True, WHITE)
    instruction = font.render("クリックしてスタート", True, WHITE)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 50))
    screen.blit(instruction, (WIDTH//2 - instruction.get_width()//2, HEIGHT//2 + 50))

def draw_game():
    """ゲーム画面を描画"""
    screen.fill(BLUE)
    
    # 残り時間を計算
    elapsed = time.time() - start_time
    remaining = max(0, game_time - elapsed)
    
    # スコアと時間を表示
    score_text = font.render(f"スコア: {score}", True, WHITE)
    time_text = font.render(f"残り時間: {int(remaining)}秒", True, WHITE)
    screen.blit(score_text, (10, 10))
    screen.blit(time_text, (WIDTH - 200, 10))
    
    # 穴とワニを描画
    for hole in holes:
        if hole in active_holes:
            wani_data = active_holes[hole]
            draw_hole(hole, True, wani_data['progress'])
        else:
            draw_hole(hole)
    
    # 時間切れチェック
    if remaining <= 0:
        global game_state
        game_state = STATE_GAMEOVER

def draw_gameover():
    """ゲームオーバー画面を描画"""
    screen.fill(BLUE)
    gameover_text = font.render("ゲームオーバー", True, WHITE)
    score_text = font.render(f"最終スコア: {score}", True, WHITE)
    restart_text = font.render("クリックして再スタート", True, WHITE)
    
    screen.blit(gameover_text, (WIDTH//2 - gameover_text.get_width()//2, HEIGHT//2 - 80))
    screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2))
    screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 80))

# メインゲームループ
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == STATE_TITLE:
                # タイトル画面からゲーム開始
                game_state = STATE_PLAYING
                score = 0
                start_time = time.time()
                active_holes = {}
            
            elif game_state == STATE_PLAYING:
                # プレイ中のクリック処理
                check_hit(event.pos)
            
            elif game_state == STATE_GAMEOVER:
                # ゲームオーバーからタイトルに戻る
                game_state = STATE_TITLE
    
    # 状態に応じた更新と描画
    if game_state == STATE_TITLE:
        draw_title()
    
    elif game_state == STATE_PLAYING:
        update_wani()
        draw_game()
    
    elif game_state == STATE_GAMEOVER:
        draw_gameover()
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
