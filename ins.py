#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/7/19 13:31
# @Author : YXH
# @Email : 874591940@qq.com
# @desc : Ins自动发帖

import os
import time
import configparser
import pyperclip
import win32api
import win32con
import psutil

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

from pynput.keyboard import Listener, Key
from multiprocessing import Process

from MyUtils.chrome.selenium_chrome import ChromeDriver

# “run”进程对象
process_run = None


class InsPost(ChromeDriver):
    def __init__(self, chrome_data_path, config, auth_proxy_info):
        """
        初始化参数，打开浏览器
        :param chrome_data_path: chrome数据存放路径
        :param config: 配置参数
        :param auth_proxy_info: 代理
        """
        auth_proxy_info = {
            'host': '38.79.90.27',
            'port': 12440,
            'username': '874591940',
            'password': '25EA8B54ABF8B326DF8A684E8014FD23',
            'scheme': 'http'
        }
        super(InsPost, self).__init__(auth_proxy_info=auth_proxy_info, chrome_data_path=chrome_data_path, phone_info={'deviceName': 'iPhone 6/7/8'},lang='en-US')
        self.config = config
        self.chrome.get('https://wtfismyip.com/')

    def post_article(self):
        """
        发帖
        :return:
        """
        # 若没有图片，则退出程序
        if len(self.config['image']['list']) == 0:
            print('没有图片了，程序结束！')
            self.chrome.quit()
            exit(0)
        # 获取图片
        image_path = self.config['image']['list'][0]
        error_num = 0
        # 错误重试
        while error_num <= self.config['config']['retry_num']:
            if error_num:
                print('正在进行第{}次重试！'.format(error_num))
            try:
                # 打开ins页面
                self.chrome.get('https://www.instagram.com/')
                # 等待页面加载完成
                logo_image = '//*[@id="react-root"]/section/nav[1]/div/div/header/div/h1/div/a/img'
                self.wait.until(ec.presence_of_element_located((By.XPATH, logo_image)))
                # 点击发帖按钮
                add_btn = '//*[@id="react-root"]/section/nav[2]/div/div/div[2]/div/div/div[3]'
                self.wait.until(ec.presence_of_element_located((By.XPATH, add_btn))).click()
                # 选择图片路径
                self.choose_image(image_path)
                # 点击下一步
                next_btn = '//*[@id="react-root"]/section/div[1]/header/div/div[2]/button'
                self.wait.until(ec.presence_of_element_located((By.XPATH, next_btn))).click()
                # 输入关键字
                text_area = '//*[@id="react-root"]/section/div[2]/section[1]/div[1]/textarea'
                keywords = self.get_keywords()
                self.wait.until(ec.presence_of_element_located((By.XPATH, text_area))).send_keys(keywords)
                # 点击分享
                post_btn = '//*[@id="react-root"]/section/div[1]/header/div/div[2]/button'
                self.wait.until(ec.presence_of_element_located((By.XPATH, post_btn))).click()
                # 点击分享后，等待页面加载完成，即表示发送成功
                self.wait.until(ec.presence_of_element_located((By.XPATH, logo_image)))
                # 删除数据
                self.delete_data()
                return True
            except Exception as e:
                print('错误原因：{}'.format(e))
                error_num += 1
        return False

    def choose_image(self, image_path):
        """
        从系统对话框中选择图片
        :param image_path: 图片路径
        :return:
        """
        # 复制文件路径到剪切板
        pyperclip.copy(image_path)
        # 等待程序加载 时间 看你电脑的速度 单位(秒)
        time.sleep(self.config['image']['wait_time'])
        # 发送 ctrl（17） + V（86）按钮
        win32api.keybd_event(17, 0, 0, 0)
        win32api.keybd_event(86, 0, 0, 0)
        win32api.keybd_event(86, 0, win32con.KEYEVENTF_KEYUP, 0)  # 松开按键
        win32api.keybd_event(17, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(1)
        win32api.keybd_event(13, 0, 0, 0)  # (回车)
        win32api.keybd_event(13, 0, win32con.KEYEVENTF_KEYUP, 0)  # 松开按键
        win32api.keybd_event(13, 0, 0, 0)  # (回车)
        win32api.keybd_event(13, 0, win32con.KEYEVENTF_KEYUP, 0)

    def get_keywords(self):
        """
        从关键词文件中取出若干关键词
        :return: 关键词
        """
        string = ''
        with open(self.config['keywords']['path'], 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            # 读取若干行
            keywords = lines[:self.config['keywords']['num']]
            # 若没有空格
            for word in keywords:
                word = word.replace('\n', '')
                string += word if word.endswith(' ') else word + ' '
        return string or self.config['keywords']['default_keywords']

    def delete_data(self):
        """
        删除发送成功的图片和关键字
        :return:
        """
        # 从数组中删除
        image_path = self.config['image']['list'].pop(0)
        # 删除图片
        try:
            os.remove(image_path)
        except Exception as e:
            print('图片删除失败，原路径：{}，失败原因：{}'.format(image_path, e))
        with open(self.config['keywords']['path'], 'r') as f:
            lines = f.readlines()
        # 删除关键字
        with open(self.config['keywords']['path'], 'w') as f:
            f.writelines(lines[self.config['keywords']['num']:])

    def run(self):
        """
        启动
        :return:
        """
        time.sleep(self.config['chrome']['wait_time'])
        # 最大发帖数
        for i in range(self.config['user']['max_post_num']):
            if not self.post_article():
                print('\t\t第{}次发帖失败，重试次数过多，开始切换下一个账号！'.format(i + 1))
                break
            print('\t\t第{}次发帖成功！'.format(i + 1))
        self.chrome.quit()


def get_config():
    """
    读取配置文件，初始化参数
    :return:
    """
    config = {}
    # 读取配置文件
    cp = configparser.ConfigParser()
    cp.read('./config.ini', encoding="utf-8")
    # 按照键值对形式保存
    for header in cp.sections():
        if header not in config:
            config[header] = {}
        for key, value in cp.items(header):
            value = value.strip()
            try:
                # 自动转为整型
                config[header][key] = int(value)
                continue
            except:
                pass
            # 路径类
            try:
                if 'path' in key or 'dir' in key:
                    config[header][key] = os.path.abspath(value)
                    continue
            except:
                pass
            config[header][key] = value
    # chrome浏览器对象列表
    # 依次获取各浏览器数据保存位置
    for filename in os.listdir(config['chrome']['data_dir']):
        # 初始化数组
        if 'start_order' not in config['chrome']:
            config['chrome']['start_order'] = []
        if 'start_dict' not in config['chrome']:
            config['chrome']['start_dict'] = {}
        full_path = os.path.abspath(os.path.join(config['chrome']['data_dir'], filename))
        if os.path.isdir(full_path):
            # 获取chrome下标
            try:
                chrome_index = int(filename.replace(config['chrome']['base_name'], ''))
            except:
                chrome_index = -1
            # 若chrome小于指定的启动位置，则跳过
            # if chrome_index >= config['chrome']['start_index']:
            config['chrome']['start_order'].append(chrome_index)
            config['chrome']['start_dict'][chrome_index] = full_path
    # chrome启动顺序排序
    config['chrome']['start_order'].sort()
    # 获取图片列表
    for filename in os.listdir(config['image']['dir']):
        # 初始化数组
        if 'list' not in config['image']:
            config['image']['list'] = []
        full_path = os.path.abspath(os.path.join(config['image']['dir'], filename))
        try:
            file_type = full_path.lower().rsplit('.')[-1]
            if file_type in ['jpg', 'jpeg', 'png', 'bmp']:
                config['image']['list'].append(full_path)
        except:
            continue
    return config


def run():
    """
    启动主程序
    :return:
    """

    proxy_list = [
        {
            'host': '2.56.100.22',
            'port': 33333,
            'username': '874591940',
            'password': '25EA8B54ABF8B326DF8A684E8014FD23',
            'scheme': 'http'
        },
        {
            'host': '38.79.90.27',
            'port': 12440,
            'username': '874591940',
            'password': '25EA8B54ABF8B326DF8A684E8014FD23',
            'scheme': 'http'
        }
    ]

    # 获取配置
    config = get_config()
    index = 1
    for i in range(config['config']['loop_num']):
        # 默认从指定位置开始，第二次循环则从1开始
        start = 1 if i != 0 else config['chrome']['start_index']
        print('第{}次循环开始，起始位置：{}'.format(i + 1, start))
        # 依次运行
        for start_order in config['chrome']['start_order']:
            # 若有发送限制，则超过就停止
            if config['user']['max_num'] != -1 and index >= config['user']['max_num']:
                print('程序结束，已发送{}个账号'.format(config['user']['max_num']))
                return True
            # 默认从指定位置开始，第二次循环则从1开始
            if start_order < start:
                continue
            print('\t第{}个账号正在发送中！'.format(start_order))
            InsPost(config['chrome']['start_dict'][start_order], config, proxy_list[index - 1])  # .run()
            input('::::')
            index += 1


def on_release(key):
    """
    键盘监听：暂停、继续、结束程序。
    :param key:
    :return:
    """
    # 暂停、继续任务
    if key == Key.f7:
        # 暂停“run”进程
        if process_run.status() == 'running':
            print('程序已暂停，请按enter键继续任务，或按backsapce键结束任务。')
            process_run.suspend()
        # 继续“run”进程
        elif process_run.status() == 'stopped':
            print('程序已继续，可以按enter键暂停任务，或按backsapce键结束任务。')
            process_run.resume()
    # 结束任务
    elif key == Key.f8:
        print('程序已结束。')
        os._exit(0)


def thread_run():
    # 启动“run”进程
    p2 = Process(target=run)
    p2.start()
    # 获取“run”进程对象

    global process_run
    process_run = psutil.Process(p2.pid)
    # 键盘监听
    with Listener(on_release=on_release) as listener:
        listener.join()


if __name__ == '__main__':
    run()
    input('press on Enter:')
    # pyinstaller -Fw ins.py
