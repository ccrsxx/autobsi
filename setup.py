import os
import sys
from win32api import GetFileVersionInfo, HIWORD
from urllib.request import urlopen
from zipfile import ZipFile
from io import BytesIO

def main():
    CHROME_PATHS = [
        os.path.join(os.environ['ProgramFiles'], 'Google\Chrome\Application\Chrome.exe'),
        os.path.join(os.environ['ProgramFiles(x86)'], 'Google\Chrome\Application\Chrome.exe'),
        os.path.join(os.environ['LocalAppData'], 'Google\Chrome\Application\Chrome.exe')
    ]

    DRIVER_URLS = {
        90: 'https://chromedriver.storage.googleapis.com/90.0.4430.24/chromedriver_win32.zip',
        91: 'https://chromedriver.storage.googleapis.com/91.0.4472.101/chromedriver_win32.zip',
        92: 'https://chromedriver.storage.googleapis.com/92.0.4515.43/chromedriver_win32.zip',
        93: 'https://chromedriver.storage.googleapis.com/93.0.4577.63/chromedriver_win32.zip',
        94: 'https://chromedriver.storage.googleapis.com/94.0.4606.113/chromedriver_win32.zip',
        95: 'https://chromedriver.storage.googleapis.com/95.0.4638.69/chromedriver_win32.zip',
        96: 'https://chromedriver.storage.googleapis.com/96.0.4664.45/chromedriver_win32.zip',
        97: 'https://chromedriver.storage.googleapis.com/97.0.4692.20/chromedriver_win32.zip',
    }

    no_chrome = True

    print('Checking needed folder...')
    for folder in ['logs', 'screenshots']:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f'Created {folder}')
    print('Checking folder done.')

    for chrome_path in CHROME_PATHS:
        if os.path.exists(chrome_path):
            no_chrome = False
            chrome_version = HIWORD(GetFileVersionInfo(chrome_path, '\\')['FileVersionMS'])

    if no_chrome:
        return print('Google Chrome is not installed.')

    if chrome_version < 90:
        return print('Google Chrome must be at least at version 90 or higher.')

    os.chdir(os.path.join(os.path.dirname(sys.executable), 'Scripts'))

    print(f'Downloading webdriver for Google Chrome {chrome_version}...')

    with ZipFile(BytesIO(urlopen(DRIVER_URLS[chrome_version]).read())) as zip:
        zip.extractall()

    print('Setup Completed.')


if __name__ == '__main__':
    main()
