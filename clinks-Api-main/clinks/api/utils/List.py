
def remove_duplicates(objects, key_to_compare):
    already_exist = {}
    for current_object in objects:
        if current_object[f"{key_to_compare}"] in already_exist.keys():
            objects.remove(current_object)
        else:
            already_exist[current_object[f"{key_to_compare}"]] = 1


def find(objects, key_to_compare, value_to_compare):

    from collections import OrderedDict

    for current_object in objects:
        is_dict = type(current_object) is dict or type(current_object) is OrderedDict
        value = current_object[f"{key_to_compare}"] if is_dict else f"{current_object}.{key_to_compare}"
        if value == value_to_compare:
            return current_object

    return None


def get_unique_item_ids(items):
    current_ids = {item['id']: item for item in items}
    ids = []

    for id in current_ids:
        if id not in ids:
            ids.append(id)

    return ids


def count_occurrence(list_, comparison_key):
    result = []
    for item in list_:
        found_item = next((x for x in result if x["item"][f"{comparison_key}"] == item[f"{comparison_key}"]), None)

        if found_item is None:
            result.append({
                "item": item,
                "occurrence": 1
            })
            continue
        found_item["occurrence"] += 1

    return result