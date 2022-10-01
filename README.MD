<img src="./assets/banner.jpg"/></img>

# Cubox to Notion [ Engligh | [中文](./README.ZH.MD) ]

![version](https://img.shields.io/badge/version-alpha-red)
![GitHub top language](https://img.shields.io/github/languages/top/reycn/cubox-to-notion) [![codebeat badge](https://codebeat.co/badges/ffea9c86-2b10-45b9-b4cc-d7cb35bbde4d)](https://codebeat.co/projects/github-com-reycn-cubox-to-notion-main) ![License](https://img.shields.io/badge/license-MIT-000000.svg)  
A slight tool for [Notion](https://www.notion.so/) users to integrate [Cubox](https://cubox.pro/) service.

**Motivation**: In most cases (including WeChat/web clipping), Cubox is a decent solution to collect something, however, Notion is more capable for managing and utilizing them.

**Next Update**: planned before Jan, 23.

# What's New in Oct.✨

-   **Full-text suport** (experimental, dute to API limis, some article will be fallback to description)
-   Improved speed by locah chache control
-   Issue fixed: [No.5](https://github.com/reycn/cubox-to-notion/issues/5])

# Features

-   **TOTALLY FREE**
-   Cubox contents -> Notion, currently supporting

    -   Basic information, including title, descriptionc, link, tags
    -   Cubox properties, including link, full-text, created time (planned)

-   Consecutive, incremental synchronization
-   Duplication detection & control
-   Automatic deletion & control
-   Improved speed
-   Multiple folders (implemented, not tested though)
-   Select folder by name (planned)

# At a glance

<img src="./assets/cubox-to-notion.gif"/></img>

# How to start

## 1. Prepare a Notion database and a bot

(1) Prepare a Notion database with following necessary columns:

-   Name, `title`
-   URL, `link`
-   Cubox, `link`
-   Tags, `multiple selection`
-   Type, `selection`, a default item 'Cubox' required

(2) copy your Notion database id, to `config.ini`(template found at `config.template.ini`)  
(3) create a Notion Bot, get a key, and copy to `config.ini`  
(4) invite your bot to your database, make sure it has **write** permission

## 2. Get your Cubox token and locate your group to sync

(1) log in, for sure, and copy your `token` stored in your cookies to `config.ini`  
(remember to qute them with `"` since Cubox token has a `=` in its string)  
(2) copy your collection id to `config.ini`

## 3. Start to run

-   If you would like to keep your Notion database updated consecutively, use loop sync:  
    `python main.py`
-   If you would like to excute an one-time sync, use:  
    `scrapy crawl cubox_to_notion -L ERROR` # where log-level can be customized by replacing `ERROR` to `INFO`, `CRITICAL`, etc.  
    _MORE EXPLANATION INCOMING_

## Required & not required

### Required

-   An Notion API token, make sure your extension is invited to your datdabase
-   A server or a local computer with Python 3.6+ installed

### Not Required

-   Notion Pro Plan ( = free 🤩)
-   **Cubox Pro Plan** ( = free 🤩)

## Technical Details

In a word, we utilized the potential of Scrapy.

-   [Scrapy](https://github.com/scrapy/scrapy), to fetch and parse Cubox contents
-   [Requests](https://github.com/psf/requests), interaction between two products
-   API
    -   [Notion, official](https://developers.notion.com/), directly and rapidly interacted in HTTP
    -   [ Cubox, unofficial](https://github.com/reycn/cubox-to-notion), since the official one is not sufficient to accomplish our task : )
-   Third-party module:
    -   [Notionfier](https://github.com/Arsenal591/notionfier), for Markdown full-text support
-   See: [architecture](https://app.tryeraser.com/workspace/xYpHHokfhmbpjrVowqsb?origin=share)
    <img src="./assets/architecture.png"/></img>

## Support the Author

-   Click 🌟
-   Donation through [afdian](https://afdian.net/@reynd/plan)

## LICENSE

Permission is hereby granted in [MIT LICENSE](LICENSE)
