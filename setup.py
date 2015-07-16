import glob

from setuptools import find_packages, setup

setup(name='conectsim',
      version='0.2.dev0',
      description="instrument simulator",
      url='http://guaix.fis.ucm.es/~spr',
      maintainer='Sergio Pascual',
      maintainer_email='sergiopr@fis.ucm.es',
      license='GPLv3',
      packages=find_packages(),
      classifiers=[
        "Programming Language :: Python",
        'Development Status :: 3 - Alpha',
        "Environment :: Other Environment",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Astronomy",
        ],
     long_description=open('README.txt').read()
)

