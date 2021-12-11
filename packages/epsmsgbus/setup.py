/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



**********************************************************************************/


"""
Installation for epsmsgbus and its dependencies.
"""

import setuptools

README = "epsmsgbus - store data in Cynosure and Jakob."

# Read from README.md on-the-fly
with open("README.md") as fp:
    README = fp.read()


with open("VERSION") as fp:
    version = fp.read().strip()


setuptools.setup(
        name="epsmsgbus",
        version=version,
        author="facosta",
        author_email="fredrik.acosta@volvocars.com",
        url="http://www.volvocars.com/",
        description="Save testresults in Jakob DB and/or Cynosure",
        long_description=README,
        package_data = {
            '': ['db.ini'],
        },
        packages=['', 'epsmsgbus', 'epsdb'],
        classifiers=[
            "Programming Language :: Python :: 3",
            "License :: Other/Proprietary Licence",
        ],
        python_requires='>=3.6',
        install_requires=[
            "pytz",
            "pyodbc",
            "python-dateutil",
        ]
)
