import node

sep = '::'

class IDLTypedef(node.IDLNode):
    
    def __init__(self, parent):
        super(IDLTypedef, self).__init__('IDLTypedef', '', parent)
        self._verbose = True
        self._type = None

    @property
    def full_path(self):
        return self.parent.full_path + sep + self.name

    def to_simple_dic(self, quiet):
        if quiet:
            return 'typedef ' + self._name
        dic = 'typedef ' + self._type + ' ' + self._name
        return dic

    def to_dic(self):
        dic = { 'name' : self.name,
                'classname' : self.classname,
                'type' : self.type }
        return dic

    @property
    def type(self):
        return self._type
    
    def parse_blocks(self, blocks):
        type_name_ = ''
        rindex = 1
        name = blocks[-rindex]
        while True:
            if name.find('[') < 0:
                break
            
            if name.find('[') > 0:
                type_name_ = name[name.find('['):]
                name = name[:name.find('[')]
                #rindex = rindex + 1
                break

            type_name_ = name + type_name_
            rindex = rindex + 1
            name = blocks[-rindex]

        type_name = ''
        for t in blocks[:-rindex]:
            type_name = type_name + ' ' + t
        type_name = type_name + ' ' + type_name_
        type_name = type_name.strip()

        self._type = type_name
        self._name = name

        self._post_process()

    def _post_process(self):
        self._type = self.refine_typename(self.type)
