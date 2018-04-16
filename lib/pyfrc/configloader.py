
import json
from os.path import abspath, dirname, exists, join, isabs

import logging
logger = logging.getLogger('pyfrc.config')


_field_root = abspath(join(dirname(__file__), 'sim', 'field'))

_field_defaults = {
    '2017': {
        'h': 31,
        'w': 29,
        'px_per_ft': 17,
        'image': join(_field_root, '2017-field.gif')
    },
    '2018': {
        'h': 27,
        'w': 30,
        'px_per_ft': 15,
        'image': join(_field_root, '2018-field.gif'),
        'game_specific_messages': [
            'RRR', 'RLR', 'LRL', 'LLL'
        ],
    },
    'default': {
        'h': 1,
        'w': 1,
        'px_per_ft': 10,
        'image': None
    }
}

_default_year = '2018'

# Do this to avoid breaking teams that created their own field stuff
_field_defaults['default']['game_specific_messages'] = _field_defaults[_default_year]['game_specific_messages']

def _load_config(robot_path):
    '''
        Used internally by pyfrc, don't call this directly.
        
        Loads a json file from sim/config.json and makes the information available
        to simulation/testing code.
        
        
    '''
    
    from . import config
    config_obj = config.config_obj
    
    sim_path = join(robot_path, 'sim')
    config_file = join(sim_path, 'config.json')
    
    if exists(config_file):
        with open(config_file, 'r') as fp:
            config_obj.update(json.load(fp))
    else:
        logger.warning("sim/config.json not found, using default simulation parameters")
    
    config_obj['simpath'] = sim_path
    
    # setup defaults
    config_obj.setdefault('pyfrc', {})
    
    config_obj['pyfrc'].setdefault('robot', {})
    config_obj['pyfrc']['robot'].setdefault('w', 2)
    
    # switched from 'h' to 'l' in 2018, but keeping it there for legacy reasons
    l = config_obj['pyfrc']['robot'].get('h', 3)
    config_obj['pyfrc']['robot'].setdefault('l', l)
    
    config_obj['pyfrc']['robot'].setdefault('starting_x', 0)
    config_obj['pyfrc']['robot'].setdefault('starting_y', 0)
    config_obj['pyfrc']['robot'].setdefault('starting_angle', 0)
    
    # list of dictionaries of x=, y=, angle=, name=
    config_obj['pyfrc']['robot'].setdefault('start_positions', [])
    
    field = config_obj['pyfrc'].setdefault('field', {})
    force_defaults = False
    
    # The rules here are complex because of backwards compat
    # -> if you specify a particular season, then it will override w/h/px
    # -> if you specify objects then you will get your own stuff
    # -> if you don't specify anything then it override w/h/px
    #    -> if you add your own, it will warn you unless you specify an image
    
    # backwards compat
    if 'season' in config_obj['pyfrc']['field']:
        season = config_obj['pyfrc']['field']['season']
        defaults = _field_defaults.get(str(season), _field_defaults['default'])
        force_defaults = True
    elif 'objects' in config_obj['pyfrc']['field']:
        defaults = _field_defaults['default']
    else:
        if 'image' not in field:
            force_defaults = True
        defaults = _field_defaults[_default_year]
    
    if force_defaults:
        if 'w' in field or 'h' in field or 'px_per_ft' in field:
            logger.warning("Ignoring field w/h/px_per_ft settings")
        field['w'] = defaults['w']
        field['h'] = defaults['h']
        field['px_per_ft'] = defaults['px_per_ft']
    
    config_obj['pyfrc']['field'].setdefault('objects', [])
    config_obj['pyfrc']['field'].setdefault('w', defaults['w'])
    config_obj['pyfrc']['field'].setdefault('h', defaults['h'])
    config_obj['pyfrc']['field'].setdefault('px_per_ft', defaults['px_per_ft'])
    img = config_obj['pyfrc']['field'].setdefault('image', defaults['image'])
    
    config_obj['pyfrc'].setdefault('game_specific_messages', defaults.get('game_specific_messages', []))
    assert isinstance(config_obj['pyfrc']['game_specific_messages'], list)
    
    if img and not isabs(config_obj['pyfrc']['field']['image']):
        config_obj['pyfrc']['field']['image'] = abspath(join(sim_path, img))
    
    config_obj['pyfrc'].setdefault('analog', {})
    config_obj['pyfrc'].setdefault('CAN', {})
    config_obj['pyfrc'].setdefault('dio', {})
    config_obj['pyfrc'].setdefault('pwm', {})
    config_obj['pyfrc'].setdefault('relay', {})
    config_obj['pyfrc'].setdefault('solenoid', {})
    
    config_obj['pyfrc'].setdefault('joysticks', {})
    for i in range(6):
        config_obj['pyfrc']['joysticks'].setdefault(str(i), {})
        config_obj['pyfrc']['joysticks'][str(i)].setdefault('axes', {})
        config_obj['pyfrc']['joysticks'][str(i)].setdefault('buttons', {})
        
        config_obj['pyfrc']['joysticks'][str(i)]['buttons'].setdefault("1", "Trigger")
        config_obj['pyfrc']['joysticks'][str(i)]['buttons'].setdefault("2", "Top")
