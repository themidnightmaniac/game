from math import atan2, degrees
from os.path import join
import pygame
from  pytmx.util_pygame import load_pygame


WIN_W, WIN_H, = 800, 600
TILE_SIZE = 64
SHOOTING_COOLDOWN = 150
BULLET_SPEED = 2000
FPS = 60
BULLET_OFFSET = pygame.Vector2(10,10)

class PickUps(pygame.sprite.Sprite):
    """Manages the animation and displaying of the pickups"""
    def __init__(self, pos, name, surf, groups):
        super().__init__(groups)
        self.image = pygame.Surface((50,50))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_frect(topleft = pos)
        self.name = name

    def collect(self):
        """Handle the pickup collection logic here"""
        print(f"Picked up: {self.name}")
        self.kill()  # Remove the pickup from the game

class AllSprites(pygame.sprite.LayeredUpdates):
    """Groups sprites for easier bliting and changes their drawing method"""
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.Vector2(0,0)

    def draw(self, target_pos):
        """Custom drawing method"""
        self.offset.x = -(target_pos[0] - WIN_W //2)
        self.offset.y = -(target_pos[1] - WIN_H //2)
        for sprite in self:
            self.display_surface.blit(sprite.image, sprite.rect.topleft + self.offset)

class Sprite(pygame.sprite.Sprite):
    """Aling sprites in the same way as in tiled"""
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(topleft = pos)

class Bullet(pygame.sprite.Sprite):
    """Manages the movement and displaying of bullets"""
    def __init__(self, surf, pos, direction, groups, angle):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(center = pos)
        self.bullet_surf = self.image
        self.angle = angle


        self.direction = direction
        self.speed = BULLET_SPEED

    def rotate(self):
        """Rotates the bullet sprite so it is aligned with the angle it was fired from"""
        self.image = pygame.transform.rotozoom(self.bullet_surf, self.angle, 1)
        self.rect = self.image.get_rect(center = self.rect.center)

    def update(self, dt):
        """Calls the rotate method and THEN moves the bullet"""
        self.rotate()
        self.rect.center += self.direction * self.speed * dt

class CollisionSprite(pygame.sprite.Sprite):
    """Groups all sprites that have collisions"""
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(topleft = pos)

class Player(pygame.sprite.Sprite):
    """Manages player movement, direction, rotation, and collision"""
    def __init__(self, pos, groups, collision_sprites):
        super().__init__(groups)
        self.image = pygame.image.load(join('images', 'player.png')).convert_alpha()
        self.player_surf = self.image
        self.rect = self.image.get_frect(center = pos)
        self.hitbox_rect = self.rect.inflate(0, 0)
        self.rotation = 0
        self.angle = 0
        self.direction = pygame.Vector2()
        self.speed = 500
        self.collision_sprites = collision_sprites

        self.pos = pygame.Vector2(WIN_W / 2, WIN_H / 2)

    def get_direction(self):
        """Determines the direction which the player is facing relative to the mouse"""
        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        self.rotation = (mouse_pos - self.pos).normalize()

    def rotate(self):
        """Rotates the player sprite so it is aligned to the mouse"""
        self.angle = degrees(atan2(self.rotation.x, self.rotation.y)) + 180
        self.image = pygame.transform.rotozoom(self.player_surf, self.angle, 1)
        self.rect = self.image.get_rect(center = self.hitbox_rect.center)

    def input(self):
        """Determines the player movement direction"""
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_d]) - int(keys[pygame.K_a ])
        self.direction.y = int(keys[pygame.K_s]) - int(keys[pygame.K_w])
        self.direction = self.direction.normalize() if self.direction else self.direction

    def move(self, dt):
        """Moves player using values from self.input()"""
        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self.collision('horizontal')
        self.hitbox_rect.y += self.direction.y * self.speed * dt
        self.collision('vertical')
        self.rect.center = self.hitbox_rect.center

    def collision(self, direction):
        """Checks for player collision with the sprites in the collision sprites group"""
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox_rect):
                if direction == 'horizontal':
                    if self.direction.x > 0:
                        self.hitbox_rect.right = sprite.rect.left
                    if self.direction.x < 0:
                        self.hitbox_rect.left = sprite.rect.right
                else:
                    if self.direction.y > 0:
                        self.hitbox_rect.bottom = sprite.rect.top
                    if self.direction.y < 0:
                        self.hitbox_rect.top = sprite.rect.bottom

    def update(self, dt):
        """Runs all the Player() methods"""
        self.get_direction()
        self.rotate()
        self.input()
        self.move(dt)

class Game():
    """Main game loop and some shooting logic"""
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

    def check_pickup_collisions(self):
        """Check if the player has picked up any pickups"""
        for pickup in pygame.sprite.spritecollide(self.player, self.all_sprites, False):
            if isinstance(pickup, PickUps):
                pickup.collect()


    def load_images(self):
        """Loads images"""
        self.bullet_surf = pygame.image.load(join('images', 'bullet.png')).convert_alpha()

    def input(self):
        """Gets input for shooting"""
        shooting = pygame.key.get_pressed()[pygame.K_SPACE] or pygame.mouse.get_pressed()[0]
        if shooting and self.can_shoot:
            pos = self.player.rect.center + BULLET_OFFSET
            Bullet(self.bullet_surf, pos, self.player.rotation, (self.all_sprites, self.bullet_sprites), self.player.angle)# pylint: disable=line-too-long
            self.can_shoot = False
            self.shoot_time = pygame.time.get_ticks()

    def gun_timer(self):
        """Defines the delay between shots"""
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.shoot_time >= self.gun_cooldown:
                self.can_shoot = True

    def setup(self):
        """Draws the map"""
        le_map = load_pygame(join('level', 'level.tmx'))

        for x, y, image in le_map.get_layer_by_name('Floor').tiles():
            Sprite((x * TILE_SIZE ,y * TILE_SIZE), image, self.all_sprites)

        for obj in le_map.get_layer_by_name('Objects'):
            CollisionSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))

        for obj in le_map.get_layer_by_name('Collisions'):
            CollisionSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), self.collision_sprites) # pylint: disable=line-too-long

        for obj in le_map.get_layer_by_name('Pickups'):
            surf = pygame.image.load(join('images', 'pillar.png'))
            self.pick_ups = PickUps((obj.x, obj.y), obj.name, surf, (self.all_sprites, self.collision_sprites)) # pylint: disable=line-too-long

        for obj in le_map.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player((obj.x,obj.y), self.all_sprites, self.collision_sprites)
                self.all_sprites.change_layer(self.player, 2)

    def check_bullet_collisions(self):
        """De-spawns bullets if they touch a wall or expire TODO"""
        for bullet in self.bullet_sprites:
            if pygame.sprite.spritecollideany(bullet, self.collision_sprites):
                bullet.kill()

    def run(self):
        """Main game loop"""
        while self.running:
            dt = self.clock.tick(FPS) / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            self.gun_timer()
            self.input()

            self.check_bullet_collisions()
            self.check_pickup_collisions()

            self.display_surface.fill('black')
            self.all_sprites.draw(self.player.rect.center)

            self.all_sprites.update(dt)
            pygame.display.update()

        pygame.quit()

if __name__ == '__main__':
    game = Game()
    game.run()
