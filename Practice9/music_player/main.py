import pygame
import sys
from player import MusicPlayer

def main():
    pygame.init()
    player = MusicPlayer()
    player.run()

if __name__ == "__main__":
    main()