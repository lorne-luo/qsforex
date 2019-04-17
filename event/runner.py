import logging
import sys
import time
import traceback

from event.handler import QueueBase

logger = logging.getLogger(__name__)


class Runner(QueueBase):
    handlers = []
    running = True
    initialized = False

    def run(self):
        raise NotImplementedError

    def register(self, *args):
        for handler in args:
            if isinstance(handler, BaseHandler):
                handler.set_queue(self.queue)
                self.handlers.append(handler)

    def handle_event(self, event):
        """loop handlers to process event"""
        re_put = False
        for handler in self.handlers:
            if '*' in handler.subscription:
                result = self.process_event(handler, event)
                re_put = result or re_put
                continue
            elif event.type in handler.subscription:
                result = self.process_event(handler, event)
                re_put = result or re_put
        if re_put:
            if event.tried > 10:
                logger.error('[EVENT_RETRY] tried to many times abort, event=%s' % event)
            else:
                event.tried += 1
                self.put(event)

    def process_event(self, handler, event):
        """process event by single handler"""
        try:
            return handler.process(event)
        except Exception as ex:
            logger.error('[EVENT_PROCESS] %s, event=%s' % (ex, event.__dict__))
            # print trace stack
            extracted_list = traceback.extract_tb(ex.__traceback__)
            for item in traceback.StackSummary.from_list(extracted_list).format()[:8]:
                logger.error(item.strip())
            self.handle_error(ex)

    def handle_error(self, ex):
        pass

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
        logger.info('%s statup.' % self.__class__.__name__)
        logger.info('Registered handler: %s' % ', '.join([x.__class__.__name__ for x in self.handlers]))
        logger.info('\n')

        while True:
            try:
                event = self.get(False)
            except queue.Empty:
                time.sleep(self.heartbeat)
                self.put(HeartBeatEvent())
            else:
                if event:
                    if settings.DEBUG:
                        logger.info("New %sEvent: %s", (event.type, event.__dict__))
                    else:
                        logger.debug("New %sEvent: %s", (event.type, event.__dict__))

                    self.handle_event(event)


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
