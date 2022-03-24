import schedule

from src import os, time, logging, get_from_config, attend_class, job


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        datefmt='%H:%M:%S',
        handlers=[
            logging.FileHandler(os.path.join('logs', 'temp.txt')),
            logging.StreamHandler(),
        ],
    )

    setup = {
        'get': get_from_config,
        'mail': False,
        'verbose': False,
        'cloud': False,
    }

    attend_class(**setup)

    '''
    schedule.every().monday.at('12:30').do(job, 'monday', None, **setup)
    schedule.every().tuesday.at('07:00').do(job, 'tuesday', None, **setup)
    schedule.every().wednesday.at('09:30').do(job, 'wednesday', None, **setup)
    schedule.every().thursday.at('15:00').do(job, 'thursday', 0, **setup)
    schedule.every().thursday.at('19:00').do(job, 'thursday', 1, **setup)

    while True:
        schedule.run_pending()
        time.sleep(1)
    '''


if __name__ == '__main__':
    main()
