import pygame
import math
from datetime import datetime

class MickeyClock:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Mickey's Clock")
        self.clock = pygame.time.Clock()
        
        self.clock_face = pygame.image.load("mickeyclock.jpeg")
        self.clock_face = pygame.transform.scale(self.clock_face, (400, 400))
        
        right_raw = pygame.image.load("images/right_hand.png")
        self.right_hand = pygame.transform.scale(right_raw, (60, 160))
        
        left_raw = pygame.image.load("images/left_hand.png")
        self.left_hand = pygame.transform.scale(left_raw, (60, 160))
        
        self.center_x = 400
        self.center_y = 300
        
        self.font = pygame.font.Font(None, 48)
        
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            now = datetime.now()
            minutes = now.minute
            seconds = now.second
            
            minute_angle = minutes * 6
            second_angle = seconds * 6
            
            self.screen.fill((255, 255, 255))
            
            face_rect = self.clock_face.get_rect(center=(self.center_x, self.center_y))
            self.screen.blit(self.clock_face, face_rect)
            
            rotated_right = pygame.transform.rotate(self.right_hand, -minute_angle)
            rotated_left = pygame.transform.rotate(self.left_hand, -second_angle)
            
            right_rect = rotated_right.get_rect(center=(self.center_x, self.center_y))
            left_rect = rotated_left.get_rect(center=(self.center_x, self.center_y))
            
            self.screen.blit(rotated_right, right_rect)
            self.screen.blit(rotated_left, left_rect)
            
            time_text = self.font.render(f"{minutes:02d}:{seconds:02d}", True, (0, 0, 0))
            text_rect = time_text.get_rect(center=(self.center_x, self.center_y + 220))
            self.screen.blit(time_text, text_rect)
            
            pygame.display.flip()
            self.clock.tick(1)
        
        pygame.quit()