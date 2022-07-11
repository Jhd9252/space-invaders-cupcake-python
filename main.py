# -*- coding: utf-8 -*-
"""
Created on Sun Jul 10 21:00:30 2022

@author: jhd9252
Source: https://www.youtube.com/watch?v=Q-__8Xw9KTM&ab_channel=TechWithTim

To Add:
    power-ups
    Bosses every 3 levels (just more health)
    save high score + time + date + name serialization? writing to text?

"""

# imports
import pygame
import os
import time
import random

# pygame font for window
pygame.font.init()

# creating pygame window with width height
WIDTH, HEIGHT = 750, 750
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Space Shooter Tutorial')


# loading ship image assets in order to display them to the screen
RED_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_red_small.png"))
BLUE_SHIP = pygame.image.load(os.path.join('assets','pixel_ship_blue_small.png'))
GREEN_SHIP = pygame.image.load(os.path.join('assets','pixel_ship_green_small.png'))

# player image asset
YELLOW_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_yellow.png"))

# loading laser image assets
RED_LASER = pygame.image.load(os.path.join('assets','pixel_laser_red.png'))
BLUE_LASER = pygame.image.load(os.path.join('assets','pixel_laser_blue.png'))
GREEN_LASER = pygame.image.load(os.path.join('assets','pixel_laser_green.png'))
YELLOW_LASER = pygame.image.load(os.path.join('assets','pixel_laser_yellow.png'))

# loading background image asset
BG = pygame.transform.scale(pygame.image.load(os.path.join("assets", "background-black.png")), (WIDTH, HEIGHT))

class Laser:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)
        
    def draw(self, window):
        WINDOW.blit(self.img, (self.x, self.y))
        
    def move(self, vel):
        self.y += vel # sign of vel determines moving up or down
        
    def off_screen(self, height):
        return not (self.y <= height and self.y >= 0)
    
    def collision(self, obj):
        return collide(self,obj)
    
    

# abstract class for player ships and enemy ships
class Ship:
    CD = 30 # utilizing 60 FPS, this equates to half a second 
    def __init__(self, x, y, health = 100):
        self.x = x
        self.y = y
        self.health = health
        self.ship_img = None # later instantiation
        self.laser_img = None # later instantiation
        self.lasers = [] # tracking projectiles
        self.cooldown = 0 # stops spamming of lasers with cooldown timer
        
    def draw(self, window):
        WINDOW.blit(self.ship_img, (self.x, self.y)) # rect to fill with ship img
        for laser in self.lasers:
            laser.draw(window)
            
    def move_lasers(self, vel, obj):
        self.cooldown_incre()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(obj):
                obj.health -= 10
                self.lasers.remove(laser)
        
    def get_width(self): # getter width
        return self.ship_img.get_width()
    
    def get_height(self): # getter height
        return self.ship_img.get_height()
    
    def cooldown_incre(self):
        if self.cooldown >= self.CD:
            self.cooldown = 0
        elif self.cooldown > 0:
            self.cooldown += 1
        
    def shoot(self): # if counter == 0, create laser, set cooldown = 1
        if self.cooldown == 0:
            laser = Laser(self.x, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cooldown = 1
            
    
        
class Player(Ship):
    def __init__(self, x, y, health=100):
        super().__init__(x,y,health) # uses Ship initialization method
        self.ship_img = YELLOW_SHIP
        self.laser_img = YELLOW_LASER
        self.mask= pygame.mask.from_surface(self.ship_img) # pixel-perfect collisions
        self.max_health = health
        
    def move_lasers(self, vel, objs):
        self.cooldown_incre()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                for obj in objs:                    
                    if laser.collision(obj):
                        objs.remove(obj)
                        if laser in self.lasers: # in case laser removed in other cases
                            self.lasers.remove(laser)
                        
    def healthbar(self, window):
        # two rectangles as red and green overlapping
        # green bar receeds according to percentage health
       pygame.draw.rect(window, (255,0,0), (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width(), 10))
       pygame.draw.rect(window, (0,255,0), (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width() * (self.health/self.max_health), 10))
       
    def draw(self, window):
        super().draw(window)
        self.healthbar(window)
        
        
        
class Enemy(Ship):
    COLOR_MAP = {'red':(RED_SHIP, RED_LASER), 'blue':(BLUE_SHIP, BLUE_LASER), 'green':(GREEN_SHIP, GREEN_LASER)}
    
    def __init__(self, x, y, color, health = 100):
        super().__init__(x, y, health)
        self.ship_img, self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)
        
    def move(self, vel): # enemy ships spawn random x  and move down
        self.y += vel
        
    def shoot(self): # if counter == 0, create laser, set cooldown = 1
        if self.cooldown == 0:
            laser = Laser(self.x - 20, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cooldown = 1

def collide(obj1, obj2):
    # using mask to determine if collision occured / overlapping in pygame
    offset_x = obj2.x - obj1.x # determines offset of x coord
    offset_y = obj2.y - obj1.y # determines offset of y coord
    # checks collisions using obj1 and obj2 masks using the offsets
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) != None
    
def main():
    run = True # boolean tracking status of game 
    FPS = 60 # determines the tracking per second of frames (collisions, movement, etc)
    clock = pygame.time.Clock() # pygame object to track time ticks
    level = 0 
    lives = 5
    player_vel = 7 # every key press moves 5 pixels
    main_font = pygame.font.SysFont('comicsans', 30)
    enemies = []
    enemy_vel = 1
    wave_length = 5 # per level
    lost = False
    lost_count = 1
    laser_vel = 5
    player = Player(100, 400)
    
    def redraw_window():
        WINDOW.blit(BG, (0,0)) # covers previous window with background
        level_label = main_font.render("Level: " + str(level), 1, (255, 0, 0))
        lives_label = main_font.render("Lives: " + str(lives), 1, (255, 0, 0))
        WINDOW.blit(lives_label, (10,10))
        WINDOW.blit(level_label, (WIDTH-level_label.get_width() - 10, 10))
        
        for enemy in enemies:
            enemy.draw(WINDOW)
            
        player.draw(WINDOW)
        
        if lost:
            lost_label = main_font.render('You Lost',1, (255,255,255))
            WINDOW.blit(lost_label, (WIDTH/2 - lost_label.get_width()/2, HEIGHT/2))
        
        pygame.display.update() # update the display over new BG
        
        
    while run:
        clock.tick(FPS)
        redraw_window()
        if lives <= 0 or player.health <= 0:
            lost = True
            lost_count += 1
            
        if lost:
            if lost_count > FPS * 3: # this loop ensures lost screen stays til game end
                run = False # once counter is done, end game
                pygame.display.quit()
                pygame.quit()
            else:
                continue # loss screen stays
        if len(enemies) == 0:
            level += 1
            enemy_vel += 1
            wave_length += 1
            for i in range(wave_length):
                # since we want enemies to roll onto the screen, and not spawn fully
                # spawn enemies in negative y coord
                enemy = Enemy(random.randrange(50, WIDTH-100), random.randrange(-1500, -100), random.choice(['red','blue','green']))
                enemies.append(enemy)
        # for each time tick 
        for event in pygame.event.get():
            # check if user wants to exit game 
            if event.type == pygame.QUIT:
                run = False
                pygame.display.quit()
                pygame.quit()
                
        # tracking and moving according to key presses
        # check bounds
        keys = pygame.key.get_pressed() # get dict of key presses
        if keys[pygame.K_a] and player.x - player_vel > 0 : # move left
            player.x -= player_vel
        if keys[pygame.K_d] and player.x + player_vel + player.get_width()< WIDTH: # move right
            player.x += player_vel
        if keys[pygame.K_w] and player.y - player_vel > 0: # move up
            player.y -= player_vel
        if keys[pygame.K_s] and player.y + player_vel + player.get_height() + 15< HEIGHT: # move down
            player.y += player_vel
        if keys[pygame.K_SPACE]:
            player.shoot()
            
        # enemy actions + lasers + collisions  
        for enemy in enemies[:]:
            enemy.move(enemy_vel)
            enemy.move_lasers(laser_vel, player)
            
            if random.randrange(0, 4*60) == 1:
                enemy.shoot()
                
            if collide(enemy, player):
                enemies.remove(enemy)
                player.health -= 10
            
            elif enemy.y + enemy.get_height() > HEIGHT:
                lives -= 1
                enemies.remove(enemy)
              
        player.move_lasers(-laser_vel, enemies)

def menu():
    title_font = pygame.font.SysFont('comicsan', 70)
    run = True
    while run:
        WINDOW.blit(BG, (0,0))
        title_label = title_font.render('Click To Begin', 1, (255,255,255))
        WINDOW.blit(title_label, (WIDTH/2-title_label.get_width()/2,title_label.get_height()/2))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                main()
                
    pygame.quit()
    quit()
                
menu()