# Podman Proxy

Flask based application to run reverse proxy with basic http auth on podman socket. The requirement of the project is to run as proxy on top podman socket to provide rest api service to machines outside the host.

## Attempt
The python application makes sure that podman binary is present in the current environment, Once it confirms the binary is present then it checks for podman proxy username and password exported in the environment. Even if either of the values are not present then the application exits with an error.
Once everything is verified it starts the podman socket based rest service using the following command `podman system service --log-level=debug --time=0`. This starts the socket service and once the application is exited the socket service is also closed.
Application then forwards all request on `/podmanproxy` to podman rest socket.
# Pre-requisites
Checks before triggering the application
## Operating System Checks
For the application to run properly it requires podman be installed on the host.
check using podman using 
```
ubuntu@podman-proxy:~/podman-proxy$ which podman
/usr/bin/podman
```
check if the port 8181 is allowed in firewall
```
ubuntu@podman-proxy:~/podman-proxy$ sudo ufw status numbered
Status: active

     To                         Action      From
     --                         ------      ----
[ 1] 8181                       ALLOW IN    Anywhere                  
[ 2] 22/tcp                     ALLOW IN    Anywhere                  
[ 3] 8181 (v6)                  ALLOW IN    Anywhere (v6)             
[ 4] 22/tcp (v6)                ALLOW IN    Anywhere (v6)    
```

**8181** is the default port.
## Python Environment Setup
It is better to setup the application in a virtual environment, because this application uses requests_unixsocket and the usage monkey_patching, these package will affect the host's python requests libraries.

### Setting up the environment
```
ubuntu@podman-proxy:~/podman-proxy$ python3 -m venv venv
ubuntu@podman-proxy:~/podman-proxy$ source venv/bin/activate
(venv) ubuntu@podman-proxy:~/podman-proxy$ pip3 install -r requirements.txt 
.
.
.
Installing collected packages: urllib3, MarkupSafe, itsdangerous, idna, click, charset-normalizer, certifi, Werkzeug, requests, Jinja2, requests-unixsocket, Flask, Flask-HTTPAuth
Successfully installed Flask-2.2.2 Flask-HTTPAuth-4.7.0 Jinja2-3.1.2 MarkupSafe-2.1.1 Werkzeug-2.2.2 certifi-2022.9.24 charset-normalizer-2.1.1 click-8.1.3 idna-3.4 itsdangerous-2.1.2 requests-2.28.1 requests-unixsocket-0.3.0 urllib3-1.26.13
```
### Requirements File

|     Package        |UseCase                             | PyPi Page                        |
|--------------------|-----------------------------------|------------
|Flask               |`Package for running rest api`     | [flask](https://pypi.org/project/Flask/)        
|requests            |`Package for making http requests` | [requests](https://pypi.org/project/requests/)    
|requests-unixsocket | `Use requests to talk HTTP via a UNIX domain socket` | [requests-unixsocket](https://pypi.org/project/requests-unixsocket/)
|Flask-HTTPAuth      | `Simple extension that provides Basic and Digest HTTP authentication for Flask routes.` | [Flask-HTTPAuth](https://pypi.org/project/Flask-HTTPAuth/)

# Runtime

This section deals with runtime details.


## Environment Variables

Following are the environment variables 
| Variable      | UseCase   | Default (Please Change According to your needs) | Required
|---------------|-----------|---------------|---
|SECRET_KEY     |The secret key is needed to keep the client-side sessions secure | `some random string` | Optional
|PROXY_PORT     | The Port on which the application will listen | `8181`| Optional
|PODMAN_PROXY_USERNAME| The username with which the reverse proxy is authenticated| `null`| Required
|PODMAN_PROXY_PASSWORD|The password with which reverse proxy is authenticated| `null`| Required

##  Executing the application
one can start the proxy using the following command, after the environment has been set up.
```
(venv) ubuntu@podman-proxy:~/podman-proxy$ PODMAN_PROXY_USERNAME="admin" PODMAN_PROXY_PASSWORD="test" python3 main.py
podman binary exists
 * Serving Flask app 'main'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8181
 * Running on http://10.44.247.148:8181
Press CTRL+C to quit

```
## Building the binary
One can use pyinstaller to create onefile binary that can be executed on any environment without actually setting up the whole environment.
you can trigger this inside the `GITROOT` directory
```
pip install pyinstaller
pyinstaller --onefile main.py
```
or trigger make command to execute the build
```
ubuntu@podman-proxy:~/podman-proxy$ make build
```
## Reverse Proxy endpoints
| Endpoints | Methods | Authentication | Purpose
|-----------|---------|----------------|--
|`/healthz` | ["GET"] | Not Required   | To check the health of the proxy
|`/podmanproxy/<podman_rest_path>`|["GET", "POST", "PUT", "DEL"]| Required| Serve as proxy endpoint
> **Note:** The **podman_rest_path** can be referred from the [podman rest api documentation](https://docs.podman.io/en/latest/_static/api.html)

### Example curl calls
*Call to check if proxy is working*
```
[harshvardhan@homeserver podman-proxy]$ curl http://10.44.247.148:8181/healthz
proxy is running!
```
*Call without authentication*
```
[harshvardhan@homeserver podman-proxy]$ curl http://10.44.247.148:8181/podmanproxy/system/df
Unauthorized Access
```
Call with authentication
```
[harshvardhan@homeserver podman-proxy]$ curl -u "admin:test" http://10.44.247.148:8181/podmanproxy/system/df
{"LayersSize":0,"Images":[],"Containers":[],"Volumes":[],"BuildCache":[],"BuilderSize":0}
```