#!/usr/bin/env python

'''
Installs the code in ./robot to a FRC cRio-based Robot via FTP

Usage: run install.py, and it will upload
'''

import os
import ftplib
import socket
import sys
from optparse import OptionParser



def get_robot_host(team_number):
    '''Given a team number, determine the address of the robot'''
    return '10.%d.%d.2' % (team_number / 100, team_number % 100 )
    
    
def reboot_crio():
    ''' 
        Send the reboot command to any cRios connected on the network
        -> Extracted from https://github.com/rbmj/netconsole, license unknown
    '''

    # ports
    UDP_IN_PORT=6666
    UDP_OUT_PORT=6668

    out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    out.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    out.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    out.bind( ('',UDP_OUT_PORT) ) # bind is necessary for escoteric reasons stated on interwebs
    out.sendto(b'\nreboot\n', ('255.255.255.255', UDP_OUT_PORT))


class RobotCodeInstaller(object):
    """
        Use this class to create programs that automatically upload your
        python code to the robot in the right place without having
        to deal with an FTP client

        Example:

            from install import RobotCodeInstaller, get_robot_host

            installer = None
            my_team_number = 2423

            try:
                installer = RobotCodeInstaller( get_robot_host( my_team_number ) )
            except Exception as e:
                print("Could not connect to robot FTP server %s: %s" % (robot_host, e))
                exit(1)

            installer.upload_directory( '/py', '.')

            installer.close()
    """
    
    def _remove_slash(self, path):
        return path[:-1] if path.endswith('/') else path
            

    def __init__(self, robot_host, username='FRC', password='FRC', timeout=5):
        self.ftp = ftplib.FTP(robot_host, username, password, '', timeout)

    def close(self):
        '''
            Closes the connection
        '''
        self.ftp.quit()
        
    def create_remote_directory( self, remote_dir, verbose=True ):
        '''
            Creates a directory on the server. If the parent paths do not
            exist, this function creates those paths as well. 
        
            remote_dir      Path on remote server
        '''
        
        path = remote_dir.replace('\\','/').split('/')
       
        for idx in range(1,len(path)+1):
            
            rpath = '/'.join( path[:idx] )
        
            if self._create_and_list_remote_path( rpath, verbose ) is None:
                return False
            
        return True
        
    def delete_remote( self, remote_item, verbose=True ):
        '''
            Recursively deletes a directory or file. Ignores errors, since the 
            installer doesn't really care.. 
        '''
        
        try:
            files = self.ftp.nlst( remote_item )
        except ftplib.Error as e:
            return
        
        # see if this is actually a file
        if len(files) == 1 and (files[0] == remote_item or remote_item.endswith( '/' + files[0] )):
            try:
                self.ftp.delete( remote_item )
                if verbose:
                    print( 'DELETE %s' % remote_item )
            except ftplib.Error as e:
                sys.stderr.write( 'ERROR deleting file %s: %s\n' % (remote_item, e ))
        
        else:
            for file_path in files:
                
                file = file_path
                if file_path.startswith( remote_item ):
                    file = file_path[len(remote_item)+1:]
                else:
                    file_path = remote_item + '/' + file_path
                    
                if file == '.' or file == '..':
                    continue
                    
                self.delete_remote( file_path, verbose )
        
            try:                
                self.ftp.rmd( remote_item )
                if verbose:
                    print( 'RMDIR %s' % remote_item )
            except ftplib.Error as e:
                sys.stderr.write( 'ERROR deleting directory %s: %s\n' % (remote_item, e ))
                

    def upload_file( self, remote_dir, local_dir, filename, verbose=True ):
        '''
            Uploads a single file to the remote server. Does not check
            to see if the remote directory exists. You should call 
            create_remote_directory() before calling this function.
        
            Parameters: 
            
                remote_dir:
                    The remote directory to upload files to. Absolute path, 
                    unless you previously called set_current_directory(). 

                local_dir:
                    The local directory to upload files from. Absolute or relative
                    path. 

                filename:
                    The name of the file to upload
                
                verbose:
                    Set to true to output the name of each file as it is
                    being uploaded
                    
            Returns:
                True if successful, False if not successful. Errors are
                printed out to stderr
        '''
        remote_dir = self._remove_slash(remote_dir)
        local_dir = self._remove_slash(local_dir)
        
        lfn = os.path.join( local_dir, filename )
        rfn = remote_dir + '/' + filename.replace( '\\', '/' )
        
        # upload the file already!
        with open(lfn, 'rb') as stor_file:
            try:
                self.ftp.storbinary( 'STOR ' + rfn, stor_file )

                if verbose:
                    print( 'STOR ' + rfn )
                else:
                    sys.stdout.write('.')
                    sys.stdout.flush()
            except ftplib.Error as msg:
                sys.stderr.write("ERROR writing %s: %s\n" % (rfn, msg ))
                return False
            except IOError as msg:
                sys.stderr.write("ERROR reading from %s: %s\n" % (lfn, msg))
                return False
                
        return True
        
    def upload_directory( self, remote_dir, local_dir, recursive=True, verbose=False, skip_special=True ):
        '''
            Uploads the contents of a local directory to the remote server.
        
            Parameters:

                remote_root:
                    The remote directory to upload files to

                local_root:
                    The local directory to upload files from

                recursive:
                    Set to true to recursively walk local_root to upload files

                verbose:
                    Set to true to output the name of each file as it is
                    being uploaded

                skip_special:
                    Don't upload __pycache__ directories or directories/files 
                    that start with .
        '''

        remote_dir = self._remove_slash(remote_dir)
        local_dir = self._remove_slash(local_dir)

        if not os.path.isdir( local_dir ):
            sys.stderr.write("ERROR: Local root directory %s does not exist\n" % local_dir )
            return False

        for root, dirs, files in os.walk( local_dir ):

            remote_root = remote_dir + '/' + root[len(local_dir)+1:].replace( '\\', '/' )
            remote_root = self._remove_slash(remote_root)
            
            # skip .svn, .git, .hg directories
            if skip_special:
                for d in dirs[:]:
                    if d.startswith('.') or d == '__pycache__':
                        dirs.remove(d)

            sys.stdout.write(root + ': ')
            if verbose:
                sys.stdout.write('\n')

            remote_files = self._create_and_list_remote_path( remote_root, verbose )
            if remote_files is None:
                return False

            # if there is a __pycache__ directory, delete it
            pycache_dir = remote_root + '/__pycache__'
            if pycache_dir in remote_files:
                self.delete_remote(pycache_dir, verbose)

            for filename in files:

                r, ext = os.path.splitext( filename )

                # if this accidentally got in there, don't upload it
                if skip_special and (ext == '.pyc' or r.startswith('.')):
                    continue
                    
                pyc_file = remote_root + '/' + r + '.pyc'

                # for each py file, delete a pyc file associated with it
                if ext == '.py' and pyc_file in remote_files:
                    self.delete_remote( pyc_file )
                        
                if not self.upload_file( remote_root, root, filename, verbose=verbose ):
                    return False

            sys.stdout.write('\n')

            if not recursive:
                break

        return True
        
    def _create_and_list_remote_path( self, rpath, verbose ):
        # internal function: returns the contents of a remote
        # directory, if the directory does not exist it creates
        # the path
    
        rpath = self._remove_slash(rpath)
    
        try:
            files = self.ftp.nlst( rpath )
            
            # some FTP servers do not return an absolute path. Some do. We want
            # an absolute path here
            if len(files) > 0 and not files[0].startswith( rpath + '/' ):
                files = [ rpath + '/' + file for file in files ]
            
            return files
            
        except ftplib.Error:
            # directory must not exist, right?
            try:
                self.ftp.mkd( rpath )
                if verbose:
                    print( 'MKDIR ' + rpath )
                return []
                
            except ftplib.Error as msg:
                sys.stderr.write("ERROR: Creating directory %s failed: %s\n" % (rpath, msg))
                return None
                
        
    

if __name__ == '__main__':

    parser = OptionParser('Usage: %program [remote_host]')
    parser.add_option('-v', '--verbose', dest='verbose',
                        help='Verbose output', action='store_true', default=False)
    parser.add_option('-t', '--team', dest='team_number', help='Team number', default=None)


    parser.add_option('--remote-root', dest='remote_root',
                        help='Remote root directory (default: %default)',
                        default='/')

    parser.add_option('--local-root', dest='local_root',
                        help='Local root directory (default: %default)',
                        default=os.path.join( os.path.dirname(__file__), 'robot' ) )

    (options, args) = parser.parse_args()

    robot_host = None

    if len(args) == 1:
        robot_host = args[0]
    elif len(args) != 0:
        parser.error("Invalid arguments passed")

    # banner message
    print( "Robot code uploader v1.1" )


    if robot_host is None:
        # if the team number hasn't been specified in an option, then
        # ask the user for the team number.
        team_number = options.team_number

        while team_number is None:
            try:
                team_number = int(input('Team number? '))
            except ValueError:
                pass

        # determine the host name from the team number
        robot_host = '10.%d.%d.2' % (team_number / 100, team_number % 100 )

    # ok, we're ready. Process the manifest and upload it

    try:
        installer = RobotCodeInstaller( robot_host )
    except Exception as e:
        sys.stderr.write("Could not connect to robot FTP server %s: %s\n" % (robot_host, e))
        exit(1)

    installer.upload_directory( options.remote_root, options.local_root, verbose=options.verbose )

    installer.close()
    
    # New feature: ask the user to reboot after installation?
    if sys.version_info[0] < 3:
        ask = raw_input
    else:
        ask = input
    
    while True:
        yn = ask("Reboot robot? [y/n]").lower()
        if yn == 'y':
            reboot_crio()
            break
        elif yn == 'n':
            break
