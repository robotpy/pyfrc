
import os
import sys

from ..robotpy import install

try:
    from msvcrt import getch
except ImportError:
    def getch():
        pass
    
def relpath(path):
    '''Path helper, gives you a path relative to this file'''
    return os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), path))

def run(run_fn, file_location):
    
    # run the test suite before uploading
    if '--skip-tests' not in sys.argv:
        from . import cli_test
        retval = cli_test.run(run_fn, file_location, ignore_missing_test=True)
        if retval != 0:
            print("Your robot tests failed, aborting upload. Use --skip-tests if you want to upload anyways")
            return retval
    
    # upload all files in the robot.py source directory
    local_root = os.path.abspath(os.path.dirname(file_location))
    remote_root = '/py'
    
    # TODO: exclude the test directory if it exists

    team_number = None
    team_filename = os.path.join(local_root, '.team_number')
    
    # load the team number from a file
    try:
        with open(team_filename, 'r') as fp:
            team_number = int(fp.read().strip())
            
        print("Using team number %s loaded from %s" % (team_number, team_filename))
    except:
        pass
    
        
    while team_number is None:
        try:
            team_number = int(input('Team number? '))
        except ValueError:
            pass

    # determine the host name from the team number
    robot_host = '10.%d.%d.2' % (team_number / 100, team_number % 100 )
    
    try:
        server = install.RobotCodeInstaller(robot_host)
    except Exception as e:
        print("Error connecting to remote host: %s" % e)
        getch()
        return 1
        
    print('Beginning code installation.')
    
    # delete the remote directory
    server.delete_remote(remote_root)
    server.create_remote_directory(remote_root)
    
    # upload boot.py first
    server.upload_file(remote_root, relpath('../robotpy'), 'boot.py', verbose=True)
    server.upload_directory(remote_root, local_root, verbose=True, recursive=True, skip_special=True)
    
    print('Code installation complete.')

    server.close()
    
    # after we succeed, write the team number to a file
    try:
        if not os.path.exists(team_filename):
            with open(team_filename, 'w') as fp:
                fp.write(str(team_number))
    except:
        pass
    
    while True:
        yn = str(input("Reboot robot? [y/n]")).strip().lower()
            
        if yn == 'y':
            install.reboot_crio()
            break
        elif yn == 'n':
            break
    
    return 0
