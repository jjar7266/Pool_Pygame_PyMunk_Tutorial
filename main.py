# My header will go up here
# etc.

# Import modules
import pygame
import pymunk
import pymunk.pygame_util
import math

# Initialize Pygame
pygame.init()

# Setup game window
SCREEN_WIDTH  = 1200
SCREEN_HEIGHT = 678

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pool made with Pygame/Pymunk")

# PyMunk Space
space = pymunk.Space()
static_body = space.static_body

draw_options = pymunk.pygame_util.DrawOptions(screen)

# Clock
clock = pygame.time.Clock()
FPS = 120

# Game Variables
dia = 36

# Load Images
cue_image = pygame.image.load("assets/images/cue.png").convert_alpha()
table_image = pygame.image.load("assets/images/table.png").convert_alpha()

ball_images = []
for i in range(1, 17):
    ball_image = pygame.image.load(f"assets/images/ball_{i}.png").convert_alpha()
    ball_images.append(ball_image)

# COLORs (RGB)
BG  = ( 50,  50,  50)
RED = (255,   0,   0)

# Function for creating balls
def create_ball(radius, pos):
    body = pymunk.Body()
    body.position = pos
    shape = pymunk.Circle(body, radius)
    shape.mass = 5
    shape.elasticity = 0.8

    # Use pivot joint to add friction
    pivot = pymunk.PivotJoint(static_body, body, (0, 0), (0, 0))
    pivot.max_bias = 0      # disable joint correction
    pivot.max_force = 1000  # emulate linear friction


    space.add(body, shape, pivot)
    return shape

# Setup game balls
balls = []
rows = 5

# potting balls
for col in range(5):
    for row in range(rows):
        pos = (250 + (col * (dia + 1)), 267 + (row * (dia + 1)) + (col * dia / 2))
        new_ball = create_ball(dia / 2, pos)
        balls.append(new_ball)
    rows -= 1

# Cue Ball
pos = (888, SCREEN_HEIGHT / 2)
cue_ball = create_ball(dia / 2, pos)
balls.append(cue_ball)

# Create pool table cushions
cushions = [
    [(88, 56), (109, 77), (555, 77), (564, 56)],
    [(621, 56), (630, 77), (1081, 77), (1102, 56)],
    [(89, 621), (110, 600), (556, 600), (564, 621)],
    [(622, 621), (630, 600), (1081, 600), (1102, 621)],
    [(56, 96), (77, 117), (77, 560), (56, 581)],
    [(1143, 96), (1122, 117), (1122, 560), (1143, 581)]
]

# Function for creating cushions
def create_cushion(poly_dims):
    body = pymunk.Body(body_type = pymunk.Body.STATIC)
    body.position = ((0, 0))
    shape = pymunk.Poly(body, poly_dims)
    shape.elasticity = 0.8

    space.add(body, shape)

for c in cushions:
    create_cushion(c)

# Create Pool Cue
class Cue():
    def __init__(self, pos):
        self.original_image = cue_image
        self.angle = 0
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect()
        self.rect.center = pos


    def update(self, angle):
        self.angle = angle


    def draw(self, surface):
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        surface.blit(self.image,)


cue = Cue(balls[-1].body.position)

# Game Loop
run = True

while run:

    clock.tick(FPS)
    space.step(1 / FPS)

    # Fill background
    screen.fill(BG)

    # Draw Pool Table
    screen.blit(table_image, (0, 0))

    # Draw Pool Balls
    for i, ball in enumerate(balls):
        screen.blit(ball_images[i], (ball.body.position[0] - ball.radius, ball.body.position[1] - ball.radius))

    # Draw Pool Cue
    # calculate pool cue angle
    mouse_pos = pygame.mouse.get_pos()
    x_dist = balls[-1].body.position[0] - mouse_pos[0]
    y_dist = -(balls[-1].body.position[1] - mouse_pos[1])  # negative because y coordinates increase down the screen
    cue_angle = math.degrees(math.atan2(y_dist, x_dist))
    cue.update(cue_angle)

    cue.draw(screen)


    # Event handler
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            cue_ball.body.apply_impulse_at_local_point((-1500, 0), (0, 0))


    #space.debug_draw(draw_options)
    pygame.display.update()

pygame.quit()

