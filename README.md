How to run:
 1) Install dependencies `pip install python-telegram-bot`
 2) Create "SECRET.txt" file with the telegram bot token in the root of the repository
 3) Launch bot: `python3 main.py`. Bot stops on CTRL+C. Database in birthdays.db file
 4) Launch local cli: `python3 birthday.py`. Commands are the same but without the "/bday" prefix.

How to run using docker:
 1) Build the container: `./build.sh`
 2) Run the container: `./run.sh`
 3) Stop the container: `./stop.sh`
