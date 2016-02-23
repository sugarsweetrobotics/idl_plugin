import sys, os
import wasanbon
from wasanbon.core.plugins import PluginFunction, manifest

from idl_parser import *

class Plugin(PluginFunction):

    def __init__(self):
        super(Plugin, self).__init__()
        self._parser = None
        pass

    def depends(self):
        return ['admin.environment']

    def _print_alternatives(self, args):
        print 'hoo'
        print 'foo'
        print 'hoge'
        print 'yah'


    def forEachIDL(self, func):
        idl_dirs = [os.path.join(wasanbon.get_rtm_root(), 'rtm', 'idl'),
                    os.path.join(wasanbon.home_path, 'idl')]

        self._parser = parser.IDLParser(idl_dirs)
        except_files = ['RTM.idl', 'RTC.idl', 'OpenRTM.idl', 'DataPort.idl', 'Manager.idl', 'SDOPackage.idl']
        self.forEachIDL(func, except_files=except_files)

    def _parse(self):
        idl_dirs = [os.path.join(wasanbon.get_rtm_root(), 'rtm', 'idl'),
                    os.path.join(wasanbon.home_path, 'idl')]

        self._parser = parser.IDLParser(idl_dirs)
        except_files = ['RTM.idl', 'RTC.idl', 'OpenRTM.idl', 'DataPort.idl', 'Manager.idl', 'SDOPackage.idl']
        self._parser.parse(except_files=except_files)


    @manifest
    def list(self, argv):
        """ This is help text
        """

        #self.parser.add_option('-f', '--force', help='Force option (default=False)', default=False, action='store_true', dest='force_flag')
        options, argv = self.parse_args(argv[:], self._print_alternatives)
        verbose = options.verbose_flag # This is default option

        self.forEachIDL(lambda x: sys.stdout.write(x + '\n'))
        return 0


    @manifest
    def parse(self, argv):
        """ This is help text
        """
        self.parser.add_option('-d', '--detail', help='Detail information option (default=False)', default=False, action='store_true', dest='detail_flag')
        self.parser.add_option('-l', '--long', help='Long format option (default=False)', default=False, action='store_true', dest='long_flag')
        options, argv = self.parse_args(argv[:], self._print_alternatives)
        verbose = options.verbose_flag # This is default option
        long = options.long_flag
        detail = options.detail_flag

        self._parse()

        import yaml
        if detail:
            print yaml.dump(self._parser.global_module.to_dic(), default_flow_style=False)
        else:
            print yaml.dump(self._parser.global_module.to_simple_dic(not long), default_flow_style=False)

    @manifest
    def show(self, argv):
        """ This is help text
        """
        self.parser.add_option('-l', '--long', help='Long option (default=False)', default=False, action='store_true', dest='long_flag')
        options, argv = self.parse_args(argv[:], self._print_alternatives)
        verbose = options.verbose_flag # This is default option
        long = options.long_flag

        wasanbon.arg_check(argv, 4)


        self._parse()

        full_typename = argv[3]
        typs = self._parser.global_module.find_types(full_typename)
        if len(typs) == 0:
            sys.stdout.write('Not Found.\n')
            return 0

        for t in typs:
            import yaml
            print yaml.dump(t.to_simple_dic(), default_flow_style=False)

        return 0
        



