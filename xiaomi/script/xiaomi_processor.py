# -*- coding:UTF-8 -*-


import sys
import json
import time
import logging
import requests
import warnings

warnings.filterwarnings('ignore')
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

content_type = "application/json"
online_http_address = "xxx.xx.xx"
online_client_id = "xxxx"
online_client_secret = "********"
batch_size = 100
query_size = 20

status_code = {
    "success": 1,
    "unkown": 2,
    "fail": 3,
}


def get_dsp_token():
    get_interface = "xxx"
    validate_interface = "xxxx"

    try:
        # get token
        get_token_url = online_http_address + "/" + \
                        get_interface + "?" + \
                        "clientId=" + online_client_id + "&" + \
                        "clientSecret=" + online_client_secret
        logging.debug(get_token_url)
        response = requests.get(get_token_url, verify=False)
        logging.debug(response.text.encode("utf-8"))
        response_data = json.loads(response.text)
        if response_data["code"] != "0":
            logging.debug("get_token: response code is not 0.")
            return False, 0
        token = response_data["token"]
        expires_time = response_data["expires_in"]
        logging.debug(token)
        logging.debug(expires_time)
    except Exception as e:
        logging.debug("get token failed: " + str(e))
        return False, 0
    return True, token


def validate_dsp_token(token):
    get_interface = "xxx"
    validate_interface = "xxxx"
    try:
        # validate token
        validate_token_url = online_http_address + "/" + \
                                validate_interface + "?" + \
                                "token=" + token
        logging.debug(validate_token_url)
        response = requests.get(validate_token_url)
        logging.debug(response.text.encode("utf-8"))
        response_data = json.loads(response.text)
        if response_data["code"] != "0":
            logging.debug("validate_token: response code is not 0.")
            return False, ""
        dsp_name = response_data["dsp"]

    except Exception as e:
        logging.debug("validate token failed: " + str(e))
        return False, ""

    return True, dsp_name


def update_dsp_token(token, retry_num):
    get_status = False
    new_token = 0
    dsp_name = ""

    is_valid, dsp_name = validate_dsp_token(token)
    for i in range(retry_num):
        if is_valid:
            return True, token, dsp_name

        # token has expired, get new token
        get_status, new_token = get_dsp_token()
        if get_status:
            is_valid, dsp_name = validate_dsp_token(new_token)

    if is_valid:
        return True, new_token, dsp_name
    return False, 0, ""


def upload_apk_data(token, dsp_name, packages):
    interface = "xxxxx"
    upload_url = online_http_address + "/" + interface
    header_map = {
        "Content-Type": content_type,
        "Authorization": token
    }
    data_json = json.dumps({
        "seat": dsp_name,
        "packages": packages
    })
    res = ""
    try:
        response = requests.post(upload_url, data=data_json, headers=header_map)
        res = response.text.encode("utf-8")
        logging.debug(upload_url)
        logging.debug(data_json)
        logging.debug(header_map)
        logging.debug(response.text.encode("utf-8"))
    except Exception as e:
        logging.error(e)
    return res


def load_apk_name(apk_name_file):
    apk_name_set = set([])
    with open(apk_name_file, "r") as f:
        for line in f.readlines():
            data = line.strip()
            apk_name_set.add(data)
    return apk_name_set


def main():
    func = sys.argv[1]
    if func == "download":
        logging.basicConfig(filename='../logs/request.log', level=logging.DEBUG, format=LOG_FORMAT)

        apk_name_file = sys.argv[2]
        apk_name_list = list(load_apk_name(apk_name_file))
        output_file = sys.argv[3]
        output_f = open(output_file, "w")

        # get token
        get_status, token = get_dsp_token()

        # upload apk_name
        retry_num = 3
        apk_name_num = len(apk_name_list)
        batch_num = apk_name_num / batch_size + 1
        query_num = batch_size / query_size + 1
        for i in range(batch_num):
            batch_begin = i * batch_size
            batch_end = min((i + 1) * batch_size, apk_name_num)
            if batch_begin >= batch_end:
                continue

            batch_package_list = apk_name_list[batch_begin:batch_end]
            for j in range(query_num):
                query_begin = j * query_size
                query_end = min((j + 1) * query_size, len(batch_package_list))
                if query_begin >= query_end:
                    continue

                # send request
                query_package_list = batch_package_list[query_begin:query_end]
                is_valid, token, dsp_name = update_dsp_token(token, retry_num)
                if is_valid:
                    res = upload_apk_data(token, dsp_name, query_package_list)
                    output_f.write("\t".join([",".join(query_package_list), res]) + "\n")
            time.sleep(1)

        output_f.close()
    elif func == "parse":
        logging.basicConfig(filename='../logs/parse.log', level=logging.DEBUG, format=LOG_FORMAT)
        response_file = sys.argv[2]
        app_status_file = sys.argv[3]

        input_f = open(response_file, "r")
        output_f = open(app_status_file, "w")

        for line in input_f.readlines():
            try:
                data = line.strip().split("\t")
                apk_name_list = data[0].split(",")
                response_json = json.loads(data[1])
                code = response_json["code"]
    
                if code != 0:
                    for apk_name in apk_name_list:
                        output_f.write("\t".join([apk_name, str(status_code["unkown"])]) + "\n")
                else:
                    apk_success_set = set(response_json["result"])
                    for apk_name in apk_name_list:
                        if apk_name in apk_success_set:
                            output_f.write("\t".join([apk_name, str(status_code["success"])]) + "\n")
                        else:
                            output_f.write("\t".join([apk_name, str(status_code["fail"])]) + "\n")
            except Exception as e:
                logging.error(e)

        input_f.close()
        output_f.close()


if __name__ == "__main__":
    main()
