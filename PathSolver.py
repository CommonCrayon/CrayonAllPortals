"""
Multi-player stronghold routing using OR-Tools' vehicle routing solver.

Players are paired onto shared spawn -> spawn loops (P1 + P2 on path 1, P3 + P4 on path 2, ...).
With an odd player count the last player gets a solo path that doesn't return to spawn.

Time model:
    A path's time = (strongholds x STRONGHOLD_SECONDS + nether blocks travelled / TRAVEL_SPEED) / path speed.
    The solver balances that time across paths (mostly minimising the slowest path), so it weighs an
    extra stronghold (5 minutes) against the travel it saves rather than splitting strongholds evenly.

Player weights:
    Each player has a weight (how fast they are compared to the others). A path's speed is the sum of
    its players' weights, so a weight 2 player is expected to get through strongholds and travel twice
    as fast and is handed about twice the work.

Path optimisers (each can be switched on or off):
    spawn_reset:  don't place a bed, so the next death respawns you at world spawn and you
                  travel from spawn to the next stronghold.
    previous_bed: don't place a new bed, so the next death respawns you at the bed you already
                  have set (left at an earlier stronghold) and you travel from there.
"""

import math
import random
import time
from ortools.constraint_solver import pywrapcp, routing_enums_pb2


NETHER_SCALE = 8
ORIGIN_NODE = 0

TRAVEL_SPEED = 30          # nether blocks per second between strongholds
STRONGHOLD_SECONDS = 300   # time to find and fill a stronghold's portal

'''
Weight on the gap between the slowest and fastest path time.
Higher values push the solver harder toward every path finishing at the same time,
at some cost to total time across all players.
'''
SPAN_COST_COEFFICIENT = 100

'''
OR-Tools needs integer costs, so path times are counted in units of 1 / TIME_RESOLUTION seconds.
'''
TIME_RESOLUTION = 100

DEFAULT_PLAYER_WEIGHT = 1
MIN_PLAYER_WEIGHT = 0.1
MAX_PLAYER_WEIGHT = 10

'''
The previous-bed optimiser depends on where the player's bed was left, which OR-Tools' arc costs
can't express. When it's on, OR-Tools gets this share of the computation time and a bed-aware
local search spends the rest improving the routes.
'''
ORTOOLS_TIME_SHARE = 2 / 3
REFINE_BEAM_WIDTH = 8      # bed locations tracked per leg while refining (exact for planning)
REFINE_NEIGHBOURS = 8      # nearest strongholds considered for each move
REFINE_MAX_SEGMENT = 3     # longest run of strongholds moved in one go

REPORT_INTERVAL = 0.25     # seconds between progress updates sent to the app


#======================================================================================================================
# Players -> paths
#======================================================================================================================

def group_players(num_players: int) -> list[list[int]]:
    '''
    Player indices on each path: [[0, 1], [2, 3], ...], with the last path solo if the count is odd.
    '''
    return [list(range(i, min(i + 2, num_players))) for i in range(0, num_players, 2)]


def path_speeds(player_weights: list[float]) -> list[float]:
    '''
    Combined weight of the players on each path.
    '''
    return [sum(player_weights[p] for p in group) for group in group_players(len(player_weights))]


def path_seconds(num_strongholds: int, overworld_distance: float, speed: float) -> float:
    '''
    Estimated time for a path: doing its strongholds plus travelling it, shared by its players.
    '''
    return (num_strongholds * STRONGHOLD_SECONDS + overworld_distance / NETHER_SCALE / TRAVEL_SPEED) / speed


#======================================================================================================================
# Respawn planning
#======================================================================================================================

def _route_cost(route: list[int], dist: list[list[float]], closed: bool, spawn_reset: bool, previous_bed: bool, beam: int | None = None) -> float:
    '''
    Cheapest overworld distance of a route of node indices (ORIGIN_NODE = spawn) given the enabled optimisers.

    Before leaving stronghold k for the next one the player respawns at one of:
        - a bed placed at stronghold k (always allowed)
        - world spawn, by not placing a bed (spawn_reset)
        - the bed they already have set at an earlier stronghold (previous_bed)

    States map "where the bed currently is" -> cheapest cost so far (ORIGIN_NODE = no bed / spawn).
    With beam set, only the cheapest few bed locations are tracked (fast, near-exact).
    '''
    if not route:
        return 0.0

    origin_row = dist[ORIGIN_NODE]
    states = {ORIGIN_NODE: origin_row[route[0]]}
    last = len(route) - 1

    for k, here in enumerate(route):
        if k < last:
            target = route[k + 1]
        elif closed:
            target = ORIGIN_NODE
        else:
            break

        best = min(states.values())
        new_states = {here: best + dist[here][target]}

        if spawn_reset:
            new_states[ORIGIN_NODE] = best + origin_row[target]

        if previous_bed:
            for bed, cost in states.items():
                if bed == ORIGIN_NODE:
                    continue
                value = cost + dist[bed][target]
                if value < new_states.get(bed, math.inf):
                    new_states[bed] = value

        if beam and len(new_states) > beam:
            new_states = dict(sorted(new_states.items(), key=lambda item: item[1])[:beam])

        states = new_states

    return min(states.values())


def plan_route(stops: list[list[int]], closed: bool, spawn_reset: bool, previous_bed: bool) -> tuple[float, list[dict | None]]:
    '''
    Exact respawn plan for a route of [stronghold_id, x, z] stops.

    Returns (total overworld distance, legs) where legs[k] describes the leg leaving stops[k]:
        {"option": "here" | "spawn" | "keep", "distance": float, "saving": float}
    "saving" is how much shorter the leg is than respawning at a bed placed at stops[k].
    legs[k] is None when stops[k] has no leg after it (end of a solo path).
    For a closed route the last entry is the return leg to spawn.
    '''
    if not stops:
        return 0.0, []

    points = [(0, 0)] + [(stop[1], stop[2]) for stop in stops]
    dist = [[math.hypot(a[0] - b[0], a[1] - b[1]) for b in points] for a in points]
    route = list(range(1, len(points)))
    last = len(route) - 1

    states = {ORIGIN_NODE: dist[ORIGIN_NODE][route[0]]}
    layers = []  # per leg: new bed -> (previous bed, option)

    for k, here in enumerate(route):
        if k < last:
            target = route[k + 1]
        elif closed:
            target = ORIGIN_NODE
        else:
            break

        best_bed = min(states, key=states.get)
        best = states[best_bed]

        new_states = {here: best + dist[here][target]}
        back = {here: (best_bed, "here")}

        if spawn_reset:
            new_states[ORIGIN_NODE] = best + dist[ORIGIN_NODE][target]
            back[ORIGIN_NODE] = (best_bed, "spawn")

        if previous_bed:
            for bed, cost in states.items():
                if bed == ORIGIN_NODE:
                    continue
                value = cost + dist[bed][target]
                if value < new_states.get(bed, math.inf):
                    new_states[bed] = value
                    back[bed] = (bed, "keep")

        layers.append((target, back))
        states = new_states

    # Walk back from the cheapest final state to recover each leg's respawn point
    bed = min(states, key=states.get)
    total = states[bed]

    legs: list[dict | None] = [None] * len(route)
    for k in reversed(range(len(layers))):
        target, back = layers[k]
        previous, option = back[bed]
        here = route[k]

        distance = dist[bed][target]
        legs[k] = {"option": option, "distance": distance, "saving": dist[here][target] - distance}
        bed = previous

    return total, legs


#======================================================================================================================
# Progress reporting
#======================================================================================================================

class ProgressReporter:
    '''
    Tracks what the solver is doing and sends snapshots through send(info), at most every REPORT_INTERVAL
    seconds unless the stage changes.

    info = {
        "stage":            what the solver is doing right now
        "improvements":     better solutions found so far
        "last_improvement": time.time() of the latest better solution (or None)
        "first_total":      nether blocks of the first solution (or None)
        "total":            nether blocks of the best solution (or None)
        "paths":            per path of the best solution: {"count": strongholds, "distance": nether blocks,
                            "seconds": estimated time (see path_seconds)} (or None)
        "routes":           best solution as [[id, x, z], ...] per path, for drawing (or None)
    }
    Distances use the exact respawn plan for the enabled optimisers, same as "Copy for NavAssist".
    '''

    def __init__(self, send, strongholds: list[list[int]], dist: list[list[float]], closed: list[bool], speeds: list[float], spawn_reset: bool, previous_bed: bool):
        self.send = send
        self.speeds = speeds
        self.strongholds = strongholds
        self.dist = dist
        self.closed = closed
        self.spawn_reset = spawn_reset
        self.previous_bed = previous_bed

        self.info = {"stage": "", "improvements": 0, "last_improvement": None, "first_total": None, "total": None, "paths": None, "routes": None}
        self.node_routes = None
        self.dirty = False
        self.last_sent = 0.0

    def stage(self, text: str):
        self.info["stage"] = text
        self.flush(force=True)

    def improved(self, node_routes: list[list[int]]):
        self.node_routes = [list(route) for route in node_routes]
        self.info["improvements"] += 1
        self.info["last_improvement"] = time.time()
        self.dirty = True
        self.flush()

    def flush(self, force: bool = False):
        now = time.monotonic()
        if not force and (not self.dirty or now - self.last_sent < REPORT_INTERVAL):
            return

        if self.dirty:
            self._summarise()

        self.last_sent = now
        self.send(dict(self.info))

    def _summarise(self):
        overworld = [_route_cost(route, self.dist, self.closed[p], self.spawn_reset, self.previous_bed) for p, route in enumerate(self.node_routes)]
        distances = [d / NETHER_SCALE for d in overworld]
        seconds = [path_seconds(len(route), d, self.speeds[p]) for p, (route, d) in enumerate(zip(self.node_routes, overworld))]
        total = sum(distances)

        if self.info["first_total"] is None:
            self.info["first_total"] = total

        self.info["total"] = total
        self.info["paths"] = [{"count": len(route), "distance": d, "seconds": t} for route, d, t in zip(self.node_routes, distances, seconds)]
        self.info["routes"] = [[list(self.strongholds[node - 1]) for node in route] for route in self.node_routes]
        self.dirty = False


#======================================================================================================================
# OR-Tools
#======================================================================================================================

def build_distance_matrix(coords: list[list[int]], dummy_end_node: int, spawn_reset: bool) -> list[list[float]]:
    '''
    Precompute an N x N distance matrix.

    With spawn_reset, a player can warp back to the origin (spawn) before
    heading to their next stronghold, so the cost of a leg (i -> j) is whichever
    is cheaper: flying directly, or resetting to spawn first and flying from there.

    Without spawn_reset, the cost is always the direct distance i -> j.
    '''
    n = len(coords)
    matrix = [[0.0] * n for _ in range(n)]

    def euclid(a: int, b: int) -> float:
        return math.hypot(coords[a][1] - coords[b][1], coords[a][2] - coords[b][2])

    for i in range(n):
        for j in range(n):
            # self-loops and "transition into end" cost 0
            if i == j or j == dummy_end_node:
                continue

            real_distance = euclid(i, j)

            # Only consider the spawn-reset option when it's enabled
            if spawn_reset and i != ORIGIN_NODE:
                real_distance = min(real_distance, euclid(ORIGIN_NODE, j))

            matrix[i][j] = real_distance

    return matrix


def solve_player_paths(strongholds: list[list[int]], player_weights: list[float], computation_time: int, spawn_reset: bool = False, previous_bed: bool = False, progress=None) -> list[list[list[int]]]:
    """
    Partition strongholds into paths, one per pair of players (plus a solo path for an odd player out).

    progress: optional callable receiving ProgressReporter snapshots while solving.
    """
    groups = group_players(len(player_weights))
    num_paths = len(groups)

    if not strongholds or num_paths == 0:
        return [[] for _ in range(num_paths)]

    speeds = path_speeds(player_weights)
    closed = [len(group) == 2 for group in groups]

    has_solo_path = not closed[-1]
    solo_path_id = num_paths - 1 if has_solo_path else None

    deadline = time.monotonic() + computation_time
    ortools_time = computation_time * ORTOOLS_TIME_SHARE if previous_bed else computation_time

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

    # Plain distances between origin + strongholds, for progress reports and the bed-aware refinement
    points = coords[:len(strongholds) + 1]
    dist = [[math.hypot(a[1] - b[1], a[2] - b[2]) for b in points] for a in points]

    reporter = ProgressReporter(progress, strongholds, dist, closed, speeds, spawn_reset, previous_bed) if progress else None
    if reporter:
        reporter.stage("Finding a first solution")

    manager = pywrapcp.RoutingIndexManager(len(coords), num_paths, [ORIGIN_NODE] * num_paths, end_nodes)
    routing = pywrapcp.RoutingModel(manager)

    distance_matrix = build_distance_matrix(coords, dummy_end_node, spawn_reset)

    # Arc cost = time: travelling i -> j plus doing stronghold i, divided by the path's speed
    # (faster paths get cheaper arcs, so balancing time hands them more work)
    callback_functions = []  # keep the Python callbacks alive while OR-Tools uses them
    callbacks_by_speed = {}
    vehicle_callbacks = []
    max_edge = 0

    def make_callback(time_matrix: list[list[int]]):
        def arc_cost(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return time_matrix[from_node][to_node]
        callback_functions.append(arc_cost)
        return routing.RegisterTransitCallback(arc_cost)

    for path_id in range(num_paths):
        speed = speeds[path_id]
        key = round(speed, 9)

        if key not in callbacks_by_speed:
            time_matrix = []
            for i, row in enumerate(distance_matrix):
                stronghold_time = 0 if i == ORIGIN_NODE or i == dummy_end_node else STRONGHOLD_SECONDS
                time_matrix.append([round((stronghold_time + d / NETHER_SCALE / TRAVEL_SPEED) * TIME_RESOLUTION / speed) for d in row])
            max_edge = max(max_edge, max(max(row) for row in time_matrix))
            callbacks_by_speed[key] = make_callback(time_matrix)

        cb = callbacks_by_speed[key]
        vehicle_callbacks.append(cb)
        routing.SetArcCostEvaluatorOfVehicle(cb, path_id)

    # Upper bound for the Time dimension (+1 edge for the return leg)
    max_route_time = max_edge * (len(strongholds) + 1)

    routing.AddDimensionWithVehicleTransits(vehicle_callbacks, 0, max_route_time, True, "Time")
    time_dimension = routing.GetDimensionOrDie("Time")
    time_dimension.SetGlobalSpanCostCoefficient(SPAN_COST_COEFFICIENT)

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.LOCAL_CHEAPEST_COST_INSERTION

    if num_paths > 1:
        params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH

    params.time_limit.seconds = max(1, int(ortools_time))

    def read_routes(next_index) -> list[list[int]]:
        '''Node routes (strongholds only, no spawn / dummy end), following next_index(index) from each start.'''
        node_routes = []
        for path_id in range(num_paths):
            index = routing.Start(path_id)
            nodes = [manager.IndexToNode(index)]
            while not routing.IsEnd(index):
                index = next_index(index)
                nodes.append(manager.IndexToNode(index))
            node_routes.append([node for node in nodes if node != ORIGIN_NODE and node != dummy_end_node])
        return node_routes

    # Report every better solution OR-Tools finds
    if reporter:
        best_cost = [None]

        def on_solution():
            cost = routing.CostVar().Value()
            if best_cost[0] is not None and cost >= best_cost[0]:
                return
            if best_cost[0] is None:
                reporter.info["stage"] = "Improving routes"
            best_cost[0] = cost
            reporter.improved(read_routes(lambda index: routing.NextVar(index).Value()))

        callback_functions.append(on_solution)
        routing.AddAtSolutionCallback(on_solution)

    solution = routing.SolveWithParameters(params)
    if not solution:
        return [[] for _ in range(num_paths)]

    node_routes = read_routes(lambda index: solution.Value(routing.NextVar(index)))

    # Make the routes bed-aware with whatever time is left
    if previous_bed:
        if reporter:
            reporter.stage("Planning around beds")
        on_improve = reporter.improved if reporter else None
        node_routes = refine_routes(node_routes, closed, speeds, dist, spawn_reset, previous_bed, deadline, on_improve=on_improve)

    if reporter:
        reporter.flush(force=True)

    return [[list(strongholds[node - 1]) for node in route] for route in node_routes]


def solve_in_background(result_queue, solver_args: dict):
    '''
    Process entry point: solve and send ("done", routes) or ("error", message) back to the app,
    with ("progress", info) snapshots along the way.
    Running in a separate process keeps the window responsive while OR-Tools works.
    '''
    try:
        routes = solve_player_paths(**solver_args, progress=lambda info: result_queue.put(("progress", info)))
        result_queue.put(("done", routes))
    except Exception as error:
        result_queue.put(("error", f"{type(error).__name__}: {error}"))


#======================================================================================================================
# Bed-aware refinement
#======================================================================================================================

def refine_routes(routes: list[list[int]], closed: list[bool], speeds: list[float], dist: list[list[float]], spawn_reset: bool, previous_bed: bool, deadline: float, on_improve=None) -> list[list[int]]:
    '''
    Local search over the routes using the real respawn-aware cost, minimising the same
    objective as OR-Tools: total time + SPAN_COST_COEFFICIENT * longest path time.

    Moves (first improvement, nearest-neighbour candidates only):
        - relocate a run of 1..REFINE_MAX_SEGMENT strongholds (either direction) next to a nearby stronghold,
          on the same path or on another path
        - 2-opt: reverse part of a path so a stronghold sits next to a nearby one
        - swap two nearby strongholds on different paths
    Stops when no move improves or the deadline passes. on_improve(routes) is called after every improvement.
    '''
    routes = [list(route) for route in routes]
    nodes = [node for route in routes for node in route]
    if not nodes:
        return routes

    rng = random.Random(0)
    num_paths = len(routes)

    def route_time(path_id: int, route: list[int]) -> float:
        return path_seconds(len(route), _route_cost(route, dist, closed[path_id], spawn_reset, previous_bed, REFINE_BEAM_WIDTH), speeds[path_id])

    def objective(times: list[float]) -> float:
        return sum(times) + SPAN_COST_COEFFICIENT * max(times)

    times = [route_time(p, r) for p, r in enumerate(routes)]
    best = objective(times)

    neighbours = {u: sorted((v for v in nodes if v != u), key=lambda v: dist[u][v])[:REFINE_NEIGHBOURS] for u in nodes}

    def locate() -> dict[int, tuple[int, int]]:
        return {node: (p, i) for p, route in enumerate(routes) for i, node in enumerate(route)}

    def try_change(changes: dict[int, list[int]]) -> bool:
        '''Apply {path_id: new_route} if it improves the objective.'''
        nonlocal best
        new_times = list(times)
        for p, route in changes.items():
            new_times[p] = route_time(p, route)

        value = objective(new_times)
        if value < best - 1e-9 * max(1.0, best):
            for p, route in changes.items():
                routes[p] = route
                times[p] = new_times[p]
            best = value
            if on_improve:
                on_improve(routes)
            return True
        return False

    def relocate(u: int, where: dict) -> bool:
        p, i = where[u]
        route = routes[p]

        for length in range(1, REFINE_MAX_SEGMENT + 1):
            if i + length > len(route):
                break
            segment = route[i:i + length]
            rest = route[:i] + route[i + length:]

            # Insert positions next to nearby strongholds, plus the start of any empty path
            candidates = set()
            for w in neighbours[segment[0]] + neighbours[segment[-1]]:
                if w in segment:
                    continue
                q, j = where[w]
                if q == p:
                    j = rest.index(w)
                candidates.add((q, j))
                candidates.add((q, j + 1))
            for q in range(num_paths):
                if not routes[q] and q != p:
                    candidates.add((q, 0))

            for q, j in candidates:
                for piece in (segment, segment[::-1]):
                    if q == p:
                        changes = {p: rest[:j] + piece + rest[j:]}
                    else:
                        target = routes[q]
                        changes = {p: rest, q: target[:j] + piece + target[j:]}
                    if try_change(changes):
                        return True
        return False

    def two_opt(u: int, where: dict) -> bool:
        p, i = where[u]
        route = routes[p]

        for w in neighbours[u]:
            q, j = where[w]
            if q != p:
                continue
            if j > i + 1:
                new_route = route[:i + 1] + route[i + 1:j + 1][::-1] + route[j + 1:]
            elif j < i - 1:
                new_route = route[:j] + route[j:i][::-1] + route[i:]
            else:
                continue
            if try_change({p: new_route}):
                return True
        return False

    def swap(u: int, where: dict) -> bool:
        p, i = where[u]

        for w in neighbours[u]:
            q, j = where[w]
            if q == p:
                continue
            route_p = list(routes[p])
            route_q = list(routes[q])
            route_p[i], route_q[j] = w, u
            if try_change({p: route_p, q: route_q}):
                return True
        return False

    improved = True
    while improved and time.monotonic() < deadline:
        improved = False
        order = list(nodes)
        rng.shuffle(order)

        for u in order:
            if time.monotonic() >= deadline:
                break
            for move in (relocate, two_opt, swap):
                if move(u, locate()):
                    improved = True
                    break

    return routes