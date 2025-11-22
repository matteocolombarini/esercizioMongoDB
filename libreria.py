import asyncio
import tornado.web
import json
from bson import ObjectId
from pymongo import AsyncMongoClient

client = AsyncMongoClient("localhost", 27017)
db = client["publisher_db"]
publishers_collection = db["publishers"]
books_collection = db["books"]

def convert_objectid_to_string(document):
    if isinstance(document, dict):
        for key, value in document.items():
            if isinstance(value, ObjectId):
                document[key] = str(value)
    return document

class PublisherHandler(tornado.web.RequestHandler):
    async def get(self):
        filters = {}
        name = self.get_argument("name", None)
        country = self.get_argument("country", None)

        if name:
            filters["name"] = name
        if country:
            filters["country"] = country

        publishers = await publishers_collection.find(filters).to_list(length=100)
        self.write(json.dumps([convert_objectid_to_string(publisher) for publisher in publishers], ensure_ascii=False))

    async def post(self):
        data = json.loads(self.request.body)
        publisher = {
            "name": data["name"],
            "founded_year": data["founded_year"],
            "country": data["country"]
        }
        result = await publishers_collection.insert_one(publisher)
        publisher["_id"] = str(result.inserted_id)
        self.write(json.dumps({"message": "Casa editrice aggiunta con successo", "publisher": publisher}))


class PublisherDetailHandler(tornado.web.RequestHandler):
    async def get(self, publisher_id):
        publisher = await publishers_collection.find_one({"_id": ObjectId(publisher_id)})
        if publisher is None:
            self.set_status(404)
            self.write(json.dumps({"error": "Publisher not found"}))
            return
        self.write(json.dumps(convert_objectid_to_string(publisher)))

    async def put(self, publisher_id):
        data = json.loads(self.request.body)
        result = await publishers_collection.update_one(
            {"_id": ObjectId(publisher_id)},
            {"$set": data}
        )
        if result.modified_count == 0:
            self.set_status(404)
            self.write(json.dumps({"error": "Publisher not found"}))
            return
        self.write(json.dumps({"message": "Casa editrice aggiornata con successo"}))

    async def delete(self, publisher_id):
        result = await publishers_collection.delete_one({"_id": ObjectId(publisher_id)})
        if result.deleted_count == 0:
            self.set_status(404)
            self.write(json.dumps({"error": "Publisher not found"}))
            return
        self.write(json.dumps({"message": "Casa editrice eliminata con successo"}))


class BookHandler(tornado.web.RequestHandler):
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

        books = await books_collection.find({"publisher_id": ObjectId(publisher_id), **filters}).to_list(length=100)
        self.write(json.dumps([convert_objectid_to_string(book) for book in books]))

    async def post(self, publisher_id):
        data = json.loads(self.request.body)
        book = {
            "publisher_id": ObjectId(publisher_id),
            "title": data["title"],
            "author": data["author"],
            "genre": data["genre"],
            "year": data["year"]
        }
        result = await books_collection.insert_one(book)
        book["_id"] = str(result.inserted_id)
        self.write(json.dumps({"message": "Libro aggiunto con successo", "book": convert_objectid_to_string(book)}))


class BookDetailHandler(tornado.web.RequestHandler):
    async def get(self, publisher_id, book_id):
        book = await books_collection.find_one({"_id": ObjectId(book_id), "publisher_id": ObjectId(publisher_id)})
        if book is None:
            self.set_status(404)
            self.write(json.dumps({"error": "Book not found"}))
            return
        self.write(json.dumps(convert_objectid_to_string(book)))

    async def put(self, publisher_id, book_id):
        data = json.loads(self.request.body)
        result = await books_collection.update_one(
            {"_id": ObjectId(book_id), "publisher_id": ObjectId(publisher_id)},
            {"$set": data}
        )
        if result.modified_count == 0:
            self.set_status(404)
            self.write(json.dumps({"error": "Book not found"}))
            return
        self.write(json.dumps({"message": "Libro aggiornato con successo"}))

    async def delete(self, publisher_id, book_id):
        result = await books_collection.delete_one({"_id": ObjectId(book_id), "publisher_id": ObjectId(publisher_id)})
        if result.deleted_count == 0:
            self.set_status(404)
            self.write(json.dumps({"error": "Book not found"}))
            return
        self.write(json.dumps({"message": "Libro eliminato con successo"}))


def make_app():
    return tornado.web.Application([
        (r"/publishers", PublisherHandler),
        (r"/publishers/([a-f0-9]{24})", PublisherDetailHandler),
        (r"/publishers/([a-f0-9]{24})/books", BookHandler),
        (r"/publishers/([a-f0-9]{24})/books/([a-f0-9]{24})", BookDetailHandler),
    ])


async def main():
    app = make_app()
    app.listen(8888)
    print("Server attivo su http://localhost:8888")
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
