import pathlib

PACKAGE_PATH = pathlib.Path(__file__).parents[1]
SOURCE_DATA_PATH = PACKAGE_PATH / 'data/sourced'

merged = []
for source_data_path in SOURCE_DATA_PATH.glob('*.txt'):
    source_name = source_data_path.name.split('_', 1)[0]
    for test_line in open(source_data_path):
        test_line = f'[{source_name}] {test_line}'
        merged.append(test_line)

output_path = SOURCE_DATA_PATH.parent / 'uploads/tests_list.txt'
text = ''.join(merged)
output_path.write_text(text)
