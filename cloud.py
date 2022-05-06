from src import Callable, get_from_heroku, write_cloud_function


def write_schedule(
    get: Callable,
    mail: bool,
    verbose: bool,
    cloud: bool,
):
    setup = ', '.join(map(str, [get.__name__, mail, verbose, cloud]))

    attend_function = f'attend_class({setup})'

    timetable = get('timetable')

    class_schedule = []

    for day in timetable:
        item = timetable[day]
        start_time, _ = item['time']

        if isinstance(start_time, list):
            for i, (start_time, _) in enumerate(item['time']):
                class_schedule.append(
                    f"schedule.every().{day}.at('{start_time}').do(job, '{day}', {i}, {setup})"
                )
        else:
            class_schedule.append(
                f"schedule.every().{day}.at('{start_time}').do(job, '{day}', None, {setup})"
            )

    with open('server.py', 'w') as f:
        f.write(
            write_cloud_function(
                get.__name__, attend_function, ';'.join(class_schedule)
            )
        )


def main():
    setup = {
        'get': get_from_heroku,
        'mail': True,
        'verbose': False,
        'cloud': True,
    }

    write_schedule(**setup)


if __name__ == '__main__':
    main()
