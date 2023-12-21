import random
from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlalchemy import select
from components.data.schemas.scylla_schemas import GroupPOST
from components.functions.message import handle_add_new_message
from components.functions.security import handle_create_hash
from components.functions.group import handle_add_new_group, handle_add_new_participant
from components.data import PostgresSession, ScyllaSession
from components.data.models import postgres_models as p_models, scylla_models as s_models
from components.data.schemas import scylla_schemas as s_schemas
from configurations.conf import Env

router = APIRouter()


def generate():
    hashed_password = handle_create_hash("system_user_password")
    group = None
    with PostgresSession() as session:
        # 6000 system users
        for i in range(1, 6001):
            new_accountinfo = p_models.Accountinfo(name=f"System User No.{i}")
            session.add(new_accountinfo)
            session.flush()
            new_account = p_models.Account(username=f"system_user_{i}",
                                           email=f"system_user_{i}.email.com",
                                           password=hashed_password,
                                           accountinfo_id=new_accountinfo.id)
            session.add(new_account)
            session.flush()

            # 300 groups, each group has 20 participants
            if (i - 1) % 20 == 0:
                err, group = handle_add_new_group(GroupPOST(
                    name=f"System Group No.{(i - 1) // 20}",
                    description=f"Auto-generated group No.{(i - 1) // 20} for system users, using for testing purposes. Group owner: {new_account.id}",
                    visibility=True), new_accountinfo)
                if err is not None:
                    print("ERROR: ", err)
                    return
                print(f"{group.name} set up completely. Group owner: {new_account.id}")
                message_content = f"User {new_accountinfo.name} has created group."

            else:
                err, _ = handle_add_new_participant(group.id, new_accountinfo.id, accountinfo_name=new_accountinfo.name)
                if err is not None:
                    print("ERROR: ", err)
                    return
                message_content = f"User {new_accountinfo.name} joined group {group.name}."

            err, _ = handle_add_new_message(s_schemas.MessagePOST(group_id=group.id,
                                                                  accountinfo_id=new_accountinfo.id,
                                                                  group_name=group.name,
                                                                  accountinfo_name=new_accountinfo.name,
                                                                  type=s_models.CONSTANT.Message_type[2],
                                                                  content=message_content))
            if err is not None:
                print("ERROR: ", err)
        session.commit()
    print("Done")


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
def generate_testdata(background_task: BackgroundTasks):
    with PostgresSession() as session:
        existed_system_user = session.scalar(select(p_models.Account).where(p_models.Account.username == "system_user_1"))
        if existed_system_user is not None:
            raise HTTPException(status_code=400, detail="Test data already existed")
    background_task.add_task(generate)
    return "Generating test data on the background"
