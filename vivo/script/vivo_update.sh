#!/bin/bash

event_day=`date +"%Y%m%d"`
event_hour=`date +"%H"`
remove_day=`date -d "${event_day} 3 days ago" +"%Y%m%d"`

python="./python"
script="vivo_processor.py"
apk_name_file="../../apk_data/data/apk_name.txt"
request_log_file="../logs/request.log"
parse_log_file="../logs/parse.log"
tmp_data_dir="../data/tmp"
response_file="${tmp_data_dir}/response.txt"
upload_file="${tmp_data_dir}/apk_name.txt"
app_status_file="../data/app_status.txt"
app_success_file="${tmp_data_dir}/app_success.txt"
app_fail_file="${tmp_data_dir}/app_fail.txt"
app_unkown_file="${tmp_data_dir}/app_unkown.txt"
app_status_res="../data/app_status.txt"
status_backup_file="../data/backup/app_status.txt.${event_day}${event_hour}"
upload_backup_file="../data/backup/apk_name.txt.${event_day}${event_hour}"


# initialize
if [[ -a ${request_log_file} ]]
then
    rm ${request_log_file}
fi

if [[ -a ${parse_log_file} ]]
then
    rm ${parse_log_file}
fi

if [[ -a ${tmp_data_dir} ]]
then
    rm -rf ${tmp_data_dir}
fi
mkdir ${tmp_data_dir}

cp ${apk_name_file} ${upload_file}
cp ${apk_name_file} ${upload_backup_file}

retry_num=3
while [[ ${retry_num} -gt 0 ]]
do
    retry_num=`expr ${retry_num} - 1`
    # request
    ${python} ${script} download ${upload_file} ${response_file}.tmp
    mv ${response_file}.tmp ${response_file}
    
    # parse
    ${python} ${script} parse ${response_file} ${app_status_file}.tmp
    mv ${app_status_file}.tmp ${app_status_file}
    
    # select
    awk '{if($2=="1"){print;}}' ${app_status_file} >> ${app_success_file}
    awk '{if($2=="3"){print;}}' ${app_status_file} >> ${app_fail_file}
    awk '{if($2=="2"){print;}}' ${app_status_file} > ${app_unkown_file}
    awk '{print $1}' ${app_unkown_file} > ${upload_file}

    # all response
    if [[ `ls -l ${upload_file} | awk '{print $5}'` -eq 0 ]]
    then
        break
    fi

    sleep 5
done

# post
sort ${app_success_file} ${app_fail_file} ${app_unkown_file} | uniq > ${app_status_res}.tmp
mv ${app_status_res}.tmp ${app_status_res}
cp ${app_status_res} ${status_backup_file}

rm -rf ${tmp_data_dir}

for file in `ls ../data/backup | grep "${remove_day}"`
do
    rm ../data/backup/${file}
done

for file in `ls ../logs | grep "${remove_day}" | grep "update"`
do
    rm ../logs/${file}
done

# curl
curl="./curl"
ftp_host="xxx.xx.xx"
ftp_path="xxx/vivo_app_info.txt"
ftp_backup_path="xxx/vivo_app_info.txt.${event_day}${event_hour}"
ftp_pass="******"

${curl} -u ${ftp_pass} -T ${app_status_res} ${ftp_host}:${ftp_path}
${curl} -u ${ftp_pass} -T ${app_status_res} ${ftp_host}:${ftp_backup_path}
