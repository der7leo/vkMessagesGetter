import sys
from getopt import getopt
from getpass import getpass

from vkMessages.network import network
from vkMessages.parser import parser

helpstring = """
usage: vkMessagesGetter.py [key][value]
keys:
   -e, --email - your email on vk
   -u, --userid - id of user, messages with whether you want to download messages
   -f, --file - name of file, where will be messages after download
   -h, --help - print this string

example: EngParse.py -email nyan@example.org -userid 123456 -file messages.txt
"""

def parseCmdLine():
    email = ''
    userid = ''
    filename = ''

    try:
        opts, args = getopt(sys.argv[1:], 'e:u:f:h',
        ['email=','userid=','file=', 'help'])
    except:
        raise Exception("Wrong command line arguments")

    for (opt, arg) in opts:
        if opt in ('-e', '--email'):
            email = arg
        elif opt in ('-u', '--userid'):
            userid = arg
        elif opt in ('-f', '--file'):
            filename = arg
        elif opt in ('-h', '--help'):
            print helpstring
            sys.exit()

    if not (email or userid or filename):
        raise Exception("Wrong command line arguments")

    return email, userid, filename

def askForPassword():
    print "Enter the password:"
    return getpass()

def main():
    vkNet = network()
    vkParse = parser()
    try:
        email, uid, filename = parseCmdLine()
        password = askForPassword()
        vkNet.login(email, password)
        messages = vkNet.getMessages(uid)
        people = vkNet.getDialogMembersList(messages)
        open(filename, 'w').write(vkParse.getMessages(messages, people))
    except Exception, e:
        print e
        if e.message == "Wrong command line arguments":
            print helpstring
        sys.exit(1)

if __name__ == '__main__':
    main()