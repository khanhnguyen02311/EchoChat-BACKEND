from faker import Faker
import string
import random

faker = Faker()


def name():
    return faker.name()
    # return ''.join(random.choices(string.ascii_letters + string.digits, k=16))


def identifier():
    return random.randint(1, 9999)
