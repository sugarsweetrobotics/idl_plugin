import wasanbon
from wasanbon.core.plugins import PluginFunction, manifest

class Plugin(PluginFunction):

    def __init__(self):
        super(Plugin, self).__init__()
        pass

    def depends(self):
        return ['admin.environment']

    def _print_alternatives(self, args):
        print 'hoo'
        print 'foo'
        print 'hoge'
        print 'yah'

    @manifest
    def parse(self, argv):
        """ This is help text
        """
        #self.parser.add_option('-f', '--force', help='Force option (default=False)', default=False, action='store_true', dest='force_flag')
        options, argv = self.parse_args(argv[:], self._print_alternatives)
        verbose = options.verbose_flag # This is default option
        #force   = options.force_flag

        wasanbon.arg_check(argv, 4)

        idl_file = argv[3]

        print idl_file

