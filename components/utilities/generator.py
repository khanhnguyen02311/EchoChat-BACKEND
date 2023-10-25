import string
import random


def random_name():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))


def random_identifier():
    return random.randint(1, 9999)
