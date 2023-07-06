from src.traffic.gui import GUI
import os

from src.traffic.model import TrafficModel
from src.traffic.repetitive_model import RepetitiveTrafficModel
from src.traffic.settings import measure_settings, sessions, experiment

os.makedirs(os.path.dirname("output_files/" + experiment + "/"), exist_ok=True)
gui = GUI(RepetitiveTrafficModel(
    experiment=experiment,
    measure_settings= measure_settings,
    sessions=sessions,
))
gui.run()
