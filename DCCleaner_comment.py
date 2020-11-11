from bs4 import BeautifulSoup
import js2py
import json
import lxml.html
import pyperclip
import re
import requests
import time

# JS For decoding Service Code
decode_service_code = '''
    function get_service_code(service_code, r_value){
    var a,e,n,t,f,d,h,i = "yL/M=zNa0bcPQdReSfTgUhViWjXkYIZmnpo+qArOBs1Ct2D3uE4Fv5G6wHl78xJ9K",
    o = "",
    c = 0;
    for (r_value = r_value.replace(/[^A-Za-z0-9+/=]/g,""); c < r_value.length;) {
        t = i.indexOf(r_value.charAt(c++));
        f = i.indexOf(r_value.charAt(c++));
        d = i.indexOf(r_value.charAt(c++));
        h = i.indexOf(r_value.charAt(c++));
        a = t << 2 | f >> 4;
        e = (15 & f) << 4 | d >> 2;
        n = (3 & d) << 6 | h;
        o += String.fromCharCode(a);
        64 != d && (o += String.fromCharCode(e));
        64 != h && (o += String.fromCharCode(n));
        }
        var tvl = o;
        var fi = parseInt(tvl.substr(0,1));
        fi = fi > 5 ? fi - 5 : fi + 4;
        var _r = tvl.replace(/^./, fi);
        var _rs = _r.split(",");
        var replace = "";
        for (e = 0; e < _rs.length; e++) replace += String.fromCharCode(2 * (_rs[e] - e - 1) / (13 - e - 1));
        return service_code.replace(/(.{10})$/, replace)
    }
    '''
decode_service_code = js2py.eval_js(decode_service_code)

# Make New Login Session
sess = requests.Session()
sess.headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Whale/2.8.107.16 Safari/537.36"
}


def delete_comment(dcid, gall_url):
    # COMMENT DELETE Headers
    COMMENT_DELETE_REQ_HEADERS = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "gallog.dcinside.com",
        "Origin": "https://gallog.dcinside.com",
        "Referer": "https://gallog.dcinside.com/" + gall_url,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "X-Requested-With": "XMLHttpRequest"
    }

    # Parse Comments
    gallog_comments = sess.get("https://gallog.dcinside.com/" + gall_url)
    comments_parsed = lxml.html.fromstring(gallog_comments.text)

    # Get Values for Service Code
    hidden_r = comments_parsed.xpath('//*[@id="container"]/article/div/section/script[2]')[0].text.strip()
    hidden_r = re.findall("_d\('([\w\0-Z]*)'\)", hidden_r)[0]
    hidden_svc_code = comments_parsed.xpath('//*[@id="container"]/article/div/section/div[1]/input')[0].get("value")

    # Generate Service Code
    svc_code = decode_service_code(hidden_svc_code, hidden_r)

    # Get Comment Information
    comment_gall = comments_parsed.xpath('//*[@id="container"]/article/div/section/div[1]/div/ul/li[1]/div[3]/span/a')[
        0].text
    comment_no = comments_parsed.xpath('//*[@id="container"]/article/div/section/div[1]/div/ul/li[1]')[0].get("data-no")
    comment_delete_url = "https://gallog.dcinside.com/" + dcid + "/ajax/log_list_ajax/delete"

    COMMENT_DELETE_REQ_DATA = {
        "ci_t": sess.cookies['ci_c'],
        "no": comment_no,
        "service_code": svc_code
    }

    # POST & GET Result
    delete_result = sess.post(comment_delete_url, data=COMMENT_DELETE_REQ_DATA, headers=COMMENT_DELETE_REQ_HEADERS)
    result = json.loads(delete_result.text)['result']

    # IF reCaptcha
    if result == "captcha":
        print("\nERROR! - 리캡챠 인증이 발생하였습니다.")
        print("갤로그로 이동하여 로그인 후 삭제 버튼을 눌러 리캡챠를 해제한 후 다시 시도해주세요.")
        pyperclip.copy("https://gallog.dcinside.com/" + dcid + "/comment")
        print("브라우저 주소창에 Ctrl+V 하시면 바로 갤로그로 이동할 수 있습니다.")
        input("\n엔터키를 입력하면 종료됩니다.")
        exit(1)
    else:
        return f'GallName: {comment_gall} / CommentNum : {comment_no} / Result = {result}'


def get_comments_num(gall_url, flag):
    # Get Gallog
    gallog = sess.get("https://gallog.dcinside.com/" + gall_url)
    gallog_parsed = lxml.html.fromstring(gallog.text)

    # Get num
    if flag == 0:
        num = gallog_parsed.xpath('//*[@id="container"]/article/div/section/div[1]/header/div/div[1]/button[1]/span')[
            0].text.replace(",", "")
        num = re.findall("\d+", num)[0]
    else:
        num = gallog_parsed.xpath('//*[@id="container"]/article/div/section/div[1]/header/div/h2/span[3]')[
            0].text.replace(",", "")
        num = re.findall("\d+", num)[0]
    return num


def login(dcid, dcpw):
    # Login Headers
    LOGIN_REQ_HEADERS = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "dcid.dcinside.com",
        "Origin": "https://www.dcinside.com",
        "Referer": "https://www.dcinside.com/",
        "Upgrade-Insecure-Requests": "1"
    }
    LOGIN_POST_DATA = {
        's_url': "https://www.dcinside.com/",
        'ssl': "Y",
        'user_id': dcid,
        'pw': dcpw
    }

    # Get Hidden Robot Code
    hidden = requests.get("https://www.dcinside.com/")
    hidden_parsed = lxml.html.fromstring(hidden.text)
    hidden_name = hidden_parsed.xpath('//*[@id="login_process"]/input[3]')[0].get("name")
    hidden_value = hidden_parsed.xpath('//*[@id="login_process"]/input[3]')[0].get("value")
    LOGIN_POST_DATA[hidden_name] = hidden_value

    # Login
    try_login = sess.post("https://dcid.dcinside.com/join/member_check.php", data=LOGIN_POST_DATA,
                          headers=LOGIN_REQ_HEADERS)
    if "history.back(-1);" in try_login.text:
        print("\nLogin Failure! 로그인 정보를 다시 확인해주세요.")
        input("\n엔터키를 입력하면 종료됩니다.")
        exit(1)
    else:
        print("\nLogin Successfully with %s.\n" % dcid)


def select_gall_list(dcid):
    # Get Gallog
    gallog = sess.get("https://gallog.dcinside.com/" + dcid + "/comment")
    gallog_parsed = BeautifulSoup(gallog.text, "lxml")

    # Parse optionbox for Listing All Galleries
    option_box = gallog_parsed.find_all(class_="option_box")[1]
    option_box = option_box.find_all("li")

    gall_list = ["전체 삭제"]
    gall_list_no = [dcid + "/comment"]
    for gall in range(1, len(option_box)):
        gall_list += [option_box[gall].text]
        gall_list_no += [option_box[gall]['onclick'][15:-1]]

    # Select Gallery
    for i in range(len(gall_list)):
        print(str(i) + " - " + gall_list[i])

    select_no = int(input("댓글 삭제를 원하는 갤러리의 번호를 입력해주세요 : "))
    if select_no == 0:
        print("\n전체 삭제를 선택하셨습니다.")
    else:
        print("\n" + gall_list[select_no] + " 갤러리를 선택하셨습니다.")

    return gall_list_no[select_no]


if __name__ == '__main__':
    print("DCInside Comment Cleaner by qwertycvb\n")
    dcid = input("아이디를 입력하세요 : ")
    dcpw = input("패스워드를 입력하세요 : ")

    login(dcid, dcpw)

    selected_gall = select_gall_list(dcid)

    if selected_gall == dcid + "/comment":
        num = get_comments_num(selected_gall, 0)
    else:
        num = get_comments_num(selected_gall, 1)
    print("총 " + num + "개의 댓글에 대한 삭제를 시도합니다.\n")

    for i in range(int(num)):
        rst = delete_comment(dcid, selected_gall)
        print(rst + " - (" + str(i + 1) + "/" + num + ")")
        time.sleep(1)
    input("\n엔터키를 입력하면 종료됩니다.")
