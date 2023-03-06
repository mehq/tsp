import math
from typing import Any, Dict, List, Optional

from ortools.constraint_solver import pywrapcp, routing_enums_pb2


def calculate_distance(from_location: List[float], to_location: List[float]) -> float:
    return math.hypot(from_location[0] - to_location[0], from_location[1] - to_location[1])


def create_distance_matrix(geocoded_locations: List[List[float]]) -> List[List[float]]:
    location_count = len(geocoded_locations)
    distance_matrix = [[0.0 for _ in range(location_count)] for _ in range(location_count)]

    for i, row in enumerate(distance_matrix):
        for j, _ in enumerate(row):
            if i != j:
                distance_matrix[i][j] = calculate_distance(geocoded_locations[i], geocoded_locations[j])

    return distance_matrix


def create_data_model(distance_matrix: List[List[float]]) -> Dict[str, Any]:
    return {
        "distance_matrix": distance_matrix,
        "num_vehicles": 1,
        "depot": 0,
    }


def build_solution_model(
    data: Dict[str, Any], manager: pywrapcp.RoutingIndexManager, routing: pywrapcp.RoutingModel, solution: Any
) -> Dict[str, Any]:
    """
    Builds and returns the solution data model.
    """
    solution_data = {
        "objective": solution.ObjectiveValue(),
        "max_route_distance": 0,
        "route_plans": [],
    }

    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        route_plan: Dict[str, Any] = {
            "vehicle_id": vehicle_id,
            "routes": [],
            "route_distance": 0,
        }

        while not routing.IsEnd(index):
            route_plan["routes"].append(
                {
                    "route_index": manager.IndexToNode(index),
                }
            )
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_plan["route_distance"] += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)

        route_plan["routes"].append(
            {
                "route_index": manager.IndexToNode(index),
            }
        )

        solution_data["route_plans"].append(route_plan)

        solution_data["max_route_distance"] = max(route_plan["route_distance"], solution_data["max_route_distance"])

    return solution_data


def build_solution_model_with_time_windows(
    data: Dict[str, Any], manager: pywrapcp.RoutingIndexManager, routing: pywrapcp.RoutingModel, solution: Any
) -> Dict[str, Any]:
    """
    Builds and returns the solution data model.
    """
    solution_data = {
        "objective": solution.ObjectiveValue(),  # in minutes
        "total_time": 0,  # Total time of all routes (in minutes).
        "route_plans": [],
    }
    time_dimension = routing.GetDimensionOrDie("Time")

    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        route_plan: Dict[str, Any] = {
            "vehicle_id": vehicle_id,
            "routes": [],
        }

        while not routing.IsEnd(index):
            time_var = time_dimension.CumulVar(index)

            route_plan["routes"].append(
                {
                    "route_index": manager.IndexToNode(index),
                    "min_time": solution.Min(time_var),
                    "max_time": solution.Max(time_var),
                }
            )

            index = solution.Value(routing.NextVar(index))

        time_var = time_dimension.CumulVar(index)

        route_plan["routes"].append(
            {
                "route_index": manager.IndexToNode(index),
                "min_time": solution.Min(time_var),
                "max_time": solution.Max(time_var),
            }
        )

        route_plan["time"] = solution.Min(time_var)  # in minutes

        solution_data["route_plans"].append(route_plan)

        solution_data["total_time"] += solution.Min(time_var)

    return solution_data


def get_matrix_range(distance_matrix):
    min_distance, max_distance = 0, 0

    for i, row in enumerate(distance_matrix):
        _max = max(row)
        _min = min(row)

        if not i:
            min_distance = _min
            max_distance = _max
            continue

        if _min < min_distance:
            min_distance = _min

        if _max > max_distance:
            max_distance = _max

    return min_distance, max_distance


def scale(value, old_min, old_max, new_min, new_max):
    result = ((new_max - new_min) * ((value - old_min) / (old_max - old_min))) + new_min
    return int(result)


def scale_matrix(matrix, old_min, old_max, new_min, new_max):
    for i, row in enumerate(matrix):
        for j, _ in enumerate(row):
            matrix[i][j] = scale(matrix[i][j], old_min, old_max, new_min, new_max)

    return matrix


def find_route(
    geocoded_locations: List[List[float]],
    time_windows: Optional[List[List[int]]] = None,
    depot: int = 0,
    num_vehicles: int = 1,
) -> Optional[Dict[str, Any]]:
    """
    Returns the solution model or `None` if none found.

    NOTE: Uses `time_matrix` and `distance_matrix` interchangeably for the sake of simplicity.
    """
    # pylint:disable=too-many-locals
    distance_matrix = create_distance_matrix(geocoded_locations)

    if time_windows:
        min_distance, max_distance = get_matrix_range(distance_matrix)
        min_time, max_time = get_matrix_range(time_windows)
        distance_matrix = scale_matrix(distance_matrix, min_distance, max_distance, min_time, max_time)

    matrix_model_name = "time_matrix" if time_windows else "distance_matrix"

    data: Dict[str, Any] = {
        matrix_model_name: distance_matrix,
        "time_windows": time_windows,
        "num_vehicles": num_vehicles,
        "depot": depot,
    }

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(len(data[matrix_model_name]), data["num_vehicles"], data["depot"])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    def transit_callback(from_index, to_index):
        """Returns the travel time between the two nodes."""
        # Convert from routing variable Index to time matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data[matrix_model_name][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(transit_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Time Windows constraint.
    dimension_name = "Time" if time_windows else "Distance"

    routing.AddDimension(
        transit_callback_index,
        30 if time_windows else 0,  # allow waiting time.
        30 if time_windows else 3000,  # maximum time per vehicle or max travel distance.
        not time_windows,  # Don't force start cumul to zero or start.
        dimension_name,
    )

    time_dimension = routing.GetDimensionOrDie(dimension_name)

    if not time_windows:
        time_dimension.SetGlobalSpanCostCoefficient(100)

    if time_windows:
        # Add time window constraints for each location except depot.
        for location_idx, time_window in enumerate(data["time_windows"]):
            if location_idx == data["depot"]:
                continue

            index = manager.NodeToIndex(location_idx)
            time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])

        # Add time window constraints for each vehicle start node.
        depot_idx = data["depot"]

        for vehicle_id in range(data["num_vehicles"]):
            index = routing.Start(vehicle_id)
            time_dimension.CumulVar(index).SetRange(
                data["time_windows"][depot_idx][0], data["time_windows"][depot_idx][1]
            )

        # Instantiate route start and end times to produce feasible times.
        for i in range(data["num_vehicles"]):
            routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(routing.Start(i)))
            routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(routing.End(i)))

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC  # pylint: disable=no-member
    )

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if solution:
        if time_windows:
            return build_solution_model_with_time_windows(data, manager, routing, solution)

        return build_solution_model(data, manager, routing, solution)

    return None
