import concurrent.futures as cf
import itertools
import pathlib
import string

import bs4
import requests

MAX_KEY_LEN = 3
MAX_WORKERS = 32


def get_results(key: str, /) -> list[str]:
    print(f'Reading URL for key={key}.')
    response = requests.post('https://www.walkinlab.com/products/predictSearch', data={'search': key}, headers={"User-Agent": 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0'})
    response.raise_for_status()
    content = response.content.decode()
    # print(f'Read URL for key={key} with status {response.status_code}.')

    # print(f'Parsing content of length {len(content):,} for key {key}.')
    parser = bs4.BeautifulSoup(response.content, 'html.parser')
    results = [result.get_text() for result in parser.find_all('a', href=True)]
    results = list(dict.fromkeys(results))
    return results


all_results = set()
for key_len in range(1, MAX_KEY_LEN + 1):
    keys = [''.join(key) for key in itertools.product(string.ascii_lowercase, repeat=key_len)]

    with cf.ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results_groups = executor.map(get_results, keys)

    for result_group in results_groups:
        for result in result_group:
            all_results.add(result)
    print(f'Obtained a total of {len(all_results)} until key length {key_len}.')

all_results = sorted(all_results)
text = '\n'.join(all_results)
path = pathlib.Path(__file__).parents[1] / 'uploads/WalkInLab_tests_list.txt'
print(f'Writing {len(all_results)} results having text length {len(text):,} to {path}.')
path.write_text(text)
