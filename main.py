from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import OneLineAvatarIconListItem
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import MDList
from kivymd.theming import ThemableBehavior

from kivy.properties import StringProperty, BooleanProperty, ObjectProperty
from kivy.lang import Builder

import sqlite3

class MainScreen(MDScreen):

    def addTask(self):
        text = self.ids.task.text
        text = str(text)
        if text.strip():
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            sql = ("INSERT INTO tasks(task, complete) VALUES(?, ?);")
            data = (text, False,)
            c.execute(sql, data)
            c.execute("SELECT * FROM tasks")
            tasks = c.fetchall()
            id = str(tasks[-1][0])
            conn.commit()
            conn.close()

            self.ids.mdlist.add_widget(Task(text=text, complete=False, id=id), index=0)
        self.ids.task.text = ''

class Task(OneLineAvatarIconListItem):
    complete = BooleanProperty()
    id = StringProperty() 

class LoginScreen(MDScreen):
    pass

class DialogContentView(MDBoxLayout):
    text = StringProperty()
    item = ObjectProperty()

class DialogContentEdit(MDBoxLayout):
    value = StringProperty()
    item = ObjectProperty()

class DrawerList(ThemableBehavior, MDList):
    def set_color_item(self, instance_item):
        for item in self.children:
            if item.text_color == self.theme_cls.primary_color:
                item.text_color = self.theme_cls.text_color
                break
        instance_item.text_color = self.theme_cls.primary_color

class Main(MDApp):
    task_view = None
    task_edit = None

    def build(self):
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("""CREATE TABLE if not exists tasks(id INTEGER NOT NULL PRIMARY KEY, task, complete)""")
        conn.commit()
        conn.close()
        return Builder.load_file("kivy.kv")

    def on_start(self):
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM tasks")
        tasks = c.fetchall()
        print(tasks)
        for i in tasks:
            complete = True if i[2] == 1 else False
            text = i[1]
            if complete:
                text = '[s]' + text + '[/s]'
            self.root.ids.main.ids.mdlist.add_widget(Task(text=text, complete=complete, id=str(i[0])))
        conn.commit()
        conn.close()

    def showDialogView(self, item):
        if not self.task_view:
            self.task_view = MDDialog(
                    title="View Task",
                    type="custom",
                    content_cls=DialogContentView(text=item.text.replace("[s]", "").replace("[/s]", ""), item=item),
                    )
        self.task_view.open()
        # no clue bit it doesn't update unless updated manually
        self.task_view.content_cls.item = item
        self.task_view.content_cls.text = item.text.replace("[s]", "").replace("[/s]", "")

    def showDialogEdit(self, item):
        self.task_view.dismiss()
        if not self.task_edit:
            self.task_edit = MDDialog(
                    title="Edit Task",
                    type="custom",
                    content_cls=DialogContentEdit(value=item.text.replace("[s]", "").replace("[/s]", ""), item=item),
                    )
        self.task_edit.open()
        self.task_edit.content_cls.item = item
        self.task_edit.content_cls.value = item.text.replace("[s]", "").replace("[/s]", "")

    def moveUp(self, item):
        id = int(item.id)
        if id > 1:
            id_above = int(item.id) - 1
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            #c.execute("UPDATE tasks SET id = ? WHERE id = ?", (id_above, id))
            #get above task
            c.execute("SELECT * FROM tasks WHERE id = ?", (id_above,))
            task_above = c.fetchall()
            #deletes the above task
            c.execute("CREATE TABLE IF NOT EXISTS backup(id INTEGER NOT NULL PRIMARY KEY, task, complete)")
            c.execute("SELECT * FROM tasks")
            tasks = c.fetchall()
            print(tasks)
            for task in tasks:
                if not task[0] == id_above:
                    c.execute("INSERT INTO backup VALUES (?, ?, ?)", (task[0], task[1], task[2]))
            c.execute("DROP TABLE IF EXISTS tasks")
            c.execute("ALTER TABLE backup RENAME TO tasks")\
            #moves clicked task up
            c.execute("UPDATE tasks SET id = ? WHERE id = ?", (id_above, id))
            #adds task_above back to db
            c.execute("INSERT INTO tasks VALUES (?, ?, ?)", (id, task_above[0][1], task_above[0][2]))
            c.execute("SELECT * FROM tasks")
            tasks = c.fetchall()
            print(tasks)
            conn.commit()
            conn.close()
            #change ids in kivy gui
            mdlist = self.root.ids.main.ids.mdlist.children
            x = 0
            for i in mdlist:
                if i == item:
                    list_id = x
                else:
                    x += 1
            item_clicked = item
            above_id = int(self.root.ids.main.ids.mdlist.children[list_id+1].id)
            above_id += 1
            self.root.ids.main.ids.mdlist.children[list_id+1].id = str(above_id)
            self.root.ids.main.ids.mdlist.remove_widget(item)
            self.root.ids.main.ids.mdlist.add_widget(Task(text=item_clicked.text, complete=item_clicked.complete, id=str(int(item_clicked.id)-1)), index=list_id+1)
        else: 
            print("already top")

    def moveDown(self, item):
        id = int(item.id)
        if id < len(self.root.ids.main.ids.mdlist.children):
            id_under = int(item.id) + 1
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            #c.execute("UPDATE tasks SET id = ? WHERE id = ?", (id_above, id))
            #get above task
            c.execute("SELECT * FROM tasks WHERE id = ?", (id_under,))
            task_under = c.fetchall()
            #deletes the above task
            c.execute("CREATE TABLE IF NOT EXISTS backup(id INTEGER NOT NULL PRIMARY KEY, task, complete)")
            c.execute("SELECT * FROM tasks")
            tasks = c.fetchall()
            print(tasks)
            for task in tasks:
                if not task[0] == id_under:
                    c.execute("INSERT INTO backup VALUES (?, ?, ?)", (task[0], task[1], task[2]))
            c.execute("DROP TABLE IF EXISTS tasks")
            c.execute("ALTER TABLE backup RENAME TO tasks")
            #moves clicked task up
            c.execute("UPDATE tasks SET id = ? WHERE id = ?", (id_under, id))
            #adds task_above back to db
            c.execute("INSERT INTO tasks VALUES (?, ?, ?)", (id, task_under[0][1], task_under[0][2]))
            c.execute("SELECT * FROM tasks")
            tasks = c.fetchall()
            print(tasks)
            conn.commit()
            conn.close()
            #change ids in kivy gui
            mdlist = self.root.ids.main.ids.mdlist.children
            x = 0
            for i in mdlist:
                if i == item:
                    list_id = x
                else:
                    x += 1
            item_clicked = item
            under_id = int(self.root.ids.main.ids.mdlist.children[list_id-1].id)
            under_id -= 1
            self.root.ids.main.ids.mdlist.children[list_id-1].id = str(under_id)
            self.root.ids.main.ids.mdlist.remove_widget(item)
            self.root.ids.main.ids.mdlist.add_widget(Task(text=item_clicked.text, complete=item_clicked.complete, id=str(int(item_clicked.id)+1)), index=list_id-1)
        else: 
            print("already last")

    def check(self, item):
        if item.complete:
            item.text = item.text.replace("[s]", "")
            item.text = item.text.replace("[/s]", "")
            item.complete = False
        else:
            item.text = '[s]' + item.text + '[/s]'
            item.complete = True

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        text = item.text.replace("[s]", "").replace("[/s]", "")
        c.execute("UPDATE tasks SET complete = ? WHERE id = ?", (item.complete, int(item.id)))
        conn.commit()
        conn.close()
        self.task_view.dismiss()

    def editTask(self, item):
        text_new = self.task_edit.content_cls.ids.new_text.text
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("UPDATE tasks SET task = ? WHERE id = ?", (text_new, int(item.id))) 
        conn.commit()
        conn.close()
        self.task_edit.dismiss()
        item.text = text_new

    def cancelEdit(self):
        self.task_edit.dismiss()

    def deleteTask(self, item):
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("CREATE TABLE if not exists backup(id INTEGER NOT NULL PRIMARY KEY, task, complete)")
        c.execute("SELECT * FROM tasks")
        tasks = c.fetchall()
        for i in tasks:
            if not i[0] == int(item.id):
                c.execute("INSERT INTO backup VALUES(?, ?, ?)", (i[0], i[1], i[2]))
        c.execute("DROP TABLE IF EXISTS tasks")
        c.execute("ALTER TABLE backup RENAME TO tasks")
        conn.commit()
        conn.close()
        self.task_view.dismiss()

        self.root.ids.main.ids.mdlist.remove_widget(item)


if __name__ == "__main__":
    app = Main()
    app.run()
