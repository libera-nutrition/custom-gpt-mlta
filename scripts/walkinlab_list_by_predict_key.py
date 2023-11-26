import concurrent.futures as cf
import datetime
import itertools
import pathlib
import string
import sys

import bs4
import diskcache
import requests

PACKAGE_PATH = pathlib.Path(__file__).parents[1]
DISKCACHE = diskcache.FanoutCache(directory=str(PACKAGE_PATH / '.diskcache'), timeout=1, size_limit=1024 ** 3)

MAX_KEY_LEN = 3
MAX_WORKERS = 32
REQUEST_HEADERS = {"User-Agent": 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0'}
HREF_PREFIX = '/products/view/'
EXCLUDED = {'gift-card-1'}


@DISKCACHE.memoize(expire=datetime.timedelta(weeks=4).total_seconds(), tag='get_results')
def get_results(key: str, /) -> list[str]:
    print(f'Reading URL for key={key}.')
    response = requests.post('https://www.walkinlab.com/products/predictSearch', data={'search': key}, headers=REQUEST_HEADERS)
    response.raise_for_status()
    print(f'Read URL for key={key} with status {response.status_code}.')

    # print(f'Parsing content of length {len(content):,} for key {key}.')
    parser = bs4.BeautifulSoup(response.content, 'html.parser')
    results = parser.find_all('a', href=True)
    results = [result['href'] for result in results]
    results = list(dict.fromkeys(results))
    return results


@DISKCACHE.memoize(expire=datetime.timedelta(weeks=4).total_seconds(), tag='get_content')
def get_content(href: str) -> bytes:
    assert href.startswith(HREF_PREFIX), href
    href_short = href.removeprefix(HREF_PREFIX)
    print(f'Reading data for {href_short}.')
    response = requests.get(f'https://www.walkinlab.com{href}', headers=REQUEST_HEADERS)
    try:
        response.raise_for_status()
    except Exception:
        print(f'Failed to get content for {href}.', file=sys.stderr)
        raise
    print(f'Read data for {href_short}.')
    return response.content


def get_data(href: str) -> dict[str, str]:
    assert href.startswith(HREF_PREFIX), href
    href_short = href.removeprefix(HREF_PREFIX)
    content = get_content(href).decode()

    try:
        parser = bs4.BeautifulSoup(content, 'html.parser')
        data = {'id': href_short, 'name': parser.h1.get_text(strip=True), 'description': parser.find('div', {'class': 'description'}).get_text(strip=True)}
        assert data['name'], data
        assert ('\n' not in data['name']), data
        assert data['description'], data
        assert ('\n' not in data['description']), data

        advert = parser.find('div', {'class': 'description'}).find('span', {'class': 'red'})
        if advert:
            advert = advert.get_text(strip=True)  # Example: November Special: Save 15% with coupon code NOV15.
            assert advert, (data, advert)
            assert data['description'].startswith(advert), (data, advert)
            data['description'] = data['description'].removeprefix(advert).lstrip()
            assert data['description'], data

        data['description'] = data['description'].replace('\xa0', ' ')  # Note: unicodedata.normalization with NFKC or NFKD shouldn't be used here as both undesirably replace the ™ character.
    except Exception:
        print(f'Failed to parse data for {href}.', file=sys.stderr)
        raise
    return data


def main() -> None:
    final_results = {}
    for key_len in range(1, MAX_KEY_LEN + 1):
        chars = string.ascii_lowercase + '0123456789' if (key_len <= 2) else string.ascii_lowercase
        keys = [''.join(key) for key in itertools.product(chars, repeat=key_len)]

        curr_results = set()
        with cf.ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
            results_groups = executor.map(get_results, keys)
            for result_group in results_groups:
                for result in result_group:
                    if (result not in final_results) and (result.removeprefix(HREF_PREFIX) not in EXCLUDED):
                        curr_results.add(result)
            results_data = list(executor.map(get_data, list(curr_results)))
            for result_data in results_data:
                final_results[result_data['id']] = result_data
        print(f'Obtained a total of {len(final_results)} results until key length {key_len}.')

    output_results = {r['name']: r['description'] for r in final_results.values()}
    output_results = [f'{k}: {v}' for k, v in output_results.items()]
    output_results = sorted(output_results)
    text = '\n'.join(output_results)
    path = PACKAGE_PATH / 'uploads/WalkInLab_tests_list.txt'
    print(f'Writing {len(output_results)} results having text length {len(text):,} to {path}.')
    path.write_text(text)


def delete_cache_by_function(fn_name: str, /) -> None:
    for key in list(DISKCACHE):
        if key[0] == fn_name:
            print(f'Deleting cache for key={key}')
            del DISKCACHE[key]


if __name__ == '__main__':
    main()
    # delete_cache_by_function('__main__.get_data')
