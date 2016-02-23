import node


class IDLArgument(node.IDLNode):
    def __init__(self, parent):
        super(IDLArgument, self).__init__('IDLArgument', '', parent)
        self._verbose = True
        self._dir = 'in'
        self._type = None

    def parse_blocks(self, blocks):
        directions = ['in', 'out', 'inout']
        self._dir = 'in'
        if blocks[0] in directions:
            self._dir = blocks[0]
            blocks.pop(0)
            pass
        argument_name, argument_type = self._name_and_type(blocks)
        self._name = argument_name
        self._type = argument_type

    def to_simple_dic(self):
        dic = '%s %s %s' % (self.direction, self.type, self.name)
        return dic

    def to_dic(self):
        dic = { 'name' : self.name,
                'classname' : self.classname,
                'type' : self.type,
                'direction' : self.direction }
        return dic

    @property
    def direction(self):
        return self._dir

    @property
    def type(self):
        return self._type

    def post_process(self):
        self._type = self.refine_typename(self.type)

        
class IDLMethod(node.IDLNode):
    def __init__(self, parent):
        super(IDLMethod, self).__init__('IDLValue', '', parent)
        self._verbose = True
        self._returns = None
        self._arguments = []

    def parse_blocks(self, blocks):

        if blocks[0] == 'oneway':
            self._oneway = True
            blocks.pop(0)
        else:
            self._oneway = False

        self._returns = blocks[0]
        self._name = blocks[1]
        self._arguments = []

        if not blocks[2] == '(':
            print ' -- Invalid Interface Token (%s)' % interface_name
            print blocks
            
        index = 3
        argument_blocks = []
        while True:
            if index == len(blocks):
                break
            token = blocks[index]
            if token == ',' or token == ')':
                if len(argument_blocks) == 0:
                    break

                a = IDLArgument(self)
                self._arguments.append(a)
                a.parse_blocks(argument_blocks)

                argument_blocks = []
            else:
                argument_blocks.append(token)
            index = index + 1

    def to_simple_dic(self):
        return {self.name : {
                'returns' : self.returns,
                'params' : [a.to_simple_dic() for a in self.arguments]}}

    def to_dic(self):
        dic = { 'name' : self.name,
                'classname' : self.classname,
                'returns' : self._returns,
                'arguments' : [a.to_dic() for a in self.arguments]}
        return dic

    @property
    def returns(self):
        return self._returns

    @property
    def arguments(self):
        return self._arguments

    def forEachArgument(self, func):
        for a in self.arguments:
            func(a)

    def post_process(self):
        self._returns = self.refine_typename(self.returns)
        self.forEachArgument(lambda a : a.post_process())

class IDLInterface(node.IDLNode):
    
    def __init__(self, name, parent):
        super(IDLInterface, self).__init__('IDLInterface', name, parent)
        self._verbose = True
        self._methods = []

    def to_simple_dic(self, quiet=False):
        if quiet:
            return 'interface %s' % self.name
        dic = { 'interface ' + self.name : [m.to_simple_dic() for m in self.methods] }
        return dic

    def to_dic(self):
        dic = { 'name' : self.name,
                'classname' : self.classname,
                'methods' : [m.to_dic() for m in self.methods] }
        return dic
    
    def parse_tokens(self, token_buf):
        kakko = token_buf.pop()
        if not kakko == '{':
            if self._verbose: sys.stdout.write('# Error. No kakko "{".\n')
            raise InvalidIDLSyntaxError()
        
        block_tokens = []        
        while True:

            token = token_buf.pop()
            if token == None:
                if self._verbose: sys.stdout.write('# Error. No kokka "}".\n')
                raise InvalidIDLSyntaxError()
            
            elif token == '}':
                token = token_buf.pop()
                if not token == ';':
                    if self._verbose: sys.stdout.write('# Error. No semi-colon after "}".\n')
                    raise InvalidIDLSyntaxError()
                break
            
            if token == ';':
                self._parse_block(block_tokens)
                block_tokens = []
                continue
            block_tokens.append(token)
        self._post_process()

    def _post_process(self):
        self.forEachMethod(lambda m : m.post_process())

    def _parse_block(self, blocks):
        v = IDLMethod(self)
        v.parse_blocks(blocks)
        self._methods.append(v)

    @property
    def methods(self):
        return self._methods

    def forEachMethod(self, func):
        for m in self.methods:
            func(m)

        