import os, sys

import module, token_buffer



class IDLParser():

    def __init__(self, idl_dirs=[]):
        self._global_module = module.IDLModule()
        self._dirs = idl_dirs

    @property
    def global_module(self):
        return self._global_module

    def parse(self, idl_dirs=[], except_files=[]):
        self._dirs = self._dirs + idl_dirs
        self.forEachIDL(self.parse_idl, except_files=except_files)

    def parse_idl(self, idl_path):

        f = open(idl_path, 'r')
        lines = []
        for line in f:
            lines.append(line)

        lines = self._clear_comments(lines)
        lines = self._paste_include(lines)            
        lines = self._clear_ifdef(lines)

        self._token_buf = token_buffer.TokenBuffer(lines)

        self._global_module.parse_tokens(self._token_buf)


    def forEachIDL(self, func, idl_dirs=[], except_files=[]):
        idl_dirs = self._dirs + idl_dirs
        idls_ = []
        basenames_ = []
        for idl_dir in idl_dirs:
            for f in os.listdir(idl_dir):
                if f.endswith('.idl'):
                    if not f in except_files:
                        path = os.path.join(idl_dir, f)
                        if not f in basenames_:
                            idls_.append(path)
                            basenames_.append(os.path.basename(path))

        for f in idls_:
            func(f)


    def _find_idl(self, filename, apply_func, idl_dirs=[]):
        global retval
        retval = None
        def func(filepath):

            if os.path.basename(filepath) == filename:
                global retval
                retval = apply_func(filepath)
                
        self.forEachIDL(func, idl_dirs=idl_dirs)
        return retval

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

            else:
                output_line = line
                
            output_lines.append(output_line)

        return output_lines



    def _clear_comments(self, lines):
        output_lines = []
        in_comment = False

        for line in lines:
            line = line.strip()
            output_line = ''
            if line.find('//') >= 0:
                line = line[:line.find('//')]

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
                    token = token.replace('}', ' } ')
                    output_line = output_line + ' ' + token.strip()
            if len(output_line.strip()) > 0:
                output_lines.append(output_line.strip() + '\n')
        
        return output_lines

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

