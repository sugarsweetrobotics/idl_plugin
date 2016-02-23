import os, sys, traceback

import node

sep = '::'

class IDLValue(node.IDLNode):
    def __init__(self, parent):
        super(IDLValue, self).__init__('IDLValue', '', parent)
        self._verbose = True
        self._type = None
    
    @property
    def full_path(self):
        return self.parent.full_path + '::' + self.name

    def parse_blocks(self, blocks):
        name, type = self._name_and_type(blocks)
        self._name = name
        self._type = type

    def to_simple_dic(self):
        dic = {self.name : self.type }
        return dic

    def to_dic(self):
        dic = { 'name' : self.name,
                'classname' : self.classname,
                'type' : self.type }
        return dic

    @property
    def type(self):
        return self._type

    def post_process(self):
        self._type = self.refine_typename(self.type)
                

class IDLStruct(node.IDLNode):
    
    def __init__(self, name, parent):
        super(IDLStruct, self).__init__('IDLStruct', name.strip(), parent)
        self._verbose = True
        self._members = []

    @property
    def full_path(self):
        return self.parent.full_path + sep + self.name

    def to_simple_dic(self, quiet=False):
        if quiet:
            return 'struct %s' % self.name 
        dic = { 'struct %s' % self.name : [v.to_simple_dic() for v in self.members] }
        return dic
                    

    def to_dic(self):
        dic = { 'name' : self.name,
                'classname' : self.classname,
                'members' : [v.to_dic() for v in self.members] }
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
            
    def _parse_block(self, blocks):
        v = IDLValue(self)
        v.parse_blocks(blocks)
        self._members.append(v)
    
    def _post_process(self):
        self.forEachMember(lambda m : m.post_process())

    @property
    def members(self):
        return self._members
    
    def forEachMember(self, func):
        for m in self._members:
            func(m)
