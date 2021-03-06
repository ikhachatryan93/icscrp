import MySQLdb as mysql
import traceback


class MySQL:

    def __init__(self, host=None, port=None, user=None, password=None, db=None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db = db
        self.conn = None
        self.cursor = None
        self.conn_num = 0

    def connect(self):
        try:
            self.conn = mysql.connect(host=self.host, port=self.port, user=self.user, password=self.password,
                                      db=self.db, charset='utf8', autocommit=False)
            self.cursor = self.conn.cursor()
            self.execute('SET autocommit=0')
        except:
            raise Exception('Error occurred during SQL connection. Reason: {}'.format(traceback.format_exc()))

    def insert(self, query):
        try:
            self.cursor.execute(query)
            self.conn_num += 1
            if self.conn_num % 300 == 0:
                self.conn.commit()
        except:
            raise Exception('Error occurred during insertion. Reason: {}'.format(traceback.format_exc()))

    def execute(self, query):
        try:
            self.cursor.execute(query)
        except:
            raise Exception('Error occurred during query execution. Reason: {}'.format(traceback.format_exc()))

    def read_row(self, query):
        try:
            self.cursor.execute(query)
            out = self.cursor.fetchone()

            return out

        except:
            raise Exception('Error occurred during read single row. Reason: {}'.format(traceback.format_exc()))

    def read_all_rows(self, query):
        try:
            self.cursor.execute(query)
            out = self.cursor.fetchall()

            return out

        except:
            raise Exception('Error occurred during reading rows. Reason: {}'.format(traceback.format_exc()))

    def disconnect(self):

        self.cursor.close()
        self.conn.close()

# db = MySQL(host="localhost", port=3306, user="root", password="3789", db="ico")
# db.connect()
# db.insert({"aaa": {"a": 1, "b": 2}})
# db.disconnect()
