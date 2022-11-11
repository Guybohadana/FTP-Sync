import ctypes
import threading
import time
from flask import Flask, render_template, request, session, flash, jsonify, Response
import json
import os
from threading import Thread
from ftplib import FTP
import subprocess

app = Flask(__name__)

status_connection = ""
connect_status = ''
tunnel_status = "Tunnel is up and running."
password = 'amspassword'
port = 22
ftp_user = "ftpuser"
targetip = '192.168.100.200'
ftppass = 'thFx9cOTmdxBILYGCrxC'
status = None
status_ftp = None
connect = 'live'

# FTP transfer
@app.route('/status-FTP', methods=['GET'])
def getStatusFTP():
    statusListftp = {'status_ftp': status_ftp}
    return json.dumps(statusListftp)


def task_ftp(act):
    global status_ftp
    print(act.split(' ')[1])
    print("Start copy")
    status_ftp = 20
    copyFromCustomer = subprocess.Popen("sudo rsync -azrP --append ftpuser@192.168.100.200:/home/ftpuser/"+act.split(' ')[1]+"/ /home/ftpuser/"+act.split(' ')[1]+"/", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("Copied")
    status_ftp = 40
    # wait for the process to terminate
    out, err = copyFromCustomer.communicate()
    copy = out.decode()
    print("Start send")
    status_ftp = 60
    sendToCustomer = subprocess.Popen("sudo rsync -azrP --append /home/ftpuser/"+act.split(' ')[1]+"/ ftpuser@192.168.100.200:/home/ftpuser/"+act.split(' ')[1]+"/", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = sendToCustomer.communicate()
    print("Sent")
    status_ftp = 80
    send = out.decode()
    if "incremental" not in copy and "incremental" not in send:
        status_ftp = 404
    else:
        status_ftp = 100
        print("Rsync Successfully")
    os.system("sudo pkill fortivpn")
    print("Disconnected")


# connect forti status
@app.route('/status', methods=['GET'])
def status():
    if connect == 'live':
        status_ist = {'status': status}
    else:
        status_ist = {'status': 'dead'}
    return json.dumps(status_ist, default=str)


# connect forti status
@app.route('/dis', methods=['GET'])
def disconnect():
    status_dis = {'status': 'Disconnected'}
    return json.dumps(status_dis, default=str)


def task(act):
    global status
    os.system("sudo pkill fortivpn")
    #os.system("python3 /home/user/connectvpn.py &")
    os.system("sudo openfortivpn -c /etc/openfortivpn/"+act.split(' ')[1]+"-config >connection_log.txt 2>&1 &")
    print("Connecting...")
    time.sleep(1)
    for i in range(0, 101, 10):
        status = i
        time.sleep(5)
        outfile = open('connection_log.txt', 'r').read()
        if tunnel_status in outfile:
            status = 100
            print("Connected to "+act.split(' ')[1])
            break
        if i == 100 and tunnel_status not in outfile:
            print(i)
            print(status)
            status = 404
            print(status)
            print("failed")
            os.system("sudo pkill fortivpn")
            break


def connection_forti(act):
    global connect
    action = act.split(' ')[0]
    print(act,"actttt")
    for thread in threading.enumerate():  # find last thread and kill it for multiple connect requests
        if "task" in thread.name:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, ctypes.py_object(SystemExit))
    if action == "connect":
        connect = 'live'
        print("Starting to connect openforti")
        t1 = Thread(target=task(act))
        t1.start()
    elif action == "disconnect":
        connect = 'dead'
        for thread in threading.enumerate():  # find last thread and kill it for multiple connect requests
            if "task" in thread.name:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, ctypes.py_object(SystemExit))
        os.system("sudo pkill openforti")
    return status_connection


def ftp(act):
    for thread in threading.enumerate():  # find last thread and kill it for multiple connect requests
        if "task" in thread.name:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, ctypes.py_object(SystemExit))
    if "FTP" in act:
        print("Starting FTP transfer")
        t2 = Thread(target=task_ftp(act))
        t2.start()




@app.route('/connector', methods=['POST'])
def connector():
    button_clicked = request.data.decode()
    if "connect" == button_clicked.split(' ')[0]:
        connection_forti(button_clicked)
    elif "disconnect" == button_clicked.split(' ')[0]:
        connection_forti(button_clicked)
    elif "FTP" in button_clicked:
        ftp(button_clicked)
    return jsonify(button_clicked)


@app.route('/', methods=['POST', 'GET'])
def main():
    global status, status_ftp
    print("-----------------------------------------")
    status = status_ftp = 0
    return render_template("page.html")


if __name__ == '__main__':
    app.run(debug=True)
