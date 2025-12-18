import math
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

OR_SCALE = 10_000


def make_stronghold_list(points: list[tuple], time_per_path: int):
    
    # Add 0 0 coordinate for start origin
    coords = [(-1, 0, 0)] + points

    # OR-Tools setup
    manager = pywrapcp.RoutingIndexManager(
        len(coords),
        1,  # one route
        0   # start at spawn
    )
    routing = pywrapcp.RoutingModel(manager)


    # True cost callback
    def arc_cost(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)

        if from_node == to_node:
            return 0
        
        distance = math.hypot(coords[from_node][1] - coords[to_node][1], coords[from_node][2] - coords[to_node][2])
        return int(distance * OR_SCALE)


    transit_cb = routing.RegisterTransitCallback(arc_cost)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_cb)

    # path search parameters
    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    params.local_search_metaheuristic = (routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    params.time_limit.seconds = time_per_path


    # Solve for best path
    solution = routing.SolveWithParameters(params)
    assert solution, "No solution found"


    # Extract route (skip spawn nodes)
    index = routing.Start(0)
    route = []

    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        if node != 0:
            route.append(node - 1)  # shift back to points index
        index = solution.Value(routing.NextVar(index))

    
    # Final Path list
    strongholds = []
    for idx in route:
        sh_num, x, z = points[idx]
        strongholds.append([sh_num, x, z])

    return strongholds

