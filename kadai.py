import pygame 
from pygame.locals import *
from types import SimpleNamespace
from pygame.math import Vector2
import sys
import math
import random

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 800
FPS = 60

pygame.init()  
screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
pygame.display.set_caption("game")
clock = pygame.time.Clock()

frame_count = 0
player_shot_timer = 0 
enemies=[]

SCREEN_CENTER = SimpleNamespace(x=SCREEN_WIDTH//2, y=SCREEN_HEIGHT//2)

PLAYER = SimpleNamespace(
    who="p", width=20, height=20,radius=5,
    pos=Vector2(SCREEN_CENTER.x, SCREEN_HEIGHT-150),
    speed=4, hp=10, hpfull=10,
    bullet=SimpleNamespace(color="white", radius=5, speed=10, cooldown=10)
)

VEC = SimpleNamespace(LEFT=[-1,0], RIGHT=[1,0], UP=[0,-1], DOWN=[0,1])


#敵の設定
class Enemy:
    def __init__(self, x, y, hp=3):
        self.pos = Vector2(x, y)
        self.hp = hp
        self.radius = 15
        self.speed = 2
        self.timer = 0

    def update(self):
        # 左右にゆらゆら動く例
        self.pos.x += math.sin(frame_count * 0.05) * 2
        self.pos.y += 0.5 # ゆっくり降りてくる
        
        # 描画
        pygame.draw.circle(screen, (255, 0, 0), (int(self.pos.x), int(self.pos.y)), self.radius)
        # HPバーの簡易表示
        pygame.draw.rect(screen, (255, 0, 0), (self.pos.x-15, self.pos.y-25, 30, 5))
        pygame.draw.rect(screen, (0, 255, 0), (self.pos.x-15, self.pos.y-25, 30 * (self.hp/3), 5))

#弾の設定
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
    def get_position(self):
        return self.pos.copy()
    def get_velocity(self):
        return self.velocity.copy()
    def set_velocity(self,velocity):
        self.velocity = velocity
        self.angle = self.velocity.as_polar()[1]

class ColorBullet(Bullet):
    def __init__(self,color,radius):
        super().__init__()
        self.color=color
        self.radius=radius

    def draw(self):
        pygame.draw.circle(screen,self.color,(self.pos.x,self.pos.y),self.radius)

    def draw(self):
        pygame.draw.circle(screen,self.color,(self.pos.x,self.pos.y),self.radius)

class AngVelBullet(Bullet):
    def __init__(self,color,radius):
        super().__init__()
        self.color=color
        self.radius=radius
        self.angle_speed = 0
        self.speed_multiplier = 1

    def draw(self):
        pygame.draw.circle(screen,self.color,(self.pos.x,self.pos.y),self.radius)
    def update(self):
        self.velocity = self.velocity.rotate(self.angle_speed)
        self.velocity *= self.speed_multiplier
        return super().update()
    def set_spiral(self, angle, speed_up):
        self.angle_speed = angle
        self.speed_multiplier = speed_up
    
class AccelBullet(Bullet):
    def __init__(self,color,radius):
        super().__init__()
        self.color=color
        self.radius=radius
        self.accel=0
        self.spawn_count=frame_count

    def draw(self):
        pygame.draw.circle(screen,self.color,(self.pos.x,self.pos.y),self.radius)
    def update(self):
        if(frame_count-self.spawn_count>=30):
            # 1. 現在の進行方向の向き（単位ベクトル）を取得
            direction = self.velocity.normalize()
            # 2. 向きに加速量を掛けて「加速ベクトル」を作る
            accel_vector = direction * self.accel
            # 3. 速度ベクトルに加算
            self.velocity += accel_vector
            
        return super().update()
    def set_accel(self,accel):
        self.accel=accel

class FirstStopBullet(Bullet):
    def __init__(self,color,radius):
        super().__init__()
        self.color=color
        self.radius=radius
        self.stop_frame=0

    def draw(self):
        pygame.draw.circle(screen,self.color,(self.pos.x,self.pos.y),self.radius)
    def update(self):
        if(frame_count>=self.stop_frame):
            return super().update()
        self.draw()
    def set_stop_frame(self,stop_frame):
        self.stop_frame=stop_frame

#弾幕の設定
class Barrage:
    def __init__(self) :
        self.bullets = []

    def update(self):
        self.update_bullets()

    def update_bullets(self):
        self.bullets = [b for b in self.bullets if not b.update()]

class PlayerDanmaku(Barrage):
    def __init__(self):
        super().__init__()
    def generate(self):
        bullet = ColorBullet(PLAYER.bullet.color, PLAYER.bullet.radius)
        bullet.set_position(Vector2(PLAYER.pos.x,PLAYER.pos.y))
        bullet.set_velocity(Vector2(0, -PLAYER.bullet.speed))
        self.bullets.append(bullet)

class RandomDanmaku(Barrage):
    def __init__(self):
        super().__init__()

    def update(self): 
        super().update()
        if(frame_count%2==1):
            bullet= ColorBullet("red",5)     
            bullet.set_position(Vector2(PLAYER.pos.x,PLAYER.pos.y))
            angle = random.randint(0, 360)
            vel = Vector2()
            vel.from_polar((5, angle)) 
            bullet.set_velocity(vel)
            self.bullets.append(bullet)
        
class OmnidirectionalDanmaku(Barrage):

    def __init__(self):
        super().__init__()
    def update(self): 
        super().update()

        if(frame_count%30 ==0):
            DIV = 64
            for i in range(DIV):
                bullet =ColorBullet("green",5)
                bullet.set_position(Vector2(PLAYER.pos.x,PLAYER.pos.y))
                bullet.set_velocity(Vector2(1, 0).rotate(360 / DIV * i)*5)
                self.bullets.append(bullet)

class UzumakiDanmaku(Barrage):

    def __init__(self):
        super().__init__()
    def update(self): 
        super().update()
        if(frame_count%3 ==0):
            bullet =ColorBullet("blue",5)
            bullet.set_position(Vector2(PLAYER.pos.x,PLAYER.pos.y))
            bullet.set_velocity(Vector2(1, 0).rotate(frame_count*3)*5)
            self.bullets.append(bullet)

class RasenDanmaku(Barrage):
    def __init__(self):
        super().__init__()
    def update(self): 
        super().update()
        if(frame_count%200==0):
            for i in range(2):
                bullet = AngVelBullet("cyan",10)
                if(i==0):
                    bullet.set_position(Vector2(PLAYER.pos.x+30,PLAYER.pos.y))
                else:
                    bullet.set_position(Vector2(PLAYER.pos.x-30,PLAYER.pos.y))
                bullet.set_velocity(Vector2(1, 0).rotate(180*i)*0.5)
                bullet.set_spiral(1.5,1.01)
                self.bullets.append(bullet)
        
        if(frame_count%5==0):
            new_bullets = [] 
            for option_bullet in self.bullets:
                if isinstance(option_bullet,AngVelBullet):
                    bullet = AccelBullet("orange",5)
                    bullet.set_position(option_bullet.get_position())
                    bullet.set_velocity(option_bullet.get_velocity().normalize().rotate(270)*0.001)
                    bullet.set_accel(0.01)
                    new_bullets.append(bullet)
            self.bullets.extend(new_bullets)

class LinearScatteredDanmaku(Barrage):
    def __init__(self):
        super().__init__()
        self.option_angle=0
    def update(self): 
        super().update()
        start_x=random.randint(0,SCREEN_WIDTH)
        end_x=random.randint(0,SCREEN_WIDTH)
        angle=math.degrees(math.atan2(SCREEN_HEIGHT,(end_x-start_x)))
        if(frame_count%400==0):
            bullet = ColorBullet("yellow",5)
            bullet.set_position(Vector2(start_x,0))
            bullet.set_velocity(Vector2(1, 0).rotate(angle)*5)
            self.bullets.append(bullet)
        if(frame_count%4==0):
            new_bullets = [] 
            for option_bullet in self.bullets:
                if isinstance(option_bullet,ColorBullet) and option_bullet.color=="yellow":
                    bullet = FirstStopBullet("gray",5)
                    bullet.set_position(option_bullet.get_position())
                    bullet.set_velocity(Vector2(1, 0).rotate(self.option_angle)*2)
                    bullet.set_stop_frame(120+frame_count)
                    new_bullets.append(bullet)
                    self.option_angle+=30
            self.bullets.extend(new_bullets)

class AimedDanmaku(Barrage):
    def __init__(self):
        super().__init__()
    def update(self): 
        super().update()
        if(frame_count%30==0):
            bullet = ColorBullet("purple",5)
            bullet.set_position(Vector2(PLAYER.pos.x,PLAYER.pos.y))
            direction = Vector2(SCREEN_CENTER.x - PLAYER.pos.x, SCREEN_CENTER.y - PLAYER.pos.y).normalize()
            bullet.set_velocity(direction * 5)
            self.bullets.append(bullet)

def player_move(vec,isShift):
    coe=1
    if(isShift):
        coe=0.3
    PLAYER.pos.x+=vec[0]*PLAYER.speed*coe
    PLAYER.pos.y+=vec[1]*PLAYER.speed*coe
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

def operate(player_b):
    global player_shot_timer
    pressed_key = pygame.key.get_pressed()
    pressed_mouse= pygame.mouse.get_pressed()
    isShift=pressed_key[K_LSHIFT] or pressed_key[K_RSHIFT]
    if pressed_key[K_LEFT] or pressed_key[K_a]: player_move(VEC.LEFT,isShift)
    if pressed_key[K_RIGHT] or pressed_key[K_d]:player_move(VEC.RIGHT,isShift)
    if pressed_key[K_UP] or pressed_key[K_w]:   player_move(VEC.UP,isShift)
    if pressed_key[K_DOWN] or pressed_key[K_s]: player_move(VEC.DOWN,isShift)
    if pressed_key[K_z] or pressed_mouse[0]:
        if player_shot_timer <= 0:
            player_b.generate()
            player_shot_timer=PLAYER.bullet.cooldown
      
def draw_ui():
    pressed_key = pygame.key.get_pressed()
    pygame.draw.rect(screen,(255,255,255,0.5),(PLAYER.pos.x-PLAYER.width//2,PLAYER.pos.y-PLAYER.height//2,PLAYER.width,PLAYER.height))
    if(pressed_key[K_RSHIFT] or pressed_key[K_LSHIFT]):
        pygame.draw.circle(screen,(100,100,255,0.5),(PLAYER.pos.x,PLAYER.pos.y),PLAYER.radius)        
    pygame.draw.rect(screen,(0,255,0),(PLAYER.pos.x-PLAYER.width//2,PLAYER.pos.y+PLAYER.height//2,PLAYER.width-(PLAYER.width/PLAYER.hpfull)*(PLAYER.hpfull-PLAYER.hp),10))
def collision(player_b):
    global enemies
    for b in player_b.bullets[:]:
        for e in enemies[:]:
            dist = b.pos.distance_to(e.pos)
            if dist < b.radius + e.radius:
                e.hp -= 1 #ダメージ量
                if b in player_b.bullets: player_b.bullets.remove(b)
                if e.hp <= 0:#死亡処理
                    if e in enemies: enemies.remove(e)

    for e in enemies:
        dist = PLAYER.pos.distance_to(e.pos)
        if dist < PLAYER.radius + e.radius:
            PLAYER.hp -= 1 #ダメージ量

def main_loop():
    
    global frame_count, player_shot_timer

    player_b=PlayerDanmaku()
    random_b= RandomDanmaku()
    omnidirectional_b=OmnidirectionalDanmaku()
    beam_b=UzumakiDanmaku()
    rasen_b=RasenDanmaku()
    linearScattered_b=LinearScatteredDanmaku()
    aimed_b=AimedDanmaku()

    while (1):
        screen.fill((0,0,0))       

        for event in pygame.event.get():
            if event.type ==  QUIT:  
                pygame.quit()      
                sys.exit()
        if frame_count % 100 == 0:
            enemies.append(Enemy(random.randint(50, SCREEN_WIDTH-50), -50))
        operate(player_b)
        if player_shot_timer > 0:
            player_shot_timer -= 1

        player_b.update()
        random_b.update()
        omnidirectional_b.update()
        beam_b.update()
        rasen_b.update()
        linearScattered_b.update()
        aimed_b.update()

        for e in enemies[:]:
            e.update()
            if e.pos.y > SCREEN_HEIGHT + 50: # 画面外に出たら削除
                enemies.remove(e)

        collision(player_b)
        draw_ui()

        pygame.display.update()    
        frame_count += 1
        clock.tick(FPS)

if __name__ == "__main__":
    main_loop()