import csv
import os
from datetime import datetime, timedelta

from post import read_post_file, Post
from utility import debug, post_file_name, error, out, warn, build_post_key


def find_item_blurred(orig_dt, a_timedelta, data, post_id):
    """
    Blurry search within -3 .. +3 seconds
    :param orig_dt:
    :param a_timedelta:
    :param data:
    :param post_id:
    :return:
    """
    for s in [0, 1, -1, 2, -2, 3, -3]:
        dt = orig_dt + timedelta(seconds=s) + a_timedelta
        if build_post_key(dt) in data:
            debug(f"Found sidecar item with {dt} for {post_id}")
            return data[build_post_key(dt)]

    return None


def find_item_by_key(data, post):
    """
    Key must not match the item's key exactly. It can differ within 2 hours
    :return: Item, if found or None
    """
    dt = post.get_datetime()

    # Normal case
    if build_post_key(dt) in data:
        return data[build_post_key(dt)]

    for s in [0, 1, -1, 2, -2, 3, -3, 4, -4]:
        ret = find_item_blurred(post.get_datetime(), timedelta(hours=s), data, post.get_dir())
        if ret is not None:
            return ret

    return None


def add_sidecar_data(post, data, devices):
    """
    Add attributes from sidecar, if found
    :param devices: dict with HUGO devices
    :param post: Post object
    :param data: Dictionary with the sidecar data
    :return: true if added, otherwise false
    """

    # debug(f"date {data}")
    debug(f"opened post {post.get_dir()}")
    item = find_item_by_key(data, post)

    if item is None:
        warn(f"Key {post.get_dir()} not found in sidecar")
        return False

    debug(f"item={item}")

    materials = get_material_list(item, devices)

    set_category(post, item)

    set_or_remove(len(item['Kommentar']) > 0, post, Post.DESCRIPTION, item['Kommentar'])

    set_or_remove(len(map_device(materials)) > 0, post, Post.DEVICE, map_device(materials))

    set_or_remove_sport(Post.DEVICE in post.data, post, devices)

    set_topic(post, item)

    set_or_remove( len(map_utensils(materials)) > 0, post, Post.UTENSILS, map_utensils(materials))

    post.save()

    return True


def set_or_remove_sport(switch, post, devices):
    """
    Set or remove sport value from data dictionary in the post object
    :param switch: If true, value will be set, otherwise removed
    :param post: Object
    :param devices: All devices
    """
    key = Post.SPORT
    if switch:
        value = map_sport(post.data[Post.DEVICE], devices)
        post.data[key] = value
    else:
        if key in post.data:
            post.data.remove(key)


def set_category(post, item):
    """
    Set category
    :param post: Object
    :param item: Actual item
    """
    sportart = item['Sportart'].lower()

    if sportart == 'laufsport':
        post.data[Post.CATEGORY] = Post.CATEGORY_RUNNING
    elif sportart == 'radsport':
        post.data[Post.CATEGORY] = Post.CATEGORY_CYCLING
    elif sportart == 'mountainbike':
        post.data[Post.CATEGORY] = Post.CATEGORY_CYCLING
    elif sportart == 'fitness':
        post.data[Post.CATEGORY] = Post.CATEGORY_GYM
    elif sportart == 'wandern':
        post.data[Post.CATEGORY] = Post.CATEGORY_HIKING
    else:
        post.data[Post.CATEGORY] = Post.CATEGORY_OTHERS

    if item['Kommentar'].lower().startswith("die runde stunde"):
        post.data[Post.TOPIC] = Post.TOPIC_DIE_RUNDE_STUNDE
    else:
        post.data[Post.TOPIC] = item['Trainingsart'].lower()


def set_topic(post, item):
    """
    Set topic
    :param post: Object
    :param item: Actual item
    """
    if item['Kommentar'].lower().startswith("die runde stunde"):
        post.data[Post.TOPIC] = Post.TOPIC_DIE_RUNDE_STUNDE

    else:
        post.data[Post.TOPIC] = item['Trainingsart'].lower()


def set_or_remove(switch, post, key, value):
    """
    Set or remove value from data dictionary in the post object
    :param switch: If true, value will be set, otherwise removed
    :param post: Object
    :param key: Key
    :param value: Value
    """
    if switch:
        post.data[key] = value
    else:
        if key in post.data:
            post.data.remove(key)


def map_sport(device, devices):
    """
    Get the sport for an existing device. Device must exists in devices
    :param device: Item from devices
    :param devices: dict
    :return: String with sport, can be empty
    """
    if len(device) == 0:
        return ""

    # debug(f"map sport from {devices[device]}")
    return devices[device][Post.SPORT]


def get_material_list(item, devices):
    """
    Parse materials string and extract a list with materials. Every material must match an HUGO device,
    otherwise error will be executed.
    :param devices: Hugo devices
    :param item: actual item from velohero csv
    :return: List with material names, e.g. ["focus-mtb"}
    """
    ret = []
    for mat in item['Material'].split(","):
        name = mat.strip().replace(" ", "-").lower()
        if len(name) == 0:
            continue

        if name not in devices:
            error(f"Missing device directory for '{name}'")

        ret.append(name)

    return ret


def map_utensils(materials):
    """
    Get following material, if available
    :param materials: list with checked materials, can be empty
    :return: converted list with device names, e.g. TACX R--> trek-rad. Can be an empty string
    """
    if len(materials) < 1:
        return ""

    return ", ".join(materials[1:])


def map_device(materials):
    """
    Get (first) material, if available
    :param materials: list with checked materials, can be empty
    :return: device name, e.g. "trek-rad"
    """
    if len(materials) == 0:
        return ""

    return materials[0]


def read_sidecar(sidecar_file):
    """
    Opens the csv file and return an dict of items with date time string as key
    :param sidecar_file:
    :return:
    """

    if not os.path.exists(sidecar_file):
        error(f"Sidecar file not found: {sidecar_file}")

    ret = dict()
    with open(sidecar_file, newline='') as f:
        reader = csv.DictReader(f, delimiter=';')

        for r in reader:
            date = datetime.strptime(r['Datum'], "%Y-%m-%d").strftime("%Y%m%d")
            time = datetime.strptime(r['Startzeit'], "%H:%M:%S").strftime("%H%M%S")
            key = f"{date}-{time}"
            ret[key] = r

        debug(f"Read {len(ret)} sidecar items")
        return ret
