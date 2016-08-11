'''

@author: MengLai 
'''
import os
import tempfile
import uuid
import time

import zstackwoodpecker.test_util as test_util
import zstackwoodpecker.test_lib as test_lib
import zstackwoodpecker.test_state as test_state

test_stub = test_lib.lib_get_test_stub()
test_obj_dict = test_state.TestStateDict()
tmp_file = '/tmp/%s' % uuid.uuid1().get_hex()


def test():
    test_util.test_dsc('Create test vm to test zstack upgrade by -u.')
    image_name = os.environ.get('imageName_i_c7')
    vm = test_stub.create_vlan_vm(image_name)
    test_obj_dict.add_vm(vm)
    if os.environ.get('zstackManagementIp') == None:
        vm.check()
    else:
        time.sleep(60)

    vm_inv = vm.get_vm()
    vm_ip = vm_inv.vmNics[0].ip
    target_file = '/root/zstack-all-in-one.tgz'
    test_stub.prepare_test_env(vm_inv, target_file)
    ssh_cmd = 'ssh  -oStrictHostKeyChecking=no -oCheckHostIP=no -oUserKnownHostsFile=/dev/null %s' % vm_ip
    test_stub.copy_id_dsa(vm_inv, ssh_cmd, tmp_file)
    test_stub.copy_id_dsa_pub(vm_inv)
    test_stub.execute_all_install(ssh_cmd, target_file, tmp_file)
    test_stub.check_installation(ssh_cmd, tmp_file, vm_inv)

# create nest-vm in vm
#    test_stub.create_nest_vm(ssh_cmd, tmp_file, vm_inv)

# create start and stop scheduler in vm 
#    start_date = int(time.time())
#    test_stub.create_stop_vm_scheduler(ssh_cmd, tmp_file, vm_inv, start_date+60)
#    test_stub.create_start_vm_scheduler(ssh_cmd, tmp_file, vm_inv, start_date+120)
    
# check scheduler 

    test_stub.upgrade_zstack(ssh_cmd, target_file, tmp_file)
    test_stub.check_installation(ssh_cmd, tmp_file, vm_inv)

    os.system('rm -f %s' % tmp_file)
    vm.destroy()
    test_util.test_pass('ZStack upgrade Test Success')

#Will be called only if exception happens in test().
def error_cleanup():
    os.system('rm -f %s' % tmp_file)
    test_lib.lib_error_cleanup(test_obj_dict)
