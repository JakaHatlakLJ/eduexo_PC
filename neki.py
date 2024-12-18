# Example file showing a circle moving on screen
import pygame
from pylsl import StreamInlet, resolve_stream

width = 1280
height = 720
offset = 100
maxP = 180
minP = 55


green = (0, 255, 0)
blue = (0, 0, 128)


# Stream resolve
streams = resolve_stream('type', 'EEG')
inlet = StreamInlet(streams[0])
print("Receiving data...")

# pygame setup
pygame.init()
screen = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()
running = True
dt = 0

# dot_pos = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)





font = pygame.font.Font('freesansbold.ttf', 48) # Select font and size

UP_text = font.render('UP', True, "white") # Text, Anti alias, Color
textRect_UP = UP_text.get_rect(center = (screen.get_width() / 2, 1.5 * offset)) # Location

DOWN_text = font.render('DOWN', True, "white") # Text, Anti alias, Color
textRect_DOWN = DOWN_text.get_rect(center = (screen.get_width() / 2, height - 1.5 * offset)) # Location


while running:



    sample, timestamp = inlet.pull_sample()
    loc = sample[0]
    loc = (loc / (maxP - minP) - minP / (maxP - minP)) * (screen.get_height()-2*offset) + offset 

    dot_pos = pygame.Vector2(screen.get_width() / 2,  loc)
    
    print(f'pos: {dot_pos}, pos:{sample[0]}')

    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # fill the screen with a color to wipe away anything from last frame
    screen.fill("black")

    p1 = pygame.Vector2(0, 1.5 * offset)
    p2 = pygame.Vector2(width, 1.5 * offset)
    if loc < 1.9 * offset:
        pygame.draw.line(screen, "green", p1, p2, width = offset)

    p1 = pygame.Vector2(0, height - 1.5 * offset)
    p2 = pygame.Vector2(width, height - 1.5 * offset)
    if loc > height - 1.9 * offset:
        pygame.draw.line(screen, "green", p1, p2, width = offset)
    
    p1 = pygame.Vector2(0, offset)
    p2 = pygame.Vector2(width, offset)
    pygame.draw.line(screen, "white", p1, p2)

    p1 = pygame.Vector2(0, 2*offset)
    p2 = pygame.Vector2(width, 2*offset)
    pygame.draw.line(screen, "white", p1, p2)

    p1 = pygame.Vector2(0, height-offset)
    p2 = pygame.Vector2(width, height-offset)
    pygame.draw.line(screen, "white", p1, p2)

    p1 = pygame.Vector2(0, height-2*offset)
    p2 = pygame.Vector2(width, height-2*offset)
    pygame.draw.line(screen, "white", p1, p2)

    screen.blit(UP_text, textRect_UP)
    screen.blit(DOWN_text, textRect_DOWN)
    # Draw dot
    pygame.draw.circle(screen, "red", dot_pos, 10)

    # flip() the display to put your work on screen
    pygame.display.flip()

pygame.quit()