
import time
class Retry:
    def __init__(self, attempts=3, backoff=0.2):
        self.attempts = attempts
        self.backoff = backoff
    def run(self, fn, key=None):
        last = None
        for i in range(self.attempts):
            try:
                return fn()
            except Exception as e:
                last = e
                time.sleep(self.backoff * (i+1))
        raise last
