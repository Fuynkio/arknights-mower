#!/usr/bin/env python3
import datetime

import pandas as pd
import requests

from arknights_mower.solvers import record
from arknights_mower.solvers.skland import SKLand
from arknights_mower.utils.conf import load_conf, save_conf, load_plan, write_plan
from arknights_mower.utils import depot
from arknights_mower.utils.log import logger
from arknights_mower.utils.path import get_path
from arknights_mower.__main__ import main
from arknights_mower.data import agent_list, shop_items

from flask import Flask, send_from_directory, request, abort
from werkzeug.exceptions import NotFound
from flask_cors import CORS
from flask_sock import Sock

from simple_websocket import ConnectionClosed

import webview

import os
import multiprocessing
from threading import Thread
import json
import time
import sys
import mimetypes

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from functools import wraps

import pathlib

import tkinter
from tkinter import messagebox

import platform

mimetypes.add_type("text/html", ".html")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/javascript", ".js")

app = Flask(__name__, static_folder="dist", static_url_path="")
sock = Sock(app)
CORS(app)

conf = {}
plan = {}
mower_process = None
read = None
operators = {}
log_lines = []
ws_connections = []


def require_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if hasattr(app, "token") and request.headers.get("token", "") != app.token:
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


@app.route("/<path:path>")
def serve_index(path):
    return send_from_directory("dist", path)


@app.errorhandler(404)
def not_found(e):
    if (path := request.path).startswith("/docs/") and path.endswith("/"):
        try:
            return send_from_directory("dist" + path, "index.html")
        except NotFound:
            return send_from_directory("dist", "index.html")
    else:
        return send_from_directory("dist", "index.html")


@app.route("/conf", methods=["GET", "POST"])
@require_token
def load_config():
    global conf

    if request.method == "GET":
        conf = load_conf()
        return conf
    else:
        conf.update(request.json)
        save_conf(conf)
        return f"New config saved!"


@app.route("/plan", methods=["GET", "POST"])
@require_token
def load_plan_from_json():
    global plan

    if request.method == "GET":
        global conf
        plan = load_plan(conf["planFile"])
        return plan
    else:
        plan = request.json
        write_plan(plan, conf["planFile"])
        return f"New plan saved at {conf['planFile']}"


@app.route("/operator")
def operator_list():
    return agent_list


@app.route("/shop")
def shop_list():
    return shop_items


def read_log(conn):
    global operators
    global mower_process
    global log_lines
    global ws_connections

    try:
        while True:
            msg = conn.recv()
            if msg["type"] == "log":
                new_line = time.strftime("%m-%d %H:%M:%S ") + msg["data"]
                log_lines.append(new_line)
                log_lines = log_lines[-500:]
                for ws in ws_connections:
                    ws.send(new_line)
            elif msg["type"] == "operators":
                operators = msg["data"]
            elif msg["type"] == "update_conf":
                global conf
                conn.send(conf)
    except EOFError:
        conn.close()


@app.route("/depot/readdepot")
def read_depot():
    return depot.readcsv()


@app.route("/running")
def running():
    global mower_process
    return "false" if mower_process is None else "true"


@app.route("/start")
@require_token
def start():
    global conf
    global plan
    global mower_process
    global operators
    global log_lines

    if mower_process is not None:
        return "Mower is already running."

    # 创建 tmp 文件夹
    tmp_dir = get_path("@app/tmp")
    tmp_dir.mkdir(exist_ok=True)

    read, write = multiprocessing.Pipe()
    mower_process = multiprocessing.Process(
        target=main,
        args=(
            conf,
            plan,
            operators,
            write,
        ),
        daemon=False,
    )
    mower_process.start()

    Thread(target=read_log, args=(read,)).start()

    log_lines = []

    return "Mower started."


@app.route("/stop")
@require_token
def stop():
    global mower_process

    if mower_process is None:
        return "Mower is not running."

    mower_process.terminate()
    mower_process = None

    return "Mower stopped."


@sock.route("/log")
def log(ws):
    global ws_connections
    global log_lines

    ws.send("\n".join(log_lines))
    ws_connections.append(ws)

    try:
        while True:
            ws.receive()
    except ConnectionClosed:
        ws_connections.remove(ws)


@app.route("/dialog/file")
@require_token
def open_file_dialog():
    window = webview.active_window()
    file_path = window.create_file_dialog(dialog_type=webview.OPEN_DIALOG)
    if file_path:
        return file_path[0]
    else:
        return ""


@app.route("/dialog/folder")
@require_token
def open_folder_dialog():
    window = webview.active_window()
    folder_path = window.create_file_dialog(dialog_type=webview.FOLDER_DIALOG)
    if folder_path:
        return folder_path[0]
    else:
        return ""


@app.route("/dialog/save/img", methods=["POST"])
@require_token
def save_file_dialog():
    img = request.files["img"]
    if not img:
        return "图片未上传"
    window = webview.active_window()
    img_path = window.create_file_dialog(
        dialog_type=webview.SAVE_DIALOG,
        save_filename="plan.png",
        file_types=("PNG图片 (*.png)",),
    )
    if not img_path:
        return "保存已取消"
    if not isinstance(img_path, str):
        img_path = img_path[0]
    if os.path.exists(img_path) and platform.system() == "Linux":
        root = tkinter.Tk()
        root.withdraw()
        replace = messagebox.askyesno(
            "arknights-mower",
            f"同名文件{img_path}已存在，是否覆盖？",
        )
        root.destroy()
        if not replace:
            return f"保存已取消"
    img.save(img_path)
    return f"图片已导出至{img_path}"


@app.route("/check-maa")
@require_token
def get_maa_adb_version():
    try:
        asst_path = os.path.dirname(pathlib.Path(conf["maa_path"]) / "Python" / "asst")
        if asst_path not in sys.path:
            sys.path.append(asst_path)
        from asst.asst import Asst

        Asst.load(conf["maa_path"])
        asst = Asst()
        version = asst.get_version()
        asst.set_instance_option(2, conf["maa_touch_option"])
        if asst.connect(conf["maa_adb_path"], conf["adb"]):
            maa_msg = f"Maa {version} 加载成功"
        else:
            maa_msg = "连接失败，请检查Maa日志！"
    except Exception as e:
        maa_msg = "Maa加载失败：" + str(e)
    return maa_msg


@app.route("/maa-conn-preset")
@require_token
def get_maa_conn_presets():
    try:
        with open(
            os.path.join(conf["maa_path"], "resource", "config.json"),
            "r",
            encoding="utf-8",
        ) as f:
            presets = [i["configName"] for i in json.load(f)["connection"]]
    except:
        presets = []
    return presets


@app.route("/record/getMoodRatios")
def get_mood_ratios():
    return record.get_mood_ratios()


def str2date(target: str):
    try:
        return datetime.datetime.strptime(target, "%Y-%m-%d").date()
    except ValueError:
        return datetime.datetime.strptime(target, "%Y/%m/%d").date()


def date2str(target: datetime.date):
    try:
        return datetime.datetime.strftime(target, "%Y-%m-%d")
    except ValueError:
        return datetime.datetime.strftime(target, "%Y/%m/%d")


@app.route("/report/getReportData")
def get_report_data():
    record_path = get_path("@app/tmp/report.csv")
    try:
        format_data = []
        if os.path.exists(record_path) is False:
            logger.debug("基报不存在")
            return False
        df = pd.read_csv(record_path, encoding="gbk")
        data = df.to_dict("records")
        earliest_date = str2date(data[0]["Unnamed: 0"])

        for item in data:
            format_data.append(
                {
                    "日期": date2str(
                        str2date(item["Unnamed: 0"]) - datetime.timedelta(days=1)
                    ),
                    "作战录像": item["作战录像"],
                    "赤金": item["赤金"],
                    "龙门币订单": item["龙门币订单"],
                    "龙门币订单数": item["龙门币订单数"],
                    "每单获取龙门币": int(item["龙门币订单"] / item["龙门币订单数"]),
                }
            )

        if len(format_data) < 15:
            for i in range(1, 16 - len(format_data)):
                format_data.insert(
                    0,
                    {
                        "日期": date2str(earliest_date - datetime.timedelta(days=i + 1)),
                        "作战录像": "-",
                        "赤金": "-",
                        "龙门币订单": "-",
                        "龙门币订单数": "-",
                        "每单获取龙门币": "-",
                    },
                )
        logger.debug(format_data)
        return format_data
    except PermissionError:
        logger.info("report.csv正在被占用")


@app.route("/report/getHalfMonthData")
def get_half_month_data():
    record_path = get_path("@app/tmp/report.csv")
    try:
        format_data = []
        if os.path.exists(record_path) is False:
            logger.debug("基报不存在")
            return False
        df = pd.read_csv(record_path, encoding="gbk")
        data = df.to_dict("records")
        earliest_date = datetime.datetime.now()

        begin_make_orundum = (earliest_date + datetime.timedelta(days=1)).date()
        print(begin_make_orundum)
        if len(data) >= 15:
            for i in range(len(data) - 1, -1, -1):
                if 0 < i < len(data) - 15:
                    data.pop(i)
                else:
                    logger.info("合成玉{}".format(data[i]["合成玉"]))
                    if data[i]["合成玉"] > 0:
                        begin_make_orundum = str2date(data[i]["Unnamed: 0"])
        else:
            for item in data:
                if item["合成玉"] > 0:
                    begin_make_orundum = str2date(item["Unnamed: 0"])
        if begin_make_orundum > earliest_date.date():
            return format_data
        total_orundum = 0
        for item in data:
            total_orundum = total_orundum + item["合成玉"]
            format_data.append(
                {
                    "日期": date2str(
                        str2date(item["Unnamed: 0"]) - datetime.timedelta(days=1)
                    ),
                    "合成玉": item["合成玉"],
                    "合成玉订单数量": item["合成玉订单数量"],
                    "抽数": round((item["合成玉"] / 600), 1),
                    "累计制造合成玉": total_orundum,
                }
            )

        if len(format_data) < 15:
            earliest_date = str2date(data[0]["Unnamed: 0"])
            for i in range(1, 16 - len(format_data)):
                format_data.insert(
                    0,
                    {
                        "日期": date2str(earliest_date - datetime.timedelta(days=i + 1)),
                        "合成玉": "-",
                        "合成玉订单数量": "-",
                        "抽数": "-",
                        "累计制造合成玉": 0,
                    },
                )
        logger.debug(format_data)
        return format_data
    except PermissionError:
        logger.info("report.csv正在被占用")


@app.route("/test-email")
@require_token
def test_email():
    msg = MIMEMultipart()
    msg.attach(MIMEText("arknights-mower测试邮件", "plain"))
    msg["Subject"] = conf["mail_subject"] + "测试邮件"
    msg["From"] = conf["account"]
    try:
        s = smtplib.SMTP_SSL("smtp.qq.com", 465, timeout=10.0)
        s.login(conf["account"], conf["pass_code"])
        s.sendmail(conf["account"], conf["account"], msg.as_string())
    except Exception as e:
        return "邮件发送失败！\n" + str(e)
    return "邮件发送成功！"


@app.route("/test-serverJang-push")
@require_token
def test_serverJang_push():
    try:
        response = requests.get(
            f"https://sctapi.ftqq.com/{conf['sendKey']}.send",
            params={"title": "arknights-mower推送测试", "desp": "arknights-mower推送测试"},
        )

        if response.status_code == 200 and response.json().get("code") == 0:
            return "发送成功"
        else:
            return "发送失败 : " + response.json().get("message", "")
    except Exception as e:
        return "发送失败 : " + str(e)


@app.route("/check-skland")
@require_token
def test_skland():
    return SKLand(conf["skland_info"]).test_connect()
