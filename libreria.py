import asyncio
import tornado.web
import json
from bson import ObjectId
from pymongo import AsyncMongoClient

client = AsyncMongoClient("localhost", 27017)
db = client["publisher_db"]
publishers_collection = db["publishers"]
books_collection = db["books"]


def convert_id(document):
    if "_id" in document:
        document["_id"] = str(document["_id"])
    if "publisher_id" in document:
        document["publisher_id"] = str(document["publisher_id"])
    return document


class PublisherHandler(tornado.web.RequestHandler):

    async def get(self, publisher_id=None):
        self.set_header("Content-Type", "application/json")

        if publisher_id:
            try:
                obj_id = ObjectId(publisher_id)
            except:
                self.set_status(400)
                self.write({"error": "ID Publisher non valido"})
                return

            publisher = await publishers_collection.find_one({"_id": obj_id})
            if not publisher:
                self.set_status(404)
                self.write({"error": "Casa editrice non trovata"})
                return

            self.set_status(200)
            self.write(convert_id(publisher))
            return

 
        filters = {}
        name = self.get_argument("name", None)
        country = self.get_argument("country", None)

        if name:
            filters["name"] = {"$regex": name, "$options": "i"}
        if country:
            filters["country"] = {"$regex": country, "$options": "i"}

        cursor = publishers_collection.find(filters)
        results = []
        async for pub in cursor:
            results.append(convert_id(pub))

        self.set_status(200)
        self.write(tornado.escape.json_encode(results))

    async def post(self):
        self.set_header("Content-Type", "application/json")

        try:
            data = tornado.escape.json_decode(self.request.body)
        except:
            self.set_status(400)
            self.write({"error": "JSON non valido"})
            return

        new_publisher = {
            "name": data["name"],
            "founded_year": data["founded_year"],
            "country": data["country"]
        }

        result = await publishers_collection.insert_one(new_publisher)
        new_publisher["_id"] = str(result.inserted_id)

        self.set_status(201)
        self.write(tornado.escape.json_encode(new_publisher))

    async def put(self, publisher_id):
        self.set_header("Content-Type", "application/json")

        if not publisher_id:
            self.set_status(400)
            self.write({"error": "ID mancante"})
            return

        try:
            obj_id = ObjectId(publisher_id)
            data = tornado.escape.json_decode(self.request.body)
        except:
            self.set_status(400)
            self.write({"error": "ID o JSON non valido"})
            return

        update_data = {
            "name": data["name"],
            "founded_year": data["founded_year"],
            "country": data["country"]
        }

        await publishers_collection.update_one({"_id": obj_id}, {"$set": update_data})
        
        self.set_status(200)
        self.write({"message": "Casa editrice aggiornata"})

    async def delete(self, publisher_id):
        self.set_header("Content-Type", "application/json")
        
        try:
            obj_id = ObjectId(publisher_id)
        except:
            self.set_status(400)
            self.write({"error": "ID non valido"})
            return

        await publishers_collection.delete_one({"_id": obj_id})
 
        self.set_status(200)
        self.write({"message": "Casa editrice eliminata"})


class BookHandler(tornado.web.RequestHandler):

    async def get(self, publisher_id, book_id=None):
        self.set_header("Content-Type", "application/json")

        try:
            pub_obj_id = ObjectId(publisher_id)
        except:
            self.set_status(400)
            self.write({"error": "ID Publisher non valido"})
            return

        if book_id:
            try:
                book_obj_id = ObjectId(book_id)
            except:
                self.set_status(400)
                self.write({"error": "ID Libro non valido"})
                return

            book = await books_collection.find_one({
                "_id": book_obj_id, 
                "publisher_id": pub_obj_id
            })
            
            if not book:
                self.set_status(404)
                self.write({"error": "Libro non trovato"})
                return

            self.set_status(200)
            self.write(convert_id(book))
            return

        filters = {"publisher_id": pub_obj_id}
        
        title = self.get_argument("title", None)
        author = self.get_argument("author", None)
        genre = self.get_argument("genre", None)

        if title:
            filters["title"] = {"$regex": title, "$options": "i"}
        if author:
            filters["author"] = {"$regex": author, "$options": "i"}
        if genre:
            filters["genre"] = {"$regex": genre, "$options": "i"}

        cursor = books_collection.find(filters)
        results = []
        async for book in cursor:
            results.append(convert_id(book))

        self.set_status(200)
        self.write(tornado.escape.json_encode(results))

    async def post(self, publisher_id):
        self.set_header("Content-Type", "application/json")

        try:
            pub_obj_id = ObjectId(publisher_id)
            data = tornado.escape.json_decode(self.request.body)
        except:
            self.set_status(400)
            self.write({"error": "ID Publisher o JSON non valido"})
            return

  
        publisher = await publishers_collection.find_one({"_id": pub_obj_id})
        if not publisher:
            self.set_status(404)
            self.write({"error": "Publisher non esistente"})
            return


        new_book = {
            "publisher_id": pub_obj_id,
            "title": data["title"],
            "author": data["author"],
            "genre": data["genre"],
            "year": data["year"]
        }

        result = await books_collection.insert_one(new_book)
        
        new_book["_id"] = str(result.inserted_id)
        new_book["publisher_id"] = str(new_book["publisher_id"])

        self.set_status(201)
        response = {
            "message": "Libro aggiunto con successo",
            "book": new_book
        }
        self.write(tornado.escape.json_encode(response))

    async def put(self, publisher_id, book_id):
        self.set_header("Content-Type", "application/json")

        try:
            pub_obj_id = ObjectId(publisher_id)
            book_obj_id = ObjectId(book_id)
            data = tornado.escape.json_decode(self.request.body)
        except:
            self.set_status(400)
            self.write({"error": "ID o JSON non valido"})
            return

        update_data = {
            "title": data["title"],
            "author": data["author"],
            "genre": data["genre"],
            "year": data["year"]
        }

        await books_collection.update_one(
            {"_id": book_obj_id, "publisher_id": pub_obj_id},
            {"$set": update_data}
        )

        self.set_status(200)
        self.write({"message": "Libro aggiornato con successo"})

    async def delete(self, publisher_id, book_id):
        self.set_header("Content-Type", "application/json")

        try:
            pub_obj_id = ObjectId(publisher_id)
            book_obj_id = ObjectId(book_id)
        except:
            self.set_status(400)
            self.write({"error": "ID non valido"})
            return

        await books_collection.delete_one({
            "_id": book_obj_id, 
            "publisher_id": pub_obj_id
        })

        self.set_status(200)
        self.write({"message": "Libro eliminato"})


def make_app():
    return tornado.web.Application([
        (r"/publishers", PublisherHandler),
        (r"/publishers/([0-9a-fA-F]{24})", PublisherHandler),
        (r"/publishers/([0-9a-fA-F]{24})/books", BookHandler),
        (r"/publishers/([0-9a-fA-F]{24})/books/([0-9a-fA-F]{24})", BookHandler)
    ])


async def main():
    app = make_app()
    app.listen(8888)
    print("Server avviato su http://localhost:8888/publishers")
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer arrestato.")
    except Exception as e:
        print(f"Errore critico: {e}")
