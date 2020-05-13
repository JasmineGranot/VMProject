from pathlib import Path
class Consts:

    FILE_TO_LOAD_PATH = Path('data')/'input-2.json'

    class VMConsts:
        VM_LIST = 'vms'
        VM_ID = 'vm_id'
        TAGS = 'tags'

        QUERY_PARAM_ID = VM_ID

    class FWConsts:
        FW_LIST = 'fw_rules'
        FW_ID = ' fw_id'
        SRC_TAG = 'source_tag'
        DST_TAG = 'dest_tag'
