from Tkinter import *
import Tkinter as tk
import PIL.Image
import tkMessageBox
import tkFont,tkFileDialog

# This part is designed for the menu for the MLN
# The question is this: i wanted to build another class the MyMenu, the problem is when i build a model, i am not sure how to refer another class's properties. This problem
# is met when i was try to save the show the result on the left hand side.

class  Application(tk.Tk):
   def __init__(self, parent):
      tk.Tk.__init__(self,parent)
      print(self)
      self.parent = parent
      print(self)
      self.initialize()
   def initialize(self):

      self.geometry("1200x600")
      self.title('IFT Tool Box')
      var = IntVar()
      # # Grid.rowconfigure(root, 0, weight=1)
      # # Grid.columnconfigure(root, 0, weight=1)
      frame=Frame(self)
      frame.grid(row=0, column=3, sticky='NEWS')
      # # grid=Frame(frame)
      # # grid.grid(sticky=N+S+E+W, column=0, row=0, columnspan=2)
      # # Grid.rowconfigure(frame, 7, weight=1)
      # # Grid.columnconfigure(frame, 0, weight=1)
      helv36 = tkFont.Font(family='Helvetica', size=20, weight=tkFont.BOLD)
      row = 0
      lab1 = Label(frame, text= "MLN Reason Engine",font=helv36)
      lab1.grid(row = row, column=1,columnspan=2,sticky='N')
      # lab1.grid(row=row,column=0,sticky=W)

      photo_tmp = PIL.Image.open('a.jpg')
      photo_tmp = photo_tmp.resize((45,45))
      photo_tmp.save("b.gif",'gif')
      photo = PhotoImage(file='b.gif')
      lab2=Label(frame,image=photo)
      lab2.grid(row=row,column=0,columnspan=1,rowspan=1,sticky=W,padx=5,pady=5)

      row +=1
      self.lab2=Label(frame,text='Decision Rule:')
      self.lab2.grid(row=row, column=0,sticky=W)
      self.lab3=Label(frame,text='Evidence:')
      self.lab3.grid(row=row, column = 2,sticky=W)
      row +=1
      self.text_load= Text(frame,background='yellow')
      self.text_load.insert(INSERT,'DATA description...')
      self.text_load.grid(row=row,column=0, rowspan=1,columnspan=2,sticky="W")

      self.text_res= Text(frame,background='yellow')
      self.text_res.insert(INSERT,'Inference Result...')
      self.text_res.grid(row=row,column=2, rowspan=1,columnspan=2,sticky="NEWS")


      row +=1
      btn2=Button(frame,text="Inference")
      btn2.grid(row=row,sticky=W)
      btn3=Button(frame, text="Save")
      btn3.grid(row=row,column =3, sticky = E)

      row +=1
      # This part is for display text file.
      text1 = Text(frame,background="green", foreground="black",height=5)
      text1.insert(INSERT,'Running...')
      text1.grid(row=row,column=0, rowspan=2, columnspan =4, sticky='EW' )
      # yscrollbar=Scrollbar(frame, orient=VERTICAL, command=text1.yview)
      checkbutton = Checkbutton(frame, text='Save Log File', variable=var)
      checkbutton.grid(columnspan=2, sticky=W)

      self.menubar = Menu(self)
      filemenu = Menu(self.menubar, tearoff=0)
      filemenu.add_command(label="New", command=self.donothing)
      filemenu.add_command(label="Open", command=self.donothing)
      filemenu.add_command(label="Save", command=self.donothing)
      filemenu.add_command(label="Save as...", command=self.donothing)
      filemenu.add_command(label="Close", command=self.donothing)
      filemenu.add_separator()
      filemenu.add_command(label="Exit", command=self.quit)
      self.menubar.add_cascade(label="File", menu=filemenu)

      editmenu = Menu(self.menubar, tearoff=0)
      editmenu.add_command(label="Undo", command=self.donothing)
      editmenu.add_separator()
      editmenu.add_command(label="Cut", command=self.donothing)
      editmenu.add_command(label="Copy", command=self.donothing)
      editmenu.add_command(label="Paste", command=self.donothing)
      editmenu.add_command(label="Delete", command=self.donothing)
      editmenu.add_command(label="Select All", command=self.donothing)
      self.menubar.add_cascade(label="Edit", menu=editmenu)
      optionmenu = Menu(self.menubar, tearoff=0)
      submenu = Menu(optionmenu)
      submenu.add_command(label="MLN")
      submenu.add_command(label='BLN')
      optionmenu.add_cascade(label="Model Selection", menu=submenu)
      optionmenu.add_command(label="Data-Driven", command=self.donothing)
      optionmenu.add_command(label="Model-Driven", command=self.donothing)
      self.menubar.add_cascade(label="Option", menu=optionmenu)

      helpmenu = Menu(self.menubar, tearoff=0)
      helpmenu.add_command(label="Help instruction", command=self.donothing)
      helpmenu.add_command(label="About...", command=self.donothing)
      self.menubar.add_cascade(label="Help", menu=helpmenu)
      self.config(menu=self.menubar)
      print(self)

   def donothing(self):
      self.filename = tkFileDialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("db files","*.db"),("jpeg files","*.jpg"),("all files","*.*")))
      print(self.filename)
      f=open(self.filename)
      self.text_load.delete('1.0',END)
      self.text_load.insert(1.0,f.read())
      print(self)






   def addmenu(self, Menu):  ##### What does the Menu mean?
      Menu(self)




class  MyMenu():
   def donothing(self):
      self.filename = tkFileDialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("db files","*.db"),("jpeg files","*.jpg"),("all files","*.*")))
      print(self.filename)
      f=open(self.filename)
      print(self)
   def __init__(self,root):
      # initialization of menu bar
      self.menubar=Menu(root)
      filemenu = Menu(self.menubar, tearoff=0)
      filemenu.add_command(label="New", command=self.donothing)
      filemenu.add_command(label="Open", command=self.donothing)
      filemenu.add_command(label="Save", command=self.donothing)
      filemenu.add_command(label="Save as...", command=self.donothing)
      filemenu.add_command(label="Close", command=self.donothing)
      filemenu.add_separator()
      filemenu.add_command(label="Exit", command=root.quit)
      self.menubar.add_cascade(label="File", menu=filemenu)

      editmenu = Menu(self.menubar, tearoff=0)
      editmenu.add_command(label="Undo", command=self.donothing)
      editmenu.add_separator()
      editmenu.add_command(label="Cut", command=self.donothing)
      editmenu.add_command(label="Copy", command=self.donothing)
      editmenu.add_command(label="Paste", command=self.donothing)
      editmenu.add_command(label="Delete", command=self.donothing)
      editmenu.add_command(label="Select All", command=self.donothing)
      self.menubar.add_cascade(label="Edit", menu=editmenu)
      optionmenu = Menu(self.menubar, tearoff=0)
      submenu= Menu(optionmenu)
      submenu.add_command(label="MLN")
      submenu.add_command(label='BLN')
      optionmenu.add_cascade(label="Model Selection",menu=submenu)
      optionmenu.add_command(label="Data-Driven", command=self.donothing)
      optionmenu.add_command(label="Model-Driven", command=self.donothing)
      self.menubar.add_cascade(label="Option",menu=optionmenu)

      helpmenu = Menu(self.menubar, tearoff=0)
      helpmenu.add_command(label="Help instruction", command=self.donothing)
      helpmenu.add_command(label="About...", command=self.donothing)
      self.menubar.add_cascade(label="Help", menu=helpmenu)
      root.config(menu=self.menubar)
      print(self)


def main():
   app = Application(None)
   app.title('IFT MLN Toolbox')
   # Mymenu(app)
   # app.addmenu(MyMenu)
   print(app)
   app.mainloop()

if __name__=='__main__':
   main()

