# -*- coding:UTF-8 -*-

import sys
import json
import time
import base64
import hashlib
import logging
import warnings
import requests


warnings.filterwarnings('ignore')
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


channel = 1110
api_key = "*************"
online_http_address = "xxx.xx.xxx/xx"
batch_size = 100

status_code = {
    "success": 1,
    "unkown": 2,
    "fail": 3,
}


def generate_token(channel, api_key):
    time_stamp = int(time.time())

    sign_text = str(channel) + str(api_key) + str(time_stamp)
    sign = hashlib.sha1(sign_text).hexdigest()
    logging.debug("sign_text: " + sign_text)
    logging.debug("sign: " + sign)

    token_text = ",".join(map(str, [channel, time_stamp, sign]))
    token = base64.b64encode(token_text)
    logging.debug("token_text: " + token_text)
    logging.debug("token: " + token)

    return token 


def upload_apk_data(token, packages):
    upload_url = online_http_address
    data_json = json.dumps({
        "pkgs": packages,
        "token": token
    })
    logging.debug(upload_url)
    logging.debug(data_json)

    res = ""
    try:
        response = requests.post(upload_url, data=data_json)
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

        token = generate_token(channel, api_key)
        apk_name_num = len(apk_name_list)
        batch_num = apk_name_num / batch_size + 1
        for i in range(batch_num):
            batch_begin = i * batch_size
            batch_end = min((i + 1) * batch_size, apk_name_num)
            if batch_begin >= batch_end:
                continue

            apk_name_batch_list = apk_name_list[batch_begin:batch_end]
            res = upload_apk_data(token, apk_name_batch_list)
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
                if response_json["ret"] != 0:
                    for apk_name in apk_name_list:
                        output_f.write("\t".join([apk_name, str(status_code["unkown"])]) + "\n")
                else:
                    apk_res_map = response_json["data"]
                    for apk_name in apk_name_list:
                        if apk_name not in apk_res_map:
                            output_f.write("\t".join([apk_name, str(status_code["fail"])]) + "\n")
                        elif apk_res_map[apk_name]["status"] != 1:
                            output_f.write("\t".join([apk_name, str(status_code["fail"])]) + "\n")
                        else:
                            output_f.write("\t".join([apk_name, str(status_code["success"])]) + "\n")
            except Exception as e:
                logging.error(e)

        input_f.close()
        output_f.close()



if __name__ == "__main__":
    main()
