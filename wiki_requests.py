"""Functions for wrapped MediaWiki API requests."""

from typing import List, Dict, Any
from time import sleep

import logging
import requests as r  # pylint:disable=import-error

# TODO This is a sloppy type annotation, but mypy doesn't have JSON support yet
JSON = Dict[str, Any]


def request_category_info(category_id: str) -> JSON:
    params = {
        "format": "json",
        "action": "query",
        "list": "categorymembers",
        "cmpageid": category_id,
        "cmtype": "subcat|page",
        "cmlimit": 500
    }

    resp = wrapped_request(params)
    members: List[JSON] = resp["query"]["categorymembers"]
    subcats = [member for member in members
               if member["title"].startswith("Category:")]

    page_count = len(members) - len(subcats)

    category_info = {"page_count": page_count,
                      "subcats": subcats}

    return category_info


def request_subpages(category_id: str) -> List[JSON]:
    """
    Return the subpages of a given category.

    :param category_id: the pageid of the category
    :returns: a list of subpages
    """
    params = {
        "format": "json",
        "action": "query",
        "list": "categorymembers",
        "cmpageid": category_id,
        "cmtype": "page",
        "cmlimit": 500
    }

    resp = wrapped_request(params)
    subpages: List[JSON] = resp["query"]["categorymembers"]
    return subpages


def request_page_categories(page_id: str) -> List[str]:
    """
    Return the categories to which a given page belongs.

    :param page_id: the id of the page
    :returns: a list of category ids
    """
    params = {
        "format": "json",
        "action": "query",
        "pageids": page_id,
        "generator": "categories",
        "prop": "info",
        "cllimit": 500
    }

    resp = wrapped_request(params)
    pages = list(resp["query"]["pages"].keys())
    return [str(page) for page in pages]


def request_pageid_from_title(page_title: str) -> str:
    """
    Return the id of the page with a given title.

    :param page_title: the title of the page
    :returns: a pageid
    """
    params = {
        "format": "json",
        "action": "query",
        "titles": page_title
    }

    resp = wrapped_request(params)
    pageid = list(resp["query"]["pages"].keys())[0]
    return pageid


def wrapped_request(params: JSON) -> JSON:
    """Wrap a request to deal with connection errors.

    :param params: request parameters
    :returns: MediaWiki API response data
    """

    user_agent = ("wiki_bot/1.2.1 (https://github.com/ddxtanx/wiki_bot; "
                  "gcc@ameritech.net)")
    header = {"Api-User-Agent": user_agent}

    max_attempts = 5
    attempt = 0
    while True:
        # TODO argparse this
        sleep(1)

        try:
            base_url = "https://en.wikipedia.org/w/api.php"
            resp: r.Response = r.get(base_url,
                                     headers=header,
                                     params=params,
                                     timeout=5)

            return resp.json()
        except (r.exceptions.Timeout, r.exceptions.ConnectionError) as conn_error:
            err_type = type(conn_error).__name__
            if attempt < max_attempts:
                attempt += 1
                logging.warning("Caught %s, retrying. (attempt %d/%d)",
                                err_type, attempt, max_attempts)
            else:
                raise conn_error
