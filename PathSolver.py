import math
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

OR_SCALE = 10_000

"""
Main Path Solver.
"""
def solve_multi_player_paths(strongholds: list[list], num_players: int, computation_time: int) -> tuple[list[list], list[float]]:

    # Return if paths can not be formed.
    if not strongholds or num_players <= 0:
        return [[] for _ in range(num_players)], [0.0] * num_players

    # Coordinate list: Start at [0 0] + stronghold list + dummy end node
    coords = [(-1, 0, 0)] + strongholds + [(-2, 0, 0)]
    dummy_end_node = len(coords) - 1 # Dummy that is cost of 0.

    # Setup RoutingIndexManager:
    # All paths start at [0, 0] and end whereever best (dummy_end_node).
    manager = pywrapcp.RoutingIndexManager(len(coords), num_players, [0] * num_players, [dummy_end_node] * num_players)
    routing = pywrapcp.RoutingModel(manager)

    # Distance matrix callback
    def arc_cost(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        
        # if nodes are the same, then return 0
        if from_node == to_node:
            return 0
        
        # if destination is dummy_end_node, then return 0 and finish path.
        if to_node == dummy_end_node:
            return 0

        distance = math.hypot(coords[from_node][1] - coords[to_node][1], coords[from_node][2] - coords[to_node][2])

        # TODO
        # Check for distance from previous node too.
        # Check for distance form 0 0 too. 
        # As it is very easy to get to both locations.

        return int(distance * OR_SCALE)

    transit_callback = routing.RegisterTransitCallback(arc_cost)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback)

    # Add Distance Dimension
    dimension_name = "Distance"
    routing.AddDimension(transit_callback, 0, 3_000_000 * OR_SCALE, True, dimension_name)
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    distance_dimension.SetGlobalSpanCostCoefficient(100)

    # Search parameters
    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
    params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.seconds = computation_time

    solution = routing.SolveWithParameters(params)

    # Return if solution fails.
    if not solution:
        return [[] for _ in range(num_players)], [0.0] * num_players


    # Lists to be returned
    player_routes = []
    player_distances = []

    # Create a route for each player
    for player_id in range(num_players):
        index = routing.Start(player_id)
        route = []
        route_dist_scaled = 0

        # Creating Route
        while not routing.IsEnd(index):

            current_node = manager.IndexToNode(index)
            next_index = solution.Value(routing.NextVar(index))
            
            # Accumulate transit cost
            route_dist_scaled += routing.GetArcCostForVehicle(index, next_index, player_id)
            
            # Ignore start orgin node [0 0] and dummy end node. Otherwise append route
            if current_node != 0 and current_node != dummy_end_node:
                sh_num, x, z = strongholds[current_node - 1]
                route.append([sh_num, x, z])
                
            index = next_index

        # Append to list to be returned.
        player_routes.append(route)
        player_distances.append(route_dist_scaled / OR_SCALE)

    return player_routes, player_distances