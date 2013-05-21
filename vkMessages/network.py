import mechanize
import cookielib
import json

class network:
    """Working with vk.com web-site"""
    # clientid=3625158 - id of registered by me application on vk.com
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
        """Login in vk.com with username and password"""
        print "Trying to login to vk.com"
        self.br.open(self.login_url)
        assert self.br.viewing_html()
        self.br.select_form( nr = 0 )
        self.br.form['email'] = email
        self.br.form['pass'] = password
        self.br.submit()
        # usually after login redirect url looks like that:
        # 'https://oauth.vk.com/blank.html#access_token=TOKEN'
        # '&expires_in=DATA&user_id=USER_ID'
        # if splits doesn't work that means there's no access_token
        # in url and, usually, that password is wrong.
        try:
            urlparts = self.br.geturl().split('#')[1].split('&')
            self.access_token = urlparts[0].split('=')[1]
            self.expires_in = urlparts[1].split('=')[1]
            self.uid = urlparts[2].split('=')[1]
        except KeyError:
            raise Exception("Wrong password")

        print "Success!"

    def getUidName(self, uid):
        """Gets name of user by his uid (user id)"""
        jsondata = self.br.open('https://api.vk.com/method/getProfiles?'
        'uid=%s&access_token=%s' % (uid, self.access_token)).read()
        profile = json.loads(jsondata)['response'][0]

        first_name = profile['first_name'].encode('utf-8')
        last_name = profile['last_name'].encode('utf-8')
        return (first_name, last_name)

    def getMessages(self, uid):
        """Downloads messages, saves in json format"""
        def getNMessages():
            """Gets number of messages in dialog"""
            jsondata = self.br.open('https://api.vk.com/method/messages.getDialogs?'
            'uid=%s&access_token=%s' % (uid, self.access_token)).read()
            return json.loads(jsondata)['response'][0]

        print "Starting messages download..."
        nMessages = getNMessages()
        allMessages = []
        offset = 0
        while offset <= nMessages:
            # 200 - max num of messages, that one json-response with messages from vk.com can contain
            jsondata = self.br.open('https://api.vk.com/method/messages.getHistory?'
            'uid=%s&offset=%d&count=200&rev=1&access_token=%s' % (uid, offset, self.access_token)).read()
            messages = json.loads(jsondata)['response'][1:]
            allMessages.extend(messages)
            offset += 200
            print "%d from %d" % (len(allMessages), nMessages)

        return allMessages

    def getDialogMembersList(self, messages):
        """Gets names of users, who participates in dialog"""
        members = {}
        for message in messages:
            uid = message['uid']
            if uid not in members.keys():
                members[uid] = self.getUidName(uid)
            try:
                fwd_messages = message['fwd_messages']
                for fwdMessage in fwd_messages:
                    uid = fwdMessage['uid']
                    if uid not in members.keys():
                        members[uid] = self.getUidName(uid)
            except KeyError:
                pass

        return members