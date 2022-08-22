# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ArticleItem(scrapy.Item):
    # define the fields for your item here like:
    token = scrapy.Field(serializer=str)
    database = scrapy.Field(serializer=str)
    title = scrapy.Field(serializer=str)
    url = scrapy.Field(serializer=str)
    tags = scrapy.Field(serializer=list)
    content = scrapy.Field(serializer=str)
    id = scrapy.Field(serializer=str)  # cubox id
