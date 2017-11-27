from rq import Worker, Queue, Connection
from komidabot import redisCon

listen = ['high', 'default', 'low']


if __name__ == '__main__':
    with Connection(redisCon):
        worker = Worker(map(Queue, listen))
        worker.work()
