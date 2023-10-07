from components.storages import scylla_models as s_models


def handle_create_new_participant(group_id, account_id) -> tuple[
    s_models.ParticipantByAccount, s_models.ParticipantByGroup]:

    new_participant_by_account = s_models.ParticipantByAccount.create(
        notify=True,
        id_account=account_id,
        id_chatgroup=group_id
    )
    new_participant_by_chat_group = s_models.ParticipantByGroup.create(
        notify=True,
        id_account=account_id,
        id_chatgroup=group_id
    )
    return new_participant_by_account, new_participant_by_chat_group


def handle_create_new_group(account_id_list):
    new_group = s_models.Group.create(name="Temporary")
    for account_id in account_id_list:
        handle_create_new_participant(new_group.id, account_id)
    return new_group


def handle_get_participants_by_account(account_id):
    return s_models.ParticipantByAccount.objects.filter(id_account=account_id).all()


def handle_get_participants_by_group(group_id):
    return s_models.ParticipantByGroup.objects.filter(id_chatgroup=group_id).all()


def handle_get_participant_by_account_and_group(account_id, group_id):
    valid_participant = s_models.ParticipantByAccount.objects \
        .filter(id_account=account_id) \
        .filter(id_chatgroup=group_id) \
        .first()
    return valid_participant


def handle_add_message(account_id, group_id, content):
    valid_participant = handle_get_participant_by_account_and_group(account_id, group_id)
    if valid_participant is not None:
        new_message = s_models.MessageByGroup.create(text=content,
                                                     id_chatgroup=group_id,
                                                     id_chatparticipant=valid_participant.id)
        return new_message
    return None
