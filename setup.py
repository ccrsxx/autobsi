import os
import platform

from win32api import GetFileVersionInfo, HIWORD
from urllib.request import urlopen
from zipfile import ZipFile
from io import BytesIO

CHROME_PATHS = [
    os.path.join(os.getenv(path), 'Google\Chrome\Application\Chrome.exe')
    for path in ('ProgramFiles', 'ProgramFiles(x86)', 'LocalAppData')
]

DRIVER_URLS = {
    ver.split('.')[
        0
    ]: f'https://chromedriver.storage.googleapis.com/{ver}/chromedriver_win32.zip'
    for ver in (
        '90.0.4430.24',
        '91.0.4472.101',
        '92.0.4515.43',
        '93.0.4577.63',
        '94.0.4606.113',
        '95.0.4638.69',
        '96.0.4664.45',
        '97.0.4692.20',
        '98.0.4758.80',
        '99.0.4844.17',
        '100.0.4896.60',
        '101.0.4951.15',
        '102.0.5005.27',
        '103.0.5060.134',
        '104.0.5112.79',
        '105.0.5195.19',
    )
}


def main():
    if platform.system() != 'Windows':
        print('This setup is only for Windows!')
        return

    no_chrome = True

    print('Checking If Google Chrome is installed...')

    for chrome_path in CHROME_PATHS:
        if os.path.exists(chrome_path):
            no_chrome = False
            chrome_version = HIWORD(
                GetFileVersionInfo(chrome_path, '\\')['FileVersionMS']
            )

    if no_chrome:
        print('Google Chrome is not installed.')
        return

    if chrome_version < 90:
        print('Google Chrome must be at least at version 90 or higher.')
        return

    print(f'Google Chrome version {chrome_version} detected.')

    os.chdir('bin')

    print(f'Downloading webdriver for Google Chrome version {chrome_version}...')

    with ZipFile(BytesIO(urlopen(DRIVER_URLS[str(chrome_version)]).read())) as zip:
        zip.extractall()

    print('Setup Completed.')


if __name__ == '__main__':
    main()
