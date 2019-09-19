from setuptools import setup, find_packages

print(find_packages())

setup(name="MMath",
      version="0.1",
      description="Optimized microscoper math packagage",
      author="Jeremy G. Porquez",
      author_email="jeremyporquez@trentu.ca",
      license="NONLICENSE",
      packages=find_packages(),
      zip_safe=False,
      include_package_data=False,
      install_requires=[],
      )
## to create package
## python setup.py sdist

## to install using pip
## pip install -e .