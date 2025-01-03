import pymysql

def conectar_db():
    return pymysql.connect(
        host="srv774.hstgr.io",  # Cambia por tu host de MySQL
        user="u403491029_bruno_user",         # Usuario de tu base de datos
        password="PrettyF33t!",  # Contraseña de tu base de datos
        database="u403491029_bruno_db", # Nombre de tu base de datos
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def guardar_mensaje(user_id, role, content):
    conn = conectar_db()
    logging.info(f"Guardando mensaje: {user_id}, {role}, {content}")
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO conversation_history (user_id, message_role, message_content) VALUES (%s, %s, %s)"
            cursor.execute(sql, (user_id, role, content))
        conn.commit()
    finally:
        conn.close()

def obtener_historial(user_id):
    logging.info(f"Obteneindo historial: {user_id}")
    conn = conectar_db()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT message_role, message_content FROM conversation_history WHERE user_id = %s ORDER BY timestamp"
            cursor.execute(sql, (user_id,))
            return cursor.fetchall()
    finally:
        conn.close()
