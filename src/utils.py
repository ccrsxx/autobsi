from .autobsi import Union


def get_elapsed_time(seconds: Union[int, float]):
    template = {
        'hours': 0,
        'minutes': 0,
        'seconds': 0,
    }

    seconds = round(seconds)

    minutes = seconds // 60

    template['minutes'] = minutes

    if minutes > 60:
        template['hours'] = minutes // 60
        template['minutes'] = minutes % 60

    template['seconds'] = seconds % 60

    output_time = []

    for key, value in template.items():
        if value:
            output_time.append(f'{value} {key}')

    if len(output_time) == 3:
        return f'{", ".join(output_time[:-1])} and {output_time[-1]}'

    return ' and '.join(output_time)
