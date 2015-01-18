
import inspect
import os

import shutil
import tempfile
import threading

from os.path import abspath, basename, dirname, exists, join, splitext

from ..robotpy import installer


def relpath(path):
    '''Path helper, gives you a path relative to this file'''
    return os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), path))
    
class PyFrcDeploy:
    """
        Uploads your robot code to the robot and executes it immediately
    """
    
    def __init__(self, parser):
        ''' :type parser: argparse.ArgumentParser '''
        parser.add_argument('--builtin', default=False, action='store_true',
                                help="Use pyfrc's builtin tests if no tests are specified")
        
        parser.add_argument('--skip-tests', action='store_true', default=False,
                            help="If specified, don't run tests before uploading code to robot (DANGEROUS)")
        
        parser.add_argument('--debug', action='store_true', default=False,
                            help="If specified, runs the code in debug mode (which only currently enables verbose logging)")
        
        parser.add_argument('--nonstandard', action='store_true', default=False,
                            help="When specified, allows you to deploy code in a file that isn't called robot.py")
        
        parser.add_argument('--nc', '--netconsole', action='store_true', default=False,
                            help="Attach netconsole listener and show robot stdout")

        parser.add_argument('--in-place', action='store_true', default=False,
                            help="Overwrite currently deployed code, don't delete anything, and don't restart running robot code.")
    
    def run(self, options, robot_class, **static_options):
        
        from .. import config
        config.mode = 'upload'
        
        # run the test suite before uploading
        if not options.skip_tests:
            from .cli_test import PyFrcTest
            
            tester = PyFrcTest()
            
            retval = tester.run_test([], robot_class, options.builtin, ignore_missing_test=True)
            if retval != 0:
                print("Your robot tests failed, aborting upload. Use --skip-tests if you want to upload anyways")
                return retval
        
        # upload all files in the robot.py source directory
        robot_file = abspath(inspect.getfile(robot_class))
        robot_path = dirname(robot_file)
        robot_filename = basename(robot_file)
        cfg_filename = join(robot_path, '.deploy_cfg')
        
        if not options.nonstandard and robot_filename != 'robot.py':
            print("ERROR: Your robot code must be in a file called robot.py (launched from %s)!" % robot_filename)
            print()
            print("If you really want to do this, then specify the --nonstandard argument")
            return 1
        
        # This probably should be configurable... oh well
        
        deploy_dir = '/home/lvuser'
        py_deploy_dir = '%s/py' % deploy_dir
        
        # note below: deployed_cmd appears that it only can be a single line
        
        if options.debug:
            deployed_cmd = 'env LD_PRELOAD=/lib/libstdc++.so.6.0.20 /usr/local/frc/bin/netconsole-host /usr/local/bin/python3 %s/%s -v run' % (py_deploy_dir, robot_filename)
            deployed_cmd_fname = 'robotDebugCommand'
            extra_cmd = 'touch /tmp/frcdebug; chown lvuser:ni /tmp/frcdebug'
        else:
            deployed_cmd = 'env LD_PRELOAD=/lib/libstdc++.so.6.0.20 /usr/local/frc/bin/netconsole-host /usr/local/bin/python3 -O %s/%s run' % (py_deploy_dir, robot_filename)
            deployed_cmd_fname = 'robotCommand'
            extra_cmd = ''

        if options.in_place:
            del_cmd = ""
        else:
            del_cmd = "[ -d %(py_deploy_dir)s ] && rm -rf %(py_deploy_dir)s;"

        del_cmd %= {"py_deploy_dir": py_deploy_dir}
        sshcmd = "/bin/bash -ce '" + \
                 '%(del_cmd)s' + \
                 'echo "%(cmd)s" > %(deploy_dir)s/%(cmd_fname)s; ' + \
                 '%(extra_cmd)s' + \
                 "'"
              
        sshcmd %= {
            'del_cmd': del_cmd,
            'deploy_dir': deploy_dir,
            'cmd': deployed_cmd,
            'cmd_fname': deployed_cmd_fname,
            'extra_cmd': extra_cmd
        }

        nc_thread = None
        
        try:
            controller = installer.SshController(cfg_filename,
                                                 username='lvuser',
                                                 password='')
            
            # This asks the user if not configured, so get the value first
            hostname = controller.hostname
            print("Deploying to robot at", hostname)

            # Housekeeping first
            controller.ssh(sshcmd) 
            
            # Copy the files over, copy to a temporary directory first
            # -> this is inefficient, but it's easier in sftp
            tmp_dir = tempfile.mkdtemp()
            py_tmp_dir = join(tmp_dir, 'py')
                    
            try:
                self._copy_to_tmpdir(py_tmp_dir, robot_path)
                controller.sftp(py_tmp_dir, deploy_dir, mkdir=not options.in_place)
            finally:
                shutil.rmtree(tmp_dir)
            
            fix_pyfrc_2015_0_x = '[ ! -f /var/local/natinst/log/FRC_UserProgram.log ] || rm -f /var/local/natinst/log/FRC_UserProgram.log;'

            if not options.in_place:
                # Restart the robot code and we're done!
                sshcmd = "/bin/bash -ce '" + \
                         fix_pyfrc_2015_0_x + \
                         '. /etc/profile.d/natinst-path.sh; ' + \
                         'chown -R lvuser:ni %s; ' + \
                         '/usr/local/frc/bin/frcKillRobot.sh -t -r' + \
                         "'"
            
                sshcmd %= (py_deploy_dir)
            
            # start the netconsole listener now if requested, *before* we
            # actually start the robot code, so we can see all messages
            if options.nc:
                from netconsole import run
                nc_event = threading.Event()
                nc_thread = threading.Thread(target=run,
                                             kwargs={'init_event': nc_event},
                                             daemon=True)
                nc_thread.start()
                nc_event.wait(5)
                print("Netconsole is listening...")
            
            controller.ssh(sshcmd)
            controller.close()
            
        except installer.Error as e:
            print("ERROR: %s" % e)
            return 1
        else:
            print("Deploy was successful!")
        
        if nc_thread is not None:
            nc_thread.join()
        
        return 0

    def _copy_to_tmpdir(self, tmp_dir, robot_path):
        
        upload_files = []
        
        for root, dirs, files in os.walk(robot_path):
            
            prefix = root[len(robot_path)+1:]
            os.mkdir(join(tmp_dir, prefix))
            
            # skip .svn, .git, .hg, etc directories
            for d in dirs[:]:
                if d.startswith('.') or d == '__pycache__':
                    dirs.remove(d)
                    
            # skip .pyc files
            for filename in files:
                
                r, ext = splitext(filename)
                if ext == 'pyc' or r.startswith('.'):
                    continue
                
                shutil.copy(join(root, filename), join(tmp_dir, prefix, filename))
        
        return upload_files
