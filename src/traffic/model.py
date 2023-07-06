import random
import warnings

import mesa
import json
import numpy as np
import pandas as pd
from mesa import DataCollector

from src.traffic.node import Node
from src.traffic.driver import Driver


class TrafficModel(mesa.Model):
    """
    Flocker model class. Handles agent creation, placement and scheduling.
    """

    def __init__(self, experiment,
                 measure_settings,read_agents=True, read_nodes=True):
        # random.seed(2990)
        drivers_json_file = "input_files/" + experiment + "/drivers.json"
        nodes_json_file = "input_files/" + experiment + "/lights.json"
        traffic_json_file = "input_files/" + experiment + "/traffic.json"
        self.agent_data_file = "output_files/" + experiment + "/agent_data.csv"
        self.finished = False
        self.delay_time = None
        self.fps = None
        self.torus = None
        self.n_lanes = None
        self.height = None
        self.n_nodes = None
        self.n_agents = None
        self.width = None
        self.datacollector = None
        self.time = 0
        self.measure_settings = measure_settings

        # Reading traffic_json config file
        self.read_traffic_from_file(traffic_json_file)
        self.nodes = []
        self.drivers = []
        self.schedule = mesa.time.BaseScheduler(self)
        self.lights_schedule = mesa.time.StagedActivation(self)
        self.space = mesa.space.ContinuousSpace(self.width, self.height, self.torus)

        # Reading nodes_json config file
        if read_nodes:
            self.read_nodes_from_file(nodes_json_file)
        else:
            self.make_nodes()
        # Reading drivers_json config file
        if read_agents:
            self.read_agent_from_file(drivers_json_file)

        # Initiation of Mesa data collector
        self.data_collector_init()

    def step(self):
        if not self.finished:
            self.time+=1
            if len(self.schedule.agents)==0:
                self.finished=True
            self.schedule.step()
            self.lights_schedule.step()
            self.datacollector.collect(self)
        else:
            return
    def setup_delays(self):
        delays_on_lanes = [0] * self.n_lanes
        for driver in self.schedule.agents:
            driver.delay = delays_on_lanes[driver.current_lane[0]]
            delays_on_lanes[driver.current_lane[0]] += self.delay_time



    # time measurements not relevant here
    def data_collector_save(self, tm = None):
        print("calculating measures like flow rate not implemented for basic TrafficModel!")
        agent_data = self.datacollector.get_agent_vars_dataframe()
        self.datacollector
        agent_data.to_csv(self.agent_data_file)

    def data_collector_init(self):
        self.datacollector = DataCollector(
            agent_reporters={
                "X": lambda a: a.pos[0],
                "Y": lambda a: a.pos[1],
                "Velocity": lambda a: a.velocity,
                "Current_lane": lambda a: a.current_lane[0],
                "Is_alive": lambda a: a.is_alive
            }
        )

    # Creates a node with equal distances
    def make_nodes(self):
        self.nodes.append(Node(model=self, unique_id=0, pos=(0, 0)))
        self.lights_schedule.add(self.nodes[-1])
        for i in range(1, self.n_nodes):
            node = Node(model=self, unique_id=i, pos=(i * self.width / (self.n_nodes - 1), 0))
            self.nodes.append(node)
            self.lights_schedule.add(node)

    def make_random_agents(self, n_agents, max_speed_avg, max_speed_dev, desired_distance_avg,
                           desired_distance_dev, acceleration_avg, acceleration_dev,
                           starting_id = 0):
        """
        Create self.n_agents agents
        """
        for i in range(starting_id, starting_id+n_agents):
            start_node = 0  # random.randint(0, 3)
            end_node = self.n_nodes - 1  # random.randint(start_node + 1, self.n_nodes - 1)
            current_lane = random.randint(0, self.n_lanes - 1)
            height_unit = self.height / (self.n_lanes * 2)  # used to calc where to put an agent (lane-based)
            pos = [self.nodes[start_node].pos[0], height_unit + current_lane * height_unit * 2]
            driver = Driver(driver_id=i,
                            model=self,
                            pos=pos,
                            car_size=20,
                            velocity=np.array([random.random() * max_speed_avg, 0]),
                            max_speed=max_speed_avg + (random.random() * 2 - 1) * max_speed_dev,
                            acceleration=acceleration_avg + (random.random() * 2 - 1) * acceleration_dev,
                            desired_distance=desired_distance_avg + (random.random() * 2 - 1) * desired_distance_dev,
                            current_lane=current_lane,
                            start_node=start_node,
                            end_node=end_node,
                            strategy=None)
            self.space.place_agent(driver, pos)
            self.schedule.add(driver)
            self.drivers.append(driver)
        self.setup_delays()

    def create_agent(self, unique_id, start, end, lane, velocity, max_speed, acceleration, desired_distance, strategy):
        height_unit = self.height / (self.n_lanes * 2)
        pos = (self.nodes[start].pos[0], height_unit + lane * height_unit * 2)
        if lane > self.n_lanes - 1:
            raise Exception("The driver can not be on line", lane)
        return Driver(driver_id=unique_id,
                      model=self,
                      pos=pos,
                      car_size=20,
                      velocity=velocity,
                      max_speed=max_speed,
                      acceleration=acceleration,
                      desired_distance=desired_distance,
                      current_lane=lane,
                      start_node=start,
                      end_node=end,
                      strategy=strategy)

    def read_agent_from_file(self, filename):
        with open(filename, "r") as read_file:
            data = json.load(read_file)
            for driver_json in data:
                driver = self.create_agent(unique_id=driver_json["unique_id"],
                                           # start=driver_json["start"],
                                           # end=driver_json["end"],
                                           start=0,  # all drivers start at 0, finishes at the last node
                                           end=len(self.nodes) - 1,
                                           lane=driver_json["lane"],
                                           velocity=np.array(driver_json["velocity"]),
                                           max_speed=driver_json["max_speed"],
                                           acceleration=driver_json["acceleration"],
                                           desired_distance=driver_json["desired_distance"],
                                           strategy=driver_json["strategy"])
                self.space.place_agent(driver, driver.pos[0])
                self.schedule.add(driver)
                self.drivers.append(driver)
            self.n_agents = len(self.schedule.agents)
            self.setup_delays()

    def read_traffic_from_file(self, filename):
        with open(filename, "r") as read_file:
            data = json.load(read_file)
            self.width = data["width"]
            self.height = data["height"]
            self.n_lanes = data["n_lane"]
            self.torus = data["torus"]
            self.fps = data["fps"]
            self.n_agents = data["n_agents"]
            self.delay_time = data["delay_time"]
            self.n_nodes = data["n_nodes"]

    def read_nodes_from_file(self, filename):
        with open(filename, "r") as read_file:
            data = json.load(read_file)
            for i, node_json in enumerate(data):
                node = Node(model=self,
                            unique_id=i,
                            pos=(node_json["pos"], 0),
                            durations=node_json["durations"],  # red,yellow,green
                            state=node_json["state"]
                            )
                self.nodes.append(node)
                self.lights_schedule.add(node)
            self.n_nodes = len(self.nodes)
