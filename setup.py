import os
import shutil
import platform
import requests

from win32api import GetFileVersionInfo, HIWORD
from urllib.request import urlopen
from zipfile import ZipFile
from io import BytesIO

from typing import TypedDict, Union, Literal, List, Dict, cast


CHROME_PATHS = [
    os.path.join(cast(str, os.getenv(path)), 'Google\Chrome\Application\Chrome.exe')
    for path in ('ProgramFiles', 'ProgramFiles(x86)', 'LocalAppData')
]


class ChromeDriverDownload(TypedDict):
    url: str
    platform: Union[
        Literal['linux64'],
        Literal['mac-arm64'],
        Literal['mac-x64'],
        Literal['win32'],
        Literal['win64'],
    ]


class ChromeMilestone(TypedDict):
    milestone: str
    version: str
    revision: str
    downloads: Dict[
        Union[
            Literal['chrome'], Literal['chromedriver'], Literal['chrome-headless-shell']
        ],
        List[ChromeDriverDownload],
    ]


class ChromeDriverResponse(TypedDict):
    timestamp: str
    milestones: Dict[str, ChromeMilestone]


def get_chrome_driver_url(chrome_version: str) -> str:
    response = requests.get(
        'https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json'
    )

    if response.status_code != 200:
        raise Exception('Failed to get driver url.')

    data: ChromeDriverResponse = response.json()

    drivers = data['milestones']

    filtered_drivers = {
        version: driver
        for version, driver in drivers.items()
        if 'chromedriver' in driver['downloads']
    }

    if chrome_version not in filtered_drivers:
        raise Exception(f'Your chrome version {chrome_version} is not supported.')

    chrome_driver_url = None

    for version, driver in filtered_drivers.items():
        if chrome_version == version:
            chrome_driver_url = driver['downloads']['chromedriver'][-1]['url']
            break

    if chrome_driver_url is None:
        raise Exception(f'Failed to get driver url for version {chrome_version}.')

    return chrome_driver_url


def get_chrome_version() -> str:
    if platform.system() != 'Windows':
        raise Exception('This setup is only for Windows!')

    no_chrome = True

    print('Checking If Google Chrome is installed...')

    for chrome_path in CHROME_PATHS:
        if os.path.exists(chrome_path):
            no_chrome = False
            chrome_version = HIWORD(
                GetFileVersionInfo(chrome_path, '\\')['FileVersionMS']
            )

    if no_chrome:
        raise Exception('Google Chrome is not installed.')

    if chrome_version < 90:
        raise Exception('Google Chrome must be at least at version 90 or higher.')

    return str(chrome_version)


def main() -> None:
    chrome_version = get_chrome_version()

    print(f'Google Chrome version {chrome_version} detected.')

    os.chdir('bin')

    print(f'Downloading webdriver for Google Chrome version {chrome_version}...')

    chrome_driver_url = get_chrome_driver_url(chrome_version)

    with ZipFile(BytesIO(urlopen(chrome_driver_url).read())) as zip:
        zip.extractall()

    shutil.move('chromedriver-win64/chromedriver.exe', 'chromedriver.exe')
    shutil.rmtree('chromedriver-win64')

    print('Setup Completed.')


if __name__ == '__main__':
    main()
