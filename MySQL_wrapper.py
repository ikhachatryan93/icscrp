import pymysql


class MySQL:

    def __init__(self,host=None, port=None, user=None, password=None, db=None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db = db

    def connect(self):
        try:
            self.conn = pymysql.connect(host=self.host,port=self.port,user=self.user,password=self.password,db=self.db)
            self.cursor = self.conn.cursor()

        except Exception as err:
            print ('Error occured during SQL connection. Reason: {}'.format(err))

    def insert(self, data):
        # data should be a list of dictionaries [{table_name:{col1:value1,col2:value2}},{...}]
        for dict in data:
            table = list(dict.keys())[0]
            columns=",".join(dict[table].keys())
            values=",".join(str(i) for i in dict[table].values())
            query = "insert into {0} ({1}) values ({2})".format(table, columns, values)

            try:
                self.cursor.execute(query)
                self.conn.commit()

            except Exception as err:
                print ('Error occured during insertion. Reason {}'.format(err))

    def read_row(self, query):

        self.cursor.execute(query)
        out = self.cursor.fetchone()

        return out

    def read_all_rows(self, query):

        self.cursor.execute(query)
        out = self.cursor.fetchall()

        return out

    def disconnect(self):

        self.cursor.close()
        self.conn.close()


db=MySQL(host="localhost",port=3306,user="root",password="3789",db="ico")
db.connect()
db.insert({"aaa":{"a":1,"b":2}})
db.disconnect()




