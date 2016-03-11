#coding=utf-8
from twisted.python import log
from twisted.web import http, proxy
from twisted.internet import endpoints, reactor
import time
from dealhttpdata import *
import urllib2
from pprint import pprint
import argparse

change_resp_flag = False
measure_whole_flag = False
change_header_flag = True


#控制从http server 发往 浏览器的数据包
class ProxyClient(proxy.ProxyClient):

    def __init__(self, command, rest, version, headers, data, father):
        proxy.ProxyClient.__init__(self, command, rest, version, headers, data, father)
        self.connectTime = None
        self.dataType = None

    #修改header
    #header 是一行行被处理的
    def handleHeader(self, key, value):
        #print (key, value)
        if key == 'Content-Type':
            self.dataType = value
        proxy.ProxyClient.handleHeader(self, key, value)

    #修改http response response 可能有多种编码方式
    #因此修改有时可能会出错
    def handleResponsePart(self, resp):
        #print resp

        #设置为可选 修改会让时间变得不准确
        if change_resp_flag:
            print "Cotent type: ", self.dataType
            n_w, o_w = ask_input(" change response ")
            if n_w != "NOMODI!":
                resp = modify_data(resp, n_w, o_w)
        proxy.ProxyClient.handleResponsePart(self, resp)

    def connectionMade(self):
        #建立连接, 开始发送请求，记录开始时间
        self.connectTime = time.time()
        proxy.ProxyClient.connectionMade(self)

    def handleResponseEnd(self):
        if self._finished:
            print "request", self.dataType, "use time: ", \
                time.time() - self.connectTime, "seconds"
        try:
            proxy.ProxyClient.handleResponseEnd(self)
        except Exception as e:
            pass

    def connectionLost(self, reason):
        proxy.ProxyClient.connectionLost(self, reason)


class ProxyClientFactory(proxy.ProxyClientFactory):
    protocol = ProxyClient


class ProxyRequest(proxy.ProxyRequest):
    protocols = dict(http=ProxyClientFactory)


#控制从 浏览器到 http server 请求的数据包
class Proxy(proxy.Proxy):
    requestFactory = ProxyRequest

    #可以修改发出的header
    def headerReceived(self, line):
        #print 'header line: ', line
        proxy.Proxy.headerReceived(self, line)

    #先调用这个方法，这个方法会调用lineReceived
    def dataReceived(self, data):

        # 修改发送的数据
        #print data
        #开始请求网页
        #无法从http包直观看出哪一个是结束的包（一个请求会对应多个包）因此整个网页的请求用requests代替
        #因为页面加载后仍然可能又使用javascript请求其他资源
        split_data = data.split("\r\n")
        print "start request", split_data[0]

        if change_header_flag:
            pprint(split_data[1:])

        if change_header_flag:
            n_w, o_w = ask_input(" change header ")
            data = modify_data(data, n_w, o_w)

        if measure_whole_flag:
            if data.startswith('GET'):
                req_url, secs = time_get_header(data)
                print "whole request ", req_url, "use time: ", secs, "seconds"

            if data.startswith('POST'):
                req_url, header_dict = parse_header(data)
                start_time = time.time()
                if not req_url.startswith("http://"):
                    req_url += "http://"

                try:
                    req = urllib2.Request(req_url, data, header_dict)
                    response = urllib2.urlopen(req)
                    print "whole post use : ", time.time() - start_time
                    print response.read()

                except Exception as e:
                    print "POST wrong here: "
                    print e

        proxy.Proxy.dataReceived(self, data)


class ProxyFactory(http.HTTPFactory):
    protocol = Proxy


port_ = "1543"


if __name__ == '__main__':
    #增加命令行选项，使用 -h 查看使用说明
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", help="set listen port ")
    parser.add_argument("-r", "--response", help="change response ", action="store_true")
    parser.add_argument("-w", "--whole", help="measure whole ", action="store_true")
    args = parser.parse_args()
    if args.port:
        port_ = args.port
        print "serve at port ", port_
    if args.whole:
        print "measure whole url on"
        measure_whole_flag = True
    if args.response:
        print "change response on "
        change_resp_flag = True
        change_header_flag = False

    def shutdown(reason, new_reactor, stopping=[]):
        if stopping:
            return
        stopping.append(True)
        if reason:
            pass
            log.msg(reason.value)
        new_reactor.callWhenRunning(new_reactor.stop)


    #设定监听地址
    #将浏览器的代理服务器设置为 localhost:1543
    portstr = "tcp:"+port_+":interface=localhost"
    #设定记录打印的地方，设置为标准输出
    #log.startLogging(sys.stdout)
    #设置代理服务器访问地址
    endpoint = endpoints.serverFromString(reactor, portstr)
    #设置代理服务器处理网络协议的方式
    d = endpoint.listen(ProxyFactory())
    #设置出错时的回调函数
    d.addErrback(shutdown, reactor)

    #启动代理服务器的事件循环
    reactor.run()
