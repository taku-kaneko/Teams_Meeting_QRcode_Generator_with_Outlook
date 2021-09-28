import time

import wx
from utils.logger import get_logger
from utils.utils import SetIcon2Frame

logger = get_logger(__name__)


class QRcodeFrame(wx.Frame):
    def __init__(self, image, meeting_dict, *args, **kwds):
        self.image = image
        self.config = args[0].config
        self.meeting_dict = meeting_dict

        wx.Frame.__init__(
            self,
            None,
            -1,
            self.meeting_dict["subject"],
            size=(330, 380),
            style=wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP,
        )

        self.wxImage = wx.Image(*image.size)
        self.wxImage.SetData(image.convert("RGB").tobytes())

        SetIcon2Frame(self)

        self.InitializeComponents()

    def InitializeComponents(self):
        mainPanel = wx.Panel(self)

        subject_string = "件名：" + self.meeting_dict["subject"]
        subject = wx.StaticText(mainPanel, wx.ID_ANY, subject_string)

        time_string = (
            "時間："
            + self.meeting_dict["start"].strftime("%H:%M")
            + "~"
            + self.meeting_dict["end"].strftime("%H:%M")
        )
        time = wx.StaticText(mainPanel, wx.ID_ANY, time_string)
        qrcode = wx.StaticBitmap(
            mainPanel,
            wx.ID_ANY,
            self.wxImage.ConvertToBitmap(),
        )
        close = wx.Button(mainPanel, wx.ID_ANY, "閉じる")
        redisplay = wx.Button(
            mainPanel, wx.ID_ANY, f"{self.config['redisplay_duration']}分後に再表示"
        )

        subject.SetFont(
            wx.Font(
                12,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                0,
                "Yu Gothic UI",
            )
        )
        time.SetFont(
            wx.Font(
                12,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                0,
                "Yu Gothic UI",
            )
        )

        # Create a sizer.
        sizer = wx.GridBagSizer()
        sizer.Add(subject, (0, 0), (1, 2), wx.LEFT, 10)
        sizer.Add(time, (1, 0), (1, 2), wx.LEFT, 10)
        sizer.Add(qrcode, (2, 0), (1, 2), wx.ALIGN_CENTER_HORIZONTAL)
        sizer.Add(close, (3, 0), (1, 1), wx.TOP | wx.LEFT, 10)
        sizer.Add(redisplay, (3, 1), (1, 1), wx.ALIGN_RIGHT | wx.TOP | wx.RIGHT, 10)

        self.Bind(wx.EVT_BUTTON, self.on_close, close)
        self.Bind(wx.EVT_BUTTON, self.on_redisplay, redisplay)

        sizer.AddGrowableRow(0)
        sizer.AddGrowableRow(1)
        sizer.AddGrowableRow(2)
        sizer.AddGrowableRow(3)
        sizer.AddGrowableCol(0)
        sizer.AddGrowableCol(1)
        mainPanel.SetSizer(sizer)

    def on_close(self, event):
        wx.CallAfter(self.Destroy)

    def on_redisplay(self, event):
        wx.CallAfter(self.Destroy)
        wx.CallLater(self.config["redisplay_duration"] * 60 * 1000, self.Redisplay)

    def Redisplay(self):
        frame = QRcodeFrame(self.image, self.meeting_dict, self)
        frame.Show()
