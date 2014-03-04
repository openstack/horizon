#!/bin/bash
#
# Enforce the requirement that dependencies are listed in the input
# files in alphabetical order.

# FIXME(dhellmann): This doesn't deal with URL requirements very
# well. We should probably sort those on the egg-name, rather than the
# full line.

function check_file() {
    typeset f=$1

    # We don't care about comment lines.
    grep -v '^#' $f > ${f}.unsorted
    sort -i -f ${f}.unsorted > ${f}.sorted
    diff -c ${f}.unsorted ${f}.sorted
    rc=$?
    rm -f ${f}.sorted ${f}.unsorted
    return $rc
}

exit_code=0
for filename in $@
do
    check_file $filename
    if [ $? -ne 0 ]
    then
        echo "Please list requirements in $filename in alphabetical order" 1>&2
        exit_code=1
    fi
done
exit $exit_code
