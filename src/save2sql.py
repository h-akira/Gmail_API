#!/usr/bin/env python3
import gmail_module
import os
import sys
import datetime
import sqlite3
from bs4 import BeautifulSoup

def main():
  import argparse
  parser = argparse.ArgumentParser(description="""\
Gmailからメッセージを取得してSQLに保存する．
""")
  parser.add_argument("--version", action="version", version='%(prog)s 0.0.1')
  parser.add_argument("-t", "--token", metavar="Path", default=os.path.join(os.path.dirname(__file__),"../secret/token.json"), help="token.json（存在しない場合は生成される）")
  parser.add_argument("-c", "--credentials", metavar="Path", default=os.path.join(os.path.dirname(__file__),"../secret/credentials.json"), help="credentials.json（client_secret_hogehoge.json）")
  parser.add_argument("--create", action="store_true", help="テーブルを削除して作り直す")
  parser.add_argument("-n", "--number", metavar="数字", type=int, default=10, help="取得するメッセージの件数")
  parser.add_argument("-q", "--query", metavar="文字列", default="", help="検索")
  parser.add_argument("-b", "--break-id-number", metavar="数字", type=int, default=5, help="既知のメッセージか判断するのに用いるidの数")
  parser.add_argument("--log", metavar="ファイル", help="実行履歴をファイルに追記する．")
  parser.add_argument("--known-continue", action="store_true", help="既知のメッセージに達したときに継続する")
  parser.add_argument("dbfile", metavar="db-file", help="データベースのファイル")
  options = parser.parse_args()

  if options.log:
    start = datetime.datetime.now()
    options_str = " ".join([i for i in sys.argv[1:]])

  if (not os.path.isfile(options.dbfile)):
    options.create = True
    print("DBが存在しないため作成します．")
  elif options.create:
    if input('テーブルが既に存在する場合は削除されます．本当によろしいですか？(y/other): ') != 'y':
      print('プログラムを終了します．')
      sys.exit()
  
  conn = sqlite3.connect(options.dbfile)
  conn.row_factory = sqlite3.Row
  cur = conn.cursor()
  
  # elseの場合にappend
  known_ids = []
  
  if options.create:
    cur.execute("drop table if exists mail")
    sql="""\
CREATE TABLE mail(
id INTEGER PRIMARY KEY AUTOINCREMENT,
_id TEXT,
_subject TEXT,
_date TEXT,
_from TEXT,
_to TEXT,
_body TEXT,
_text TEXT
);"""
    cur.execute(sql)
  else:
    cur.execute("SELECT max(id) AS max_id FROM mail;")
    row = cur.fetchone()
    max_id = row['max_id']
    if max_id==None:
      max_id = 0
    ## print(max_id.__class__)
    ## sys.exit()
    for i in range(min(max_id,options.break_id_number)):
      ## print(f"SELECT _id FROM mail WHERE id = {str(max_id-i)};")
      cur.execute(f"SELECT _id FROM mail WHERE id = {str(max_id-i)};")
      ## cur.execute(f"SELECT _subject, _date FROM mail WHERE id = {str(max_id-i)};")
      ## cur.execute(f"SELECT max(id)-{str(i)},_id FROM mail;")
      row = cur.fetchone()
      known_ids.append(row['_id'])
      ## known_ids.append(row['_subject']+row['_date'])
      ## print(row['_id'])
    ## print(break_ids)
    ## sys.exit()
  creds = gmail_module.get_creds(options.token,options.credentials)
  service = gmail_module.get_service(creds)
  print('メッセージを取得します．')
  mail_list = gmail_module.get_mail_list(service,options.query,options.number,
progress=True,known_ids=known_ids,known_continue=options.known_continue)
  print('データベースに保存します．')
  N = len(mail_list)
  for i,mail in enumerate(reversed(mail_list)):  # 逆にしないと既知で前回取得時より大きな数を指定しないといけなくなる
    print("\r"+f'progress:{i+1}/{N}',end="")
    body = mail.get_connected_body()
    text = BeautifulSoup(body,'html.parser').get_text()
    
    # SQLのシングルクォーテーションのエスケープ
    body=body.replace("'","''")
    text=text.replace("'","''")
    subject=mail.subject.replace("'","''")

    sql=f"INSERT INTO mail(_id,_subject,_date,_from,_to,_body,_text) VALUES('{mail.id}','{subject}','{mail.date}','{mail._from}','{mail._to}','{body}','{text}');"
    ## print(sql)
    try:
      cur.execute(sql)
    ## except:
    ## if i==5:
    except:
      print('\n以下のSQL文でエラーです．')
      print(sql)
      cur.execute(sql)
      sys.exit()
  print("")
  conn.commit()
  conn.close()

  if options.log:
    end = datetime.datetime.now()
    with open(options.log, mode='a') as f:
      print("start time: {}".format(start.strftime("%Y-%m-%d--%H-%M-%S")),file=f)
      print("end time  : {}".format(end.strftime("%Y-%m-%d--%H-%M-%S")),file=f)
      ## print("options   : {}".format(" ".join([i for i in sys.argv[1:]])),file=f)
      print("options   : {}".format(options_str),file=f)

if __name__ == "__main__":
  main()



