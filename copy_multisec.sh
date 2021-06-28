#!/bin/zsh

if [[ "$#" -ne 3 ]]; then
    echo "The number of parameters was not correct: $#"
    echo "Usage: ./copy_to_post.sh \"[ tower | post ]\" ID HOSTNAME"
fi

ACCESS_HOST="${2}@${3}"

if [[ "$1" == "tower" ]]; then
    scp -r ./MultiView-Tower ${ACCESS_HOST}:~/

elif [[ "$1" == "post" ]]; then
    scp -r  ./MultiView-Post ${ACCESS_HOST}:~/

elif [[ "$1" == "cube" ]]; then
    scp -r ./MultiView-Cube ${ACCESS_HOST}:~/
    
else;
    echo "The module type \"$1\" does not supported"
    echo "Usage: ./copy_to_post.sh \"[ tower | post ]\" ID HOSTNAME"
fi