#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import argparse 

parser = argparse.ArgumentParser(description="Display information with optional rotation")
parser.add_argument('--rotate', action='store_true', help="Rotate text by 180 degrees")
args = parser.parse_args()

picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic/2in9')
fontdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

print(fontdir)

from TP_lib import icnt86
from TP_lib import epd2in9_V2
from TP_lib import weather_2in9_V2

import time
import logging
from PIL import Image, ImageDraw, ImageFont
import traceback
import threading
from datetime import datetime
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)
flag_t = 1
refresh_counter = 0
counter = 0
weather_counter = 0
temperature = 0
weather_description = ""
temperature_max = 0
temperature_min = 0

load_dotenv()
WEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')

import requests
import json
import time

def fetch_and_display_connections(epd, draw, counter, weather_counter, temperature, weather_description, temperature_max, temperature_min):
    should_sleep = False
    amount_to_sleep = 0
    try:
        logging.info("Fetching connections from API...")
        response = requests.get(URL)
        response.raise_for_status()  # Raise an exception for non-200 status codes
        data = json.loads(response.text)

        connections = data["stationboard"]
        connections_sorted = sorted(connections, key=lambda x: get_departure_time(x))  

        x = 10
        y = 12
        amount_displayed = 0

        # Create an empty image for text drawing
        text_image = Image.new('1', (image.height, image.width), 255)  # White background
        text_draw = ImageDraw.Draw(text_image)

        for connection in connections_sorted:
            # Drawing logic remains the same...
            # Draw text on the blank image
            if int(minutes_to_departure) > 3 and amount_displayed < 5:
                # Draw the text in the appropriate location
                text_draw.text((x, y), f"{number}", font=font, fill=0)
                text_draw.text(((x + 15), y), f"{destination}", font=font, fill=0)
                text_draw.text((200, y), f"{minutes_to_departure_string}", font=font, fill=0)
                y = y + 24
                amount_displayed += 1

            if int(minutes_to_departure) > 40 and amount_displayed < 5:
                should_sleep = True
                amount_to_sleep = (int(minutes_to_departure) - 1) * 60

        current_hour = datetime.now().strftime("%H") 
        current_minutes = datetime.now().strftime("%M")
        text_draw.text((220, 12), f"{current_hour}:{str(current_minutes)}", font=font_time, fill=0)

        # Draw weather information
        if counter == 5 or weather_counter == 0:
            temperature, weather_description, temperature_min, temperature_max = get_weather() 
            weather_counter += 1

        text_draw.text((220, 55), f"{int(temperature)}°C" , font=font_weather, fill=0)
        text_draw.text((220, 82), f"{weather_description}" , font=font_weather, fill=0)
        text_draw.text((220, 107), f"H: {temperature_max}°C L: {int(temperature_min)}°C", font=font_weather2, fill=0)

        # Rotate the text image by 180 degrees if the --rotate flag is set
        if args.rotate:
            rotated_text_image = text_image.rotate(180, expand=True)  # Rotate by 180 degrees
        else:
            rotated_text_image = text_image.rotate(90, expand=True)  # Original 90-degree rotation

        image.paste(rotated_text_image)

        # Display on screen
        if counter > 0:
            epd.display_Partial_Wait(epd.getbuffer(image))
        else:
            epd.display_Base(epd.getbuffer(image))

    except requests.exceptions.RequestException as err:
        logging.error("Error fetching data:", err)

    return should_sleep, amount_to_sleep, weather_counter, temperature, weather_description, temperature_max, temperature_min

epd = epd2in9_V2.EPD_2IN9_V2()
tp = icnt86.INCT86()

ICNT_Dev = icnt86.ICNT_Development()
ICNT_Old = icnt86.ICNT_Development()

logging.info("init and Clear")
epd.init()
tp.ICNT_Init()

t1 = threading.Thread(target = pthread_irq)
t1.setDaemon(True)
t1.start()

image = Image.new('1', (epd.width, epd.height), 255)   # 255: clear the frame
draw = ImageDraw.Draw(image)

while True:
  try:
    if refresh_counter ==  6:
        counter = 0
        refresh_counter = 0
        should_sleep, time_to_sleep, weather_counter, temperature, weather_description, temperature_max, temperature_min = fetch_and_display_connections(epd, draw, counter, weather_counter, temperature, weather_description, temperature_max, temperature_min)
        if should_sleep:
            time.sleep(time_to_sleep + 25) 
        else:
            time.sleep(25)

    else:
        should_sleep, time_to_sleep, weather_counter, temperature, weather_description, temperature_max, temperature_min  = fetch_and_display_connections(epd, draw, counter, weather_counter, temperature, weather_description, temperature_max, temperature_min)
        if should_sleep:
            time.sleep(time_to_sleep + 30) 
        else:
            time.sleep(30)

    counter += 1
    refresh_counter += 1

  except KeyboardInterrupt:
    logging.info("Stopping program...")
    epd.sleep()  # Put display to sleep
    break
