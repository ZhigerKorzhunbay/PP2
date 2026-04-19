import pygame

class Ball:
    def __init__(self):
        self.width = 800
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Moving Ball Game")
        self.clock = pygame.time.Clock()
        
        self.ball_radius = 25
        self.ball_x = self.width // 2
        self.ball_y = self.height // 2
        self.move_distance = 20
        
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.move_ball(event.key)
            
            self.screen.fill((255, 255, 255))
            pygame.draw.circle(self.screen, (255, 0, 0), (self.ball_x, self.ball_y), self.ball_radius)
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
    
    def move_ball(self, key):
        if key == pygame.K_UP:
            new_y = self.ball_y - self.move_distance
            if new_y - self.ball_radius >= 0:
                self.ball_y = new_y
        elif key == pygame.K_DOWN:
            new_y = self.ball_y + self.move_distance
            if new_y + self.ball_radius <= self.height:
                self.ball_y = new_y
        elif key == pygame.K_LEFT:
            new_x = self.ball_x - self.move_distance
            if new_x - self.ball_radius >= 0:
                self.ball_x = new_x
        elif key == pygame.K_RIGHT:
            new_x = self.ball_x + self.move_distance
            if new_x + self.ball_radius <= self.width:
                self.ball_x = new_x