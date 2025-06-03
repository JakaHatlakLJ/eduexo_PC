import pygame
from pylsl import StreamInlet, resolve_streams, resolve_byprop
from experiment_LSL import LSLHandler
from time import perf_counter

class Interface:
    """
    Class for handling GUI for EDUEXO-EEG experiment.
    Responsible for drawing all visual elements, updating state from hardware,
    and managing user interaction via keyboard and window events.
    """

    def __init__(self, state_dict = {}, width=1280, height=820, band_offset=60, pas=60, maxP=180, minP=55):
        """
        Initializes pygame and all necessary parameters for the GUI.

        :param state_dict: state dictionary created at the start of experiment
        :param width: width of a GUI screen
        :param height: height of GUI screen
        :param band_offset: offset of goal bands from the edge of the screen
        :param pas: width of the goal band
        :param maxP: edge position of eduexo in extension [deg]
        :param minP: edge position of eduexo in compression [deg]
        """
        self.width = width
        self.height = height
        self.band_offset = band_offset
        self.pas = pas
        self.dot_size = 10
        self.maxP = maxP
        self.minP = minP

        self.state_dict = state_dict

        # Initialize pygame and set up the display window
        pygame.init()
        if state_dict["fullscreen"]:
            info = pygame.display.Info()
            self.width = info.current_w
            self.height = info.current_h
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.NOFRAME | pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        self.edge_margin = 2
        self.clock = pygame.time.Clock()
        self.continue_experiment = True
        self.prev_time = perf_counter()

        # Create different fonts for various UI elements
        self.font = pygame.font.SysFont('Arial', 48)    # Main font
        self.font2 = pygame.font.SysFont('Arial', 100, bold=True)  # Large font for instructions
        self.font3 = pygame.font.SysFont('Arial', 24)   # Small font
        self.font4 = pygame.font.SysFont('Arial', 24, bold=True)   # Small bold font

        # Pre-render static texts for performance
        self.update_static_texts()

    def update(self, state_dict):
        """
        Updates the state_dict with the current position of the exoskeleton and
        calculates the dot position for drawing.

        :param state_dict: state dictionary of main program
        :return: pygame.Vector2 with the dot position on the screen
        """
        self.state_dict = state_dict

        if self.state_dict["current_position"] is None:
            loc = (self.maxP - self.minP)/2 + self.minP
        else:
            loc = self.state_dict["current_position"]

        # Map exoskeleton angle to vertical screen position
        self.loc = (loc / (self.maxP - self.minP) - self.minP / (self.maxP - self.minP)) * (self.height - 2 * self.band_offset) + self.band_offset

        # Determine if the dot is in the middle, upper, or lower band
        if self.loc < self.height/2 + self.dot_size/2 + 1 and self.loc > self.height/2 - self.dot_size/2 - 1:
            self.state_dict["in_the_middle"] = True
        else:
            self.state_dict["in_the_middle"] = False

        if self.loc < 0.9 * self.pas + self.band_offset:
            self.state_dict["is_UP"] = True
        else:
            self.state_dict["is_UP"] = False

        if self.loc > self.height - 0.9 * self.pas - self.band_offset:
            self.state_dict["is_DOWN"] = True
        else:
            self.state_dict["is_DOWN"] = False

        # Determine if the dot is moving (not in any band or middle)
        if self.state_dict["is_UP"] or self.state_dict["is_DOWN"] or self.state_dict["in_the_middle"]:
            self.state_dict["on_the_move"] = False
        else:
            self.state_dict["on_the_move"] = True

        return pygame.Vector2(self.width/2,  self.loc)
    
    def draw(self, dot_pos):
        """
        Draws all GUI components on the screen based on the current state.

        :param dot_pos: position of the dot on the screen
        """
        # Set background color
        if "background_color" in self.state_dict:
            self.screen.fill(self.state_dict["background_color"])
        else:
            self.screen.fill("black")

        # Ensure current_state is set
        if "current_state" not in self.state_dict:
            self.state_dict["current_state"] = None
            
        keys = pygame.key.get_pressed()
        self.in_band = False
        if self.state_dict["is_UP"] or self.state_dict["is_DOWN"]:
            self.in_band = True

        #### INITIAL SCREEN STATE
        if self.state_dict["current_state"] == "INITIAL_SCREEN":     
            # Show instructions for starting, exiting, and pausing
            self._draw_dynamic_text(text=f"Press ENTER when ready.", font=1, y_position=0.4*self.height)
            self._draw_dynamic_text(text=f"Press ESC to exit.", font=1)
            self._draw_dynamic_text(text=f"Press SPACE to pause.", font=1, y_position=0.6*self.height)

        #### PAUSE STATE
        elif self.state_dict["current_state"] == "PAUSE":
            # Show pause screen
            self.screen.fill("darkorange3")
            self._draw_dynamic_text(text="Paused. Press SPACE to continue.", font=1)

        #### EXIT, TERMINATION OR STREAM DISCONNECTION STATES
        elif self.state_dict["current_state"] == "EXIT":
            # Show experiment summary or exit instructions
            if self.state_dict["avg_time"] == None:
                self._draw_dynamic_text(text=self.state_dict["main_text"], y_position=0.45*self.height, font=1)     # Status text
                self._draw_dynamic_text(text=self.state_dict["sub_text"], y_position=0.55*self.height, font=4)      # Procedure instructions
            else:
                if self.state_dict["avg_time"] == 0:
                    time = "-- sec"
                    number = f'0/{str(self.state_dict["trials_No"])}'
                else:
                    time = f'{str(self.state_dict["avg_time"])} sec'
                    number =f'{str(self.state_dict["succ_trials"])}/{str(self.state_dict["trials_No"])}'

                self._draw_dynamic_text(text=self.state_dict["main_text"], y_position=0.3*self.height, font=1)                                  # Status text
                self._draw_dynamic_text(text=self.state_dict["sub_text"], x_position=self.width/2 - 10, y_position=0.4*self.height, font=4)     # Procedure instructions
                self._draw_dynamic_text("Avg. trial completition time:", x_position=0.6*self.width, y_position=0.55*self.height)                # Time results text
                self._draw_dynamic_text("Successful trials:", x_position=0.36*self.width, y_position=0.55*self.height)                          # Successfulness results text
                self._draw_dynamic_text(text=time, x_position=0.6*self.width, y_position=0.6*self.height)                                       # Time results
                self._draw_dynamic_text(text=number, x_position=0.36*self.width, y_position=0.6*self.height)                                    # Successfulness results

        #### ALL THE OTHER STATES
        #### BAND COLORING
        else:
            # Draw upper band
            p11 = pygame.Vector2(0, self.band_offset + self.pas/2)
            p12 = pygame.Vector2(self.width, self.band_offset + self.pas/2)
            if self.state_dict["trial"] == "UP":
                if self.state_dict["is_UP"]:
                    color = "green"    
                elif self.state_dict["is_DOWN"]:
                    color = "red"    
                elif not self.in_band and self.state_dict["current_state"] in {"TRIAL_UP", "MOVING_UP"}: 
                    color = self.state_dict["color"]
                else:
                    color = "black"
                pygame.draw.line(self.screen, color, p11, p12, width = self.pas)

            # Draw lower band
            p21 = pygame.Vector2(0, self.height - self.band_offset - self.pas/2)
            p22 = pygame.Vector2(self.width, self.height - self.band_offset - self.pas/2)
            if self.state_dict["trial"] == "DOWN":
                if self.state_dict["is_DOWN"]:
                    color = "green"    
                elif self.state_dict["is_UP"]:
                    color = "red"    
                elif not self.in_band and self.state_dict["current_state"] in {"TRIAL_DOWN", "MOVING_DOWN"}:
                    color = self.state_dict["color"]         
                else:
                    color = "black"                    
                pygame.draw.line(self.screen, color, p21, p22, width = self.pas)

            # Draw failure indication
            if self.state_dict["current_state"] == "FAILURE":
                if self.state_dict["is_UP"]:
                    pygame.draw.line(self.screen, "red", p11, p12, width = self.pas)
                elif self.state_dict["is_DOWN"]:
                    pygame.draw.line(self.screen, "red", p21, p22, width = self.pas)

            #### DRAW BANDS 
            # Draw white lines for band boundaries
            pygame.draw.line(self.screen, "white", (0, self.band_offset), (self.width, self.band_offset))                                                         # Top line of UPPER BAND
            pygame.draw.line(self.screen, "white", (0, self.band_offset + self.pas), (self.width, self.band_offset + self.pas))                                   # Bottom line of UPPER BAND
            pygame.draw.line(self.screen, "white", (0, self.height-self.band_offset), (self.width, self.height-self.band_offset))                                 # Bottom line of LOWER BAND
            pygame.draw.line(self.screen, "white", (0, self.height - self.band_offset - self.pas), (self.width, self.height - self.band_offset - self.pas))       # Top line of LOWER BAND 

            #### DRAW REMAINING TIME
            self._draw_dynamic_text(text=str(self.state_dict["remaining_time"]), x_position=0.88*self.width, y_position=0.55*self.height)

            #### DRAW TRIAL COUNTER
            self._draw_dynamic_text(text=f'{str(self.state_dict["current_trial_No"])}/{str(self.state_dict["trials_No"])}', x_position=0.1*self.width, y_position=0.55*self.height)

            #### DRAW ALL CONSTANT TEXTs
            # Draw static labels for bands and counters
            self.screen.blit(*self.UP_text)
            self.screen.blit(*self.DOWN_text)  
            self.screen.blit(*self.current_trial_text)
            self.screen.blit(*self.remaining_time_text)

            #### DRAW INSTRUCTIONS WHILE TRAIL IS IN PROGRESS
            # Show "UP" or "DOWN" instruction if trial is in progress and not in band
            UP_sign = self._create_static_text(text="UP", color=self.state_dict["color"], font=2, y_position=0.4*self.height)                                                           # UP instruction text
            DOWN_sign = self._create_static_text(text="DOWN", color=self.state_dict["color"], font=2, y_position=0.6*self.height)                                                       # DOWN instruction text    
            if not self.in_band:
                if self.state_dict["trial"] == "UP" and self.state_dict["trial_in_progress"]:
                    self.screen.blit(*UP_sign)
                elif self.state_dict["trial"] == "DOWN" and self.state_dict["trial_in_progress"]:
                    self.screen.blit(*DOWN_sign)
            
            #### RETURN TO CENTER TEXT AND TARGET CIRCLE
            # Show main instruction and target circle in relevant states
            if self.state_dict["current_state"] in {"RETURN_TO_CENTER", "IN_MIDDLE_CIRCLE", "WAITING", "IMAGINATION", "INTENTION", "TRIAL_UP", "TRIAL_DOWN"}:
                self._draw_dynamic_text(text=self.state_dict["main_text"], color="white", y_position=0.4*self.height, font=1)        
                pygame.draw.circle(self.screen, "white", (self.width/2, self.height/2), 1.3*self.dot_size + 3, width=2)              

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
            pygame.draw.circle(self.screen, "white", dot_pos, self.dot_size)

    def run(self, state_dict):
        """
        Runs the main GUI update and draw loop for a single frame.
        - Updates state from hardware
        - Draws all GUI elements
        - Handles window events (quit, resize)
        :param state_dict: state dictionary of main program
        :return: bool, whether to continue the experiment
        """
        dot_pos = self.update(state_dict)
        self.draw(dot_pos)

        pygame.display.update()
        self.clock.tick(60)

        # Handle window and quit events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.continue_experiment = False
            # Handle window resize
            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.w, event.h
                self.band_offset = int(round(60/820 * self.height))
                self.pas = int(round(60/820 * self.height))
                self.dot_size = int(round(6/820 * self.height + 4))
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                self.update_static_texts()

        return self.continue_experiment                        
    
    def _draw_dynamic_text(self, text="[SYSTEM]: No input given", color="white", background_color=None, x_position=None, y_position=None, font=3):
        """
        Draws dynamic (potentially changing) text on the screen at the given position and font.
        :param text: string to display
        :param color: text color
        :param background_color: background color for text
        :param x_position: x coordinate for text center
        :param y_position: y coordinate for text center
        :param font: font selector (1, 2, 3, or 4)
        """
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
        """
        Pre-renders static text for performance, returns the rendered surface and its rect.
        :param text: string to display
        :param color: text color
        :param background_color: background color for text
        :param x_position: x coordinate for text center
        :param y_position: y coordinate for text center
        :param font: font selector (1, 2, 3, or 4)
        :return: tuple (surface, rect)
        """
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
    
    def update_static_texts(self):
        """
        Pre-renders all static text labels for the GUI (band labels, counters).
        Should be called after resizing the window.
        """
        self.UP_text = self._create_static_text(text="UP", y_position=self.band_offset + self.pas/2, font=1)                                         # Upper band text
        self.DOWN_text = self._create_static_text(text="DOWN", y_position=self.height - self.band_offset - self.pas/2, font=1)                       # Lower band text
        self.current_trial_text = self._create_static_text(text='Current Trial', x_position=0.1*self.width, y_position=0.45*self.height)        # Current trial text
        self.remaining_time_text = self._create_static_text(text='Remaining Time', x_position=0.88*self.width, y_position=0.45*self.height)     # Remaining time text
    
    ### FOR RUNNING GUI IN THREAD
    def thread_run(self, stop_event, cont_lock):
        """
        Runs the GUI in a separate thread.
        - Calls update() and draw() in a loop
        - Handles quit events
        - Updates a global continue_experiment_g variable with a lock
        :param stop_event: threading.Event to signal stopping
        :param cont_lock: threading.Lock for continue_experiment_g
        """
        while not stop_event.is_set():
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
    # Example usage for testing the interface
    interface = Interface()
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
        interface.run(interface.state_dict)
        print(f' is_UP: {interface.state_dict["is_UP"]}, is_DOWN: {interface.state_dict["is_DOWN"]}, in_the_middle: {interface.state_dict["in_the_middle"]}, on_the_move: {interface.state_dict["on_the_move"]}, Current Position: {interface.state_dict["current_position"]}')

    pygame.quit()