from janito.work import Workdir

with Workdir() as workdir:
    workdir.run("create an hello.py with a python hello world")