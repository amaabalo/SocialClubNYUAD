import os
import IO
import Views
import sys






if __name__=='__main__':
    if (len(sys.argv) != 4):
        print('USAGE: python ' + sys.argv[0] + ' <DATABASE> <USER> <PASSWORD>')
        sys.exit(0)
    m = Views.WelcomeMenu()
    m.start()
