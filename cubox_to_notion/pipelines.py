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
    PAGES_STORED = []
    DATABASE = ''
    PROPERTY_ID = ''

    def notion_concat_headers(self, token: str) -> dict:
        headers = {
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        return headers

    # Concatenate payload
    def notion_concat_payload(self, database: str, title: str, url: str,
                              tags: list, content: str, cubox_url: str,
                              type_sig: str) -> str:
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
                "Cubox": {
                    "url": cubox_url
                },
                "Type": {
                    "select": {
                        "name": type_sig
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
    def notion_get_database_id(self, database: str, headers: dict) -> str:
        url = f"https://api.notion.com/v1/databases/{database}/query"
        r = requests.post(url, headers=headers)
        logging.info(f"[Notion] retrieving a database: {database}")
        if r.status_code == 200:
            database = r.json()["results"][0]["parent"]["database_id"]
            # print(r.json())
        else:
            logging.error('[Notion] database_id not found')
            database = '00'
        return database

    # Get basic info of a database
    def notion_get_pages_stored(self,
                                database: str,
                                property_id: str,
                                headers: dict,
                                type_name="Cubox") -> list:

        logging.info(f"[Notion] checking pages stored...")
        url = f"https://api.notion.com/v1/databases/{database}/query"
        payload = json.dumps(
            {"filter": {
                "property": "Type",
                "select": {
                    "equals": type_name
                }
            }})
        r = requests.post(url, data=payload, headers=headers)
        pages_stored = []
        # print(r.json()['results'][0]['id'])
        if r.status_code == 200:
            for page in r.json()['results']:
                page_id = page['id']
                # print(page_id)
                cubox_url = self.notion_get_property_value(
                    page_id, property_id, headers)
                pages_stored.append(cubox_url)
            logging.info(
                f"[Notion] {len(pages_stored)} pages have been stored, these pages will be ignored."
            )
            return pages_stored
        else:
            logging.error('[Notion] failed to determine pages stored, pass')
            return []

    def notion_get_property_id(self,
                               database: str,
                               headers: dict,
                               type_sig="Cubox") -> str:
        url = f"https://api.notion.com/v1/databases/{database}/query"
        payload = json.dumps(
            {"filter": {
                "property": "Type",
                "select": {
                    "equals": type_sig
                }
            }})
        # print(payload)
        r = requests.post(url, data=payload, headers=headers)

        # print(r.json()['results'][0]['properties']['Cubox']['id'])
        if r.status_code == 200:
            property_id = r.json()['results'][0]['properties']['Cubox']['id']
            return property_id
        else:
            logging.error('[Notion] property id not found')
            return ''

    def notion_get_property_value(self, page_id: str, property_id: str,
                                  headers: dict):
        url = f"https://api.notion.com/v1/pages/{page_id}/properties/{property_id}"
        # print(url)
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            value = r.json()['url']
            # print(r.json())
            return value
        else:
            logging.error('[Notion] property value not found, pass')
            return ""

    # Create a page with content
    def notion_create_page(self,
                           database: str,
                           headers: dict,
                           title: str,
                           url: str,
                           tags: list,
                           content: str,
                           cubox_id: str,
                           type_sig: str = "Cubox") -> bool:

        if database != '00':
            logging.info(f"[Notion] creating a page...")
            cubox_url = f"https://cubox.pro/my/card?id={cubox_id}"
            payload = self.notion_concat_payload(
                database,
                title,
                url,
                tags,
                content,
                cubox_url,
                type_sig,
            )
            # print(payload)
            api = f"https://api.notion.com/v1/pages"
            r = requests.post(api, data=payload, headers=headers)
            if r.status_code == 200:
                try:
                    self.cubox_delete_page(cubox_id)
                except Exception as e:
                    logging.error(f"[Cubox] exception: {e}")
                return True  # created and delted
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

    def cubox_delete_page(self, cubox_id):
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
            data = f"searchEngines=%5B%7B%22userSearchEngineID%22%3A%22{cubox_id}%22%7D%5D"
            # logging.critical(data)
            logging.info(
                f"[Cubox] auto delete is enabled, deleting article: {cubox_id}"
            )
            r = requests.post(url, data=data, headers=headers)
            if r.status_code == 200 and r.json()['code'] != -1:
                logging.info(f"[Cubox] article deleted: {r.json()}")
            else:
                logging.error(f"[Cubox] article not deleted: {r.json()}")
        else:
            logging.debug(f"[Cubox] auto delete is disabled")

    def process_item(self, item, spider) -> None:
        headers = self.notion_concat_headers(item["token"])
        self.DATABASE = self.notion_get_database_id(
            item["database"],
            headers) if self.DATABASE == '' else self.DATABASE
        self.PROPERTY_ID = self.notion_get_property_id(
            self.DATABASE,
            headers) if self.PROPERTY_ID == '' else self.PROPERTY_ID
        self.PAGES_STORED = self.notion_get_pages_stored(
            self.DATABASE, self.PROPERTY_ID, headers) if len(
                self.PAGES_STORED) == 0 else self.PAGES_STORED
        cubox_url = f"https://cubox.pro/my/card?id={item['id']}"
        if cubox_url in self.PAGES_STORED:
            logging.info(f"[Notion] the page above is already stored, pass")
            pass
        else:
            self.notion_create_page(self.DATABASE, headers, item["title"],
                                    ''.join(item["url"]), item["tags"],
                                    item["content"], item['id'])

    #def detect_duplicate() #[x]TODO detect duplicate
