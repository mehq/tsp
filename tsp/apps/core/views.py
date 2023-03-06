import json
import traceback
from uuid import UUID, uuid4

from django.core.handlers.wsgi import WSGIRequest
from django.http.response import HttpResponse, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from tsp.utils.amqp import Publisher

from .utils import get_solution_delay


@require_http_methods(["GET"])
def health_check(request: WSGIRequest):
    del request
    return HttpResponse(b"ok")


@csrf_exempt
@require_http_methods(["POST"])
def solve_tsp(request: WSGIRequest):
    try:
        request_body = request.body
        json_body = json.loads(request_body)
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "message": "Invalid data provided.",
            },
            status=400,
        )

    try:
        problem_id = str(uuid4())
        publisher = Publisher()
        publisher.publish_problem(
            json.dumps(
                {
                    "id": problem_id,
                    "problem": json_body,
                }
            ).encode()
        )

        return JsonResponse(
            {
                "id": problem_id,
                "solution_location": request.build_absolute_uri(
                    reverse("get-tsp-solution", kwargs={"problem_id": problem_id})
                ),
            }
        )
    except Exception:  # pylint:disable=broad-except
        print(traceback.format_exc())
        return JsonResponse(
            {
                "message": "Something went wrong. Try again later.",
            },
            status=500,
        )


@require_http_methods(["GET"])
def get_tsp_solution(request: WSGIRequest, problem_id: UUID):
    del request

    try:
        solution = get_solution_delay(str(problem_id))

        return JsonResponse(
            {
                "id": problem_id,
                "solution": solution,
            }
        )
    except Exception:  # pylint:disable=broad-except
        print(traceback.format_exc())
        return JsonResponse(
            {
                "message": "Something went wrong. Try again later.",
            },
            status=500,
        )
