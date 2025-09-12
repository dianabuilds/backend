
from typing import Dict

class Dispatcher:
    def __init__(self, transport, retry, quota):
        self.transport = transport
        self.retry = retry
        self.quota = quota

    def send(self, message: Dict) -> None:
        self.quota.check(message)
        def op():
            self.transport.deliver(message)
        self.retry.run(op, key=message.get("id"))
