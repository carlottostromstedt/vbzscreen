# vbzscreen

Python-Script for fetching API data from Opentransportdata and displaying it on an E-Paper screen on a Raspberry Pi.

## Setup

1. clone the repository
2. follow the instructions for setting up the screen from here: https://www.waveshare.com/wiki/2.9inch_Touch_e-Paper_HAT_Manual#Raspberry_Pi
3. install dotenv with `sudo apt install python3 dotenv`
4. add a `.env` file to `scripts` and add the key `OPENWEATHER_API_KEY`
5. run the service with python3 display_connections.py
