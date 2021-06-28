#!/bin/zsh

if [ "$#" -ne 1 ]; then
    echo "The number of paramters was not correct: $#"
    echo "Usage: zsh ./copy_to_vcenter.sh [ sec | col | cache | vis ]"
    exit 1
fi

if [[ "$1" == "sec" ]]; then
    TARGET="Security-Analysis/simple_active_flow_bps_scoring.py"
    scp ./${TARGET} koneadmin@k1-v-center:~/MultiView-Tower/${TARGET}

elif [[ "$1" == "col" ]]; then
    TARGET="Visibility-Collection-Validation/Collectors"
    scp -r ./${TARGET}/Custom-Collector-Python koneadmin@k1-v-center:~/MultiView-Tower/${TARGET}/

elif [[ "$1" == "cache" ]]; then
    TARGET="Visibility-Storage-Staging"
    scp -r ./${TARGET}/Flow-Cache-Management koneadmin@k1-v-center:~/MultiView-Tower/${TARGET}

elif [[ "$1" == "vis" ]]; then
    PREFIX="Visibility-Visualization/pvcT-Visualization"
    scp -r ./${PREFIX}/public koneadmin@k1-v-center:~/MultiView-Tower/${PREFIX}
    scp -r ./${PREFIX}/routes koneadmin@k1-v-center:~/MultiView-Tower/${PREFIX}
    scp ./${PREFIX}/MultiView-DataAPI.js koneadmin@k1-v-center:~/MultiView-Tower/${PREFIX}/

else;
    echo "The paramter \"$1\" does not supported"
    echo "Usage: zsh ./copy_to_vcenter.sh [ sec | col | cache | vis ]"
    exit 1
fi