import pygame
import sys
from ball import Ball

def main():
    pygame.init()
    ball_game = Ball()
    ball_game.run()

if __name__ == "__main__":
    main()