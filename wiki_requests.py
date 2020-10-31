#!/usr/bin/env python

from typing import List, Dict, Any
from time import sleep

import logging
import requests as r  # pylint:disable=import-error


def request_subcategories(category_id: str) -> List[Dict[str, str]]:
    """
    Return the subcategories of a given category.

    :param category_id: the pageid of the category
    :returns: a list of subcategories
    """
    params = {
        "format": "json",
        "action": "query",
        "list": "categorymembers",
        "cmpageid": category_id,
        "cmtype": "subcat"
    }

    resp = wrapped_request(params)
    subcats: List[Dict[str, str]] = resp["query"]["categorymembers"]
    return subcats


def request_subpages(category_id: str) -> List[Dict[str, str]]:
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
        "cmtype": "page"
    }

    resp = wrapped_request(params)
    subpages: List[Dict[str, str]] = resp["query"]["categorymembers"]
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
        "prop": "info"
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


# TODO This is a sloppy type annotation, but mypy doesn't have JSON support
def wrapped_request(params: Dict[str, str]) -> Dict[str, Any]:
    """Wrap a request to deal with connection errors.

    :param params: request parameters
    :returns: MediaWiki API response data
    """

    user_agent = ("wiki_bot/1.2.1 (https://github.com/ddxtanx/wiki_bot; "
                  "gcc@ameritech.net)")
    header = {"Api-User-Agent": user_agent}

    max_attempts = 5
    for attempt in range(max_attempts):
        # TODO argparse this
        sleep(1)

        try:
            base_url = "https://en.wikipedia.org/w/api.php"
            resp: r.Response = r.get(base_url,
                                     headers=header,
                                     params=params)

            return resp.json()
        except r.exceptions.ConnectionError as conn_error:
            err_type = type(conn_error).__name__
            logging.warning("Caught %s, retrying. (attempt %d/%d)",
                            err_type, attempt + 1, max_attempts)

    logging.warning("Request failed. Returning nothing.")
    return {}
