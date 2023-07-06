import mesa


class Node(mesa.Agent):
    def __init__(
            self,
            model,
            unique_id,
            pos,
            durations=[0, 0, 1],  # red,yellow,green
            state="red"
    ):
        super().__init__(unique_id, model)
        self.durations = durations
        self.phase = 0
        self.state = "red"
        self.pos = pos
        self.state = state

    def step(self):
        self.phase += 1
        if self.phase > sum(self.durations):
            self.phase = 0
        if 0 < self.phase <= self.durations[0]:
            self.state = "red"
        elif self.durations[0] < self.phase <= sum(self.durations[0:2]):
            self.state = "yellow"
        else:
            self.state = "green"
