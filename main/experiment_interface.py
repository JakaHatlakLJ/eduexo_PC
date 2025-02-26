import pygame
from pylsl import StreamInlet, resolve_streams, resolve_byprop
from experiment_LSL import LSLHandler

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
        self.total_trials = state_dict["trials_No"] + 2 * state_dict["control_trials_No"]

        self.inlet = inlet

        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        self.continue_experiment = True

        #### CREATE DIFFERENT FONTS
        self.font = pygame.font.SysFont('Arial', 48)    # Select font and size
        self.font2 = pygame.font.SysFont('Arial', 100, bold=True)
        self.font3 = pygame.font.SysFont('Arial', 24)
        self.font4 = pygame.font.SysFont('Arial', 24, bold=True)

        #### CREATE ALL STATIC TEXTs
        self.UP_text = self._create_static_text(text="UP", y_position=self.offset + self.pas/2, font=1)                                         # Upper band text
        self.DOWN_text = self._create_static_text(text="DOWN", y_position=self.height - self.offset - self.pas/2, font=1)                       # Lower band text
        self.current_trial_text = self._create_static_text(text='Current Trial', x_position=0.1*self.width, y_position=0.45*self.height)        # Current trial text
        self.remaining_time_text = self._create_static_text(text='Remaining Time', x_position=0.88*self.width, y_position=0.45*self.height)     # Remaining time text

    def update(self, state_dict):
        """
        pulls LSL sample and updates state_dict values related to current position of eduexo
        """
        self.state_dict = state_dict

        if self.state_dict["current_position"] is None:
            loc = (self.maxP - self.minP)/2 + self.minP
        else:
            loc = self.state_dict["current_position"]

        self.loc = (loc / (self.maxP - self.minP) - self.minP / (self.maxP - self.minP)) * (self.height-2*self.offset) + self.offset        # linear transformation of EXO angle to dot position on screen

        if self.loc < self.height/2 + 6 and self.loc > self.height/2 - 6:
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

        #### INITIAL SCREEN STATE
        if self.state_dict["current_state"] == "INITIAL_SCREEN":
            self._draw_dynamic_text(text=self.state_dict["main_text"], font=1)

        #### PAUSE STATE
        elif self.state_dict["current_state"] == "PAUSE":
            self.screen.fill("darkorange3")
            self._draw_dynamic_text(text="Paused. Press SPACE to continue.", font=1)

        #### EXIT, TERMINATION OR STREAM DISCONNECTION STATES
        elif self.state_dict["current_state"] == "EXIT":
            if self.state_dict["avg_time"] == None:
                self._draw_dynamic_text(text=self.state_dict["main_text"], y_position=0.45*self.height, font=1)     # Status text
                self._draw_dynamic_text(text=self.state_dict["sub_text"], y_position=0.55*self.height, font=4)      # Procedure instructions
            else:
                if self.state_dict["avg_time"] == 0:
                    time = "-- sec"
                    number = f'0/{str(self.total_trials)}'
                else:
                    time = f'{str(self.state_dict["avg_time"])} sec'
                    number =f'{str(self.state_dict["succ_trials"])}/{str(self.total_trials)}'

                self._draw_dynamic_text(text=self.state_dict["main_text"], y_position=0.3*self.height, font=1)                                  # Status text
                self._draw_dynamic_text(text=self.state_dict["sub_text"], x_position=self.width/2 - 10, y_position=0.4*self.height, font=4)     # Procedure instructions
                self._draw_dynamic_text("Avg. trial completition time:", x_position=0.6*self.width, y_position=0.55*self.height)                # Time results text
                self._draw_dynamic_text("Successful trials:", x_position=0.36*self.width, y_position=0.55*self.height)                          # Successfulness results text
                self._draw_dynamic_text(text=time, x_position=0.6*self.width, y_position=0.6*self.height)                                       # Time results
                self._draw_dynamic_text(text=number, x_position=0.36*self.width, y_position=0.6*self.height)                                    # Successfulness results

        #### ALL THE OTHER STATES
        
        #### BAND COLORING
        else:
            p11 = pygame.Vector2(0, self.offset + self.pas/2)
            p12 = pygame.Vector2(self.width, self.offset + self.pas/2)
            if self.state_dict["trial"] == "UP":
                if self.state_dict["is_UP"]:
                    color = "green"    
                elif self.state_dict["is_DOWN"]:
                    color = "red"    
                elif not self.in_band and self.state_dict["current_state"] == "GO_TO_UPPER_BAND": 
                    color = self.state_dict["color"]
                else:
                    color = "black"
                pygame.draw.line(self.screen, color, p11, p12, width = self.pas)

            p21 = pygame.Vector2(0, self.height - self.offset - self.pas/2)
            p22 = pygame.Vector2(self.width, self.height - self.offset - self.pas/2)
            if self.state_dict["trial"] == "DOWN":
                if self.state_dict["is_DOWN"]:
                    color = "green"    
                elif self.state_dict["is_UP"]:
                    color = "red"    
                elif not self.in_band and self.state_dict["current_state"] == "GO_TO_LOWER_BAND":
                    color = self.state_dict["color"]         
                else:
                    color = "black"                    
                pygame.draw.line(self.screen, color, p21, p22, width = self.pas)

            if self.state_dict["current_state"] == "FAILURE":
                if self.state_dict["is_UP"]:
                    pygame.draw.line(self.screen, "red", p11, p12, width = self.pas)
                elif self.state_dict["is_DOWN"]:
                    pygame.draw.line(self.screen, "red", p21, p22, width = self.pas)

            #### DRAW BANDS 
            pygame.draw.line(self.screen, "white", (0, self.offset), (self.width, self.offset))                                                         # Top line of UPPER BAND
            pygame.draw.line(self.screen, "white", (0, self.offset + self.pas), (self.width, self.offset + self.pas))                                   # Bottom line of UPPER BAND
            pygame.draw.line(self.screen, "white", (0, self.height-self.offset), (self.width, self.height-self.offset))                                 # Bottom line of LOWER BAND
            pygame.draw.line(self.screen, "white", (0, self.height - self.offset - self.pas), (self.width, self.height - self.offset - self.pas))       # Top line of LOWER BAND 

            #### DRAW REMAINING TIME
            self._draw_dynamic_text(text=str(self.state_dict["remaining_time"]), x_position=0.88*self.width, y_position=0.55*self.height)

            #### DRAW TRIAL COUNTER
            self._draw_dynamic_text(text=f'{str(self.state_dict["current_trial_No"])}/{str(self.total_trials)}', x_position=0.1*self.width, y_position=0.55*self.height)

            #### DRAW ALL CONSTANT TEXTs
            self.screen.blit(*self.UP_text)
            self.screen.blit(*self.DOWN_text)  
            self.screen.blit(*self.current_trial_text)
            self.screen.blit(*self.remaining_time_text)

            #### DRAW INSTRUCTIONS WHILE TRAIL IS IN PROGRESS
            UP_sign = self._create_static_text(text="UP", color=self.state_dict["color"], font=2, y_position=0.4*self.height)                                                           # UP instruction text
            DOWN_sign = self._create_static_text(text="DOWN", color=self.state_dict["color"], font=2, y_position=0.6*self.height)                                                       # DOWN instruction text    
            if not self.in_band:
                if self.state_dict["trial"] == "UP" and self.state_dict["trial_in_progress"]:
                    self.screen.blit(*UP_sign)
                elif self.state_dict["trial"] == "DOWN" and self.state_dict["trial_in_progress"]:
                    self.screen.blit(*DOWN_sign)
            
            #### RETURN TO CENTER TEXT AND TARGET CIRCLE
            if self.state_dict["current_state"] in {"RETURN_TO_CENTER", "IN_MIDDLE_CIRCLE", "WAITING", "IMAGINATION", "INTENTION"}:
                self._draw_dynamic_text(text=self.state_dict["main_text"], color="white", y_position=0.4*self.height, font=1)        
                pygame.draw.circle(self.screen, "white", (self.width/2, self.height/2), 17, width=2)              

            #### SUCCESSFUL TRIAL SIGN
            elif self.state_dict["current_state"] in {"IN_UPPER_BAND", "IN_LOWER_BAND"}:
                self._draw_dynamic_text(text=self.state_dict["main_text"], color="green", font=1)

            #### FAILED TRIAL SIGN
            elif self.state_dict["current_state"] in {"TIMEOUT", "FAILURE"}:
                self._draw_dynamic_text(text=self.state_dict["main_text"], color="red", font=1)

            #### X in the middle of the screen
            else:
                if not self.state_dict["in_the_middle"]:
                    self._draw_dynamic_text(text="X", x_position=self.width/2, y_position=self.height/2, font=3)

            #### DRAW THE MAIN DOT AT THE END
            pygame.draw.circle(self.screen, "white", dot_pos, 10)

    def run(self, state_dict):
        """
        Runs following functions in order:\n
        - Interface.update()\n
        - Interface.draw()\n
        \n
        Then checks if "X" button for quiting was pressed to terminate experiment
        """

        dot_pos = self.update(state_dict)
        self.draw(dot_pos)

        pygame.display.update()
        self.clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.continue_experiment = False


        return self.continue_experiment                        
    
    def _draw_dynamic_text(self, text="[SYSTEM]: No input given", color="white", background_color=None, x_position=None, y_position=None, font=3):
        if font == 1:
            t = self.font.render(text, True, color, background_color)
        elif font == 2:
            t = self.font2.render(text, True, color, background_color)
        elif font == 4:
            t = self.font4.render(text, True, color, background_color)
        else:
            t = self.font3.render(text, True, color, background_color)
        if x_position == None:
            x_position = self.width/2
        if y_position == None:
            y_position = self.height/2
        tR = t.get_rect(center = (x_position, y_position))
        self.screen.blit(t, tR)
        
    def _create_static_text(self, text="[SYSTEM]: No input given", color="white", background_color=None, x_position=None, y_position=None, font=3):
        if font == 1:
            t = self.font.render(text, True, color, background_color)
        elif font == 2:
            t = self.font2.render(text, True, color, background_color)
        elif font == 4:
            t = self.font4.render(text, True, color, background_color)
        else:
            t = self.font3.render(text, True, color, background_color)
        if x_position == None:
            x_position = self.width/2
        if y_position == None:
            y_position = self.height/2
        tR = t.get_rect(center = (x_position, y_position))
        return (t, tR)
    
    ### FOR RUNING GUI IN THREAD
    def thread_run(self, stop_event, cont_lock):
        """
        Runs following functions in order:\n
        - Interface.update()\n
        - Interface.draw()\n
        \n
        Then checks if "X" button for quiting was pressed to terminate experiment
        """
        while not stop_event is set:
            try:
                dot_pos = self.update()
                self.draw(dot_pos)

                pygame.display.update()
                self.clock.tick(60)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.continue_experiment = False

                global continue_experiment_g
                with cont_lock:
                    continue_experiment_g = self.continue_experiment
            except Exception as e:
                print(e) 


        
if __name__ == "__main__":
    inlet = Interface.lsl_stream()
    interface = Interface(inlet=inlet)
    interface.state_dict["event_type"] = None
    interface.state_dict["trial_in_progress"] = True
    interface.state_dict["main_text"] = "Return to center"
    interface.state_dict["remaining_time"] = "3.0"
    interface.state_dict["current_trial_No"] = 3
    interface.state_dict["trials_No"] = 20
    interface.state_dict["trial"] = "UP"
    interface.state_dict["color"] = "yellow"

    interface.state_dict["sub_text"] = "testing Interface !?"
    interface.state_dict["avg_time"] = 0

    LSL = LSLHandler(send=False)

    while interface.continue_experiment: 
        interface.state_dict["current_state"] = "IMAGINATION"
        if pygame.key.get_pressed()[pygame.K_UP] or pygame.key.get_pressed()[pygame.K_DOWN]:
            interface.state_dict["current_state"] = None
        LSL.EXO_stream_in(interface.state_dict)
        interface.run()
        print(f' is_UP: {interface.state_dict["is_UP"]}, is_DOWN: {interface.state_dict["is_DOWN"]}, in_the_middle: {interface.state_dict["in_the_middle"]}, on_the_move: {interface.state_dict["on_the_move"]}, Current Position: {interface.state_dict["current_position"]}')

    pygame.quit()