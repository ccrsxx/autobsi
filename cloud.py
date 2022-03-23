from src import get_from_heroku

source = (
    lambda x: f'''
import schedule

from src import (
    os,
    time,
    logging,
    get_from_heroku,
    attend_class,
    job,
)


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

    attend_class(get=get_from_heroku, mail=True, verbose=False, cloud=True)

    {x}

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    main()
'''
)


def main():
    timetable = get_from_heroku('timetable')

    class_schedule = []

    for day in timetable:
        item = timetable[day]
        start_time, _ = item['time']

        if isinstance(start_time, list):
            for i, (start_time, _) in enumerate(item['time']):
                class_schedule.append(
                    f'schedule.every().{day}.at(\'{start_time}\').do(job, \'{day}\', {i})'
                )
        else:
            class_schedule.append(
                f'schedule.every().{day}.at(\'{start_time}\').do(job, \'{day}\')'
            )

    with open('server.py', 'w') as f:
        f.write(source(';'.join(class_schedule)))


if __name__ == '__main__':
    main()
