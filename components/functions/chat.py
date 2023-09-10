from components.storages import scylla_models as s_models


def handle_create_new_participant(group_id, account_id) -> tuple[
    s_models.ChatParticipantByAccount, s_models.ChatParticipantByChatGroup]:

    new_participant_by_account = s_models.ChatParticipantByAccount.create(
        notify=True,
        id_account=account_id,
        id_chatgroup=group_id
    )
    new_participant_by_chat_group = s_models.ChatParticipantByChatGroup.create(
        notify=True,
        id_account=account_id,
        id_chatgroup=group_id
    )
    return new_participant_by_account, new_participant_by_chat_group


def handle_create_new_group(account_id_list):
    new_group = s_models.ChatGroup.create(name="Temporary")
    for account_id in account_id_list:
        handle_create_new_participant(new_group.id, account_id)
    return new_group
