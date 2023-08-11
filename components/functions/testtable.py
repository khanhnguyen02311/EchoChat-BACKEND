import random
from . import FunctionException
from sqlalchemy import select

from components.storages import Session
from components.storages.postgres_models import TestingTable


def handle_setup_testing_table():
    """Create the TestingTable with random attributes. Return error if needed"""

    random_names = ['apple', 'pear', 'banana', 'melon', 'peas', 'orange', 'peach',
                    'cherry', 'strawberry', 'lemon', 'coconut', 'mango']

    with Session.begin() as session:
        try:
            for i in range(50):
                item = random.choice(random_names)
                optional_item = random.choice(random_names) if random.choice([True, False]) else None
                number = random.randint(1, 10)
                session.add(TestingTable(item=item, optional_item=optional_item, number=number))
            session.commit()

        except Exception as e:
            session.rollback()
            raise FunctionException(handle_setup_testing_table.__name__, e)


def test_query():
    """Test SQLAlchemy query functions"""

    with Session.begin() as session:
        try:
            execute_rows = session.execute(select(TestingTable).where(TestingTable.id <= 5)).all()
            scalars_rows = session.scalars(select(TestingTable).where(TestingTable.id <= 5)).all()
            scalar_row = session.scalar(select(TestingTable).where(TestingTable.id <= 5))
            print(execute_rows)
            print(scalars_rows)
            print(scalar_row)

        except Exception as e:
            raise FunctionException(test_query.__name__, e)

        session.close()
