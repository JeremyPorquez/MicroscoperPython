from setuptools import setup, find_packages

print(find_packages())

setup(name="PyAPT",
      version="0.1",
      description="PyAPT",
      author="https://github.com/mcleung/PyAPT",
      author_email="https://github.com/mcleung/PyAPT",
      license="NONLICENSE",
      packages=find_packages(),
      zip_safe=False,
      include_package_data=False,
      install_requires=[],
      )

