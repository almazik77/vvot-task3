import os
import json
import requests
import boto3

TELEGRAM_API_URL = 'https://api.telegram.org/bot'


def handler(event, context):
    DATABASE = os.environ.get('db_file_name')
    AWS_ACESS_KEY_ID = os.environ.get('aws_access_key_id')
    AWS_SECRET_ACESS_KEY = os.environ.get('aws_secret_access_key')
    API_KEY = os.environ.get('api_key')
    MESSAGE_QUEUE_URL = os.environ.get('message_queue_url')
    BOT_KEY = os.environ.get('bot_token')
    TELEGRAM_CHAT_ID = os.environ.get('chat_id')
    BUCKET_ID = os.environ.get('bucket_id')
    QUEUE_MESSAGE_EVENT_TYPE = "yandex.cloud.events.messagequeue.QueueMessage"

    session = boto3.session.Session()
    s3 = session.client(
        service_name='s3',
        endpoint_url='https://storage.yandexcloud.net',
        aws_access_key_id=AWS_ACESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACESS_KEY
    )

    message_queue = True
    try:
        event['messages'][0]['event_metadata']['event_type']

    except KeyError:
        message_queue = False

    if message_queue:
        message_body_json = event['messages'][0]['details']['message']['body']
        message_body = json.loads(message_body_json)

        faces_array = message_body['faces']
        parent_object = message_body['parentObject']

        for face in faces_array:
            face_image_response = s3.get_object(Bucket=BUCKET_ID, Key=face)
            face_image_content = face_image_response['Body'].read()
            params = {'chat_id': TELEGRAM_CHAT_ID, 'caption': parent_object}
            files = {'photo': face_image_content}
            postRequest(BOT_KEY, '/sendMessage', json_variable={'chat_id': TELEGRAM_CHAT_ID, 'text': 'Кто на фото?'})
            requests.post(TELEGRAM_API_URL + '{0}/sendPhoto'.format(BOT_KEY), data=params, files=files)

    else:
        try:
            body = event['body']
            body_json = json.loads(body)
            message = body_json['message']
            message_id = message['message_id']
        except KeyError:
            message = body_json['edited_message']
            message_id = message['message_id']

        validate_flag = False
        validate_id = ""
        validate_name = ""
        try:
            message_photo = message['reply_to_message']['photo']
            validate_id = message['reply_to_message']['caption']
            if message['reply_to_message']['from']['is_bot'] == True:
                validate_flag = True
                validate_name = message['text']

        except KeyError:
            validate_flag = False

        if validate_flag:
            db_file = {}
            try:
                get_db_file_response = s3.get_object(Bucket=BUCKET_ID, Key=DATABASE)
                db_file = json.loads(get_db_file_response['Body'].read())
            except Exception as e:
                db_file = {}

            current_images_for_name = []
            try:
                current_images_for_name = db_file[validate_name]
            except KeyError:
                current_images_for_name = []

            IS_NEED_TO_APPEND_FILE = True
            for image in current_images_for_name:
                if image == validate_id:
                    IS_NEED_TO_APPEND_FILE = False
            if IS_NEED_TO_APPEND_FILE:
                current_images_for_name.append(validate_id)
                db_file[validate_name] = current_images_for_name
                s3.put_object(Body=json.dumps(db_file), Bucket=BUCKET_ID, Key=DATABASE)

        else:
            try:
                message_text = message['text']
            except Exception as e:
                postRequest(BOT_KEY, '/sendMessage',
                            json_variable={'chat_id': TELEGRAM_CHAT_ID, 'text': 'Не понимаю вас!',
                                           'reply_to_message_id': message_id})
                return {
                    'statusCode': 200,
                    'body': 'Didnt understand command!',
                }
            command_parts = message_text.split(' ')
            find_flag = False
            for part in command_parts:
                if part == '/find':
                    find_flag = True
            if len(command_parts) == 2 and find_flag:
                name_to_find = command_parts[1]
                try:
                    get_db_file_response = s3.get_object(Bucket=BUCKET_ID, Key=DATABASE)
                    db_file = json.loads(get_db_file_response['Body'].read())
                except Exception as e:
                    postRequest(BOT_KEY, '/sendMessage', json_variable={'chat_id': TELEGRAM_CHAT_ID,
                                                                        'text': 'Фотографий нет',
                                                                        'reply_to_message_id': message_id})
                    return {
                        'statusCode': 200,
                        'body': 'No photo!',
                    }
                try:
                    images = db_file[name_to_find]
                except KeyError:
                    postRequest(BOT_KEY, '/sendMessage', json_variable={'chat_id': TELEGRAM_CHAT_ID,
                                                                        'text': 'Фотографий нет',
                                                                        'reply_to_message_id': message_id})
                    return {
                        'statusCode': 200,
                        'body': 'No photo!',
                    }
                postRequest(BOT_KEY, '/sendMessage', json_variable={'chat_id': TELEGRAM_CHAT_ID,
                                                                    'text': f'Фотографии с именем {name_to_find}:'})
                for image in images:
                    image_response = s3.get_object(Bucket=BUCKET_ID, Key=image)
                    image_response_content = image_response['Body'].read()
                    params = {'chat_id': TELEGRAM_CHAT_ID}
                    files = {'photo': image_response_content}
                    requests.post(TELEGRAM_API_URL + '{0}/sendPhoto'.format(BOT_KEY), data=params, files=files)
            else:
                postRequest(BOT_KEY, '/sendMessage', json_variable={'chat_id': TELEGRAM_CHAT_ID,
                                                                    'text': 'Используйте команду "/find name" для поиска.',
                                                                    'reply_to_message_id': message_id})
                return {
                    'statusCode': 200,
                    'body': 'Wrong command!',
                }

    return {
        'statusCode': 200,
        'body': 'Ok',
    }


def postRequest(token, method, json_variable):
    return requests.post(TELEGRAM_API_URL + token + method, json=json_variable)