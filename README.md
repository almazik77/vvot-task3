# Инструкция :
1. Выдать аккаунту роль serverless.functions.invoker и editor, создать API-ключ и статический ключ доступа.
2. Скопировать все файлы в облачную функцию, создать очередь сообщений, Message Queue, Telegram бота
3. Добавить в переменные окружения параметры:
     - aws_access_key_id - id статического ключа доступа;
     - aws_secret_access_key - секретный ключ доступа;
     - db_file_name - имя файла базы данных
     - bot_token - токен бота;
     - chat_id - id чата 
     - bucket_id - id бакета