import pathlib

import hext
import requests

PACKAGE_PATH = pathlib.Path(__file__).parents[1]

response = requests.get('https://www.questhealth.com/shop?start=1&sz=100')  # Works for up to 100 results.
response.raise_for_status()
content = response.content.decode()

results = hext.Rule('<h3 class="product-title" @text:name></h3> <div class="description" @text:description></div>').extract(hext.Html(content))
results = {r['name']: r['description'] for r in results}
results = [f'{k}: {v}' for k, v in results.items()]
results = sorted(results)

text = '\n'.join(results)
path = PACKAGE_PATH / 'data/sourced/QuestHealth_tests_list.txt'
print(f'Writing {len(results)} results having text length {len(text):,} to {path}.')
path.write_text(text)
