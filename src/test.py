import Tkinter as tk
from Tkinter import *
import PIL.Image
import tkMessageBox
import tkFont,tkFileDialog



Large_Font=("Verdana",12)
class App(tk.Tk):
    def __init__(self,*args,**kwargs):
        tk.Tk.__init__(self,*args,**kwargs)
        container = tk.Frame(self)
        container.pack(side="top", fill="both",expand = True)
        container.grid_rowconfigure(0,weight=1)
        container.grid_columnconfigure(0,weight=1)
        self.frames = {}

        for F in (StartPage,PageOne, PageTwo):


            self.title('IFT Tool Box')

            frame= F(container,self) # pass the container and self into the StartPage, not sure about the self.container?

            self.frames[F] =frame

            frame.grid(row=0, column=0, stick="nsew")

        self.show_frame(StartPage)

    def show_frame(self,cont):
        frame = self.frames[cont]
        if cont==PageOne:
            self.geometry("570x550")
        elif cont==StartPage:
            self.geometry("1132x541")
        elif cont==PageTwo:
            self.geometry("570x550")

        print self.winfo_width()
        print self.winfo_height()
        frame.tkraise()
        menubar = frame.menubar_1(self)
        self.config(menu = menubar)
def qf(param):
    print(param)
class StartPage(tk.Frame):
    def __init__(self,parent, controller):
        tk.Frame.__init__(self,parent)

        self.grid(row=0, column=3, sticky='NEWS')
        helv36 = tkFont.Font(family='Helvetica', size=20, weight=tkFont.BOLD)
        var = IntVar()

        row = 0
        lab1 = Label(self, text="MLN Reason Engine", font=helv36)
        lab1.grid(row=row, column=1, columnspan=2, sticky='N')
        photo_tmp = PIL.Image.open('a.jpg')
        photo_tmp = photo_tmp.resize((45, 45))
        photo_tmp.save("b.gif", 'gif')
        photo = PhotoImage(file='b.gif')
        lab2 = Label(self, image=photo)
        lab2.grid(row=row, column=0)

        # lab2.grid(row=row, column=0, columnspan=1, rowspan=1, sticky=W, padx=5, pady=5)

        row +=1
        lab2=Label(self,text='Decision Rule:')
        lab2.grid(row=row, column=0,sticky=W)
        lab3=Label(self,text='Evidence:')
        lab3.grid(row=row, column = 2,sticky=W)
        btn_edit = Button(self,text="Edit",command=lambda :controller.show_frame(PageOne))
        btn_edit.grid(row= row, column=1,sticky= E)
        btn_edit_evi = Button(self,text="Edit",command= lambda: controller.show_frame(PageTwo))
        btn_edit_evi.grid(row = row, column=3, sticky=E)
        row +=1
        self.text_load= Text(self,background='yellow')
        self.text_load.insert(INSERT,'DATA description...')
        self.text_load.grid(row=row,column=0, rowspan=1,columnspan=2,sticky="W")

        text_res= Text(self,background='yellow')
        text_res.insert(INSERT,'Inference Result...')
        text_res.grid(row=row,column=2, rowspan=1,columnspan=2,sticky="NEWS")

        row +=1
        btn2=Button(self,text="Inference",command=lambda: controller.show_frame(PageOne))
        btn2.grid(row=row,sticky=W)
        btn3=Button(self, text="Save")
        btn3.grid(row=row,column =3, sticky = E)

        row +=1
        # This part is for display text file.
        text1 = Text(self,background="green", foreground="black",height=5)
        text1.insert(INSERT,'Running...')
        text1.grid(row=row,column=0, rowspan=2, columnspan =4, sticky='EW' )
        # yscrollbar=Scrollbar(frame, orient=VERTICAL, command=text1.yview)
        checkbutton = Checkbutton(self, text='Save Log File', variable=var, command=lambda :controller.show_frame(PageOne))
        checkbutton.grid(columnspan=2, sticky=W)
### Menu bar set up:


    def menubar_1(self, root):
        menubar = Menu(root)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="New")
        filemenu.add_command(label="Open",command=self.Open_File)

        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        editmenu = Menu(menubar, tearoff=0)
        editmenu.add_command(label="Undo")
        editmenu.add_separator()
        editmenu.add_command(label="Cut")

        menubar.add_cascade(label="Edit")
        optionmenu = Menu(menubar, tearoff=0)
        submenu = Menu(optionmenu)
        submenu.add_command(label="MLN")
        submenu.add_command(label='BLN')
        optionmenu.add_cascade(label="Model Selection", menu=submenu)
        optionmenu.add_command(label="Data-Driven")
        optionmenu.add_command(label="Model-Driven")
        menubar.add_cascade(label="Option", menu=optionmenu)

        helpmenu = Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Help instruction")
        return  menubar


    def Open_File(self):
        self.filename = tkFileDialog.askopenfilename(initialdir="/", title="Select file", filetypes=(
            ("db files", "*.db"), ("jpeg files", "*.jpg"), ("all files", "*.*")))
        print(self.filename)
        f = open(self.filename)
        print f
        self.text_load.delete('1.0', END)
        self.text_load.insert(1.0, f.read())
    # def menubar_1(self, root):
    #     menubar = tk.Menu(root)
    #     pageMenu = tk.Menu(menubar)
    #     pageMenu.add_command(label="PageOne")
    #     pageMenu.add_command(label="PageTwo")
    #     menubar.add_cascade(label="Option", menu=pageMenu)
    #     return menubar
class PageOne(tk.Frame):
    def __init__(self,parent, controller):

        tk.Frame.__init__(self,parent)

        self.grid(row=0, column=2, sticky='NEWS')
        helv36 = tkFont.Font(family='Helvetica', size=20, weight=tkFont.BOLD)
        var = IntVar()

        row = 0
        lab1 = Label(self, text="MLN Rules Editor", font=helv36)
        lab1.grid(row=row, column=0, columnspan=2, sticky='N')

        row +=1
        lab2=Label(self,text='Decision Rule:')
        lab2.grid(row=row, column=0,sticky=W)
        row +=1
        self.text_load= Text(self)
        self.text_load.insert(INSERT,'DATA description...')
        self.text_load.grid(row=row,column=0, rowspan=1,columnspan=2,sticky="W")


        row +=1
        btn2=Button(self,text="Main Menu",command=lambda: controller.show_frame(StartPage))
        btn2.grid(row=row,sticky=W)
        btn3=Button(self, text="Save",command=self.Save_File)
        btn3.grid(row=row,column =1, sticky = "E")

        row +=1
        # This part is for display text file.
        self.text1 = Text(self,background="green", foreground="black",height=5)
        self.text1.insert(INSERT,'Running...')
        self.text1.grid(row=row,column=0, rowspan=2, columnspan =2, sticky='EW' )
        # yscrollbar=Scrollbar(frame, orient=VERTICAL, command=text1.yview)
        checkbutton = Checkbutton(self, text='Save Log File', variable=var)
        checkbutton.grid(columnspan=2, sticky=W)

    def menubar_1(self, root):
        menubar = Menu(root)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="New")
        filemenu.add_command(label="Open", command=self.Open_File)
        filemenu.add_command(label="Save", command=self.Save_File)

        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        return menubar

    def Open_File(self):
        self.filename = tkFileDialog.askopenfilename(initialdir="/", title="Select file", filetypes=(
            ("db files", "*.db"), ("jpeg files", "*.jpg"), ("all files", "*.*")))
        self.text1.configure(state='normal')
        self.text1.delete('1.0',END)
        self.text1.insert(1.0,self.filename)
        self.text1.configure(state='disabled')
        f = open(self.filename)
        print f
        self.text_load.delete('1.0', END)
        self.text_load.insert(1.0, f.read())

    def Save_File(self):
        f = tkFileDialog.asksaveasfile(mode='w', defaultextension=".mln")
        if f is None:
            return
        self.text1.configure(state='normal')
        self.text1.delete('1.0',END)
        self.text1.insert(1.0,f.name)
        self.text1.configure(state='disabled')
        text2save = str(self.text_load.get(1.0, END))  # starts from `1.0`, not `0.0`
        f.write(text2save)
        f.close()




        # print(self)

class PageTwo(tk.Frame):
    def __init__(self,parent, controller):

        tk.Frame.__init__(self,parent)

        self.grid(row=0, column=2, sticky='NEWS')
        helv36 = tkFont.Font(family='Helvetica', size=20, weight=tkFont.BOLD)
        var = IntVar()

        row = 0
        lab1 = Label(self, text="MLN Evidence Editor", font=helv36)
        lab1.grid(row=row, column=0, columnspan=2, sticky='N')

        row +=1
        lab2=Label(self,text='Decision Rule:')
        lab2.grid(row=row, column=0,sticky=W)
        row +=1
        self.text_load= Text(self)
        self.text_load.insert(INSERT,'DATA description...')
        self.text_load.grid(row=row,column=0, rowspan=1,columnspan=2,sticky="W")


        row +=1
        btn2=Button(self,text="Main Menu",command=lambda: controller.show_frame(StartPage))
        btn2.grid(row=row,sticky=W)
        btn3=Button(self, text="Save",command=self.Save_File)
        btn3.grid(row=row,column =1, sticky = "E")

        row +=1
        # This part is for display text file.
        self.text1 = Text(self,background="green", foreground="black",height=5)
        self.text1.insert(INSERT,'Running...')
        self.text1.grid(row=row,column=0, rowspan=2, columnspan =2, sticky='EW' )
        # yscrollbar=Scrollbar(frame, orient=VERTICAL, command=text1.yview)
        checkbutton = Checkbutton(self, text='Save Log File', variable=var)
        checkbutton.grid(columnspan=2, sticky=W)

    def menubar_1(self, root):
        menubar = Menu(root)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="New")
        filemenu.add_command(label="Open", command=self.Open_File)
        filemenu.add_command(label="Save", command=self.Save_File)

        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        return menubar

    def Open_File(self):
        self.filename = tkFileDialog.askopenfilename(initialdir="/", title="Select file", filetypes=(
            ("db files", "*.db"), ("jpeg files", "*.jpg"), ("all files", "*.*")))
        self.text1.configure(state='normal')
        self.text1.delete('1.0',END)
        self.text1.insert(1.0,self.filename)
        self.text1.configure(state='disabled')
        f = open(self.filename)
        print f
        self.text_load.delete('1.0', END)
        self.text_load.insert(1.0, f.read())

    def Save_File(self):
        f = tkFileDialog.asksaveasfile(mode='w', defaultextension=".mln")
        if f is None:
            return
        self.text1.configure(state='normal')
        self.text1.delete('1.0',END)
        self.text1.insert(1.0,f.name)
        self.text1.configure(state='disabled')
        text2save = str(self.text_load.get(1.0, END))  # starts from `1.0`, not `0.0`
        f.write(text2save)
        f.close()


app = App()

app.mainloop()



