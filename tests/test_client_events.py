from todus.client import ToDusClient


def test_client_dispatches_various_events():
    client = ToDusClient()
    seen = {
        "message": 0,
        "presence": 0,
        "iq": 0,
        "tdack": 0,
        "receipt": 0,
        "deleted": 0,
        "chat_state": 0,
    }

    @client.events.on("message")
    def on_msg(e):
        seen["message"] += 1

    @client.events.on("presence")
    def on_pres(e):
        seen["presence"] += 1

    @client.events.on("iq")
    def on_iq(e):
        seen["iq"] += 1

    @client.events.on("tdack")
    def on_td(e):
        seen["tdack"] += 1

    @client.events.on("receipt")
    def on_rc(e):
        seen["receipt"] += 1

    @client.events.on("deleted")
    def on_del(e):
        seen["deleted"] += 1

    @client.events.on("chat_state")
    def on_cs(e):
        seen["chat_state"] += 1

    # message with body -> should trigger message
    client.handle_parsed_stanza({"from": "1", "body": "hello"}, sock=None, callback=None)

    # presence
    client.handle_parsed_stanza({"from": "2", "status": "online"}, sock=None, callback=None)

    # iq
    client.handle_parsed_stanza({"from": "3", "query": "x"}, sock=None, callback=None)

    # tdack
    client.handle_parsed_stanza({"type": "tdack", "message_id": "m1"}, sock=None, callback=None)

    # receipt
    client.handle_parsed_stanza({"receipt": "m2", "receipt_type": "delivered"}, sock=None, callback=None)

    # deleted
    client.handle_parsed_stanza({"deleted": "m3"}, sock=None, callback=None)

    # chat_state
    client.handle_parsed_stanza({"chat_state": "composing"}, sock=None, callback=None)

    # message is dispatched for actual message, deleted and chat_state per implementation
    assert seen["message"] == 3
    assert seen["presence"] == 1
    assert seen["iq"] == 1
    assert seen["tdack"] == 1
    assert seen["receipt"] == 1
    assert seen["deleted"] == 1
    assert seen["chat_state"] == 1
