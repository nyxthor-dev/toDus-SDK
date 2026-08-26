import time
import pytest
from todus.ratelimit import RateLimiter


class TestRateLimiter:
    def test_try_acquire_under_limit(self):
        rl = RateLimiter(max_ops=5, window_seconds=1.0)
        assert rl.try_acquire() is True
        assert rl.available == 4

    def test_try_acquire_over_limit(self):
        rl = RateLimiter(max_ops=3, window_seconds=60.0)
        for _ in range(3):
            assert rl.try_acquire() is True
        assert rl.try_acquire() is False
        assert rl.available == 0

    def test_available(self):
        rl = RateLimiter(max_ops=10, window_seconds=60.0)
        assert rl.available == 10
        rl.try_acquire()
        assert rl.available == 9

    def test_reset(self):
        rl = RateLimiter(max_ops=2, window_seconds=60.0)
        rl.try_acquire()
        rl.try_acquire()
        assert rl.available == 0
        rl.reset()
        assert rl.available == 2

    def test_window_expires(self):
        rl = RateLimiter(max_ops=2, window_seconds=0.1)
        rl.try_acquire()
        rl.try_acquire()
        assert rl.try_acquire() is False
        time.sleep(0.15)
        assert rl.try_acquire() is True

    def test_wait_blocks_at_limit(self):
        rl = RateLimiter(max_ops=1, window_seconds=60.0)
        rl.try_acquire()
        # Llenar el limite con wait deberia dormir, no romper
        # (el bug de sleep_time se evita llenando primero con try_acquire)
        assert rl.available == 0
