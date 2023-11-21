# -*- coding:UTF-8 -*-

import sys
import json
import time
import logging
import hashlib
import warnings
import requests
import collections

warnings.filterwarnings('ignore')
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

content_type = "application/json"
online_http_address = "xxx.xx.xx"
token = "**********"
dsp_id = 111000
batch_size = 10


def generate_s(token, **params):
    params_sorted = sorted(params.items())
    params_ordered_dict = collections.OrderedDict()
    for key, value in params_sorted:
        params_ordered_dict[key] = value
    params_json = json.dumps(params_ordered_dict).replace(" ", "")
    s_str = params_json + str(token)
    s_md5 = hashlib.md5(s_str).hexdigest()
    res = s_md5.upper()
    return res


def req_apk_data(token, dsp_id, package):
    interface = "xxx"
    req_url = online_http_address + "/" + interface
    header_map = {
        "Content-Type": content_type
    }
    s = generate_s(token, dspId=dsp_id, apkPackage=package)
    data_json = json.dumps({
        "s": s,
        "dspId": dsp_id,
        "apkPackage": package
    })
    res = ""
    try:
        logging.debug(req_url)
        logging.debug(data_json)
        logging.debug(header_map)
        response = requests.post(req_url, data=data_json, headers=header_map)
        logging.debug(response.text)
        res = response.text.encode("utf-8")
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


def check_apk_data(token, dsp_id, apk_info):
    interface = "/xxxx"
    req_url = online_http_address + "/" + interface
    header_map = {
        "Content-Type": content_type
    }
    s = generate_s(token, dspId=dsp_id, apkInfos=apk_info)
    data_json = json.dumps({
        "s": s,
        "dspId": dsp_id,
        "apkInfos": apk_info
    })
    res = ""
    try:
        logging.debug(req_url)
        logging.debug(data_json)
        logging.debug(header_map)
        response = requests.post(req_url, data=data_json, headers=header_map)
        logging.debug(response.text)
        res = response.text.encode("utf-8")
    except Exception as e:
        logging.error(e)
    return res


def main():
    func = sys.argv[1]
    if func == "download":
        logging.basicConfig(filename='../logs/request.log', level=logging.DEBUG, format=LOG_FORMAT)

        apk_name_file = sys.argv[2]
        apk_name_set = load_apk_name(apk_name_file)
        apk_name_list = list(apk_name_set)

        output_file = sys.argv[3]
        output_f = open(output_file, "w")

        apk_name_num = len(apk_name_list)
        batch_num = apk_name_num / batch_size + 1
        for i in range(batch_num):
            batch_begin = i * batch_size
            batch_end = min((i + 1) * batch_size, apk_name_num)
            if batch_begin >= batch_end:
                continue

            apk_name_batch_list = apk_name_list[batch_begin:batch_end]
            for apk_name in apk_name_batch_list:
                logging.debug("apk_name: " + apk_name)
                res = req_apk_data(token, dsp_id, apk_name)
                output_f.write("\t".join([apk_name, res]) + "\n")
            time.sleep(1)
        output_f.close()
    elif func == "parse":
        logging.basicConfig(filename='../logs/parse.log', level=logging.DEBUG, format=LOG_FORMAT)

        response_file = sys.argv[2]
        apk_status_file = sys.argv[3]

        input_f = open(response_file, "r")
        output_f = open(apk_status_file, "w")

        for line in input_f.readlines():
            try:
                data = line.strip().split("\t")
                response_json = json.loads(data[1])
                if response_json["code"] == 0:
                    output_f.write("\t".join([data[0], str(response_json["app"]["appStatus"])]) + "\n")
            except Exception as e:
                logging.error(e)

        input_f.close()
        output_f.close()
    elif func == "check":
        logging.basicConfig(filename='../logs/check.log', level=logging.DEBUG, format=LOG_FORMAT)

        apk_info_file = sys.argv[2]
        apk_check_res_file = sys.argv[3]
        input_f = open(apk_info_file, "r")
        output_f = open(apk_check_res_file, "w")

        for line in input_f.readlines():
            try:
                apk_name, doc_id, apk_md5, apk_version = line.strip().split("\t")
                apk_info = [{
                    "apkPackage": apk_name,
                    "channel": doc_id,
                    "md5": apk_md5
                }]
                res = check_apk_data(token, dsp_id, apk_info)
                response_json = json.loads(res)
                if response_json["code"] == 0:
                    apk_status = response_json["details"][0]["status"]
                    output_f.write("\t".join(map(str, [apk_name, doc_id, apk_md5, apk_status])) + "\n")

            except Exception as e:
                logging.error(e)

        input_f.close()
        output_f.close()


if __name__ == "__main__":
    main()
