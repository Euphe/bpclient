import vk
import os  
import re
import hashlib

vk_app_id = "5591268"

def parse_vk_uri(uri):
    token = re.compile(r'(token=)(\w+)')
    user_id = re.compile(r'(user_id=)(\w+)')
    #secret = re.compile(r'(secret=)(\w+)')
    return token.search(uri).group(2), user_id.search(uri).group(2)#, secret.search(uri).group(2),

def vk_login(app_id):
    auth_link = make_auth_link(app_id)
    print("Auth link:\n{0}".format(auth_link))
    response_uri = input("Enter the uri from browser:")
    return parse_vk_uri(response_uri)
#api = vk_login(vk_app_id, vk_secret_key, vk_user_login, vk_user_password)


def make_auth_link(app_id):
    base = "https://oauth.vk.com/authorize?client_id={0}&redirect_uri=https://oauth.vk.com/blank.html&scope=offline, messages&response_type=token"
    params = {
    "client_id":app_id,
    }

    return base.format(params["client_id"])
    #https://oauth.vk.com/authorize?client_id=1&display=page&redirect_uri=http://example.com/callback&scope=friends&response_type=token&v=5.53&state=123456



#print(make_auth_link(vk_app_id))
#my_link
#https://oauth.vk.com/blank.html#access_token=41cb7b47eccbc013031688d03949cb5a6d2b81aedfe51dfb3c573eff3853a5503b97605e8f811a5bd1a3e&expires_in=0&user_id=43447713
def create_sig(method, params, secret):

    params = params
    request = "/method/{0}?{1}".format(method, params)
    print(request+secret)
    return hashlib.md5(request+secret).hexdigest()

def initial_start():
    file_exists = os.path.isfile('./token.txt')
    if file_exists:
        with open('token.txt') as f:
            token, user_id = f.read().strip().split('\n')
    else:
        token, user_id = vk_login(vk_app_id)

    #login to vk
    #if login is succesful write token down to file
    session = vk.Session(token, no_https=False)
    api = vk.API(session)
    #print(api.users.get(user_ids=1, sig = create_sig("users/get", "user_ids=1&access_token="+token, secret)))
    assert(api.users.get(user_ids=1) != None)

    with open('token.txt', 'w+') as f:
    	f.write(token +'\n' +user_id)

    messages = api.messages.get()
    print(messages)

initial_start()