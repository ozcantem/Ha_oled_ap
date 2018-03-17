import os
import yaml
import logging
from urllib.request import urlopen
import json
import asyncio
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import spidev as SPI
import SSD1306
import time
import signal

# log file settings
basedir = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger("ha-oled-ap")
logger.setLevel(logging.INFO)

# create the logging file handler
fh = logging.FileHandler("ha-oled-ap.log")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

# create the custom font
font_dir = os.path.dirname(os.path.realpath(__file__)) +"/conthrax-sb.ttf"
font1 = ImageFont.truetype(font_dir, 10)
font2 = ImageFont.truetype(font_dir, 20)

# Raspberry pi pin settings
RST = 24
DC = 23
bus = 0
device = 0

# 128x64 display with hardware SPI:
disp = SSD1306.SSD1306(RST, DC, SPI.SpiDev(bus, device))

# Initialize library.
disp.begin()

# Clear display.
disp.clear()
disp.display()

ha_api_url = ''
ha_attributes = {}
ha_attributes_entity = []
ha_attributes_state = []
# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)
# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=0)

# First define some constants to allow easy resizing of shapes.
padding = 1
top = padding
x = padding


def retrieve_information(seconds):
    get_states_from_ha()
    global ha_attributes_entity, ha_attributes_state
    ha_attributes_entity = [ha_attributes[i]['entity_id'] for i in range(ha_attributes.__len__())]
    ha_attributes_state = [ha_attributes[i]['state'] for i in range(ha_attributes.__len__())]
    loop.call_later(seconds, lambda: retrieve_information(seconds))


def stop_loop(loop):
    print('stopping loop')
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    disp.clear()
    disp.display()
    loop.stop()


def get_configuration_data():
    try:
        with open(os.path.dirname(os.path.realpath(__file__)) +"/configurations.yaml", 'r') as ymlfile:
            config = yaml.load(ymlfile)
        global  ha_api_url
        ha_api_url = config['application']['ha_api_url']

    except Exception as er:
        print (er)
        logger.error(str(er))


def get_states_from_ha():
    response = urlopen(ha_api_url)
    string = response.read().decode('utf-8')
    json_obj = json.loads(string)
    global ha_attributes
    ha_attributes = json_obj
    return ha_attributes


# Display messages in two rows
def display_information(seconds):

    for i in range(ha_attributes.__len__()):
        # Draw a black filled box to clear the image.
        draw.rectangle((0, 0, width, height), outline=0, fill=0)

        draw.text((x, top), str(ha_attributes_entity[i]), font=font1, fill=255)
        draw.text((x, top + 20), str( ha_attributes_state[i]), font=font2, fill=255)
        disp.image(image)
        disp.display()
        time.sleep(5)

    loop.call_later(seconds, lambda : display_information(seconds))


if __name__ == '__main__':
    print('Starting')
    logger.info("Starting")
    get_configuration_data()
    loop = asyncio.get_event_loop()
    loop.call_soon(lambda: retrieve_information(15))
    loop.call_later(1, lambda : display_information(5))
    loop.add_signal_handler(signal.SIGINT, stop_loop, loop)
    loop.run_forever()
    print('Exiting')
    logger.info("Exiting")
