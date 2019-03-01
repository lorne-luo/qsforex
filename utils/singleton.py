class SingletonDecorator:
    def __init__(self, klass):
        self.klass = klass
        self.instance = {}

    def __call__(self, *args, **kwargs):
        kw = ['%s=%s' % (k, kwargs[k]) for k in sorted(kwargs.keys())]
        ag = [str(i) for i in args]
        key = ','.join(ag + kw)
        key = '%s.%s:%s' % (self.klass.__module__, self.klass.__name__, key)

        if self.instance.get(key, None) == None:
            self.instance[key] = self.klass(*args, **kwargs)
        return self.instance[key]
