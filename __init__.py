import sys, os
import wasanbon
from wasanbon.core.plugins import PluginFunction, manifest

class Plugin(PluginFunction):

    def __init__(self):
        super(Plugin, self).__init__()
        self._model = {'__global__' : {'struct': {},
                                       'enum': {},
                                       'interface': {},
                                       'typedef' : {}}}
        pass

    def depends(self):
        return ['admin.environment']

    def _print_alternatives(self, args):
        print 'hoo'
        print 'foo'
        print 'hoge'
        print 'yah'


    def forEachIDL(self, func, idl_dirs = []):
        except_idl = ['RTM.idl', 'RTC.idl', 'OpenRTM.idl', 'DataPort.idl', 'Manager.idl', 'SDOPackage.idl']
        idls_ = []
        root_idl_dir = os.path.join(wasanbon.get_rtm_root(), 'rtm', 'idl')
        for f in os.listdir(root_idl_dir):
            if f.endswith('.idl'):
                if not f in except_idl:
                    idls_.append(os.path.join(root_idl_dir, f))
                
        wasanbon_idl_dir = os.path.join(wasanbon.home_path, 'idl')
        
        idl_dirs_ = idl_dirs + [wasanbon_idl_dir]

        for idl_dir in idl_dirs_:
            for f in os.listdir(idl_dir):
                if f.endswith('.idl'):
                    path = os.path.join(idl_dir, f)
                    idls_.append(path)

        for f in idls_:
            func(f)
                
    @manifest
    def list(self, argv):
        """ This is help text
        """
        #self.parser.add_option('-f', '--force', help='Force option (default=False)', default=False, action='store_true', dest='force_flag')
        options, argv = self.parse_args(argv[:], self._print_alternatives)
        verbose = options.verbose_flag # This is default option

        self.forEachIDL(lambda x: sys.stdout.write(x + '\n'))
        return 0

    def parse_idl(self, idl_path):
        #sys.stdout.write('\np:%s\n' % idl_path)
        f = open(idl_path, 'r')
        lines = []
        for line in f:
            lines.append(line)
            
        lines = self._clear_comments(lines)
        lines = self._paste_include(lines)
        lines = self._clear_ifdef(lines)
        #for line in lines:
        #    print line,
            
        self._parse_inner(lines)

        self._refine_model()


        
    def find_type(self, name, module_name=None):
        """ returns (module_name, 'struct' or 'enum' or 'typedef', type_name, type_value_dictionary) """
        
        def _find_type(name, module_name):
            for struct_name, struct_model in self._model[module_name]['struct'].items():
                if name == struct_name:
                    return (module_name, 'struct', struct_name, struct_model)

            for typedef_name, typedef_model in self._model[module_name]['typedef'].items():
                if name == typedef_name:
                    return (module_name, 'typedef', typedef_name, typedef_model)

            return None
        if module_name != None:
            retval = _find_type(name, module_name)
            if retval != None:
                return retval
        return _find_type(name, '__global__')

    def _refine_inner(self, type_name, module_name):
        if type_name.find('::') >= 0:
            return type_name
        if type_name.find('sequence') >= 0:
            seq_inner_type = type_name[type_name.find('<')+1: type_name.rfind('>')]
            return 'sequence< ' + self._refine_inner(seq_inner_type, module_name).strip() + ' >'
        
        type_info = self.find_type(type_name, module_name)
        if not type_info is None:
            return type_info[0] + '::' + type_info[2]
        return type_name

    def _refine_model(self):
        for module_name, module_model in self._model.items():
            for struct_name, struct_model in module_model['struct'].items():
                for value_name, value_model in struct_model.items():
                    self._model[module_name]['struct'][struct_name][value_name]['type'] = self._refine_inner(self._model[module_name]['struct'][struct_name][value_name]['type'], module_name)

            for interface_name, interface_model in module_model['interface'].items():
                for function_name, function_model in interface_model.items():
                    for argument_name, argument_model in function_model['arguments'].items():
                        self._model[module_name]['interface'][interface_name][function_name]['arguments'][argument_name]['type'] = self._refine_inner(                        self._model[module_name]['interface'][interface_name][function_name]['arguments'][argument_name]['type'], module_name)
                    function_model['returns'] = self._refine_inner(function_model['returns'], module_name)
            
            for typedef_name, typedef_model in module_model['typedef'].items():
                typedef_model['type'] = self._refine_inner(typedef_model['type'], module_name)

    def _pop_token(self):
        if len(self._tokens) == self._token_offset:
            return None
        t = self._tokens[self._token_offset].strip()
        self._token_offset = self._token_offset + 1
        return t

    def _parse_module_inner(self, module_name):
        if not module_name in self._model.keys():
            self._model[module_name] = {'struct': {},
                                        'interface' : {},
                                        'enum' : {},
                                        'typedef' : {}}
        while True:
            if self._parse_token(module_name) == '}':
                break
        return True

    def _parse_interface_inner(self, interface_name, current_module):
        # print interface_name, '---' * 10
        model = {}
        while True:
            block_tokens = []
            token = self._pop_token()
            if token == '}':
                token = self._pop_token()
                if not token == ';':
                    raise InvalidIDLSyntaxError()
                break
                return True
            block_tokens.append(token)
            while True:
                token = self._pop_token()
                if token == ';':
                    break
                block_tokens.append(token)
            returns = block_tokens[0]
            name = block_tokens[1]
            model[name] = {'returns' : returns,
                           'arguments' : {}}
            if not block_tokens[2] == '(':
                print ' -- Invalid Interface Token (%s)' % interface_name
                print block_tokens
            
            index = 3
            argument_blocks = []
            while True:
                if index == len(block_tokens):
                    break
                token = block_tokens[index]
                if token == ',' or token == ')':
                    if len(argument_blocks) == 0:
                        break

                    directions = ['in', 'out', 'inout']
                    dir = 'in'
                    if argument_blocks[0] in directions:
                        dir = argument_blocks[0]
                        argument_blocks.pop(0)
                    argument_name, argument_type = self._name_and_type(argument_blocks)
                    model[name]['arguments'][argument_name] = {'type' : argument_type,
                                                                    'direction' : dir}
                    argument_blocks = []
                else:
                    argument_blocks.append(token)
                index = index + 1
                
            
        self._model[current_module]['interface'][interface_name] = model
        return True
        
    def _name_and_type(self, blocks):
        name = blocks[-1]
        type = ''
        for t in blocks[:-1]:
            type = type + ' ' + t
        type = type.strip()
        return (name, type)
    
    def _parse_struct_inner(self, struct_name, current_module):
        model = {}
        while True:
            block_tokens = []
            token = self._pop_token()
            if token == '}':
                token = self._pop_token()
                if not token == ';':
                    raise InvalidIDLSyntaxError()
                break
                return True
            block_tokens.append(token)
            while True:
                token = self._pop_token()
                if token == ';':
                    break
                block_tokens.append(token)
            #type = block_tokens[0]
            #name = block_tokens[1]
            name, type = self._name_and_type(block_tokens)
            model[name] = {'type' : type}
            
        self._model[current_module]['struct'][struct_name] = model
        return True

    def _parse_token(self, current_module):
        token = self._pop_token()
        if token == None:
            return None
        if token == 'module':
            if not current_module == '__global__':
                raise InvalidIDLSyntaxError()
            module_name = self._pop_token()
            kakko = self._pop_token()
            if not kakko == '{':
                raise InvalidIDLSyntaxError()
            return self._parse_module_inner(module_name)
        elif token == 'struct':
            struct_name = self._pop_token()
            kakko = self._pop_token()
            if not kakko == '{':
                raise InvalidIDLSyntaxError()
            return self._parse_struct_inner(struct_name, current_module)
        elif token == 'interface':
            interface_name = self._pop_token()
            kakko = self._pop_token()
            if not kakko == '{':
                raise InvalidIDLSyntaxError()
            return self._parse_interface_inner(interface_name, current_module)
        elif token == 'typedef':
            return self._parse_typedef_inner(current_module)
        else:
            return token

    def _parse_typedef_inner(self, module_name):
        block_tokens = []
        while True:
            token = self._pop_token()
            if token == ';':
                break
            block_tokens.append(token)
            pass
        type_name_ = ''
        rindex = 1
        name = block_tokens[-rindex]
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
            name = block_tokens[-rindex]

        type_name = ''
        for t in block_tokens[:-rindex]:
            type_name = type_name + ' ' + t
        type_name = type_name + ' ' + type_name_
        type_name = type_name.strip()

        self._model[module_name]['typedef'][name] = {'type' : type_name}
        
    def _parse_inner(self, lines):
        self._tokens = []
        self._token_offset = 0
        for line in lines:
            ts = line.split(' ')
            for t in ts:
                if len(t.strip()) != 0:
                    self._tokens.append(t.strip())
                    #self._tokens = self._tokens + ts
        
        while True:
            if self._parse_token( '__global__') == None:
                break


    def _clear_ifdef(self, lines):
        output_lines = []
        def_tokens = []
        global offset
        offset = 0
        def _parse(flag):
            global offset
            while offset < len(lines):
                line = lines[offset]
                if line.startswith('#define'):
                    def_token = line.split(' ')[1]
                    def_tokens.append(def_token)
                    offset = offset + 1
                elif line.startswith('#ifdef'):
                    def_token = line.split(' ')[1]
                    offset = offset + 1
                    _parse(def_token in def_tokens)

                elif line.startswith('#ifndef'):
                    def_token = line.split(' ')[1]
                    offset = offset + 1
                    _parse(not def_token in def_tokens)

                elif line.startswith('#endif'):
                    offset = offset + 1
                    return

                else:
                    offset = offset + 1
                    if flag:
                        output_lines.append(line)

        _parse(True)
        return output_lines

                
    def _find_idl(self, filename, apply_func, idl_dirs = []):
        global retval
        retval = None
        def func(filepath):

            if os.path.basename(filepath) == filename:
                global retval
                retval = apply_func(filepath)
                
        self.forEachIDL(func, idl_dirs = idl_dirs)
        return retval

    def _clear_comments(self, lines):
        output_lines = []
        in_comment = False

        for line in lines:
            line = line.strip()
            output_line = ''
            for token in line.split(' '):
                
                if in_comment and token.find('*/') >= 0:
                    in_comment = False
                    output_line = output_line + ' ' + token[token.find('*/')+2:].strip()

                elif in_comment:
                    continue

                elif token.startswith('//'):
                    break # ignore this line
                
                elif token.find('/*') >= 0:
                    in_comment = True
                    output_line = output_line + ' ' + token[0: token.find('/*')]
                else:
                    if token.find('{') >= 0:
                        token = token.replace('{', ' { ')
                    if token.find(';') >= 0:
                        token = token.replace(';', ' ;')
                    if token.find('(') >= 0:
                        token = token.replace('(', ' ( ')
                    token = token.replace(',', ' , ')
                    token = token.replace(')', ' ) ')
                    output_line = output_line + ' ' + token.strip()
            if len(output_line.strip()) > 0:
                output_lines.append(output_line.strip() + '\n')
        
        return output_lines

    def _paste_include(self, lines):
        output_lines = []

        for line in lines:
            output_line = ''
            if line.startswith('#include'):
                def _include_paste(filepath):
                    return filepath

                if line.find('"') >= 7:
                    filename = line[line.find('"')+1 : line.rfind('"')]
                    p = self._find_idl(filename, _include_paste)
                    inc_lines = []
                    f = open(p, 'r')
                    for l in f:
                        inc_lines.append(l)
                    inc_lines = self._clear_comments(inc_lines)
                    inc_lines = self._paste_include(inc_lines)
                    #output_line = p + '\n'
                    output_lines = output_lines + inc_lines

                elif line.find('<') >= 7:
                    filename = line[line.find('<')+1 : line.rfind('>')]
                    p = self._find_idl(filename, _include_paste)
                    inc_lines = []
                    f = open(p, 'r')
                    for l in f:
                        inc_lines.append(l)
                    inc_lines = self._clear_comments(inc_lines)
                    inc_lines = self._paste_include(inc_lines)
                    output_lines = output_lines + inc_lines
                    #output_line = p + '\n'


            else:
                output_line = line
                
            output_lines.append(output_line)

        return output_lines
    @manifest
    def show(self, argv):
        """ This is help text
        """
        #self.parser.add_option('-f', '--force', help='Force option (default=False)', default=False, action='store_true', dest='force_flag')
        options, argv = self.parse_args(argv[:], self._print_alternatives)
        verbose = options.verbose_flag # This is default option
        #force   = options.force_flag

        wasanbon.arg_check(argv, 4)

        #idl_file = argv[3]
        
        self.forEachIDL(self.parse_idl)
        #self.parse_idl('/Users/ysuga/.wasanbon/idl/ARTKMarkerInfo.idl')
        #self.parse_idl('/Users/ysuga/.wasanbon/idl/ManipulatorCommonInterface_MiddleLevel.idl')

        full_typename = argv[3]
        dic = self.find(full_typename)
        import yaml
        print yaml.dump(dic, default_flow_style=False)
        return 0

    def find(self, full_typename):
        if full_typename.find('::') >= 0:
            module_names = ['__global__', full_typename[:full_typename.find('::')]]
            typename = full_typename[full_typename.find('::')+2:]

        else:
            module_names = ['__global__'] + self._model.keys()
            typename = full_typename
        for module_name in module_names:

            type_info = self.find_type(typename, module_name)
            if type_info:
                def _parse(type_i, class_i):
                    if class_i == 'struct':
                        return _parse_struct(type_i)
                    elif class_i == 'typedef':
                        return _parse_typedef(type_i)
                def _parse_typedef(type_i):
                    dic = {'typename' : type_i,
                           'typeinfo' : {}}
                    #d = self.find(type_i)
                    #if d:
                    #    dic['typeinfo'] = d
                    #else:
                    #    del dic['typeinfo']
                    return dic

                def _parse_struct(type_i):
                    #print type_i
                    dic = {'typename' : type_i['type'],
                            'typeinfo' : {}}
                    d = self.find(type_i['type'])

                    if d:
                        dic['typeinfo'] = d
                    else:
                        del dic['typeinfo']
                    return dic

                type_dic = {}
                type_dic = {
                    'module' : type_info[0],
                    'class' : type_info[1],
                    'name' : type_info[2],
                    'member' : {}
                    }
                if type_info[1] == 'typedef':
                    del type_dic['member']
                    type_dic['type_info'] = type_info[3]['type']
                else:
                    for member_name, member_type in type_info[3].items():
                        type_dic['member'][member_name] = _parse( member_type, type_info[1])
                return type_dic
        return None

        
    @manifest
    def parse(self, argv):
        """ This is help text
        """
        options, argv = self.parse_args(argv[:], self._print_alternatives)
        verbose = options.verbose_flag # This is default option

        self.forEachIDL(self.parse_idl)

        import yaml
        print yaml.dump(self._model)
