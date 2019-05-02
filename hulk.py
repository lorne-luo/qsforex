import time

import boto3
import json
from decimal import Decimal
from fxcmpy import fxcmpy
from random import random

import settings
from mt4.constants import get_mt4_symbol, pip

awsRegion = "us-east-2"  # The AWS region where your Kinesis Analytics application is configured.
accessKeyId = settings.AWS_ACCESS_ID  # Your AWS Access Key ID
secretAccessKey = settings.AWS_ACCESS_KEY
inputStream = "Hulk"  # The name of the stream being used as input into the Kinesis Analytics hotspots application

# Variables that control properties of the generated data.
xRange = [0, 10]  # The range of values taken by the x-coordinate
yRange = [0, 10]  # The range of values taken by the y-coordinate
hotspotSideLength = 1  # The side length of the hotspot
hotspotWeight = 0.2  # The fraction ofpoints that are draw from the hotspots

kinesis = boto3.client('kinesis')
records = []


def generate_point_in_rectangle(x_min, width, y_min, height):
    """Generate points uniformly in the given rectangle."""
    return {
        'x': x_min + random() * width,
        'y': y_min + random() * height
    }


class RecordGenerator(object):
    """A class used to generate points used as input to the hotspot detection algorithm. With probability hotspotWeight,
    a point is drawn from a hotspot, otherwise it is drawn from the base distribution. The location of the hotspot
    changes after every 1000 points generated."""

    def __init__(self):
        self.x_min = xRange[0]
        self.width = xRange[1] - xRange[0]
        self.y_min = yRange[0]
        self.height = yRange[1] - yRange[0]
        self.points_generated = 0
        self.hotspot_x_min = None
        self.hotspot_y_min = None

    def get_record(self):
        if self.points_generated % 1000 == 0:
            self.update_hotspot()

        if random() < hotspotWeight:
            record = generate_point_in_rectangle(self.hotspot_x_min, hotspotSideLength, self.hotspot_y_min,
                                                 hotspotSideLength)
            record['is_hot'] = 'Y'
        else:
            record = generate_point_in_rectangle(self.x_min, self.width, self.y_min, self.height)
            record['is_hot'] = 'N'

        self.points_generated += 1
        data = json.dumps(record)
        return {'Data': bytes(data, 'utf-8'), 'PartitionKey': 'partition_key'}

    def get_records(self, n):
        return [self.get_record() for _ in range(n)]

    def update_hotspot(self):
        self.hotspot_x_min = self.x_min + random() * (self.width - hotspotSideLength)
        self.hotspot_y_min = self.y_min + random() * (self.height - hotspotSideLength)


def tick_to_kinesis(tick, dataframe):
    instrument = get_mt4_symbol(tick['Symbol'])
    bid = str(Decimal(str(tick['Rates'][0])).quantize(pip(instrument)/10))
    ask = str(Decimal(str(tick['Rates'][1])).quantize(pip(instrument)/10))
    data = {
        'timestamp': int(tick['Updated']) / 1000.0,
        'bid': bid,
        'ask': ask
    }
    data = json.dumps(data)
    records.append({'Data': bytes(data, 'utf-8'), 'PartitionKey': instrument})

    if len(records) == 10:
        print(records)
        kinesis.put_records(StreamName=inputStream, Records=records)
        records.clear()


def main():
    pairs = ['EUR/USD']

    fxcm = fxcmpy(access_token=settings.FXCM_ACCESS_TOKEN, server='demo')
    for pair in pairs:
        fxcm.subscribe_market_data(pair, (tick_to_kinesis,))

    while True:
        time.sleep(5)


if __name__ == "__main__":
    main()
