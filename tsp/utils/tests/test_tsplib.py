from tsp.utils.tsplib import find_route


def test_find_route_returns_result():
    locations = [
        [40.74924, 169.19068],
        [39.28762, 75.30099],
        [-45.81594, 146.19084],
        [-35.28499, 22.68073],
        [16.53802, -148.45893],
    ]

    assert find_route(locations) is not None
