# 動作確認（自動テスト）

## まとめて実行する

```bash
cd tests
python3 runall.py      # 順番に気をつけて全部を実行する
```

`resptest.py` と `wintest.py` は、途中で偽モジュールをわざと止める確認を
含むため、いちばん最後に実行する必要があります。`runall.py` はその順番と
偽モジュールの起動・停止をまとめて面倒を見ます。


Chrome を裏で動かして `index.html` を実際に操作し、結果を確かめます。

```bash
cd tests
python3 flowtest.py         # 登録→魚フォルダ→編集で自動読み込み→魚編集後へ保管（19項目）
python3 registertest.py     # 登録タブ一式（50項目）
python3 wheeltest.py        # ランク・数量のホイール（29項目）
python3 foldertest.py       # 取込のフォルダ表示・ずれ直し（23項目）
python3 fstest.py           # 保存先フォルダ・パソコン経路（16項目）
python3 fsandroidtest.py    # 保存先フォルダ・Android経路（19項目）
python3 fstest.py           # 保存先フォルダ・パソコン経路（16項目）
python3 fsandroidtest.py    # 保存先フォルダ・Android経路（19項目）
python3 exporttest.py       # 出品CSV+画像ZIPの生成（14項目）
python3 redotest.py         # 拡大と1枚だけやり直し（23項目）
python3 croptest.py         # 拡大のゲージと切り取り保存（14項目）
python3 tidytest.py         # 品種を減らす（25項目）
python3 goodstest.py        # 用品（餌・容器・道具）の登録（49項目）
python3 goodsfixedtest.py   # 用品の固定写真と固定の管理番号（25項目）
python3 autoprinttest.py    # 登録したらすぐテプラから出る（20項目）
python3 surfacetest.py      # Windowsの案内／ローカル保存（16項目）
python3 goodsprinttest.py   # 用品は選んで発行したものだけ出る（21項目）
python3 labeltest.py        # ラベルの長さ（余白）とランク→数量の移動（17項目）
python3 blanktest.py        # 白紙のラベルを出さない・二重印刷を防ぐ（17項目）
python3 phonetest.py        # 携帯の画面幅での見え方（8項目）

# Windows経路（テプラ クリエイター WebAPI）
python3 fake_webapi.py &    # 偽の通信モジュールを立てる
python3 usbtest.py          # USB優先とBluetoothへの切替（21項目）
python3 wintest.py          # 25項目（※最後に偽モジュールを止めるので、いちばん最後に実行する）
pkill -f fake_webapi.py
```

必要なもの: `pip3 install websocket-client pillow`

| ファイル | 何を確かめるか |
|---|---|
| `common.py` | ブラウザ操作の共通部分 |
| `flowtest.py` | 登録で「魚」にフォルダができる／編集タブを開くと自動で読み込む／「編集を終えて保存する」で原本と編集後が「魚編集後」に入り「魚」が空になる／「魚編集後」の自動生成 |
| `registertest.py` | ステップ式の登録／頭文字の絞り込み／検索／管理番号の発番／その場追加／テプラCSV／Androidの窓口／写真の割り当て |
| `wheeltest.py` | ランク・数量のホイール／ペア・セット・雄雌の切り替え／古いランクの入れ替え／タブのアイコン |
| `foldertest.py` | 管理番号ごとのフォルダ表示／写真の自動振り分け／区切りを1枚ずつ動かす／余りの扱い |
| `fstest.py` | 保存先フォルダの選択／登録時のフォルダ自動作成／使えない文字の置き換え／フォルダからの読み込み |
| `fstest.py` | 保存先フォルダの選択／登録時のフォルダ自動作成／使えない文字の置き換え／フォルダからの読み込み |
| `fsandroidtest.py` | Android経路：フォルダ自動作成／その場で撮る／写真から追加／縮めて読み込む |
| `exporttest.py` | 出品タブからCSV+画像ZIPを作り、中身（列・画像枚数・文字コード）を確かめる |
| `redotest.py` | フォルダから写真を拡大／1枚だけやり直し／ダメだった理由の記録とAIへの反映 |
| `croptest.py` | 拡大のゲージ／見えている範囲の切り取り保存（保存画像の中身も確認）／出品への反映 |
| `tidytest.py` | 品種の複数選択と削除／登録ずみ商品が残ること／検索しながらの整理／初期一覧への復帰 |
| `goodstest.py` | メダカ／用品の切り替え／用品はランクを聞かず個数だけ／用品用の出品タイトル／用品だけ減らせること |
| `goodsfixedtest.py` | 用品ごとの固定管理番号（重複しない・変更できる）／固定写真の登録と削除／取込で固定写真が入ること |
| `autoprinttest.py` | 登録と同時の印刷／経路判定が未了でも出ること／用品の出し直し／切り替えを外すと出ないこと |
| `surfacetest.py` | 用品はテプラを出さないこと／パソコンで繋がらないときの案内と対処／アプリのローカル保存 |
| `goodsprinttest.py` | 用品は登録時に出ないこと／選んだものだけ発行されること／何度でも出せること／魚のまとめ印刷に混ざらないこと |
| `labeltest.py` | ラベルの余白設定／Android・Windows双方への反映／古いアプリでも動くこと／ランクを選ぶと数量へ進むこと |
| `blanktest.py` | 中身の無いラベルを送らないこと／白紙の画像を作らないこと／二重に印刷しないこと |
| `usbtest.py` | USB機を優先して選ぶこと／印刷に失敗したらBluetoothへ切り替えること／余白が二重にかからないこと／テープの切り方 |
| `cuttest.py` | 印刷前にテープ送り・カットを出していないこと／接続確認でテープを動かさないこと／送る設定が仕様書どおりか／手動のテープ送り |
| `speedtest.py` | 登録を押してから印刷に送るまでの問い合わせ回数と時間（`FAKE_DELAY=1.0` で本物の待ち時間を模す） |
| `sharptest.py` | ラベル画像が白と黒だけでできていること（にじまない）／文字の大きさ設定が効くこと／本体側で拡大縮小させていないこと |
| `glyphtest.py` | 小さい文字がつぶれていないか（字の中の空白が残っているか）／行ごとの大きさの差 |
| `structtest.py` | 関数88個・画面の部品27個がそろっているか（書き換えで消える事故を止める）／印刷の入口がどんな時も結果を返すこと |
| `resptest.py` | 通信モジュールの返事が本文なし・JSONでない場合でも失敗にしないこと／止まっているときの理由 |
| `phonetest.py` | iPhone SE・iPhone 15・Pixel 8・360px端末で、横にはみ出さないか／指で押せる大きさか |
| `fake_webapi.py` | Windowsの通信モジュール（localhost:29108）を真似たもの。送られた画像を `/tmp/fake_tepra/` に保存する |
| `wintest.py` | Windows経路：経路の判定／ラベル画像の大きさ／印刷パラメータ／まとめ印刷／モジュール停止時の扱い |
