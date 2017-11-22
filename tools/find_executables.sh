OUTPUT=`find . \( -name .tox -o -name .git \) -prune -o -type f -perm /a=x -print \
        | grep -v -F -f ./tools/executable_files.txt`
if [ -n "$OUTPUT" ]; then
    echo "Unexpected executable files are found:"
    for f in $OUTPUT; do
        echo $f
    done
    echo
    echo "If you really need to add an executable file, add it to tools/executable_files.txt"
    exit 1
fi
