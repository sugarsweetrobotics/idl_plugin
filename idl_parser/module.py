import os, sys, traceback

import node
import struct, typedef, interface, enum
global_namespace = '__global__'
sep = '::'

class IDLModule(node.IDLNode):

    def __init__(self, name=None, parent = None):
        super(IDLModule, self).__init__('IDLModule', name, parent)
        self._verbose = False
        if name is None:
            self._name = global_namespace

        self._interfaces = []
        self._typedefs = []
        self._structs = []
        self._enums = []
        self._modules = []

    @property
    def is_global(self):
        return self.name == global_namespace
        
    @property
    def full_path(self):
        if self.parent is None:
            return '' # self.name
        else:
            if len(self.parent.full_path) == 0:
                return self.name
            return self.parent.full_path + sep + self.name

    def to_simple_dic(self, quiet=False):
        dic = {'module %s' % self.name : [s.to_simple_dic(quiet) for s in self.structs] +
               [i.to_simple_dic(quiet) for i in self.interfaces] +
               [m.to_simple_dic(quiet) for m in self.modules] + 
               [e.to_simple_dic(quiet) for e in self.enums] + 
               [t.to_simple_dic(quiet) for t in self.typedefs]}
        return dic

    def to_dic(self):
        dic = { 'name' : self.name,
                'classname' : self.classname,
                'interfaces' : [i.to_dic() for i in self.interfaces],
                'typedefs' : [t.to_dic() for t in self.typedefs],
                'structs' : [s.to_dic() for s in self.structs],
                'enums' : [e.to_dic() for e in self.enums],
                'modules' : [m.to_dic() for m in self.modules] }
        return dic
    

    def parse_tokens(self, token_buf):
        if not self.name == global_namespace:
            kakko = token_buf.pop()
            if not kakko == '{':
                if self._verbose: sys.stdout.write('# Error. No kakko "{".\n')
                raise InvalidIDLSyntaxError()

        while True:
            token = token_buf.pop()
            if token == None:
                if self.name == global_namespace:
                    break
                if self._verbose: sys.stdout.write('# Error. No kokka "}".\n')
                raise InvalidIDLSyntaxError()
            elif token == 'module':
                name_ = token_buf.pop()
                m = self.module_by_name(name_)
                if m == None:
                    m = IDLModule(name_, self)
                    self._modules.append(m)
                m.parse_tokens(token_buf)
            elif token == 'typedef':
                blocks = []
                while True:
                    t = token_buf.pop()
                    if t == None:
                        raise InvalidIDLSyntaxError()
                    elif t == ';':
                        break
                    else:
                        blocks.append(t)
                t = typedef.IDLTypedef(self)
                self._typedefs.append(t)
                t.parse_blocks(blocks)
            elif token == 'struct':
                name_ = token_buf.pop()
                s_ = self.struct_by_name(name_)
                s = struct.IDLStruct(name_, self)
                s.parse_tokens(token_buf)
                if s_:
                    if self._verbose: sys.stdout.write('# Error. Same Struct Defined (%s)\n' % name_)
                #    raise InvalidIDLSyntaxError
                else:
                    self._structs.append(s)

            elif token == 'interface':
                name_ = token_buf.pop()
                s = interface.IDLInterface(name_, self)
                s.parse_tokens(token_buf)

                s_ = self.interface_by_name(name_)
                if s_:
                    if self._verbose: sys.stdout.write('# Error. Same Interface Defined (%s)\n' % name_)
                #    raise InvalidIDLSyntaxError
                else:
                    self._interfaces.append(s)
            
            elif token == 'enum':
                name_ = token_buf.pop()
                s = enum.IDLEnum(name_, self)
                s.parse_tokens(token_buf)
                s_ = self.enum_by_name(name_)
                if s_:
                    if self._verbose: sys.stdout.write('# Error. Same Enum Defined (%s)\n' % name_)
                #    raise InvalidIDLSyntaxError
                else:
                    self._enums.append(s)

                pass
            elif token == '}':
                break
            
        return True



    @property
    def modules(self):
        return self._modules

    def module_by_name(self, name):
        for m in self.modules:
            if m.name == name:
                return m
        return None

    def forEachModule(self, func):
        for m in self.modules:
            func(m)

    @property
    def interfaces(self):
        return self._interfaces

    def interface_by_name(self, name):
        for i in self.interfaces:
            if i.name == name:
                return i
        return None

    def forEachInterface(self, func):
        for m in self.interfaces:
            func(m)

    @property
    def structs(self):
        return self._structs

    def struct_by_name(self, name):
        for s in self.structs:
            if s.name == name:
                return s
        return None

    def forEachStruct(self, func):
        for m in self.structs:
            func(m)

    @property
    def enums(self):
        return self._enums

    def enum_by_name(self, name):
        for e in self.enums:
            if e.name == name:
                return e
        return None

    def forEachEnum(self, func):
        for m in self.enums:
            func(m)

    @property
    def typedefs(self):
        return self._typedefs

    def typedef_by_name(self, name):
        for t in self.typedefs:
            if t.name == name:
                return t
        return None

    def forEachTypedef(self, func):
        for m in self.typedefs:
            func(m)

    def find_types(self, full_typename):
        typenode = []

        def parse_node(s, name=str(full_typename)):
            if s.name == name.strip() or s.full_path == name.strip():
                typenode.append(s)

        def parse_module(m):
            m.forEachModule(parse_module)
            m.forEachStruct(parse_node)
            m.forEachTypedef(parse_node)
            m.forEachEnum(parse_node)
            m.forEachInterface(parse_node)

        parse_module(self)

        return typenode
