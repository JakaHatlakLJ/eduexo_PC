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
        self.continue_experiment = True

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
    
        self.current_trial = self.font3.render('Current Trial', True, "white")
        self.textRect_current_trial = self.current_trial.get_rect(center = (0.1*self.width, 0.45*self.height))

    def update(self):
        self.state_dict["Current_Position"] = self.sample[0]
        
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
    
    @staticmethod
    def lsl_stream():
        streams = resolve_stream('type', 'EXO')
        inlet = StreamInlet(streams[0])
        print("Receiving data...")
        return inlet

    def dot_position(self):
        self.inlet.flush()
        self.sample, _ = self.inlet.pull_sample(timeout=1)
        
        if self.sample is None:
            self.sample = [(self.maxP - self.minP)/2 + self.minP]
            self.state_dict["stream_online"] = False
        else:
            self.state_dict["stream_online"] = True

        loc = self.sample[0]
        self.loc = (loc / (self.maxP - self.minP) - self.minP / (self.maxP - self.minP)) * (self.height-2*self.offset) + self.offset 
        return pygame.Vector2(self.width/2,  self.loc)
    
    def draw(self, dot_pos):
        if "background_color" in self.state_dict:
            self.screen.fill(self.state_dict["background_color"])
        else:
            self.screen.fill("black")

        if "current_state" not in self.state_dict:
            self.state_dict["current_state"] = None
            
        keys = pygame.key.get_pressed()
        self.in_band = False
        if self.loc < 0.9 * self.pas + self.offset or self.loc > self.height - 0.9 * self.pas - self.offset:
            self.in_band = True


        if self.state_dict["current_state"] == "INITIAL_SCREEN":
            self.screen.fill(self.state_dict["background_color"])
            main_text = self.font.render(self.state_dict["main_text"], True, "white")
            textRect_main = main_text.get_rect(center = (self.width/2, self.height/2))
            self.screen.blit(main_text, textRect_main)

        elif self.state_dict["current_state"] == "PAUSE":
            self.screen.fill(self.state_dict["background_color"])
            main_text = self.font.render(self.state_dict["main_text"], True, "white")
            textRect_main = main_text.get_rect(center = (self.width/2, self.height/2))
            self.screen.blit(main_text, textRect_main)

        elif self.state_dict["current_state"] == "EXIT":
            self.screen.fill(self.state_dict["background_color"])
            main_text = self.font.render(self.state_dict["main_text"], True, "white")
            sub_text = self.font3.render(self.state_dict["sub_text"], True, "white")
            textRect_main = main_text.get_rect(center = (self.width/2, self.height/2))
            textRect_sub = sub_text.get_rect(center = (self.width/2 - 10, 0.6*self.height))
            self.screen.blit(main_text, textRect_main)
            self.screen.blit(sub_text, textRect_sub)

        else:
            p1 = pygame.Vector2(0, self.offset + self.pas/2)
            p2 = pygame.Vector2(self.width, self.offset + self.pas/2)
            if self.loc < 0.9 * self.pas + self.offset:
                pygame.draw.line(self.screen, "green", p1, p2, width = self.pas)      
            elif (keys[pygame.K_UP] or self.state_dict["current_trial"] == "UP") and self.state_dict["trial_in_progress"] and not self.in_band: 
                pygame.draw.line(self.screen, "orange", p1, p2, width = self.pas)

            p1 = pygame.Vector2(0, self.height - self.offset - self.pas/2)
            p2 = pygame.Vector2(self.width, self.height - self.offset - self.pas/2)
            if self.loc > self.height - 0.9 * self.pas - self.offset:
                pygame.draw.line(self.screen, "green", p1, p2, width = self.pas)
            elif (keys[pygame.K_DOWN] or self.state_dict["current_trial"] == "DOWN") and self.state_dict["trial_in_progress"] and not self.in_band:
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

            if not self.in_band:
                if (keys[pygame.K_UP] or self.state_dict["current_trial"] == "UP") and self.state_dict["trial_in_progress"]:
                    self.screen.blit(self.UP_sign, self.textRect_UP_sign)
                elif (keys[pygame.K_DOWN] or self.state_dict["current_trial"] == "DOWN") and self.state_dict["trial_in_progress"]:
                    self.screen.blit(self.DOWN_sign, self.textRect_DOWN_sign)
            
            if self.state_dict["current_state"] in {"GO_TO_MIDDLE_CIRCLE", "IN_MIDDLE_CIRCLE"}:
                Instructions_text = self.font.render(self.state_dict["main_text"], True, "white")
                textRect_Instructions = Instructions_text.get_rect(center = (self.width/2, self.height*0.4))
                self.screen.blit(Instructions_text, textRect_Instructions)  
        
                pygame.draw.circle(self.screen, "white", (self.width/2, self.height/2), 17, width= 2)              
                if self.loc < self.height/2 + 5 and self.loc > self.height/2 - 5:
                    pygame.draw.circle(self.screen, "green", (self.width/2, self.height/2), 16)
            
            pygame.draw.circle(self.screen, "white", dot_pos, 10)

    def run(self):
        dot_pos = self.dot_position()
        self.draw(dot_pos)

        pygame.display.update()
        self.clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.continue_experiment = False
        
        self.update()

        return self.continue_experiment                        
        
        

if __name__ == "__main__":
    inlet = Interface.lsl_stream()
    interface = Interface(inlet=inlet)
    interface.state_dict["current_trial"] = None
    interface.state_dict["trial_in_progress"] = True
    interface.state_dict["main_text"] = "Return to center"
    while interface.continue_experiment: 
        interface.state_dict["current_state"] = "GO_TO_MIDDLE_CIRCLE"
        if pygame.key.get_pressed()[pygame.K_UP] or pygame.key.get_pressed()[pygame.K_DOWN]:
            interface.state_dict["current_state"] = None
        interface.run()
        print(f' is_UP: {interface.state_dict["is_UP"]}, is_DOWN: {interface.state_dict["is_DOWN"]}, in_the_middle: {interface.state_dict["in_the_middle"]}, on_the_move: {interface.state_dict["on_the_move"]}, Current_Position: {interface.state_dict["Current_Position"]}')

    pygame.quit()