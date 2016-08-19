from asciimatics.widgets import Frame, ListBox, Layout, Divider, Text, \
    Button, TextBox, Widget
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
from custom_widgets import DialogueList, MessageList
import sys

class Dialogue:
    def __init__(self, dialogue_id, body, from_name, unread_msgs, datetime, messages = []):
        self.dialogue_id = dialogue_id
        self.body = body
        self.from_name = from_name
        self.unread_msgs = unread_msgs
        self.datetime = datetime
        self.messages = messages

class Message:
    def __init__(self, message_id, text, from_name, unread, datetime):
        self.message_id = message_id
        self.text = text
        self.from_name = from_name
        self.unread = unread
        self.datetime = datetime

Message(101, "Hello, I am john", "john",False, "18.08.16 10:15")

def format_dialogue_text(dialogue):
    sender = dialogue["from"]
    unread = dialogue["unread"]
    body = dialogue["body"]

    template = """{0} {1} : {2}"""

    return template.format("!!!" if unread else "", sender, body)

def format_msg_text(message):
    sender = message["from"]
    date = message["date"]
    text = message["text"]

    template = """{0} : {1} | {2}"""

    return template.format(sender, text, date)


class MessengerView(Frame):

    palette = {
        "background":
            (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK),
        "shadow":
            (Screen.COLOUR_BLACK, None, Screen.COLOUR_BLACK),
        "disabled":
            (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLACK),
        "label":
            (Screen.COLOUR_GREEN, Screen.A_BOLD, Screen.COLOUR_BLACK),
        "borders":
            (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLACK),
        "scroll":
            (Screen.COLOUR_CYAN, Screen.A_NORMAL, Screen.COLOUR_BLACK),
        "title":
            (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK),
        "edit_text":
            (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK),
        "focus_edit_text":
            (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_CYAN),
        "button":
            (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK),
        "focus_button":
            (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_CYAN),
        "control":
            (Screen.COLOUR_YELLOW, Screen.A_NORMAL, Screen.COLOUR_BLACK),
        "selected_control":
            (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLACK),
        "focus_control":
            (Screen.COLOUR_YELLOW, Screen.A_NORMAL, Screen.COLOUR_BLACK),
        "selected_focus_control":
            (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_CYAN),
        "field":
            (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK),
        "selected_field":
            (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLACK),
        "focus_field":
            (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK),
        "selected_focus_field":
            (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_CYAN),
    }

    def __init__(self, screen):
        super(MessengerView, self).__init__(screen,
                                       screen.height,
                                       screen.width,
                                       hover_focus=True,
                                       title="Messenger")
        # Create the form for displaying the list of dialogues.
        base_height = 24
        self._dialogue_list = DialogueList(base_height, [ ],name="dialogues", on_change=self._on_pick_dialogue)
        self._messages_list = MessageList(base_height, [ ],app.user_id,name="messages")
        layout = Layout([55, 100])
        self.add_layout(layout)
        layout.add_widget(self._dialogue_list, 0)
        layout.add_widget(Divider())
        layout.add_widget(self._messages_list, 1)
        bottom_layout = Layout([100])
        self.add_layout(bottom_layout)
        bottom_layout.add_widget(Divider())
        bottom_layout.add_widget(Text("Command:", "main_input"))
        self._dialogue_list.dialogues = test_data["dialogues"]
        self.fix()

    def _on_pick_dialogue(self):
        #create text options for ListBox from dialogue messages
        if self._dialogue_list.value:
            app.current_dialogue = self._dialogue_list.value
            self._messages_list.messages = self._dialogue_list.value.messages


class App():
    def __init__(self, vk_api, user_id, token):
        self.vk_api = vk_api
        self.user_id = user_id
        self.token = token

        #1 screen
        self.screen = None
        #1 scene
        self.messenger_scene = None
        #3 frames
        self.dialogs_frame = None
        self.dialogue_frame = None

        self.current_dialogue = None

    def run(self, screen):
        self.screen = screen
        self.messenger_scene = Scene([MessengerView(screen)], -1, name="Dialogues")
        self.screen.play([self.messenger_scene], stop_on_resize=True, start_scene=self.messenger_scene)


user_id = "0000"
vk_api = object()
token = ""


test_data = {
    "dialogues": [
        Dialogue(1, "Hello, I am john", "john","2","18.08.16 10:15", [
            Message(101, "Hey", user_id,False, "18.08.16 10:11"),
            Message(102, "Hello, I am john", "john",False, "18.08.16 10:15"),
        ]),
        Dialogue(2, "Wassup", "alex","2","18.08.16 11:15", [
            Message(103, "Just testing", user_id,False, "18.08.16 11:11"),
            Message(104, "Wassup", "alex",False, "18.08.16 11:15"),
        ])
    ]
}



app = App(vk_api, user_id, token)
while True:
    Screen.wrapper(app.run)
    sys.exit(0)

