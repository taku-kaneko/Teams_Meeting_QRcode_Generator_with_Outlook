import os
import sys
import threading

import wx
import wx.adv

from frames.TaskBar import TaskBarIcon
from utils.config import initialize_config
from utils.logger import get_logger
from utils.QRcoder import QRcoder

logger = get_logger("__main__")


class App(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(
            self,
            parent,
            id,
            title,
            size=(300, 300),
            style=wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP,
        )

        # アプリの二重起動防止
        instance = wx.SingleInstanceChecker(self.GetTitle())
        if instance.IsAnotherRunning():
            message = f"{self.GetTitle()}はすでに起動中です"
            dialog = wx.MessageDialog(None, message, "エラー", wx.ICON_ERROR)
            dialog.ShowModal()
            dialog.Destroy()
            self.Close()

        # self.SetTopWindow(frame)

        # アイコンファイルのパスを取得
        path = os.path.dirname(os.path.abspath(__file__))
        if hasattr(sys, "_MEIPASS"):
            self.icon_path = os.path.join(path, "icon.ico")
        else:
            self.icon_path = os.path.join(path, "icon\\icon.ico")

        # 設定の読み込み
        self.config = initialize_config()

        qrcoder = QRcoder(self)

        # スレッドの準備
        self.thread_event = threading.Event()
        self.thread = threading.Thread(
            target=qrcoder.Main, daemon=True, args=(self.thread_event,)
        )

        # タスクバー
        TaskBarIcon(self, qrcoder)

        # スレッドの実行
        wx.CallAfter(self.thread.start)

        logger.info("launch App.")


def main():
    app = wx.App()
    App(None, wx.ID_ANY, "Sample")
    app.MainLoop()


if __name__ == "__main__":
    main()
