from boto.sqs.connection import SQSConnection
from boto.sqs.message import Message


def pop(queue='pi-status'):
    '''
    Pop the next Message off the queue, immediately delete it
    (mark it as consumed), and return the body string.
    '''
    sqs = SQSConnection()
    sqs_queue = sqs.create_queue(queue)

    message = sqs_queue.read()
    if message is not None:
        sqs_queue.read()
        body = message.get_body()
        message.delete()
        return body


def push(body, queue='pi-status'):
    '''
    Create a plain boto-style Message object and write it to the queue.
    '''
    sqs = SQSConnection()
    sqs_queue = sqs.create_queue(queue)

    message = Message(body=body)
    sqs_queue.write(message)
