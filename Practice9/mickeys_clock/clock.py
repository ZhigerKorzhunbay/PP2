import pygame
import math
from datetime import datetime

class MickeyClock:
    def __init__(self):
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Mickey's Clock")
        self.clock = pygame.time.Clock()
        
        try:
            self.mickey_image = pygame.image.load("images/mickey_hand.png")
            self.mickey_image = pygame.transform.scale(self.mickey_image, (400, 400))
        except:
            self.mickey_image = None
        
        self.center_x = 400
        self.center_y = 300
        
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            self.screen.fill((255, 255, 255))
            
            current_time = datetime.now()
            minutes = current_time.minute
            seconds = current_time.second
            
            minute_angle = minutes * 6
            second_angle = seconds * 6
            
            if self.mickey_image:
                self.screen.blit(self.mickey_image, (self.center_x - 200, self.center_y - 200))
            
            minute_hand = self.create_hand(150, 15, (0, 0, 0))
            second_hand = self.create_hand(180, 5, (255, 0, 0))
            
            rotated_minute = pygame.transform.rotate(minute_hand, -minute_angle)
            rotated_second = pygame.transform.rotate(second_hand, -second_angle)
            
            minute_rect = rotated_minute.get_rect(center=(self.center_x, self.center_y))
            second_rect = rotated_second.get_rect(center=(self.center_x, self.center_y))
            
            self.screen.blit(rotated_minute, minute_rect)
            self.screen.blit(rotated_second, second_rect)
            
            font = pygame.font.Font(None, 36)
            time_text = font.render(f"{minutes:02d}:{seconds:02d}", True, (0, 0, 0))
            text_rect = time_text.get_rect(center=(self.center_x, self.center_y + 200))
            self.screen.blit(time_text, text_rect)
            
            pygame.display.flip()
            self.clock.tick(1)
        
        pygame.quit()
    
    def create_hand(self, length, width, color):
        hand = pygame.Surface((length * 2, width * 2), pygame.SRCALPHA)
        pygame.draw.rect(hand, color, (length - width//2, 0, width, length))
        return hand