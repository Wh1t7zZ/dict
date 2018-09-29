'''
name Wh1t7zZ
date 2018-9-28
email:475011139@qq.com
环境：ubantu 16.04 python3.5 mysql 5.7.23
'''
from socket import *
import pymysql
import os
import signal
import sys
import time

#定义需要的全局变量
DICT_TEXT = "./dict.txt"
HOST = '0.0.0.0'
PORT = 8000
ADDR = (HOST,PORT)

#流程控制
def main():
    #创建数据库连接
    db = pymysql.connect('localhost','root','123456','dict')

    #创建套接字
    s = socket()
    s.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
    s.bind(ADDR)
    s.listen(5)

    #忽略子进程信号
    signal.signal(signal.SIGCHLD,signal.SIG_IGN)

    while True:
        try:
            c,addr=s.accept()
            print('connect from ',addr)
        except KeyboardInterrupt:
            s.close()
            sys.exit('\n服务器退出')
        except Exception as e:
            print(e)
            continue

        #创建子进程
        pid = os.fork()
        if pid == 0:
            s.close()
            do_child(c,db)
        else:
            c.close()

def do_child(c,db):
    while True:
        data = c.recv(128).decode()
        if not data or data == 'E':
            c.close()
            sys.exit(0)
        elif data[0] == 'R':
            do_register(c,db,data)
        elif data[0] == 'L':
            do_login(c,db,data)
        elif data[0] == 'Q':
            do_query(c,db,data)
        elif data[0] == 'H':
            do_host(c,db,data)

def do_register(c,db,data):
    L = data.split(' ')
    name = L[1]
    passwd = L[2]
    cursor = db.cursor()
    sql = "select * from user where name='%s'"%name
    r = cursor.execute(sql)
    print(r)
    if r != 0:
        c.send(b'exist')
        return
    sql = "insert into user (name,passwd)\
     values('%s','%s')"%(name,passwd)
    try:
        cursor.execute(sql)
        db.commit()
        c.send(b'ok')
    except:
        db.rollback()
        c.send(b'fall')
        return
    else:
        print('%s注册成功'%name)

def do_login(c,db,data):
    L = data.split(' ')
    cursor = db.cursor()
    name = L[1]
    passwd = L[2]
    sql="select * from user where\
     name='%s' and passwd='%s'"%(name,passwd)
    cursor.execute(sql)
    r = cursor.fetchone()
    if r == None:
        c.send('用户名或密码不正确'.encode())
    else:
        c.send(b'ok')

def do_query(c,db,data):
    cursor = db.cursor()
    L = data.split(' ')
    name = L[1]
    word = L[2]

    def insert_hist():
        sql="insert into history(name,word)\
         values('%s','%s')"%(name,word)
        try:
            cursor.execute(sql)
            db.commit()
        except:
            db.rollback()
            return

    # sql = "select * from words where word='%s'"%word 
    # cursor.execute(sql)
    # r = cursor.fetchone()
    # print(r)
    # if r == None:
    #     c.send(b'not found')
    # else:
    #     c.send(b'ok')
    #     time.sleep(0.1)
    #     c.send('解释: '.encode())
    #     c.send(r[2].encode())
    #     insert_hist()

    #文本查找
    try:
        f = open(DICT_TEXT,'rb')
    except:
        c.send("500 服务端异常".encode())
        return
    while True:
        line = f.readline().decode()
        w = line.split(' ')[0]
        if (not line) or w > word:
            c.send("没找到该单词".encode())
            break 
        elif w == word:
            c.send(b'OK')
            time.sleep(0.1)
            c.send(line.encode())
            insert_history()
            break
    f.close()

def do_host(c,db,data):
    name = data.split(' ')[1]
    cursor = db.cursor()
    try:
        sql = "select * from history where name='%s'\
         order by id desc limit 10"%name
        cursor.execute(sql)
        r = cursor.fetchall()
        if not r:
            c.send(b'no select history')
            return
        else:
            c.send(b'ok')
    except:
        c.send('数据库查询错误'.encode())

    for i in r:
        time.sleep(0.1)
        msg = '%s  %s  %s'%(i[1],i[2],i[3])
        c.send(msg.encode())
    time.sleep(0.1)
    c.send(b'##')


if __name__ == '__main__':
    main()