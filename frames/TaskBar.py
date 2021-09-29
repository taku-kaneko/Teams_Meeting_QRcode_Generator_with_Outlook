import pandas as pd
import wx
import wx.adv
from utils.logger import get_logger
from utils.utils import CreateMenuItem, SetIcon2Frame, ShowNotification

from frames.ConfigFrame import ConfigFrame

logger = get_logger(__name__)


class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame, qrcoder):
        super(TaskBarIcon, self).__init__()

        self.frame = frame
        self.qrcoder = qrcoder
        self.configFrame = ConfigFrame(frame)

        SetIcon2Frame(self, self.frame.icon_path, withAppName=True)
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_open_settings)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        CreateMenuItem(menu, "前の会議を表示", self.on_display_previous)
        CreateMenuItem(menu, "今の会議を表示", self.on_display_now)
        CreateMenuItem(menu, "次の会議を表示", self.on_display_next)

        menu.AppendSeparator()

        CreateMenuItem(menu, "設定", self.on_open_settings)

        menu.AppendSeparator()

        CreateMenuItem(menu, "終了", self.on_exit)

        return menu

    def on_display_previous(self, event):
        now = pd.Timestamp.now()
        condition_1 = self.qrcoder.df["start"] < now
        condition_2 = self.qrcoder.df["end"] < now
        df = self.qrcoder.df.loc[condition_1 & condition_2]
        if not df.empty:
            index = df.tail(1)["index"].iloc[0]
            self.qrcoder.DisplayQRcode(index)
        else:
            message = "前の会議は見つかりませんでした"
            wx.CallAfter(ShowNotification, "Warning", message, "warning")

    def on_display_now(self, event):
        now = pd.Timestamp.now()
        condition_1 = self.qrcoder.df["start"] < now
        condition_2 = self.qrcoder.df["end"] > now
        df = self.qrcoder.df.loc[condition_1 & condition_2]
        if not df.empty:
            for i in range(df.shape[0]):
                index = df.head(i + 1)["index"].iloc[0]
                self.qrcoder.DisplayQRcode(index)
        else:
            message = "開催中の会議は見つかりませんでした"
            wx.CallAfter(ShowNotification, "Warning", message, "warning")

    def on_display_next(self, event):
        now = pd.Timestamp.now()
        condition = self.qrcoder.df["start"] > now
        df = self.qrcoder.df.loc[condition]
        if not df.empty:
            index = df.head(1)["index"].iloc[0]
            self.qrcoder.DisplayQRcode(index)
        else:
            message = "この後の会議は見つかりませんでした"
            wx.CallAfter(ShowNotification, "Warning", message, "warning")

    def on_open_settings(self, event):
        if self.configFrame.IsClose:
            self.configFrame = ConfigFrame(self.frame)
            self.configFrame.Show()
        elif not self.configFrame.IsShow:
            self.configFrame.Show()
            self.configFrame.IsShow = True

    def on_exit(self, event):
        logger.info("exit")
        wx.CallAfter(self.Destroy)
        self.frame.Close()
