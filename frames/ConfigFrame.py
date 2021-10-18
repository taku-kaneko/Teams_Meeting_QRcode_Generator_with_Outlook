import wx
from utils.config import save_config
from utils.logger import get_logger
from utils.utils import SetIcon2Frame

logger = get_logger(__name__)


class ConfigFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        self.config = args[0].config
        self.thread_event = args[0].thread_event
        self.icon_path = args[0].icon_path

        width = 323
        height = 239

        w = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
        h = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)

        # Centre of the screen
        x = w / 2
        y = h / 2

        # Minus application offset
        x -= width / 2
        y -= height / 2

        pos = (x, y)

        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, pos=pos, *args, **kwds)
        self.SetSize((width, height))
        self.SetTitle("設定画面")
        SetIcon2Frame(self, self.icon_path)

        self.panel = wx.Panel(self, wx.ID_ANY)

        main_sizer = wx.StaticBoxSizer(
            wx.StaticBox(self.panel, wx.ID_ANY, ""), wx.VERTICAL
        )

        # Update Duration
        update_duration = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add(update_duration, 0, wx.EXPAND, 0)

        label_update = wx.StaticText(self.panel, wx.ID_ANY, "更新間隔（秒）")
        update_duration.Add(label_update, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 9)

        self.text_update = wx.TextCtrl(
            self.panel,
            wx.ID_ANY,
            str(self.config["update_duration"]),
            style=wx.TE_RIGHT,
        )
        update_duration.Add(self.text_update, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 63)
        self.text_update.Bind(wx.EVT_CHAR, self.check_text)

        # Time to show QR code
        show_time = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add(show_time, 0, wx.EXPAND, 0)

        label_2 = wx.StaticText(self.panel, wx.ID_ANY, "QRコード表示タイミング（分）")
        show_time.Add(label_2, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 8)

        self.text_qrcodeTime = wx.TextCtrl(
            self.panel,
            wx.ID_ANY,
            str(self.config["display_duration"]),
            style=wx.TE_RIGHT,
        )
        show_time.Add(
            self.text_qrcodeTime,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.LEFT | wx.TOP,
            6,
        )
        self.text_qrcodeTime.Bind(wx.EVT_CHAR, self.check_text)

        # Check to show QRcodes in the office
        reshow_qrcode = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add(reshow_qrcode, 0, wx.EXPAND, 0)

        label_redisplay = wx.StaticText(self.panel, wx.ID_ANY, "QRコード再表示時間（分）")
        reshow_qrcode.Add(label_redisplay, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)

        self.text_redisplay = wx.TextCtrl(
            self.panel,
            wx.ID_ANY,
            str(self.config["redisplay_duration"]),
            style=wx.TE_RIGHT,
        )
        reshow_qrcode.Add(self.text_redisplay, 0, wx.BOTTOM | wx.LEFT | wx.TOP, 9)
        self.text_redisplay.Bind(wx.EVT_CHAR, self.check_text)

        # Checkbox QRcode
        check_show = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add(check_show, 0, wx.EXPAND, 0)

        self.checkbox = wx.CheckBox(self.panel, wx.ID_ANY, "出社時は毎回、QRコードを表示するかどうかを確認する")
        check_show.Add(
            self.checkbox,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.LEFT | wx.TOP,
            13,
        )
        self.checkbox.SetValue(self.config["isCheckQRcodeInOffice"])

        # Apply Button
        OK_button = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add(OK_button, 0, wx.EXPAND, 0)

        self.button = wx.Button(self.panel, wx.ID_ANY, "適用して閉じる")
        OK_button.Add(self.button, 0, wx.LEFT, 10)
        self.button.SetFocus()

        self.Bind(wx.EVT_BUTTON, self.apply_close, self.button)
        self.Bind(wx.EVT_CLOSE, self.close)

        self.panel.SetSizer(main_sizer)

        self.Layout()

    def check_text(self, event):
        keycode = event.GetKeyCode()
        if ord("0") < keycode < ord("9"):
            event.Skip()
            return

        if keycode in [8, 127, 314, 315, 316, 317]:
            event.Skip()
            return

        return

    def apply_close(self, event):
        self.config["update_duration"] = int(self.text_update.GetValue())
        self.config["display_duration"] = int(self.text_qrcodeTime.GetValue())
        self.config["redisplay_duration"] = int(self.text_redisplay.GetValue())

        self.config["isCheckQRcodeInOffice"] = self.checkbox.IsChecked()

        print("|---------- self.configuration ----------|")
        for key, val in self.config.items():
            print(f"   {key}: {val}")
        print("|----------------------------------------|")

        save_config(self.config)

        # Thread の Wait を解除して、設定を更新する
        self.thread_event.set()

        self.Hide()

    def close(self, event):
        self.Hide()
