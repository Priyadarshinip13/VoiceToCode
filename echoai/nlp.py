def get_bot_reply(user_input):
    if "time" in user_input:
        return "I am your voice clone. The current time is unknown to me, but I can help you code."
    return "You said: " + user_input
