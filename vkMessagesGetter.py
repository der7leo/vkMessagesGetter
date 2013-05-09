import mechanize
import cookielib
import sys
import time
from getpass import getpass
from xml.dom import minidom

# vkMessagesGetter - a script, that downloads
# all messages with any user from vk.com
# and put it into file.
#
# Autor: Artem Zyryanov (der7leo@gmail.com)

def getFirstNodeInElementByTagName(xmlObject, tagname):
    return xmlObject.getElementsByTagName(tagname)[0].childNodes[0]

class VkNetworking:
    # clientid=3625158 - id of registered
    login_url = 'https://oauth.vk.com/authorize?client_id=3625158'\
                '&scope=messages&redirect_uri=https://oauth.vk.com/blank.html'\
                '&display=wap&response_type=token'

    def __init__(self):
        # Browser
        self.br = mechanize.Browser()

        # Cookie jar
        cj = cookielib.LWPCookieJar()
        self.br.set_cookiejar(cj)

        # Browser options
        self.br.set_handle_equiv(True)
        self.br.set_handle_redirect(True)
        self.br.set_handle_referer(True)
        self.br.set_handle_robots(False)

        # Some masquerade
        self.br.addheaders = [('User-agent', 'Mozilla/5.0 '
                '(X11; U; Linux 1686; en-US;rv:1.9.0.1)'
                'Gecko/201171615 Ubuntu/11.10-1 Firefox/3.0.1')]

    def login(self, email, password):
        print "Trying to login in vk.com"
        self.br.open(self.login_url)
        assert self.br.viewing_html()
        self.br.select_form( nr = 0 )
        self.br.form['email'] = email
        self.br.form['pass'] = password
        self.br.submit()
        # usually after login redirect url looks like that:
        # 'https://oauth.vk.com/blank.html#access_token=TOKEN'0
        # '&expires_in=DATA&user_id=USER_ID'
        # if splits doesn't work that means there's no access_token
        # in url and, usually, that password is wrong.
        try:
            urlparts = self.br.geturl().split('#')[1].split('&')
            self.access_token = urlparts[0].split('=')[1]
            self.expires_in = urlparts[1].split('=')[1]
            self.uid = urlparts[2].split('=')[1]
        except IndexError:
            raise Exception("Wrong password")

        print "Success!"

    def getUidName(self, uid):
        xmldata = self.br.open('https://api.vk.com/method/getProfiles.xml?'
        'uid=%s&access_token=%s' % (uid, self.access_token)).read()
        xmldoc = minidom.parseString(xmldata).childNodes[0]

        first_name = getFirstNodeInElementByTagName(xmldoc, 'first_name').data
        last_name = getFirstNodeInElementByTagName(xmldoc, 'last_name').data
        return (first_name.encode('utf-8'), last_name.encode('utf-8'))

    def getMessages(self, uid):
        def getNMessages():
            xmldata = self.br.open('https://api.vk.com/method/messages.getDialogs.xml?'
            'uid=%s&access_token=%s' % (uid, self.access_token)).read()
            xmldoc = minidom.parseString(xmldata).childNodes[0]
            nMessages = int(getFirstNodeInElementByTagName(xmldoc, 'count').data)
            return nMessages

        print "Starting messages download..."
        nMessages = getNMessages()
        offset = 0
        messages = []
        while offset <= nMessages:
            # 200 - max num of messages, that one xml-file with messages from vk.com can contain
            xmldata = self.br.open('https://api.vk.com/method/messages.getHistory.xml?'
            'uid=%s&offset=%d&count=200&rev=1&access_token=%s' % (uid, offset, self.access_token)).read()
            xmldoc = minidom.parseString(xmldata).childNodes[0]
            messagesInXmldoc = xmldoc.getElementsByTagName('message')
            for message in messagesInXmldoc:
                messages.append(message)
            offset += 200
            print "%d from %d" % (len(messages), nMessages)

        return messages

helpstring = """
usage: vkMessagesGetter.py [key][value]
keys:
   -email - your email on vk
   -userid - id of user, messages with whether you want to download messages
   -file - name of file, where will be messages after download
   -help - print this string

example: EngParse.py -email nyan@example.org -userid 123456 -file messagex.txt
"""

def printMessages(filename, messages, yourName, interlocutorName):

    def getMessageDate(message):
        return time.localtime(int(getFirstNodeInElementByTagName(message, 'date').data))

    def isDatesDifferent(date_a, date_b):
        return not (date_a.tm_mday == date_b.tm_mday and date_a.tm_mon == date_b.tm_mon
               and date_a.tm_year == date_b.tm_year)

    def getMessageBody(message):
        text = ""
        try:
            text = getFirstNodeInElementByTagName(message, 'body').data
        except:
            pass
        # <br> in vk message is '\n' symbol
        text = '\n'.join(text.split('<br>')).encode('utf-8')
        return text

    def getMessageAttachments(message):
        attachments = message.getElementsByTagName('attachment')
        if len(attachments) == 0:
            return ""

        attachmentsInfo = "Attachments:\n"
        for attachment in attachments:
            attachmentType = getFirstNodeInElementByTagName(attachment, 'type').data
            if attachmentType == 'photo':
                attachmentsInfo += "Photo\n"
            if attachmentType == 'video':
                title = getFirstNodeInElementByTagName(attachment, 'type').data
                attachmentsInfo += "Video: %s\n" % title.encode('utf-8')
            if attachmentType == 'audio':
                performer = getFirstNodeInElementByTagName(attachment, 'performer').data
                title = getFirstNodeInElementByTagName(attachment, 'title').data
                attachmentsInfo += "Music: %s - %s\n" % (performer.encode('utf-8'), title.encode('utf-8'))
            if attachmentType == 'doc':
                title = getFirstNodeInElementByTagName(attachment, 'title').data
                attachmentsInfo += "Document: %s\n" % title.encode('utf-8')

        return attachmentsInfo

    fsock = open(filename, 'w')
    if getFirstNodeInElementByTagName(messages[0], 'out').data == '1':
        wasPreviousOut = False
    else:
        wasPreviousOut = True

    previousMessageDate = time.localtime(0)

    for message in messages:
        # Except all forwarded messages (not supported yet)
        try:
            isMessageOut = int(getFirstNodeInElementByTagName(message, 'out').data)
        except IndexError:
            fsock.write("...Forwarded message was there...\n")
            continue

        messageDate = getMessageDate(message)
        messageBody = getMessageBody(message)
        messageAttachments = getMessageAttachments(message)
        messageAttachments = getMessageAttachments(message)

        # working with dates
        isDayPassed = isDatesDifferent(messageDate, previousMessageDate)

        if isDayPassed:
            fsock.write(time.strftime("\n%d/%m/%Y\n", messageDate))

        if isMessageOut and (not wasPreviousOut or isDayPassed):
            fsock.write(yourName[0] + ": ")
        if not isMessageOut and (wasPreviousOut or isDayPassed):
            fsock.write(interlocutorName[0] + ": ")

        fsock.write(messageAttachments)
        fsock.write(messageBody + '\n')
        #if messageAttachments: printAttachments(messageAttachments)

        # for next cycle iteration
        wasPreviousOut = isMessageOut
        previousMessageDate = messageDate

    fsock.close()

def parseCmdLine():
    email = ''
    userid = ''
    filename = ''

    try:
        for i in range(1, len(sys.argv)):
            if sys.argv[i] == '-h':
                print helpstring
                exit(0)
            if sys.argv[i] == '-email':
                email = sys.argv[i+1]
            if sys.argv[i] == '-file':
                filename = sys.argv[i+1]
            if sys.argv[i] == '-userid':
                userid = sys.argv[i+1]
    except:
        raise Exception("Wrong command arguments")

    if not (email or userid or filename):
        raise Exception("Wrong command arguments")

    return email, userid, filename

def askForPassword():
    print "Enter the password:"
    return getpass()

def main():
    vkNet = VkNetworking()
    try:
        email, uid, filename = parseCmdLine()
        password = askForPassword()
        vkNet.login(email, password)
        yourName = vkNet.getUidName(vkNet.uid)
        interlocutorName = vkNet.getUidName(uid)
        messages = vkNet.getMessages(uid)
        printMessages(filename, messages, yourName, interlocutorName)
    except Exception, e:
        print e
        if e.message == "Wrong command arguments":
            print helpstring
        exit(1)

if __name__ == '__main__':
    main()
