import requests
import hashlib
import pickle
import time
import smtplib
import ssl

from os.path import exists
from bs4 import BeautifulSoup as soup, element
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart


head = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:92.0) Gecko/20100101 Firefox/92.0'}


def main():
    urls = readFile("./urls.txt")
    originalPickle = "./original.pkl"
    updatedPickle = "./updated-data.pkl"
    global currentHash
    currentHash = {}
    for url in urls: #Fill hash dictionary
        currentHash[url] = hash(requests.get(url , headers = head)) 

    if exists(originalPickle) == False: #Store the page data
        if exists(updatedPickle):
            print('Updating pickle...')
            updatePickleFile(originalPickle, updatedPickle)
        else:
            pageData = {}
            for url in urls:
                pageData[url] = getPageData(url)
            pickleData(originalPickle, pageData)

    compareWebsites(urls) #Monitor for changes


def readFile(filename): 
    f = open(filename, 'r')
    content = f.readlines()
    return content

def getPageData(url):
    content = requests.get(url, headers = head)
    return soup(content.text, 'html.parser')

def pickleData(filename, dict):
    outfile = open(filename, 'wb')
    pickle.dump(dict, outfile)
    outfile.close()
    print('Data has been pickled! \n')

def hash(content):
    hashedContent = hashlib.md5(content.text.encode('utf-8')).hexdigest()
    return hashedContent

def compareWebsites(urls):
    for url in urls:
        print('Checking: ' + url)
        try:
            now = datetime.now()
            dateString = now.strftime('%m/%d/%Y %H:%M')
            content = requests.get(url, headers = head)
            newHash = hash(content)
            time.sleep(5)
            if currentHash[url] != newHash:
                print('something has changed in '+ url)
                currentHash[url] = newHash
                notify(url)
            else:
                continue
        except Exception as e:
            print(str(e))
            print('Error: retrying connection in 60 seconds...')
            time.sleep(60)
            content = requests.get(url, headers = head)
            if (content.status_code == 200):
                print('connection established, resuming monitor.')
            else:
                print(str(e))
                continue
    compareWebsites(urls)

def updatePickleDictionary():
    urls = readFile("./urls.txt")
    pageData = {}
    for url in urls:
        getPageData(urls)
    pickleData('./updated-data', pageData)

def updatePickleFile(old, new):
    infile = open(new, "rb")
    file_data = pickle.load(infile)
    infile.close()
    outfile = open(old, 'wb')
    pickle.dump(file_data, outfile)
    outfile.close()

def getUpdatedPageData(url):
    infile = open("./original.pkl", "rb")
    file_data = pickle.load(infile)
    originalPageData = file_data[url]
    infile.close()
    f = open('./original.html', 'w')
    f.write(str(originalPageData))
    f.close()        


def notify(url):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    gmail = 'SENDER_EMAIL'
    password = 'SENDER_EMAIL_PW'
    recipient = 'RECIPIENT_EMAIL'
    message = MIMEMultipart('mixed')
    message['From'] = 'Luigi <{sender}>'.format(sender = gmail)
    message['To'] = recipient
    message['Subject'] = 'A subject line'
    messageContent = 'Hello! A change has occurred at: ' + str(url) + '. Attached is the previous version'
    body = MIMEText(messageContent, 'html')
    message.attach(body)
    getUpdatedPageData(url)    
    attachmentPath = './original.html'
    try:
        with open(attachmentPath, 'rb') as attachment:
            p = MIMEApplication(attachment.read(), _subtype='html')
            p.add_header('Content-Disposition', "attachment; filename= %s" % attachmentPath.split("./")[-1]) 
            message.attach(p)
    except Exception as e:
        print(str(e))
    fullMessage = message.as_string()
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.ehlo()  
        server.starttls(context=context)
        server.ehlo()
        server.login(gmail, password)
        server.sendmail(gmail, recipient, fullMessage)
        server.quit()
        
    print('email sent')
    main()


if __name__ == '__main__':
    main()
