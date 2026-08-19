# =============================================================
# Pool Game Tutorial
# coded along by Jose "Joe" Ruiz
#
# This project is based on the excellent tutorial by:
# Coding with Russ
# Tutorial Video: https://www.youtube.com/watch?v=txcOqDhrwBo
# - Uses pygame-ce
# - Uses pymunk for physics
# - Adds constants, pathlib asset paths, and clearer naming
# - Modernized for clarity, readability, and 2026 Python practices
# =============================================================

# ---------- Import modules ----------
import pygame
import pymunk
import pymunk.pygame_util
import math
from pathlib import Path

# ---------- Pygame Initialization ----------
pygame.init()

# ---------- Paths & Assets Setup ----------
# Use pathlib so paths are clean and cross-platform
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets" / "images"

# ---------- Screen / Layout Constants ----------
SCREEN_WIDTH  = 1200
SCREEN_HEIGHT = 678
BOTTOM_PANEL  = 50

# Create the main window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT + BOTTOM_PANEL))
pygame.display.set_caption("Pool made with Pygame/Pymunk")

# ---------- Physics (PyMunk) Setup ----------
space = pymunk.Space()
static_body = space.static_body

# Optional: tweak global physics behavior
space.damping = 0.99  # slight damping so balls eventually stop

# Helper for drawing physics shapes (for debugging)
draw_options = pymunk.pygame_util.DrawOptions(screen)

# ---------- Timing ----------
clock = pygame.time.Clock()
FPS = 120  # high FPS for smooth physics

# ---------- Game Constants ----------
LIVES_START          = 3
BALL_DIAMETER        = 36
POCKET_DIAMETER      = 66
CUE_MAX_FORCE        = 10000
CUE_FORCE_STEP       = 100
CUE_POWER_BAR_WIDTH  = 10
CUE_POWER_BAR_HEIGHT = 20
CUE_POWER_BAR_STEP   = 15
CUE_POWER_DIVISOR    = 2000

# ---------- Game State Variables ----------
lives           = LIVES_START
force           = 0
max_force       = CUE_MAX_FORCE
force_direction = 1
game_running    = True
cue_ball_potted = False
taking_shot     = True
powering_up     = False

potted_balls    = []

# ---------- Colors (RGB) ----------
BG    = ( 50,  50,  50)
RED   = (255,   0,   0)
WHITE = (255, 255, 255)

# ---------- Fonts ----------
font       = pygame.font.SysFont("Lato", 30)
large_font = pygame.font.SysFont("Lato", 60)

# ---------- Load Images ----------
# Use pathlib paths and convert_alpha() for proper transparency
cue_image_path   = ASSETS_DIR / "cue.png"
table_image_path = ASSETS_DIR / "table.png"

cue_image   = pygame.image.load(str(cue_image_path)).convert_alpha()
table_image = pygame.image.load(str(table_image_path)).convert_alpha()

ball_images = []
for i in range(1, 17):
    ball_image_path = ASSETS_DIR / f"ball_{i}.png"
    ball_image = pygame.image.load(str(ball_image_path)).convert_alpha()
    ball_images.append(ball_image)

# ---------- Helper: Draw Text ----------
def draw_text(text, font, text_col, x, y):
    """ Render text onto the screen at a given position. """
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

# ---------- Helper: Create a Ball ----------
def create_ball(radius, pos):
    """
    Create a pool ball with:
    - a dynamic body (it can move)
    - a circular shape
    - elasticity (bounciness)
    - a pivot joint to simulate friction
    """
    body = pymunk.Body()
    body.position = pos

    shape = pymunk.Circle(body, radius)
    shape.mass = 5
    shape.elasticity = 0.8

    # Pivot joint used to emulate friction against the table
    pivot = pymunk.PivotJoint(static_body, body, (0, 0), (0, 0))
    pivot.max_bias = 0      # disable joint correction
    pivot.max_force = 1000  # emulate linear friction

    space.add(body, shape, pivot)
    return shape

# ---------- Setup Game Balls ----------
balls = []
rows = 5  # number of rows in the triangle rack

# Create the triangle of balls (the rack)
for col in range(5):
    for row in range(rows):
        # Position formula to create the triangle layout
        pos = (
            250 + (col * (BALL_DIAMETER + 1)),
            267 + (row * (BALL_DIAMETER + 1)) + (col * BALL_DIAMETER / 2)
        )
        new_ball = create_ball(BALL_DIAMETER / 2, pos)
        balls.append(new_ball)
    rows -= 1  # each column has one fewer ball

# ---------- Cue Ball ----------
cue_ball_start_pos = (888, SCREEN_HEIGHT / 2)
cue_ball = create_ball(BALL_DIAMETER / 2, cue_ball_start_pos)
balls.append(cue_ball)

# ---------- Pockets ----------
# Six pockets: top-left, top-middle, top-right, bottom-left, bottom-middle, bottom-right
pockets = [
    (55, 63),
    (592, 48),
    (1134, 64),
    (55, 616),
    (592, 629),
    (1134, 616)
]

# ---------- Cushions ----------
# Each cushion is defined by a polygon (list of points)
cushions = [
    [(88, 56), (109, 77), (555, 77), (564, 56)],
    [(621, 56), (630, 77), (1081, 77), (1094, 56)],
    [(89, 621), (110, 600), (556, 600), (564, 621)],
    [(622, 621), (630, 600), (1081, 600), (1094, 621)],
    [(56, 96), (77, 117), (77, 560), (56, 581)],
    [(1143, 96), (1122, 117), (1122, 560), (1143, 581)]
]

# ---------- Helper: Create Cushion ----------
def create_cushion(poly_dims):
    """
    Create a static cushion:
    - Static body (doesn't move)
    - Polygon shape
    - Elasticity for bouncy collisions
    """
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    body.position = (0, 0)
    shape = pymunk.Poly(body, poly_dims)
    shape.elasticity = 0.8

    space.add(body, shape)

# Add all cushions to the physics space
for cushion_points in cushions:
    create_cushion(cushion_points)

# ---------- Cue Class ----------
class Cue:
    """
    Represents the pool cue:
    - Stores the original image
    - Rotates based on angle
    - Draws centered around the cue ball
    """
    def __init__(self, pos):
        self.original_image = cue_image
        self.angle = 0
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect()
        self.rect.center = pos

    def update(self, angle):
        """ Update the cue's angle (in degrees.) """
        self.angle = angle

    def draw(self, surface):
        """ Draw the rotated cue image centered on its rect. """
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        surface.blit(
            self.image,
            (
                self.rect.centerx - self.image.get_width() / 2,
                self.rect.centery - self.image.get_height() / 2
            )
        )

# Create the cue positioned at the cue ball
cue = Cue(balls[-1].body.position)

# ---------- Power Bar ----------
# Small red rectangles that show how strong the shot will be
power_bar = pygame.Surface((CUE_POWER_BAR_WIDTH, CUE_POWER_BAR_HEIGHT))
power_bar.fill(RED)

# ---------- Main Game Loop ----------
run = True

while run:
    # --- Timing & Physics Step ---
    dt = 1 / FPS
    clock.tick(FPS)
    space.step(dt)

    # --- Draw Background & Table ---
    screen.fill(BG)
    screen.blit(table_image, (0, 0))

    # --- Check for Potted Balls ---
    for i, ball in enumerate(balls):
        for pocket in pockets:
            ball_x_dist = abs(ball.body.position[0] - pocket[0])
            ball_y_dist = abs(ball.body.position[1] - pocket[1])
            ball_dist = math.sqrt((ball_x_dist ** 2) + (ball_y_dist ** 2))

            if ball_dist <= POCKET_DIAMETER / 2:
                # If the cue ball is potted (last ball in list)
                if i == len(balls) -1:
                    lives -= 1
                    cue_ball_potted = True
                    # Move cue ball off-screen and stop it
                    ball.body.position = (-100, -100)
                    ball.body.velocity = (0.0, 0.0)
                else:
                    # Remove regular ball from physics and list
                    space.remove(ball.body)
                    balls.remove(ball)
                    potted_balls.append(ball_images[i])
                    ball_images.pop(i)

    # --- Draw Pool Balls ---
    for i, ball in enumerate(balls):
        screen.blit(
            ball_images[i],
            (
                ball.body.position[0] - ball.radius,
                ball.body.position[1] - ball.radius
            )
        )

    # --- Check if All Balls Have Stopped Moving ---
    taking_shot = True
    for ball in balls:
        # If any ball has non-zero velocity, we are still in motion
        if int(ball.body.velocity[0]) != 0 or int(ball.body.velocity[1]) != 0:
            taking_shot = False

    # --- Draw Pool Cue When Ready to Shoot ---
    if taking_shot and game_running:
        if cue_ball_potted:
            # Reposition cue ball to starting spot
            balls[-1].body.position = cue_ball_start_pos
            cue_ball_potted = False

        # Calculate cue angle based on mouse position
        mouse_pos = pygame.mouse.get_pos()
        cue.rect.center = balls[-1].body.position

        x_dist = balls[-1].body.position[0] - mouse_pos[0]
        # Negative because screen y increases downward
        y_dist = -(balls[-1].body.position[1] - mouse_pos[1])

        cue_angle = math.degrees(math.atan2(y_dist, x_dist))
        cue.update(cue_angle)
        cue.draw(screen)

    # --- Powering Up the Cue (Holding Mouse Button) ---
    if powering_up and game_running:
        # Increase or decrease force based on direction
        force += CUE_FORCE_STEP * force_direction

        # Reverse direction when hitting limits
        if force >= max_force or force <= 0:
            force_direction *= -1

        # Draw power bars near the cue ball
        bars_to_draw = math.ceil(force / CUE_POWER_DIVISOR)
        for b in range(bars_to_draw):
            screen.blit(
                power_bar,
                (
                    balls[-1].body.position[0] - 30 + (b * CUE_POWER_BAR_STEP),
                    balls[-1].body.position[1] + 30
                )
            )

    # --- Release Shot (Mouse Button Up) ---
    elif not powering_up and taking_shot:
        # Convert angle to impulse direction
        x_impulse = math.cos(math.radians(cue_angle))
        y_impulse = math.sin(math.radians(cue_angle))

        # Apply impulse to cue (negative x because of angle orientation)
        balls[-1].body.apply_impulse_at_local_point(
            (force * -x_impulse, force * y_impulse),
            (0, 0)
        )

        # Reset force for next shot
        force = 0
        force_direction = 1

    # --- Bottom Panel (UI) ---
    pygame.draw.rect(screen, BG, (0, SCREEN_HEIGHT, SCREEN_WIDTH, BOTTOM_PANEL))
    draw_text(f"LIVES: {lives}", font, WHITE, SCREEN_WIDTH - 200, SCREEN_HEIGHT + 10)

    # Draw potted balls in the bottom panel
    for i, ball_img in enumerate(potted_balls):
        screen.blit(ball_img, (10 + (i * 50), SCREEN_HEIGHT + 10))

    # --- Game Over / Win Messages ---
    if lives <= 0:
        draw_text(
            "GAME OVER",
            large_font,
            WHITE,
            SCREEN_WIDTH / 2 - 160,
            SCREEN_HEIGHT / 2 - 100
        )
        game_running = False

    if len(balls) == 1:
        draw_text(
            "You WIN!!",
            large_font,
            WHITE,
            SCREEN_WIDTH / 2 - 160,
            SCREEN_HEIGHT / 2 - 100
        )
        game_running = False

    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN and taking_shot:
            powering_up = True

        if event.type == pygame.MOUSEBUTTONUP and taking_shot:
            powering_up = False

        if event.type == pygame.QUIT:
            run = False

    # Optional: show physics shapes for debugging
    # space.debug_draw(draw_options)

    # --- Flip Display ---
    pygame.display.update()

# ---------- Clean Exit ----------
pygame.quit()
