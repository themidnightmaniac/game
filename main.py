import pygame
from math import atan2, degrees
from os.path import join
from os import walk
from random import randint
from  pytmx.util_pygame import load_pygame
from random import randint


WIN_W, WIN_H, = 1920, 1080
TILE_SIZE = 64
SHOOTING_COOLDOWN = 150
BULLET_SPEED = 1000
FPS = 120

class AllSprites(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.Vector2(0,0)

    def draw(self, target_pos):
        self.offset.x = -(target_pos[0] - WIN_W //2)
        self.offset.y = -(target_pos[1] - WIN_H //2)
        for sprite in self:
            self.display_surface.blit(sprite.image, sprite.rect.topleft + self.offset)

class Sprite(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(topleft = pos)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, surf, pos, direction, groups, angle):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(center = pos)
        self.bullet_surf = self.image
        self.angle = angle


        self.direction = direction
        self.speed = BULLET_SPEED

    def rotate_bullet(self):
        self.image = pygame.transform.rotozoom(self.bullet_surf, self.angle, 1)
        self.rect = self.image.get_rect(center = self.rect.center)

    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt
        self.rotate_bullet()

class CollisionSprite(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(topleft = pos)

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, collision_sprites):
        super().__init__(groups)
        self.image = pygame.image.load(join('images', 'player.png')).convert_alpha()
        self.player_surf = self.image
        self.rect = self.image.get_frect(center = pos)
        self.hitbox_rect = self.rect.inflate(0, 0)

        self.direction = pygame.math.Vector2()
        self.speed = 500
        self.collision_sprites = collision_sprites

        self.pos = pygame.Vector2(WIN_W / 2, WIN_H / 2)

    def get_direction(self):
        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        self.rotation = (mouse_pos - self.pos).normalize()

    def rotate(self):
        self.angle = degrees(atan2(self.rotation.x, self.rotation.y)) + 180
        self.image = pygame.transform.rotozoom(self.player_surf, self.angle, 1)
        self.rect = self.image.get_rect(center = self.hitbox_rect.center)

    def input(self):
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_d]) - int(keys[pygame.K_a])
        self.direction.y = int(keys[pygame.K_s]) - int(keys[pygame.K_w])
        self.direction = self.direction.normalize() if self.direction else self.direction

    def move(self, dt):
        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self.collision('horizontal')
        self.hitbox_rect.y += self.direction.y * self.speed * dt
        self.collision('vertical')
        self.rect.center = self.hitbox_rect.center

    def collision(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox_rect):
                if direction == 'horizontal':
                    if self.direction.x > 0: self.hitbox_rect.right = sprite.rect.left
                    if self.direction.x < 0: self.hitbox_rect.left = sprite.rect.right
                else:
                    if self.direction.y > 0: self.hitbox_rect.bottom = sprite.rect.top
                    if self.direction.y < 0: self.hitbox_rect.top = sprite.rect.bottom

    def update(self, dt):
        self.get_direction()
        self.rotate()
        self.input()
        self.move(dt)

class Game():
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("yo")
        self.clock = pygame.time.Clock()
        self.running = True
        self.bullet_surf = pygame.image.load(join('images', 'bullet.png')).convert_alpha()

        self.all_sprites = AllSprites()
        self.collision_sprites =  pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()

        self.setup()

        self.can_shoot = True
        self.shoot_time = 0
        self.gun_cooldown = SHOOTING_COOLDOWN

    def load_images(self):
        self.bullet_surf = pygame.image.load(join('images', 'bullet.png')).convert_alpha()

    def input(self):
        if pygame.mouse.get_pressed()[0] and self.can_shoot:
            pos = self.player.rect.center + self.player.direction * 50
            Bullet(self.bullet_surf, pos, self.player.rotation, (self.all_sprites, self.bullet_sprites), self.player.angle)
            self.can_shoot = False
            self.shoot_time = pygame.time.get_ticks()

    def gun_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.shoot_time >= self.gun_cooldown:
                self.can_shoot = True

    def setup(self):
        map = load_pygame(join('level', 'level.tmx'))

        for x, y, image in map.get_layer_by_name('Floor').tiles(): 
            Sprite((x * TILE_SIZE ,y * TILE_SIZE), image, self.all_sprites)

        for obj in map.get_layer_by_name('Objects'):
            CollisionSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))

        for obj in map.get_layer_by_name('Collisions'):
            CollisionSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), self.collision_sprites)

        for obj in map.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player((obj.x,obj.y), self.all_sprites, self.collision_sprites)
                
    def check_bullet_collisions(self):
        for bullet in self.bullet_sprites:
            # Check if the bullet collides with any CollisionSprite
            if pygame.sprite.spritecollideany(bullet, self.collision_sprites):
                bullet.kill()  # Remove the bullet if it collides with a CollisionSprite

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
             
            self.gun_timer()
            self.input()

            self.check_bullet_collisions()

            self.display_surface.fill('black')
            self.all_sprites.draw(self.player.rect.center)

            self.all_sprites.update(dt)
            pygame.display.update()
    
        pygame.quit()

if __name__ == '__main__':
    game = Game()
    game.run()
