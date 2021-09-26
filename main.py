import pygame
import os
import random
import neat

pygame.font.init()

# Game resolution
WIN_WIDTH = 500
WIN_HEIGHT = 800

# Variable for display on which gen we are
GEN = 0

# Initialization of screen
win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

pygame.display.set_caption('Flappy Birds')

# Creating variables for sprites
BIRD_IMGS = [
    pygame.transform.scale2x(pygame.image.load(os.path.join('Images', 'bird1.png'))),
    pygame.transform.scale2x(pygame.image.load(os.path.join('Images', 'bird2.png'))),
    pygame.transform.scale2x(pygame.image.load(os.path.join('Images', 'bird3.png')))
]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join('Images', 'pipe.png')))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join('Images', 'base.png')))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join('Images', 'bg.png')))

STAT_FONT = pygame.font.SysFont('comicsans', 50)

class Bird:
    """
    Bird class representing the flappy bird
    """
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        """
        That's how the bird moving arc: is starts with speed -10.5 (if we jumped) pixels per minute(going up), and with
        every tick it velocity decreasing by this formula. For example:
        d(1) = -10.5*1+1.5*1 = -9 -> But it's -2 'cause of the condition (still going up);
        ...;
        d(7) = -10,5*7+1,5*49 = 0 (now the bird's velocity is 0);
        d(8) = -10,5*8+1,5*64 = 12 (the bird starts going down);
        If velocity is 0 from the start, than the speed of falling will increase, of course
        :return: None
        """
        self.tick_count += 1

        d = self.vel*self.tick_count + 1.5*self.tick_count**2

        # Max speed of falling
        if d >= 16:
            d = 16

        # Max speed of going up
        if d < 0:
            d -= 2

        self.y = self.y + d

        # If bird is moving up from the init jump position we tilt it upward, and, when it's lower than init jump pos,
        # we tilt it down
        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        self.img_count += 1

        # Creating the fly animation
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # If bird is going down than we need only spreaded wings sprite
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

        # Rotating the bird
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        """
        Instead of doing the rectangle for collision we can create a mask which covers the sprite
        :return: Object
        """
        return pygame.mask.from_surface(self.img)


class Pipe:
    """
    represents a pipe object
    """
    GAP = 200
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.gap = 100

        self.top = 0
        self.bottom = 0

        # We flip the image of pipe not by X (False), but by Y (True)
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        """
        Here we can check if the bird crashed into the pipes or not
        :param bird: Object
        :return: bool
        """
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:
            return True

        return False


class Base:
    """
    represents a base (moving floor) object
    """
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        """
        In real we create two sprites of the base. And when first going from the right side, the second one replaces it.
        It works with the second-one situation too.
        :return: None
        """
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        """
        Draw the floor. This is two images that move together.
        :param win: the pygame surface/window
        :return: None
        """
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, birds, pipes, base, score, gen):
    win.blit(BG_IMG, (0, 0))

    for pipe in pipes:
        pipe.draw(win)

    scr = STAT_FONT.render('Score: ' + str(score), True, (255, 255, 255))
    win.blit(scr, (WIN_WIDTH - 10 - scr.get_width(), 10))

    gn = STAT_FONT.render('Generation: ' + str(gen), True, (255, 255, 255))
    win.blit(gn, (10, 10))

    brd = STAT_FONT.render('Birds: ' + str(len(birds)), True, (255, 255, 255))
    win.blit(brd, (10, gn.get_height() + 10))

    base.draw(win)

    for bird in birds:
        bird.draw(win)

    pygame.display.update()


def main(genomes, config):
    """
    runs the simulation of the current population of
    birds and sets their fitness based on the distance they
    reach in the game
    """
    global GEN
    GEN += 1
    nets = []
    ge = []
    score = 0
    birds = []

    for _, g in genomes:
        # net is for controlling movements of each bird: net[0] => birds[0]
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)

        birds.append(Bird(230, 350))

        # g[0] => birds[0]
        g.fitness = 0
        ge.append(g)

    base = Base(730)
    pipes = [Pipe(700)]

    # Exit-condition from the loop
    run = True

    clock = pygame.time.Clock()

    while run:
        # FPS
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

        pipe_ind = 0

        if len(birds) > 0:
            # If birds already have passed the first pipe on the screen and there are two pipes at the same time
            # then birds are working with the second one
            if len(pipes) > 1 and birds[0].x > pipes[0].PIPE_TOP.get_width() + pipes[0].x:
                pipe_ind = 1
        else:
            run = False
            break

        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += .1

            # send bird location, top pipe location and bottom pipe location and determine from network whether to jump or not
            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            # we use a tanh activation function so result will be between -1 and 1. if over 0.5 jump
            if output[0] > 0.5:
                bird.jump()

        add_pipe = False
        rem = []

        base.move()

        for pipe in pipes:
            pipe.move()

            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[x].fitness -= 1
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(600))

        # Deleting the pipe that went out of the screen
        for r in rem:
            pipes.remove(r)

        # We delete the bird if it's too high or too low
        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        # We stop the programme after the bird reaches 50 scores
        if score > 10:
            break

        draw_window(win, birds, pipes, base, score, GEN)


def run(config_path):
    """
    runs the NEAT algorithm to train a neural network to play flappy bird.
    :param config_file: location of config file
    :return: None
    """
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)
    p = neat.Population(config)

    # After every gen we can see stats about this gen
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # We start the main program for 50 times (generations)
    winner = p.run(main, 50)

    # show final stats
    print('\nBest genome:\n{!s}'.format(winner))


if __name__ == '__main__':
    # Determine path to configuration file. This path manipulation is
    # here so that the script will run successfully regardless of the
    # current working directory.
    local_directory = os.path.dirname(__file__)
    config_path = os.path.join(local_directory, 'config_feedforward.txt')
    run(config_path)
