import flask

import models
import forms


app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://coe:CoEpasswd@127.0.0.1:5433/coedb"
models.init_app(app)


@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()
    return flask.render_template(
        "index.html",
        notes=notes,
    )


@app.route("/notes/create", methods=["GET", "POST"])
def notes_create():
    form = forms.NoteForm()
    if not form.validate_on_submit():
        print("error", form.errors)
        return flask.render_template(
            "notes-create.html",
            form=form,
        )
    note = models.Note()
    form.populate_obj(note)
    note.tags = []

    db = models.db
    for tag_name in form.tags.data:
        tag = (
            db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
            .scalars()
            .first()
        )

        if not tag:
            tag = models.Tag(name=tag_name)
            db.session.add(tag)

        note.tags.append(tag)

    db.session.add(note)
    db.session.commit()

    return flask.redirect(flask.url_for("index"))


@app.route("/tags/<tag_name>")
def tags_view(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()

    return flask.render_template(
        "tags-view.html",
        tag_name=tag_name,
        notes=notes,
    )

@app.route("/notes/<int:note_id>/edit", methods=["GET", "POST"])
def notes_edit(note_id):
    db = models.db
    note = db.session.execute(
        db.select(models.Note).where(models.Note.id == note_id)
    ).scalars().first()

    form = forms.NoteForm(obj=note)

    if form.validate_on_submit():
        # ยกเลิกการใช้ form.populate_obj(note) แล้วกำหนดค่าเองทีละตัวแทน
        note.title = form.title.data
        note.description = form.description.data
        
        note.tags.clear() # ล้าง Tag เดิมออกก่อน

        # อัปเดต Tag ใหม่
        for tag_name in form.tags.data:
            tag = db.session.execute(
                db.select(models.Tag).where(models.Tag.name == tag_name)
            ).scalars().first()

            if not tag:
                tag = models.Tag(name=tag_name)
                db.session.add(tag)

            note.tags.append(tag)

        db.session.commit()
        return flask.redirect(flask.url_for("index"))

    # ดึงรายชื่อ Tag เดิมมาแสดงในช่องกรอกตอนโหลดหน้าเว็บครั้งแรก
    if flask.request.method == "GET":
        form.tags.data = [tag.name for tag in note.tags]

    return flask.render_template("notes-create.html", form=form)

@app.route("/tags/<tag_name>/edit", methods=["GET", "POST"])
def tags_edit(tag_name):
    db = models.db
    # ค้นหา Tag จากชื่อ
    tag = db.session.execute(
        db.select(models.Tag).where(models.Tag.name == tag_name)
    ).scalars().first()

    if not tag:
        return flask.redirect(flask.url_for("index"))

    # เมื่อกดปุ่ม Save จะเข้ามาทำงานส่วนนี้
    if flask.request.method == "POST":
        new_name = flask.request.form.get("new_tag_name")
        if new_name:
            tag.name = new_name
            db.session.commit()
            return flask.redirect(flask.url_for("tags_view", tag_name=tag.name))

    # เพื่อความรวดเร็ว ใช้ HTML Form ง่ายๆ ในนี้เลยครับ
    html_form = f"""
    <h2>Edit Tag: {tag.name}</h2>
    <form method="POST">
        <input type="text" name="new_tag_name" value="{tag.name}" required>
        <button type="submit">Save</button>
    </form>
    <br>
    <a href="/">Back to Home</a>
    """
    return html_form
if __name__ == "__main__":
    app.run(debug=True)
