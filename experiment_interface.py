import pygame
from pylsl import StreamInlet, resolve_stream

class Interface:
    """
    GUI for EDUEXO-EEG experiment:\n
    inlet: LSL stream inlet of eduexo's current position, velocity and trorque\n
    state_dict: state dictionary created at the start of experiment\n
    width: width of a GUI screen\n
    height: height of GUI screen\n
    offset: offset of goal bands from the edge of the screen\n
    pas: width of the goal band\n
    maxP: edge position of eduexo in extension [deg]\n
    minP: edge position of eduexo in compression [deg]\n
    """
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
    
        self.current_trial_text = self.font3.render('Current Trial', True, "white")
        self.textRect_current_trial = self.current_trial_text.get_rect(center = (0.1*self.width, 0.4*self.height))
        self.remaining_time_text = self.font3.render('Remaining Time', True, "white")
        self.textRect_remaining_time = self.remaining_time_text.get_rect(center = (0.88*self.width, 0.4*self.height))

    def update(self):
        """
        pulls LSL sample and updates state_dict values related to current position of eduexo
        """
        self.inlet.flush()
        self.sample, _ = self.inlet.pull_sample(timeout=1)
        
        if self.sample is None:
            self.sample = [(self.maxP - self.minP)/2 + self.minP]
            self.state_dict["stream_online"] = False
        else:
            self.state_dict["stream_online"] = True
            self.state_dict["current_position"] = self.sample[0]
            self.state_dict["current_velocity"] = self.sample[1]
            self.state_dict["current_torque"] = self.sample[2]

        loc = self.sample[0]
        self.loc = (loc / (self.maxP - self.minP) - self.minP / (self.maxP - self.minP)) * (self.height-2*self.offset) + self.offset 

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

        return pygame.Vector2(self.width/2,  self.loc)
    
    @staticmethod
    def lsl_stream():
        streams = resolve_stream('type', 'EXO')
        inlet = StreamInlet(streams[0])
        print("Receiving data...")
        return inlet
    
    def draw(self, dot_pos):
        """
        Draws all GUI components on the screen
        """
        if "background_color" in self.state_dict:
            self.screen.fill(self.state_dict["background_color"])
        else:
            self.screen.fill("black")

        if "current_state" not in self.state_dict:
            self.state_dict["current_state"] = None
            
        keys = pygame.key.get_pressed()
        self.in_band = False
        if self.state_dict["is_UP"] or self.state_dict["is_DOWN"]:
            self.in_band = True

        if self.state_dict["current_state"] == "INITIAL_SCREEN":
            main_text = self.font.render(self.state_dict["main_text"], True, "white")
            textRect_main = main_text.get_rect(center = (self.width/2, self.height/2))
            self.screen.blit(main_text, textRect_main)

        elif self.state_dict["current_state"] == "PAUSE":
            self.screen.fill("darkorange3")
            main_text = self.font.render("Paused. Press SPACE to continue.", True, "white")
            textRect_main = main_text.get_rect(center = (self.width/2, self.height/2))
            self.screen.blit(main_text, textRect_main)

        elif self.state_dict["current_state"] == "EXIT":
            main_text = self.font.render(self.state_dict["main_text"], True, "white")
            sub_text = self.font3.render(self.state_dict["sub_text"], True, "white")
            textRect_main = main_text.get_rect(center = (self.width/2, self.height/2))
            textRect_sub = sub_text.get_rect(center = (self.width/2 - 10, 0.6*self.height))
            self.screen.blit(main_text, textRect_main)
            self.screen.blit(sub_text, textRect_sub)

        else:
            p11 = pygame.Vector2(0, self.offset + self.pas/2)
            p12 = pygame.Vector2(self.width, self.offset + self.pas/2)
            if self.state_dict["current_state"] in {"GO_TO_UPPER_BAND", "IN_UPPER_BAND"}:
                if self.state_dict["is_UP"]:
                    color = "green"    
                elif self.state_dict["is_DOWN"]:
                    color = "red"    
                elif keys[pygame.K_UP] or self.state_dict["trial_in_progress"] and not self.in_band: 
                    color = "orange"
                pygame.draw.line(self.screen, color, p11, p12, width = self.pas)

            p21 = pygame.Vector2(0, self.height - self.offset - self.pas/2)
            p22 = pygame.Vector2(self.width, self.height - self.offset - self.pas/2)
            if self.state_dict["current_state"] in {"GO_TO_LOWER_BAND", "IN_LOWER_BAND"}:
                if self.state_dict["is_DOWN"]:
                    color = "green"    
                elif self.state_dict["is_UP"]:
                    color = "red"    
                elif keys[pygame.K_DOWN] or self.state_dict["trial_in_progress"] and not self.in_band:
                    color = "orange"          
                pygame.draw.line(self.screen, color, p21, p22, width = self.pas)

            if self.state_dict["current_state"] == "FAILURE":
                if self.state_dict["is_UP"]:
                    pygame.draw.line(self.screen, "red", p11, p12, width = self.pas)
                elif self.state_dict["is_DOWN"]:
                    pygame.draw.line(self.screen, "red", p21, p22, width = self.pas)
    
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

            
            remaining_time = self.font3.render(str(self.state_dict["remaining_time"]), True, "white")
            Rect_remaining_time = remaining_time.get_rect(center = (0.88*self.width, 0.5*self.height))
            current_trial = self.font3.render(f'{str(self.state_dict["current_trial_No"])}/{str(self.state_dict["Trials_No"])}', True, "white")
            Rect_current_trial = current_trial.get_rect(center = (0.1*self.width, 0.5*self.height))

            self.screen.blit(self.UP_text, self.textRect_UP)
            self.screen.blit(self.DOWN_text, self.textRect_DOWN)
            self.screen.blit(self.current_trial_text, self.textRect_current_trial)
            self.screen.blit(self.remaining_time_text, self.textRect_remaining_time)
            self.screen.blit(remaining_time, Rect_remaining_time)
            self.screen.blit(current_trial, Rect_current_trial)

            if not self.in_band:
                if (keys[pygame.K_UP] or self.state_dict["event_type"] == "UP") and self.state_dict["trial_in_progress"]:
                    self.screen.blit(self.UP_sign, self.textRect_UP_sign)
                elif (keys[pygame.K_DOWN] or self.state_dict["event_type"] == "DOWN") and self.state_dict["trial_in_progress"]:
                    self.screen.blit(self.DOWN_sign, self.textRect_DOWN_sign)
            
            if self.state_dict["current_state"] in {"GO_TO_MIDDLE_CIRCLE", "IN_MIDDLE_CIRCLE"}:
                Instructions_text = self.font.render(self.state_dict["main_text"], True, "white")
                textRect_Instructions = Instructions_text.get_rect(center = (self.width/2, self.height*0.4))
                self.screen.blit(Instructions_text, textRect_Instructions)  
        
                pygame.draw.circle(self.screen, "white", (self.width/2, self.height/2), 17, width= 2)              
                if self.state_dict["in_the_middle"]:
                    pygame.draw.circle(self.screen, "green", (self.width/2, self.height/2), 16)

            elif self.state_dict["current_state"] in {"IN_UPPER_BAND", "IN_LOWER_BAND"}:
                Instructions_text = self.font.render(self.state_dict["main_text"], True, "green")
                textRect_Instructions = Instructions_text.get_rect(center = (self.width/2, self.height*0.5))
                self.screen.blit(Instructions_text, textRect_Instructions)  

            elif self.state_dict["current_state"] in {"TIMEOUT", "FAILURE"}:
                Instructions_text = self.font.render(self.state_dict["main_text"], True, "red")
                textRect_Instructions = Instructions_text.get_rect(center = (self.width/2, self.height*0.5))
                self.screen.blit(Instructions_text, textRect_Instructions)  
            
            pygame.draw.circle(self.screen, "white", dot_pos, 10)

    def run(self):
        """
        Runs following functions in order:\n
        - Interface.update()\n
        - Interface.draw()\n
        \n
        Then checks if "X" button for quiting was pressed to terminate experiment
        """

        dot_pos = self.update()
        self.draw(dot_pos)

        pygame.display.update()
        self.clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.continue_experiment = False

        return self.continue_experiment                        
        
        
if __name__ == "__main__":
    inlet = Interface.lsl_stream()
    interface = Interface(inlet=inlet)
    interface.state_dict["event_type"] = None
    interface.state_dict["trial_in_progress"] = True
    interface.state_dict["main_text"] = "Return to center"
    while interface.continue_experiment: 
        interface.state_dict["current_state"] = "GO_TO_MIDDLE_CIRCLE"
        if pygame.key.get_pressed()[pygame.K_UP] or pygame.key.get_pressed()[pygame.K_DOWN]:
            interface.state_dict["current_state"] = None
        interface.run()
        print(f' is_UP: {interface.state_dict["is_UP"]}, is_DOWN: {interface.state_dict["is_DOWN"]}, in_the_middle: {interface.state_dict["in_the_middle"]}, on_the_move: {interface.state_dict["on_the_move"]}, Current Position: {interface.state_dict["current_position"]}')

    pygame.quit()