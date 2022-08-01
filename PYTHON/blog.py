from ast import keyword
from crypt import methods
import email
from attr import validate
from cherrypy import url
from click import confirm
from django.shortcuts import render
from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from matplotlib.pyplot import title
from sympy import content, re
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
#kullanıcı giriş decorator----------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args,**kwargs)
        else:
            flash("Bu sayfayı görüntülemek için giriş yapınız ","danger")
            return redirect(url_for("login"))
            
        
    return decorated_function
# ------------------------------------------------------------------------------------------------
app=Flask(__name__)
app.secret_key="ybblog"
#flask ile mysql arasındaki bağlantılar--------------------------------------------------------------
app.config["MYSQL_HOST"]="127.0.0.1"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="ybblog"
app.config["MYSQL_CURSORCLASS"]="DictCursor"
mysql= MySQL(app)
#Kulllanıcı kayıt formu---------------------------------------------------------------------
class RegisterForm(Form):
    name=StringField("İsim Soyisim",validators=[validators.Length(min=4,max=25)])
    username=StringField("Kullancı Adı",validators=[validators.Length(min=5,max=25),validators.DataRequired(message="Lütfen Kullanıcı Adınzı Giriniz")])
    email=StringField("Email",validators=[validators.Email(message="Lütfen geçerli email adresinizi giriniz")])
    password=PasswordField("Parola",validators=[validators.Length(min=4,max=25),
    validators.DataRequired("lütfen parola giriniz"),
    validators.EqualTo(fieldname="confirm",message="Parolanız uyuşmuyor...")])
    confirm=PasswordField("Parola Doğrula")
#----------------------login formu---------------------------------------------------------
class LoginForm(Form):
    username=StringField("Kullanıcı Adı")
    password=PasswordField("Parola Giriniz")
#-----------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")
#-------------------------------------------------- --------------------------------------
@app.route("/about")
def about():
    return render_template("about.html")
#kayıt olma-----------
@app.route("/register",methods=["GET","POST"])
def register():
    form=RegisterForm(request.form)
    if request.method== "POST" and form.validate():
        name=form.name.data
        username=form.username.data
        email=form.email.data
        password=sha256_crypt.encrypt(form.password.data)  
        cursor=mysql.connection.cursor()
        sorgu="Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()
        flash("Başarıyla Kayıt Oldunuz","success")

        return redirect(url_for("login"))
    else:
            return render_template ("register.html",form=form)
#login işlemi -------------------------------------------------------------------------
@app.route("/login",methods=["GET","POST"])
def login ():
    form=LoginForm(request.form)
    if request.method=="POST":
        username=form.username.data
        password_entered=form.password.data
        cursor=mysql.connection.cursor()
        sorgu="Select * from users where username=%s"
        result=cursor.execute(sorgu,(username,))
        if result > 0:
            data=cursor.fetchone() 
            real_password=data["password"]  
            if sha256_crypt.verify(password_entered,real_password):
                flash("Başarıyla giriş yaptınız","success")
                session["logged_in"]=True
                session["username"]=username
                return redirect(url_for("index"))
            else:
                flash("Parola yanlış girildi","danger")
                return redirect(url_for("login"))     

        else:
            flash("Böyle bir kullanıcı bulunmuyor.","danger")
            return redirect(url_for("login"))

    


    return render_template("login.html",form=form)
#logout -----------------------------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
#--------------dashboard-------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    cursor=mysql.connection.cursor()
    sorgu="Select * from articles where author =%s"
    result=cursor.execute(sorgu,(session["username"],))
    if result > 0:
        articles=cursor.fetchall()
        return render_template("dashboard.html",articles=articles)

    else:
        return render_template("dashboard.html")

#-----------makale ekleme--------------
@app.route("/addarticle",methods=["GET","POST"])
def addarticles():
    form=ArticleForm(request.form)
    if request.method== "POST"  and form.validate():
        title=form.title.data
        content=form.content.data
        cursor=mysql.connection.cursor()
        sorgu="Insert into articles(title,author,content) Values (%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("Makale başarıyla eklendi...","success")
        return redirect(url_for("dashboard"))
    return render_template("addarticles.html",form=form)
#------------ makale detay -------------
@app.route("/article/<string:id>")
def article(id):
    cursor=mysql.connection.cursor()
    sorgu="Select *from articles where id = %s"
    result=cursor.execute(sorgu,(id,))
    if result > 0:
        article=cursor.fetchone()
        return render_template("article.html",article=article)

    else:
        return render_template("article.html")

    


    return render_template("addarticles.html",form=form)
#makale formu----------------
class ArticleForm(Form):
    title=StringField("Makale Başlığı",validators=[validators.Length(min=5,max=100)])
    content=TextAreaField("Makale İçeriği",validators=[validators.Length(min=10)])
#makaleler-----------------------------------------------------
@app.route("/article")
def articles():
    cursor=mysql.connection.cursor()
    sorgu="Select * from articles "
    result=cursor.execute(sorgu)
    if result > 0:
        articles=cursor.fetchall()
        return render_template("articles.html",articles=articles)
    else:
        return render_template("articles.html")
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor=mysql.connection.cursor()
    sorgu="Select * from articles where author= %s and id = %s"
    result=cursor.execute(sorgu,(session["username"],id))

    if result>0:
        sorgu2="Delete  from articles where id=%s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya bu işleme yetkiniz yok","danger")
        redirect(url_for("index"))
#------------ makale güncelle----
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def update(id):
    if request.method== "GET":
        cursor=mysql.connection.cursor()
        sorgu="Select * from articles where id=%s and author =%s "
        result=cursor.execute(sorgu,(id,session["username"]))
        if result ==0:
            flash("Böyle bir makale yok veya yetkiniz yok","danger")
            return redirect(url_for("index"))
        else:
            article=cursor.fetchone()
            form=ArticleForm()
            form.title.data=article["title"]
            form.content.data=article["content"]
            return render_template("updates.html",form=form)

    else:
        form=ArticleForm(request.form)
        newTitle=form.title.data
        newContent=form.content.data
        sorgu2="Update articles Set title=%s,content=%s where id=%s "
        cursor=mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()
        flash("Makale başarıyla güncellenmiştir","success")
        return redirect(url_for("index"))
    
#arama sayfası---------
@app.route("/search",methods=["GET","POST"])
def search():
    if request.method=="GET":
        return redirect(url_for("index"))
    else:
        keyword=request.form.get("keyword")
        cursor=mysql.connection.cursor()
        sorgu="Select * from articles where title like '%"+ keyword +"%'"
        result= cursor.execute(sorgu)
        if result ==0:
            flash("Aranan kelimeyle eşleşen makale yok...","warning")
            return redirect(url_for("articles"))
        else:
            articles=cursor.fetchall()
            return render_template("articles.html",articles=articles)


            
    



if __name__ == "__main__":
    app.run(debug=True)
