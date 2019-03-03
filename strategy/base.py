class StrategyBase(object):
    name = None
    version = None
    queue = None

    weekdays = list(range(6))

    pairs = {
        'EURUSD': {'timeframes': [], 'longest_window': 30, 'hours': list(range(24))}  # GMT hour
    }

    data_reader = None

    def __str__(self):
        return '%s v%s' % (self.name, self.version)

    def __init__(self, reader, queue, *args, **kwargs):
        self.data_reader = reader
        self.queue = queue

    def calculate_signals(self):
        raise NotImplementedError

    def put_event(self, event):
        self.queue.put(event)
