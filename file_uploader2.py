from flask import Flask, request, send_from_directory, render_template_string
from flask_caching import Cache
app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
import os
import qrcode
import base64
from io import BytesIO
import socket
import webbrowser
import time
import logging
from datetime import datetime
import sys

print('''
//
//                       _oo0oo_
//                      o8888888o
//                      88" . "88
//                      (| -_- |)
//                      0\  =  /0
//                    ___/`---'\___
//                  .' \\|     |// '.
//                 / \\|||  :  |||// \\
//                / _||||| -:- |||||- \\
//               |   | \\\\\  -  /// |   |
//               | \\_|  ''\\---/''  |_/ |
//               \\  .-\\__  '-'  ___/-. /
//             ___'. .'  /--.--\\  `. .'___
//          ."" '<  `.___\\_<|>_/___.' >' "".
//         | | :  `- \\`.;`\\ _ /`;.`/ - ` : | |
//         \\  \\ `_.   \\_ __\\ /__ _/   .-` /  /
//     =====`-.____`.___ \\_____/___.-`___.-'=====
//                       `=---='
//     ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
//
//               佛祖保佑         永无BUG
//
//     ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
//                使用完毕之后关闭此窗口
//                       
//                       v 2.0
//                       
//                 by h9h 2024/05/17
//     ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
''')

template = '''
<!DOCTYPE html>
<html>
<head>
    <title>同Wi-Fi局域网文件传输工具</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            margin: 0;
            background-color: #f0f0f0;
            font-family: Arial, sans-serif;
            padding: 10px;
            min-height: 100vh;
        }
        h1 {
            color: #333;
            text-align: center;
        }
        h2 {
            margin-top: 10px;
        }
        h3 {
            margin-top: 10px; 
            color: red;
            text-align: center;
        }
        form {
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 100%;
            max-width: 400px;
        }
        input[type="submit"] {
            margin-top: 10px;
            padding: 5px 20px;
            background-color: #008CBA; 
            border-color: #008CBA;
            color: white;
            text-align: center;
            text-decoration: none;
            font-size: 20px;
            border-radius:15px;
            z-index: 5555;
        }
        input[type="submit"]:hover {
            background-color: #007B9A;
        }
        input[type="file"]::file-selector-button {
            display: none;
        }
        label {
            margin-top: 10px;
            padding: 5px 10px;
            font-weight: 500;
            color: white;
            background-color: #008CBA;
            border-radius:15px;
        }
        @media (max-width: 600px) {
            h1 {
                font-size: 24px;
            }
            h2 {
                font-size: 20px;
            }
            h3 {
                color: red;
                font-size: 16px;
            }
        }
        .overlay {
            display: none;
            position: fixed;
            width: 100%;
            height: 100%;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0,0,0,0.5);
            z-index: 6666;
            cursor: pointer;
        }
        #loader {
            display: none;
            border: 16px solid #f3f3f3;
            border-radius: 50%;
            border-top: 16px solid #3498db;
            width: 120px;
            height: 120px;
            -webkit-animation: spin 2s linear infinite;
            animation: spin 2s linear infinite;
            position: fixed;
            z-index: 999999999;
        }
        @-webkit-keyframes spin {
            0% { -webkit-transform: rotate(0deg); }
            100% { -webkit-transform: rotate(360deg); }
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        #drop-area {
            border: 2px dashed #008CBA;
            border-radius: 15px;
            padding: 30px;
            margin-top:10px;
            width: 100%;
            max-width: 200px;
            text-align: center;
            color: #333;
        }
        @media screen and (max-width: 600px) {
            #links {
                width: 80vw;
            }
        }
        @media screen and (min-width: 601px) {
            #links {
                width: 360px;
            }
        }
    </style>
</head>
<body>
    <h1>同Wi-Fi局域网文件传输工具</h1>
    <h2>手机端扫描二维码访问</h2>
    <h3>需要关闭防火墙且所有设备在同一网络<br/>部分手机只支持单文件上传</h3>
    {% if is_local %}
    <a href="/open_file_path">打开文件保存处</a>
    {% endif %}
    
    {% if download_links %}
    <div id="links">
        <ul style="margin-top:10px; padding: 10px; border:1px solid #ccc; font-size: 1rem; list-style-type: none;">
        {% for item in download_links %}
            <li style="display: flex; justify-content: space-between;">
                <a style=" text-align: left;" href="{{ url_for('download_file', item=item.caption) }}">下载 {{ shorten(item.caption, 20) }}</a> 
                {% if is_local %}
                <a style=" text-align: right;" href="{{ url_for('delete_item', item=item.caption) }}">删除</a>
                {% endif %}
            </li>
        {% endfor %}
        </ul>
    </div>
    {% endif %}

    {% if is_local %}
    <div id="drop-area" class="drop-area">
        <p>拖动文件到此处分享</p>
    </div>
    {% endif %}

    <form id="file-form" method="POST" action="" enctype="multipart/form-data">
        {{ img_tag|safe }}
        {% if not is_local %}
        <label for="file_select">选择单或多文件</label>
        <input type="file" hidden="hidden" id="file_select" name="files" multiple onchange="displayFileNames(this)">
        <ul id="fileNames" hidden="hidden" style="width: 100%; text-align: left; margin-top:10px; border:1px solid #ccc; padding: 10px; font-size: 1rem; list-style-type: none;"></ul>
        <input type="submit" value="点击上传" onclick="loading();">
        {% endif %}
        <div style="width: 100%; height: 1.5rem; text-align: center;margin-top:10px">by h9h</div>
    </form>
    <div id="overlay" class="overlay"></div>
    <div id="loader" class="loader"></div>
</body>
<script type="text/javascript">
    
    function displayFileNames(inputElement){
        var fileNamesList = document.getElementById('fileNames');
        fileNamesList.style.display = "block";
        fileNamesList.innerHTML = "";
        for(var i=0; i<inputElement.files.length; i++){
            fileNamesList.innerHTML += "<li>" + inputElement.files[i].name + "</li>";
        }
    }

    function loading() {
        document.getElementById("overlay").style.display = "block";
        document.getElementById("loader").style.display = "block";
    }

    var dropArea = document.getElementById('drop-area');
    dropArea.addEventListener('dragenter', preventDefaults, false);
    dropArea.addEventListener('dragleave', preventDefaults, false);
    dropArea.addEventListener('dragover', preventDefaults, false);
    dropArea.addEventListener('drop', handleDrop, false);

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function handleDrop(e) {
        e.preventDefault();
        var dt = e.dataTransfer;
        var files = dt.files;
        handleFiles(files);
    }

    function handleFiles(files) {
        var formData = new FormData();
        for (var i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }
        fetch('/pc', {
            method: 'POST',
            body: formData
        }).then(response => response.text()).then(data => {
            window.location.href="/";
        }).catch(error => {
            console.error(error);
            alert('上传失败');
        });
    }
</script>
</html>
'''
app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.disabled = True
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
UPLOAD_FOLDER = './files'
download_links = []
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_time():
    now = datetime.now()
    formatted_now = now.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_now

# 定义 shorten 函数
def shorten(str, maxLength):
    if len(str) > maxLength:
        return str[:int(maxLength/2)] + '...' + str[-int(maxLength/2):]
    return str

# 使用 context_processor 将函数添加到模板上下文中
@app.context_processor
def utility_processor():
    return {"shorten": shorten}

def is_local_request(request):
    remote_address = request.remote_addr
    local_ip = socket.gethostbyname(socket.gethostname())
    # print("local: " + local_ip)
    print(f'{get_time()} 来访主机: {remote_address}')
    return local_ip == remote_address

@app.route('/pc', methods=['GET', 'POST'])
def upload_file_from_pc():
    is_local = is_local_request(request)
    if request.method == 'POST':
        files = request.files.getlist("files")
        if not files or files[0].filename == '':
            print("No file uploaded")
            return '<script> alert("请先选择文件！！！");window.location.href="/";</script>'
        for file in files:
            filename = file.filename
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            download_links = cache.get('download_links') or []
            card_dict = {}
            card_dict["caption"] = filename
            download_links.append(card_dict)
            cache.set('download_links', download_links)
    download_links = cache.get('download_links') or [] 
    return render_template_string(template, img_tag=img_tag, download_links=download_links, is_local=is_local)

@app.route('/', methods=['GET', 'POST'])
def upload_file_from_mobile():
    is_local = is_local_request(request)
    if request.method == 'POST':
        T1 = time.time()
        files = request.files.getlist("files")
        if not files or files[0].filename == '':
            print("No file uploaded")
            return '<script> alert("请先选择文件！！！");window.location.href="/";</script>'
        for file in files:
            filename = file.filename
            print(f'上传文件名：{filename}')
            file.save(os.path.join(UPLOAD_FOLDER, filename))
        T2 = time.time()
        print('本次上传耗时时间:%s毫秒' % ((T2 - T1)*1000))
        return '<script> alert("上传成功！文件保存在本程序目录files文件夹");window.location.href="/";</script>'
    download_links = cache.get('download_links') or [] 
    return render_template_string(template, img_tag=img_tag, download_links=download_links, is_local=is_local)

# 运行打包成exe形式的下载
@app.route('/download/<item>')
def download_file(item):
    BASE_DIR = os.path.dirname(os.path.realpath(sys.executable))
    FILE_FOLDER = os.path.join(BASE_DIR, UPLOAD_FOLDER)
    remote_address = request.remote_addr
    print(f'{get_time()} 来访主机: {remote_address} 下载文件: {item}')
    return send_from_directory(FILE_FOLDER, item, as_attachment=True)

# 直接运行py脚本的下载
# @app.route('/download/<item>')
# def download_file(item):
#     return send_from_directory(UPLOAD_FOLDER, item)

@app.route('/delete/<item>')
def delete_item(item):
    download_links = cache.get('download_links')
    download_links = [d for d in download_links if d.get('caption') != item]
    cache.set('download_links', download_links)
    return '<script>window.location.href="/";</script>'

@app.route('/open_file_path')
def open_file_path():
    absolute_path = os.path.abspath(UPLOAD_FOLDER)
    os.startfile(absolute_path)
    return '<script>window.location.href="/";</script>'

if __name__ == '__main__':
    ip_address = socket.gethostbyname_ex(socket.gethostname())[2][-1]
    for item in socket.gethostbyname_ex(socket.gethostname())[2]:
        print(f'本机地址：{item}')
    ip_port = 80
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=1,
    )
    qr.add_data('http://' + ip_address + ':' + str(ip_port))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    img_tag = f'<img src="data:image/png;base64,{img_str}" alt="qr-code" style="margin-top: 10px;max-width: 50%;"/>'
    webbrowser.open('http://' + ip_address + ':' + str(ip_port))
    app.run(host='0.0.0.0', port=80)


