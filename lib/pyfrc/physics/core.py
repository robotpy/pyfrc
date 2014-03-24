
'''
    TODO: a better way to implement this is have something track all of
    the input values, and have that in a data structure, while also
    providing the override capability.
'''

import inspect

def _create_wrapper(cls, fname, new_fn, old_fn):
    setattr(cls, fname, lambda s, *args, **kwargs: new_fn(s, lambda *oargs, **okwargs: old_fn(s, *oargs, **okwargs), *args, **kwargs))

def set_physics(physics):
    
    from .. import wpilib

    # for now, look for a class called PhysicsEngine
    engine = physics.PhysicsEngine()
    
    print("Initializing physics patching")
    
    # iterate the methods, monkeypatch them in
    for name, new_fn in inspect.getmembers(engine, predicate=inspect.ismethod):
        if not name.startswith('sim_'):
            continue
        
        # determine which class to override
        name_c = name.split('_')
        if len(name_c) != 3:
            raise ValueError("%s is not a valid sim method name" % name)
    
        ignore, clsname, fname = name_c
    
        cls = getattr(wpilib, clsname, None)
        if cls is None or not inspect.isclass(cls):
            raise AttributeError("%s does not specify a valid class name" % name)
    
        old_fn = getattr(cls, fname, None)
        if old_fn is None:
            raise AttributeError("%s does not specify a valid attribute of %s" % (name, clsname))
        
        # TODO: inspect function and make sure it complies with the interface
        
        _create_wrapper(cls, fname, new_fn, old_fn)
        
        print("->", name, "patches %s.%s" % (clsname, fname))
    
    #
    # setup the update_sim function
    # -> TODO: this is bad form, provide a hook somewhere or something
    #    how to chain these together without breaking existing tests?
    #
    
    old_wait = wpilib.Wait
    def wait_wrapper(tm):
        now = wpilib._wpilib._fake_time.FAKETIME.Get()
        engine.update_sim(now)
        
        old_wait(tm)
        
    wpilib.Wait = wait_wrapper
    


    print("Physics initialized")
    