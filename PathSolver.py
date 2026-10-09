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


def build_distance_matrix(coords: list[list[int]], dummy_end_node: int, advanced_pathing: bool) -> list[list[int]]:
    '''
    Precompute an N x N integer distance matrix.

    With advanced_pathing, a player can warp back to the origin (spawn) before
    heading to their next stronghold, so the cost of a leg (i -> j) is whichever
    is cheaper: flying directly, or resetting to spawn first and flying from there.

    Without advanced_pathing, the cost is always the direct distance i -> j.
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

            # Only consider the spawn-reset option in advanced mode
            if advanced_pathing and i != ORIGIN_NODE:
                real_distance = min(real_distance, euclid(ORIGIN_NODE, j))

            matrix[i][j] = round(real_distance)

    return matrix


def solve_player_paths(strongholds: list[list[int]], num_players: int, computation_time: int, advanced_pathing: bool) -> list[list[list[int]]]:
    """
    Partition strongholds into paths.
    """
    num_paths = (num_players + 1) // 2

    if not strongholds or num_players <= 0:
        return [[] for _ in range(num_paths)]

    has_solo_path = num_players % 2 == 1
    solo_path_id = num_paths - 1 if has_solo_path else None

    # Coordinate list: origin + strongholds (+ dummy end node for the solo path)
    coords = [[-1, 0, 0]] + strongholds
    dummy_end_node = -1  # never matches a real node
    if has_solo_path:
        coords.append([-2, 0, 0])
        dummy_end_node = len(coords) - 1

    # Every path starts at spawn. Paired paths end at spawn, the solo path ends at the dummy node.
    end_nodes = [ORIGIN_NODE] * num_paths
    if has_solo_path:
        end_nodes[solo_path_id] = dummy_end_node

    manager = pywrapcp.RoutingIndexManager(len(coords), num_paths, [ORIGIN_NODE] * num_paths, end_nodes)
    routing = pywrapcp.RoutingModel(manager)

    distance_matrix = build_distance_matrix(coords, dummy_end_node, advanced_pathing)

    def make_callback(weight: int):
        def arc_cost(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return distance_matrix[from_node][to_node] * weight
        return routing.RegisterTransitCallback(arc_cost)

    normal_callback = make_callback(1)
    solo_callback = make_callback(2)  # solo path counts double -> balances to half length

    vehicle_callbacks = []
    for path_id in range(num_paths):
        cb = solo_callback if path_id == solo_path_id else normal_callback
        vehicle_callbacks.append(cb)
        routing.SetArcCostEvaluatorOfVehicle(cb, path_id)

    # Upper bound for the Distance dimension (x2 for weighting, +1 edge for the return leg)
    max_edge = max(max(row) for row in distance_matrix)
    max_route_distance = max_edge * (len(strongholds) + 1) * 2

    routing.AddDimensionWithVehicleTransits(vehicle_callbacks, 0, max_route_distance, True, "Distance")
    distance_dimension = routing.GetDimensionOrDie("Distance")
    distance_dimension.SetGlobalSpanCostCoefficient(SPAN_COST_COEFFICIENT)

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.LOCAL_CHEAPEST_COST_INSERTION

    if num_paths > 1:
        params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH

    params.time_limit.seconds = computation_time

    solution = routing.SolveWithParameters(params)
    if not solution:
        return [[] for _ in range(num_paths)]

    player_routes: list[list[list[int]]] = []

    for path_id in range(num_paths):
        index = routing.Start(path_id)
        nodes = [manager.IndexToNode(index)]
        while not routing.IsEnd(index):
            index = solution.Value(routing.NextVar(index))
            nodes.append(manager.IndexToNode(index))

        current_route: list[list[int]] = []

        for node in nodes:
            # Skip spawn (start/return) and the solo path's dummy end node
            if node == ORIGIN_NODE or node == dummy_end_node:
                continue

            sh_num, x, z = strongholds[node - 1]
            current_route.append([sh_num, x, z])

        player_routes.append(current_route)

    return player_routes