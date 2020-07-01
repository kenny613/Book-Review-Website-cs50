import os
import csv


from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


def writebook(db):

    f = open("books.csv")
    reader = csv.reader(f,delimiter=',')
    next(reader)

    for isbn,title,author,year in reader: # loop gives each column a name
        db.execute("INSERT INTO books (isbn,title,author,year) VALUES (:isbn,:title,:author,:year)",
                    {"isbn":isbn,"title":title,"author":author,"year":year}) # substitute values from CSV line into SQL command, as per this dict
        print(f"read {title}")
    db.commit()
     # transactions are assumed, so close the transaction finished

