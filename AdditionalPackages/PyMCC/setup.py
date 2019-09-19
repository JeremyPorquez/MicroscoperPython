from setuptools import setup, find_packages

print(find_packages())

setup(name="PyMCC",
      version="0.1",
      description="MCCDaq",
      author="Jeremy Porquez",
      author_email="jeremyporquez@trentu.ca",
      license="NONLICENSE",
      packages=find_packages(),
      zip_safe=False,
      include_package_data=False,
      install_requires=[],
      )

