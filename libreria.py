import asyncio
import tornado.web
from pymongo import AsyncMongoClient

client = AsyncMongoClient("localhost", 27017)
db = client["libreria_db"]
publishers_collection = db["publishers"]
books_collection = db["books"]

class PublisherHandler(tornado.web.RequestHandler):

    async def get(self):
        pass

    async def post(self):
        pass


class PublisherDetailHandler(tornado.web.RequestHandler):

    async def get(self):
        pass



    async def put(self):
        pass


    async def delete(self):
        pass


class BookHandler(tornado.web.RequestHandler):
    async def get(self):
        pass


    async def post(self):
        pass


class BookDetailHandler(tornado.web.RequestHandler):
    async def get(self):
        pass


    async def put(self):
        pass


    async def delete(self):
        pass



def make_app():
    return tornado.web.Application([
        (r"/publishers", PublisherHandler),
        (r"/publishers/([a-f0-9]{24})", PublisherDetailHandler),
        (r"/publishers/([a-f0-9]{24})/books", BookHandler),
        (r"/publishers/([a-f0-9]{24})/books/([a-f0-9]{24})", BookDetailHandler),
    ])


async def main(shutdown_event):
    app = make_app()
    app.listen(8888)
    print("Server attivo su http://localhost:8888/products")
    await shutdown_event.wait()


if __name__ == "__main__":
    shutdown_event = asyncio.Event()
    try:
        asyncio.run(main(shutdown_event))
    except KeyboardInterrupt:
        shutdown_event.set()























import tornado.ioloop
import tornado.web
from tornado import gen
import json
from pymongo import MongoClient
from bson import ObjectId

# Connessione a MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client["publisher_db"]
publishers_collection = db["publishers"]
books_collection = db["books"]

# Funzione per serializzare l'ObjectId in stringa
def serialize_objectid(document):
    if isinstance(document, dict):
        for key, value in document.items():
            if isinstance(value, ObjectId):
                document[key] = str(value)
    return document

class PublisherHandler(tornado.web.RequestHandler):
    # GET tutte le case editrici o filtrate
    async def get(self):
        filters = {}
        name = self.get_argument("name", None)
        country = self.get_argument("country", None)

        if name:
            filters["name"] = name
        if country:
            filters["country"] = country

        publishers = publishers_collection.find(filters)
        publishers = [serialize_objectid(publisher) for publisher in publishers]
        self.write(json.dumps(publishers, ensure_ascii=False))

    # POST nuova casa editrice
    async def post(self):
        data = json.loads(self.request.body)
        publisher = {
            "name": data["name"],
            "founded_year": data["founded_year"],
            "country": data["country"]
        }
        result = publishers_collection.insert_one(publisher)
        publisher["_id"] = str(result.inserted_id)
        self.write(json.dumps({"message": "Casa editrice aggiunta con successo", "publisher": publisher}, ensure_ascii=False))

class PublisherDetailHandler(tornado.web.RequestHandler):
    # GET casa editrice specifica
    async def get(self, publisher_id):
        publisher = publishers_collection.find_one({"_id": ObjectId(publisher_id)})
        if not publisher:
            self.set_status(404)
            self.write(json.dumps({"error": "Publisher not found"}))
            return
        publisher = serialize_objectid(publisher)
        self.write(json.dumps(publisher, ensure_ascii=False))

    # PUT aggiorna casa editrice
    async def put(self, publisher_id):
        data = json.loads(self.request.body)
        result = publishers_collection.update_one(
            {"_id": ObjectId(publisher_id)},
            {"$set": data}
        )
        if result.modified_count == 0:
            self.set_status(404)
            self.write(json.dumps({"error": "Publisher not found"}))
            return
        self.write(json.dumps({"message": "Casa editrice aggiornata con successo"}))

    # DELETE elimina casa editrice
    async def delete(self, publisher_id):
        result = publishers_collection.delete_one({"_id": ObjectId(publisher_id)})
        if result.deleted_count == 0:
            self.set_status(404)
            self.write(json.dumps({"error": "Publisher not found"}))
            return
        self.write(json.dumps({"message": "Casa editrice eliminata con successo"}))

class BookHandler(tornado.web.RequestHandler):
    # GET tutti i libri della casa editrice
    async def get(self, publisher_id):
        filters = {}
        title = self.get_argument("title", None)
        author = self.get_argument("author", None)
        genre = self.get_argument("genre", None)

        if title:
            filters["title"] = title
        if author:
            filters["author"] = author
        if genre:
            filters["genre"] = genre

        books = books_collection.find({"publisher_id": ObjectId(publisher_id), **filters})
        books = [serialize_objectid(book) for book in books]
        self.write(json.dumps(books, ensure_ascii=False))

    # POST nuovo libro
    async def post(self, publisher_id):
        data = json.loads(self.request.body)
        book = {
            "publisher_id": ObjectId(publisher_id),
            "title": data["title"],
            "author": data["author"],
            "genre": data["genre"],
            "year": data["year"]
        }
        result = books_collection.insert_one(book)
        book["_id"] = str(result.inserted_id)
        book["publisher_id"] = str(book["publisher_id"])
        self.write(json.dumps({"message": "Libro aggiunto con successo", "book": book}, ensure_ascii=False))

class BookDetailHandler(tornado.web.RequestHandler):
    # GET libro specifico
    async def get(self, publisher_id, book_id):
        book = books_collection.find_one({"_id": ObjectId(book_id), "publisher_id": ObjectId(publisher_id)})
        if not book:
            self.set_status(404)
            self.write(json.dumps({"error": "Book not found"}))
            return
        book = serialize_objectid(book)
        self.write(json.dumps(book, ensure_ascii=False))

    # PUT aggiorna libro
    async def put(self, publisher_id, book_id):
        data = json.loads(self.request.body)
        result = books_collection.update_one(
            {"_id": ObjectId(book_id), "publisher_id": ObjectId(publisher_id)},
            {"$set": data}
        )
        if result.modified_count == 0:
            self.set_status(404)
            self.write(json.dumps({"error": "Book not found"}))
            return
        self.write(json.dumps({"message": "Libro aggiornato con successo"}))

    # DELETE elimina libro
    async def delete(self, publisher_id, book_id):
        result = books_collection.delete_one({"_id": ObjectId(book_id), "publisher_id": ObjectId(publisher_id)})
        if result.deleted_count == 0:
            self.set_status(404)
            self.write(json.dumps({"error": "Book not found"}))
            return
        self.write(json.dumps({"message": "Libro eliminato con successo"}))