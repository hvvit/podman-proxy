from flask import Flask, jsonify, Response, request
from shutil import which
from os import environ, popen
from sys import exit
import requests
import subprocess
import requests_unixsocket
requests_unixsocket.monkeypatch()

def podman_version():
  return popen('podman -v').read().strip('\n').split(' ')[-1]

def run_podman_api():
  command_in_list = ["podman", "system", "service", "--log-level=debug", "--time=0"]
  with open('/tmp/podmanrest.log', 'a') as out, open('/tmp/podmanrest-error.log', 'a') as err:
    process = subprocess.Popen(command_in_list, stdout=out,stderr=err)
  return process


app = Flask(__name__)

app.config['SECRET_KEY'] = environ.get('SECRET_KEY', "yXS4Udk7ZrMRW9brjBAMCf5pQHGe9NgpQdd652WrcPrTfLkZWCHUKHab8VSW6DXG")
proxy_port = environ.get('PROXY_PORT', 8181)

from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()

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

@app.route('/healthz')
def index():
  return 'proxy is running!'

@auth.verify_password
def verify_password(username, password):
  if username == proxy_username and password == proxy_password:
    return username

@app.route('/podmanproxy/<path:path>',methods=['GET'])
@auth.login_required
def proxy(path):
  resp = requests.get(f'{SITE_NAME}{path}')
  excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
  headers = [(name, value) for (name, value) in     resp.raw.headers.items() if name.lower() not in excluded_headers]
  response = Response(resp.content, resp.status_code, headers)
  return response

@app.route('/podmanproxy/<path:path>',methods=['PUT'])
@auth.login_required
def putproxy(path):
  resp = requests.put(f'{SITE_NAME}{path}',json=request.get_json())
  excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
  headers = [(name, value) for (name, value) in     resp.raw.headers.items() if name.lower() not in excluded_headers]
  response = Response(resp.content, resp.status_code, headers)
  return response

@app.route('/podmanproxy/<path:path>' ,methods=['POST'])
@auth.login_required
def postproxy(path):
  resp = requests.post(f'{SITE_NAME}{path}',json=request.get_json())
  excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
  headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
  response = Response(resp.content, resp.status_code, headers)
  return response

@app.route('/podmanproxy/<path:path>' ,methods=['DELETE'])
@auth.login_required
def deleteproxy(path):
  resp = requests.delete(f'{SITE_NAME}{path}')
  excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
  headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
  response = Response(resp.content, resp.status_code, headers)
  return response

if __name__ == '__main__':
  try:
    podman_rest_process = run_podman_api()
    app.run(threaded=True, host="0.0.0.0" ,port=proxy_port)
  finally:
    podman_rest_process.kill()

