import vk
import os  
import re
import hashlib
import time 
from interface import GUI, SwitchDialogue
import datetime 
import math
import threading
import atexit


vk_app_id = "5591268"
UPDATE_PERIOD = 3

def parse_vk_uri(uri):
    token = re.compile(r'(token=)(\w+)')
    user_id = re.compile(r'(user_id=)(\w+)')
    #secret = re.compile(r'(secret=)(\w+)')
    return token.search(uri).group(2), user_id.search(uri).group(2)#, secret.search(uri).group(2),

def vk_login(app_id):
    auth_link = make_auth_link(app_id)
    print("Auth link:\n{0}".format(auth_link))
    response_uri = input("Enter the uri from browser:")
    return parse_vk_uri(response_uri)
#api = vk_login(vk_app_id, vk_secret_key, vk_user_login, vk_user_password)


def make_auth_link(app_id):
    base = "https://oauth.vk.com/authorize?client_id={0}&redirect_uri=https://oauth.vk.com/blank.html&scope=offline, messages&response_type=token"
    params = {
    "client_id":app_id,
    }

    return base.format(params["client_id"])
    #https://oauth.vk.com/authorize?client_id=1&display=page&redirect_uri=http://example.com/callback&scope=friends&response_type=token&v=5.53&state=123456



#print(make_auth_link(vk_app_id))
#my_link
#https://oauth.vk.com/blank.html#access_token=41cb7b47eccbc013031688d03949cb5a6d2b81aedfe51dfb3c573eff3853a5503b97605e8f811a5bd1a3e&expires_in=0&user_id=43447713
def create_sig(method, params, secret):

    params = params
    request = "/method/{0}?{1}".format(method, params)
    print(request+secret)
    return hashlib.md5(request+secret).hexdigest()


"""

example dialogue from vk

{'read_state': 1, 'mid': 1176444, 'out': 0, 'date': 1472050604, 'title': ' ... ', 'uid': 231793188, 'body': '×åðòèë'}
{'read_state': 1, 'mid': 1174454, 'body': 'Åíòî êàê õî÷åøü', 'title': ' ... ', 'uid': 144248502, 'out': 0, 'date': 1471104886}]
"""
class Dialogue:
    def __init__(self, dialogue_id, body, from_user_id, read_state, date, from_name=None):
        self.dialogue_id = dialogue_id
        self.body = body
        self.from_user_id = from_user_id
        self.read_state = read_state
        self.date = date
        self.from_name = from_name


    @property
    def readable_time(self):
        show_date = False
        if datetime.datetime.today().date() == self.date.date():
            return self.date.strftime('%H:%M')
        else:
            return self.date.strftime('%d.%m.%y %H:%M')

"""
example msg
{'uid': 43447713, 'date': 1398681688, 'read_state': 1, 'mid': 945033, 'body': 'да', 'from_id': 43447713, 'out': 1}
"""
class Message:
    def __init__(self, message_id,  body, from_user_id, read_state, date, out, from_name=None):
        self.message_id = message_id
        self.body = body
        self.from_user_id = from_user_id
        self.read_state = read_state
        self.date = date
        self.out = out
        self.from_name = from_name



class App():
    def __init__(self, vk_api=None, user_id=None, token=None):
        self.vk_api = vk_api
        self.user_id = user_id
        self.token = token

        self.gui = None

        self._dialogues = None
        self._messages = None

        #todo remove
        self.messages = None
        self.current_dialogue = None

        self.dialogue_timer = None
        self.message_timer = None

        self.stop = False

    @property
    def dialogues(self):
        return self._dialogues

    @dialogues.setter
    def dialogues(self, new_value):
        if new_value:
            
            # Only trigger notification after we've changed selection
            new_value.sort(key=lambda x: x.date, reverse=True)
            self._dialogues = new_value
            if not self.current_dialogue:
                self.current_dialogue = self._dialogues[0]
            


    def run(self):

        file_exists = os.path.isfile('./token.txt')
        if file_exists:
            with open('token.txt') as f:
                token, user_id = f.read().strip().split('\n')
        else:
            token, user_id = vk_login(vk_app_id)

        #login to vk
        #if login is succesful write token down to file
        session = vk.Session(token)
        api = vk.API(session)
        #print(api.users.get(user_ids=1, sig = create_sig("users/get", "user_ids=1&access_token="+token, secret)))
        assert(api.users.get(user_ids=1) != None)

        with open('token.txt', 'w+') as f:
            f.write(token +'\n' +user_id)


        self.vk_api = api
        self.user_id = user_id
        self.token = token

        self.gui = GUI(self)
        self.main_loop()

    def get_dialogues(self):
        temp_dialogues = self.vk_api.messages.getDialogs()[1:]
        # with open("debug.txt", "w", encoding='utf-8') as f:
        #     f.write(str(temp_dialogues)+'\n'+str('')+'\n' )
        # assert(False)

        dialogues = []
        for d in temp_dialogues:
            if "chat_id" in d.keys():
                #its a chat
                dialogue = Dialogue(d["mid"], d["body"], d["uid"], d["read_state"], datetime.datetime.fromtimestamp(int(d['date'])),d["title"])
            else:
                dialogue = Dialogue(d["mid"], d["body"], d["uid"], d["read_state"], datetime.datetime.fromtimestamp(int(d['date'])))
            dialogues.append(dialogue)


        user_ids = [d.from_user_id for d in dialogues if d.from_name == None]
        users = self.vk_api.users.get(user_ids=user_ids)
        #names = [u['first_name'] + ' ' + u['last_name'] for u in users]
        uid_to_names = {}
        for u in users:
            uid_to_names[str(u["uid"])] = u['first_name'] + ' ' + u['last_name']

        
            
        for d in dialogues:
            if str(d.from_user_id) in uid_to_names.keys():
                d.from_name = uid_to_names[str(d.from_user_id)]
            #dialogues[i].from_name = names[i]
        
        return dialogues

"""
example msg
{'uid': 43447713, 'date': 1398681688, 'read_state': 1, 'mid': 945033, 'body': 'да', 'from_id': 43447713, 'out': 1}

class Message:
    def __init__(self, message_id,  body, from_user_id, read_state, date, out, from_name=None):
        """



    def get_messages(self):
        if self.current_dialogue:
            raw_messages = self.vk_api.messages.getHistory(user_id=str(self.current_dialogue.from_user_id))[1:]
            with open('debug.txt', 'w', encoding="utf-8") as f:
                f.write(str(raw_messages))

            messages = []
            
            for msg in raw_messages:
                message = Message(msg["uid"], msg["body"], msg["from_id"], msg["read_state"], msg["date"], msg["out"])
                messages.append(message)


            assert(False)

        return messages

    def poll_messages(self):
        if not self.stop:
            self.messages = self.get_messages()
            self.gui.update_messages(self.messages)
            self.message_timer = threading.Timer(UPDATE_PERIOD, self.poll_messages)
            self.message_timer.start()

    def poll_dialogues(self):
        if not self.stop:
            self.dialogues = self.get_dialogues()
            self.gui.update_dialogues(self.dialogues)
            self.dialogue_timer = threading.Timer(UPDATE_PERIOD, self.poll_dialogues)
            self.dialogue_timer.start()

    def main_loop(self):
        while True:
            # with open('debug.txt', 'a') as f:
            #     f.write("tick"+'\n')
            #     f.write(str(int(time.clock()))+'\n')
            #     f.write(str(int(time.clock()) % UPDATE_PERIOD)+'\n')
            # if int(time.clock()) % UPDATE_PERIOD == 0:
            #     
            #     #self.messages = self.get_messages(self.current_dialogue)
            # self.dialogue_timer = threading.Timer(UPDATE_PERIOD, self.poll_dialogues)
            # self.dialogue_timer.daemon = True
            # self.dialogue_timer.start()
            self.poll_dialogues()
            self.poll_messages()
            try:
                self.gui.tick()
                sys.exit(0)
            except SwitchDialogue as e:
                self.current_dialogue = e.dialogue
                raise(Exception("inactive till messages are implemented"))
                    #self.messages = self.get_messages()

    def cleanup(self):
        if self.dialogue_timer:
            self.dialogue_timer.cancel()
            #sys.exit(0)


app = App()

try:
    app.run()
except Exception as e:
    app.stop = True
    raise(e)

atexit.register(app.cleanup)

"""

Dialogs example:

response: {
count: 886,
items: [{
message: {
id: 1176628,
date: 1472121481,
out: 1,
user_id: 55581920,
read_state: 1,
title: ' ... ',
body: 'но кодить?',
random_id: -341847832
},
in_read: 1176627,
out_read: 1176628
}, {
message: {
id: 1176555,
date: 1472114579,
out: 0,
user_id: 132536763,
read_state: 1,
title: ' ... ',
body: 'Нуок) справедливо'
},
in_read: 1176555,
out_read: 1176554
}]


"""

"""messages example

response: {
count: 398,
items: [{
id: 1680163,
body: 'test message',
user_id: 2314852,
from_id: 2314852,
date: 1468343751,
read_state: 1,
out: 0
}],
in_read: 1680163,
out_read: 1680162
}
"""