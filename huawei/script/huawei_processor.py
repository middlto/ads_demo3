# -*- coding:UTF-8 -*-

import sys
import hmac
import json
import time
import base64
import hashlib
import logging
import warnings
import datetime
import requests

warnings.filterwarnings('ignore')
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

sign_type_map = {
    "hmac-sha256": "1",
}

status_code = {
    "success": 1,
    "unkown": 2,
    "fail": 3,
}

x_app_id = "xxx"
x_sign_type = "xxx"
content_type = "application/json; charset=utf-8"
accept = "application/json"
online_http_address = "https://xx.xx.xx/xx"
secret_key = "*************"
batch_size = 10

def upload_apk_data(packages):
    base_path = "/ppsmanage/v2"
    resource_path = "/promoteApp"
    time_stamp = str(int(time.time() * 1000))
    secret_data = base_path + resource_path + time_stamp
    x_sign = hmac.new(secret_key, secret_data, digestmod=hashlib.sha256).hexdigest()
    logging.debug("base_path: " + base_path)
    logging.debug("resource_path: " + resource_path)
    logging.debug("time_stamp: " + time_stamp)
    logging.debug("secret_data: " + secret_data)
    logging.debug("x_sign: " + x_sign)

    upload_url = online_http_address + base_path + resource_path
    header_map = {
        "Content-Type": content_type,
        "Accept": accept,
        "x-appId": x_app_id,
        "x-signType": sign_type_map[x_sign_type],
        "x-sign": x_sign,
        "timestamp": time_stamp,
    }
    data_map = []
    for apk_name in packages:
        promoteApps = {"pkgName": apk_name}
        data_map.append(promoteApps)
    data_json = json.dumps({
        "id": time_stamp,
        "promoteApps": data_map,
    })
    logging.debug(upload_url)
    logging.debug(data_json)
    logging.debug(header_map)

    res = ""
    try:
        response = requests.post(upload_url, data=data_json, headers=header_map)
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
            res = upload_apk_data(apk_name_batch_list)
            output_f.write("\t".join([",".join(apk_name_batch_list), res]) + "\n")
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
                apk_name_list = data[0].split(",")
                response_json = json.loads(data[1])

                if response_json["retCode"] == 500 or response_json["retCode"] == 501:
                    for apk_name in apk_name_list:
                        output_f.write("\t".join([apk_name, str(status_code["unkown"])]) + "\n")
                elif response_json["retCode"] == 204:
                    for apk_name in apk_name_list:
                        output_f.write("\t".join([apk_name, str(status_code["fail"])]) + "\n")
                elif response_json["retCode"] == 200:
                    for apk_name in apk_name_list:
                        output_f.write("\t".join([apk_name, str(status_code["success"])]) + "\n")
                elif response_json["retCode"] == 206:
                    apk_res_map = set([])
                    for app_detail in response_json["appDetails"]:
                        apk_res_map.add(app_detail["pkgName"])
                    for apk_name in apk_name_list:
                        if apk_name in apk_res_map:
                            output_f.write("\t".join([apk_name, str(status_code["success"])]) + "\n")
                        else:
                            output_f.write("\t".join([apk_name, str(status_code["fail"])]) + "\n")
            except Exception as e:
                logging.error(e)

        input_f.close()
        output_f.close()


if __name__ == "__main__":
    main()
