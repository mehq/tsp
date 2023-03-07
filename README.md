# tsp

Vehicle routing problem-solving web service.

* [Quickstart](#quickstart)
  * [With Docker](#with-docker)
  * [Without Docker](#without-docker)
* [Configuration](#configuration)
* [Design](#design)
  * [API](#api)
  * [Queue](#queue)
  * [Background Worker](#background-worker)
* [API Documentation](#api-documentation)
  * [Write API](#write-api)
  * [Read API](#read-api)
* [Request Model (Problem)](#problem-request-model)
* [Response Model (Solution)](#solution-response-model)
  * [Without Time Constraints](#without-time-constraints)
  * [With Time Constraints](#with-time-constraints)

## Quickstart

### With Docker

**Pre-requisites:**

* [Git](https://git-scm.com/downloads)
* [Docker Engine](https://docs.docker.com/engine/install/) `17.04.0+`
* [Docker Compose](https://docs.docker.com/compose/install/) `1.12.0`

Steps:
```shell
# Clone the repository.
git clone https://github.com/mehq/tsp.git  # (HTTPS)
# or
git clone git@github.com:mehq/tsp.git  # (SSH)

# Enter clone location.
cd tsp

# Create a .env file from the provided sample and update the variables to
# match your specific needs, paying special attention to the rabbitmq
# url.
cp .env.sample .env

# Start services with docker.
./example.sh docker
```

### Without Docker

**Pre-requisites:**

* [Git](https://git-scm.com/downloads)
* [Python](https://www.python.org/downloads/) `3.9+`
* [RabbitMQ](https://www.rabbitmq.com/download.html) `3+`

Steps:
```shell
# Clone the repository.
git clone https://github.com/mehq/tsp.git  # (HTTPS)
# or
git clone git@github.com:mehq/tsp.git  # (SSH)

# Enter clone location.
cd tsp

# Create a .env file from the provided sample and update the variables to
# match your specific needs, paying special attention to the rabbitmq
# url.
cp .env.sample .env

# Start services without docker.
./example.sh
```

**NOTE:** Make sure rabbitmq server is running and correct url is configured in `.env` file before executing `example.sh`.

**TIP:** Utilize a Python virtual environment to isolate the installed dependencies.

## Configuration

Refer to the [.env.sample](.env.sample) file to understand which settings can be configured using environment variables.

## Design

![design](design.png)

This API service was built with standard Django. For simplicity's sake, it has been kept stateless so no persistant database was used.

There are three primary components to the system.

1. API
2. Queue
3. Background Worker


### API

There are two possible client-server flows, which are discussed below:

**Scenario A:**

1. The **Client** sends a request with proper data to the **Write API**.
2. The **Server** generates a random id (uuid version 4) and attaches it to the user's payload.
3. The **Server** sends the payload (along with generated id) to the underlying **Problem Queue**.
4. The **Server** responds the user with the id and an url where the solution can be read from the **Solution Queue**.

**Scenario B:**

1. The **Client** sends a request to the **Read API** url (obtained from *Scenario A*).
2. The **Server** reads the solution from the **Solution Queue** with the id from user's request.
3. The **Server** responds the user with the solution.

### Queue

The system utilizes two durable queues from *rabbitmq* to maintain communication between the **API** server and the **Background Worker**. The inbound queue is used for storing problem statements and the outbound queue is used for storing the solutions.

### Background Worker

The background worker runs independently and does not rely on the API server. It reads problems from the inbound queue (**Problem Queue**), uses the underlying optimization library to solve the problem and write the solution to the outbound queue (**Solution Queue**).

## API Documentation

### Write API

**URL:** `{base_url}/api/solve-tsp/`

**Method**: `POST`

**Body (JSON):**

See [Problem Request Model](#problem-request-model).

**Response (JSON):**

| Property            | Description                               | Type        |
|---------------------|-------------------------------------------|-------------|
| `id`                | Problem identifier.                       | *UUID (v4)* |
| `solution_location` | Full url where the solution can be found. | *str*       |


### Read API

**URL:** `{base_url}/api/solve-tsp/{problem_id}/`

**Method**: `GET`

**Response (JSON):**

See [Solution Response Model](#solution-response-model).

## Problem Request Model

The request model is a JSON object with following properties:

| Property       | Description                                    | Required | Type                | Default |
|----------------|------------------------------------------------|----------|---------------------|---------|
| `locations`    | List of geocoded locations (lat, long).        | *yes*    | *List[List[float]]* | `None`  |
| `time_windows` | List of time constraints (min time, max time). | *no*     | *List[List[int]]*   | `None`  |
| `depot`        | Starting location index.                       | *no*     | *int*               | `0`     |
| `num_vehicles` | Number of vehicles.                            | *no*     | *int*               | `1`     |

Example:
```json
{
  "locations": [
    [40.74924, 169.19068],
    [39.28762, 75.30099],
    [-45.81594, 146.19084],
    [-35.28499, 22.68073],
    [16.53802, -148.45893]
  ],
  "time_windows": [
    [0, 5],
    [5, 10],
    [7, 8],
    [10, 15],
    [11, 15]
  ],
  "depot": 0,
  "num_vehicles": 2
}

```

## Solution Response Model

The response model is a JSON object with following properties:

### Without Time Constraints

| Property   | Description          | Type        |
|------------|----------------------|-------------|
| `id`       | Problem identifier.  | *UUID (v4)* |
| `solution` | **Solution** object. | *dict*      |

**Solution** object have the following properties:

| Property             | Description                            | Type         |
|----------------------|----------------------------------------|--------------|
| `objective`          | Objective distance.                    | *int*        |
| `max_route_distance` | Distance of longest route (euclidean). | *int*        |
| `route_plans`        | List of **Route Plan** object.         | *List[dict]* |

**Route Plan** object have the following properties:

| Property         | Description                        | Type         |
|------------------|------------------------------------|--------------|
| `vehicle_id`     | Vehicle identifier.                | *int*        |
| `route_distance` | Distance of the route (euclidean). | *int*        |
| `routes`         | List of **Route** object.          | *List[dict]* |

**Route** object have the following properties:

| Property      | Description                                                                     | Type  |
|---------------|---------------------------------------------------------------------------------|-------|
| `route_index` | Route index in [Problem Request Model](#problem-request-model)->locations list. | *int* |

Example:

```json
{
  "id": "05744a34-785f-422b-8024-9c951db38b62",
  "solution": {
    "objective": 71407,
    "max_route_distance": 707,
    "route_plans": [
      {
        "vehicle_id": 0,
        "routes": [
          { "route_index": 2 },
          { "route_index": 0 },
          { "route_index": 1 },
          { "route_index": 4 },
          { "route_index": 3 },
          { "route_index": 2 }
        ],
        "route_distance": 707
      }
    ]
  }
}
```

### With Time Constraints

| Property   | Description          | Type        |
|------------|----------------------|-------------|
| `id`       | Problem identifier.  | *UUID (v4)* |
| `solution` | **Solution** object. | *dict*      |

**Solution** object have the following properties:

| Property      | Description                            | Type         |
|---------------|----------------------------------------|--------------|
| `objective`   | Objective time.                        | *int*        |
| `total_time`  | Total time of all routes (in minutes). | *int*        |
| `route_plans` | List of **Route Plan** object.         | *List[dict]* |

**Route Plan** object have the following properties:

| Property     | Description                               | Type         |
|--------------|-------------------------------------------|--------------|
| `vehicle_id` | Vehicle identifier.                       | *int*        |
| `time`       | Estimated time of the route (in minutes). | *int*        |
| `routes`     | List of **Route** object.                 | *List[dict]* |

**Route** object have the following properties:

| Property      | Description                                                                     | Type  |
|---------------|---------------------------------------------------------------------------------|-------|
| `route_index` | Route index in [Problem Request Model](#problem-request-model)->locations list. | *int* |
| `min_time`    | Minimum time constraint.                                                        | *int* |
| `max_time`    | Maximum time constraint.                                                        | *int* |

Example:

```json
{
  "id": "35e863a3-aa6e-4c9f-85a5-101ad76041ab",
  "solution": {
    "objective": 45,
    "total_time": 49,
    "route_plans": [
      {
        "vehicle_id": 0,
        "routes": [
          { "route_index": 0, "min_time": 0, "max_time": 0 },
          { "route_index": 1, "min_time": 5, "max_time": 5 },
          { "route_index": 4, "min_time": 15, "max_time": 15 },
          { "route_index": 0, "min_time": 30, "max_time": 30 }
        ],
        "time": 30
      },
      {
        "vehicle_id": 1,
        "routes": [
          { "route_index": 0, "min_time": 0, "max_time": 0 },
          { "route_index": 2, "min_time": 7, "max_time": 7 },
          { "route_index": 3, "min_time": 12, "max_time": 12 },
          { "route_index": 0, "min_time": 19, "max_time": 19 }
        ],
        "time": 19
      }
    ]
  }
}
```
