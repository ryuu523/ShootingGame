import pygame 
from pygame.locals import *
from types import SimpleNamespace
from pygame.math import Vector2
import sys
import math
import random

# --- 設定 ---
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 800
FPS = 60

pygame.init()  
screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
pygame.display.set_caption("game")
clock = pygame.time.Clock()

# 共有変数の初期化
frame_count = 0
player_shot_timer = 0 

SCREEN_CENTER = SimpleNamespace(x=SCREEN_WIDTH//2, y=SCREEN_HEIGHT//2)

FPS=60
PLAYER = SimpleNamespace(
    who="p", width=20, height=20,
    pos=Vector2(SCREEN_CENTER.x, SCREEN_HEIGHT-150),
    speed=4, hp=10, hpfull=10,
    bullet=SimpleNamespace(color="blue", radius=5, speed=10, cooldown=10)
)

VEC = SimpleNamespace(LEFT=[-1,0], RIGHT=[1,0], UP=[0,-1], DOWN=[0,1])



class Bullet:
    def __init__(self):
        self.pos=Vector2(0,0)
        self.velocity=Vector2(0,0)
        self.angle=0

    def draw(self):
        pass
    
    def update(self):
        self.pos+=self.velocity
        self.draw()
        return self.collision_field()
    
    def collision_field(self):
        return  not (self.pos.x > 0 and self.pos.x < SCREEN_WIDTH and self.pos.y > 0 and self.pos.y < SCREEN_HEIGHT)
    
    def set_position(self,pos):
        self.pos = pos
    
    def set_velocity(self,velocity):
        self.velocity = velocity
        self.angle = self.velocity.as_polar()[1]

class  Bullet01(Bullet):
    def __init__(self,color,radius):
        super().__init__()
        self.color=color
        self.radius=radius

    def draw(self):
        pygame.draw.circle(screen,self.color,(self.pos.x,self.pos.y),self.radius)

class Barrage:
    def __init__(self) :
        self.bullets = []

    def update(self):
        self.update_bullets()

    def update_bullets(self):
        self.bullets = [b for b in self.bullets if not b.update()]

class Barrage01(Barrage):
    def __init__(self):
        super().__init__()

    def update(self): 
        super().update()
        if(frame_count%2==1):
            bullet= Bullet01("red",10)     
            bullet.set_position(Vector2(PLAYER.pos.x,PLAYER.pos.y))
            angle = random.randint(0, 360)
            vel = Vector2()
            vel.from_polar((5, angle)) 
            bullet.set_velocity(vel)
            self.bullets.append(bullet)
        

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

def operate(my_barrage):
    global player_shot_timer
    pressed_key = pygame.key.get_pressed()
    pressed_mouse= pygame.mouse.get_pressed()
    if pressed_key[K_LEFT] or pressed_key[K_a]: player_move(VEC.LEFT)
    if pressed_key[K_RIGHT] or pressed_key[K_d]:player_move(VEC.RIGHT)
    if pressed_key[K_UP] or pressed_key[K_w]:   player_move(VEC.UP)
    if pressed_key[K_DOWN] or pressed_key[K_s]: player_move(VEC.DOWN)
    if pressed_key[K_z] or pressed_mouse[0]:
            if player_shot_timer <= 0:
                p_bullet = Bullet01(PLAYER.bullet.color, PLAYER.bullet.radius)
                p_bullet.set_position(Vector2(PLAYER.pos.x,PLAYER.pos.y))
                p_bullet.set_velocity(Vector2(0, -PLAYER.bullet.speed))
                my_barrage.bullets.append(p_bullet)
                player_shot_timer = PLAYER.bullet.cooldown
                    
def draw_ui():
    pygame.draw.rect(screen,(100,100,255),(PLAYER.pos.x-PLAYER.width//2,PLAYER.pos.y-PLAYER.height//2,PLAYER.width,PLAYER.height))
    pygame.draw.rect(screen,(0,255,0),(PLAYER.pos.x-PLAYER.width//2,PLAYER.pos.y+PLAYER.height//2,PLAYER.width-(PLAYER.width/PLAYER.hpfull)*(PLAYER.hpfull-PLAYER.hp),10))
def main_loop():
    global frame_count, player_shot_timer
    danmaku= Barrage01()

    while (1):
        screen.fill((0,0,0))       

        for event in pygame.event.get():
            if event.type ==  QUIT:  
                pygame.quit()      
                sys.exit()

        operate(danmaku)
        if player_shot_timer > 0:
            player_shot_timer -= 1

        danmaku.update()

        draw_ui()

        pygame.display.update()     # 画面を更新
        frame_count += 1
        clock.tick(FPS)

if __name__ == "__main__":
    main_loop()