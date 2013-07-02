import time
import HTMLParser

class parser:
    """Working with messages printing"""
    def getMessageDate(self, message):
            """Gets message date in time format"""
            return time.localtime(int(message['date']))

    def getMessageAttachments(self, message):
            """Gets and parses attachments in message"""
            try:
                attachments = message['attachments']
            except KeyError:
                return ""

            attachmentsString = "Attachments:\n"
            for attachment in attachments:
                data_type = attachment['type']
                if data_type == 'photo':
                    attachmentsString += 'Photo\n'
                elif data_type == 'video':
                    title = attachment['video']['title']
                    attachmentsString += "Video: %s\n" % title.encode('utf-8')
                elif data_type == 'audio':
                    performer = attachment['audio']['performer']
                    title = attachment['audio']['title']
                    attachmentsString += "Music: %s - %s\n" % (performer.encode('utf-8'), title.encode('utf-8'))
                elif data_type == 'doc':
                    title = attachment['doc']['title']
                    attachmentsString += "Document: %s\n" % title.encode('utf-8')

            return attachmentsString

    def getMessageBody(self, message):
            """Gets text of message and replaces special HTML symbols- to readable"""
            h = HTMLParser.HTMLParser()
            try:
                # replacing special HTML symbols
                text = h.unescape(message['body']).replace('<br>', '\n')
            except:
                return ""
            
            return text.encode('utf-8') + "\n"

    def isDatesDifferent(self, date_a, date_b):
        """Defines, is dates (day, month, year) different"""
        return not (date_a.tm_mday == date_b.tm_mday
                    and date_a.tm_mon == date_b.tm_mon
                    and date_a.tm_year == date_b.tm_year)

    def getMessages(self, messages, people):
        text = ""
        prevUid = 0
        prevDate = time.localtime(0)
        for message in messages:
            messageUid = message['uid']
            messageDate = self.getMessageDate(message)
            if self.isDatesDifferent(prevDate, messageDate):
                text += time.strftime("\n%d/%m/%Y\n", messageDate)

            if not (prevUid == messageUid) or self.isDatesDifferent(prevDate, messageDate):
                text += people[messageUid][0] + ': '

            try:
                fwd_messages = message['fwd_messages']
                text += "Forwarded messages:\n"
                text += self.getMessages(fwd_messages, people)
                text += "Forwarded messages ends.\n"
            except KeyError:
                pass

            text += self.getMessageBody(message)
            text += self.getMessageAttachments(message)

            prevUid = message['uid']
            prevDate = messageDate

        return text
