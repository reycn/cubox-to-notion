# use `scrapy crawl cubox_to_notion -L DEBUG` instead
# this script is not functional yet
from configparser import ConfigParser
import logging
from os import path, system
from time import sleep

from datetime import datetime


def config(section, key, cofig_path='/config.ini'):
    cofig_path = path.abspath(path.dirname(__file__)) + cofig_path
    value = ''
    # logging.critical(cofig_path)
    try:
        cfg = ConfigParser()
        cfg.read(cofig_path)
        value = cfg[section][key]
        # logging.critical(cfg[section][key])
        return value
    except:
        value = f"[{section}] value not found: {value}"
        logging.error(value)
        return value


def run(cmd="scrapy crawl cubox_to_notion -L ", log="ERROR") -> None:
    system(cmd + log.upper())


if __name__ == "__main__":
    # print(config("general", "period"))
    epic = 0
    sleep_period = int(config("general", "period"))
    while True:
        epic += 1
        current = datetime.now().strftime('%H:%M:%S')
        logging.critical(f"[Cron] starting task No.{epic}, at {current}")
        run(log="info")
        sleep(sleep_period)
