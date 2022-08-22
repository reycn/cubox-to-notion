# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import json
import logging
from configparser import ConfigParser
from os import path

import requests
# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

from cubox_to_notion.items import ArticleItem


class SaveToNotion:
    # Concatenate headers with token
    def concat_headers(self, token: str) -> dict:
        headers = {
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        return headers

    # Concatenate payload
    def concat_payload(self, database: str, title: str, url: str, tags: list,
                       content: str, type: str) -> str:
        payload = json.dumps({
            "parent": {
                "type": "database_id",
                "database_id": database
            },
            "properties": {
                "Name": {
                    "title": [{
                        "text": {
                            "content": title
                        }
                    }]
                },
                "URL": {
                    "url": url
                },
                "Tags": {
                    "multi_select": [{
                        "name": tag
                    } for tag in tags]
                },
                "Type": {
                    "select": {
                        "name": type
                    }
                }
            },
            "children": [{
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "type": "text",
                        "text": {
                            "content": content
                        }
                    }]
                }
            }]
        })
        return payload

    # Get basic info of a database
    def retrieve_database(self, database: str, headers: dict) -> str:
        url = f"https://api.notion.com/v1/databases/{database}/query"
        r = requests.request("POST", url, headers=headers)
        logging.info(f"[Notion] retrieving a database: {database}")
        if r.status_code == 200:
            database = r.json()["results"][0]["parent"]["database_id"]
        else:
            logging.error('[Notion] database_id not found')
            database = '00'
        return database

    # Create a page with content
    def create_page(self,
                    database: str,
                    headers: dict,
                    title: str,
                    url: str,
                    tags: list,
                    content: str,
                    id: str,
                    classification: str = "Cubox") -> bool:

        if database != '00':
            logging.info(f"[Notion] creating a page...")
            payload = self.concat_payload(database, title, url, tags, content,
                                          classification)
            api = f"https://api.notion.com/v1/pages"
            r = requests.post(api, data=payload, headers=headers)
            if r.status_code == 200:
                # page_id = r.json()['id']
                # print(f"Success synced to Notion: {r.json()['id']}")
                try:
                    self.delete_cubox(id)
                except Exception as e:
                    logging.error(f"[Cubox] exception: {e}")
                return True
            else:
                logging.error(
                    f"[Notion] page not created ({title}) for adding a page.")

                logging.error(f"Details: {r.json()}")
                return False
        else:
            logging.error(
                f"[Notion] page not created ({title}) for a failure in retrieving database ({database})."
            )
            return False

    def process_item(self, item, spider):
        headers = self.concat_headers(item["token"])
        database = self.retrieve_database(item["database"], headers)
        self.create_page(database, headers, item["title"],
                         ''.join(item["url"]), item["tags"], item["content"],
                         item['id'])

    #def detect_duplicate() #[x]TODO detect duplicate

    def delete_cubox(self, id):
        cofig_path = path.abspath(path.dirname(
            path.dirname(__file__))) + '/config.ini'
        with open(cofig_path) as fp:
            cfg = ConfigParser()
            cfg.readfp(fp)
            token = cfg.get('cubox', 'token').strip('"')
            delete = cfg.get('cubox', 'delete_after_cync')
            fp.close()
        # logging.critical(cofig_path, token, 'end')
        if delete == 'true':
            headers = {
                "authorization": f"{token}",
                "Content-Type": "application/x-www-form-urlencoded"
            }  # form-data, complex :(
            url = f"https://cubox.pro/c/api/search_engines/delete"
            data = f"searchEngines=%5B%7B%22userSearchEngineID%22%3A%22{id}%22%7D%5D"
            # logging.critical(data)
            logging.info(
                f"[Cubox] auto delete is enabled, deleting article: {id}")
            r = requests.post(url, data=data, headers=headers)
            if r.status_code == 200 and r.json()['code'] != -1:
                logging.info(f"[Cubox] article deleted: {r.json()}")
            else:
                logging.error(f"[Cubox] article not deleted: {r.json()}")
        else:
            logging.debug(f"[Cubox] auto delete is disabled")
