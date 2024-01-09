import json

with open('Pipfile.lock') as file:
    data = json.load(file)
    locked_packages = set(data['default'].keys())  # Assuming you installed packages in the default section

with open('current_requirements.txt') as file:
    current_packages = set(line.split('==')[0] for line in file)

extra_packages = current_packages - locked_packages
print("Extra packages installed:", extra_packages)
