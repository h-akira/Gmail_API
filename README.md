# Gmail_API（2022年10月26日に再作成）
## 主な参考文献
- [公式ドキュメント](https://developers.google.com/gmail/api/quickstart/python)


## 環境構築
```
pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
pip3 install bs4
```

## 概要・使用方法
### `gmail_module.py`
モジュールとして`import`するものだが，
単体で実行した場合，
利用例である`sample()`関数が実行され，
有効な`token.json`が同じ階層にあれば
10件のメールを取得して表示する．

### `save2sql.py`
メールを取得して`sqlite3`に保存する．
HTMLメールにも対応している．

利用するには有効な`token.json`を`-t`で渡す必要がある．
初回でこれがない場合は，認証情報を作成して
`crient_secret_${長いやつ}.json`をダウンロードして，
これをオプション`-c`で渡す．すると`token.json`が出力され，
そのままプログラムが継続する．

