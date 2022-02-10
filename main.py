from src import *


def main():
    os.chdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'src'))

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%H:%M:%S',
                        handlers=[
                            logging.FileHandler(os.path.join('logs', f'{datetime.now().strftime("%d %b")}.txt')),
                            logging.StreamHandler()
                        ]
                        )

    attend_class()

    '''
    schedule.every().monday.at('12:30').do(job, 'monday')
    schedule.every().tuesday.at('07:00').do(job, 'tuesday')
    schedule.every().wednesday.at('09:30').do(job, 'wednesday')
    schedule.every().thursday.at('15:00').do(job, 'thursday', 0)
    schedule.every().thursday.at('19:00').do(job, 'thursday', 1)

    while True:
        schedule.run_pending()
        time.sleep(1)
    '''


if __name__ == '__main__':
    main()
