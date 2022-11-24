from flask import Flask, jsonify, Response, request
from flask_login import login_user, logout_user, login_required
from flask_login import LoginManager
from flask_login import UserMixin
from shutil import which
from os import environ, popen
from sys import exit
import requests
import subprocess
import requests_unixsocket
requests_unixsocket.monkeypatch()


login_manager = LoginManager()

def podman_version():
  return popen('podman -v').read().strip('\n').split(' ')[-1]

def run_podman_api():
  command_in_list = ["podman", "system", "service", "--log-level=debug", "--time=0"]
  with open('/tmp/podmanrest.log', 'a') as out, open('/tmp/podmanrest-error.log', 'a') as err:
    process = subprocess.Popen(command_in_list, stdout=out,stderr=err)
  return process

class User(UserMixin):
  def __init__(self, username):
    self.username = username

  def get_id(self):
    return self.username
  def is_active(self):
    return True

app = Flask(__name__)

app.config['SECRET_KEY'] = environ.get('SECRET_KEY', "yXS4Udk7ZrMRW9brjBAMCf5pQHGe9NgpQdd652WrcPrTfLkZWCHUKHab8VSW6DXG")
proxy_port = environ.get('PROXY_PORT', 8181)
login_manager.init_app(app)
if which('podman') is not None:
  print("podman binary exists")
  podman_v = podman_version()
  SITE_NAME = 'http+unix://%2frun%2fuser%2f1000%2fpodman%2fpodman.sock/'
else:
  print("Please install podman on this machine")
  exit(1)
if 'PODMAN_PROXY_USERNAME' in environ:
  proxy_username = environ.get('PODMAN_PROXY_USERNAME')
else:
  print("Please export PODMAN_PROXY_USERNAME environment variable, exiting")
  exit(1)

if 'PODMAN_PROXY_PASSWORD' in environ:
  proxy_password = environ.get('PODMAN_PROXY_PASSWORD')
else:
  print("Please export PODMAN_PROXY_PASSWORD environment variable, exiting")
  exit(1)

@login_manager.user_loader
def load_user(id):
  if proxy_username != "":
    return None
  user_obj = User(proxy_username)
  return user_obj

@app.route('/healthz')
def index():
  return 'proxy is running!'

@app.route('/authz/login', methods=["POST"])
def login():
  request_data = request.get_json()
  username = request_data['username']
  password = request_data['password']
  if username != proxy_username:
    return jsonify({'status': 'error wrong username'}), 401
  if password != proxy_password:
    return jsonify({'status': 'error wrong password'}), 401
  user = User(username)
  login_user(user)
  return jsonify({'status': 'login successful'})

@app.route('/authz/logout')
@login_required
def logout():
  logout_user()
  return jsonify({'status': 'logout successful'})

@app.route('/podmanproxy/<path:path>',methods=['GET'])
@login_required
def proxy(path):
  resp = requests.get(f'{SITE_NAME}{path}')
  excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
  headers = [(name, value) for (name, value) in     resp.raw.headers.items() if name.lower() not in excluded_headers]
  response = Response(resp.content, resp.status_code, headers)
  return response


@app.route('/podmanproxy/<path:path>' ,methods=['POST'])
@login_required
def postproxy(path):
  resp = requests.post(f'{SITE_NAME}{path}',json=request.get_json())
  excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
  headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
  response = Response(resp.content, resp.status_code, headers)
  return response

@app.route('/podmanproxy/<path:path>' ,methods=['DELETE'])
@login_required
def deleteproxy(path):
  resp = requests.delete(f'{SITE_NAME}{path}')
  excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
  headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
  response = Response(resp.content, resp.status_code, headers)
  return response

if __name__ == '__main__':
  try:
    podman_rest_process = run_podman_api()
    app.run(threaded=True, port=proxy_port)
  finally:
    podman_rest_process.kill()

