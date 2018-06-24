# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication, QWidget

if __name__ == '__main__':

    # 必ず作らなければいけないオブジェクト
    app = QApplication(sys.argv)

    # ウィジェットオブジェクトの作成(画面のこと)
    w = QWidget()
    # 画面を横幅を250px、高さを150pxにする
    w.resize(250, 150)
    # x=300,y=300の場所へ画面を移動
    w.move(300, 300)
    # タイトルを設定
    w.setWindowTitle('Simple')
    # 画面表示
    w.show()
    # プログラムをクリーンに終了する
    sys.exit(app.exec_())