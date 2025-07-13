from flask import Flask,render_template,redirect,url_for,request,flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager,UserMixin,login_required,logout_user,login_user,current_user
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] ='saturno'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///proyecto.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# modelos
class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    is_admin = db.Column(db.Boolean, default=False)
    tareas = db.relationship('Tarea', backref='usuario', lazy=True)
    

class Tarea(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titulo = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.datetime.now())
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)



@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


# rutas
@app.route("/")
@login_required
def tarea_read():
    tareas = Tarea.query.filter_by(usuario_id=current_user.id).all()
    return render_template("index.html",tareas=tareas, user = current_user)


@app.route("/tarea_add", methods=['GET','POST'])
@login_required
def tarea_add():
    if request.method == 'POST':
        try:
            id=request.form.get('txtid')
            titulo=request.form.get('txttitulo')
            descripcion=request.form.get('txtdescripcion')
            obj= Tarea(titulo=titulo, descripcion=descripcion,usuario_id=current_user.id)
            db.session.add(obj)
            db.session.commit()
            return redirect(url_for('tarea_read'))
        except Exception as e :
            return redirect('error.html',error=e)
    return render_template("tarea_add.html", user = current_user)


@app.route("/tarea_update/<int:id>", methods=['GET','POST'])
@login_required
def tarea_update(id):
    if request.method == 'POST':
        obj=Tarea.query.filter_by(id=id).first()
        obj.titulo =request.form.get('txttitulo')
        obj.descripcion = request.form.get('txtdescripcion')
        obj.fecha_creacion = datetime.datetime.now()
        db.session.commit()
        return redirect(url_for('tarea_read'))
   
    obj=Tarea.query.filter_by(id=id).first()
    return render_template("tarea_update.html", tarea= obj, user = current_user)


@app.route("/tarea_delete/<int:id>")
@login_required
def tarea_delete(id):
    obj = Tarea.query.filter_by(id=id).first()
    db.session.delete(obj)
    db.session.commit()
    return f"<p>Se ha eliminado, {id}!</p>"


@app.route("/login", methods=['GET','POST'])
def login():
    if request.method=='POST':
        usuario = Usuario.query.filter_by(username=request.form.get('txtusername')).first()
        if usuario and check_password_hash(usuario.password,request.form.get('txtpassword')) :
                login_user(usuario)
                return redirect(url_for('tarea_read'))
        else:
            return render_template('login.html', error='Clave incorrecta')
    else:
        return render_template('login.html', error='')

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/usuario_add", methods=['GET','POST'])
@login_required
def usuario_add():
    if request.method=="POST":
        # id = request.form.get('txtid')
        username = request.form.get('txtusername')
        email = request.form.get('txtemail')
        password = generate_password_hash(request.form.get('txtpassword'))
        is_admin = True if request.form.get('txtis_admin')=='on' else False
        if Usuario.query.filter_by(username=username).first():
            return render_template('usuario_add.html', error="El nombre de usuario ya existe.", user=current_user)
        if Usuario.query.filter_by(email=email).first():
            return render_template('usuario_add.html', error="El correo ya está registrado.", user=current_user)
        
        obj = Usuario(
                #id=id,
                username=username,
                email=email,
                password=password,
                is_admin=is_admin
            )
        db.session.add(obj)
        db.session.commit()
        return redirect(url_for('usuario_add'))
    else:
        return render_template('usuario_add.html', user = current_user)
    

@app.route("/usuario_read", methods=['GET','POST'])
@login_required
def usuario_read():
    usuarios = Usuario.query.all()
    return render_template('usuario_read.html',usuarios=usuarios, user = current_user)


@app.route("/usuario_update/<int:id>", methods=['GET','POST'])
@login_required
def usuario_update(id):
    try:
        objUsuario = Usuario.query.filter_by(id=id).first()
        if request.method == 'POST':
            objUsuario.username = request.form.get('txtusername')
            objUsuario.email = request.form.get('txtemail')
            objUsuario.is_admin = True if request.form.get('txtis_admin') == 'on' else False
            db.session.commit()
            return redirect(url_for('usuario_read'))
        return render_template('usuario_update.html', usuario=objUsuario, user=current_user)
    except Exception as e:
        db.session.rollback()
        return render_template('error.html', error=str(e), user=current_user)
    

@app.route("/usuario_delete/<int:id>", methods=['GET', 'POST'])
@login_required
def usuario_delete(id):
    try:
        objUsuario = Usuario.query.filter_by(id=id).first()

        # Verificar si el usuario existe
        if objUsuario is None:
            raise Exception("⚠️ Usuario no encontrado.")

        # Evitar que un usuario se elimine a sí mismo
        if current_user.id == objUsuario.id:
            raise Exception("❌ No puedes eliminar tu propio usuario.")

        # Evitar eliminar al usuario admin por defecto
        if objUsuario.id == 1:
            raise Exception("❌ No se permite eliminar el usuario administrador por defecto.")

        # Eliminar primero las agendas asociadas
        Tarea.query.filter_by(usuario_id=objUsuario.id).delete()
        # Eliminar el usuario
        db.session.delete(objUsuario)
        db.session.commit()

        return redirect(url_for('usuario_read'))

    except Exception as e:
        db.session.rollback()
        return render_template('error.html', error=str(e), user=current_user)

if __name__=="__main__":
    with app.app_context():
        db.create_all()
        if not Usuario.query.filter_by(id=1).first():
            admin = Usuario(
                username='admin',
                email='admin@example.com',
                password=generate_password_hash('12345'),
                # generate_password_hash('admin', method='sha256'),
                is_admin=True
            )

            db.session.add(admin)
            db.session.commit()


    app.run(debug=True)