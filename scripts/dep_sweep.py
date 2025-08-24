import pathlib
import re

reqs = set()
for path in pathlib.Path('JarvisPrime').rglob('requirements*.txt'):
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            reqs.add(line)
pathlib.Path('CONSOLIDATED_REQUIREMENTS.txt').write_text('\n'.join(sorted(reqs)) + '\n')
print(f"found {len(reqs)} requirements")
