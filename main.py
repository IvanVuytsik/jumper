import pygame
from pygame import mixer
import random
import os

mixer.init()
pygame.init()

FPS = 60
WIDTH = 400
HEIGHT = 600

SCROLL_THR = 200
GRAVITY = 1
MAX_PLANKS = 10

bg_scroll = 0
scroll = 0
game_over = False
score = 0
fade_counter = 0

if os.path.exists('score.txt'):
    with open('score.txt', 'r') as f:
        high_score = int(f.read())
else:
 high_score = 0

clock = pygame.time.Clock()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Jumper')

# sounds
pygame.mixer.music.load('ballad.mp3')
pygame.mixer.music.set_volume(0.6)
pygame.mixer.music.play(-1, 0.0)
jump_fx = pygame.mixer.Sound('jump.mp3')
jump_fx.set_volume(0.2)

#pics
bg_image = pygame.image.load('img/bg.png').convert_alpha()
bg = pygame.transform.scale(bg_image, (WIDTH*2, HEIGHT))
char_image = pygame.image.load('img/jumper.png').convert_alpha()

plank_img = pygame.image.load('img/plank.png').convert_alpha()


class SpriteSheet():
    def __init__(self, image):
        self.sheet = image

    def get_image(self, frame, width, height, scale, colour):
        image = pygame.Surface((width, height)).convert_alpha()
        image.blit(self.sheet, (0, 0), ((frame * width), 0, width, height))
        image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
        image.set_colorkey(colour)

        return image

bird_img = pygame.image.load('img/birdy.png').convert_alpha()
bird_sheet = SpriteSheet(bird_img)

#colors an texts
PURPLE = (150,50,100)
WHITE = (255,255,255)
BLACK = (0,0,0)

font_s = pygame.font.SysFont('Lucida Sans', 20)
font_l = pygame.font.SysFont('Lucida Sans', 24)
def draw_text(text, font, color, x, y):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

def draw_bg(bg_scroll):
    screen.blit(bg, (0, 0 + bg_scroll))
    screen.blit(bg, (0, -HEIGHT + bg_scroll))

def draw_panel():
    pygame.draw.rect(screen, PURPLE, (0,0, WIDTH, 30))
    pygame.draw.line(screen, WHITE, (0, 30), (WIDTH, 30), 2)
    draw_text('SCORE: ' + str(score), font_s, WHITE, 0, 0)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, SCREEN_W, y, sprite_sheet, scale):
        #animation list
        self.animation_list = []
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()

        pygame.sprite.Sprite.__init__(self)
        self.direction = random.choice([-1, 1])
        if self.direction == -1:
            self.flip = True
        else:
            self.flip = False

        #load img
        animation_steps = 3
        for animation in range(animation_steps):
            image = sprite_sheet.get_image(animation, 90,90, scale, (0, 0, 0)) # image from SpriteSheet class
            image = pygame.transform.flip(image, self.flip, False)
            image.set_colorkey((0, 0, 0))
            self.animation_list.append(image)

        # select first image
        self.image = self.animation_list[self.frame_index]
        self.rect = self.image.get_rect()

        if self.direction == 1:
           self.rect.x = 0
        else:
           self.rect.x = WIDTH
        self.rect.y = y

    def update(self, scroll, SCREEN_W):
        # update animation
        ANIMATION_COOLDOWN = 200
        #update frame
        self.image = self.animation_list[self.frame_index]
        # time passed
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        if self.frame_index >= len(self.animation_list):
            self.frame_index = 0

        self.rect.x += self.direction * 2
        self.rect.y += scroll

        #off screen
        if self.rect.right < 0 or self.rect.left > SCREEN_W:
            self.kill()


class Player():
    def __init__(self, x, y):
        self.image = pygame.transform.scale(char_image, (64, 64))
        self.width = 40
        self.height = 50
        self.rect = pygame.Rect(0,0, self.width, self.height)
        self.rect.center = (x,y)
        self.val_y = 0
        self.flip = False

    def move(self):
        scroll = 0
        dx = 0
        dy = 0

        key = pygame.key.get_pressed()
        if key[pygame.K_a]:
            dx -= 10
            self.flip = False
        if key[pygame.K_d]:
            dx += 10
            self.flip = True

        #gravity
        self.val_y += GRAVITY
        dy += self.val_y

        #edges collisions
        if self.rect.left + dx < 0:
            dx = - self.rect.left
        if self.rect.right + dx > WIDTH:
            dx = WIDTH - self.rect.right

        for p in plank_group:
            if p.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                #above the plank check
                if self.rect.bottom < p.rect.centery:
                    if self.val_y > 0:
                        self.rect.bottom = p.rect.top
                        dy = 0
                        self.val_y = - 20
                        jump_fx.play()

        # temporary collision with the bottom
        # if self.rect.bottom + dy > HEIGHT:
        #     dy = 0
        #     self.val_y = - 20

        # scroll line collisions
        if self.rect.top <= SCROLL_THR:
            if self.val_y < 0:
                    scroll = -dy

        self.rect.x += dx
        self.rect.y += dy + scroll

        #mask
        self.mask = pygame.mask.from_surface(self.image)

        return scroll

    def draw(self):
        #pygame.draw.rect(screen, (255,0,0), self.rect, 2)
        screen.blit(pygame.transform.flip(self.image, self.flip, False), (self.rect.x-12, self.rect.y-15))


#----------------------------------
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, moving):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.transform.scale(plank_img, (width, 20))
        self.rect = self.image.get_rect()
        self.moving = moving
        self.move_counter = random.randint(0, 50)
        self.direction = random.choice([-1, 1])
        self.speed = random.randint(1, 3)
        self.rect.x = x
        self.rect.y = y

    def update(self, scroll):
        # movement if moving
        if self.moving == True:
            self.move_counter += 1
            self.rect.x += self.direction * self.speed
        if self.move_counter >= 100 or self.rect.left < 0 or self.rect.right > WIDTH:
            self.direction *= -1
            self.move_counter = 0

        # update platforms vert position
        self.rect.y += scroll

        if self.rect.top > HEIGHT:
            self.kill()


#--------------------------------------------------------------
jumper = Player(WIDTH//2, HEIGHT // 2)
plank_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()

#starting plank
plank = Platform(WIDTH//2, HEIGHT - 50, 70, False)
plank_group.add(plank)


run = True
while run:
    clock.tick(FPS)

    if game_over == False:
        scroll = jumper.move()
        #print(scroll)
        bg_scroll += scroll
        if bg_scroll >= HEIGHT:
            bg_scroll = 0
        draw_bg(bg_scroll)

        #pygame.draw.line(screen, (255, 255, 255), (0, SCROLL_THR), (WIDTH, SCROLL_THR))

        if len(plank_group) < MAX_PLANKS:
            p_w = random.randint(40, 60)
            p_x = random.randint(0, WIDTH - p_w)
            p_y = plank.rect.y - random.randint(80, 120)
            p_type = random.randint(1, 2)
            if p_type == 1 and score > 500:
                p_moving = True
            else:
                p_moving = False

            plank = Platform(p_x, p_y, p_w, p_moving)
            plank_group.add(plank)

        plank_group.update(scroll)
        # generator enemy
        if len(enemy_group) == 0: #and score > 1500:
            enemy = Enemy(WIDTH, 100, bird_sheet, 0.8)
            enemy_group.add(enemy)

        enemy_group.update(scroll, WIDTH)

        #score
        if scroll > 0:
            score += scroll

        # previous score drawing
        pygame.draw.line(screen, PURPLE,
                         (0, score - high_score + SCROLL_THR),
                         (WIDTH, score - high_score + SCROLL_THR), 3)
        draw_text('HIGH SCORE', font_s, PURPLE, WIDTH - 130, score - high_score + SCROLL_THR)

        draw_panel()

        # draw sprites
        plank_group.draw(screen)
        enemy_group.draw(screen)
        jumper.draw()

        # for enemy in enemy_group:
        #     pygame.draw.rect(screen, WHITE, enemy.rect, 2)

        # game over condition
        if jumper.rect.top > HEIGHT:
           game_over = True
        #check with collision with enemies
        if pygame.sprite.spritecollide(jumper, enemy_group, False):
            if pygame.sprite.spritecollide(jumper, enemy_group, False, pygame.sprite.collide_mask):
               game_over = True
    else:
        if fade_counter < WIDTH:
           fade_counter += 5
           for y in range(0, 6, 2):
               pygame.draw.rect(screen, BLACK, (0, y * 100, fade_counter, HEIGHT //6))
               pygame.draw.rect(screen, BLACK, (WIDTH - fade_counter, (y+1) * 100, WIDTH, HEIGHT //6))
        else:
            draw_text('GAME OVER!', font_l, PURPLE, 130, 200)
            draw_text('SCORE: ' + str(score), font_l, PURPLE, 150, 250)
            draw_text('PRESS SPACE TO PLAY AGAIN', font_l, PURPLE, 40, 300)

            if score > high_score:
                high_score = score
                with open('score.txt', 'w') as f:
                    f.write(str(high_score))

            # reset
            key = pygame.key.get_pressed()
            if key[pygame.K_SPACE]:
                game_over = False
                score = 0
                scroll = 0
                fade_counter = 0
                jumper.rect.center = (WIDTH // 2, HEIGHT // 2)
                plank_group.empty()
                enemy_group.empty()
                #starting plank
                plank = Platform(WIDTH//2, HEIGHT - 50, 70, False)
                plank_group.add(plank)


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            if score > high_score:
                high_score = score
                with open('score.txt', 'w') as f:
                    f.write(str(high_score))
            running = False
            pygame.quit()


    pygame.display.update()






if __name__== "__main__":
    pass