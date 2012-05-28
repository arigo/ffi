
class BaseType(object):
    pass

class PrimitiveType(BaseType):
    def __init__(self, name):
        self.name = name

class Function(BaseType):
    def __init__(self, args, result):
        self.args = args
        self.result = result

class Struct(BaseType):
    def __init__(self, name, fields):
        self.name = name
        self.fields = fields

class Pointer(BaseType):
    def __init__(self, to):
        self.to = to
