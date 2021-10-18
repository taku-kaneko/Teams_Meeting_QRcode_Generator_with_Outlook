import datetime
import inspect
import os
import re
import subprocess as sp
import sys
import traceback
from ast import parse
from os.path import expanduser

import pandas as pd
import pythoncom
import pywintypes
import win32com.client
import wx
import wx.adv

from utils.defined_exceptions import OutlookReadError
from utils.logger import get_logger

logger = get_logger(__name__)

TEAMS_LINK = "https://teams.microsoft.com/l/meetup-join"
CONFIG_PATH = filename = expanduser("~") + "\\Documents\\TeamsQRcoder\\config.json"
APP_NAME = "TeamsQRcoder"


def ResourcePath(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = os.path.dirname(inspect.stack()[1].filename)
    # base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def ShowNotification(title, message, kind="information"):
    nmsg = wx.adv.NotificationMessage(title=title, message=message)

    if kind == "information":
        nmsg.SetFlags(wx.ICON_INFORMATION)
    elif kind == "warning":
        nmsg.SetFlags(wx.ICON_WARNING)

    nmsg.Show(timeout=wx.adv.NotificationMessage.Timeout_Auto)


def ShowMessageDialog(title, message):
    dialog = wx.MessageDialog(None, message, title, wx.YES_NO | wx.ICON_QUESTION)

    result = dialog.ShowModal()
    if result == wx.ID_YES:
        logger.info("Chosen Yes")
    else:
        logger.info("Chosen No")

    dialog.Destroy()

    return result


def SetIcon2Frame(frame, icon_path, withAppName=False):
    if os.path.isfile(icon_path):
        icon = wx.Icon(wx.Bitmap(icon_path))
        if withAppName:
            frame.SetIcon(icon, APP_NAME)
        else:
            frame.SetIcon(icon)


def CreateMenuItem(menu, label, func):
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.Append(item)

    return item


def SubprocessArgs(include_stdout=True):
    if hasattr(sp, "STARTUPINFO"):
        si = sp.STARTUPINFO()
        si.dwFlags |= sp.STARTF_USESHOWWINDOW
        env = os.environ
    else:
        si = None
        env = None

    if include_stdout:
        ret = {"stdout": sp.PIPE}
    else:
        ret = {}

    ret.update({"stdin": sp.PIPE, "stderr": sp.PIPE, "startupinfo": si, "env": env})
    return ret


def GetWindowsName():
    o = sp.Popen(
        "systeminfo", encoding="shift-jis", **SubprocessArgs(True)
    ).communicate()[0]
    try:
        o = str(o, "latin-1")  # Python 3+
    except Exception:
        pass
    return re.search("OS (Name|名):\s*(.*)", o).group(2).strip()


def FindUrls(text):
    pattern = "https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
    return re.findall(pattern, text)


def GetTeamsMeetings():
    try:
        pythoncom.CoInitialize()

        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        calender = outlook.GetDefaultFolder(9)

        now = datetime.datetime.now()
        tomorrow = now + datetime.timedelta(days=1)
        start = now.strftime("%Y/%m/%d")
        end = tomorrow.strftime("%Y/%m/%d")

        items = calender.Items
        items.IncludeRecurrences = True
        items.Sort("[Start]")
        restriction = f"[Start] >= '{start}' AND [Start] <= '{end}'"
        restricted_items = items.Restrict(restriction)

        indices, subjects, starts, ends, teams_urls = [], [], [], [], []
        for item in restricted_items:
            urls = FindUrls(item.body)
            url = [url for url in urls if url.startswith(TEAMS_LINK)]
            if len(url) > 0:
                indices += [item.ConversationIndex]
                subjects += [item.subject]
                starts += [item.start.strftime("%Y-%m-%d %H:%M")]
                ends += [item.end.strftime("%Y-%m-%d %H:%M")]
                # modify += [item.LastModificationTime.strftime("%Y-%m-%d %H:%M")]
                teams_urls += url

        item_df = pd.DataFrame(
            {
                "index": indices,
                "subject": subjects,
                "start": pd.to_datetime(starts),
                "end": pd.to_datetime(ends),
                "url": teams_urls,
                "isShow": False,
            }
        )
        item_df = item_df.sort_values("start").reset_index(drop=True)

        pythoncom.CoUninitialize()

        # For debug
        # item_df = pd.read_csv("schedule.csv", parse_dates=["start", "end"])

        return item_df
    except pywintypes.com_error as e:
        if e.args[1]:
            logger.error(traceback.format_exc())
            raise OutlookReadError("Outlook is not installed.")
    except Exception as e:
        logger.error(traceback.format_exc())
        raise OutlookReadError(
            "An error occurred when loading the schedule from Outlook."
        )
