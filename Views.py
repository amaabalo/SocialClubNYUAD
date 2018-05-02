import os
import IO
import string
import sys
from abc import ABCMeta, abstractmethod
from UserContext import User, Status
import time, threading

# Abstract Class
class Menu(object):
    __metaclass__ = ABCMeta
    def __init__(self, user, name, options, dismissable):
        self.name = name
        self.options = options
        self.current_option = 0
        self.dismissable = dismissable
        self.no_options = len(self.options) + 1 if self.dismissable else len(self.options)
        self.cancel = "CANCEL"
        self.dismissed = False
        self.user = user
        self.error_messages = []


    def display(self):
        rows, columns = os.popen('stty size', 'r').read().split()
        rows = int(rows)
        columns = int(columns)
        n_spaces = (columns - 2 - len(self.name))/2
        remainder = (columns - 2 - len(self.name))%2
        print('#' * columns)
        # print options
        print('#' + ' ' * n_spaces + self.name.upper() + ' ' * (n_spaces + remainder) + "#")
        for i, option in enumerate(self.options):
            n_spaces = (columns - 3 - len(option))
            if (i == self.current_option):
                print('#' + u'\u25b8' + IO.bcolors.OKBLUE + option + IO.bcolors.ENDC + ' ' * (n_spaces) + "#")
            else:
                print('#' + ' ' + option + ' ' * (n_spaces) + "#")
        #print dismiss option if enabled
        if (self.dismissable):
            n_spaces = (columns - 3 - len(self.cancel))
            if (self.current_option == len(self.options)):
                print('#' + u'\u25b8' + IO.bcolors.FAIL + self.cancel + IO.bcolors.ENDC + ' ' * (n_spaces) + "#")
            else:
                print('#' + ' ' + self.cancel + ' ' * (n_spaces) + "#")
        # print error messages
        print('#' + " "*(columns - 2) + '#')
        for error_message in self.error_messages:
            n_spaces = columns - 2 - len(" Error: ") - len(error_message)
            print('#' + IO.bcolors.FAIL + " Error: " + IO.bcolors.ENDC + error_message + ' ' * n_spaces + '#')
        # fill spaces
        for i in range(rows - 5 - len(self.options) - len(self.error_messages)) :
            print('#' + " "*(columns - 2) + '#');
        print('#' * columns)

    def add_error(self, error_message):
        self.error_messages.append(error_message)

    def start(self):
        while not self.dismissed:
            self.display()
            self.process_key()

    def process_key(self):
        while True:
            key = IO.get()
            if key == '\x1b[A' or key == '\x1b[D':
                self.current_option = (self.current_option - 1) % self.no_options
                break;
            elif key == '\x1b[B' or key == '\x1b[C':
                self.current_option = (self.current_option + 1) % self.no_options
                break;
            elif key == '\r':
                self.process_selection_()
                break;

    def process_selection_(self):
        if self.dismissable and self.current_option == len(self.options):
            self.dismissed = True;
        self.process_selection()

    @abstractmethod
    def process_selection(self):
        raise NotImplementedError('')

class WelcomeMenu(Menu):

    def __init__(self):
        super(WelcomeMenu, self).__init__(None, "Welcome", ["Log In", "Sign Up", "Exit"], False)

    def process_selection(self):
        if self.current_option == 0:
            log_in_form = LogInForm()
            responses = log_in_form.get_responses()
            if responses == None:
                return
            username, password = responses
            user = User()
            status = user.log_in(username, password)
            if status == Status.LOGIN_SUCCESS:
                home_menu = HomeMenu(user)
                home_menu.start()
            else:
                self.add_error("Could Not Log In - " + Status().error_string(status))
        elif self.current_option == 1:
            signUpForm = SignUpForm()
            responses = signUpForm.get_responses()
            if responses == None:
                return
            username, f_name, l_name, email, password, DOB = responses
            user = User()
            status = user.create_and_log_in(username, f_name, l_name, email, password, DOB)
            if status == Status.CREATE_LOG_IN_SUCCESS:
                home_menu = HomeMenu(user)
                home_menu.start()
            else:
                self.add_error("Could Not Log In - " + Status().error_string(status))

        elif self.current_option == 2:
            sys.exit(0)

class HomeMenu(Menu):

    def __init__(self, user):
        super(HomeMenu, self).__init__(user, "Dashboard",\
                                          ["Friends",\
                                          "Messaging",\
                                          "Analytics",\
                                          "Log Out",\
                                          "Delete Account"],\
                                          False)
    def process_selection(self):
        if (self.current_option == 3):
            self.user.log_out()
            self.dismissed = True


# Abstract Class
# Concrete classes must implement validate function
class Form(object):
    __metaclass__ = ABCMeta
    # name = the name of the form, will be displayed at the top of the view
    # fields = List of strings denoting each fields
    # submit = String to be displayed for submit button
    # multiline_fields = List of indices of fields which will be multilined, all others will be single lined
    def __init__(self, name, fields, submit, multiline_fields = None):
        self.name = name
        self.fields = fields
        self.current_selection = 0
        self.no_options = len(self.fields) + 2 # fields, submit, and cancel
        self.responses = ['' for i in range(len(fields))]
        self.submit = submit
        self.cancel = 'CANCEL'
        self.submitted = False
        self.error_messages = []
        self.multiline_fields = multiline_fields
        self.num_rows_printed = 0
        self.cursor = u'\u258d'
        self.pointer = u'\u25b8'


    def print_with_indent(self, indentation, text):
        if (text == ''):
            return 0
        if (text[0] == '\n'):
            text = text[1:]
        rows, columns = os.popen('stty size', 'r').read().split()
        columns = int(columns)
        n_lines_printed = 0
        text_width = columns - indentation - 2
        lines = text.split('\n')
        for line in lines:
            while True:
                line_to_print = '#' + ' ' * (indentation - 1)
                line_to_print += line[0:text_width]
                n_spaces = columns - len(line_to_print) - 2
                line_to_print += (" " * n_spaces) + " #"
                print(line_to_print)
                n_lines_printed += 1
                line = line[text_width:]
                if (line == ''):
                    break
        return n_lines_printed


    def print_multiline(self, columns, field, text, highlighted, bulleted,
                        editing, highlight_color = IO.bcolors.OKBLUE,
                        bullet = None, separator = ": "):
        n_lines_printed = 0
        if (bullet == None):
            bullet = self.pointer

        if not bulleted:
            bullet = ' '

        if highlighted:
            line = "#" + bullet + highlight_color + field + IO.bcolors.ENDC + separator
            indentation = len(line) - len(highlight_color) - len(IO.bcolors.ENDC)
        else:
            line = "#" + bullet + field + separator
            indentation = len(line)

        if editing:
            text += self.cursor
        # print the first line
        text_width = indentation + 2 # ends with a ' #'
        #text_width = len(line) + 2 # ends with a ' #'
        word_start_index = 0
        current_word_index = 0
        first_new_line = text.find('\n', 0)
        space_remaining = max(0, columns - text_width)

        if (first_new_line == -1):
            first_new_line = space_remaining
        stop = min(first_new_line, space_remaining)
        to_append = text[0 : stop]
        line += to_append
        n_spaces = columns - len(line) - 2
        if highlighted:
            n_spaces += (len(highlight_color) + len(IO.bcolors.ENDC))
        line += ' ' * n_spaces
        line += " #"
        print(line)
        n_lines_printed += 1
        text = text[stop : ]
        n_lines_printed += self.print_with_indent(indentation, text)
        return n_lines_printed


    def print_single_line(self, columns, field, text, highlighted, bulleted,
                          editing, highlight_color = IO.bcolors.OKBLUE,
                          bullet = None, separator = ": "):

        if (bullet == None):
            bullet = self.pointer

        cols_available_for_response = columns - len('#' + bullet + field + separator + " #")
        if not bulleted:
            bullet = ' '

        if highlighted:
            field = highlight_color + field + IO.bcolors.ENDC

        start = '#' + bullet + field + separator

        if editing:
            text_to_print = text[max(0, len(text) - (cols_available_for_response - 1)): len(text)]
            text_to_print += self.cursor
        else:
            text_to_print = text[0: (cols_available_for_response)]

        n_spaces = cols_available_for_response - len(text_to_print)
        print(start + text_to_print + ' ' * (n_spaces) + " #")

        return 1


    def get_rows_columns(self):
        rows, columns = os.popen('stty size', 'r').read().split()
        rows = int(rows)
        columns = int(columns)
        return (rows, columns)


    def print_horizontal_bar(self, columns):
        print('#' * columns)
        return 1

    def print_centered(self, columns, string):
        n_spaces = (columns - 2 - len(string))/2
        remainder = (columns - 2 - len(string))%2
        print('#' + ' ' * n_spaces + string + ' ' * (n_spaces + remainder) + "#")
        return 1

    def is_multiline_field(self, index):
        if self.multiline_fields == None:
            return False
        return index in self.multiline_fields

    def display_multiline_field (self, columns, field, response, selected):
        return self.print_multiline(columns, field, response, selected, selected, selected)

    def display_single_line_field (self, columns, field, response, selected):
        return self.print_single_line(columns, field, response, selected, selected, selected)

    def display_error_message (self, columns, error_message):
        return self.print_multiline(columns, "Error", error_message, True, False,
                                    False, highlight_color = IO.bcolors.FAIL)


    def display_all_fields(self, columns):
        n_rows_printed = 0
        for i, option in enumerate(self.fields):
            if self.is_multiline_field(i):
                n_rows_printed += self.display_multiline_field(columns, option, self.responses[i], i == self.current_selection)
            else:
                n_rows_printed += self.display_single_line_field(columns, option, self.responses[i], i == self.current_selection)
        return n_rows_printed


    def display_submit_button(self, columns):
        n_spaces = (columns - 3 - len(self.submit))
        if (self.current_selection == len(self.fields)):
            print('#' + u'\u25b8' + IO.bcolors.OKGREEN + self.submit + IO.bcolors.ENDC + ' ' * (n_spaces) + "#")
        else:
            print('#' + ' ' + self.submit + ' ' * (n_spaces) + "#")
        return 1


    def display_cancel_option(self, columns):
        n_spaces = (columns - 3 - len(self.cancel))
        if (self.current_selection == len(self.fields) + 1):
            print('#' + u'\u25b8' + IO.bcolors.FAIL + self.cancel + IO.bcolors.ENDC + ' ' * (n_spaces) + "#")
        else:
            print('#' + ' ' + self.cancel + ' ' * (n_spaces) + "#")
        return 1


    def print_empty_space(self, columns):
        print('#' + " "*(columns - 2) + '#')
        return 1


    def display_error_messages(self, columns):
        n_rows_printed = self.print_empty_space(columns)
        for error_message in self.error_messages:
            n_rows_printed += self.display_error_message(columns, error_message)
        return n_rows_printed


    def fill_empty_space(self, rows, columns, num_rows_printed):
        remainder = num_rows_printed % (rows - 1)
        to_fill = (rows - 1) - remainder
        for i in range(to_fill - 1):
            print('#' + " "*(columns - 2) + '#')
        print('#' * columns)


    def display(self):
        rows, columns = self.get_rows_columns()
        num_rows_printed = 0
        num_rows_printed += self.print_horizontal_bar(columns)
        num_rows_printed += self.print_centered(columns, self.name.upper())
        num_rows_printed += self.display_all_fields(columns)
        num_rows_printed += self.display_submit_button(columns)
        num_rows_printed += self.display_cancel_option(columns)
        num_rows_printed += self.display_error_messages(columns)
        self.fill_empty_space(rows, columns, num_rows_printed)


    def get_responses(self):
        while not self.submitted:
            self.display()
            self.process_key()
        return self.responses

    def process_key(self):
        while True:
            key = IO.get()
            if key == '\x1b[A' or key == '\x1b[D':
                self.current_selection = (self.current_selection - 1) % self.no_options
                break
            elif key == '\x1b[B' or key == '\x1b[C':
                self.current_selection = (self.current_selection + 1) % self.no_options
                break
            elif key == '\t':
                self.current_selection = (self.current_selection + 1) % self.no_options # can use tab to move down
                break
            elif key == '\r': # enter
                if self.is_multiline_field(self.current_selection):
                    self.responses[self.current_selection] += '\n'
                    break
                if self.current_selection == len(self.fields): # submit button
                    self.process_submission_()
                    break
                elif self.current_selection == len(self.fields) + 1: # cancel button
                    self.submitted = True
                    self.responses = None
                    break
            elif self.current_selection < len(self.fields):
                if key == '\x7f': # backspace
                    str_len = len(self.responses[self.current_selection])
                    self.responses[self.current_selection] = self.responses[self.current_selection][0 : str_len - 1]
                    break;
                elif key in string.printable:
                    self.responses[self.current_selection] += key
                    break;

    def process_submission_(self):
        self.error_messages = []
        isValid = self.validate()
        if isValid:
            self.submitted = True

    def add_error(self, error_message):
        self.error_messages.append(error_message)

    # Should return true if responses are valid, false otherwise
    # In the case of in valid input, any errors recorded using
    # addError() will be displayed.
    @abstractmethod
    def validate(self):
        raise NotImplementedError('')

# getResponses will return a list of strings
# [Username, First Name, Last Name, Email, Password]
class SignUpForm(Form):
    def __init__(self):
        super(SignUpForm, self).__init__("Sign Up",\
                                        ["Username",\
                                         "First Name",\
                                         "Last Name",\
                                         "Email",\
                                         "Password",\
                                         "Date of Birth (YYYY-MM-DD)"],\
                                         "Join the Club!",\
                                         multiline_fields = [])

    def validate(self):
        isValid = True
        # no empty fields
        for i,field in enumerate(self.fields):
            if self.responses[i] == '':
                self.add_error("'" + field + "' cannot be empty.")
                isValid = False

        return isValid

# getResponses will return a list of strings
# [Username, Password]
class LogInForm(Form):
    def __init__(self):
        super(LogInForm, self).__init__("Log In", ["Username", "Password"], "Log In")

    def validate(self):
        isValid = True
        for i,field in enumerate(self.fields):
            if self.responses[i] == '':
                self.add_error("'" + field + "' cannot be empty.")
                isValid = False
        return isValid
