# main script here
# data with here
# run pip/pip3 install bs4
import requests as rq
from bs4 import BeautifulSoup
import time

# serve var is for the link to the Moodle's service,
serve = 'link_to_moodle_site'

if serve[-1] != '/':
    serve += '/'
    
#   I. Login and logout
def login(login, passwd):
    s = rq.session()
    login = {"username": login, "password": passwd}
    s.post(serve + "login/index.php", data=login)
    return(s)

def logout(s):
    link = serve + "report/usersessions/user.php"
    # the data
    data = BeautifulSoup(s.get(link, cookies=s.cookies).text, "html5lib")
    
    for i in data.find_all('a'):
        if i.text == "Log out" and i.attrs['href'].startswith(serve + 'login/logout.php'):
            s.post(i.attrs['href'], cookies=s.cookies)

# -newline-
#  II. Control session
def drop(s):
    link = serve + "report/usersessions/user.php"
    # the data
    data = BeautifulSoup(s.get(link, cookies=s.cookies).text, "html5lib")
    sk = ""
    
    for i in data.find_all('a'):
        if i.text == "Log out" and not i.attrs['href'].startswith(serve + 'login/logout.php'):
            s.get(i.attrs['href'], cookies=s.cookies)

def get_sesskey(s):
    link = serve + "report/usersessions/user.php"
    # the data
    data = BeautifulSoup(s.get(link, cookies=s.cookies).text, "html5lib")
    
    for i in data.find_all('a'):
        if i.text == "Log out" and i.attrs['href'].startswith(serve + 'login/logout.php'):
            return i.attrs['href'].split("sesskey=")[1]
    return ""

def get_id(s):
    link = serve + 'my/'
    
    data = BeautifulSoup(s.get(link, cookies=s.cookies).text, "html5lib")
    
    for i in data.find_all('a'):
        if 'href' in i.attrs and i.attrs['href'].startswith(serve + 'user/profile.php?'):
            return i.attrs['href'].split("profile.php?id=")[1]

def session_data(s):
    return(get_sesskey(s), get_id(s))

# -newline-
# III. Main functions
# got user IDs by their names
def user_list(s, **kwargs):
    def levenshtein(s1, s2):
        if len(s1) < len(s2):
            return levenshtein(s2, s1)

        # len(s1) >= len(s2)
        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]
    
    if 'names' not in kwargs:
        print("please add Names dictionary")
        raise KeyboardInterrupt
    
    link = serve + 'user/profile.php?id='
    users = {}
    names = kwargs['names']
    count = 0
    max_id = 10000
    try:
        for i in range(1, max_id):
            if i % 500 == 0:
                print('now on', i)
            d = BeautifulSoup(s.get(link + str(i), cookies=s.cookies).text, "html5lib").find_all('title')[0].text
            z = d.split(':')[0].strip()
            if d and d != 'IU Moodle: User' and z in names:
                count += 1
                users[z] = i
                print('[' + str(count) + ']', 'got', z, i)
            elif d and d != 'IU Moodle: User':
                # use only if there are levenstein error not more than 5.
                for q in names:
                    if levenshtein(q, z) <= 4:
                        users[z] = i
                        print('[LEV][' + str(count) + ']', 'got', z, i)
        print('[SUCC] got', count,'IDs')
        return users
    except KeyboardInterrupt:
        print('[SUCC] got', count,'IDs')
        return users

def send_single(s, msg, dest_id, **kwargs):
    if 'sesskey' in kwargs and 'my_id' in kwargs:
        sesskey = kwargs['sesskey']
        my_id = kwargs['my_id']
    else:
        sesskey = get_sesskey(s)
        my_id = get_id(s)
        
    query = {'_qf__send_form': '1', 'user1': str(my_id), 'user2': str(dest_id), 'message': msg, 'sesskey': sesskey, 
             'submitbutton': 'Send+message', 'viewing': 'unread', '_form_action': 'Send'}

    # link to the conversation permamently
    link = serve + "message/index.php?user1=" + str(my_id) + "&user2=" + str(dest_id)
    # the data
    rq.post(link, cookies=s.cookies, data=query)
    
def message_client(s, dests, msg, **kwargs):
    if 'sesskey' in kwargs and 'my_id' in kwargs:
        sesskey = kwargs['sesskey']
        my_id = kwargs['my_id']
    else:
        sesskey = get_sesskey(s)
        my_id = get_id(s)
    
    def full(n, m):
        return '\nDear ' + n + ',\n\n' + m
    
    h = 0
    for name in dests:
        h += 1
        T = time.time()
        send_single(s, full(name, msg), dests[name], sesskey=sesskey, my_id=my_id)
        print('visited', name, 'in', time.time() - T, 'seconds')
        
        T = time.time()
        clear_all(s, dests[name], sesskey=sesskey, my_id=my_id)
        print('cleared', name, 'in', time.time() - T, 'seconds')
        
        T = time.time()
        block(s, dests[name], sesskey=sesskey, my_id=my_id)
        print('blocked', name, 'in', time.time() - T, 'seconds')
        
        if not h % 25:
            drop(s)
    
    print('[SUCC] messages delivered')

# -newline-
#  IV. EXTERNAL
#      clear_all messages with dest_id
def clear_all(s, dest_id, **kwargs):
    if 'sesskey' in kwargs and 'my_id' in kwargs:
        sesskey = kwargs['sesskey']
        my_id = kwargs['my_id']
    else:
        sesskey = get_sesskey(s)
        my_id = get_id(s)
    
    link = serve + 'message/index.php?user1=' + str(my_id) + '&user2=' + str(dest_id) + '&history=1'
    g = BeautifulSoup(s.get(link, cookies=s.cookies).text, "html5lib")
    data = {'user1': str(my_id), 'user2': str(dest_id), 'viewing': 'contacts',
           'sesskey': str(sesskey), 'deletemessageconfirm': '1', 'deletemessagetype': 'message_read'}
    
    for i in g.find_all('a'):
        if 'name' in i.attrs and i.attrs['name'].startswith('m'):
            data['deletemessageid'] = i.attrs['name'].split('m')[1]
            s.post(link, cookies=s.cookies, data = data)
            time.sleep(0.001)

#      block the dest_id
def block(s, dest_id, **kwargs):
    if 'sesskey' in kwargs and 'my_id' in kwargs:
        sesskey = kwargs['sesskey']
        my_id = kwargs['my_id']
    else:
        sesskey = get_sesskey(s)
        my_id = get_id(s)
    
    link = serve + 'message/index.php?user1=' + str(my_id) + '&user2=' + str(dest_id) + '&viewing=blockedusers&blockcontact=' + str(dest_id) + '&sesskey=' + sesskey
    rq.get(link, cookies=s.cookies)

# -newline-
# EXEC your code here

"""
Simple usage:

session = login("your_login", 'your_password')
u, v = session_data(session)
send_single(session, "My first message!", destination_id, sesskey=u, my_id=v)
logout(session)

Enjoy!
"""

# -newline-
# -eof-
