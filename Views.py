import os
import IO
import string
import sys
from abc import ABCMeta, abstractmethod
from UserContext import User, Status, DatabaseHelper, Request
import time, threading
from datetime import datetime, date
import re

# Abstract Class
# Must implement process_selection
class Menu(object):
    __metaclass__ = ABCMeta
    # user = User object can be None
    # name = title to be displayed at the top of the menu
    # options = list of options to be displayed on the menu
    # options_title = title to be displayed before options
    # dismissable = whether the menu can be dismissed or not. If dismissable = False,
    # the menu can still be dismissed by setting self.dismissed = True in
    # process_selection
    def __init__(self, user, name, options, dismissable = True, options_title = ''):
        self.name = name
        self.options = options
        self.current_option = 0
        self.dismissable = dismissable
        self.no_options = len(self.options) + 1 if self.dismissable else len(self.options)
        self.cancel = "CANCEL"
        self.dismissed = False
        self.user = user
        self.error_messages = []
        self.notifications = []
        self.options_title = options_title
        self.pointer = u'\u25b8'
        self.cursor = u'\u258d'


    def print_horizontal_bar(self, columns):
        print('#' * columns)
        return 1

    def print_centered(self, columns, string, highlight_color = None):
        n_spaces = (columns - 2 - len(string))/2
        remainder = (columns - 2 - len(string))%2
        if highlight_color:
            print('#' + ' ' * n_spaces + highlight_color + string + IO.bcolors.ENDC + ' ' * (n_spaces + remainder) + "#")
        else:
            print('#' + ' ' * n_spaces + string + ' ' * (n_spaces + remainder) + "#")
        return 1

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


    def print_empty_space(self, columns):
        print('#' + " "*(columns - 2) + '#')
        return 1

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

    def display_notification (self, columns, error_message):
        return self.print_multiline(columns, "NOTIFICATION", error_message, True, False,
                                    False, highlight_color = IO.bcolors.OKBLUE)

    def display_notifications(self, columns):
        n_rows_printed = 0
        if self.notifications:
            n_rows_printed = self.print_empty_space(columns)
        for notification in self.notifications:
            n_rows_printed += self.display_notification(columns, notification)
        if self.notifications:
            n_rows_printed += self.print_empty_space(columns)
            n_rows_printed += self.print_horizontal_bar(columns)
        return n_rows_printed

    def display_string_option(self, columns, option, selected):
        return self.print_single_line(columns, option, '', selected, selected, False, separator = '')

    def display_user_instance(self, columns, user, selected):
        n_rows_printed = 0
        # print the name
        name = (user.f_name + " " +  user.l_name).upper() + " ~ " + user.user_id + " ~ "
        n_rows_printed += self.print_single_line(columns, name, '', selected, selected, False, separator = '')
        # print username and email address
        #n_rows_printed += self.print_single_line(columns, "Username", user.user_id, False, False, False)
        n_rows_printed += self.print_single_line(columns, "Email", user.email, False, False, False)
        n_rows_printed += self.print_empty_space(columns)
        return n_rows_printed

    def display_request_instance(self, columns, request, selected):
        n_rows_printed = 0
        # print the name and message
        title = (request.requester_f_name + " " +  request.requester_l_name).upper()
        if request.group_id:
            title += " wants to join " + request.group_name
        n_rows_printed += self.print_multiline(columns, title, request.message, selected, selected, False)
        n_rows_printed += self.print_empty_space(columns)
        return n_rows_printed

    def display_all_options(self, columns):
        n_rows_printed = 0
        for i, option in enumerate(self.options):
            selected = i == self.current_option
            if (isinstance(option, str)):
                n_rows_printed += self.display_string_option(columns, option, selected)
            elif (isinstance(option, User)):
                n_rows_printed += self.display_user_instance(columns, option, selected)
            elif (isinstance(option, Request)):
                n_rows_printed += self.display_request_instance(columns, option, selected)
        return n_rows_printed


    def display_string_options(self, columns):
        for i, option in enumerate(self.options):
            n_spaces = (columns - 3 - len(option))
            if (i == self.current_option):
                print('#' + u'\u25b8' + IO.bcolors.OKBLUE + option + IO.bcolors.ENDC + ' ' * (n_spaces) + "#")
            else:
                print('#' + ' ' + option + ' ' * (n_spaces) + "#")

    def display_dismiss_option(self, columns):
        if (self.dismissable):
            return self.print_single_line(columns, self.cancel, '', self.current_option == len(self.options),
                                        self.current_option == len(self.options),
                                        False, highlight_color = IO.bcolors.FAIL, separator = '')
        return 0

    def display_error_message (self, columns, error_message):
            return self.print_multiline(columns, "Error", error_message, True, False,
                                        False, highlight_color = IO.bcolors.FAIL)

    def display_error_messages(self, columns):
        n_rows_printed = self.print_empty_space(columns)
        for error_message in self.error_messages:
            n_rows_printed += self.display_error_message(columns, error_message)
        return n_rows_printed


    def fill_empty_space(self, rows, columns, num_rows_printed):
        remainder = num_rows_printed % (rows - 1)
        to_fill = (rows - 1) - remainder
        num_rows_printed = 0
        for i in range(to_fill - 1):
            num_rows_printed += self.print_empty_space(columns)
        num_rows_printed += self.print_horizontal_bar(columns)
        return num_rows_printed

    def display_screen_title(self, columns):
        return self.print_centered(columns, self.name.upper())

    def display_options_title(self, columns):
        if self.options_title:
            return self.print_centered(columns, self.options_title)
        return 0

    def display(self):
        rows, columns = self.get_rows_columns()
        num_rows_printed = 0
        num_rows_printed += self.print_horizontal_bar(columns)
        num_rows_printed += self.display_screen_title(columns)
        num_rows_printed += self.print_horizontal_bar(columns)
        num_rows_printed += self.display_notifications(columns)
        num_rows_printed += self.display_options_title(columns)
        num_rows_printed += self.display_all_options(columns)
        num_rows_printed += self.display_dismiss_option(columns)
        num_rows_printed += self.display_error_messages(columns)
        num_rows_printed += self.fill_empty_space(rows, columns, num_rows_printed)

    # Use this to add an errror which will be displayed, e.g.
    # self.add_error("Username does not exist")
    def add_error(self, error_message):
        self.error_messages.append(error_message)

    # Use this to add a notification which will be displayed
    def add_notification(self, notification):
        self.notifications.append(notification)

    # Call this function after instantiation of a concrete class
    # to display the menu.
    def start(self):
        while not self.dismissed:
            self.display()
            self.process_key()
        self.on_dismiss()

    def process_key(self):
        while True:
            key = IO.get()
            if key == '\x1b[A' or key == '\x1b[D':
                self.current_option = (self.current_option - 1) % self.no_options
                break;
            elif key == '\x1b[B' or key == '\x1b[C' or key == '\t':
                self.current_option = (self.current_option + 1) % self.no_options
                break;
            elif key == '\r':
                self.process_selection_()
                break;

    def process_selection_(self):
        self.error_messages = []
        self. notifications = []
        if self.dismissable and self.current_option == len(self.options):
            self.on_dismiss()
            self.dismissed = True;
        self.process_selection()

    # function that can be overridden to do something just before dismissing
    def on_dismiss(self):
        pass

    # here, check the index of the currently selected item using
    # self.current option, process accordingly. If dismissable = False
    @abstractmethod
    def process_selection(self):
        raise NotImplementedError('')

class WelcomeMenu(Menu):

    def __init__(self):
        super(WelcomeMenu, self).__init__(None, "Welcome", ["Log In", "Sign Up", "Exit"], dismissable = False)

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
            username, f_name, l_name, email, password, verified_password, DOB = responses
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
        super(HomeMenu, self).__init__(user, user.f_name + "'s Dashboard",\
                                          ["Friends",\
                                          "Messaging",\
                                          "Analytics",\
                                          "Log Out",\
                                          "Delete Account"],\
                                          dismissable = False)
    def process_selection(self):
        if (self.current_option == 0):
            friends_menu = FriendsMenu(self.user)
            friends_menu.start()
            return
        elif self.current_option == 1: #Messaging
            MessagingMenu(self.user).start()
            return
        elif self.current_option == 2: #Analytics
			AnalyticsMenu(self.user).start()
			return
        elif (self.current_option == 3):
            self.user.log_out()
            self.dismissed = True
        elif (self.current_option == 4):
            db_helper = DatabaseHelper.get_instance()
            db_result = db_helper.drop_user(self.user.user_id)
            self.user.log_out()
            self.dismissed = True

class AnalyticsMenu(Menu):
	def __init__(self, user):
		super(AnalyticsMenu, self).__init__(user, "Analytics",\
											["3Degrees",\
											 "Top k users for past x days"],\
											 True)
		self.db_helper = DatabaseHelper.get_instance()

	def process_selection(self):
		if self.current_option == 0: #3degrees
			res = SearchFor3DegreesForm().get_responses()
			if res == None:
				return
			user1, user2 = res
			db_helper = DatabaseHelper.get_instance()
			db_result = db_helper.three_degrees(user1, user2)
			
			self.add_notification("Result: "+str(db_result))
		elif self.current_option == 1: #Top-k
			res = SearchForTopKForm().get_responses()
			if res == None:
				return
			user1, user2 = res
			db_helper = DatabaseHelper.get_instance()
			db_result = db_helper.topUsers(user1, user2)
			self.add_notification("Result: "+str(db_result))
			return

class FriendsMenu(Menu):
    def __init__(self, user):
        super(FriendsMenu, self).__init__(user, "Friends",\
                                          ["Search for someone",\
                                          "Send a friend request",\
                                          "Confirm friend requests",\
                                          "Send a group join request",\
                                          "Confirm group requests",\
                                          "Create a group",\
                                          "Display friends"],\
                                          True)
        self.db_helper = DatabaseHelper.get_instance()

    def process_selection(self):
        if self.current_option == 0: # searching for someone
            res = SearchForUserForm().get_responses()
            if res == None:
                return
            keyword, = res
            db_helper = DatabaseHelper.get_instance()
            users_found = User.get_user_objects(db_helper.search_for_user(keyword))
            UserSearchResultsMenu(users_found).start()
            return
        if self.current_option == 1: # sending a friend request
            res = WhichFriendForm(self.user).get_responses()
            if not res:
                return
            friends_username, = res
            first_name, last_name = self.db_helper.get_names_from_user_id(friends_username)
            res = SendFriendRequestForm(first_name).get_responses()
            if not res:
                return
            message, = res
            name = first_name + " " + last_name
            if self.user.send_friend_request_to(friends_username, message):
                self.add_notification("Friend request sent to " + name + "!")
            else:
                self.add_error("Failed to send friend request to " + name + ".")
            return
        if self.current_option == 3: # sending a group join request
            res = WhichGroupForm(self.user).get_responses()
            if not res:
                return
            group_id, = res
            group_name = self.db_helper.get_group_name_from_group_id(group_id)
            res = SendGroupJoinRequestForm(group_name).get_responses()
            if not res:
                return
            message, = res
            if self.user.send_group_join_request_to(group_id, message):
                self.add_notification("Successfully requested to join " + group_name + ".")
            else:
                self.add_error("Request to join " + group_name + " failed.")

        if self.current_option == 2: # confirming friend requests
            pending_friend_requests = self.user.get_pending_friend_requests()
            ConfirmRequestsMenu(self.user, pending_friend_requests).start()
            return
        if self.current_option == 4: # confirming group requests
            pending_group_requests = self.user.get_pending_group_join_requests()
            ConfirmRequestsMenu(self.user, pending_group_requests).start()
            return
        if self.current_option == 5: # creating a new group
            res = CreateGroupForm().get_responses()
            if not res:
                return
            group_id, group_name, limit, description = res
            if not self.user.create_new_group(group_id, group_name, limit, description):
                self.add_error("Could not create group.")
                return
            self.add_notification("Success! You are now the manager of your new group, " + group_name + ".")
            return
        if self.current_option == 6: #displaying friends
            friends = self.user.get_friends()
            DisplayFriendsMenu(friends).start()
            return

class MessagingMenu(Menu):
    def __init__(self, user):
        super(MessagingMenu, self).__init__(user, "Messaging",\
                                          ["Message a Friend",\
                                          "Message a Group",\
										  "Display New Messages",\
										  "Display Messages"],\
                                          dismissable = True)
    def process_selection(self):
        if self.current_option == 0: # Message a friend
            friends = self.user.get_friends()
            recipient = SelectRecipientMenu(friends).start()
            if not recipient:
                return
            res = SendMessageForm(recipient).get_responses()
            if not res:
                return
            message, = res
            if not self.user.send_message_to(recipient.user_id, message):
                self.add_error("Could not send message to " + recipient.f_name + " " + recipient.l_name + ".")
            else:
                self.add_notification("Success! Your message to " + recipient.f_name + " " + recipient.l_name + " has been sent.")
            return
        elif self.current_option == 1: # Message a group
			res = MessageGroupForm().get_responses()
			if res == None:
				return
			groupID, message = res
			db_helper = DatabaseHelper.get_instance()
			db_result = db_helper.send_group_message_to(self.user.user_id, groupID, message)
			#db_result = db_helper.display_new_messages(user1)
			#db_result = db_helper.drop_user(user1)
			self.add_notification("Result: "+str(db_result))
			return
        elif self.current_option == 2: # Display New Messages
			db_helper = DatabaseHelper.get_instance()
			db_result = db_helper.display_new_messages(self.user.user_id)
			self.add_notification("Result: "+str(db_result))
			return
        elif self.current_option == 3: # Display All Messages
			db_helper = DatabaseHelper.get_instance()
			db_result = db_helper.display_messages(self.user.user_id)
			self.add_notification("Result: "+str(db_result))
			return

class SelectRecipientMenu(Menu):
    def __init__(self, friends):
        if not friends:
            name = "Your contact list is empty :( try adding some friends!"
            friends = []
        else:
            name = "SELECT RECIPIENT"
        super(SelectRecipientMenu, self).__init__(None, name, friends)
        self.last_selection = None

    # will return last option selected
    def start(self):
        super(SelectRecipientMenu, self).start()
        return self.last_selection

    def process_selection(self):
        if self.current_option < len(self.options):
            self.last_selection = self.options[self.current_option]
            self.dismissed = True

class UserSearchResultsMenu(Menu):
    def __init__(self, users):
        if users == None or len(users) == 0:
            name = "SEARCH RETURNED NO RESULTS"
            users = []
        else:
            name = "SEARCH RESULTS"
        super(UserSearchResultsMenu, self).__init__(None, name, users)

    def process_selection(self):
        if self.current_option < len(self.options):
            DisplayProfileMenu(self.options[self.current_option]).start()

class ConfirmRequestsMenu(Menu):
    def __init__(self, user, requests):
        if requests == None or len(requests) == 0:
            name = "YOU HAVE NO REQUESTS :("
            requests = []
        else:
            name = "PENDING REQUESTS"
            requests.append("ACCEPT ALL")
            requests.append("DELETE ALL")
        super(ConfirmRequestsMenu, self).__init__(user, name, requests)
        if (requests):
            self.add_notification("Press ENTER to accept a request, 'ACCEPT ALL' to accept all requests, or 'DELETE ALL' to delete all requests. Any unaccepted requests will automatically be deleted when you exit this screen.")
        self.db_helper = DatabaseHelper.get_instance()

    def on_dismiss(self):
        # delete all remaining requests
        pass

    def accept_all_requests(self):
        if (len(self.options) <= 2):
            self.add_error("No more requests to accept.")
            return
        to_delete = []
        for i in range(len(self.options) - 2):
            request = self.options[i]
            if (request.group_id): # a group request
                if self.db_helper.check_group_limit_reached(request.group_id):
                    continue
                res = self.user.accept_group_join_request_from(request.requester_id, request.group_id)
            else:
                res = self.user.accept_friend_request_from(request.requester_id)
            if res:
                to_delete.append(request)
            else:
                self.add_error("Could not accept request from " + request.requester_f_name + " " + request.requester_l_name + ".")

        for req in to_delete:
            self.options.remove(req)
            self.no_options -= 1
            self.current_option %= self.no_options

        notification = "Accepted all requests"
        if len(self.options) > 2:
            notification += ". Any remaining requests could not be accepted due to errors"
            if (self.options[0].group_id):
                notification += " or full groups"
        notification += "."
        self.add_notification(notification)

    def accept_request(self, current_option):
        request = self.options[current_option]
        if request.group_id:
            if self.db_helper.check_group_limit_reached(request.group_id):
                self.add_notification("The group " + request.group_name + " is full. Cannot accept request from " + request.requester_f_name + " " + request.requester_l_name + ".")
                return
            res = self.user.accept_group_join_request_from(request.requester_id, request.group_id)
        else:
            res = self.user.accept_friend_request_from(request.requester_id)
        if res:
            request = self.options.pop(current_option)
            self.no_options -= 1
            self.current_option %= self.no_options
            self.add_notification("Accepted request from " + request.requester_f_name + " " + request.requester_l_name + ".")
        else:
            self.add_error("Could not accept request from " + request.requester_f_name + " " + request.requester_l_name + ".")

    def delete_all_requests(self):
        if (len(self.options) <= 2):
            self.add_error("No more requests to delete.")
            return
        to_delete = []
        for i in range(len(self.options) - 2):
            request = self.options[i]
            if (request.group_id): # a group request
                res = self.user.delete_group_join_request_from(request.requester_id, request.group_id)
            else:
                res = self.user.delete_friend_request_from(request.requester_id)
            if res:
                to_delete.append(request)
            else:
                self.add_error("Could not delete request from " + request.requester_f_name + " " + request.requester_l_name + ".")

        for req in to_delete:
            self.options.remove(req)
            self.no_options -= 1
            self.current_option %= self.no_options

        notification = "Deleted all requests"
        if len(self.options) > 2:
            notification += ". Any remaining requests could not be deleted due to errors"
        notification += "."
        self.add_notification(notification)


    def process_selection(self):
        if self.current_option < len(self.options) - 2:
            self.accept_request(self.current_option)
            return
        if self.current_option == len(self.options) - 2: #accept all
            self.accept_all_requests()
            return
        if self.current_option == len(self.options) - 1: #delete all
            self.delete_all_requests()
            pass

        # TODO: CREATE FORM HERE

class DisplayFriendsMenu(Menu):
    def __init__(self, users):
        if users == None or len(users) == 0:
            name = "YOU HAVE NO FRIENDS!"
            users = []
        else:
            name = "YOUR FRIENDS"
        super(DisplayFriendsMenu, self).__init__(None, name, users)

    def process_selection(self):
        if self.current_option < len(self.options):
            DisplayProfileMenu(self.options[self.current_option]).start()

class DisplayProfileMenu(Menu):
    def __init__(self, user):
        full_name = user.f_name + " " + user.l_name
        title =  full_name+ "'s PROFILE"
        friends = user.get_friends(limit = 3)
        if friends:
            opt_title = user.f_name + "'s Friends"
        else:
            opt_title = full_name + " HAS NO FRIENDS!"
        super(DisplayProfileMenu, self).__init__(user, title, friends, options_title = opt_title)


    def display_screen_title(self, columns):
        num_rows_printed = super(DisplayProfileMenu, self).display_screen_title(columns)
        num_rows_printed += self.print_centered(columns, "~ " + self.user.user_id + " ~", highlight_color = IO.bcolors.HEADER)
        num_rows_printed += self.print_centered(columns, self.user.email)
        age = str(self.user.get_age()) + " years old"
        num_rows_printed += self.print_centered(columns, age)
        num_rows_printed += self.print_centered(columns, "Last active " + self.user.get_last_active())
        return num_rows_printed


    def process_selection(self):
        if self.current_option < len(self.options):
            DisplayProfileMenu(self.options[self.current_option]).start()



# Abstract Class
# Concrete classes must implement validate function
class Form(object):
    __metaclass__ = ABCMeta
    # name = the name of the form, will be displayed at the top of the view
    # fields = List of strings denoting each fields
    # submit = String to be displayed for submit button
    # multiline_fields = List of indices of fields which will be multilined, all others will be single lined
    # hidden_fields = List of indices of fields whose responses should be hidden
	# defaults = a dictionary of default values to be used for each field, e.g. {0 : "Add me as a friend!", 5: "Abu Dhabi" }
    def __init__(self, name, fields, submit, multiline_fields = None, hidden_fields = None, defaults = None):
        self.name = name
        self.fields = fields
        self.current_selection = 0
        self.no_options = len(self.fields) + 2 # fields, submit, and cancel
        self.responses = ['' for i in range(len(fields))]
        if defaults:
            for key in defaults.keys():
                self.responses[key] = defaults[key]
        self.submit = submit
        self.cancel = 'CANCEL'
        self.submitted = False
        self.error_messages = []
        self.multiline_fields = multiline_fields
        self.hidden_fields = hidden_fields
        self.num_rows_printed = 0
        self.cursor = u'\u258d'
        self.pointer = u'\u25b8'
        self.hidden_char = u'\u25cf'


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

    def is_hidden_field(self, index):
        if self.hidden_fields == None:
            return False
        return index in self.hidden_fields

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
            text = self.responses[i]
            if self.is_hidden_field(i):
                text = self.hidden_char * len(text)
            if self.is_multiline_field(i):
                n_rows_printed += self.display_multiline_field(columns, option, text, i == self.current_selection)
            else:
                n_rows_printed += self.display_single_line_field(columns, option, text, i == self.current_selection)
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
        num_rows_printed = 0
        for i in range(to_fill - 1):
            num_rows_printed += self.print_empty_space(columns)
        num_rows_printed += self.print_horizontal_bar(columns)
        return num_rows_printed


    def display(self):
        rows, columns = self.get_rows_columns()
        num_rows_printed = 0
        num_rows_printed += self.print_horizontal_bar(columns)
        num_rows_printed += self.print_centered(columns, self.name.upper())
        num_rows_printed += self.print_horizontal_bar(columns)
        num_rows_printed += self.display_all_fields(columns)
        num_rows_printed += self.display_submit_button(columns)
        num_rows_printed += self.display_cancel_option(columns)
        num_rows_printed += self.display_error_messages(columns)
        num_rows_printed += self.fill_empty_space(rows, columns, num_rows_printed)

    # Call this function after instantiation of a concrete class
    # to display the form and get user's responses. Will return an array of responses corresponding
    # to each field.
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
            elif key == '\x1b[B' or key == '\x1b[C' or key == '\t':
                self.current_selection = (self.current_selection + 1) % self.no_options
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

    # validates an email using regex
    def validate_email(self, field_index):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", self.responses[field_index]):
            self.add_error(self.fields[field_index] + " format is invalid.")
            return False
        return True

    # validate nullability, maximum character length, and date formatting
    # attribute_field_map = {"userid": 0, "dob": 4}, for example meaning that
    # userid the attribute database corresponds to the first field in the form,
    # while dob corresponds to the fifth field
    def validate_against_schema(self, table_name, attribute_field_map):
        db_helper = DatabaseHelper.get_instance()
        # check if they can be null
        attributes_nullabilities = db_helper.get_attributes_nullabities(table_name)
        for attribute in attribute_field_map.keys():
            if self.responses[attribute_field_map[attribute]].strip() == '' and attributes_nullabilities[attribute] == False:
                self.add_error("'" + self.fields[attribute_field_map[attribute]] + "'" +  " cannot be empty.")
                return False

        # check that they are the correct lengths
        attributes_max_lengths = db_helper.get_attributes_lengths(table_name)
        for attribute in attribute_field_map.keys():
            if attribute in attributes_max_lengths and len(self.responses[attribute_field_map[attribute]]) > attributes_max_lengths[attribute]:
                self.add_error("'" + self.fields[attribute_field_map[attribute]] + "'" + " cannot be more than "
                              + str(attributes_max_lengths[attribute]) + " characters long.")
                return False

        # check that any dates are properly formatted, and in the past
        date_attributes = db_helper.get_date_attributes(table_name)
        for attribute in attribute_field_map.keys():
            if attribute in date_attributes:
                try:
                    datetime.strptime(self.responses[attribute_field_map[attribute]], '%Y-%m-%d')
                except ValueError:
                    self.add_error("'" + self.fields[attribute_field_map[attribute]] + "'" + " is invalid.")
                    return False
                if datetime.strptime(self.responses[attribute_field_map[attribute]], '%Y-%m-%d').date() >= date.today():
                    self.add_error("'" + self.fields[attribute_field_map[attribute]] + "'" + " must be in the past. -__-")
                    return False
        return True

    # Should return true if responses are valid, false otherwise
    # In the case of in valid input, can use add_error to display an error
    # to the user
    @abstractmethod
    def validate(self):
        raise NotImplementedError('')

class SignUpForm(Form):
    def __init__(self):
        super(SignUpForm, self).__init__("Sign Up",\
                                        ["Username",\
                                         "First Name",\
                                         "Last Name",\
                                         "Email",\
                                         "Password",\
                                         "Confirm password",\
                                         "Date of Birth (YYYY-MM-DD)"],\
                                         "Join the Club!",\
                                         hidden_fields = [4, 5])
        self.attribute_field_map = {"userid": 0,
                                    "fname": 1,
                                    "lname": 2,
                                    "email": 3,
                                    "password": 4,
                                    "dob": 6}
        self.associated_table = "profile"


    def validate(self):
        if not (self.validate_against_schema(self.associated_table, self.attribute_field_map) and self.validate_email(3)):
            return False
        db_helper = DatabaseHelper.get_instance()
        if db_helper.check_username_exists(self.responses[0]):
            self.add_error("Username already exists.")
            return False;
        if db_helper.check_email_exists(self.responses[3]):
            self.add_error("Email already exists.")
            return False;
        if not self.responses[4] == self.responses[5]:
            self.add_error("Passwords do not match.")
            return False
        return True

class CreateGroupForm(Form):
    def __init__(self):
        self.db_helper = DatabaseHelper.get_instance()
        self.associated_table = "groups"
        default_limit = str(self.db_helper.get_default_value(self.associated_table, "lmt"))
        super(CreateGroupForm, self).__init__("Create a New Group",\
                                        ["Group ID",\
                                         "Name",\
                                         "Limit",\
                                         "Description"],\
                                         "Create Group",
                                         defaults = {2:default_limit})
        self.attribute_field_map = {"gid": 0,
                                    "name": 1,
                                    "lmt": 2,
                                    "description": 3}


    def validate(self):
        if not (self.validate_against_schema(self.associated_table, self.attribute_field_map)):
            return False
        if self.db_helper.check_group_id_exists(self.responses[0]):
            self.add_error("Group ID already exists.")
            return False
        if not self.responses[2].isdigit():
            self.add_error("'" + self.fields[2] + "'" + " must be a number.")
            return False
        return True

class LogInForm(Form):
    def __init__(self):
        super(LogInForm, self).__init__("Log In", ["Username", "Password"], "Log In", hidden_fields = [1])

    def validate(self):
        for i,field in enumerate(self.fields):
            if self.responses[i] == '':
                self.add_error("'" + field + "' cannot be empty.")
                return False

        db_helper = DatabaseHelper.get_instance()
        if not db_helper.check_username_exists(self.responses[0]):
            self.add_error("Username does not exist.")
            return False;
        return True

class WhichFriendForm(Form):
    def __init__(self, user):
        super(WhichFriendForm, self).__init__("Send A Friend Request", ["Enter your friend's username"], "Submit")
        self.user = user
        self.db_helper = DatabaseHelper.get_instance()

    def validate(self):
        for i,field in enumerate(self.fields):
            if self.responses[i] == '':
                self.add_error("'" + field + "' cannot be empty.")
                return False

        if self.responses[0] == self.user.user_id:
            self.add_error("You cannot send yourself a friend request. -__-")
            return False;

        if not self.db_helper.check_username_exists(self.responses[0]):
            self.add_error("Username does not exist.")
            return False;

        first_name, last_name = self.db_helper.get_names_from_user_id(self.responses[0])
        if self.db_helper.check_friendship_exists(self.user.user_id, self.responses[0]):
            self.add_error("You are already friends with " + first_name + " " + last_name + ".")
            return False

        if self.db_helper.check_has_pending_friend_request_from(self.user.user_id, self.responses[0]):
            self.add_error("You already have a pending request from " + first_name + " " + last_name + ".")
            return False

        if self.db_helper.check_has_pending_friend_request_from(self.responses[0], self.user.user_id):
            self.add_error("You have already sent a friend request to " + first_name + " " + last_name + ".")
            return False
        return True

class SendFriendRequestForm(Form):
    def __init__(self, first_name):
        self.attribute_field_map = {"message": 0}
        self.associated_table = "pendingfriends"
        default = DatabaseHelper.get_instance().get_default_value("pendingfriends", "message")
        super(SendFriendRequestForm, self).__init__("Send A Friend Request To " + first_name,
                                                   ["Enter a message"], "Send Request",
                                                   multiline_fields = [0], defaults = {0:default})


    def validate(self):
        return self.validate_against_schema(self.associated_table, self.attribute_field_map)

class WhichGroupForm(Form):
    def __init__(self, user):
        super(WhichGroupForm, self).__init__("Send A Group Join Request", ["Enter the group's id"], "Submit")
        self.user = user
        self.db_helper = DatabaseHelper.get_instance()

    def validate(self):
        for i,field in enumerate(self.fields):
            if self.responses[i] == '':
                self.add_error("'" + field + "' cannot be empty.")
                return False

        if not self.db_helper.check_group_id_exists(self.responses[0]):
            self.add_error("No existing group with id '" + self.responses[0] + "'.")
            return False

        role = self.db_helper.check_is_group_member_or_manager(self.user.user_id, self.responses[0])
        group_name = self.db_helper.get_group_name_from_group_id(self.responses[0])
        if role:
            self.add_error("You are already a " + role + " of " + group_name + ".")
            return False

        if self.db_helper.check_has_pending_join_request_from(self.responses[0], self.user.user_id):
            self.add_error("You already have already requested to join " + group_name + ".")
            return False

        if self.db_helper.check_group_limit_reached(self.responses[0]):
            self.add_error("Sorry, this group's limit has been reached. :(")
            return False

        return True

class SendGroupJoinRequestForm(Form):
    def __init__(self, group_name):
        self.attribute_field_map = {"message": 0}
        self.associated_table = "pendinggroupmembers"
        super(SendGroupJoinRequestForm, self).__init__("Request to join " + group_name,
                                                   ["Enter a message"], "Send Request",
                                                   multiline_fields = [0], defaults = {0:"Hi! I'd like to join this group."})


    def validate(self):
        return self.validate_against_schema(self.associated_table, self.attribute_field_map)

class SearchForUserForm(Form):
    def __init__(self):
        super(SearchForUserForm, self).__init__("SEARCH FOR A USER",
                                               ["Keyword"], "Search")
    def validate(self):
        for i,field in enumerate(self.fields):
            if self.responses[i] == '':
                self.add_error("'" + field + "' cannot be empty.")
                return False
        return True

class ConfirmRequestsForm(Form):
    def __init__(self):
        super(ConfirmFriendRequestsForm, self).__init__("CONFIRM REQUEST",
                                               ["Are you sure you want to confirm this request"], "Submit")
    def validate(self):
        for i,field in enumerate(self.fields):
            if self.responses[i] == '':
                self.add_error("'" + field + "' cannot be empty.")
                return False


        return True

class SendMessageForm(Form):
    def __init__(self, recipient):
        title = "send a message to " + recipient.f_name + " " + recipient.l_name
        super(SendMessageForm, self).__init__(title, ["Enter your message"],\
                                              "Send Message", multiline_fields = [0])
        self.associated_table = "messages"
        self.attribute_field_map = {"message": 0}

    def validate(self):
        return self.validate_against_schema(self.associated_table, self.attribute_field_map)


class SearchFor3DegreesForm(Form):
    def __init__(self):
        super(SearchFor3DegreesForm, self).__init__("SEARCH FOR 3-Degrees", ["userID1", "userID2"], "Search")

    def validate(self):
        for i,field in enumerate(self.fields):
            if self.responses[i] == '':
                self.add_error("'" + field + "' cannot be empty.")
                return False
        return True

class SearchForTopKForm(Form):
    def __init__(self):
        super(SearchForTopKForm, self).__init__("SEARCH FOR TOP K USERS", ["Number of users", "Past number of days"], "Search")

    def validate(self):
        for i,field in enumerate(self.fields):
            if self.responses[i] == '':
                self.add_error("'" + field + "' cannot be empty.")
                return False
        return True

class MessageGroupForm(Form):
    def __init__(self):
        super(MessageGroupForm, self).__init__("MESSAGE GROUP FORM", ["Group ID", "Message"], "Send Message")

    def validate(self):
        for i,field in enumerate(self.fields):
            if self.responses[i] == '':
                self.add_error("'" + field + "' cannot be empty.")
                return False
        return True
