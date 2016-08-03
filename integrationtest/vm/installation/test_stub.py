import os
import subprocess
import time

import zstacklib.utils.ssh as ssh
import zstackwoodpecker.test_util as test_util
import zstackwoodpecker.test_lib as test_lib
import zstackwoodpecker.operations.resource_operations as res_ops
import zstackwoodpecker.zstack_test.zstack_test_vm as zstack_vm_header

def create_vlan_vm(image_name, l3_name=None, disk_offering_uuids=None):
    image_uuid = test_lib.lib_get_image_by_name(image_name).uuid
    if not l3_name:
        l3_name = os.environ.get('l3PublicNetworkName')

    l3_net_uuid = test_lib.lib_get_l3_by_name(l3_name).uuid
    return create_vm([l3_net_uuid], image_uuid, 'zs_install_%s' % image_name, \
            disk_offering_uuids)

def create_vm(l3_uuid_list, image_uuid, vm_name = None, \
        disk_offering_uuids = None, default_l3_uuid = None):
    vm_creation_option = test_util.VmOption()
    conditions = res_ops.gen_query_conditions('type', '=', 'UserVm')
    instance_offering_uuid = res_ops.query_resource(res_ops.INSTANCE_OFFERING, conditions)[0].uuid
    vm_creation_option.set_instance_offering_uuid(instance_offering_uuid)
    vm_creation_option.set_l3_uuids(l3_uuid_list)
    vm_creation_option.set_image_uuid(image_uuid)
    vm_creation_option.set_name(vm_name)
    vm_creation_option.set_data_disk_uuids(disk_offering_uuids)
    vm_creation_option.set_default_l3_uuid(default_l3_uuid)
    vm = zstack_vm_header.ZstackTestVm()
    vm.set_creation_option(vm_creation_option)
    vm.create()
    return vm

def check_str(string):
    if string == None:
        return ""
    return string

def execute_shell_in_process(cmd, tmp_file, timeout = 1200, no_timeout_excep = False):
    logfd = open(tmp_file, 'w', 0)
    process = subprocess.Popen(cmd, executable='/bin/sh', shell=True, stdout=logfd, stderr=logfd, universal_newlines=True)

    start_time = time.time()
    while process.poll() is None:
        curr_time = time.time()
        test_time = curr_time - start_time
        if test_time > timeout:
            process.kill()
            logfd.close()
            logfd = open(tmp_file, 'r')
            test_util.test_logger('[shell:] %s [timeout logs:] %s' % (cmd, '\n'.join(logfd.readlines())))
            logfd.close()
            if no_timeout_excep:
                test_util.test_logger('[shell:] %s timeout, after %d seconds' % (cmd, test_time))
                return 1
            else:
                os.system('rm -f %s' % tmp_file)
                test_util.test_fail('[shell:] %s timeout, after %d seconds' % (cmd, timeout))
        if test_time%10 == 0:
            print('shell script used: %ds' % int(test_time))
        time.sleep(1)
    logfd.close()
    logfd = open(tmp_file, 'r')
    test_util.test_logger('[shell:] %s [logs]: %s' % (cmd, '\n'.join(logfd.readlines())))
    logfd.close()
    return process.returncode

def execute_shell_in_process_stdout(cmd, tmp_file, timeout = 1200, no_timeout_excep = False):
    logfd = open(tmp_file, 'w', 0)
    process = subprocess.Popen(cmd, executable='/bin/sh', shell=True, stdout=logfd, universal_newlines=True)

    start_time = time.time()
    while process.poll() is None:
        curr_time = time.time()
        test_time = curr_time - start_time
        if test_time > timeout:
            process.kill()
            logfd.close()
            logfd = open(tmp_file, 'r')
            test_util.test_logger('[shell:] %s [timeout logs:] %s' % (cmd, '\n'.join(logfd.readlines())))
            logfd.close()
            if no_timeout_excep:
                test_util.test_logger('[shell:] %s timeout, after %d seconds' % (cmd, test_time))
                return 1
            else:
                os.system('rm -f %s' % tmp_file)
                test_util.test_fail('[shell:] %s timeout, after %d seconds' % (cmd, timeout))
        if test_time%10 == 0:
            print('shell script used: %ds' % int(test_time))
        time.sleep(1)
    logfd.close()
    logfd = open(tmp_file, 'r')
    stdout = '\n'.join(logfd.readlines())
    logfd.close()
    test_util.test_logger('[shell:] %s [logs]: %s' % (cmd, stdout))
    return (process.returncode, stdout)

def scp_file_to_vm(vm_inv, src_file, target_file):
    vm_ip = vm_inv.vmNics[0].ip
    vm_username = test_lib.lib_get_vm_username(vm_inv)
    vm_password = test_lib.lib_get_vm_password(vm_inv)
    ssh.scp_file(src_file, target_file, vm_ip, vm_username, vm_password)

def copy_id_dsa(vm_inv, ssh_cmd, tmp_file):
    src_file = '/root/.ssh/id_dsa'
    target_file = '/root/.ssh/id_dsa'
    if not os.path.exists(src_file):
        os.system("ssh-keygen -t dsa -N '' -f %s" % src_file)

    scp_file_to_vm(vm_inv, src_file, target_file)
    cmd = '%s "chmod 600 /root/.ssh/id_dsa"' % ssh_cmd
    process_result = execute_shell_in_process(cmd, tmp_file)

def copy_id_dsa_pub(vm_inv):
    src_file = '/root/.ssh/id_dsa.pub'
    target_file = '/root/.ssh/authorized_keys'
    if not os.path.exists(src_file):
        os.system("ssh-keygen -t dsa -N '' -f %s" % src_file)
    scp_file_to_vm(vm_inv, src_file, target_file)


def prepare_mevoco_test_env(vm_inv):
    all_in_one_pkg = os.environ['zstackPkg']
    scp_file_to_vm(vm_inv, all_in_one_pkg, '/root/zizhu.bin')

    vm_ip = vm_inv.vmNics[0].ip
    ssh.make_ssh_no_password(vm_ip, test_lib.lib_get_vm_username(vm_inv), \
            test_lib.lib_get_vm_password(vm_inv))

def prepare_test_env(vm_inv, aio_target):
    zstack_install_script = os.environ['zstackInstallScript']
    target_file = '/root/zstack_installer.sh'
    vm_ip = vm_inv.vmNics[0].ip
    vm_username = test_lib.lib_get_vm_username(vm_inv)
    vm_password = test_lib.lib_get_vm_password(vm_inv)
    scp_file_to_vm(vm_inv, zstack_install_script, target_file)

    all_in_one_pkg = os.environ['zstackPkg']
    scp_file_to_vm(vm_inv, all_in_one_pkg, aio_target)

    ssh.make_ssh_no_password(vm_ip, vm_username, vm_password)

def prepare_upgrade_test_env(vm_inv, aio_target, upgrade_pkg):
    zstack_install_script = os.environ['zstackInstallScript']
    target_file = '/root/zstack_installer.sh'
    vm_ip = vm_inv.vmNics[0].ip
    vm_username = test_lib.lib_get_vm_username(vm_inv)
    vm_password = test_lib.lib_get_vm_password(vm_inv)
    scp_file_to_vm(vm_inv, zstack_install_script, target_file)

    scp_file_to_vm(vm_inv, upgrade_pkg, aio_target)

    ssh.make_ssh_no_password(vm_ip, vm_username, vm_password)

def prepare_yum_repo(vm_inv):
    origin_file = '/etc/yum.repos.d/epel.repo'
    target_file = '/etc/yum.repos.d/epel.repo'
    vm_ip = vm_inv.vmNics[0].ip
    vm_username = test_lib.lib_get_vm_username(vm_inv)
    vm_password = test_lib.lib_get_vm_password(vm_inv)
    scp_file_to_vm(vm_inv, origin_file, target_file)

    ssh.make_ssh_no_password(vm_ip, vm_username, vm_password)

def upgrade_zstack(ssh_cmd, target_file, tmp_file):
    env_var = "WEBSITE='%s'" % 'localhost'

    cmd = '%s "%s bash %s -u"' % (ssh_cmd, env_var, target_file)

    process_result = execute_shell_in_process(cmd, tmp_file)

    if process_result != 0:
        cmd = '%s "cat /tmp/zstack_installation.log"' % ssh_cmd
        execute_shell_in_process(cmd, tmp_file)
        if 'no management-node-ready message received within' in open(tmp_file).read():
            times = 30
            cmd = '%s "zstack-ctl status"' % ssh_cmd
            while (times > 0):
                time.sleep(10)
                process_result = execute_shell_in_process(cmd, tmp_file, 10, True)
                times -= 0
                if process_result == 0:
                    test_util.test_logger("management node start after extra %d seconds" % (30 - times + 1) * 10 )
                    return 0
                test_util.test_logger("mn node is still not started up, wait for another 10 seconds...")
            else:
                test_util.test_fail('zstack upgrade failed')

def execute_mevoco_aliyun_install(ssh_cmd, tmp_file):
    target_file = '/root/zizhu.bin'
    env_var = "ZSTACK_ALL_IN_ONE='%s' WEBSITE='%s'" % \
            (target_file, 'localhost')

    cmd = '%s "%s bash /root/zizhu.bin -R aliyun -m"' % (ssh_cmd, env_var)

    process_result = execute_shell_in_process(cmd, tmp_file)

    if process_result != 0:
        cmd = '%s "cat /tmp/zstack_installation.log"' % ssh_cmd
        execute_shell_in_process(cmd, tmp_file)
        if 'no management-node-ready message received within' in open(tmp_file).read():
            times = 30
            cmd = '%s "zstack-ctl status"' % ssh_cmd
            while (times > 0):
                time.sleep(10)
                process_result = execute_shell_in_process(cmd, tmp_file, 10, True)
                times -= 0
                if process_result == 0:
                    test_util.test_logger("management node start after extra %d seconds" % (30 - times + 1) * 10 )
                    return 0
                test_util.test_logger("mn node is still not started up, wait for another 10 seconds...")
            else:
                test_util.test_fail('zstack installation failed')

def execute_mevoco_online_install(ssh_cmd, tmp_file):
    target_file = '/root/zizhu.bin'
    env_var = "ZSTACK_ALL_IN_ONE='%s' WEBSITE='%s'" % \
            (target_file, 'localhost')

    cmd = '%s "%s bash /root/zizhu.bin -m"' % (ssh_cmd, env_var)

    process_result = execute_shell_in_process(cmd, tmp_file)

    if process_result != 0:
        cmd = '%s "cat /tmp/zstack_installation.log"' % ssh_cmd
        execute_shell_in_process(cmd, tmp_file)
        if 'no management-node-ready message received within' in open(tmp_file).read():
            times = 30
            cmd = '%s "zstack-ctl status"' % ssh_cmd
            while (times > 0):
                time.sleep(10)
                process_result = execute_shell_in_process(cmd, tmp_file, 10, True)
                times -= 0
                if process_result == 0:
                    test_util.test_logger("management node start after extra %d seconds" % (30 - times + 1) * 10 )
                    return 0
                test_util.test_logger("mn node is still not started up, wait for another 10 seconds...")
            else:
                test_util.test_fail('zstack installation failed')

def execute_all_install(ssh_cmd, target_file, tmp_file):
    env_var = " WEBSITE='%s'" % ('localhost')

    cmd = '%s "%s bash %s"' % (ssh_cmd, env_var, target_file)

    process_result = execute_shell_in_process(cmd, tmp_file, 2400)

    if process_result != 0:
        cmd = '%s "cat /tmp/zstack_installation.log"' % ssh_cmd
        execute_shell_in_process(cmd, tmp_file)
        if 'no management-node-ready message received within' in open(tmp_file).read():
            times = 30
            cmd = '%s "zstack-ctl status"' % ssh_cmd
            while (times > 0):
                time.sleep(10)
                process_result = execute_shell_in_process(cmd, tmp_file, 10, True)
                times -= 0
                if process_result == 0:
                    test_util.test_logger("management node start after extra %d seconds" % (30 - times + 1) * 10 )
                    return 0
                test_util.test_logger("mn node is still not started up, wait for another 10 seconds...")
            else:
                test_util.test_fail('zstack installation failed')

def only_install_zstack(ssh_cmd, target_file, tmp_file):
    env_var = "WEBSITE='%s'" % 'localhost'

    cmd = '%s "%s bash %s -d -i"' % (ssh_cmd, env_var, target_file)

    process_result = execute_shell_in_process(cmd, tmp_file)

    if process_result != 0:
        cmd = '%s "cat /tmp/zstack_installation.log"' % ssh_cmd
        execute_shell_in_process(cmd, tmp_file)
        test_util.test_fail('zstack installation failed')

def check_installation(ssh_cmd, tmp_file, vm_inv):
    cmd = '%s "/usr/bin/zstack-cli LogInByAccount accountName=admin password=password"' % ssh_cmd
    process_result = execute_shell_in_process(cmd, tmp_file)
    if process_result != 0:
        test_util.test_fail('zstack-cli login failed')

    vm_passwd = test_lib.lib_get_vm_password(vm_inv)
    vm_ip = vm_ip = vm_inv.vmNics[0].ip
    cmd = '%s "/usr/bin/zstack-cli AddSftpBackupStorage name=bs1 description=bs hostname=%s username=root password=%s url=/home/bs"' % (ssh_cmd, vm_ip, vm_passwd)
    process_result = execute_shell_in_process(cmd, tmp_file)
    if process_result != 0:
        test_util.test_fail('zstack-cli create Backup Storage failed')

    cmd = '%s "/usr/bin/zstack-cli QuerySftpBackupStorage name=bs1"' % ssh_cmd
    process_result = execute_shell_in_process(cmd, tmp_file)
    if process_result != 0:
        test_util.test_fail('zstack-cli Query Backup Storage failed')
    cmd = '%s "/usr/bin/zstack-cli QuerySftpBackupStorage name=bs1 fields=uuid" | grep uuid | awk \'{print $2}\'' % ssh_cmd
    (process_result, bs_uuid) = execute_shell_in_process_stdout(cmd, tmp_file)
    if process_result != 0:
        test_util.test_fail('zstack-cli Query Backup Storage failed')

    cmd = '%s "/usr/bin/zstack-cli DeleteBackupStorage uuid=%s"' % (ssh_cmd, bs_uuid.split('"')[1])
    process_result = execute_shell_in_process(cmd, tmp_file)
    if process_result != 0:
        test_util.test_fail('zstack-cli Delete Backup Storage failed')

# add check item
    cmd = '%s "/usr/bin/zstack-ctl status" | grep \'^MN status\' | awk \'{print $3}\'' % ssh_cmd
    (process_result, mn_status) = execute_shell_in_process_stdout(cmd, tmp_file)
    if process_result != 0:
        test_util.test_fail('zstack-ctl get MN status failed')
    if not 'Running' in mn_status:
        test_util.test_dsc('management node is not running, try to start management node')
        cmd = '%s "/usr/bin/zstack-ctl start_node"' % ssh_cmd
        process_result = process_result = execute_shell_in_process(cmd, tmp_file)
        if process_result != 0:
            test_util.test_fail('zstack-ctl start_node failed')
        time.sleep(5)
        cmd = '%s "/usr/bin/zstack-ctl status" | grep \'^MN status\' | awk \'{print $3}\'' % ssh_cmd
        (process_result, mn_status) = execute_shell_in_process_stdout(cmd, tmp_file)
        if process_result != 0:
            test_util.test_fail('zstack-ctl get MN status failed')
        if not 'Running' in mn_status:
            test_util.test_fail('management node is not running, start management node failed')
    test_util.test_dsc('check MN, MN is running')

    cmd = '%s "/usr/bin/zstack-ctl status" | grep \'^UI status\' | awk \'{print $3}\'' % ssh_cmd
    (process_result, ui_status) = execute_shell_in_process_stdout(cmd, tmp_file)
    if process_result != 0:
        test_util.test_fail('zstack-ctl get UI status failed')
    if not 'Running' in ui_status:
        test_util.test_dsc('UI is not running, try to start UI')
        cmd = '%s "/usr/bin/zstack-ctl start_ui"' % ssh_cmd
        process_result = process_result = execute_shell_in_process(cmd, tmp_file)
        if process_result != 0:
            test_util.test_fail('zstack-ctl start_ui failed')
        time.sleep(5)
        cmd = '%s "/usr/bin/zstack-ctl status" | grep \'^MN status\' | awk \'{print $3}\'' % ssh_cmd
        (process_result, mn_status) = execute_shell_in_process_stdout(cmd, tmp_file)
        if process_result != 0:
            test_util.test_fail('zstack-ctl get MN status failed')
        if not 'Running' in mn_status:
            test_util.test_fail('UI is not running, start UI failed')
    test_util.test_dsc('check UI, UI is running')

