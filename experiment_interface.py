import pygame
from pylsl import StreamInlet, resolve_stream
import random
import numpy as np

class Interfacee:
    def __init__(self, inlet, width=1280, height=820, offset=100, pas=80, maxP=180, minP=55):
        self.width = width
        self.height = height
        self.offset = offset
        self.pas = pas
        self.maxP = maxP
        self.minP = minP

        self.inlet = inlet

        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        self.running = True

        self.font = pygame.font.Font('freesansbold.ttf', 48) # Select font and size
        self.font2 = pygame.font.Font('freesansbold.ttf', 100)

        self.UP_text = self.font.render('UP', True, "white") # Text, Anti alias, Color
        self.DOWN_text = self.font.render('DOWN', True, "white") # Text, Anti alias, Color
        self.UP_sign = self.font2.render('UP', True, "white")
        self.DOWN_sign = self.font2.render('DOWN', True, "white")

        self.textRect_UP = self.UP_text.get_rect(center = (self.width/2, self.offset + self.pas/2)) # Location
        self.textRect_DOWN = self.DOWN_text.get_rect(center = (self.width/2, self.height - self.offset - self.pas/2))
        self.textRect_UP_sign = self.UP_sign.get_rect(center = (self.width/2, self.height/2))
        self.textRect_DOWN_sign = self.DOWN_sign.get_rect(center = (self.width/2, self.height/2))

    def update(self, state_dict):
        state_dict["Current_Position"] = self.sample[0]
        state_dict["Current_Velocity"] = self.sample[1]
        state_dict["Current_Torque"] = self.sample[2]


    def lsl_stream():
        streams = resolve_stream('type', 'EXO')
        inlet = StreamInlet(streams[0])
        print("Receiving data...")
        return inlet

    def dot_position(self):
            self.sample, _ = self.inlet.pull_sample()
            loc = self.sample[0]
            self.loc = (loc / (self.maxP - self.minP) - self.minP / (self.maxP - self.minP)) * (self.height-2*self.offset) + self.offset 
            return pygame.Vector2(self.width/2,  self.loc)
    
    def background(self):
        self.screen.fill("black")

        p1 = pygame.Vector2(0, self.offset + self.pas/2)
        p2 = pygame.Vector2(self.width, self.offset + self.pas/2)
        if self.loc < 0.9 * self.pas + self.offset:
            pygame.draw.line(self.screen, "green", p1, p2, width = self.pas)

        p1 = pygame.Vector2(0, self.height - self.offset - self.pas/2)
        p2 = pygame.Vector2(self.width, self.height - self.offset - self.pas/2)
        if self.loc > self.height - 0.9 * self.pas - self.offset:
            pygame.draw.line(self.screen, "green", p1, p2, width = self.pas)
        
        p1 = pygame.Vector2(0, self.offset)
        p2 = pygame.Vector2(self.width, self.offset)
        pygame.draw.line(self.screen, "white", p1, p2)

        p1 = pygame.Vector2(0, self.offset + self.pas)
        p2 = pygame.Vector2(self.width, self.offset + self.pas)
        pygame.draw.line(self.screen, "white", p1, p2)

        p1 = pygame.Vector2(0, self.height-self.offset)
        p2 = pygame.Vector2(self.width, self.height-self.offset)
        pygame.draw.line(self.screen, "white", p1, p2)

        p1 = pygame.Vector2(0, self.height - self.offset - self.pas)
        p2 = pygame.Vector2(self.width, self.height - self.offset - self.pas)
        pygame.draw.line(self.screen, "white", p1, p2)      

        self.screen.blit(self.UP_text, self.textRect_UP)
        self.screen.blit(self.DOWN_text, self.textRect_DOWN)

    def dynamic_elements(self, dot_pos):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.screen.blit(self.UP_sign, self.textRect_UP_sign)
        elif keys[pygame.K_DOWN]:
            self.screen.blit(self.DOWN_sign, self.textRect_DOWN_sign)
        else:
            pygame.draw.circle(self.screen, "white", (self.width/2, self.height/2), 17, width= 2)
            if self.loc < self.height/2 + 5 and self.loc > self.height/2 - 5:
                pygame.draw.circle(self.screen, "green", (self.width/2, self.height/2), 16) 
        
        pygame.draw.circle(self.screen, "white", dot_pos, 10)

    def run(self):
        while self.running:
            dot_pos = self.dot_position()
            self.background()
            self.dynamic_elements(dot_pos)

            pygame.display.update()
            self.clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
        
        pygame.quit()

if __name__ == "__main__":
    inlet = Interfacee.lsl_stream()
    interface = Interfacee(inlet=inlet)
    interface.run()