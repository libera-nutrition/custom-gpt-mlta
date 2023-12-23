import concurrent.futures as cf
import datetime
import itertools
import pathlib
import string
import sys
from typing import Any, Optional

import diskcache
import requests

FILE_PATH = pathlib.Path(__file__)
PACKAGE_PATH = FILE_PATH.parents[1]
DISKCACHE_PATH = PACKAGE_PATH / '.diskcache' / FILE_PATH.stem
DISKCACHE = diskcache.FanoutCache(directory=str(DISKCACHE_PATH), timeout=1, size_limit=1024 ** 3)

MAX_KEY_LEN = 0  # Note: No additional benefit was observed with lengths 1 or 2.
MAX_WORKERS = 1

EXCLUDED_IDs = {'\ufeffHCPCS CODE'}

# Note: If this script freezes during execution, it may be because of diskcache handling a process executor poorly. In this case, either stop and rerun the script, or otherwise use a thread executor instead.


@DISKCACHE.memoize(expire=datetime.timedelta(weeks=4).total_seconds(), tag='get_data')
def get_data(term: str, /) -> Optional[list[dict[str, Any]]]:
    # print(f'Reading data for search term {term!r}.')
    response = requests.get('https://radiologyassist.com/js/CPTSearch/CPTSearch_Select2.php', params={'term': term, 'type': 'public'})
    try:
        response.raise_for_status()
    except Exception:
        print(f'Failed to get valid response for search term {term!r}.', file=sys.stderr)
        raise

    try:
        data = response.json()
    except Exception:
        print(f'Failed to parse data for search term {term!r}.', file=sys.stderr)
        raise
    print(f'Read data for search term {term!r}.')
    return data


def get_results(term: str, /) -> list[str]:
    data = get_data(term)
    if not data:
        # print(f'No results exist for search term {term!r}.')
        return []
    results = [d['text'].removeprefix(f'{d['id']} - ').strip() for d in data if (d['id'] not in EXCLUDED_IDs)]
    assert ('DESCRIPTION' not in str(results)), results
    return results


def main() -> None:
    final_results = set()
    for key_len in range(MAX_KEY_LEN + 1):
        chars = string.ascii_lowercase
        if key_len in (1, 2):
            chars += string.digits
        # if key_len == 1:
        #     chars += string.punctuation  # No benefit was observed.

        keys = [''.join(key) for key in itertools.product(chars, repeat=key_len)]

        debugging = bool(sys.gettrace())
        executor = cf.ThreadPoolExecutor if debugging else cf.ProcessPoolExecutor
        with executor(max_workers=MAX_WORKERS) as executor:
            curr_results_groups = executor.map(get_results, keys)
            for curr_results in curr_results_groups:
                final_results.update(curr_results)
        print(f'Obtained a total of {len(final_results)} results until key length {key_len}.')

    # output_results = {r['name']: r['description'] for r in final_results.values()}
    # output_results = [f'{k}: {v}' for k, v in output_results.items()]
    output_results = sorted(final_results)
    output_text = '\n'.join(output_results)
    output_path = PACKAGE_PATH / 'uploads/RadiologyAssist_tests_list.txt'
    print(f'Writing {len(output_results)} results having text length {len(output_text):,} to {output_path}.')
    output_path.write_text(output_text)


if __name__ == '__main__':
    main()
