#-*- coding:utf-8 -*-
import os, sys, serial, threading, subprocess
import serial.tools.list_ports
from time import sleep
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *


class WriterForShCon(QDialog):
    """ sh-controllerに書き込みを行うGUIクラス
    """
    VERSION = "1.0"
    TITLE = "WriterForShCon v{}".format(VERSION)
    port_flg = True


    def __init__(self, parent=None):
        """ コンストラクタ
        """
        super(WriterForShCon, self).__init__(parent)

        print("このコンソール画面はアプリを立ち上げている間は閉じないでください。")

        # アイコン画像を設定
        if sys.platform.startswith('win'):
            self.setWindowIcon(QPixmap(self.temp_path('icon.ico')))

        # Widgetsの設定(タイトル、固定横幅、固定縦幅)
        self.setWindowTitle(self.TITLE)
        self.setFixedWidth(400)
        self.setFixedHeight(320)

        # ポート選択部分
        port_layout = QHBoxLayout()
        self.combobox = QComboBox(self)
        port_layout.addWidget(QLabel("書込ポート :"), 1)
        port_layout.addWidget(self.combobox, 4)

        # zipファイル選択部分
        file_layout = QHBoxLayout()
        self.zip_path = QLineEdit("")
        self.zip_path.setEnabled(False) # テキスト入力を禁止
        self.file_select_button = QPushButton("参照")
        self.file_select_button.clicked.connect(self.filedialog_clicked)
        file_layout.addWidget(QLabel("zipファイル :"), 1)
        file_layout.addWidget(self.zip_path, 3)
        file_layout.addWidget(self.file_select_button, 1)

        # テキストボックス部分
        self.text_layout = QHBoxLayout()
        self.textbox = QListView()
        self.text_list = QStringListModel()
        self.textbox.setModel(self.text_list)
        self.text_layout.addWidget(self.textbox)

        # プログレスバー部分
        pb_layput = QHBoxLayout()
        self.pb = QProgressBar()
        self.pb.setFixedWidth(370)
        self.pb.setTextVisible(False)
        pb_layput.addWidget(self.pb)

        # 書込実行ボタン部分
        run_layout = QHBoxLayout()
        self.run_button = QPushButton("書込実行")
        self.run_button.clicked.connect(self.write_shcon)
        run_layout.addWidget(QLabel(""), 2)
        run_layout.addWidget(self.run_button, 1)
        run_layout.addWidget(QLabel(""), 2)

        # レイアウトを作成して各要素を配置
        layout = QVBoxLayout()
        layout.addLayout(port_layout)
        layout.addSpacing(6)
        layout.addLayout(file_layout)
        layout.addSpacing(6)
        layout.addLayout(self.text_layout)
        layout.addSpacing(6)
        layout.addLayout(pb_layput)
        layout.addLayout(run_layout)

        # レイアウトを画面に設定
        self.setLayout(layout)

        # シリアルポート一覧を1秒ごとに取得するスレッドを開始
        port_thread = threading.Thread(target=self.set_serial_ports_list, daemon=True)
        port_thread.start()

        # 書き込みプロセスクラスの準備
        self.wp = WritingProcess()
        self.wp.writing_thread.connect(self.print_log)
        self.wp.finished.connect(self.show_result)


    def temp_path(self, relative_path):
        """ 実行時のパスを取得する関数

            Args:
                relative_path (str): 相対ファイルパス
            
            Returns:
                実行時のパス文字列
        """
        try:
            #Retrieve Temp Path
            base_path = sys._MEIPASS
        except Exception:
            #Retrieve Current Path Then Error 
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)


    def filedialog_clicked(self):
        """ ファイル選択ダイアログを表示させる関数
        """
        dir = os.path.abspath(os.path.dirname(sys.argv[0]))
        filter = "Zip File (*.zip)"
        fileObj = QFileDialog.getOpenFileName(self, "zipファイル選択", dir, filter)
        filepath = fileObj[0]

        # ファイルが選択されていればそのパスを設定
        if (filepath is not None) and (filepath != ""):
            self.zip_path.setText("")
            self.zip_path.setText(filepath)


    def write_shcon(self):
        """ sh-controllerに書き込む関数
        """
        self.text_list.setStringList([])
        target_port = self.combobox.currentText()
        target_file = self.zip_path.text()

        if target_port == "":
            QMessageBox.warning(self, "注意", "ポートが選択されていません。")
            return

        if target_file == "":
            QMessageBox.warning(self, "注意", "zipファイルが指定されていません。")
            return

        # GUIを非活性にする
        self.set_all_enabled(False)

        # プログレスバーの開始
        self.pb.setMinimum(0)
        self.pb.setMaximum(0)

        # コマンド作成に必要な情報を設定して書き込みプロセスを開始
        self.port_flg = False
        self.wp.set_data(target_port, target_file)
        self.wp.start()


    def print_log(self, log):
        """ 書き込み中の進捗をGUIに表示する関数

            Args:
                log (Any): 進捗内容の文字列
        """
        log_list = self.text_list.stringList()
        log_list.append(str(log))
        self.text_list.setStringList(log_list)
        self.textbox.scrollToBottom()


    def show_result(self):
        """ 書き込み結果を表示する関数
        """
        if self.wp.error is None:
            QMessageBox.information(self, "正常終了", "書き込みが正常終了しました。")
        else:
            QMessageBox.warning(self, "注意", "書き込みに失敗しました。\nポートやzipファイルが間違っていないか確認して再度実行してください。\n\n" + self.wp.error)

        # プログレスバーの停止
        self.pb.setMinimum(0)
        self.pb.setMaximum(100)

        self.set_all_enabled(True) # GUIの表示を戻す
        self.port_flg = True


    def set_all_enabled(self, flg):
        """ GUIの有効/無効を設定する関数

            Args:
                flg (bool): True/有効化、False/無効化
        """
        self.combobox.setEnabled(flg)
        self.file_select_button.setEnabled(flg)
        self.run_button.setEnabled(flg)


    def set_serial_ports_list(self):
        """ シリアルポート名一覧を1秒間隔でリスト形式で取得する関数
        """
        while True:
            if self.port_flg:
                # 接続されているポートのリストを取得(最初に空文字の選択肢を追加しないと勝手に最初の値が設定される)
                result = [port_info.name for port_info in serial.tools.list_ports.comports()]

                # MacOSの場合はポート頭に/dev/を追加
                if sys.platform.startswith('darwin'):
                    result = ["/dev/" + p for p in result]

                result.insert(0, "")

                # 現在の選択値文字列を取得してプルダウンリストを更新
                current_port = self.combobox.currentText()
                self.combobox.clear()
                self.combobox.addItems(result)

                if (len(result) == 1) or (not current_port in result):
                    # 接続機器無しまたは選択ポートが接続断の場合は空文字をセット
                    self.combobox.setCurrentText("")
                else:
                    # 選択しているものを再セット
                    self.combobox.setCurrentText(current_port)
            sleep(1)



class WritingProcess(QThread):
    """ sh-controllerへの書き込み処理を行うプロセスクラス
    """
    # 書き込む時のコマンド(win)
    CMD_WRITE_STR = 'adafruit-nrfutil.exe --verbose dfu serial -b 115200 --singlebank -pkg {} -p {}'

    # 書き込む時のコマンド(mac)
    CMD_WRITE_MAC_STR = '/adafruit-nrfutil --verbose dfu serial -b 115200 --singlebank -pkg {} -p {}'

    writing_thread = Signal(str)
    read_flg = False
    target_port = ""
    target_zip_path = ""
    error = None
    exe_dir_path = os.path.abspath(os.path.dirname(sys.argv[0])) + "/"

    def __init__(self, parent=None):
        """ コンストラクタ
        """
        QThread.__init__(self, parent)


    def __del__(self):
        # Threadオブジェクトが削除されたときにThreadを停止(念のため)
        self.wait()


    def set_data(self, target_port, target_zip_path):
        """ コマンド作成に必要な情報をセットする関数

            Args:
                target_port (str): 書き込みポート
                target_zip_path (str): 対象zipファイルパス
        """
        self.target_port = target_port
        self.target_zip_path = target_zip_path


    def run(self):
        """ 書き込み処理を実行する関数
        """
        self.error = None
        write_port = [self.target_port]

        # 書き込みモードに切り替え
        self.change_write_mode()
        self.writing_thread.emit("changed write mode.")

        # 書き込みモード直後のポートリストを取得
        after_port_list = self.get_port_list()

        counter = 0
        while True:
            port_list = self.get_port_list()

            # ポートが増えていた場合はループを抜け出す
            if len(after_port_list) < len(port_list):
                write_port = list(set(after_port_list) ^ set(port_list))
                break
            elif counter > 25:
                break

            counter = counter + 1
            sleep(0.25)

        if self.error is None:
            # 書き込み実行
            self.write_sketch(write_port[0])


    def get_port_list(self):
        """ ポートのリストを取得する関数
        """
        # ポートリストを取得
        port_list = [port_info.name for port_info in serial.tools.list_ports.comports()]

        # MacOSの場合はポート頭に/dev/を追加
        if sys.platform.startswith('darwin'):
            port_list = ["/dev/" + p for p in port_list]

        return port_list


    def change_write_mode(self):
        """ 書き込みモードへ切り替えを行う関数
        """
        port = serial.Serial(self.target_port, 115200)
        try:
            port.baudrate = 1200
            port.bytesize = 8
            port.stopbits = 1
            port.setDTR(False)
            sleep(0.1)
        except Exception as e:
            self.error = e
        finally:
            port.close()


    def write_sketch(self, write_port):
        """ ボードに書き込むコマンドを実行
            Args:
                write_port (str): 書き込み対象ポート文字列
        """
        error_flg = False
        encording = "shift-jis"
        command = self.CMD_WRITE_STR

        # MacOSの場合はコマンド変更、エンコードをutf-8にする
        if sys.platform.startswith('darwin'):
            dir = os.path.abspath(os.path.dirname(sys.argv[0]))
            command = dir + self.CMD_WRITE_MAC_STR
            encording = "utf-8"

        self.writing_thread.emit("target port: {}".format(write_port))

        # 書き込みコマンド実行(対象ポートはポートリストの最後を使う)
        for line in self.run_cmd_get_line(cmd=command.format("\"" + self.target_zip_path + "\"", write_port), encoding_str=encording):
            self.writing_thread.emit(line[:-1])

            # TracebackかFaildの文字があればエラーとみなして、エラーに追記
            if 'Traceback' in str(line) or 'Faild' in str(line):
                error_flg = True
                self.error = ""

            if error_flg:
                self.error = self.error + str(line)


    def run_cmd_get_line(self, cmd, encoding_str):
        """ コマンド実行中の標準出力を非同期で取得する関数
            Args:
                cmd (str): 実行するコマンド文字列
                encoding_str (str): エンコード文字列
            
            Returns:
                標準出力 (行毎)
        """
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding=encoding_str)

        while True:
            line = proc.stdout.readline()
            if line:
                yield line
            if not line and proc.poll() is not None:
                break

        # コマンドの結果がエラーの場合の処理
        if (self.error is None) and (not proc.returncode == 0):
            self.error = "書き込み実行コマンドが失敗しました。"


if __name__ == '__main__':
    # Qtアプリケーションの作成
    app = QApplication(sys.argv)

    # フォームを作成して表示
    form = WriterForShCon()
    form.show()

    # 画面表示のためのループ
    sys.exit(app.exec())
