#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import argparse  # Import argparse to handle command-line arguments

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
STOPS_ARRAY = os.getenv('STOPS_ARRAY')
ROTATE_SCREEN = os.getenv('ROTATE_SCREEN')

import requests
import json
import time

def pthread_irq() :
  print("pthread irq running")
  while flag_t == 1 :
    if(tp.digital_read(tp.INT) == 0) :
      ICNT_Dev.Touch = 1
    else :
      ICNT_Dev.Touch = 0
    time.sleep(0.01)
  print("thread irq: exit")

def Draw_Time(image, x, y, font1, font2):
  Time = time.strftime("%H : %M", time.localtime())
  Date = time.strftime("%Y - %m - %d", time.localtime())
  imagefill=0
  if image.mode!="1":
    imagefill = (255, 255, 255, 255)
  image.text((x, y), Time, font = font1, fill = imagefill)
  image.text((x-9, y+35), Date, font = font2, fill = imagefill)

def departure_to_minutes(departure_time):
    # Parse the departure time string to a datetime object
    departure_datetime = datetime.strptime(departure_time, "%Y-%m-%dT%H:%M:%S%z")

    # Get the current time
    current_datetime = datetime.now(departure_datetime.tzinfo)

    # Calculate the time difference in minutes
    time_difference = (departure_datetime - current_datetime).total_seconds() / 60

    # Round the time difference to the nearest minute
    rounded_time_difference = round(time_difference)

    # Return the rounded time difference if greater than 0, otherwise return the character representing the tram
    if rounded_time_difference > 0:
        return rounded_time_difference
    else:
        return 0
        # return chr(30)  # Character representing the tram picture

def remove_zurich(input_string):
    if "Zürich" in input_string:
        # Find the index of "Zürich" in the string
        zurich_index = input_string.find("Zürich")

        # Remove "Zürich" and any following comma
        result = input_string[:zurich_index].strip(",") + input_string[zurich_index + 6:].lstrip(",")

        return result
    else:
        return input_string

def get_departure_time(connection):
    prognosis = connection["stop"]["prognosis"]["departure"]
    if prognosis is not None:
        return prognosis
    else:
        return connection["stop"]["departure"]

font = ImageFont.load(os.path.join(fontdir, "vbz-font.pil"))
font_weather = ImageFont.truetype(os.path.join(fontdir,"Roboto-Bold.ttf"), 14)
font_weather2 = ImageFont.truetype(os.path.join(fontdir,"Roboto-Bold.ttf"), 11)
font_time = ImageFont.truetype(os.path.join(fontdir,"Roboto-Bold.ttf"), 28)

latitude = "47.3753608"
longitude = "8.530197"
stops = STOPS_ARRAY.split(",")
WEATHER_URL = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={WEATHER_API_KEY}"

def get_weather():
    response_weather = requests.get(WEATHER_URL)
    response_weather.raise_for_status()  # Raise an exception for non-200 status codes
    data_weather = json.loads(response_weather.text)
    temperature = float(data_weather["main"]["temp"]) - 273.15
    temperature_min = float(data_weather["main"]["temp_min"]) - 273.15
    temperature_max = float(data_weather["main"]["temp_max"]) - 273.15
    temperature = int(temperature)
    temperature_min = int(temperature_min)
    temperature_max = int(temperature_max)
    description_weather = data_weather["weather"][0]["description"]
    logging.info(f"Temperature: {str(temperature)}")
    logging.info(f"Weather description: {description_weather}")
    return temperature, description_weather, temperature_min, temperature_max

logging.basicConfig(level=logging.INFO)  # Configure logging level

def fetch_and_display_connections(epd, draw, counter, weather_counter, temperature, weather_description, temperature_max, temperature_min):
  should_sleep = False
  amount_to_sleep = 0
  try:
    logging.info("Fetching connections from API...")
    connections = ""
    stop_index = 0

    for stop in stops:
      URL = f"http://transport.opendata.ch/v1/stationboard?station={stop}&limit=15"
      response = requests.get(URL)
      response.raise_for_status()  # Raise an exception for non-200 status codes
      data = json.loads(response.text)
      if stop_index == 0:
        connections = data["stationboard"]
      else:
        connections.extend(data["stationboard"])
      stop_index += 1

    connections_sorted = sorted(connections, key=lambda x: get_departure_time(x))  

    x = 10
    y = 12

    amount_displayed = 0

    text_image = Image.new('1', (image.height, image.width), 255)  # White background
    text_draw = ImageDraw.Draw(text_image)
    
    # Iterate over connections to draw text on the blank image
    for connection in connections_sorted:
        number = connection["number"]
        departure = connection["stop"]["prognosis"]["departure"]
        destination = connection["to"]
        destination = remove_zurich(destination)

        if number == None:
            number = "N"

        if departure != None:
            minutes_to_departure = departure_to_minutes(departure)
        else:
            minutes_to_departure = departure_to_minutes(connection["stop"]["departure"])

        # Draw text on the blank image
        if int(minutes_to_departure) > 3 and amount_displayed < 5:
            minutes_to_departure_string = str(minutes_to_departure) + "'"
            text_draw.text((x, y), f"{number}", font=font, fill=0)
            if "N" in number: 
              text_draw.text(((x + 24), y), f"{destination}", font=font, fill=0) # Black text
            else: 
              text_draw.text(((x + 15), y), f"{destination}", font=font, fill=0) # Black text
            text_draw.text((170, y), f"{minutes_to_departure_string}", font=font, fill=0)  # Black text
            y = y + 24
            amount_displayed += 1

        if int(minutes_to_departure) > 40 and amount_displayed < 5:
            should_sleep = True
            amount_to_sleep = (int(minutes_to_departure) - 1) * 60

    current_hour = datetime.now().strftime("%H") 
    current_minutes = datetime.now().strftime("%M")

    text_draw.text((190, 7), f"{current_hour}:{str(current_minutes)}", font=font_time, fill=0)

    if counter == 5 or weather_counter == 0:
        temperature, weather_description, temperature_min, temperature_max = get_weather() 
        weather_counter += 1
        logging.info(f"Weather counter: {weather_counter}")

    text_draw.text((190, 57), f"{int(temperature)}°C" , font=font_weather, fill=0)
    text_draw.text((190, 81), f"{weather_description}" , font=font_weather, fill=0)
    text_draw.text((190, 107), f"H: {temperature_max}°C L: {int(temperature_min)}°C", font=font_weather2, fill=0)

    if ROTATE_SCREEN:
        rotated_text_image = text_image.rotate(270, expand=True)  # Rotate by 180 degrees
    else:
        rotated_text_image = text_image.rotate(90, expand=True)  # Original 90-degree rotation

    image.paste(rotated_text_image)

    if counter > 0:
        epd.display_Partial_Wait(epd.getbuffer(image))
        logging.info("Displaying partial")
    else:
        epd.display_Base(epd.getbuffer(image))
        logging.info("Displaying Base")# Update screen

    logging.info("All lines displayed simultaneously")
     
  except requests.exceptions.RequestException as err:
    logging.error("Error fetching data:", err)

  logging.info("Waiting for next update...")
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
