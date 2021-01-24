#!/usr/bin/env bash

if [ $# -ne 3 ]; then
    echo 'usage: retry <num retries> <wait retry secs> "<command>"'
    exit 1
fi

retries=$1
wait_retry=$2
command=$3

for i in `seq 1 $retries`; do
    echo "$command"
    $command
    ret_value=$?
    [ $ret_value -eq 0 ] && break
    echo "> failed with $ret_value, waiting to retry..."
    sleep $wait_retry
done

exit $ret_value
