from time import sleep

from fastapi import APIRouter, BackgroundTasks
from components.data.schemas.scylla_schemas import GroupPOST
from components.functions.message import handle_add_new_message
from components.functions.security import handle_create_hash
from components.functions.group import handle_add_new_group, handle_add_new_participant
from components.data import PostgresSession, ScyllaSession, RedisSession, Engine
from components.data.models import postgres_models as p_models, scylla_models as s_models
from components.data.schemas import scylla_schemas as s_schemas
from configurations.conf import Env, Scylla

router = APIRouter()


def reset():
    p_models.Base.metadata.drop_all(Engine)
    p_models.Base.metadata.create_all(Engine)

    RedisSession.flushdb()

    ScyllaSession.execute(f"DROP KEYSPACE IF EXISTS {Scylla.DB_KEYSPACE}")
    ScyllaSession.execute(
        f"CREATE KEYSPACE IF NOT EXISTS {Scylla.DB_KEYSPACE} WITH replication = " +
        f"{{'class': 'NetworkTopologyStrategy', 'replication_factor': {Scylla.DB_REPLICATION_FACTOR}}}")
    ScyllaSession.execute(f"USE {Scylla.DB_KEYSPACE}")
    s_models.sync_tables()

    print("Done")


def generate(start_from: int, amount: int):
    hashed_password = handle_create_hash("system_user_password")
    start = 1
    with PostgresSession() as session:
        # 6000 system users
        for i in range(start_from, start_from + amount):
            if (i - 1) % 20 == 0:
                start = i
            new_accountinfo = p_models.Accountinfo(name=f"System User No.{i}")
            session.add(new_accountinfo)
            session.flush()
            new_account = p_models.Account(username=f"system_user_{i}",
                                           email=f"system_user_{i}.email.com",
                                           password=hashed_password,
                                           accountinfo_id=new_accountinfo.id)
            session.add(new_account)
            session.flush()

            # each user is creator of 1 group, and participant of 19 more groups
            err, group = handle_add_new_group(GroupPOST(
                name=f"System Group No.{i}",
                description=f"Auto-generated group No.{i} for system users, using for testing purposes. Group owner: {new_accountinfo.name}",
                visibility=True), new_accountinfo)
            if err is not None:
                print("ERROR: ", err)
                return
            print(f"{group.name} set up completely. Group owner: {new_account.id}")
            message_content = f"User {new_accountinfo.name} has created group."

            err, _ = handle_add_new_message(s_schemas.MessagePOST(group_id=group.id,
                                                                  accountinfo_id=new_accountinfo.id,
                                                                  group_name=group.name,
                                                                  accountinfo_name=new_accountinfo.name,
                                                                  type=s_models.CONSTANT.Message_type[2],
                                                                  content=message_content))
            if err is not None:
                print("ERROR: ", err)

            for j in range(start, start + 20):
                if j == i:
                    continue
                err, _ = handle_add_new_participant(group.id, j, accountinfo_name=f"System User No.{j}")
                if err is not None:
                    print("ERROR: ", err)
                    return
                message_content = f"User System User No.{j} joined group {group.name}."

                err, _ = handle_add_new_message(s_schemas.MessagePOST(group_id=group.id,
                                                                      accountinfo_id=j,
                                                                      group_name=group.name,
                                                                      accountinfo_name=f"System User No.{j}",
                                                                      type=s_models.CONSTANT.Message_type[2],
                                                                      content=message_content))
                if err is not None:
                    print("ERROR: ", err)

                sleep(0.1)

        session.commit()
    print("Done")


def custom_execution():
    pass


@router.get("/info")
def application_info():
    scylla_mains = ScyllaSession.execute(
        "SELECT rack, schema_version, host_id, rpc_address, data_center FROM system.local").all()
    scylla_peers = ScyllaSession.execute(
        "SELECT rack, schema_version, host_id, rpc_address, data_center FROM system.peers").all()
    return {
        "app": "EchoChat",
        "stage": Env.APP_STAGE,
        "debug": Env.APP_DEBUG,
        "scylla": {
            "main_nodes": scylla_mains,
            "peer_nodes": scylla_peers,
        },
    }


@router.get("/generate-testdata")
def generate_testdata(background_task: BackgroundTasks, start_from: int, amount: int):
    # with PostgresSession() as session:
    #     existed_system_user = session.scalar(select(p_models.Account).where(p_models.Account.username == "system_user_1"))
    #     if existed_system_user is not None:
    #         raise HTTPException(status_code=400, detail="Test data already existed")
    background_task.add_task(generate, start_from, amount)
    return "Generating test data on the background"


@router.get("/reset-databases")
def reset_databases(background_task: BackgroundTasks):
    background_task.add_task(reset)
    return "Resetting databases on the background"


@router.get("/custom-request")
def custom_request(background_task: BackgroundTasks):
    background_task.add_task(custom_execution)
    return "Custom request on the background"
