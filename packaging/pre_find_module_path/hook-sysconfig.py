import sysconfig

def pre_find_module_path(hook_api):
    old_get_sysconfigdata_name = sysconfig._get_sysconfigdata_name
    
    def new_get_sysconfigdata_name(check_exists = True):
        return old_get_sysconfigdata_name(check_exists)
    
    sysconfig._get_sysconfigdata_name = new_get_sysconfigdata_name
