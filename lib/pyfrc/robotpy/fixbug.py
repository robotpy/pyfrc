
from .installer import SshController

if __name__ == '__main__':
    ssh = SshController('.__notused__', username='admin', password='')
    ssh.ssh('[ ! -f /var/local/natinst/log/FRC_UserProgram.log ] || rm -f /var/local/natinst/log/FRC_UserProgram.log')
    
    print("Fix successfully applied!")
    # intentionally didn't call ssh.close
