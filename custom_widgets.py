from asciimatics.widgets import Frame, ListBox, Layout, Divider, Text, \
    Button, TextBox, Widget, _split_text
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
from asciimatics.event import KeyboardEvent, MouseEvent
import sys
import math

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

class DialogueList(ListBox):

    def __init__(self, height, dialogues, label=None, name=None, on_change=None):
        """
        :param height: The required number of input lines for this ListBox.
        :param label: An optional label for the widget.
        :param name: The name for the ListBox.
        :param on_change: Optional function to call when selection changes.
        """
        super(DialogueList, self).__init__(height, dialogues, label, name, on_change)
        self._dialogues = dialogues
        self._label = label
        self._line = 0
        self._dialogue = 0
        self._start_line = 0
        self._required_height = height
        self._on_change = on_change

    def update(self, frame_no):
        self._draw_label()

        # Calculate new visible limits if needed.
        width = self._w - self._offset
        height = self._h
        dx = dy = 1

        # Clear out the existing box content
        (colour, attr, bg) = self._frame.palette["field"]
        for i in range(height):
            self._frame.canvas.print_at(
                " " * width,
                self._x + self._offset + dx,
                self._y + i + dy,
                colour, attr, bg)

        # Don't bother with anything else if there are no options to render.
        if not self._dialogues or len(self._dialogues) <= 0:
            return

        # Render visible portion of the text.
        self._start_line = max(0, max(self._dialogue - height + 1,
                                      min(self._start_line, self._dialogue)))

        margin_h = 0
        margin_w = 1

        dialogue_strs = []
        for i, dialogue in enumerate(self._dialogues):
        #create dialogue template
            components = [ [ "{0.from_name}", "{0.readable_time}" ], [ "{0.body}", "{0.read_state}" ] ]
            lines = []
            for line in components:
                line[0] = line[0].format(dialogue)
                line[1] = line[1].format(dialogue)
                l_len = len(line[0])
                r_len = len(line[1])
                amount_of_spaces = width - margin_w - l_len - r_len - margin_w - 1
                dialogue_str = " "*margin_w + line[0] + " "*amount_of_spaces + line[1] + " "*margin_w
                lines.append(dialogue_str)
            dialogue_strs.append(lines)

                #patrition N messages into K pages of fixed height

        pages = []
        cur_page = 0
        cur_height = 0
        page_ind = 0
        for i, dial_lines in enumerate(dialogue_strs):
            dial_h = len(dial_lines)
            if cur_height+dial_h >= height:
                cur_page += 1
                cur_height = 0

            if cur_page > len(pages)-1:
                pages.append([])
            pages[cur_page].append([dial_lines, i])
            cur_height += dial_h
            if i == self._dialogue:
                page_ind = cur_page

        total_height = 0
        for i, (dial_lines, dial_number) in enumerate(pages[page_ind]):
            colour, attr, bg = self._pick_colours("field", dial_number == self._dialogue)
            for j, line in enumerate(dial_lines):
                xpos = self._x + self._offset + dx
                ypos = self._y + j +total_height+ dy - self._start_line
                if ypos < height:
                    self._frame.canvas.print_at(
                        "{:{width}}".format(line, width=width),
                        xpos,
                        ypos,
                        colour, attr, bg)
            total_height += len(dial_lines)

    def process_event(self, event):
        if not self._dialogues:
            return
        if isinstance(event, KeyboardEvent):
            if len(self._dialogues) > 0 and event.key_code == Screen.KEY_UP:
                # Move up one line in text - use value to trigger on_select.
                self._dialogue = max(0, self._dialogue - 1)
                self.value = self._dialogues[self._dialogue]

            elif len(self._dialogues) > 0 and event.key_code == Screen.KEY_DOWN:
                # Move down one line in text - use value to trigger on_select.
                self._dialogue = min(len(self._dialogues) - 1, self._dialogue + 1)
                self.value = self._dialogues[self._dialogue]
            else:
                # Ignore any other key press.
                return event
        elif isinstance(event, MouseEvent):
            # Mouse event - rebase coordinates to Frame context.
            new_event = self._frame.rebase_event(event)
            if event.buttons != 0:
                if (len(self._dialogues) > 0 and
                        self.is_mouse_over(new_event, include_label=False)):
                    # Use property to trigger events.
                    #self._dialogue = min(new_event.y - self._y,
                    #                 len(self._dialogues) - 1)
                    #dial = math.floor((new_event.y - self._y)/len(self._dialogues)-1)
                    dial = math.floor((new_event.y - self._y)/len(self._dialogues))
                    if dial > len(self._dialogues)-1:
                        #self._dialogue = len(self._dialogues)-1
                        pass
                    elif dial < 0:
                        #self._dialogue = 0
                        pass
                    else:
                        self._dialogue = dial


                    self.value = self._dialogues[self._dialogue]
                    return
            # Ignore other mouse events.
            return event
        else:
            # Ignore other events
            return event

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        # Only trigger notification after we've changed selection
        if self._dialogues:
            old_value = self._value
            self._value = new_value
            for i, dialogue in enumerate(self._dialogues):
                if dialogue == new_value:
                    self._dialogue = i
                    break
            else:
                self._value = None
                self._dialogue = -1
            if old_value != self._value and self._on_change:
                self._on_change()

    def reset(self):
        # Reset selection - use value to trigger on_select
        if self._dialogues and len(self._dialogues) > 0:
            self._dialogue = 0
            #with open("debug.txt", "w") as f:
                #f.write(str(self._dialogues))
            self.value = self._dialogues[self._dialogue]
        else:
            self._dialogue = -1
            self.value = None

    @property
    def dialogues(self):
        """
        The list of dialogues available for user selection - this is a list of
        tuples (<human readable string>, <internal value>).
        """
        return self._dialogues

    @dialogues.setter
    def dialogues(self, new_value):
        self._dialogues = new_value
        self.value = self._dialogues[0] if len(self._dialogues) > 0 else None


class MessageList(ListBox):

    def __init__(self, height, messages, client_user, label=None, name=None, on_change=None):
        """
        :param height: The required number of input lines for this ListBox.
        :param label: An optional label for the widget.
        :param name: The name for the ListBox.
        :param on_change: Optional function to call when selection changes.
        """
        super(MessageList, self).__init__(height, [], label, name, on_change)
        self._messages = messages
        self._label = label
        self._line = 0
        self._message = 0
        self._start_line = 0
        self._required_height = height
        self._on_change = on_change
        self.client_user = client_user

    def update(self, frame_no):
        self._draw_label()

        # Calculate new visible limits if needed.
        width = self._w - self._offset
        height = self._h
        dx = dy = 1

        # Clear out the existing box content
        (colour, attr, bg) = self._frame.palette["field"]
        for i in range(height):
            self._frame.canvas.print_at(
                " " * width,
                self._x + self._offset + dx,
                self._y + i + dy,
                colour, attr, bg)

        # Don't bother with anything else if there are no options to render.
        if not self._messages or len(self._messages) <= 0:
            return

        # Render visible portion of the text.
        self._start_line = max(0, max(self._message - height + 1,
                                      min(self._start_line, self._message)))

        margin_h = 0
        margin_w = 1
        total_height = 0

        message_strs = [] #[ [msg_lines] ]
        for i, message in enumerate(self._messages):
            if self._start_line <= i < self._start_line + height:
                
            #create message template

                lines = []
                msg_text = _split_text(message.text.strip(), width, height) + ['']
                components = ["{0.from_name}", "{0.datetime}"]
                components[0] = components[0].format(message)
                components[1] = components[1].format(message)
                r_len = len(components[0])
                l_len = len(components[1])
                amount_of_spaces = width - margin_w - l_len - r_len - margin_w - 1
                msg_str = " "*margin_w + components[0] + " "*amount_of_spaces + components[1] + " "*margin_w
                lines.append(msg_str)
                lines = lines + msg_text
                message_strs.append(lines)
                total_height += len(lines)

        #patrition N messages into K pages of fixed height

        pages = []
        cur_page = 0
        cur_height = 0
        page_ind = 0
        for i, msg_lines in enumerate(message_strs):
            msg_h = len(msg_lines)
            if cur_height+msg_h >= height:
                cur_page += 1
                cur_height = 0

            if cur_page > len(pages)-1:
                pages.append([])
            pages[cur_page].append([msg_lines, i])
            cur_height += msg_h
            if i == self._message:
                page_ind = cur_page

        total_height = 0
        msg_num = 0
        for i, (msg_lines, msg_number) in enumerate(pages[page_ind]):
            colour, attr, bg = self._pick_colours("field", msg_number == self._message)
            for j, line in enumerate(msg_lines):
                xpos = self._x + self._offset + dx
                ypos = self._y + j +total_height+ dy - self._start_line

                if ypos < height:
                    self._frame.canvas.print_at(
                        "{:{width}}".format(line, width=width),
                        xpos,
                        ypos,
                        colour, attr, bg)
            total_height += len(msg_lines)





        # for j, line in enumerate(lines):
        #     xpos = self._x + self._offset + dx
        #     ypos = self._y + total_height + j  + dy - self._start_line

        #     if ypos < height:
        #         self._frame.canvas.print_at(
        #             "{:{width}}".format(line, width=width),
        #             xpos,
        #             ypos,
        #             colour, attr, bg)



    def process_event(self, event):
        if not self._messages:
            return
        if isinstance(event, KeyboardEvent):
            if len(self._messages) > 0 and event.key_code == Screen.KEY_UP:
                # Move up one line in text - use value to trigger on_select.
                self._message = max(0, self._message - 1)
                self.value = self._messages[self._message]
            elif len(self._messages) > 0 and event.key_code == Screen.KEY_DOWN:
                # Move down one line in text - use value to trigger on_select.
                self._message = min(len(self._messages) - 1, self._message + 1)
                self.value = self._messages[self._message]
            else:
                # Ignore any other key press.
                return event
        elif isinstance(event, MouseEvent):
            # Mouse event - rebase coordinates to Frame context.
            new_event = self._frame.rebase_event(event)
            if event.buttons != 0:
                if (len(self._messages) > 0 and
                        self.is_mouse_over(new_event, include_label=False)):
                    # Use property to trigger events.
                    #self._dialogue = min(new_event.y - self._y,
                    #                 len(self._messages) - 1)
                    #dial = math.floor((new_event.y - self._y)/len(self._messages)-1)
                    msg = math.floor((new_event.y - self._y)/len(self._messages))
                    if msg > len(self._messages)-1:
                        #self._dialogue = len(self._dialogues)-1
                        pass
                    elif msg < 0:
                        #self._dialogue = 0
                        pass
                    else:
                        self._message = msg


                    self.value = self._messages[self._message]
                    return
            # Ignore other mouse events.
            return event
        else:
            # Ignore other events
            return event

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        if self._messages:
            # Only trigger notification after we've changed selection
            old_value = self._value
            self._value = new_value
            for i, message in enumerate(self._messages):
                if message == new_value:
                    self._message = i
                    break
            else:
                self._value = None
                self._message = -1
            if old_value != self._value and self._on_change:
                self._on_change()

    def reset(self):
        if self._messages:
            # Reset selection - use value to trigger on_select
            if len(self._messages) > 0:
                self._message = 0
                self.value = self._messages[self._message]
            else:
                self._message = -1
                self.value = None


    @property
    def messages(self):
        """
        The list of messages available for user selection - this is a list of
        tuples (<human readable string>, <internal value>).
        """
        return self._messages

    @messages.setter
    def messages(self, new_value):
        self._messages = new_value
        self.value = self._messages[0] if len(self._messages) > 0 else None

