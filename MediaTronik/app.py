from flask import Flask, render_template, request, redirect, url_for, session  # For flask implementation
from bson import ObjectId  # For ObjectId to work
from pymongo import MongoClient
import random
# import os

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_unicaysecreta'  # importante para las sesiones
title = "MediaTronik"
heading = "MediaTronik"  # necesario??? NO

# Un-Comment when running against the Cosmos DB Emulator
# client = MongoClient("mongodb://ref-sample-app.documents.azure.com:10255/?ssl=true") #host uri
# db = client.test    #Select the database


# Comment out when running locally
client = MongoClient("mongodb://localhost:27017/")
db = client.MyDB  # Select the database
#  db.authenticate(name=os.getenv("MONGO_USERNAME"),password=os.getenv("MONGO_PASSWORD"))

users = db.users  # Select the collection from users
lists = db.lists  # Select the collection from lists
media = db.media  # Select the collection movies and series


# PRINCIPAL PAGE RENDER
@app.route('/')
def index():
    return redirect(url_for('listMoviesSeries'))


@app.route('/mediaPage')
def mediaPage():
    element = media.find_one({"_id": int(request.args.get('id'))})
    return render_template('media.html', element=element, t=title, h=heading)

@app.route('/enviar_calificacion', methods=['POST'])
def enviar_calificacion():
    elemento_id = int(request.args.get('id'))
    nueva_calificacion = int(request.form.get('estrellas'))
    elemento = media.find_one({"_id": elemento_id})
    rating_actual = elemento.get('Rating', 0)  # Si no hay Rating, se asume 0
    # Calcular el nuevo rating como el promedio
    nuevo_rating = (rating_actual + nueva_calificacion) / 2
    # Actualizar el rating en la base de datos
    media.update_one({"_id": elemento_id}, {"$set": {"Rating": nuevo_rating}})
    return redirect(url_for('mediaPage', id=elemento_id))  # Redirigir a la página del elemento

@app.route("/listMoviesSeries", methods=['GET'])
def listMoviesSeries():
    # Display the all media
    movies = media.find({'format': 'movie'}, {'format': 1, 'title': 1, 'Rating': 1})
    series = media.find({'format': 'series'}, {'format': 1, 'title': 1, 'Rating': 1})
    
    random_genres_1, random_genres_2 = random.sample(media.distinct('genres'), 2)

    random_movies_1 = media.find({'genres': {'$in': [random_genres_1]}}, {'format': 1, 'title': 1, 'Rating': 1})
    random_movies_2 = media.find({'genres': {'$in': [random_genres_2]}}, {'format': 1, 'title': 1, 'Rating': 1})

    return render_template('index.html', movies=movies, series=series, random_movies_1=random_movies_1, random_movies_2=random_movies_2, random_genres_1=random_genres_1, random_genres_2=random_genres_2, t=title, h=heading)


# LOGIN REQUIREMENTS
@app.route('/login')
def login():
    session.pop('username', None)
    return render_template('userLogin.html', t=title, h=heading)


@app.route('/logout')
def logout():
    # Elimina la clave 'username' de la sesión
    session.pop('username', None)
    return redirect(url_for('listMoviesSeries'))


@app.route('/verifyFirstAccess', methods=['POST'])
def verifyFirst():
    user_name = request.form['username']
    user_document = users.find_one({"_id": user_name})
    if user_document:
        user_password = request.form['password']
        if user_password == user_document.get('password'):
            # Autenticación exitosa, establece la sesión y redirige
            session['username'] = user_name
            return redirect(url_for('listMoviesSeries'))
        else:
            # Contraseña incorrecta
            result = "La contraseña no es válida."
    else:
        # Usuario no encontrado
        result = "El usuario no existe."
    return render_template('userLogin.html', result=result, t=title, h=heading)


# REGISTER PARAMETERS
@app.route('/sigin')
def sigin():
    session.pop('username', None)
    return render_template('userSignin.html', result="Ingrese un usuario", is_registered=False, t=title, h=heading)


@app.route('/insertUser', methods=['POST'])
def insertUser():
    is_register = request.args.get('is_register')
    if is_register != True:
        username = request.form['username']
        if not users.find_one({"_id": username}):
            session['username'] = username
            password = request.form['password']
            session['password'] = password
            users.insert_one({"_id": username, "password": password})
            return render_template('userSignin.html', result="Ingrese sus datos", is_registered=True, t=title, h=heading)
    return render_template('userSignin.html', result="Usuario no valido, ingrese otro", is_registered=False, t=title, h=heading)


@app.route('/insertDataUser', methods=['POST'])
def insertDataUser():
    users.update_one({"_id": session.get('username')},
                     {"$set": {"name": request.form['name'], "email": request.form['email']}})
    session.pop('password', None)
    return redirect(url_for('listMoviesSeries'))


@app.route("/searchMedia", methods=['GET'])
def searchMedia():
    query = request.args.get('query', '')
    genre = request.args.get('genre', '')
    year = request.args.get('year', '')
    format = request.args.get('format', '')

    # Construir el filtro para la consulta en MongoDB
    filter_query = {'title': {'$regex': query, '$options': 'i'}}

    if genre:
        filter_query['genres'] = genre

    if year:
        filter_query['year'] = int(year)

    if format:
        filter_query['format'] = format

    # Realizar la consulta a MongoDB
    results = media.find(filter_query)

    return render_template('searchMedia.html', results=results, t=title, h=heading)


wsgi_app = app.wsgi_app

if __name__ == "__main__":
    app.run(debug=True, port=5000)