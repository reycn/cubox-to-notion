import scrapy
import json
from os import path
from configparser import ConfigParser
from cubox_to_notion.items import ArticleItem


class QuotesSpider(scrapy.Spider):

    name = "cubox_to_notion"
    cofig_path = path.abspath(
        path.dirname(path.dirname(path.dirname(__file__)))) + '/config.ini'

    def start_requests(self):
        try:
            with open(self.cofig_path) as fp:
                cfg = ConfigParser()
                cfg.readfp(fp)
                token = cfg.get('cubox', 'token')
                groups = cfg.get('cubox', 'groups')
                fp.close()
            groups = list(groups.split(","))
            self.logger.info(f"[Cubox] retrieving an article group: {groups}")
            headers = {
                "user-agent":
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
                "authorization": f"{token}"
            }
            urls = [
                f'https://cubox.pro/c/api/v2/search_engine/my?asc=true&page=1&filters=&groupId={group}&archiving=false'
                for group in groups
            ]
            for url in urls:
                yield scrapy.Request(url=url,
                                     callback=self.parse,
                                     headers=headers)
        except:
            self.logger.error(
                f"[Cubox] No valid token or groups found in config.ini, or your Cubox folder is empty"  #TODO: folder emptiness detection
            )

    def parse(self, response):
        try:
            with open(self.cofig_path) as fp:
                cfg = ConfigParser()
                cfg.readfp(fp)
                token = cfg.get('notion', 'token')
                database = cfg.get('notion', 'database')
                fp.close()
            if json.loads(response.body)["data"]:
                articles = json.loads(response.body)["data"]
                # self.record(response)
                for article in articles:
                    self.logger.info(
                        "================================================================================================================================="
                    )
                    item = ArticleItem()
                    self.logger.info(
                        f"[Cubox] parsing a article: {article['title']}")
                    item["token"] = token
                    item["database"] = database
                    item[
                        "title"] = article['title'] if article['title'] else ""
                    item["url"] = article['targetURL'] if article[
                        'targetURL'] else ""
                    item["tags"] = [tag['name'] for tag in article['tags']
                                    ] if article['tags'] else ""
                    item["content"] = article['description'] if article[
                        'description'] else ""  # INPROGRESS: add full text content

                    item["id"] = article['userSearchEngineID'] if article[
                        'userSearchEngineID'] else ""
                    yield item
            else:
                self.logger.error(
                    f"[Notion] no articles in Cubox found, plz make sure you have at least one artile to sync!"
                )
        except:
            self.logger.error(
                f"[Notion] No valid token or database found in config.ini")

    #def detect_folder_name(self, response):# TODO: add folder name detection
    def record(self, response):
        articles = json.loads(response.body)["data"]
        # articles_ids = [article["userSearchEngineID"] for article in articles]
        filename = f'output/info.dict'
        articles_info = str({
            article["userSearchEngineID"]: article["title"]
            for article in articles
        })
        with open(filename, 'w') as f:
            f.write(articles_info)

        group_id = response.url.split("&")[-2].replace("groupId=", "")
        filename = f'output/raw_{group_id}.json'
        with open(filename, 'wb') as f:
            f.write(response.body)
        self.log(f'Saved file {filename}')