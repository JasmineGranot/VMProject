import sys
from pathlib import Path
import pandas as pd
from flask import Flask, request, jsonify
import json
import time
from vm_flask_project.logger import create_logger
from vm_flask_project.stats_data import StatsData
from vm_flask_project.consts import Consts

app = Flask(__name__)
logger = create_logger("vm-app")


def setup_app(file_path):
    app.FILE_TO_LOAD_PATH = file_path

    try:
        with open(app.FILE_TO_LOAD_PATH) as json_file:
            data = json.load(json_file)
    except FileNotFoundError as e:
        logger.error(e)
        raise
    logger.info(f"loaded file from {app.FILE_TO_LOAD_PATH}")
    app.vm_in_data_list, app.fw_rules_in_data_list = _validate_json_file(data)

    app.meta = StatsData(len(app.vm_in_data_list))


def _validate_json_file(data):
    logger.info('validating virtual machines in file')
    if Consts.VMConsts.VM_LIST not in data:
        logger.warning(f"{Consts.VMConsts.VM_LIST} field was not found in file. Using empty instead.")

    vm_in_data_list = data.get(Consts.VMConsts.VM_LIST, {})

    if _get_is_json_has_missing_val(vm_in_data_list):
        raise ValueError('virtual machines has missing attributes.')

    logger.info('validating virtual machines in file')
    if Consts.FWConsts.FW_LIST not in data:
        logger.warning(f"{Consts.FWConsts.FW_LIST} field was not found in file. Using empty instead.")

    fw_rules_in_data_list = data.get(Consts.FWConsts.FW_LIST, {})
    if _get_is_json_has_missing_val(fw_rules_in_data_list):
        raise ValueError('firewall rules has missing attributes.')

    return vm_in_data_list, fw_rules_in_data_list


def _get_is_json_has_missing_val(json_data):
    """
    :type json_data: a json object
    return keys as list, ignoring data with miising values
    """
    df = pd.DataFrame(json_data)
    total_len = len(df)
    df.dropna(inplace=True)
    new_len = len(df)
    if total_len > new_len:
        logger.error('file has missing attributes.')
        return True
    return False


@app.route('/api/v1/stats', methods=['GET'])
def api_stats():
    """
    Gets an API get request 
    :return: a dictionary representing statsdata object.
    """
    start_time = time.time()
    logger.info('handling stats request.')
    stats_data = app.meta.get_stats_as_dict()
    end_time = time.time()

    app.meta.add_query(end_time - start_time)
    return jsonify(stats_data)


@app.route('/api/v1/attack', methods=['GET'])
def api_attack():
    """
    Gets an API get request with id of a virtual machine
    :return: virtual machines with an access to the given machine.
    """
    start_time = time.time()
    logger.info('handling attack request.')

    if Consts.VMConsts.QUERY_PARAM_ID in request.args:
        vm_id = request.args[Consts.VMConsts.QUERY_PARAM_ID]
    else:
        error_msg = 'No virtual machine id was provided. Please specify an vm_id.'
        logger.error(error_msg)
        return f'Error: {error_msg}', 400

    try:
        potential_threat_vm = _get_attackers(vm_id)

        return jsonify(_get_names_of_vms(potential_threat_vm))

    except ValueError as err:
        return f"Error: {err}", 404

    finally:
        end_time = time.time()
        app.meta.add_query(end_time - start_time)


def _get_names_of_vms(vm_list):
    return list(map(lambda d: d.get(Consts.VMConsts.VM_ID), vm_list))


def _get_attackers(vm_id):
    """
    :param vm_id: an id of a virtual machine to query. Assuming id is unique.
    :return: a list of virtual machines which has access to the queried virtual machine.
    """
    vm = _get_vm_by_id(vm_id)
    tags_with_access = _get_tags_set_by_firewall_rules(vm.get(Consts.VMConsts.TAGS))
    return _get_vm_by_tags(tags_with_access)


def _get_vm_by_tags(tags_set, vm_id=None, exclude_self=False):
    """
    :param tags_set: a set of tags
    :param vm_id: an id of specific virtual machine
    :param exclude_self: boolean: whether exclude the given vm
    :return: a list of virtual machines, each containing at least one of the given tags_list
    """
    vms_with_access_by_tag = filter(lambda d: set(d.get(Consts.VMConsts.TAGS)).intersection(tags_set),
                                    app.vm_in_data_list)

    if exclude_self and vm_id:
        vms_with_access_by_tag = filter(lambda d: d.get(Consts.VMConsts.VM_ID) != vm_id, vms_with_access_by_tag)

    return list(vms_with_access_by_tag)


def _get_vm_by_id(vm_id):
    """
    :param vm_id: an id of a virtual machine to query. Assuming id is unique.
    :return: a dictionary representing the vm given out of the data.
    """
    vm = list(filter(lambda d: d.get(Consts.VMConsts.VM_ID) == vm_id, app.vm_in_data_list))

    # make sure vm exist in the data
    if not vm:
        error_msg = f"Virtual machine with id {vm_id} was not found"
        logger.error(error_msg)
        raise ValueError(error_msg)

    return vm[0]


def _get_tags_set_by_firewall_rules(dst_tags):
    """
    :param dst_tags: a list of destination tags.
    :return: a set of source tags which has access to the destination tags provided according to firewall rules.
    """

    tags_with_access = set(
        map(lambda d: d.get(Consts.FWConsts.SRC_TAG),
            filter(lambda d: d.get(Consts.FWConsts.DST_TAG) in dst_tags, app.fw_rules_in_data_list)))

    return tags_with_access


if __name__ == "__main__":
    json_file = sys.argv[1] if len(sys.argv) > 1 else ''
    json_file = Consts.DATA_PATH / json_file
    setup_app(json_file)
    app.run()
