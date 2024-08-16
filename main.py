from math import atan2, degrees
from random import randint
from os.path import join
import pygame
from pytmx.util_pygame import load_pygame

WIN_W, WIN_H = 800, 600
TILE_SIZE = 64
SHOOTING_COOLDOWN = 150
BULLET_SPEED = 2000
FPS = 120
BULLET_OFFSET = pygame.Vector2(10, 10)

class PickUps(pygame.sprite.Sprite):
    """Manages the rotation of pickup sprites"""
    def __init__(self, pos, name, surf, groups):
        super().__init__(groups)
        self.original_image = surf.convert_alpha()
        self.image = self.original_image
        self.rect = self.image.get_rect(topleft=pos)
        self.name = name

        self.rotation_angle = randint(0, 360)
        self.rotation_speed = randint(30, 50)

    def collect(self, player):
        """Handle the pickup logic"""
        if self.name == 'Gun':
            player.change_image('player_gun.png')
            player.has_a_gun = True
            print("oi")
        self.kill()

    def update(self, dt):
        """Updates the rotation of the pickup"""
        self.rotation_angle += self.rotation_speed * dt
        if self.rotation_angle >= 360:
            self.rotation_angle -= 360

        rotated_image = pygame.transform.rotate(self.original_image, self.rotation_angle)
        self.rect = rotated_image.get_rect(center=self.rect.center)
        self.image = rotated_image

class AllSprites(pygame.sprite.LayeredUpdates):
    """Groups sprites for easier bliting and aligns them to topleft like in tiled"""
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.Vector2(0, 0)

    def draw(self, target_pos):
        """Custom drawing method"""
        self.offset.x = -(target_pos[0] - WIN_W // 2)
        self.offset.y = -(target_pos[1] - WIN_H // 2)
        for sprite in self:
            self.display_surface.blit(sprite.image, sprite.rect.topleft + self.offset)

class Sprite(pygame.sprite.Sprite):
    """Class for floor tile sprites"""
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)

class Bullet(pygame.sprite.Sprite):
    """Manages the movement and displaying of bullets"""
    def __init__(self, surf, pos, direction, groups, angle):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(center=pos)
        self.bullet_surf = self.image
        self.angle = angle
        self.direction = direction
        self.speed = BULLET_SPEED


    def rotate(self):
        """Rotates the bullet sprite so it is aligned with the angle it was fired from"""
        self.image = pygame.transform.rotozoom(self.bullet_surf, self.angle, 1)
        self.rect = self.image.get_rect(center=self.rect.center)

    def update(self, dt):
        """Calls the rotate method and THEN moves the bullet"""
        self.rotate()
        self.rect.center += self.direction * self.speed * dt

class CollisionSprite(pygame.sprite.Sprite):
    """Groups all sprites that have collisions"""
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)

class Player(pygame.sprite.Sprite):
    """Manages player movement, direction, rotation, and collision"""
    def __init__(self, pos, groups, collision_sprites):
        super().__init__(groups)
        self.image = pygame.image.load(join('images', 'player.png')).convert_alpha()
        self.player_surf = self.image
        self.rect = self.image.get_rect(center=pos)
        self.hitbox_rect = self.rect.inflate(0, 0)
        self.rotation = 0
        self.angle = 0
        self.direction = pygame.Vector2()
        self.velocity = pygame.Vector2()
        self.acceleration = 10000000000000000000000
        self.deceleration = 500
        self.max_speed = 500
        self.collision_sprites = collision_sprites

        self.health = 3
        self.ammo = 1000000

        self.pos = pygame.Vector2(WIN_W / 2, WIN_H / 2)

        self.has_a_gun = False

    def change_image(self, image_name):
        """Change the player's image to the specified image."""
        self.image = pygame.image.load(join('images', image_name)).convert_alpha()
        self.player_surf = self.image
        self.rect = self.image.get_rect(center=self.hitbox_rect.center)
        self.rotate()

    def collect_health(self, amount):
        """Increase player health"""
        self.health += amount
        self.health = min(self.health, 3)

    def collect_ammo(self, amount):
        """Increase player ammo"""
        self.ammo += amount

    def get_direction(self):
        """Determines the direction which the player is facing relative to the mouse"""
        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        self.rotation = (mouse_pos - self.pos).normalize()

    def rotate(self):
        """Rotates the player sprite so it is aligned to the mouse"""
        self.angle = degrees(atan2(self.rotation.x, self.rotation.y)) + 180
        self.image = pygame.transform.rotozoom(self.player_surf, self.angle, 1)
        self.rect = self.image.get_rect(center=self.hitbox_rect.center)

    def input(self):
        """Determines the player movement direction"""
        keys = pygame.key.get_pressed()
        target_direction = pygame.Vector2(
            int(keys[pygame.K_d]) - int(keys[pygame.K_a]),
            int(keys[pygame.K_s]) - int(keys[pygame.K_w])
        )
        if target_direction.length() > 0:
            target_direction.normalize_ip()
        self.direction = target_direction

    def move(self, dt):
        """Moves player using values from self.input()"""
        # Calculate desired velocity based on acceleration
        if self.direction.length() > 0:
            # Accelerate
            self.velocity += self.direction * self.acceleration * dt
        else:
            # Decelerate
            if self.velocity.length() > 0:
                deceleration_vector = self.velocity.normalize() * self.deceleration * dt
                if self.velocity.length() > deceleration_vector.length():
                    self.velocity -= deceleration_vector
                else:
                    self.velocity = pygame.Vector2()

        # Cap the velocity at max speed
        if self.velocity.length() > self.max_speed:
            self.velocity.scale_to_length(self.max_speed)

        # Move player and handle collisions
        self.handle_movement(dt)

    def handle_movement(self, dt):
        """Handle movement and collisions"""
        # Move horizontally and check for collisions
        self.hitbox_rect.x += self.velocity.x * dt
        self.collision('horizontal')

        # Move vertically and check for collisions
        self.hitbox_rect.y += self.velocity.y * dt
        self.collision('vertical')

        # Update player rect
        self.rect.center = self.hitbox_rect.center

    def collision(self, direction):
        """Checks for player collision with the sprites in the collision sprites group"""
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox_rect):
                self.velocity *= 0.955
                if direction == 'horizontal':
                    if self.velocity.x > 0:
                        self.hitbox_rect.right = sprite.rect.left
                    if self.velocity.x < 0:
                        self.hitbox_rect.left = sprite.rect.right
                else:
                    if self.velocity.y > 0:
                        self.hitbox_rect.bottom = sprite.rect.top
                    if self.velocity.y < 0:
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
        pygame.display.set_caption("Game")
        self.clock = pygame.time.Clock()
        self.running = True
        self.bullet_surf = pygame.image.load(join('images', 'bullet.png')).convert_alpha()

        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()

        self.setup()

        self.can_shoot = True
        self.shoot_time = 0
        self.gun_cooldown = SHOOTING_COOLDOWN

    def check_pickup_collisions(self):
        """Check if the player has picked up any pickups"""
        for pickup in pygame.sprite.spritecollide(self.player, self.all_sprites, False):
            if isinstance(pickup, PickUps):
                pickup.collect(self.player)

    def input(self):
        """Gets input for shooting"""
        shooting = pygame.key.get_pressed()[pygame.K_SPACE] or pygame.mouse.get_pressed()[0]
        if shooting and self.player.has_a_gun and self.can_shoot:
            if self.player.ammo > 0:
                pos = self.player.rect.center + BULLET_OFFSET
                Bullet(self.bullet_surf, pos, self.player.rotation, (self.all_sprites, self.bullet_sprites), self.player.angle)
                self.player.ammo -= 1
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
            Sprite((x * TILE_SIZE, y * TILE_SIZE), image, self.all_sprites)

        for obj in le_map.get_layer_by_name('Objects'):
            CollisionSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))

        for obj in le_map.get_layer_by_name('Collisions'):
            CollisionSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), self.collision_sprites)

        for obj in le_map.get_layer_by_name('Pickups'):
            self.pick_ups = PickUps((obj.x, obj.y), obj.name, obj.image, (self.all_sprites, self.collision_sprites))

        for obj in le_map.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player((obj.x, obj.y), self.all_sprites, self.collision_sprites)
                self.all_sprites.change_layer(self.player, 2)

    def check_bullet_collisions(self):
        """De-spawns bullets if they touch a wall or expire"""
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

            # Display player health and ammo
            font = pygame.font.Font(None, 36)
            health_text = font.render(f'Health: {self.player.health}', True, 'white')
            ammo_text = font.render(f'Ammo: {self.player.ammo}', True, 'white')
            self.display_surface.blit(health_text, (10, 10))
            self.display_surface.blit(ammo_text, (10, 40))

            pygame.display.update()

        pygame.quit()

if __name__ == '__main__':
    game = Game()
    game.run()
