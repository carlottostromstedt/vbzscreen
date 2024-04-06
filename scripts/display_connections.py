#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
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

logging.basicConfig(level=logging.DEBUG)
flag_t = 1
refresh_counter = 0
counter = 0

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
        return str(rounded_time_difference) + "'"
    else:
        return chr(30)  # Character representing the tram picture
def remove_zurich(input_string):
    if "Zürich" in input_string:
        # Find the index of "Zürich" in the string
        zurich_index = input_string.find("Zürich")

        # Remove "Zürich" and any following comma
        result = input_string[:zurich_index].strip(",") + input_string[zurich_index + 6:].lstrip(",")

        return result
    else:
        return input_string

font = ImageFont.load(os.path.join(fontdir, "vbz-font.pil"))

URL = "http://transport.opendata.ch/v1/stationboard?station=Stauffacher&limit=5"

logging.basicConfig(level=logging.INFO)  # Configure logging level

def fetch_and_display_connections(epd, draw, counter):
  try:
    logging.info("Fetching connections from API...")
    response = requests.get(URL)
    response.raise_for_status()  # Raise an exception for non-200 status codes
    data = json.loads(response.text)

    connections = data["stationboard"]

    x = 20
    y = 12

    text_image = Image.new('1', (image.height, image.width), 255)  # White background
    text_draw = ImageDraw.Draw(text_image)
    
    text_draw.text((1, 1), ".", fill=0)
    # Iterate over connections to draw text on the blank image
    for connection in connections:
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
        text_draw.text((x, y), f"{number} {destination}", font=font, fill=0)  # Black text
        text_draw.text((270, y), f"{minutes_to_departure}", font=font, fill=0)  # Black text
        y = y + 24

    # Rotate the text image and paste it onto the main image
    rotated_text_image = text_image.rotate(90, expand=True)  # Rotate and expand
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
        fetch_and_display_connections(epd, draw, counter)
        time.sleep(55) 

    else:
        fetch_and_display_connections(epd, draw, counter)
        time.sleep(60) 

    counter += 1
    refresh_counter += 1

  except KeyboardInterrupt:
    logging.info("Stopping program...")
    epd.sleep()  # Put display to sleep
    break
