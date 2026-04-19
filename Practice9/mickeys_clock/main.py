import pygame
import sys
from clock import MickeyClock

def main():
    pygame.init()
    clock = MickeyClock()
    clock.run()

if __name__ == "__main__":
    main()