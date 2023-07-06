import warnings

import pygame
from pygame.locals import *

from src.traffic.model import TrafficModel

pygame.font.init()
pygame.mixer.init()
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
FONT = pygame.font.SysFont('comicsans', 13)

class Car(pygame.sprite.Sprite):
    def __init__(self, driver,gui):
        super().__init__()
        self.driver = driver
        self.gui = gui
        self.image = pygame.Surface((driver.car_size, driver.car_size))
        self.image.fill(WHITE)  # Replace with car image loading or drawing logic
        self.rect = self.image.get_rect()
        self.rect.center = (driver.pos[0], 0)
        self.is_visible = driver.is_alive
        self.text_surface = FONT.render(str(self.driver.unique_id), True, BLACK)
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)
        pygame.Surface.blit(self.image, self.text_surface, (driver.car_size / 4, 0))

    def update(self):
        if self.driver is None or self.driver.pos is None:
            self.kill()
            # print(f"The driver {self.driver.unique_id} is DEAD")
            return
        self.is_visible = self.driver.is_alive
        self.rect.x = self.gui.screen_width* (self.driver.pos[0]/self.driver.model.width)
        self.rect.y = self.gui.screen_height* (self.driver.pos[1]/self.driver.model.height)


class GUI:
    def __init__(self, model):
        pygame.init()
        self.clock = pygame.time.Clock()
        self.is_running = True
        self.model = model
        self.screen_width = 1200
        self.screen_height = 200
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.lane_width = model.height / model.n_lanes
        self.height_unit = model.height / (model.n_lanes * 2)
        self.node_size = 20
        self.fps = model.fps
        self.t = 0
        self.time_measures = []
        pygame.display.set_caption("Traffic")

        self.cars = None

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.is_running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.is_running = False
                if event.key == K_SPACE:
                    print(f"Step nr. {self.t}")
                    self.time_measures.append(self.t)

        keys = pygame.key.get_pressed()
        slow_down_drivers = []
        # Perform actions based on key states
        if keys[K_9]:
            self.model.drivers[0].max_speed = (self.model.drivers[0].max_speed[0] - 0.001,)
            print("Driver 1 max speed is", self.model.drivers[0].max_speed)
        elif keys[K_0]:
            self.model.drivers[0].max_speed = (self.model.drivers[0].max_speed[0] + 0.001,)
            print("Driver 1 max speed is", self.model.drivers[0].max_speed)
        if keys[K_1]:
            self.model.drivers[10].max_speed = (self.model.drivers[10].max_speed[0] - 0.001,)
            print("Driver 10 max speed is", self.model.drivers[10].max_speed)
        elif keys[K_2]:
            self.model.drivers[10].max_speed = (self.model.drivers[10].max_speed[0] + 0.001,)
            print("Driver 10 max speed is", self.model.drivers[10].max_speed)


    def update(self):
        self.model.step()
        self.t+=1

        self.cars = pygame.sprite.Group()
        for driver in self.model.schedule.agents:
            if driver.is_alive:
                self.cars.add(Car(driver,self))

    def render(self):
        self.screen.fill((255, 255, 255))
        # Draw GUI elements here
        self.draw_window()
        self.cars.update()
        self.draw_window()
        self.cars.draw(self.screen)  # Draw all the sprites
        pygame.display.flip()

    def draw_node(self, node, is_final=False):
        if node.state == "red":
            col = RED
        elif node.state == "yellow":
            col = YELLOW
        else:
            col = GREEN
        if (is_final):
            pygame.draw.rect(self.screen, col, (self.screen_width*(node.pos[0]/self.model.width) - self.node_size, 0, self.node_size, self.node_size))
            text_render = FONT.render(str(node.unique_id), True, WHITE)
            text_rect = text_render.get_rect(
                center=(self.screen_width*(node.pos[0]/self.model.width) - self.node_size + self.node_size // 2, 0 + self.node_size // 2))
            self.screen.blit(text_render, text_rect)
        else:
            pygame.draw.rect(self.screen, col, (self.screen_width*(node.pos[0]/self.model.width), 0, self.node_size, self.node_size))
            text_render = FONT.render(str(node.unique_id), True, WHITE)
            text_rect = text_render.get_rect(center=(self.screen_width*(node.pos[0]/self.model.width) + self.node_size // 2, 0 + self.node_size // 2))
            self.screen.blit(text_render, text_rect)
            pygame.draw.line(self.screen, WHITE, (self.screen_width*(node.pos[0]/self.model.width), 0), (self.screen_width*(node.pos[0]/self.model.width), self.screen_height))

    def draw_window(self):
        lane_width = self.screen_height / self.model.n_lanes
        self.screen.fill(BLACK)
        for i in range(self.model.n_lanes):
            pygame.draw.line(self.screen, WHITE, (0, lane_width * i), (self.screen_width, lane_width * i))

        for node in self.model.nodes[:-1]:
            self.draw_node(node, False)
        self.draw_node(self.model.nodes[-1], True)

    def run(self):
        pygame.display.flip()
        while self.is_running and not self.model.finished:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(self.fps)
        print("Simulation finished, calculating and saving the measures...")
        self.model.data_collector_save()
        print("...done.")

        pygame.quit()


if __name__ == "__main__":
    gui = GUI(TrafficModel())
    gui.run()
