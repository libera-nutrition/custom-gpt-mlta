import pathlib
import string

import bs4
import requests

all_results = []
for letter in string.ascii_uppercase:
    url = f'https://www.walkinlab.com/categories/view/all-products?letter={letter}'

    print(f'Reading URL for letter {letter}.')
    response = requests.get(url, headers={"User-Agent": 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0'})
    response.raise_for_status()
    print(f'Read URL for letter {letter} with status {response.status_code}.')

    print(f'Parsing content of length {len(response.content):,} for letter {letter}.')
    parser = bs4.BeautifulSoup(response.content, 'html.parser')
    results = [{'name': result.find('h3').get_text(strip=True), 'description': result.find('div', class_='title').find_next('div').get_text(strip=True)} for result in parser.find_all('li', class_='product')]
    print(f'Parsed {len(results)} results for letter {letter}.')

    all_results.extend(results)
    # break

all_results = [f'{r['name']}: {r['description']}' for r in all_results]
all_results.sort()
text = '\n'.join(all_results)
path = pathlib.Path(__file__).parents[1] / 'uploads/WalkInLab_tests_list_by_letter.txt'
print(f'Writing {len(all_results)} results having text length {len(text):,} to {path}.')
path.write_text(text)
