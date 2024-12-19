# Example file showing a circle moving on screen
import pygame
from pylsl import StreamInlet, resolve_stream

width = 1280
height = 820
offset = 100
pas = 80
maxP = 180
minP = 55


green = (0, 255, 0)
blue = (0, 0, 128)


# Stream resolve
streams = resolve_stream('type', 'EXO')
inlet = StreamInlet(streams[0])
print("Receiving data...")

# pygame setup
pygame.init()
screen = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()
running = True
dt = 0

font = pygame.font.Font('freesansbold.ttf', 48) # Select font and size
font2 = pygame.font.Font('freesansbold.ttf', 100) # Select font and size

UP_text = font.render('UP', True, "white") # Text, Anti alias, Color
textRect_UP = UP_text.get_rect(center = (width/2, offset + pas/2)) # Location

DOWN_text = font.render('DOWN', True, "white") # Text, Anti alias, Color
textRect_DOWN = DOWN_text.get_rect(center = (width/2, height - offset - pas/2)) # Location

UP_sign = font2.render('UP', True, "white") # Text, Anti alias, Color
textRect_UP_sign = UP_sign.get_rect(center = (width/2, height/2)) # Location

DOWN_sign = font2.render('DOWN', True, "white") # Text, Anti alias, Color
textRect_DOWN_sign = DOWN_sign.get_rect(center = (width/2, height/2)) # Location


while running:

    sample, timestamp = inlet.pull_sample()
    loc = sample[0]
    loc = (loc / (maxP - minP) - minP / (maxP - minP)) * (height-2*offset) + offset 

    dot_pos = pygame.Vector2(width/2,  loc)
    
    # print(f'pos: {dot_pos}, pos:{sample[0]}')

    # fill the screen with a color to wipe away anything from last frame
    screen.fill("black")

    p1 = pygame.Vector2(0, offset + pas/2)
    p2 = pygame.Vector2(width, offset + pas/2)
    if loc < 0.9 * pas + offset:
        pygame.draw.line(screen, "green", p1, p2, width = pas)

    p1 = pygame.Vector2(0, height - offset - pas/2)
    p2 = pygame.Vector2(width, height - offset - pas/2)
    if loc > height - 0.9 * pas - offset:
        pygame.draw.line(screen, "green", p1, p2, width = pas)
    
    p1 = pygame.Vector2(0, offset)
    p2 = pygame.Vector2(width, offset)
    pygame.draw.line(screen, "white", p1, p2)

    p1 = pygame.Vector2(0, offset + pas)
    p2 = pygame.Vector2(width, offset + pas)
    pygame.draw.line(screen, "white", p1, p2)

    p1 = pygame.Vector2(0, height-offset)
    p2 = pygame.Vector2(width, height-offset)
    pygame.draw.line(screen, "white", p1, p2)

    p1 = pygame.Vector2(0, height - offset - pas)
    p2 = pygame.Vector2(width, height - offset - pas)
    pygame.draw.line(screen, "white", p1, p2)

    screen.blit(UP_text, textRect_UP)
    screen.blit(DOWN_text, textRect_DOWN)
    
    keys = pygame.key.get_pressed()
    if keys[pygame.K_DOWN]:
        screen.blit(DOWN_sign, textRect_DOWN_sign)
    elif keys[pygame.K_UP]:
        screen.blit(UP_sign, textRect_UP_sign)
    else:
        pygame.draw.circle(screen, "white", (width/2, height/2), 17, width= 2)
        if loc < height/2 + 5 and loc > height/2 - 5:
            pygame.draw.circle(screen, "green", (width/2, height/2), 16)
    
    # Draw dot
    pygame.draw.circle(screen, "red", dot_pos, 10)

    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # flip() the display to put your work on screen
    pygame.display.flip()

pygame.quit()

