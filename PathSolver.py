import math
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

OR_SCALE = 10_000


def solve_multi_player_paths(points: list[list], num_players: int, time_limit_sec: int) -> tuple[list[list], list[float]]:

    if not points or num_players <= 0:
        return [[] for _ in range(num_players)], [0.0] * num_players

    # Node 0: Origin (0, 0)
    # Nodes 1..N: Real strongholds
    # Node N+1: Dummy end node (unconstrained finish)
    coords = [(-1, 0, 0)] + points + [(-2, 0, 0)]
    dummy_end_node = len(coords) - 1

    # Setup RoutingIndexManager:
    # All vehicles start at Node 0 and end at dummy_end_node
    manager = pywrapcp.RoutingIndexManager(
        len(coords),
        num_players,
        [0] * num_players,              # starts
        [dummy_end_node] * num_players  # ends
    )
    
    routing = pywrapcp.RoutingModel(manager)

    # Distance matrix callback
    def arc_cost(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        
        if from_node == to_node:
            return 0
        
        # Zero cost to transition into the dummy end node
        if to_node == dummy_end_node:
            return 0

        # High cost if transitioning out of dummy node (should never happen)
        if from_node == dummy_end_node:
            return 0

        dist = math.hypot(coords[from_node][1] - coords[to_node][1], coords[from_node][2] - coords[to_node][2])
        return int(dist * OR_SCALE)

    transit_cb = routing.RegisterTransitCallback(arc_cost)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_cb)

    # Add Distance Dimension
    dimension_name = "Distance"
    routing.AddDimension(
        transit_cb,
        0,
        3_000_000 * OR_SCALE,
        True,
        dimension_name
    )
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    distance_dimension.SetGlobalSpanCostCoefficient(100)

    # Search parameters
    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.seconds = time_limit_sec

    solution = routing.SolveWithParameters(params)
    if not solution:
        return [[] for _ in range(num_players)], [0.0] * num_players

    # Extract global routes and exact distance per vehicle
    player_routes = []
    player_distances = []

    for vehicle_id in range(num_players):
        index = routing.Start(vehicle_id)
        route = []
        route_dist_scaled = 0

        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            next_index = solution.Value(routing.NextVar(index))
            
            # Accumulate transit cost (will automatically be 0 for the jump to dummy_end_node)
            route_dist_scaled += routing.GetArcCostForVehicle(index, next_index, vehicle_id)
            
            # Ignore origin (node 0) and dummy end node
            if node != 0 and node != dummy_end_node:
                sh_num, x, z = points[node - 1]
                route.append([sh_num, x, z])
                
            index = next_index

        player_routes.append(route)
        player_distances.append(route_dist_scaled / OR_SCALE)

    return player_routes, player_distances