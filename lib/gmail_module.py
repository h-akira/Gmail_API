#!/usr/bin/env python3

# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gmail_quickstart]
from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
# rom googleapiclient.errors import HttpError
####################
import base64
# from email.message import EmailMessage
####################

# If modifying these scopes, delete the file token.json.
# SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
SCOPES = ['https://mail.google.com/']

def get_creds(token_json='token.json',credentials_json='credentials.json'):
  # アクセストークンを取得
  """Shows basic usage of the Gmail API.
  Lists the user's Gmail labels.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists(token_json):
    creds = Credentials.from_authorized_user_file(token_json, SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(credentials_json, SCOPES)
      creds = flow.run_local_server(port=0)
    # Save the credentials for tahe next run
    with open(token_json, 'w') as token:
      token.write(creds.to_json())    
  return creds

def get_service(creds):
  try:
    service = build('gmail', 'v1', credentials=creds)
  except:
    print("Couldn't get service.")
    service = None
  return service

class Mail:
  def __init__(self):
    self.id = None
    self.subject = None
    self.date = None
    self._from = None
    self._to = None
    self.body = []
  def get_connected_body(self):
    return '\n'.join(self.body)

class Mail_list(list):
  def __init__(self):
    self.known_flag = False

def get_data(detail_point,data_list=list()):
  if detail_point.__class__ is list:
    iter = detail_point
  else:
    iter =  [detail_point]
  for d in iter:
    if d['body']['size']!=0:
      try:
        data_list.append(d['body']['data'])
      except:
        pass
    else:
      detail_point,data_list = get_data(d['parts'],data_list=data_list)
  return detail_point,data_list      

def get_mail_list(service,query,N,progress=False,known_ids=[],known_continue=False):
  mail_list = Mail_list()
  message_ids = service.users().messages().list(userId="me", maxResults=N, q=query).execute()
  if message_ids["resultSizeEstimate"] == 0:
    print("取得可能なメッセージはありません．")
  else:
    for i,message in enumerate(message_ids["messages"]):
      if progress:
        print("\r"+f'progress:{i+1}/{N}',end="")
      mail = Mail()
      mail.id=message["id"]
      
      ## print(mail.id)
      ## print(known_ids)
      ## import sys
      ## sys.exit()
      if mail.id in known_ids:
        mail_list.known_flag = True
        if known_continue:
          print(' 既知のメッセージのため飛ばします．')
          continue
        else:
          print(' 既知のメッセージに達したため取得を終了します．')
          break
      
      detail = service.users().messages().get(userId="me", id=message["id"]).execute()
      for header in detail["payload"]["headers"]:
        # 日付、送信元、件名を取得する
        if header["name"] == "Date":
          mail.date = header["value"]
        elif header["name"] == "From":
          mail._from = header["value"]
        elif header["name"] == "To":
          mail._to = header["value"]
        elif header["name"] == "Subject":
          mail.subject = header["value"]

      _, data_list = get_data(detail["payload"],[])  # よくわからないけどデフォルト値で[]だと残るみたい
      ## mail.body=[]
      for data in data_list:
        mail.body.append(base64.urlsafe_b64decode(data).decode("UTF-8"))
      mail_list.append(mail)
      ## print('ながさ',len(data_list))
      ## del data_list
    print("")
    if not mail_list.known_flag:
      print("既知のメッセージに達しませんでした．")
  return mail_list

def sample():
  import argparse
  parser = argparse.ArgumentParser(description="""
直近の10件のメールを取得して表示する．
""")
  parser.add_argument("--version", action="version", version='%(prog)s 0.0.1')
  parser.add_argument("-t", "--token", metavar="Path", default=os.path.join(os.path.dirname(__file__),"../secret/token.json"), help="token.json（存在しない場合は生成される）")
  parser.add_argument("-c", "--credentials", metavar="Path", default=os.path.join(os.path.dirname(__file__),"../secret/credentials.json"), help="credentials.json（client_secret_hogehoge.json）")
  options = parser.parse_args()
  
  N=10
  creds = get_creds(options.token,options.credentials)
  service = get_service(creds)
  mail_list = get_mail_list(service,"",N,progress=True)
  for mail in mail_list:
    print(mail.subject)
    print(mail.id)
    print(mail._from,mail._to)
    print(mail.body)

if __name__ == '__main__':
  sample()
