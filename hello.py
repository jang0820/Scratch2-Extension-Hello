#!/usr/bin/env python3
"""
reference to s2aio(https://github.com/MrYsLab/s2aio)
create an small example to exchange data between Scratch and Python Web Server(aiohttp)
Scratch2.0 Offline, Python3.6, Window10
"""

import argparse
import asyncio
import configparser
import os
import os.path
import signal
import sys
import webbrowser
import time
#import logging
from aiohttp import web

class HELLO:
    def __init__(self, language='3', sleeper=10):
        #logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s : %(message)s', filename='mylog.txt')
        #logging.info("init")
        self.sleeper = sleeper
        self.scratch_executable = '"C:/Program Files (x86)/Scratch 2/Scratch 2.exe"'
        #使用-l 1指定為英文，預設使用繁體中文(-l 3)
        scratch_block_language_dict = {'1': 's2aio_base.sb2', '3': 's2aio_base_zh_TW.sb2'}
        self.windows_wait_time = 3
        self.scratch_project = 'ScratchFiles/ScratchProjects/' + scratch_block_language_dict[language]
        # 設定poll回應值
        self.poll_reply = ""
        # poll watchdog的時間戳記
        self.poll_time_stamp = 0.0
        self.loop = None

    async def kick_off(self, my_loop):
        """
        start web server and scratch2.0
        """
        self.loop = my_loop
        try:
            app = web.Application()
            app.router.add_route('GET', '/poll', self.poll)
            app.router.add_route('GET', '/send_hi', self.send_hi)
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, '127.0.0.1', 50209)
            await site.start()
            # start scratch
            os_string = "start /b " + self.scratch_executable + ' ' + self.scratch_project
            await asyncio.sleep(self.windows_wait_time)
            os.system(os_string)
            await self.poll_watchdog()
        except:
            pass

    async def poll(self, request):
        """
        scratch use poll to get data from web server
        """
        self.poll_time_stamp = self.loop.time()
        total_reply = self.poll_reply
        self.poll_reply = ""
        # send the HTTP response
        # 資料回傳給scratch，一行一筆資料，key與value中間間隔一個空白鍵
        return web.Response(headers={"Access-Control-Allow-Origin": "*"},
                            content_type="text/html", charset="ISO-8859-1", text=total_reply)

    async def send_hi(self, request):
        """
        when get send_hi from scratch to web server, web server return hello 
        to scratch using return_hi reporter.
        當scratch發送send_hi命令到網頁伺服器，網頁伺服器將回應資料放置於poll_reply，
        scratch會定期瀏覽poll網址，獲得回應的資料，return_hi為scratch所指定的reporter接收變數，
        hello為變數return_hi的值
        """
        self.poll_reply += 'return_hi'+' '+'hello' + '\n'

    async def poll_watchdog(self):
        """
        This method is enabled for scratch clients. It monitors to see if polls are no longer being
        sent, and if so, shuts down the server. It waits 2 seconds before shutting down.
        """
        await asyncio.sleep(self.sleeper)
        while True:
            await asyncio.sleep(1)
            current_time = self.loop.time()
            if current_time - self.poll_time_stamp > 1:
                for t in asyncio.Task.all_tasks(self.loop):
                    t.cancel()
                self.loop.run_until_complete(asyncio.sleep(.1))
                self.loop.stop()
                self.loop.close()
                sys.exit(0)

    async def keep_alive(self):
        """
        This method is used to keep the server up and running when not connected to Scratch
        """
        while True:
            await asyncio.sleep(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", dest="language", default="3", help=" 1=English(default) 3=Chinese(zh-TW)")
    parser.add_argument("-s", dest="sleeper", default="10", help="Set timeout to allow Scratch to initialize.")
    args = parser.parse_args()
    
    language_type = args.language
    sleep = int(args.sleeper)

    hello = HELLO(language=language_type, sleeper=sleep)
    the_loop = asyncio.get_event_loop()
    try:
        the_loop.run_until_complete((hello.kick_off(the_loop)))
    except:
        sys.exit(0)
    time.sleep(2)

    # signal handler function called when Control-C occurs
    def signal_handler(signal, frame):
        print("Control-C detected. See you soon.")
        for t in asyncio.Task.all_tasks(loop):
            t.cancel()
            the_loop.run_until_complete(asyncio.sleep(.1))
            the_loop.stop()
            the_loop.close()
        sys.exit(0)
    # listen for SIGINT
    signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)

    loop = asyncio.get_event_loop()
    try:
        loop.run_forever()
        loop.stop()
        loop.close()
    except:
        pass
