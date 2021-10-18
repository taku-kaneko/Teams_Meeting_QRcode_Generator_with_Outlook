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
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.onDisplayMenu)

    def CreatePopupMenu(self):
        menu = wx.Menu()

        if self.qrcoder.df is not None:
            df = self.checkMeeting("previous")
            if not df.empty:
                index = df.tail(1)["index"].iloc[0]
                subject = df.tail(1)["subject"].iloc[0]
                subject = self.checkStringLength(subject)
                CreateMenuItem(menu, f"前: {subject}", self.getOnDisplay(index))

            df = self.checkMeeting("now")
            if not df.empty:
                for i in range(df.shape[0]):
                    index = df["index"].iloc[i]
                    subject = df["subject"].iloc[i]
                    subject = self.checkStringLength(subject)
                    CreateMenuItem(menu, f"今: {subject}", self.getOnDisplay(index))

            df = self.checkMeeting("next")
            if not df.empty:
                index = df.tail(1)["index"].iloc[0]
                subject = df.tail(1)["subject"].iloc[0]
                subject = self.checkStringLength(subject)
                CreateMenuItem(menu, f"次: {subject}", self.getOnDisplay(index))
        else:
            CreateMenuItem(menu, f"会議はありません", self.onNothing)

        menu.AppendSeparator()

        CreateMenuItem(menu, "設定", self.onOpenSettings)

        menu.AppendSeparator()

        CreateMenuItem(menu, "終了", self.onExit)

        return menu

    def checkMeeting(self, kind):
        now = pd.Timestamp.now()
        if kind == "previous":
            condition_1 = self.qrcoder.df["start"] < now
            condition_2 = self.qrcoder.df["end"] < now
            df = self.qrcoder.df.loc[condition_1 & condition_2]
        elif kind == "now":
            condition_1 = self.qrcoder.df["start"] < now
            condition_2 = self.qrcoder.df["end"] > now
            df = self.qrcoder.df.loc[condition_1 & condition_2]
        else:
            condition = self.qrcoder.df["start"] > now
            df = self.qrcoder.df.loc[condition]
        return df

    def checkStringLength(self, string):
        if len(string) > 10:
            string = string[:10] + "…"

        return string

    def onDisplayMenu(self, event):
        menu = self.CreatePopupMenu()
        self.PopupMenu(menu)
        menu.Destroy()

    def getOnDisplay(self, index):
        def onDisplay(event):
            self.qrcoder.DisplayQRcode(index)

        return onDisplay

    def onOpenSettings(self, event):
        self.configFrame.Show()

    def onNothing(self, event):
        pass

    def onExit(self, event):
        logger.info("exit")
        wx.CallAfter(self.Destroy)
        self.frame.Close()
