#coding=utf-8
import requests


# http 数据以两个\r\n分割响应和头部 有时候只有头部
def split_raw_http(data):
    endpoint = '\r\n\r\n'
    return data.split(endpoint)


#将header转换为键值对  urlparse.parse_qsl(headers)
def split_raw_header(header):
    split_data = header.split("\r\n")
    split_data = split_data[1:]
    header_dict = {}
    for d in split_data:
        if d.strip():
            index = d.find(':')  
            k = d[:index]
            v = d[index+1:]
            header_dict[k] = v
    return header_dict


# GET header to server
def time_get_header(data):
    req_url, header_dict = parse_header(data)
    secs = requests.get(req_url, params=header_dict).elapsed.total_seconds()
    return req_url, secs


def parse_header(data):
    req_url = data.split('\r\n')[0].split()[1]
    header_dict = split_raw_header(split_raw_http(data)[0])
    return req_url, header_dict


def modify_data(data, new_word, old_word=None):
    if old_word is None:
        data = new_word
    else:
        return data.replace(old_word, new_word)

    return data


def ask_input(prompt=None):
    pro = " content format(can omit old_word): new_word,old_word"
    if prompt:
        pro = prompt + pro
    words = raw_input(pro)
    if words.find(",") == -1:
        n_w = words.strip()
        o_w = None
    else:
        n_w, o_w = words.split(",")
    return n_w, o_w


