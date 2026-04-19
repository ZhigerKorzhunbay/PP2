import pygame
import sys
import os

class MusicPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((600, 400))
        pygame.display.set_caption("Music Player")
        self.clock = pygame.time.Clock()
        
        self.tracks = []
        self.current_track = 0
        self.playing = False
        
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        self.load_tracks()
        
    def load_tracks(self):
        if os.path.exists("music"):
            for file in os.listdir("music"):
                if file.endswith(".wav") or file.endswith(".mp3"):
                    self.tracks.append(file)
        
        if len(self.tracks) == 0:
            self.tracks = ["track1.wav", "track2.wav"]
    
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        self.play()
                    elif event.key == pygame.K_s:
                        self.stop()
                    elif event.key == pygame.K_n:
                        self.next_track()
                    elif event.key == pygame.K_b:
                        self.previous_track()
                    elif event.key == pygame.K_q:
                        running = False
            
            self.screen.fill((50, 50, 50))
            
            title = self.font.render("MUSIC PLAYER", True, (255, 255, 255))
            self.screen.blit(title, (200, 30))
            
            if len(self.tracks) > 0:
                track_name = self.tracks[self.current_track]
                track_text = self.font.render("Now Playing: " + track_name, True, (200, 200, 255))
                self.screen.blit(track_text, (100, 100))
            
            if self.playing:
                status_text = self.font.render("Status: PLAYING", True, (100, 255, 100))
            else:
                status_text = self.font.render("Status: STOPPED", True, (255, 100, 100))
            self.screen.blit(status_text, (100, 160))
            
            controls_y = 250
            controls = ["P - Play", "S - Stop", "N - Next Track", "B - Previous Track", "Q - Quit"]
            for control in controls:
                text = self.small_font.render(control, True, (200, 200, 200))
                self.screen.blit(text, (100, controls_y))
                controls_y += 35
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()
    
    def play(self):
        if not self.playing and len(self.tracks) > 0:
            try:
                track_path = os.path.join("music", self.tracks[self.current_track])
                pygame.mixer.music.load(track_path)
                pygame.mixer.music.play()
                self.playing = True
            except:
                print("Could not play track")
    
    def stop(self):
        pygame.mixer.music.stop()
        self.playing = False
    
    def next_track(self):
        self.stop()
        self.current_track = (self.current_track + 1) % len(self.tracks)
        self.play()
    
    def previous_track(self):
        self.stop()
        self.current_track = (self.current_track - 1) % len(self.tracks)
        self.play()