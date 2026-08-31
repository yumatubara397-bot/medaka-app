# 動作確認（自動テスト）

Chrome を裏で動かして `index.html` を実際に操作し、結果を確かめます。

```bash
cd tests
python3 registertest.py     # 登録タブ一式（51項目）
python3 wheeltest.py        # ランク・数量のホイール（29項目）
python3 foldertest.py       # 取込のフォルダ表示・ずれ直し（23項目）
python3 fstest.py           # 保存先フォルダ・パソコン経路（16項目）
python3 fsandroidtest.py    # 保存先フォルダ・Android経路（19項目）
python3 fstest.py           # 保存先フォルダ・パソコン経路（16項目）
python3 fsandroidtest.py    # 保存先フォルダ・Android経路（19項目）
python3 exporttest.py       # 出品CSV+画像ZIPの生成（14項目）
python3 phonetest.py        # 携帯の画面幅での見え方（8項目）

# Windows経路（テプラ クリエイター WebAPI）
python3 fake_webapi.py &    # 偽の通信モジュールを立てる
python3 wintest.py          # 21項目
pkill -f fake_webapi.py
```

必要なもの: `pip3 install websocket-client pillow`

| ファイル | 何を確かめるか |
|---|---|
| `common.py` | ブラウザ操作の共通部分 |
| `registertest.py` | ステップ式の登録／頭文字の絞り込み／検索／管理番号の発番／その場追加／テプラCSV／Androidの窓口／写真の割り当て |
| `wheeltest.py` | ランク・数量のホイール／ペア・セット・雄雌の切り替え／古いランクの入れ替え／タブのアイコン |
| `foldertest.py` | 管理番号ごとのフォルダ表示／写真の自動振り分け／区切りを1枚ずつ動かす／余りの扱い |
| `fstest.py` | 保存先フォルダの選択／登録時のフォルダ自動作成／使えない文字の置き換え／フォルダからの読み込み |
| `fstest.py` | 保存先フォルダの選択／登録時のフォルダ自動作成／使えない文字の置き換え／フォルダからの読み込み |
| `fsandroidtest.py` | Android経路：フォルダ自動作成／その場で撮る／写真から追加／縮めて読み込む |
| `exporttest.py` | 出品タブからCSV+画像ZIPを作り、中身（列・画像枚数・文字コード）を確かめる |
| `phonetest.py` | iPhone SE・iPhone 15・Pixel 8・360px端末で、横にはみ出さないか／指で押せる大きさか |
| `fake_webapi.py` | Windowsの通信モジュール（localhost:29108）を真似たもの。送られた画像を `/tmp/fake_tepra/` に保存する |
| `wintest.py` | Windows経路：経路の判定／ラベル画像の大きさ／印刷パラメータ／まとめ印刷／モジュール停止時の扱い |
