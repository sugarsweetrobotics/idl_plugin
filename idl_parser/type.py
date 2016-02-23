import os, sys, traceback

import node

sep = '::'

primitive = [
    'boolean',
    'char', 'byte', 'octet', 
    'short', 'wchar', 
    'long', 
    'float',
    'double',
    'string',
    'wstring']
           

def IDLType(name, parent):
    if name == 'void':
        return IDLVoid(name, parent)

    elif name.find('sequence') >= 0:
        return IDLSequence(name, parent)

    for n in name.split(' '):
        if n in primitive:
            return IDLPrimitive(name, parent)

    return IDLBasicType(name, parent)

class IDLTypeBase(node.IDLNode):
    def __init__(self, classname, name, parent):
        super(IDLTypeBase, self).__init__(classname, name, parent.root_node)
        self._is_sequence = False
        self._is_primitive = False

    def __str__(self):
        return self.name

    @property
    def is_sequence(self):
        return self._is_sequence

    @property
    def is_primitive(self):
        return self._is_primitive


class IDLVoid(IDLTypeBase):
    def __init__(self, name, parent):
        super(IDLVoid, self).__init__('IDLVoid', name, parent.root_node)
        self._verbose = True

class IDLSequence(IDLTypeBase):
    def __init__(self, name, parent):
        super(IDLSequence, self).__init__('IDLSequence', name, parent.root_node)
        self._verbose = True
        if name.find('sequence') < 0:
            raise InvalidIDLSyntaxError()
        typ_ = name[name.find('<')+1 : name.find('>')]
        self._type = IDLType(typ_, parent)        
        self._is_primitive = self.inner_type.is_primitive
    @property
    def inner_type(self):
        return self._type

    def __str__(self):
        return 'sequence<%s>' % str(self.inner_type)
    
    @property
    def obj(self):
        global_module = self.root_node
        typs = global_module.find_types(self.inner_type)
        print self.inner_type
        if len(typs) == 0:
            print 'None'
            return None
        else:
            print typs[0]
            return typs[0]

        
class IDLPrimitive(IDLTypeBase):
    def __init__(self, name, parent):
        super(IDLPrimitive, self).__init__('IDLPrimitive', name, parent.root_node)
        self._verbose = True
        self._is_primitive = True

class IDLBasicType(IDLTypeBase):
    def __init__(self, name, parent):
        super(IDLBasicType, self).__init__('IDLBasicType', name, parent.root_node)
        self._verbose = True
        self._name = self.refine_typename(self.name)
        
    @property
    def obj(self):
        global_module = self.root_node
        typs = global_module.find_types(self.name)
        if len(typs) == 0:
            return None
        else:
            return typs[0]
