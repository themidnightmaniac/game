import pygame
from sys import exit

WIN_W = 800
WIN_H = 400

pygame.display.set_caption('yo')

running = True

clock = pygame.time.Clock()

pygame.init()
screen = pygame.display.set_mode((WIN_W, WIN_H))

sky_surf = pygame.Surface((800,300))
sky_surf.fill('cyan')

floor_surf = pygame.Surface((800,100))
floor_surf.fill('brown')

snail_surf = pygame.Surface((40,40))
snail_surf.fill('red')
snail_rect = snail_surf.get_rect(midbottom = (400, 300))

player_surf = pygame.Surface((60, 60))
player_surf.fill('green')
player_rect = player_surf.get_rect(midbottom = (700, 300))

while running:
	clock.tick(60)
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			pygame.quit()
			exit()
	
	screen.blit(sky_surf, (0,0))
	screen.blit(floor_surf, (0,300))
	screen.blit(snail_surf, snail_rect)
	screen.blit(player_surf, player_rect)

	snail_rect.x += -2


	mouse_pos = pygame.mouse.get_pos()
	if player_rect.collidepoint(mouse_pos):
		print(pygame.mouse.get_pressed())

	#if player_rect.colliderect(snail_rect):
	#	pygame.quit()

	if snail_rect.right <= 0:
		snail_rect.left = WIN_W

	pygame.display.flip()

pygame.quit()