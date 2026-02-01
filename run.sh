if [ -f "current.txt" ]; then
    echo "current.txt found!"
    exit 1
fi

docker run --rm -v$(pwd):/tgbot -dt tgbot > current.txt