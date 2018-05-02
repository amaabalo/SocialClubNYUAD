import os
import IO
import Views
import sys
from UserContext import DatabaseHelper






if __name__=='__main__':
    if (len(sys.argv) != 4):
        print('USAGE: python ' + sys.argv[0] + ' <DATABASE> <USER> <PASSWORD>')
        sys.exit(0)
    m = Views.WelcomeMenu()
    m.start()
    DBHelper = DatabaseHelper.get_instance()
    print(DBHelper.get_date_attributes("profile"))
