# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import dataclasses
import json
import logging
import pickle
import re
from configparser import ConfigParser
from os import path
from unittest import result

import mistune
import requests
# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

from cubox_to_notion.items import ArticleItem
from cubox_to_notion.notionfier import MyRenderer
from cubox_to_notion.notionfier.plugins import plugin_footnotes

# from collections import Counter


class SaveToNotion:
    # Concatenate headers with token
    PAGES_STORED = {}
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
                              tags: list, content: list, cubox_url: str,
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
            "children": content
        })
        return payload

    def notion_import_markdown(self, markdown: str) -> str:
        md = mistune.create_markdown(
            renderer=MyRenderer(),
            plugins=[
                mistune.plugins.plugin_task_lists,
                mistune.plugins.plugin_table,
                mistune.plugins.plugin_url,
                mistune.plugins.plugin_def_list,
                mistune.plugins.plugin_strikethrough,
                plugin_footnotes,
            ],
        )
        result = md(markdown)
        # logging.info(result)
        return result

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

    def notion_page_cache_check(self,
                                database: str,
                                property_id: str,
                                headers: dict,
                                cubox_id: str,
                                type_name="Cubox") -> bool:
        if len(self.PAGES_STORED) == 0:
            self.notion_page_cache('read')
        page_keys = list(
            self.PAGES_STORED.keys())  # cubox ids stored in local cache
        # page_ids = self.notion_page_cache_query(
        #     headers, database)  # cubox urls stored in online Notion database
        # logging.debug(page_keys)
        # logging.debug(page_ids)
        # logging.debug(cubox_id)
        # logging.debug(self.PAGES_STORED)
        if cubox_id in page_keys:
            logging.debug(f"[Notion] page found in local cache, pass...")
            return True
        else:
            # self.PAGES_STORED[
            #     cubox_id] = f"https://cubox.pro/my/card?id={cubox_id}"
            logging.debug(
                f"[Notion] page not found in local cache, continue...")
            return False
            # self.notion_page_cache('write')

    def notion_page_cache_query(self,
                                headers: dict,
                                database: str,
                                type_name: str = 'Cubox') -> list:
        url = f"https://api.notion.com/v1/databases/{database}/query"
        payload = json.dumps(
            {"filter": {
                "property": "Type",
                "select": {
                    "equals": type_name
                }
            }})
        r = requests.post(url, data=payload, headers=headers)
        logging.debug(r.json()['results'][0]['id'])
        if r.status_code == 200:
            page_ids = [page['id'] for page in r.json()['results']]
        else:
            page_ids = []
        return page_ids

    def notion_page_cache(self, type: str = 'read') -> None:
        saved_path = path.abspath(path.dirname(
            path.dirname(__file__))) + '/saved_pages.pkl'
        if type == 'read':
            logging.debug(f"[Notion] checking pages stored...")
            try:
                f = open(saved_path, "rb")
                self.PAGES_STORED = pickle.load(f)
                f.close()
                logging.info(
                    f"[Notion] local cache of stored pages detected...")
            except:
                logging.info(
                    f"[Notion] local cache of stored pages not detected/error occured, fetching online..."
                )
                self.PAGES_STORED = {}
        elif type == 'write':
            logging.debug(f"[Notion] pages already stored will be ignored.")
            f = open(saved_path, "wb")
            pickle.dump(self.PAGES_STORED, f)
            f.close()
        else:
            self.PAGES_STORED = {}
            logging.error('[Notion] cache I/O method not specified!')

    def notion_page_cache_query_value(self,
                                      headers: dict,
                                      database: str,
                                      page_id: str,
                                      property_id: str,
                                      type_name='Cubox') -> str:
        url = f"https://api.notion.com/v1/databases/{database}/query"
        payload = json.dumps(
            {"filter": {
                "property": "Type",
                "select": {
                    "equals": type_name
                }
            }})
        r = requests.post(url, data=payload, headers=headers)
        # logging.debug(r.text)
        # logging.debug(r.json()['results'][0])
        if r.status_code == 200:
            cubox_url = self.notion_get_property_value(page_id, property_id,
                                                       headers)
            self.PAGES_STORED[
                page_id] = cubox_url  # TODO: hashmap? maybeself.PAGES_STORED[cubox_id] = cubox_url
            self.notion_page_cache('write')
            return cubox_url
        else:
            logging.error('[Notion] failed to determine pages stored, pass')
            return ''

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
            property_id = r.json()['results'][0]['properties']['Cubox'][
                'id']  #TODO: remind users
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
            # logging.critical(value)
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
                           content: list,
                           cubox_id: str,
                           type_sig: str = "Cubox"):
        if database != '00':
            try:
                logging.info(f"[Notion] creating a page...")
                cubox_url = f"https://cubox.pro/my/card?id={cubox_id}"
                payload = self.notion_concat_payload(database, title, url,
                                                     tags, content, cubox_url,
                                                     type_sig)
                # print(payload)
                api = f"https://api.notion.com/v1/pages"
                r = requests.post(api, data=payload, headers=headers)
                if r.status_code == 200:
                    self.PAGES_STORED[cubox_id] = cubox_url
                    self.notion_page_cache('write')
                    self.cubox_delete_page(cubox_id)
                    return True
                else:
                    logging.error(
                        f"[Notion] page not created ({title}) for network issues or API restriction ({database})."  #TODO: specify
                    )
                    return False
            except Exception as e:
                logging.error(f"[Cubox] exception: {e}")
                return False
        else:
            logging.error(
                f"[Notion] page not created ({title}) for a failure in retrieving database ({database})."
            )
            return False

    def cubox_concat_header(self):
        cofig_path = path.abspath(path.dirname(
            path.dirname(__file__))) + '/config.ini'
        with open(cofig_path) as fp:
            cfg = ConfigParser()
            cfg.readfp(fp)
            token = cfg.get('cubox', 'token').strip('"')
            fp.close()
        headers = {
            "Authorization": f"{token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }  # form-data, complex :(
        return headers

    # def cubox_urls_to_ids(self, urls: list) -> list:
    #     pattern = '(ff[a-z,A-Z,0-9]*)'
    #     logging.debug(urls)
    #     if len(urls) != 0:

    #         result = [
    #             re.search(pattern, url).group(0)
    #             if re.search(pattern, url) else url for url in urls
    #         ]
    #         return result
    #     else:
    #         logging.error('[Cubox] urls to deal with is empty!')
    #         return []

    def cubox_export_markdown(self,
                              cubox_id: str,
                              item_dscp: str,
                              legacy: bool = False) -> list:
        headers = self.cubox_concat_header()
        url = "https://cubox.pro/c/api/search_engines/export"
        data = f"type=md&engineIds={cubox_id}&snap=false&compressed=false"
        logging.debug(data)
        # logging.info(f"[Cubox] fetching fulltext of article: {cubox_id}")
        r = requests.post(url, data=data, headers=headers)
        logging.debug(r.text)
        if r.text and (legacy == False):
            content = [
                dataclasses.asdict(x,
                                   dict_factory=lambda x:
                                   {k: v
                                    for (k, v) in x if v is not None})
                for x in self.notion_import_markdown(r.text)
            ]
            # logging.debug(f"[Cubox] fulltext fetching succeed...")
            content = content[:
                              99]  #TODO: since limited by Notion, to find workarounds
            return content  # convert markdown strings to Notion data structure
        else:
            logging.error(
                f"[Cubox] fulltext fetching failed / legacy mode enabled, use description instead: {item_dscp}"
            )
            content = [{
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "type": "text",
                        "text": {
                            "content": item_dscp
                        }
                    }]
                }
            }]
            return content

    def cubox_check_deletion(self):
        cofig_path = path.abspath(path.dirname(
            path.dirname(__file__))) + '/config.ini'
        with open(cofig_path) as fp:
            cfg = ConfigParser()
            cfg.readfp(fp)
            delete = cfg.get('cubox', 'delete_after_cync')
            fp.close()
        return delete

    def cubox_delete_page(self, cubox_id: str):
        if self.cubox_check_deletion() == 'true':
            logging.info(
                f"[Cubox] auto delete is enabled, deleting article: {cubox_id}"
            )
            url = "https://cubox.pro/c/api/search_engines/delete"
            headers = self.cubox_concat_header()
            data = f"searchEngines=%5B%7B%22userSearchEngineID%22%3A%22{cubox_id}%22%7D%5D"
            # logging.critical(data)
            r = requests.post(url, data=data, headers=headers)
            if r.status_code == 200 and r.json()['code'] != -1:
                logging.info(f"[Cubox] article deleted: {r.json()}")
            else:
                logging.error(f"[Cubox] article not deleted: {r.json()}")
        else:
            logging.debug(f"[Cubox] auto delete is disabled")

    def process_item(self, item, spider) -> None:
        headers = self.notion_concat_headers(item["token"])

        if self.DATABASE == '':
            self.DATABASE = self.notion_get_database_id(
                item["database"], headers)
        if self.PROPERTY_ID == '':
            self.PROPERTY_ID = self.notion_get_property_id(
                self.DATABASE, headers)

        cubox_url = f"https://cubox.pro/my/card?id={item['id']}"
        # cubox_id = item['id']
        # logging.debug(cubox_id in list(self.PAGES_STORED.keys()))
        if self.notion_page_cache_check(self.DATABASE, self.PROPERTY_ID,
                                        headers, item['id']):
            logging.info(f"[Notion] page already stored, pass...")
            pass
        else:
            try:
                content = self.cubox_export_markdown(item['id'],
                                                     item['content'])
                logging.debug(content)
                if self.notion_create_page(self.DATABASE, headers,
                                           item["title"], ''.join(item["url"]),
                                           item["tags"], content,
                                           item['id']) == False:
                    content = self.cubox_export_markdown(
                        item['id'], item['content'], legacy=True
                    )  # fallback to description when fulltext failed
                    logging.debug(content)
                    self.notion_create_page(self.DATABASE, headers,
                                            item["title"],
                                            ''.join(item["url"]), item["tags"],
                                            content, item['id'])
            except:
                logging.error(f"[Cubox] page processing failed: {item['id']}")
