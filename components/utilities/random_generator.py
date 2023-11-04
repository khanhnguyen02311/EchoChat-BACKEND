import string
import random


def name():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))


def identifier():
    return random.randint(1, 9999)
