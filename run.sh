# !/bin/bash
echo "Run booking script periodically"
while true
do
  date +"%Y-%m-%d %H:%M:%S"
  echo start to run script
  /usr/bin/python3 /home/marklau/Desktop/gym-booking/force.py
  echo script finished
  date +"%Y-%m-%d %H:%M:%S"
  sleep 10h
done