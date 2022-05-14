from flask import Flask, request
from flask_restx import Api, Resource
from models import db, Movie, Director, Genre, MovieSchema, DirectorSchema, GenreSchema

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['RESTX_JSON'] = {'ensure_ascii': False, 'indent': 3}
app.config["JSON_SORT_KEYS"] = False

db.init_app(app)


api = Api(app)

movies_ns = api.namespace('movies')
movies_schema = MovieSchema(many=True)
movie_schema = MovieSchema()

genres_ns = api.namespace('genres')
genres_schema = GenreSchema(many=True)
genre_schema = GenreSchema()

directors_ns = api.namespace('directors')
directors_schema = DirectorSchema(many=True)
director_schema = DirectorSchema()


@movies_ns.route('/')
class MoviesView(Resource):
    def post(self):
        req_json = request.json
        # check if movie exists in db before adding
        current_movies = db.session.query(Movie.title, Movie.year).filter(
            Movie.title == req_json.get('title'),
            Movie.year == req_json.get('year')
        ).all()
        if not current_movies:
            new_movie = Movie(**req_json)
            db.session.add(new_movie)
            db.session.commit()
        return "", 201

    def get(self):
        general_query = db.session.query(
                Movie.id,
                Movie.title,
                Movie.year,
                Movie.rating,
                Movie.genre_id,
                Movie.director_id,
                Genre.name.label('genre_name'),
                Director.name.label('director_name')
            ).outerjoin(Movie.director).outerjoin(Movie.genre)
        page_num = request.args.get('page', type=int)
        director_id = request.args.get('director_id', type=int)
        director_name = request.args.get('director_name')
        genre_id = request.args.get('genre_id', type=int)
        genre_name = request.args.get('genre_name')
        if page_num:
            movies_per_page = 3
            offset_value = (page_num - 1) * movies_per_page
            movies_per_page = general_query.limit(movies_per_page).offset(offset_value)
            return movies_schema.dump(movies_per_page), 200
        elif genre_id and director_id:
            movies_by_genre_director = general_query.filter(
                Movie.genre_id == genre_id,
                Movie.director_id == director_id).all()
            return movies_schema.dump(movies_by_genre_director), 200
        elif genre_id or genre_name:
            movies_by_genre = general_query.filter(db.or_(
                Movie.genre_id == genre_id,
                Genre.name == genre_name
            )).all()
            return movies_schema.dump(movies_by_genre), 200
        elif director_id or director_name:
            movies_by_director = general_query.filter(
                db.or_(Movie.director_id == director_id, Director.name == director_name)).all()
            return movies_schema.dump(movies_by_director), 200
        else:
            all_movies = db.session.query(Movie).all()
            return movies_schema.dump(all_movies), 200


@movies_ns.route('/<int:mid>')
class MovieView(Resource):
    def get(self, mid: int):
        movie_by_id = db.session.query(
            Movie.id,
            Movie.title,
            Movie.description,
            Movie.year,
            Movie.trailer,
            Movie.rating,
            Genre.name.label('genre_name'),
            Director.name.label('director_name')
        ).join(Director).join(Genre).filter(Movie.id == mid).first_or_404(
            description='Movie with id {} not found'.format(mid)
        )
        return movie_schema.dump(movie_by_id)

    def delete(self, mid: int):
        movie_to_delete = db.session.query(Movie).get(mid)
        if not movie_to_delete:
            return '', 404
        db.session.delete(movie_to_delete)
        db.session.commit()
        return "", 204

    def patch(self, mid: int):
        movie_to_patch = db.session.query(Movie).get(mid)
        if not movie_to_patch:
            return '', 404
        req_json = request.json
        if 'title' in req_json:
            movie_to_patch.title = req_json['title']
        if 'description' in req_json:
            movie_to_patch.description = req_json['description']
        if 'trailer' in req_json:
            movie_to_patch.trailer = req_json['trailer']
        if 'year' in req_json:
            movie_to_patch.trailer = req_json['year']
        if 'rating' in req_json:
            movie_to_patch.rating = req_json['rating']
        if 'genre_id' in req_json:
            movie_to_patch.genre_id = req_json['genre_id']
        if 'director_id' in req_json:
            movie_to_patch.genre_id = req_json['director_id']
        db.session.add(movie_to_patch)
        db.session.commit()
        return '', 204

    def put(self, mid):
        movie_to_put = db.session.query(Movie).get(mid)
        if not movie_to_put:
            return '', 404
        req_json = request.json
        movie_to_put.title = req_json.get('title')
        movie_to_put.description = req_json.get('description')
        movie_to_put.trailer = req_json.get('trailer')
        movie_to_put.year = req_json.get('year')
        movie_to_put.rating = req_json.get('rating')
        movie_to_put.genre_id = req_json.get('genre_id')
        movie_to_put.director_id = req_json.get('director_id')
        db.session.add(movie_to_put)
        db.session.commit()
        return '', 204


@genres_ns.route('/')
class GenresView(Resource):
    def post(self):
        req_json = request.json
        new_genre = Genre(**req_json)
        db.session.add(new_genre)
        db.session.commit()
        return '', 201

    def get(self):
        all_genres = db.session.query(Genre).all()
        return genres_schema.dump(all_genres), 200


@genres_ns.route('/<int:gid>')
class GenreView(Resource):
    def get(self, gid):
        genre_by_id = db.session.query(Genre).get_or_404(gid)
        return genre_schema.dump(genre_by_id), 200

    def delete(self, gid):
        genre_to_delete = db.session.query(Genre).get_or_404(gid)
        db.session.delete(genre_to_delete)
        db.session.commit()
        return '', 204

    def put(self, gid):
        genre_to_put = db.session.query(Genre).get_or_404(gid)
        req_json = request.json
        genre_to_put.name = req_json.get('name')
        db.session.add(genre_to_put)
        db.session.commit()
        return '', 204

    def patch(self, gid):
        genre_to_patch = db.session.query(Genre).get_or_404(gid)
        req_json = request.json
        if 'name' in req_json:
            genre_to_patch.name = req_json['name']
            db.session.add(genre_to_patch)
            db.session.commit()
        return '', 204


@directors_ns.route('/')
class DirectorsView(Resource):
    def get(self):
        all_directors = db.session.query(Director).all()
        return directors_schema.dump(all_directors), 200

    def post(self):
        req_json = request.json
        new_director = Director(**req_json)
        db.session.add(new_director)
        db.session.commit()
        return '', 201


@directors_ns.route('/<int:did>')
class DirectorView(Resource):
    def get(self, did):
        director_by_id = db.session.query(Director).get_or_404(did)
        return director_schema.dump(director_by_id), 200

    def delete(self, did):
        director_to_delete = db.session.query(Director).get_or_404(did)
        db.session.delete(director_to_delete)
        db.session.commit()
        return '', 204

    def put(self, did):
        director_to_put = db.session.query(Director).get_or_404(did)
        req_json = request.json
        director_to_put.name = req_json.get('name')
        db.session.add(director_to_put)
        db.session.commit()
        return '', 204

    def patch(self, did):
        director_to_patch = db.session.query(Director).get_or_404(did)
        req_json = request.json
        if 'name' in req_json:
            director_to_patch .name = req_json.get('name')
            db.session.add(director_to_patch)
            db.session.commit()
        return '', 204


if __name__ == '__main__':
    app.run(debug=True)


