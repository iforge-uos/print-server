import sys

global config_dict

config_dict = {}
for arg in sys.argv[1:]:
    if '=' in arg:
        sep_idx = arg.find('=')
        key, value = arg[:sep_idx], arg[sep_idx + 1:]
        config_dict[key] = value