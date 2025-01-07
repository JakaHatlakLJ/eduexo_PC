import pygame
from pylsl import StreamInlet, resolve_stream

class Interface:
    def __init__(self, inlet, state_dict = {}, width=1280, height=820, offset=100, pas=80, maxP=180, minP=55):
        self.width = width
        self.height = height
        self.offset = offset
        self.pas = pas
        self.maxP = maxP
        self.minP = minP
        self.state_dict = state_dict

        self.inlet = inlet

        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        self.running = True

        self.font = pygame.font.Font('freesansbold.ttf', 48) # Select font and size
        self.font2 = pygame.font.Font('freesansbold.ttf', 100)
        self.font3 = pygame.font.Font('freesansbold.ttf', 24)

        self.UP_text = self.font.render('UP', True, "white") # Text, Anti alias, Color
        self.DOWN_text = self.font.render('DOWN', True, "white") # Text, Anti alias, Color
        self.UP_sign = self.font2.render('UP', True, "white")
        self.DOWN_sign = self.font2.render('DOWN', True, "white")
        
        self.textRect_UP = self.UP_text.get_rect(center = (self.width/2, self.offset + self.pas/2)) # Location
        self.textRect_DOWN = self.DOWN_text.get_rect(center = (self.width/2, self.height - self.offset - self.pas/2))
        self.textRect_UP_sign = self.UP_sign.get_rect(center = (self.width/2, self.height/2))
        self.textRect_DOWN_sign = self.DOWN_sign.get_rect(center = (self.width/2, self.height/2))

        self.Return_text = self.font.render('Return to center', True, "white")
        self.textRect_Return = self.Return_text.get_rect(center = (self.width/2, self.height/2))
        
        self.current_trial = self.font3.render('Current Trial', True, "white")
        self.textRect_current_trial = self.current_trial.get_rect(center = (0.1*self.width, 0.45*self.height))

    def update(self):
        self.state_dict["Current_Position"] = self.sample[0]

        self.state_dict["enter_pressed"] = pygame.key.get_pressed()[pygame.K_RETURN]
        self.state_dict["space_pressed"] = pygame.key.get_pressed()[pygame.K_SPACE]
        
        if self.loc < self.height/2 + 5 and self.loc > self.height/2 - 5:
            self.state_dict["in_the_middle"] = True
        else:
            self.state_dict["in_the_middle"] = False

        if self.loc < 0.9 * self.pas + self.offset:
            self.state_dict["is_UP"] = True
        else:
            self.state_dict["is_UP"] = False

        if self.loc > self.height - 0.9 * self.pas - self.offset:
            self.state_dict["is_DOWN"] = True
        else:
            self.state_dict["is_DOWN"] = False

        if self.state_dict["is_UP"] or self.state_dict["is_DOWN"] or self.state_dict["in_the_middle"]:
            self.state_dict["on_the_move"] = False
        else:
            self.state_dict["on_the_move"] = True

        print(self.state_dict)

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
        keys = pygame.key.get_pressed()
        self.in_band = False

        p1 = pygame.Vector2(0, self.offset + self.pas/2)
        p2 = pygame.Vector2(self.width, self.offset + self.pas/2)
        if self.loc < 0.9 * self.pas + self.offset:
            pygame.draw.line(self.screen, "green", p1, p2, width = self.pas)
            self.screen.blit(self.Return_text, self.textRect_Return)
            self.in_band = True        
        elif keys[pygame.K_UP] or \
            "current_trial" in self.state_dict and self.state_dict["current_trial"] == "UP": 
            pygame.draw.line(self.screen, "orange", p1, p2, width = self.pas)

        p1 = pygame.Vector2(0, self.height - self.offset - self.pas/2)
        p2 = pygame.Vector2(self.width, self.height - self.offset - self.pas/2)
        if self.loc > self.height - 0.9 * self.pas - self.offset:
            pygame.draw.line(self.screen, "green", p1, p2, width = self.pas)
            self.screen.blit(self.Return_text, self.textRect_Return)
            self.in_band = True
        elif keys[pygame.K_DOWN] or \
            "current_trial" in self.state_dict and self.state_dict["current_trial"] == "DOWN":
            pygame.draw.line(self.screen, "orange", p1, p2, width = self.pas)
   
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
        self.screen.blit(self.current_trial, self.textRect_current_trial)

    def dynamic_elements(self, dot_pos):
        keys = pygame.key.get_pressed()
        if not self.in_band:
            if keys[pygame.K_UP] or \
                "current_trial" in self.state_dict and self.state_dict["current_trial"] == "UP":
                self.screen.blit(self.UP_sign, self.textRect_UP_sign)
            elif keys[pygame.K_DOWN] or \
                "current_trial" in self.state_dict and self.state_dict["current_trial"] == "DOWN":
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
            
            self.update()                        
        
        pygame.quit()

if __name__ == "__main__":
    inlet = Interface.lsl_stream()
    interface = Interface(inlet=inlet)
    interface.run()