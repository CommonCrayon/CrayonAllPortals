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
ORIGIN_NODE = 0


def build_distance_matrix(coords: list[list[int]], dummy_end_node: int) -> tuple[list[list[int]], list[list[bool]]]:
    '''
    Precompute an N x N integer distance matrix.

    A player can always warp back to the origin (spawn) before heading to their 
    next stronghold, so the real cost of a leg (i -> j) is whichever is cheaper: 
    flying there directly, or resetting to spawn first and flying from there.

    origin_reset_matrix[i][j] records which case won, so the origin option
    is never lost when the previous-point pass compares against this matrix later.
    '''
    n = len(coords)
    matrix = [[0] * n for _ in range(n)]

    def euclid(a: int, b: int) -> float:
        return math.hypot(coords[a][1] - coords[b][1], coords[a][2] - coords[b][2])

    for i in range(n):
        for j in range(n):
            # self-loops and "transition into end" cost 0
            if i == j or j == dummy_end_node:
                continue

            real_distance = euclid(i, j)

            if i == ORIGIN_NODE:
                # already at the origin - nothing to reset to
                matrix[i][j] = round(real_distance)
                continue

            origin_distance = euclid(ORIGIN_NODE, j)
            if origin_distance < real_distance:
                matrix[i][j] = round(origin_distance)
            else:
                matrix[i][j] = round(real_distance)

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

    # Create solution
    solution = routing.SolveWithParameters(params)

    # If no solution return nothing
    if not solution:
        return [[] for _ in range(num_players)], [0.0] * num_players
    
    # Calculate Route for each Player
    player_routes: list[list[list[int]]] = []

    for player_id in range(num_players):

        index = routing.Start(player_id)
        nodes = [manager.IndexToNode(index)]
        while not routing.IsEnd(index):
            index = solution.Value(routing.NextVar(index))
            nodes.append(manager.IndexToNode(index))

        current_route: list[list[int]] = []
        total_distance = 0.0

        for k in range(len(nodes) - 1):
            cur_node = nodes[k]
            next_node = nodes[k + 1]

            # Respawning at spawn costs nothing.
            if next_node == dummy_end_node:
                break  

            leg_cost = distance_matrix[cur_node][next_node]

            # k >= 2 means there's another stronghold (not the origin) before cur_node. Which might be a shorter path
            if k >= 2:
                prev_node = nodes[k - 1]
                previous_leg_cost = distance_matrix[prev_node][next_node]
                if previous_leg_cost < leg_cost:
                    leg_cost = previous_leg_cost

            total_distance += leg_cost

            sh_num, x, z = strongholds[next_node - 1]
            current_route.append([sh_num, x, z])

        player_routes.append(current_route)

    return player_routes