## 概要
書込先のポートとzipファイルを指定し、sh-controllerに書き込むためのツール。

## 開発
|名称|バージョン|
|---|---|
|Python|3.9.5|
|PySide6|6.2.3|
|pyinstaller|4.5.1|

※Windowsでのバージョンのため、Macは一致しない場合有。

## ビルドコマンド
### ・Windows
```shell
pyinstaller writerForShCon.py --name writerForShCon.exe --icon=icon.ico --add-data "icon.ico;./" --add-data "adafruit-nrfutil.exe;./" --onefile
```

### ・Mac
```shell
pyinstaller writerForShCon.py --onefile
```
※Macの場合はUNIX実行ファイルになるため、同階層に「adafruit-nrfutil」を配置する必要有。

## 書き込みライブラリ引用元
- https://github.com/adafruit/Adafruit_nRF52_nrfutil
