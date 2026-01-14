import pygame 
from pygame.locals import *
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

#プレイヤーの設定
class Player:
    def __init__(self):
        self.pos = Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)
        self.width = 20
        self.height = 20
        self.radius = 5  # 当たり判定用
        self.speed = 4
        self.hp = 10
        self.hp_max = 10
        self.shot_timer = 0
        self.cooldown = 8
        self.bullet_speed = 10

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
        self.move()
        self.draw()
        # ショット処理
        if self.shot_timer > 0:
            self.shot_timer -= 1
            
        pressed_key = pygame.key.get_pressed()
        pressed_mouse = pygame.mouse.get_pressed()
        if (pressed_key[K_z] or pressed_mouse[0]) and self.shot_timer <= 0:
            self.shoot(player_bullets)
            self.shot_timer = self.cooldown

    def shoot(self, player_bullets):
        bullet = ColorBullet("white", 5)
        bullet.set_position(Vector2(self.pos.x, self.pos.y))
        bullet.set_velocity(Vector2(0, -self.bullet_speed))
        player_bullets.append(bullet)

    def draw(self):
        # プレイヤー本体
        pygame.draw.rect(screen, (255, 255, 255), 
                         (self.pos.x - self.width//2, self.pos.y - self.height//2, self.width, self.height))
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
        self.speed = 2
        self.timer = 0
        self.barrage=barrage

    def update(self,target_pos):
        # 左右にゆらゆら動く例
        self.pos.x += math.sin(frame_count * 0.05) * 2
        self.pos.y += 0.5 # ゆっくり降りてくる
        self.draw()
        
        # 弾幕の更新
        # 引数の数に合わせて呼び出しを分ける
        if isinstance(self.barrage, AimedDanmaku):
            self.barrage.update(self.pos, target_pos)
        elif isinstance(self.barrage, LinearScatteredDanmaku):
            self.barrage.update()
        else:
            self.barrage.update(self.pos)
        return self.pos.y > SCREEN_HEIGHT + 50 or self.hp <= 0

    def draw(self):
        # 描画
        pygame.draw.circle(screen, (255, 0, 0), (int(self.pos.x), int(self.pos.y)), self.radius)
        # HPバーの簡易表示
        pygame.draw.rect(screen, (255, 0, 0), (self.pos.x-15, self.pos.y-25, 30, 5))
        pygame.draw.rect(screen, (0, 255, 0), (self.pos.x-15, self.pos.y-25, 30 * (self.hp/3), 5))

#弾の設定
class Bullet:
    def __init__(self, pos=None, velocity=None, radius=5, color=(255,0,0)):
        self.pos = Vector2(pos) if pos else Vector2(0,0)
        self.velocity = Vector2(velocity) if velocity else Vector2(0,0)
        self.radius = radius
        self.color = color
        self.angle = self.velocity.as_polar()[1] if self.velocity.length() > 0 else 0

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)
    
    def update(self):
        self.pos+=self.velocity
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
        if(frame_count>=self.stop_frame):
            return super().update()
        return False
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

class RandomDanmaku(Barrage):
    def __init__(self):
        super().__init__()

    def update(self,start_pos): 
        super().update()
        if(frame_count%2==1):
            bullet= ColorBullet("red",5)     
            bullet.set_position(Vector2(start_pos.x,start_pos.y))
            angle = random.randint(0, 360)
            vel = Vector2()
            vel.from_polar((5, angle)) 
            bullet.set_velocity(vel)
            self.bullets.append(bullet)
        
class OmnidirectionalDanmaku(Barrage):

    def __init__(self):
        super().__init__()
    def update(self,start_pos): 
        super().update()

        if(frame_count%30 ==0):
            DIV = 64
            for i in range(DIV):
                bullet =ColorBullet("red",5)
                bullet.set_position(Vector2(start_pos.x,start_pos.y))
                bullet.set_velocity(Vector2(1, 0).rotate(360 / DIV * i)*5)
                self.bullets.append(bullet)

class UzumakiDanmaku(Barrage):

    def __init__(self):
        super().__init__()
    def update(self,start_pos): 
        super().update()
        if(frame_count%3 ==0):
            bullet =ColorBullet("red",5)
            bullet.set_position(Vector2(start_pos.x,start_pos.y))
            bullet.set_velocity(Vector2(1, 0).rotate(frame_count*3)*5)
            self.bullets.append(bullet)

class RasenDanmaku(Barrage):
    def __init__(self):
        super().__init__()
    def update(self,start_pos): 
        super().update()
        if(frame_count%200==0):
            for i in range(2):
                bullet = AngVelBullet("red",5)
                if(i==0):
                    bullet.set_position(Vector2(start_pos.x+30,start_pos.y))
                else:
                    bullet.set_position(Vector2(start_pos.x-30,start_pos.y))
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
            bullet = ColorBullet("red",5)
            bullet.set_position(Vector2(start_x,0))
            bullet.set_velocity(Vector2(1, 0).rotate(angle)*5)
            self.bullets.append(bullet)
        if(frame_count%4==0):
            new_bullets = [] 
            for option_bullet in self.bullets:
                if isinstance(option_bullet,ColorBullet) and option_bullet.color=="yellow":
                    bullet = FirstStopBullet("red",5)
                    bullet.set_position(option_bullet.get_position())
                    bullet.set_velocity(Vector2(1, 0).rotate(self.option_angle)*2)
                    bullet.set_stop_frame(120+frame_count)
                    new_bullets.append(bullet)
                    self.option_angle+=30
            self.bullets.extend(new_bullets)

class AimedDanmaku(Barrage):
    def __init__(self):
        super().__init__()
    def update(self,start_pos,target_pos): 
        super().update()
        if(frame_count%30==0):
            bullet = ColorBullet("red",5)
            bullet.set_position(Vector2(start_pos.x,start_pos.y))
            direction = Vector2(target_pos.x - start_pos.x, target_pos.y - start_pos.y).normalize()
            bullet.set_velocity(direction * 5)
            self.bullets.append(bullet)

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
def collision_check(player,player_bullets,enemies):
       # 1. プレイヤーの弾 vs 敵
    for b in player_bullets[:]:
        for e in enemies[:]:
            if b.pos.distance_to(e.pos) < b.radius + e.radius:
                e.hp -= 1
                if b in player_bullets: player_bullets.remove(b)
                if e.hp <= 0: enemies.remove(e)

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
def main_loop():
    
    global frame_count
    player = Player()
    player_bullets=[]
    
    enemies=[]
    
    barrage_types=[RandomDanmaku,OmnidirectionalDanmaku,UzumakiDanmaku,RasenDanmaku,AimedDanmaku]

    while (1):
        screen.fill((0, 0, 0))

        for event in pygame.event.get():
            if event.type ==  QUIT:  
                pygame.quit()      
                sys.exit()
        if frame_count % 300 == 0:
            barrage_choice = random.choice(barrage_types)()
            enemies.append(Enemy(random.randint(50, SCREEN_WIDTH-50), -50, barrage_choice))
        
        player.update(player_bullets)
        player_bullets = [b for b in player_bullets if not b.update()]
        for e in enemies[:]:
            if e.update(player.pos):
                enemies.remove(e)

        collision_check(player, player_bullets, enemies)

        pygame.display.update()    
        frame_count += 1
        clock.tick(FPS)

if __name__ == "__main__":
    main_loop()