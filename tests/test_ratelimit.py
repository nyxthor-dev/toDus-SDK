"""Tests para RateLimiter."""
import time
import threading
import pytest
from todus.ratelimit import RateLimiter


class TestRateLimiter:
    def test_basic_limit(self):
        limiter = RateLimiter(max_ops=3, window_seconds=1.0)
        for _ in range(3):
            assert limiter.try_acquire() is True
        # 4th should fail
        assert limiter.try_acquire() is False

    def test_available(self):
        limiter = RateLimiter(max_ops=5, window_seconds=60.0)
        assert limiter.available == 5
        limiter.try_acquire()
        assert limiter.available == 4

    def test_reset(self):
        limiter = RateLimiter(max_ops=2, window_seconds=60.0)
        limiter.try_acquire()
        limiter.try_acquire()
        assert limiter.available == 0
        limiter.reset()
        assert limiter.available == 2

    def test_window_expires(self):
        limiter = RateLimiter(max_ops=1, window_seconds=0.2)
        assert limiter.try_acquire() is True
        assert limiter.try_acquire() is False
        time.sleep(0.3)
        assert limiter.try_acquire() is True

    def test_wait_unblocks(self):
        limiter = RateLimiter(max_ops=2, window_seconds=0.2)
        limiter.try_acquire()
        limiter.try_acquire()
        start = time.time()
        limiter.wait()  # Should block briefly then allow
        elapsed = time.time() - start
        assert elapsed < 0.5  # Should not block too long

    def test_thread_safety(self):
        """Multiple threads using try_acquire shouldn't crash."""
        limiter = RateLimiter(max_ops=100, window_seconds=1.0)
        errors = []

        def worker():
            try:
                for _ in range(50):
                    limiter.try_acquire()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0
