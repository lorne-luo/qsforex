import logging
import queue
import sys
import time

import settings
from event.handler import QueueBase, HeartBeatEvent, BaseHandler

logger = logging.getLogger(__name__)


class Runner(QueueBase):
    handlers = []
    running = True

    def run(self):
        raise NotImplementedError

    def register(self, *args):
        for handler in args:
            if isinstance(handler, BaseHandler):
                handler.set_queue(self.queue)
                self.handlers.append(handler)

    def process_event(self, event):
        for handler in self.handlers:
            if '*' in handler.subscription:
                handler.process(event)
                continue
            if event.type in handler.subscription:
                handler.process(event)

    def print(self):
        print(self.handlers)

    def stop(self):
        del self.queue
        self.running = False
        sys.exit(0)


class HeartbeatRunner(Runner):
    def __init__(self, queue, heartbeat=5, *args, **kwargs):
        super(HeartbeatRunner, self).__init__(queue)
        self.heartbeat = heartbeat or 5  # seconds
        self.register(*args)

    def run(self):
        print('%s statup.' % self.__class__.__name__)
        print('Registered handler: %s' % ', '.join([x.__class__.__name__ for x in self.handlers]))
        print('\n')

        while True:
            try:
                event = self.queue.get(False)
            except queue.Empty:
                time.sleep(self.heartbeat)
                self.put(HeartBeatEvent())
            else:
                if event:
                    if settings.DEBUG:
                        print("Received new %s event: %s", (event.type, event.__dict__))
                    else:
                        logger.debug("Received new %s event: %s", (event.type, event.__dict__))

                    self.process_event(event)


class StreamRunnerBase(Runner):
    broker = ''
    account = None

    def __init__(self, queue, pairs, *args, **kwargs):
        super(StreamRunnerBase, self).__init__(queue)
        if args:
            self.register(*args)
        self.pairs = pairs
        self.prices = self._set_up_prices_dict()

    def _set_up_prices_dict(self):
        prices_dict = dict(
            (k, v) for k, v in [
                (p, {"bid": None, "ask": None, "time": None, "spread": None}) for p in self.pairs
            ]
        )

        return prices_dict


if __name__ == '__main__':
    # python -m event.runner
    from event.handler import *
    import queue

    q = queue.Queue(maxsize=2000)
    d = DebugHandler(q)
    t = TimeFrameTicker(q)
    r = HeartbeatRunner(q, 5, d, t)
    r.run()
