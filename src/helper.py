import os

from operator import itemgetter

from typing import Callable, TypedDict, Any


def write_schedule(get_function: str, attend_function: str, class_schedule: str) -> str:
    return f'''
import os
import time
import logging
import schedule

from src import {get_function}, attend_class, job


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

    {attend_function}

    {class_schedule}

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    main()
'''


class Setup(TypedDict):
    get: Callable[[str], Any]
    mail: bool
    verbose: bool
    cloud: bool


def write_entry_point(setup: Setup) -> None:
    get, mail, verbose, cloud = itemgetter('get', 'mail', 'verbose', 'cloud')(setup)

    setup_config = ', '.join(map(str, [get.__name__, mail, verbose, cloud]))

    attend_function = f'attend_class({setup_config})'

    timetable = get('timetable')

    class_schedule = []

    every_day_check = (
        f"schedule.every().day.at('06:00').do(attend_class, {setup_config})"
    )

    class_schedule.append(every_day_check)

    for day in timetable:
        item = timetable[day]
        start_time, _ = item['time']

        if isinstance(start_time, list):
            for i, (start_time, _) in enumerate(item['time']):
                class_schedule.append(
                    f"schedule.every().{day}.at('{start_time}').do(job, '{day}', {i}, {setup_config})"
                )
        else:
            class_schedule.append(
                f"schedule.every().{day}.at('{start_time}').do(job, '{day}', None, {setup_config})"
            )

    with open('server.py', 'w') as f:
        f.write(write_schedule(get.__name__, attend_function, ';'.join(class_schedule)))

    os.system('python server.py')
