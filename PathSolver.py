"""
Multi-player stronghold routing using OR-Tools' vehicle routing solver.
"""

import math
from ortools.constraint_solver import pywrapcp, routing_enums_pb2


'''
Weight on the gap between the longest and shortest player route. 
Higher values push the solver harder toward evenly balanced routes, 
at some cost to total distance across all players.
'''
SPAN_COST_COEFFICIENT = 100
NETHER_SCALE = 8

def build_distance_matrix(coords: list[list[int]], dummy_end_node: int) -> list[list[int]]:
    '''
    Precompute an N x N integer distance matrix.
    '''
    n = len(coords)
    matrix = [[0] * n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            # self-loops and "transition into end" cost 0
            if i == j or j == dummy_end_node:
                continue  

            matrix[i][j] = round(math.hypot(coords[i][1] - coords[j][1], coords[i][2] - coords[j][2]))

    return matrix


def solve_player_paths(strongholds: list[list[int]], num_players: int, computation_time: int) -> list[list[list[int]]]:
    """
    Partition strongholds among players and route each player to theirs.
    """
    if not strongholds or num_players <= 0:
        return [[] for _ in range(num_players)], [0.0] * num_players

    # Coordinate list: origin [0, 0] + strongholds + dummy end node.
    coords = [[-1, 0, 0]] + strongholds + [[-2, 0, 0]]
    dummy_end_node = len(coords) - 1

    manager = pywrapcp.RoutingIndexManager(len(coords), num_players, [0] * num_players, [dummy_end_node] * num_players)
    routing = pywrapcp.RoutingModel(manager)

    distance_matrix = build_distance_matrix(coords, dummy_end_node)

    def arc_cost(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)

        return distance_matrix[from_node][to_node]

    transit_callback = routing.RegisterTransitCallback(arc_cost)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback)

    # Upper bound for the Distance dimension 
    max_edge = max(max(row) for row in distance_matrix)
    max_route_distance = max_edge * len(strongholds)

    routing.AddDimension(transit_callback, 0, max_route_distance, True, "Distance")
    distance_dimension = routing.GetDimensionOrDie("Distance")
    distance_dimension.SetGlobalSpanCostCoefficient(SPAN_COST_COEFFICIENT)

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.LOCAL_CHEAPEST_COST_INSERTION

    if num_players > 1:
        params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    
    params.time_limit.seconds = computation_time


    solution = routing.SolveWithParameters(params)
    if not solution:
        return [[] for _ in range(num_players)], [0.0] * num_players
    

    player_routes: list[list[list[int]]] = []

    for player_id in range(num_players):
        index = routing.Start(player_id)
        route: list[list[int]] = []

        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)

            if node != 0 and node != dummy_end_node:
                sh_num, x, z = strongholds[node - 1]
                route.append([sh_num, x, z])

            index = solution.Value(routing.NextVar(index))

        player_routes.append(route)

    return player_routes