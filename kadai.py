import pygame 
from pygame.locals import *
from types import SimpleNamespace
import sys
import math
import random

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 800
SCREEN_CENTER=SimpleNamespace(
    x=SCREEN_WIDTH//2,
    y=SCREEN_HEIGHT//2
)
FPS=60
PLAYER=SimpleNamespace(
    who="p",
    width=20,
    height=20,
    pos=SimpleNamespace(
        x=SCREEN_CENTER.x,
        y=SCREEN_HEIGHT-50-100
    ),
    speed=3,
    atk=5,
    hp=10,
    hpfull=10,
    bullet=SimpleNamespace(
        color="blue",
        width=10,
        height=10,
        speed=10,
        cooldown=10
    )
)
BOSS=SimpleNamespace(
    who="e",
    width=200,
    height=200,
    pos=SimpleNamespace(
        x=SCREEN_CENTER.x,
        y=0+200//2+100
    ),
    speed=10,
    atk=1,
    hp=500,
    hpfull=500,
    bullet=SimpleNamespace(
        color="red",
        width=10,
        height=10,
        speed=1,

    )
)

VEC=SimpleNamespace(
    LEFT=[-1,0],
    RIGHT=[1,0],
    UP=[0,-1],
    DOWN=[0,1]
)
# スクリーン内にあるかどうか
def is_in_screen(x,y):
    return x>=0 and y>=0 and x<=SCREEN_WIDTH and y<=SCREEN_HEIGHT
# 点1から点2への角度を求める
def get_angle(x1, y1, x2, y2):
    return math.atan2(y2 - y1, x2 - x1)

class Bullet:
    def __init__(self,who,x,y,config,direction):
        self.who=who
        self.x=x
        self.y=y
        self.width=config.width
        self.height=config.height
        self.speed=config.speed
        self.color=config.color
        self.direction=direction
        self.is_alive=True

    def draw(self,screen):
        pygame.draw.circle(screen,self.color,(self.x,self.y),self.width//2)
    def update(self):
        self.x+=self.speed*math.cos(self.direction)
        self.y+=self.speed*math.sin(self.direction)

        if not is_in_screen(self.x,self.y):
            self.is_alive=False
    @property
    def rect(self):
        return pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)
def player_move(vec):
    PLAYER.pos.x+=vec[0]*PLAYER.speed
    PLAYER.pos.y+=vec[1]*PLAYER.speed
    #右壁
    if PLAYER.pos.x+PLAYER.width//2>SCREEN_WIDTH:
        PLAYER.pos.x=SCREEN_WIDTH-PLAYER.width//2
    #左壁
    if PLAYER.pos.x-PLAYER.width//2<0:
        PLAYER.pos.x=PLAYER.width//2
    #下壁
    if PLAYER.pos.y+PLAYER.height//2>SCREEN_HEIGHT:
        PLAYER.pos.y=SCREEN_HEIGHT-PLAYER.height//2
    #上壁
    if PLAYER.pos.y-PLAYER.height//2<0:
        PLAYER.pos.y=PLAYER.height//2

def boss_attack_pattern(bullets, frame_count):
    # 120フレーム（約2秒）に1回攻撃を切り替える例
    cycle = (frame_count // 120) % 3 

    if frame_count % 30 == 0: # 0.5秒に1回発射
        if cycle == 0:
            # パターン1: 自機狙い 3連射
            angle = get_angle(BOSS.pos.x, BOSS.pos.y, PLAYER.pos.x, PLAYER.pos.y)
            for i in range(-5, 5): # -1, 0, 1
                offset = i * 0.1 # 少し角度をずらす
                bullets.append(Bullet("e", BOSS.pos.x, BOSS.pos.y, BOSS.bullet, angle + offset))
        
        elif cycle == 1:
            # パターン2: 全方位弾 (360度)
            count = 36 # 12方向に発射
            for i in range(count):
                angle = (2 * math.pi / count) * i
                bullets.append(Bullet("e", BOSS.pos.x, BOSS.pos.y, BOSS.bullet, angle))

        elif cycle == 2:
            # パターン3: ランダムばらまき
            for _ in range(30):
                angle = math.pi * random.random() # 下方向(0~π)にランダム
                bullets.append(Bullet("e", BOSS.pos.x, BOSS.pos.y, BOSS.bullet, angle))

def main_loop():
    pygame.init()  
    screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
    pygame.display.set_caption("game")
    clock = pygame.time.Clock()

    bullets=[]
    frame_count=0
    player_shot_timer = 0 

    while (1):
        screen.fill((0,0,0))        # 画面を黒色に塗りつぶし
        
        
        # イベント処理
        for event in pygame.event.get():
            if event.type ==  QUIT:  # 閉じるボタンが押されたら終了
                pygame.quit()       # Pygameの終了(画面閉じられる)
                sys.exit()

        pressed_key = pygame.key.get_pressed()
        pressed_mouse= pygame.mouse.get_pressed()
        if pressed_key[K_LEFT] or pressed_key[K_a]: player_move(VEC.LEFT)
        if pressed_key[K_RIGHT] or pressed_key[K_d]:player_move(VEC.RIGHT)
        if pressed_key[K_UP] or pressed_key[K_w]:   player_move(VEC.UP)
        if pressed_key[K_DOWN] or pressed_key[K_s]: player_move(VEC.DOWN)
        if pressed_key[K_z] or pressed_mouse[0]:
            if player_shot_timer <= 0:
                new_bullet = Bullet(PLAYER.who, PLAYER.pos.x, PLAYER.pos.y, PLAYER.bullet, -math.pi/2)
                bullets.append(new_bullet)
                player_shot_timer = PLAYER.bullet.cooldown 

        if player_shot_timer > 0:
            player_shot_timer -= 1

        boss_attack_pattern(bullets, frame_count)

        for b in bullets:
            b.update()

        boss_rect = pygame.Rect(BOSS.pos.x - BOSS.width//2, BOSS.pos.y - BOSS.height//2, BOSS.width, BOSS.height)

        for b in bullets:
            if b.who == "p" and b.is_alive:
                if b.rect.colliderect(boss_rect):
                    BOSS.hp -= PLAYER.atk
                    b.is_alive = False 
            if b.who == "e" and b.is_alive:
                player_rect = pygame.Rect(PLAYER.pos.x - PLAYER.width//2, 
                                        PLAYER.pos.y - PLAYER.height//2, 
                                        PLAYER.width, PLAYER.height)
                if b.rect.colliderect(player_rect):
                    PLAYER.hp -= BOSS.atk
                    b.is_alive = False

        for b in bullets:
            b.draw(screen)

        bullets = [b for b in bullets if b.is_alive]

        pygame.draw.rect(screen,(100,100,255),(PLAYER.pos.x-PLAYER.width//2,PLAYER.pos.y-PLAYER.height//2,PLAYER.width,PLAYER.height))
        pygame.draw.rect(screen,(0,255,0),(PLAYER.pos.x-PLAYER.width//2,PLAYER.pos.y+PLAYER.height//2,PLAYER.width-(PLAYER.width/PLAYER.hpfull)*(PLAYER.hpfull-PLAYER.hp),10))
        if(BOSS.hp>0):
            pygame.draw.rect(screen,(255,255,0),(BOSS.pos.x-BOSS.width//2,BOSS.pos.y-BOSS.height//2,BOSS.width,BOSS.height))
            pygame.draw.rect(screen,(0,255,0),(0,0,SCREEN_WIDTH-(SCREEN_WIDTH/BOSS.hpfull)*(BOSS.hpfull-BOSS.hp),20))

        pygame.display.update()     # 画面を更新
        frame_count += 1
        clock.tick(FPS)
        if(PLAYER.hp<=0):
            break

if __name__ == "__main__":
    main_loop()