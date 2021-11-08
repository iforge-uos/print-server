import timeit


class Timer:
    def __init__(self, name="Source Unknown"):
        self.t0 = timeit.default_timer()
        self.name = name

    def __enter__(self):
        self.reset_timer()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"Timing for: '{self.name}' complete, {self.get_timer():.3f}s elapsed")

    def reset_timer(self):
        self.t0 = timeit.default_timer()

    def get_timer(self):
        return timeit.default_timer() - self.t0
