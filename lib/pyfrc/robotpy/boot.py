import sys

class RollbackImporter:
    def __init__(self):
        "Creates an instance and installs as the global importer"
        self.previousModules = sys.modules.copy()

    def uninstall(self):
        newmodules = sys.modules.copy()
        for modname in newmodules.keys():
            if modname not in self.previousModules and modname != "boot":
                # Force reload when modname next imported
                #print("Unloading '%s'" % modname)
                # force delete module globals
                for v in sys.modules[modname].__dict__.copy():
                    if v.startswith("__"):
                        continue
                    del sys.modules[modname].__dict__[v]
                del sys.modules[modname]

def main():
    #print(sys.path)
    if "/c/py" not in sys.path:
        sys.path.insert(0, "/c/py")
    if "." not in sys.path:
        sys.path.insert(0, ".")

    import traceback
    import gc
    import time
    #import runpy

    while True:
        rollback = RollbackImporter()
        robot = None
        try:
            print("Importing user code.")
            robot = __import__("robot")
            print("Running user code.")
            robot.run()
            #runpy.run_module("robot", run_name="__main__")
        except SystemExit:
            pass
        except:
            print("Exception in user code, type 'reboot' to restart:")
            print("-"*60)
            traceback.print_exc(file=sys.stdout)
            print("-"*60)
            return

        print("User code raised SystemExit; waiting 5 seconds before restart")
        time.sleep(5)
        sys.exc_traceback = None
        sys.last_traceback = None
        rollback.uninstall()
        if robot is not None:
            del robot
            robot = None
        gc.collect()

if __name__ == "__main__":
    main()

