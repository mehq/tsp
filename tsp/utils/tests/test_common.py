import pytest

from tsp.utils.common import retry_with_backoff


class TestException(Exception):
    __test__ = False


def test_retry_with_backoff_functions_properly():
    def always_fail():
        raise TestException("sorry :(")

    tries = 0

    def succeed_after_three_tries():
        nonlocal tries
        tries += 1

        if tries < 3:
            raise TestException("keep trying :)")

    with pytest.raises(TestException):
        retry_with_backoff(always_fail, retries=3, backoff_in_seconds=0.1)

    retry_with_backoff(succeed_after_three_tries, retries=3, backoff_in_seconds=0.1)
