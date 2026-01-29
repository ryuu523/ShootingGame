import pygame 
from pygame.locals import *
from pygame.math import Vector2
import sys
import math
import random
import json


SCREEN_WIDTH = 600
SCREEN_HEIGHT = 800
FPS = 60

ENEMY_BULLET_SPEED=2.5
BULLET_RADIUS=4

SCENE_START = 0
SCENE_PLAY = 1
SCENE_GAMEOVER = 2
SCENE_CLEAR=3
scene=SCENE_START


pygame.init()  
screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
pygame.display.set_caption("game")
clock = pygame.time.Clock()
pygame.font.init()
font = pygame.font.SysFont("arial", 24)
font_large = pygame.font.SysFont("arial", 48)

frame_count = 0
player_shot_timer = 0 
total_score = 0

#プレイヤーの設定
class Player:
    def __init__(self):
        self.reset()
    def reset(self):
        self.pos = Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)
        self.width = 20
        self.height = 20
        self.radius = 4.5
        self.speed = 4
        self.hp_max = 3
        self.hp = self.hp_max
        self.lives = 3
        self.shot_timer = 0
        self.cooldown = 4
        self.bullet_speed = 10
        self.is_invincible = False
        self.invincible_timer = 0
    def move(self):
        pressed_key = pygame.key.get_pressed()
        is_shift = pressed_key[K_LSHIFT] or pressed_key[K_RSHIFT]
        coe = 0.3 if is_shift else 1.0

        vec = Vector2(0, 0)
        if pressed_key[K_LEFT] or pressed_key[K_a]:  vec.x = -1
        if pressed_key[K_RIGHT] or pressed_key[K_d]: vec.x = 1
        if pressed_key[K_UP] or pressed_key[K_w]:    vec.y = -1
        if pressed_key[K_DOWN] or pressed_key[K_s]:  vec.y = 1

        if vec.length() > 0:
            self.pos += vec.normalize() * self.speed * coe

        # 壁判定
        self.pos.x = max(self.width//2, min(SCREEN_WIDTH - self.width//2, self.pos.x))
        self.pos.y = max(self.height//2, min(SCREEN_HEIGHT - self.height//2, self.pos.y))

    def update(self, player_bullets):
        global total_score
        self.move()
        self.draw()
        total_score+=1
        # ショット処理
        if self.shot_timer > 0:
            self.shot_timer -= 1
            
        pressed_key = pygame.key.get_pressed()
        pressed_mouse = pygame.mouse.get_pressed()
        if (pressed_key[K_z] or pressed_mouse[0]) and self.shot_timer <= 0:
            self.shoot(player_bullets)
            self.shot_timer = self.cooldown

    def shoot(self, player_bullets):
        shoot_angles=[-15,0,15]
        pressed_key = pygame.key.get_pressed()
        if pressed_key[K_LSHIFT] or pressed_key[K_RSHIFT]:
            shoot_angles=[-5,0,5]
        for angle in shoot_angles:
            bullet = ColorBullet("white", 5)
            bullet.set_position(Vector2(self.pos.x, self.pos.y))
            bullet.set_velocity(Vector2(0, -self.bullet_speed).rotate(angle))
            player_bullets.append(bullet)
    def draw(self):
        #無敵時点滅
        if self.invincible_timer%4 <2:
            # プレイヤー本体
            pygame.draw.rect(screen, (255, 255, 255), (self.pos.x - self.width//2, self.pos.y - self.height//2, self.width, self.height))
        # 低速時の判定表示
        pressed_key = pygame.key.get_pressed()
        if pressed_key[K_LSHIFT] or pressed_key[K_RSHIFT]:
            pygame.draw.circle(screen, (100, 100, 255), (int(self.pos.x), int(self.pos.y)), self.radius)
#敵の設定
class Enemy:
    def __init__(self, x, y, barrage, hp=3):
        self.pos = Vector2(x, y)
        self.hp = hp
        self.radius = 15
        self.speed = 0.5
        self.timer = 0
        self.score_value = 1000 
        self.barrage=barrage
        self.spawn_frame=frame_count

    def update(self,target_pos):
        relative_frame = frame_count - self.spawn_frame
        self.move()
        self.barrage.spawn(self.pos,relative_frame,target_pos)
        
        self.draw()
        
        if self.pos.y > SCREEN_HEIGHT + 50 or self.hp <= 0:
            return True  # 画面外に出たかHP0以下で消滅
        return False
    
    def move(self):
        self.pos.y += self.speed 
        
    def draw(self):
        pygame.draw.circle(screen, (255, 0, 0), (int(self.pos.x), int(self.pos.y)), self.radius)
        pygame.draw.rect(screen, (255, 0, 0), (self.pos.x-15, self.pos.y-25, 30, 5))
        pygame.draw.rect(screen, (0, 255, 0), (self.pos.x-15, self.pos.y-25, 30 * (self.hp/3), 5))
class SineEnemy(Enemy):
    def __init__(self, x, y, barrage, hp=3):
        super().__init__(x, y, barrage, hp)
        self.start_x = x
        self.amplitude = 100  # 揺れ幅
        self.frequency = 0.05 # 揺れる速さ

    def move(self):
        relative_frame = frame_count - self.spawn_frame
        self.pos.y += self.speed
        # サイン関数を使ってX座標を計算
        self.pos.x = self.start_x + math.sin(relative_frame * self.frequency) * self.amplitude
class HoverEnemy(Enemy):
    def __init__(self, x, y, barrage, stop_y=200, hp=5):
        super().__init__(x, y, barrage, hp)
        self.stop_y = stop_y

    def move(self):
        # 指定した座標より上なら降りる、過ぎたら止まる
        if self.pos.y < self.stop_y:
            self.pos.y += self.speed * 2  # 登場時は少し速く
class DasherEnemy(Enemy):
    def __init__(self, x, y, barrage, hp=2):
        super().__init__(x, y, barrage, hp)
        self.velocity = Vector2(0, self.speed)
        self.is_dashing = False

    def move(self):
        # ターゲット（自機）の位置情報をupdateから受け取るために引数を調整するか、
        # ここでは単純なロジックのみ記載します
        if not self.is_dashing and self.pos.y > 150:
            # ここで一度だけ自機の方向を計算して突進速度を決める（実際の実装ではtarget_posが必要）
            self.is_dashing = True
            self.velocity.y = 4  # 突進スピード
            
        self.pos += self.velocity
class CircleEnemy(Enemy):
    def __init__(self, x, y, barrage, hp=3):
        super().__init__(x, y, barrage, hp)
        self.center_pos = Vector2(x, y)
        self.angle = 0
        self.radius_orbit = 50 # 回転半径

    def move(self):
        self.angle += 0.05
        self.center_pos.y += self.speed
        self.pos.x = self.center_pos.x + math.cos(self.angle) * self.radius_orbit
        self.pos.y = self.center_pos.y + math.sin(self.angle) * self.radius_orbit
class Boss(Enemy):
    def __init__(self, x, y, barrages):
        self.barrages = [cls() for cls in barrages]
        super().__init__(x, y, self.barrages[0], hp=50) 
        self.max_hp = 100#デフォルト
        self.hp=self.max_hp
        self.radius = 40  
        self.current_pattern_index = 0
        
        # 移動用
        self.target_x = x
        self.move_timer = 0
        self.state = "entrance" # 状態管理 (登場中 -> 戦闘中)

    def move(self):
        if self.state == "entrance":
            if self.pos.y < 100:
                self.pos.y += 1
            else:
                self.state = "battle"
        
        elif self.state == "battle":
            # 左右にゆらゆら動く
            self.move_timer += 0.02
            self.pos.x = SCREEN_WIDTH // 2 + math.sin(self.move_timer) * 150
            # 少し上下にも動かす
            self.pos.y = 100 + math.cos(self.move_timer * 0.5) * 30

    def update(self, target_pos):
        # HPに応じて弾幕（フェーズ）を切り替える
        self.check_phase()
        
        relative_frame = frame_count - self.spawn_frame
        self.move()
        
        # 現在のフェーズの弾幕を放つ
        current_barrage=self.barrages[self.current_pattern_index]
        current_barrage.spawn(self.pos, relative_frame, target_pos)
        current_barrage.update_bullets()
        self.barrage = current_barrage
        self.draw()
        
        if self.hp <= 0:
            return True # 撃破
        return False

    def check_phase(self):
        if self.current_pattern_index >= len(self.barrages) - 1:
            return

        hp_per_phase = self.max_hp / len(self.barrages)
        
        threshold = self.max_hp - (hp_per_phase * (self.current_pattern_index + 1))

        if self.hp <= threshold:
            self.current_pattern_index += 1
    def draw(self):
        # ボス本体の描画
        pygame.draw.circle(screen, (255, 100, 0), (int(self.pos.x), int(self.pos.y)), self.radius)
        # 飾り（トゲのようなもの）
        for i in range(8):
            angle = i * (math.pi / 4) + (frame_count * 0.05)
            tx = self.pos.x + math.cos(angle) * (self.radius + 10)
            ty = self.pos.y + math.sin(angle) * (self.radius + 10)
            pygame.draw.line(screen, (255, 255, 0), (self.pos.x, self.pos.y), (tx, ty), 3)

        # 画面上部に固定のボスHPバーを表示
        bar_width = 400
        bar_height = 15
        bar_x = (SCREEN_WIDTH - bar_width) // 2
        bar_y = 100
        # 下地（赤）
        pygame.draw.rect(screen, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        # 現在のHP（緑）
        hp_ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, bar_width * hp_ratio, bar_height))
        # 枠線
        pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)
#弾の設定
class Bullet:
    def __init__(self, pos=None, velocity=None, radius=BULLET_RADIUS, color=(255,0,0)):
        self.pos = Vector2(pos) if pos else Vector2(0,0)
        self.velocity = Vector2(velocity) if velocity else Vector2(0,0)
        self.radius = radius
        self.color = color
        self.angle = self.velocity.as_polar()[1] if self.velocity.length() > 0 else 0
        self.live_frame=0
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)
    
    def update(self):
        self.pos+=self.velocity
        self.live_frame+=1
        self.draw(screen)
        return self.collision_field()
    
    def collision_field(self):
        return  not (self.pos.x > 0 and self.pos.x < SCREEN_WIDTH and self.pos.y > 0 and self.pos.y < SCREEN_HEIGHT)
    
    def set_position(self,pos):
        self.pos = pos
    def get_position(self):
        return self.pos.copy()
    def get_velocity(self):
        return self.velocity.copy()
    def set_velocity(self,velocity):
        self.velocity = velocity
        self.angle = self.velocity.as_polar()[1]
class ColorBullet(Bullet):
    def __init__(self,color,radius):
        super().__init__(color=color,radius=radius)
class OmnidirectionalEXBullet(Bullet):
    def __init__(self,color,radius):
        super().__init__(color=color,radius=radius)
class AngVelBullet(Bullet):
    def __init__(self,color,radius):
        super().__init__(color=color,radius=radius)
        self.angle_speed = 0
        self.speed_multiplier = 1

    def update(self):
        self.velocity = self.velocity.rotate(self.angle_speed)
        self.velocity *= self.speed_multiplier
        return super().update()
    def set_spiral(self, angle, speed_up):
        self.angle_speed = angle
        self.speed_multiplier = speed_up  
class AccelBullet(Bullet):
    def __init__(self,color,radius):
        super().__init__(color=color,radius=radius)
        self.accel=0
        self.spawn_count=frame_count
    def update(self):
        if(frame_count-self.spawn_count>=30):
            direction = self.velocity.normalize()
            accel_vector = direction * self.accel
            self.velocity += accel_vector
            
        return super().update()
    def set_accel(self,accel):
        self.accel=accel
class FirstStopBullet(Bullet):
    def __init__(self,color,radius):
        super().__init__(color=color,radius=radius)
        self.stop_frame=0

    def update(self):
        self.live_frame+=1
        if(self.live_frame<=self.stop_frame):
            self.draw(screen)
            return False
        return super().update()
    def set_stop_frame(self,stop_frame):
        self.stop_frame=stop_frame

#弾幕の設定
class Barrage:
    def __init__(self) :
        self.bullets = []
        self.is_active = True

    def update(self):
        self.update_bullets()

    def update_bullets(self):
        self.bullets = [b for b in self.bullets if not b.update()]
    def spawn(self,start_pos,target_pos=None):
        pass   
class RandomDanmaku(Barrage):
    def spawn(self,start_pos,relative_frame,target_pos=None): 
        if(self.is_active and relative_frame%2==1):
            bullet= ColorBullet("red",BULLET_RADIUS)     
            bullet.set_position(Vector2(start_pos.x,start_pos.y))
            angle = random.randint(0, 360)
            vel = Vector2()
            vel.from_polar((ENEMY_BULLET_SPEED, angle)) 
            bullet.set_velocity(vel)
            self.bullets.append(bullet)   
class OmnidirectionalDanmaku(Barrage):
    def spawn(self,start_pos,relative_frame,target_pos=None): 
        if(self.is_active and relative_frame%30 ==0):
            DIV = 64
            for i in range(DIV):
                bullet =ColorBullet("red",BULLET_RADIUS)
                bullet.set_position(Vector2(start_pos.x,start_pos.y))
                bullet.set_velocity(Vector2(1, 0).rotate(360 / DIV * i)*ENEMY_BULLET_SPEED)
                self.bullets.append(bullet)             
class OmnidirectionalDanmakuEX(Barrage):
    def spawn(self,start_pos,relative_frame,target_pos=None):

        if(self.is_active and relative_frame%300 ==0):
            DIV = 16
            for i in range(DIV):
                bullet =OmnidirectionalEXBullet("red",BULLET_RADIUS)
                bullet.set_position(Vector2(start_pos.x,start_pos.y))
                bullet.set_velocity(Vector2(1, 0).rotate(360 / DIV * i)*ENEMY_BULLET_SPEED)
                self.bullets.append(bullet)
        if(relative_frame%10==0):
            new_bullets = [] 
            for option_bullet in self.bullets:
                if isinstance(option_bullet,OmnidirectionalEXBullet):
                    if 0< option_bullet.live_frame <=60 and option_bullet.live_frame%10==0:
                        for i in [-1,1]:
                            bullet = ColorBullet("red",BULLET_RADIUS)
                            bullet.set_position(option_bullet.get_position())
                            bullet.set_velocity(option_bullet.get_velocity().normalize().rotate(45*i)*ENEMY_BULLET_SPEED*0.5)
                            new_bullets.append(bullet)
            self.bullets.extend(new_bullets)
class UzumakiDanmaku(Barrage):
    def spawn(self,start_pos, relative_frame, target_pos=None): 
        if(self.is_active and relative_frame%3 ==0):
            bullet =ColorBullet("red",BULLET_RADIUS)
            bullet.set_position(Vector2(start_pos.x,start_pos.y))
            bullet.set_velocity(Vector2(1, 0).rotate(relative_frame*3)*ENEMY_BULLET_SPEED)
            self.bullets.append(bullet)
class RasenDanmaku(Barrage):
    def spawn(self,start_pos,relative_frame,target_pos=None): 
        super().spawn(start_pos,relative_frame)
        if(self.is_active and relative_frame%200==0):
            for i in range(2):
                bullet = AngVelBullet("orange",BULLET_RADIUS*2)
                if(i==0):
                    bullet.set_position(Vector2(start_pos.x+30,start_pos.y))
                else:
                    bullet.set_position(Vector2(start_pos.x-30,start_pos.y))
                bullet.set_velocity(Vector2(1, 0).rotate(180*i)*0.5)
                bullet.set_spiral(1.5,1.01)
                self.bullets.append(bullet)

        if(relative_frame%5==0):
            new_bullets = [] 
            for option_bullet in self.bullets:
                if isinstance(option_bullet,AngVelBullet):
                    bullet = AccelBullet("red",BULLET_RADIUS)
                    bullet.set_position(option_bullet.get_position())
                    bullet.set_velocity(option_bullet.get_velocity().normalize().rotate(270)*0.001)
                    bullet.set_accel(0.01)
                    new_bullets.append(bullet)
            self.bullets.extend(new_bullets)
class LinearScatteredDanmaku(Barrage):
    def __init__(self):
        super().__init__()
        self.option_angle=0
    def spawn(self,start_pos=None,relative_frame=None,target_pos=None): 
        start_x=random.randint(0,SCREEN_WIDTH)
        end_x=random.randint(0,SCREEN_WIDTH)
        angle=math.degrees(math.atan2(SCREEN_HEIGHT,(end_x-start_x)))
        if(self.is_active and relative_frame%400==0):
            bullet = ColorBullet("orange",BULLET_RADIUS*2)
            bullet.set_position(Vector2(start_x,0))
            bullet.set_velocity(Vector2(1, 0).rotate(angle)*ENEMY_BULLET_SPEED)
            self.bullets.append(bullet)
        if(relative_frame%10==0):
            new_bullets = [] 
            for option_bullet in self.bullets:
                if isinstance(option_bullet,ColorBullet):
                    bullet = FirstStopBullet("red",BULLET_RADIUS)
                    bullet.set_position(option_bullet.get_position())
                    bullet.set_velocity(Vector2(1, 0).rotate(self.option_angle)*ENEMY_BULLET_SPEED*0.5)
                    bullet.set_stop_frame(120)
                    new_bullets.append(bullet)
                    self.option_angle+=30
            self.bullets.extend(new_bullets)
class AimedDanmaku(Barrage):
    def spawn(self,start_pos,relative_frame,target_pos): 
        if(self.is_active and relative_frame%30==0):
            bullet = ColorBullet("red",BULLET_RADIUS)
            bullet.set_position(Vector2(start_pos.x,start_pos.y))
            direction = Vector2(target_pos.x - start_pos.x, target_pos.y - start_pos.y).normalize()
            bullet.set_velocity(direction * ENEMY_BULLET_SPEED)
            self.bullets.append(bullet)
def draw_text(text, font, color, x, y):
    img = font.render(text, True, color)
    rect = img.get_rect(center=(x, y))
    screen.blit(img, rect)
def collision_check(player,player_bullets,enemies):
    global total_score,scene
       # 1. プレイヤーの弾 vs 敵
    for b in player_bullets[:]:
        for e in enemies[:]:
            if b.pos.distance_to(e.pos) < b.radius + e.radius:
                e.hp -= 1
                if b in player_bullets: player_bullets.remove(b)
                if e.hp <= 0: 
                    if isinstance(e, Boss):
                        scene = SCENE_CLEAR
                    enemies.remove(e)
                    total_score += e.score_value
    if player.invincible_timer > 0:
        return  
    # 2. 敵の弾 vs プレイヤー
    for e in enemies:
        for eb in e.barrage.bullets[:]:
            if eb.pos.distance_to(player.pos) < eb.radius + player.radius:
                player.hp -= 1
                if eb in e.barrage.bullets: e.barrage.bullets.remove(eb)
    # 3. 敵本体 vs プレイヤー
    for e in enemies:
        if e.pos.distance_to(player.pos) < e.radius + player.radius:
            player.hp -= 1
def draw_hud(player):
    global total_score
    #  HPゲージの表示
    hud_x, hud_y = 20, 20
    bar_width, bar_height = 200, 15
    
    hp_text = font.render(f"HP: ", True, (255, 255, 255))
    screen.blit(hp_text, (hud_x, hud_y))
    pygame.draw.rect(screen, (100, 0, 0), (hud_x+30, hud_y, bar_width, bar_height))
    hp_ratio = max(0, player.hp / player.hp_max)
    pygame.draw.rect(screen, (0, 255, 0), (hud_x+30, hud_y, bar_width * hp_ratio, bar_height))
    pygame.draw.rect(screen, (255, 255, 255), (hud_x+30, hud_y, bar_width, bar_height), 2)

    # スコアの表示
    score_text = font.render(f"SCORE: {str(total_score).zfill(8)}", True, (255, 255, 255))
    screen.blit(score_text, (hud_x, hud_y + 25))
    
    # 残機の表示
    for i in range(player.lives):
        pygame.draw.rect(screen, (255, 255, 255), (hud_x+60 + i*25, hud_y + 45, 15, 15))
    lives_text = font.render(f"LIVES:", True, (255, 255, 255))
    screen.blit(lives_text, (hud_x, hud_y + 45))

ENEMY_CLASSES = {
    "SineEnemy": SineEnemy,
    "HoverEnemy": HoverEnemy,
    "DasherEnemy": DasherEnemy,
    "CircleEnemy": CircleEnemy,
    "Boss": Boss
}

BARRAGE_CLASSES = {
    "RandomDanmaku": RandomDanmaku,
    "OmnidirectionalDanmaku": OmnidirectionalDanmaku,
    "OmnidirectionalDanmakuEX": OmnidirectionalDanmakuEX,
    "UzumakiDanmaku": UzumakiDanmaku,
    "RasenDanmaku": RasenDanmaku,
    "AimedDanmaku": AimedDanmaku,
    "LinearScatteredDanmaku": LinearScatteredDanmaku
}

#json形式のステージデータを読み取る関数
def load_stage_data(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def main_loop():
    
    global frame_count,total_score,scene
    player = Player()
    player_bullets=[]
    
    enemies=[]
    enemy_barrages=[]
    stage_data = load_stage_data("STAGE1.json")
    stage_idx=0
    while (1):
        screen.fill((0, 0, 0))
        for event in pygame.event.get():
            if event.type ==  QUIT:  
                pygame.quit()      
                sys.exit()
            if event.type == KEYDOWN:
                if scene == SCENE_START:
                    if event.key == K_SPACE: 
                        # リセット処理
                        player.reset()
                        player_bullets = []
                        enemies = []
                        enemy_barrages = []
                        total_score = 0
                        frame_count = 0
                        scene = SCENE_PLAY
                
                elif scene == SCENE_GAMEOVER or scene == SCENE_CLEAR:
                    if event.key == K_SPACE: 
                        scene = SCENE_START
        if scene == SCENE_START:
            draw_text("DANMAKU GAME", font_large, (255, 255, 255), SCREEN_WIDTH//2, SCREEN_HEIGHT//3)
            draw_text("Press 'SPACE' to Start", font, (200, 200, 200), SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
            draw_text("Move: Arrow Keys or WASD / Shot: Z / Slow: Shift", font, (150, 150, 150), SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100)

        elif scene == SCENE_PLAY:
            if player.hp <= 0:
                player.lives -= 1
                if player.lives >= 0:
                    player.hp = player.hp_max
                    player.invincible_timer = 120 
                else:
                    scene = SCENE_GAMEOVER


            if player.invincible_timer > 0:
                player.invincible_timer -= 1
                
            while stage_idx < len(stage_data) and frame_count >= stage_data[stage_idx]["frame"]:
                spawn_info = stage_data[stage_idx]
                e_class = ENEMY_CLASSES[spawn_info["enemy_type"]]
                ex, ey = spawn_info["x"], spawn_info["y"]
                hp = spawn_info["hp"]
                
                # 弾幕の処理
                raw_barrage = spawn_info["barrage_type"]
                
                if spawn_info["enemy_type"] == "Boss":
                    if(len(enemies)==0):
                        boss_barrage_classes = [BARRAGE_CLASSES[name] for name in raw_barrage]
                        new_enemy = Boss(ex, ey, boss_barrage_classes)
                        new_enemy.max_hp = hp
                        new_enemy.hp = hp
                    else:
                        break
                        
                else:
                    b_class = BARRAGE_CLASSES[raw_barrage]
                    b_instance = b_class()
                    enemy_barrages.append(b_instance) # 弾幕リストに追加（本体消滅後も更新するため）
                    new_enemy = e_class(ex, ey, b_instance, hp=hp)
                
                enemies.append(new_enemy)
                stage_idx += 1  # 次のデータへ
                
                
            
            player.update(player_bullets)
            player_bullets = [b for b in player_bullets if not b.update()]
            for e in enemies[:]:
                if e.update(player.pos):
                    enemies.remove(e)

            for b in enemy_barrages:
                b.update()
                if not b.is_active and len(b.bullets) == 0:
                    enemy_barrages.remove(b)
            collision_check(player, player_bullets, enemies)

            draw_hud(player)
            frame_count += 1
        
        elif scene == SCENE_GAMEOVER:
            draw_text("GAME OVER", font_large, (255, 50, 50), SCREEN_WIDTH//2, SCREEN_HEIGHT//3)
            draw_text(f"FINAL SCORE: {str(total_score).zfill(8)}", font, (255, 255, 255), SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
            draw_text("Press 'SPACE' to Return to Title", font, (200, 200, 200), SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100)
        elif scene == SCENE_CLEAR:
            draw_text("STAGE CLEAR !!", font_large, (50, 255, 50), SCREEN_WIDTH//2, SCREEN_HEIGHT//3)
            draw_text(f"FINAL SCORE: {str(total_score).zfill(8)}", font, (255, 255, 255), SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
            draw_text("Press 'SPACE' to Return to Title", font, (200, 200, 200), SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100)
        pygame.display.update()    
        clock.tick(FPS)

if __name__ == "__main__":
    main_loop()