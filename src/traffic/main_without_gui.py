import os
from src.traffic.repetitive_model import RepetitiveTrafficModel
from src.traffic.settings import sessions, measure_settings, experiment

os.makedirs(os.path.dirname("output_files/" + experiment + "/"), exist_ok=True)

model =RepetitiveTrafficModel(experiment=experiment,
                              measure_settings=measure_settings,
                              sessions=sessions)
while not model.finished:
    model.step()

print("Simulation finished, calculating and saving the measures...")
model.data_collector_save()
print("...done.")