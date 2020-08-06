import argparse
import sys

import yaml


class YamlFileType(object):
    """Factory for creating yaml file object types

    Instances of YamlFileType are typically passed as type= arguments to the
    ArgumentParser add_argument() method.
    """

    def __call__(self, string):
        try:
            # the special argument "-" means sys.std{in,out}
            if string == '-':
                return yaml.safe_load(sys.stdin)
            else:
                with open(string) as fp:
                    return yaml.safe_load(fp)
        except OSError:
            raise argparse.ArgumentTypeError(f"can't open {string}")
        except yaml.YAMLError:
            raise argparse.ArgumentTypeError(f"error in file {string}")

    def __repr__(self):
        return '%s' % type(self).__name__
