import pygame
import time


pygame.init()


GREEN_DARK = (0, 100, 0)
GREEN_LIGHT = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)


WIDTH, HEIGHT = 200, 200
screen = pygame.display.set_mode((WIDTH, HEIGHT))


square_size = 100
square_pos = (WIDTH // 2 - square_size // 2, HEIGHT // 2 - square_size // 2)


dark_green_time = 1.5
light_green_time = 7
red_time = 1
yellow_time = 5.5


def draw_square(color):
    screen.fill(color, rect=(square_pos[0], square_pos[1], square_size, square_size))

while True:
    draw_square(GREEN_DARK)
    pygame.display.update()
    time.sleep(dark_green_time)
    
    draw_square(GREEN_LIGHT)
    pygame.display.update()
    time.sleep(light_green_time)
    
    draw_square(RED)
    pygame.display.update()
    time.sleep(red_time)
    
    draw_square(YELLOW)
    pygame.display.update()
    time.sleep(yellow_time)
    
