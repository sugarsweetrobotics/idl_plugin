import os, sys, traceback

import node
import type as idl_type
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
        name, typ = self._name_and_type(blocks)
        self._name = name
        self._type = idl_type.IDLType(typ, self)

    def to_simple_dic(self, recursive=False):
        if recursive:
            if self.type.is_primitive:
                return str(self.type) + ' ' + self.name
            dic = {str(self.type) +' ' + self.name : 
                   self.type.obj.to_simple_dic(recursive=recursive, member_only=True)}
            return dic
        dic = {self.name : str(self.type) }
        return dic

    def to_dic(self):
        dic = { 'name' : self.name,
                'classname' : self.classname,
                'type' : str(self.type) }
        return dic

    @property
    def type(self):
        return self._type

    def post_process(self):
        #self._type = self.refine_typename(self.type)
        pass
                

class IDLStruct(node.IDLNode):
    
    def __init__(self, name, parent):
        super(IDLStruct, self).__init__('IDLStruct', name.strip(), parent)
        self._verbose = True
        self._members = []

    @property
    def full_path(self):
        return (self.parent.full_path + sep + self.name).strip()

    def to_simple_dic(self, quiet=False, full_path=False, recursive=False, member_only=False):
        name = self.full_path if full_path else self.name
        if quiet:
            return 'struct %s' % name 
        
        dic = { 'struct %s' % name : [v.to_simple_dic(recursive=recursive) for v in self.members] }

        if member_only:
            return dic.values()[0]
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
