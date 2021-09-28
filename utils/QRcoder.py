import os
import subprocess as sp
import time
import traceback

import pandas as pd
import qrcode
import wx
import wx.adv
from frames.QRcodeFrame import QRcodeFrame
from PIL import Image

from utils.logger import get_logger
from utils.utils import (
    GetTeamsMeetings,
    GetWindowsName,
    ShowNotification,
    SubprocessArgs,
)

logger = get_logger(__name__)


class QRcoder:
    def __init__(self, frame):
        self.frame = frame
        self.config = frame.config
        self.counter = 0

        self.df = None

        self.IsShowDialog = False
        self.IsShowQRcode = True
        self.WorkPlace = None

        self.windowsName = GetWindowsName()

    def Main(self, event):
        # 最初に予定表を取得する
        while True:
            try:
                self.df = GetTeamsMeetings()
                break
            except Exception:
                logger.error(traceback.format_exc())
                message = "予定表の読み込みに失敗しました。\n１分後に再取得します。"
                wx.CallAfter(ShowNotification, "Outlook 読み込みエラー", message, "warning")
                time.sleep(60)

        self.Check(ignore_update=True)
        while True:
            event.wait(self.config["update_duration"])
            event.clear()
            self.Check()

    def Check(self, ignore_update=False):
        logger.debug("Run checking process.")
        try:
            if not ignore_update:
                self.UpdateSchedule()

            if self.windowsName != "Microsoft Windows 10 Home":
                self.CheckWorkPlace()

            now = pd.Timestamp.now()
            self.df.loc[:, "diff"] = (self.df["start"] - now).map(
                lambda x: x.total_seconds()
            )

            condition_1 = self.df["diff"] <= self.config["display_duration"]
            condition_2 = self.df["diff"] >= 0
            isJustBeforeStart = condition_1 & condition_2
            isStarted = (self.df["start"] <= now) & (self.df["end"] > now)

            show_items = self.df.loc[isJustBeforeStart | isStarted, ["index", "isShow"]]
            if not show_items.empty:
                for _, (index, isShow) in show_items.iterrows():
                    if not isShow:
                        self.df.loc[self.df["index"] == index, "isShow"] = True
                        wx.CallAfter(self.DisplayQRcode, index)
        except Exception:
            logger.error(traceback.format_exc())
            message = "勤務形態のチェック / スケジュールの更新 / QRコードの表示の\nいずれかにエラーが発生しました。\n１分後に再実行します。"
            wx.CallAfter(ShowNotification, "", message, "warning")

        self.counter += 1

    def MakeQRcode(self, string):
        qr = qrcode.QRCode(
            version=3,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=5,
            border=2,
        )

        qr.add_data(string)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white").convert("L")
        img = img.resize((250, 250), resample=0)

        return img

    def UpdateSchedule(self):
        logger.debug("updating schedule...")

        # 現在のスケジュールを取得する
        df_new = GetTeamsMeetings()
        indices_new = df_new["index"].to_list()

        indices = self.df.loc[self.df["index"].isin(indices_new), "index"].to_list()
        _df = self.df.loc[self.df["index"].isin(indices)].copy()  # キャンセルされた会議はここで消える
        tmp = df_new.loc[df_new["index"].isin(indices)]

        # avoid error
        tmp = tmp.sort_values("index").reset_index(drop=True)
        _df = _df.sort_values("index").reset_index(drop=True)

        # Confirm changes
        _df.loc[:, "isChange"] = ~(tmp.loc[:, "start"] == _df.loc[:, "start"])
        _df.loc[_df["isChange"]] = tmp.loc[_df["isChange"]]  # override

        # concatenate
        _df = pd.concat([_df, df_new.loc[~df_new["index"].isin(indices)]])

        _df.drop(columns="isChange", inplace=True)

        self.df = _df.copy()

    def DisplayQRcode(self, index):
        meeting_dict = self.df[self.df["index"] == index].to_dict(orient="records")[0]

        img = self.MakeQRcode(meeting_dict["url"])

        # 同じ会議のQRコードが表示されていたら、表示しない
        if self.frame.FindWindowByName(meeting_dict["subject"]) is None:
            frame = QRcodeFrame(img, meeting_dict, self.frame)
            frame.Show()
        else:
            logger.info("Already display")

    def CheckWorkPlace(self):
        logger.debug("Checking work style...")

        cp = sp.run(["query", "users"], encoding="shift-jis", **SubprocessArgs(True))
        results = [
            value for value in cp.stdout.split("\n")[4].split(" ") if value != ""
        ]

        if self.WorkPlace is not None:
            if results[1] != "console" and self.WorkPlace == "Office":
                value = self.ShowMessageDialog(
                    "TeamsQRcoder", "在宅勤務に切り替えたと判断しました。Teams会議のQRコードを表示しますか？"
                )
                if value == wx.ID_YES:
                    self.IsShowQRcode = True
                else:
                    self.IsShowQRcode = False
            elif results == "console" and self.WorkPlace == "Home":
                value = self.ShowMessageDialog(
                    "出勤に切り替えたと判断しました。Teams会議のQRコードを表示し続けますか？"
                )
                if value == wx.ID_YES:
                    self.IsShowQRcode = True
                else:
                    self.IsShowQRcode = False
        else:
            if results[1] == "console":
                value = self.ShowMessageDialog("出社していると判断しました。Teams会議のQRコードを表示しますか？")
                if value == wx.ID_YES:
                    self.IsShowQRcode = True
                else:
                    self.IsShowQRcode = False
