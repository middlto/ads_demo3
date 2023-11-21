#!/bin/bash

if [[ $# -eq 2 ]]
then
    event_day=$1
    event_hour=$2
else
    event_day=`date +"%Y%m%d"`
    event_hour=`date +"%H"`
fi
remove_day=`date -d "${event_day} 5 days ago" +"%Y%m%d"`

src_host="xxxxx.xx.xx"
check_src_path="xxx/apk_table.txt"
check_local_path="../data/apk_table.txt"
apk_name_info="../data/apk_name.txt"
apk_info_path="../data/apk_info"


# apk_info for check
scp ${src_host}:${check_src_path} ${check_local_path}
awk '{print $1}' ${check_local_path} | sort | uniq > ${apk_name_info}


# clear history
for file in `ls ../logs | grep "${remove_day}"`
do
    rm ../logs/${file}
done
