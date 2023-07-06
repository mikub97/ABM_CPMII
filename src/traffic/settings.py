experiment = "experiment-traffic-lights"
measure_settings = {
    "x_start": 200,
    "x_end": 800,
    "measure_point_x": 500,
    "accepted_dist_delta": 10,
    "window_size": 100,
    "rolling_average_density_running_step": 5,
    "rolling_average_flow_running_step": 100
}
#  measures 1
# sessions = []
# for dev in [0.1,0.2,0.3,0.4,0.5]:
#     for i in range(10):
#         for n in [1,2,3]:
#                 sessions.append({
#                                "n_agents": 40,
#                                "max_speed_avg": 1.5,
#                                "max_speed_dev": dev,
#                                "desired_distance_avg": 30,
#                                "desired_distance_dev": 0,
#                                "acceleration_avg": 0.02,
#                                "acceleration_dev": 0.005,
#                                "n_lanes": n
#                            })
#
# print(sessions)

 # measures 2
sessions = []
for v in [0.5,0.6,0.7,0.8,0.9,1,1.1,1.2,1.3,1.4,1.5]:
    for i in range(10):
        sessions.append({
                       "n_agents": 40,
                       "max_speed_avg": v,
                       "max_speed_dev": v*0.2, # odchylenie 20%
                       "desired_distance_avg": 30,
                       "desired_distance_dev": 0,
                       "acceleration_avg": 0.02,
                       "acceleration_dev": 0.005,
                       "n_lanes": 2
                   })

print(sessions)