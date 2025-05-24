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

# マウスカーソルをハンマーのデザインに変更
pygame.mouse.set_cursor(pygame.cursors.broken_x)

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
BROWN = (165, 42, 42)  # 穴の色

# フォント設定
try:
    # 日本語対応フォントを試す
    font = pygame.font.Font("NotoSansCJK-Regular.ttc", 36)
except:
    try:
        # macOSの日本語フォント
        font = pygame.font.Font("/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc", 36)
    except:
        try:
            # その他のシステムフォント
            font = pygame.font.Font("/System/Library/Fonts/Arial Unicode MS.ttf", 36)
        except:
            # フォールバック
            font = pygame.font.SysFont("Arial Unicode MS", 36)
            if not font:
                font = pygame.font.SysFont("hiragino sans", 36)

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

# エフェクト設定
hit_effects = []  # ヒットエフェクトのリスト
effect_duration = 1.0  # エフェクトの表示時間（秒）

# マウス近接エフェクト設定
mouse_effects = []  # マウス近接エフェクトのリスト
mouse_effect_distance = 80  # マウスがこの距離以内に来たら反応
mouse_effect_duration = 0.8  # エフェクトの表示時間（秒）

# ゲームの状態
STATE_TITLE = 0
STATE_PLAYING = 1
STATE_GAMEOVER = 2
game_state = STATE_TITLE

# 穴を初期化
for pos in hole_positions:
    holes.append(pos)

# 画像の読み込み
crocodile_image = pygame.image.load('assets/Crocodile.png')
crocodile_image = pygame.transform.scale(crocodile_image, (100, 100))  # サイズ調整

hammer_image = pygame.image.load('assets/hammer.png')
hammer_image = pygame.transform.scale(hammer_image, (80, 80))  # サイズ調整

# ハンマーの描画位置
hammer_pos = None

# ゲームループ
clock = pygame.time.Clock()
running = True

# ハンマーの回転状態
hammer_angle = 0
hammer_tilt_time = 0  # ハンマー傾きの終了時刻

def draw_hole(pos, is_active=False, progress=0):
    """穴を描画する"""
    if is_active:
        # ワニを描画
        screen.blit(crocodile_image, (pos[0] - crocodile_image.get_width() // 2, pos[1] - crocodile_image.get_height() // 2))
    else:
        # 穴の描画（デフォルトのまま）
        pygame.draw.circle(screen, BROWN, pos, hole_radius)

def update_wani():
    """ワニの状態を更新する"""
    global active_holes, hit_effects
    
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
    
    # ヒットエフェクトを更新（時間切れのものを削除）
    hit_effects[:] = [effect for effect in hit_effects 
                      if time.time() - effect['time'] < effect_duration]

def check_mouse_proximity():
    """マウスがワニに近づいているかチェック"""
    global mouse_effects
    
    mouse_pos = pygame.mouse.get_pos()
    
    for hole, data in active_holes.items():
        if data['state'] in [APPEARING, VISIBLE]:
            dx = mouse_pos[0] - hole[0]
            dy = mouse_pos[1] - hole[1]
            distance = (dx*dx + dy*dy) ** 0.5
            
            # マウスが近づいた場合、まだエフェクトが出ていなければ追加
            if distance <= mouse_effect_distance:
                # この穴に対して既にエフェクトが出ているかチェック
                already_has_effect = any(effect['hole'] == hole for effect in mouse_effects)
                
                if not already_has_effect:
                    mouse_effects.append({
                        'hole': hole,
                        'pos': hole,
                        'time': time.time(),
                        'text': "ヤダ！"
                    })
    
    # マウス近接エフェクトを更新（時間切れのものを削除）
    mouse_effects[:] = [effect for effect in mouse_effects 
                        if time.time() - effect['time'] < mouse_effect_duration]

def check_hit(pos):
    """クリック位置がワニに当たったかチェック"""
    global score, active_holes, hit_effects
    
    for hole, data in list(active_holes.items()):
        dx = pos[0] - hole[0]
        dy = pos[1] - hole[1]
        distance = (dx*dx + dy*dy) ** 0.5
        
        if distance <= hole_radius and data['state'] in [APPEARING, VISIBLE]:
            score += 1
            # ワニをすぐに削除する
            del active_holes[hole]
            
            # ヒットエフェクトを追加
            hit_effects.append({
                'pos': hole,
                'time': time.time(),
                'text': "イテッ!"
            })
            
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
    
    # ヒットエフェクトを描画
    for effect in hit_effects:
        elapsed_time = time.time() - effect['time']
        alpha = max(0, 1 - elapsed_time / effect_duration)  # フェードアウト効果
        
        # エフェクトが移動するように y座標を上に移動
        y_offset = int(elapsed_time * 50)  # 時間に応じて上に移動
        
        # エフェクトテキストを描画
        effect_surface = font.render(effect['text'], True, RED)
        pos_x = effect['pos'][0] - effect_surface.get_width() // 2
        pos_y = effect['pos'][1] - 50 - y_offset
        
        # 透明度を適用（簡易版：赤色の強度を調整）
        color_intensity = int(255 * alpha)
        effect_surface = font.render(effect['text'], True, (color_intensity, 0, 0))
        
        screen.blit(effect_surface, (pos_x, pos_y))
    
    # マウス近接エフェクトを描画
    for effect in mouse_effects:
        elapsed_time = time.time() - effect['time']
        alpha = max(0, 1 - elapsed_time / mouse_effect_duration)  # フェードアウト効果
        
        # エフェクトが揺れるように左右に移動
        x_shake = int(5 * alpha * (1 if random.random() < 0.5 else -1))
        
        # エフェクトテキストを描画
        pos_x = effect['pos'][0] - font.get_height() // 2 + x_shake
        pos_y = effect['pos'][1] - 80
        
        # 透明度を適用（黄色で表示）
        color_intensity = int(255 * alpha)
        effect_surface = font.render(effect['text'], True, (color_intensity, color_intensity, 0))
        
        screen.blit(effect_surface, (pos_x, pos_y))
    
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
    mouse_pos = pygame.mouse.get_pos()  # マウスの現在位置を取得

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            hammer_angle = 45  # クリック時にハンマーを45度傾ける
            hammer_tilt_time = time.time() + 0.2  # 0.2秒後に戻す
            if game_state == STATE_TITLE:
                # タイトル画面からゲーム開始
                game_state = STATE_PLAYING
                score = 0
                start_time = time.time()
                active_holes = {}
                hit_effects = []  # エフェクトをクリア
                mouse_effects = []  # マウスエフェクトもクリア

            elif game_state == STATE_PLAYING:
                # プレイ中のクリック処理
                check_hit(event.pos)

            elif game_state == STATE_GAMEOVER:
                # ゲームオーバーからタイトルに戻る
                game_state = STATE_TITLE
                hit_effects = []  # エフェクトをクリア
                mouse_effects = []  # マウスエフェクトもクリア

    # ハンマーの角度を0.2秒後に戻す
    if hammer_angle != 0 and time.time() > hammer_tilt_time:
        hammer_angle = 0

    # 状態に応じた更新と描画
    if game_state == STATE_TITLE:
        draw_title()

    elif game_state == STATE_PLAYING:
        update_wani()
        check_mouse_proximity()
        draw_game()

    elif game_state == STATE_GAMEOVER:
        draw_gameover()

    # ハンマーを描画（クリック時の回転を反映）
    # ハンマーの右上寄りをカーソル中心に合わせる
    rotated_hammer = pygame.transform.rotate(hammer_image, hammer_angle)
    offset_x = int(rotated_hammer.get_width() * 0.25)
    offset_y = int(rotated_hammer.get_height() * 0.25)
    screen.blit(rotated_hammer, (mouse_pos[0] - offset_x, mouse_pos[1] - offset_y))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
