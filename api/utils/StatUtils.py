from datetime import timedelta


def sort_list_multi(stats_list, today, max_date, value_keys):
    stat_value_data = {}

    for key in value_keys:
        stat_value_data[key] = 0

    if len(stats_list) == 0:
        stats_list.append({'date': today, **stat_value_data})
        stats_list.append({'date': max_date,  **stat_value_data})

    if stats_list[0]["date"] != today:
        stats_list.insert(0, {
            'date': today,
            **stat_value_data
        })

    if stats_list[len(stats_list) - 1]["date"] != max_date:
        stats_list.append({
            'date': max_date,
            **stat_value_data
        })

    return _prepare_multi(stats_list,  value_keys)


def _prepare_multi(array, value_keys):
    if len(array) > 1:
        array = _sort(array)
        array = _fill_daily_multi(array, value_keys)

    return array


def _sort(array):
    return sorted(
        array,
        key=lambda x: x['date'], reverse=True
    )


def _fill_daily_multi(array, value_keys):

    start_date = array[len(array) - 1]['date']
    end_date = array[0]['date']

    days_no = (end_date - start_date).days  # how many days between?

    filled_array = []
    for i in range(days_no + 1):
        date = start_date + timedelta(days=i)

        stat_value_data = {}

        for key in value_keys:
            stat_value_data[key] = 0

        filled_array.append({
            "date": date,
            **stat_value_data
        })

    for i, entry in enumerate(array, start=0):
        for j, data in enumerate(filled_array, start=0):
            if entry["date"] == data["date"]:
                for key in value_keys:
                    data[key] = entry[key]

    return filled_array
