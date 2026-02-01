if [ ! -f "current.txt" ]; then
    echo "current.txt not found!"
    exit 1
fi

docker kill "$(cat current.txt)"
rm current.txt