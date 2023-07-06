import math
import random

import mesa
import numpy as np


class Driver(mesa.Agent):
    """
    A Driver agent.

    The agent follows N behaviors :

    """

    def __init__(
            self,
            driver_id,
            model,
            pos,
            car_size,
            velocity,
            max_speed,
            acceleration,
            desired_distance,
            current_lane,
            start_node,
            end_node,
            strategy
    ):
        """
        Create a new Driver  agent.

        Args:

        """
        super().__init__(driver_id, model)
        self.is_alive = False
        self.pos = pos,
        self.car_size = car_size
        self.max_speed = max_speed,
        self.acceleration = acceleration,
        self.velocity = velocity
        self.desired_distance = desired_distance
        self.current_lane = current_lane,
        self.start_node = start_node
        self.end_node = end_node
        self.delay = 0
        self.longlive = 0
        self.time_between_switches = 100
        self.last_switch = None

        # for calculating measuring timestamps
        self.t_start, self.t_end = None, None
        self.x_start_passed,self.x_end_passed=False, False

        # marking all previous nodes as already passed
        # and the rest that are still to be reached
        self.node_checkpoints = [True for _ in range(0, start_node + 1)]
        self.node_checkpoints += [False for _ in range(start_node + 1, model.n_nodes)]

        self.strategy = strategy

    def node_ahead(self):
        try:
            return self.model.nodes[self.node_checkpoints.index(False)]  ## error TODO
        except ValueError:
            return None  # we have arrived the destination

    def driver_ahead(self):
        min_distance = float("inf")
        ahead = None
        for d in self.model.schedule.agents:
            if (d.unique_id != self.unique_id) & (d.current_lane[0] is self.current_lane[0]):
                dist = d.pos[0] - self.pos[0]
                if min_distance > dist > 0:
                    min_distance = dist
                    ahead = d
        return ahead

    def step(self):
        """
        Get move accordingly.
        First check if you have just passed a new checkpoint(node) in the step.
        If so, mark it and check the lane according to your strategy
        """
        self.longlive += 1
        if self.longlive < self.delay:
            return

        node_ahead = self.node_ahead()
        driver_ahead = self.driver_ahead()

        if not self.is_alive:
            if driver_ahead is not None and (driver_ahead.pos[0] - self.pos[0]) < self.desired_distance:
                return
            self.is_alive = True

        # (re)calculate velocity and the new position
        self.calc_v(node_ahead, driver_ahead)
        new_pos = self.pos + self.velocity

        if new_pos[0] < self.model.nodes[-1].pos[0]:
            self.model.space.move_agent(self, new_pos)

        if self.pos[0]>self.model.measure_settings["x_start"] and not self.x_start_passed:
            self.t_start = self.model.time
            self.x_start_passed = True

        if self.pos[0] > self.model.measure_settings["x_end"] and not self.x_end_passed:
            self.t_end = self.model.time
            self.x_end_passed = True

        if driver_ahead is not None:
            if driver_ahead.velocity[0] - self.max_speed[0] < -0.001 and driver_ahead.pos[0] - self.pos[0] < 1.1 * self.desired_distance:
                self.switch_lane_if_possible()

        # check if a checkpoint is reached
        if node_ahead.pos[0] <= new_pos[0]:  # next_node is reached
            self.node_checkpoints[node_ahead.unique_id] = True  # set that checkpoint as reached
            # if the checkpoint is the last node in the model, kill the agent
            if node_ahead.unique_id == self.end_node or node_ahead.unique_id == self.model.n_nodes - 1:
                self.kill()
                return
            # self.switch_lane()

    def kill(self):
        self.model.schedule.remove(self)
        self.model.space.remove_agent(self)
        self.is_alive = False

    def calc_v(self, node_ahead, driver_ahead):
        """
        Function for recalculating velocity of the driver
        """
        is_freeway = False
        if driver_ahead is None:
            closer_obj_ahead = node_ahead
            if closer_obj_ahead.state == "green":
                is_freeway = True
        elif node_ahead.pos[0] < driver_ahead.pos[0]:
            closer_obj_ahead = node_ahead
            if closer_obj_ahead.state == "green":
                closer_obj_ahead = driver_ahead
        else:
            closer_obj_ahead = driver_ahead

        if is_freeway:
            if self.velocity[0] < self.max_speed[0]:
                self.velocity[0] += self.acceleration[0]
            if self.velocity[0] > self.max_speed[0]:
                self.velocity[0] = self.max_speed[0]
            return

        actual_distance = closer_obj_ahead.pos[0] - self.pos[0]
        if self.velocity[0] < self.max_speed[0]:
            max_speed = self.velocity[0] + self.acceleration[0]
            if max_speed > self.max_speed[0]:
                max_speed = self.max_speed[0]
        else:
            max_speed = self.max_speed[0]
        self.velocity[0] = max_speed * 0.5 * (
                np.tanh(actual_distance - self.desired_distance) + np.tanh(self.desired_distance))

    def accelerate(self):
        if self.velocity < self.max_speed[0]:
            self.velocity += self.acceleration[0]

    def teleport_left(self):
        self.current_lane = (self.current_lane[0] - 1,)
        new_pos = self.pos - (
            0, self.model.height / self.model.n_lanes)  # TODO add 'if there is a free space in the lane'
        self.model.space.move_agent(self, new_pos)

    def teleport_right(self):
        self.current_lane = (self.current_lane[0] + 1,)
        new_pos = (self.pos[0], self.pos[
            1] + self.model.height / self.model.n_lanes)  # TODO add 'if there is a free space in the lane'
        self.model.space.move_agent(self, new_pos)

    def teleport_to_lane(self, lane):
        self.current_lane = (lane,)
        new_pos = (self.pos[0], (
                lane + 1.5) + self.model.height / self.model.n_lanes)  # TODO add 'if there is a free space in the lane'
        self.model.space.move_agent(self, new_pos)

    def __str__(self):
        return f"Driver {self.unique_id} at pos({self.pos}),\n lane({self.current_lane[0]}), start_node({self.start_node})" \
               f", end_node({self.end_node}), velocity({self.velocity})"

    def switch_lane_if_possible(self):
        # car switching lanes too often (flashing like) fixed here:
        if self.last_switch is not None:
            if self.longlive - self.last_switch < self.time_between_switches:
                return
        self.last_switch = self.longlive

        right_possible, left_possible = False, False
        if self.current_lane[0] > 0:
            left_possible = True
        if self.current_lane[0] < self.model.n_lanes - 1:
            right_possible = True

        for driver in self.model.drivers:

            if driver.is_alive and (abs(self.pos[0] - driver.pos[0]) < 0.8 * self.desired_distance):
                if driver.current_lane[0] == self.current_lane[0] - 1:
                    left_possible = False
                elif driver.current_lane[0] == self.current_lane[0] + 1:
                    right_possible = False
        if right_possible and left_possible:
            if random.choice([True, False]):
                self.teleport_right()
            else:
                self.teleport_right()
            return
        if right_possible:
            self.teleport_right()
        if left_possible:
            self.teleport_left()

