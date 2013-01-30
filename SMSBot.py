# TODO: Implement original commands
# TODO: Form proper MMS-email addresses from carriers

import os
import sys
import subprocess

import time
import socket
import urllib2

from PIL            import ImageGrab
from Sender         import SMTP_EmailSender
from Receiver       import IMAP_EmailReceiver
from FileCrawler    import Crawler

__author__  = "George Kudrayvtsev"
__version__ = "0.82 alpha"

class Logger:
    """
    A simple file-handling class that will write
    down various debug information with time stamps.
    """
    def __init__(self, filename="debug.log"):
        self.file = open(filename, "a")
        self.open = True
        
    def Write(self, data):
        if self.open:
            self.file.write("%s: %s\n" % (time.ctime(), data))
            self.file.flush()
            
    def Close(self):
        self.file.close()
        self.open = False

class SMSException(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)
        
class SMSHandler:
    """
    The primary class that handles actions from messages.
    Custom actions can be added to the handler via callbacks.
    """
    def __init__(self, numbers, output=sys.stdout):
        self.eSend  = SMTP_EmailSender()
        self.eRecv  = IMAP_EmailReceiver()
        self.Log    = Logger("SMSBot.log")
        
        self.unread = 0
        self.emails = {}
        self.actions= {}
        self.output = output
        
        if type(numbers) != type([]):
            raise SMSException("A list of accepted phone numbers must be provided.")
        
        self.nums   = numbers
        self.Log.Write("SMSBot v%s launched." % __version__)
        self.Log.Write("Active phone numbers:")
        for n in self.nums: self.Log.Write("\t%s" % (n))
        
    def Login(self, email, password):
        """
        Logs into GMail using a plaintext email and password.
        Sorry for the lack of security. Some sort may be 
        implemented in the future.
        """
        try:
            self.eSend.Login(email, password)
            self.eRecv.Login(email, password)
            return True
            
        except:
            # Probably invalid login data.
            return False

    def Queue(self):
        """ Wait for emails to arrive. """
        self.output.write("[ ] Awaiting messages from any in %s ... \r" % (repr(self.nums)))
        
        while not self.unread:
            self.eRecv.Refresh()
            for n in self.nums:
                self.emails[n] = self.eRecv.GetEmailsFrom(n)
                self.unread += len(self.emails[n])
                
        self.output.write("[*]\n")
        
    def ClearUnread(self):
        """ Clears unread count, leaves messages in inbox marked unread. """
        self.unread = 0
        
    def AddCommand(self, text, callback):
        """ Adds a command to the message handler. """
        self.actions[text] = callback
        
    def ParseRequest(self, number, request_id):
        """ Parses emails for commands """
        email   = self.eRecv.GetEmail([request_id])[0]
        request = email.upper()
        
        for a in self.actions.keys():
            print "Searching for %s..." % a.upper()
            
            if request.find(a.upper()) >= 0:
                self.actions[a](self, number, email)
                
        self.eRecv.DeleteEmail(request_id)
        
    def Run(self):
        while True:
            self.Queue()
            
            for n in self.emails.keys():
                for id in self.emails[n]:
                    self.ParseRequest(n, id)
                    
            self.ClearUnread()
            time.sleep(5)
                
        
def help(handler, number, email):
    handler.eSend.SendEmail(number, "SMSBot v1.0a", "")
    print "[*] Sent usage."
    
def main():
    Bot = SMSHandler(["YOURPHONE@YOURCARRIER_EMAIL"])
    Bot.Login("YOURGMAIL@gmail.com", "YOURPASSWORD")
    Bot.AddCommand("Help", help)
    Bot.Run()
    
main()
        
        