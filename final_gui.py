"""
Author: Mia Skinner

Heather Koo
Mia Skinner
CIS41B Final Project
final_gui.py:
- Creates a GUI window for the user to interact with the forecasting tool.
- Uses Shipments.db (built by shipmentsDB.py) for input.
- Stores user's "saved" forecasts to .csv, .bin, and Forecast.db files
"""
import sqlite3
import tkinter as tk
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from final_visualization import PlotOrder
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter.messagebox as tkmb
import tkinter.filedialog
import datetime
from dateutil.relativedelta import *
import os
import re
import pickle


OPTIONS = ["One Month Forecast",
           "One Quarter Forecast",
           "One Year Forecast"]


class MainWin(tk.Tk):
    """ The main program window. The user can choose to view past saved forecasts (by clicking on listbox entries)
     or create a new, custom forecast.
    """
    def __init__(self):
        """ Creates a main window including one event button linked to a dialog window to create a custom forecast.
            It loads any previously saved forecasts for the user to view by displaying in the listbox.
            It also creates sqlite connection and cursor objects to connect to the database.
        """
        super().__init__()
        self.title("Order Forecasting Tool")

        # Frame 1: top row button
        self.F1 = tk.Frame(self)
        self.F1.grid(row=0, padx=10, pady=(10,0), sticky='e')
        self.buttonText = tk.StringVar()
        tk.Button(self.F1, text="Create Custom Forecast", command=self._showCustomForecastChoice).grid(row=0)

        # Frame 2: listbox with scroll bar
        self.F2 = tk.Frame(self)
        self.F2.grid(row=3, padx=10, pady=(0,10))
        S = tk.Scrollbar(self.F2)
        self.LB = tk.Listbox(self.F2, height=15, width=50, yscrollcommand=S.set)
        self.LB.bind('<ButtonRelease-1>', self._showSavedForecastChoice)
        S.config(command=self.LB.yview)
        self.LB.grid()
        S.grid(row=0, column=1, sticky='ns')

        # Frame 3: Text
        self.F3 = tk.Frame(self)
        L1 = tk.Label(self.F3, text="View Previous Selection:")

        #spaced to match approximate entry lengths
        L2 = tk.Label(self.F3, text="Prod.   ForecastRun    Period            Expiration     Quantity   MAPE")
        self.F3.grid(row=1, sticky='w', padx=10)
        L1.grid(sticky='w')
        L2.grid()

        self._getData()

    def _getData(self):
        """
        creates sqlite connection and cursor objects to connect to the database.
        :return: None
        """
        self.conn = sqlite3.connect('Forecast.db')
        self.cur = self.conn.cursor()
        self.cur.execute('''SELECT productID, forecastRun, period, expirationDate, quantity, accuracy FROM Forecast WHERE expirationDate > ? ''', (datetime.date.today(),))
        for record in self.cur.fetchall():
            s = ""
            for item in record:
                if isinstance(item, float): item = round(item, 2)
                s = s + str(item) + "     "
            self.LB.insert(tk.END, s)

    def getConn(self):
        """
        sqlite connection getter
        :return: self.conn
        """
        return self.conn

    def _showSavedForecastChoice(self, clickObj):
        """
        callback function, which will bring up a dialog window to display a saved forecast plot
        :param clickObj: unused placeholder
        :return: none
        """
        if len(self.LB.curselection()):
            choice = self.LB.get(self.LB.curselection()[0])
            dialog = DialogWin2(self, lbChoice=choice)
            self.wait_window(dialog)

    def _showCustomForecastChoice(self):
        """
        callback function, which will bring up a dialog window
        to let the user choose custom forecast settings (start date and duration)
        :return: None
        """
        #self.LB.delete(0, tk.END)
        self.buttonText.set("Select a Duration")
        dialog = DialogWin(self, OPTIONS)
        self.wait_window(dialog)
        self.periodChoice = dialog.getChoice()



class DialogWin(tk.Toplevel):
    """ a dialog window which displays the 'Custom Forecast' options for the user to select duration and start date
    """
    def __init__(self, master, choiceList):
        """
        create a dialog window which is a top level window from the main window.
        :param master - a main window object.
        :param choiceList - an iterable that contains duration choice categories
        """
        super().__init__(master)
        self.title(master.buttonText.get())
        self._controlVar = tk.StringVar()
        self._controlVar.set(choiceList[0])
        self._inputDate = tk.StringVar()

        self.F1 = tk.Frame(self)
        L = tk.Label(self.F1, text="Start Date: ")
        self.F1.grid(row=0, pady=(10,0))
        L.grid(row=0, column=0)
        self.dateBox = tk.Entry(self.F1, width=10, textvariable=self._inputDate)
        self.dateBox.insert(tk.END, str(datetime.date.today()))
        self.dateBox.grid(row=0, column=1)

        for elem in choiceList:
            tk.Radiobutton(self, text=elem, variable=self._controlVar, value=elem).grid(sticky='w', padx=30, pady=10)

        tk.Button(self, text="View Forecast", command=self._showProductOrderForecast).grid(padx=10, pady=10)
        self.grab_set()
        self.focus_set()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.transient(master)


    def getChoice(self):
        """
        returns the user choice when one clicks the 'View Forecast' button.
        :return: a string of the user choice from the radio buttons.
        """
        return self._controlVar.get()

    def _showProductOrderForecast(self):
        """
        callback function, which will bring up a dialog window
        only allows user to move forward to the plot window if valid date is entered.
        :return: None
        """
        # only allows dates in 2000's
        date_validation = re.match(r"^(20)\d\d([- /.])(0[1-9]|1[012])\2(0[1-9]|[12][0-9]|3[01])", self._inputDate.get())
        if not date_validation:
            tkmb.showerror("Invalid Date Entered", "Please enter a valid date in the format: 20YY-MM-DD", parent=self)
            # does not allow you to continue to next part of program until valid date is entered
            return -1

        dialog = DialogWin2(self, self._controlVar.get())
        self.wait_window(dialog)


    def _close(self):
        """
        invalidates user's radio button choice and closes the current window.
        :return: None
        """
        self._controlVar.set("")
        self.destroy()



class DialogWin2(tk.Toplevel):
    """ a dialog window which displays the 'Product Order Forecast' Window
    """
    def __init__(self, master, durationChoice=None, lbChoice=None):
        """
        create a dialog window which is a top level window from the main window.
        :param master - a main window object.
        :param choiceList - an iterable that contains choice categories
        """
        super().__init__(master)

        self._controlVar = tk.StringVar()
        self.title("Product Order Forecast")
        self.visualObj = PlotOrder()

        # set up empty graph area
        self.fig = plt.figure(figsize=(7, 7))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().grid(row=1, columnspan=2)
        self.canvas.draw()
        self.conn = sqlite3.connect('Forecast.db')

        # supports both saved file custom forecast paths
        # coming from Custom Forecast window
        if durationChoice:
            self.durationChoice = durationChoice
            tk.Button(self, text="Select Product", width=12, command=self._showSelectProduct).grid(row=0, column=0, sticky='w', padx=10, pady=10)
            tk.Button(self, text="Save", width=8, command=self._save).grid(row=0, column=1, sticky='e', padx=10,
                                                                        pady=10)
            self.x = None
            self.y = None
            self.choice = None
            self.startDate = master._inputDate.get()

        # coming from Saved Forecast listbox
        if lbChoice:
            self.choice = lbChoice.split()
            self.x, self.y, self.productID, self.m, self.listX, self.listY, self.newlabel, self.newpos = pickle.load(open("{}_{}.bin".format(self.choice[0], self.choice[1]), "rb"))
            self.visualObj.savedForecastPlot(self.x, self.y, self.m, self.productID, self.listX, self.listY, self.newlabel, self.newpos)
            self.canvas.get_tk_widget().grid(row=1, columnspan=2)
            self.canvas.draw()

        self.grab_set()
        self.focus_set()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.transient(master)

    def getChoice(self):
        """
        returns the user choice when one clicks the ok button.
        :return: a string of the user choice on the radio buttons.
        """
        return self._controlVar.get()

    def _showSelectProduct(self):
        """
        callback function, which will bring up a dialog window
        to let the user choose a product to plot
        :return: None
        """
        productGen = self.visualObj.findAvaliableProducts()
        self.dialog = DialogWin3(self, sorted(productGen))
        self.wait_window(self.dialog)
        self._displayChart(self.choice)

    def _displayChart(self, var):
        """
        callback function that clears the current plot and displays the plot for the user's selected product
        :param var: the product selected to plot
        :return: none
        """
        self.fig.clear("all")
        # 0 = One Month Forecast
        # 1 = One Quarter Forecast
        # 2 = One Year Forecast
        for durIndex in range(len(OPTIONS)):
            if self.durationChoice == OPTIONS[durIndex]:
                self.x, self.y, self.m, self.listX, self.listY, self.newlabel, self.newpos = \
                    self.visualObj.forecastPlot(var, durIndex, int(self.startDate[0:4]), int(self.startDate[5:7]))

        self.canvas.get_tk_widget().grid(row=1, columnspan=2)
        self.canvas.draw()

    def writeToDB(self):
        """
        Writes current plot summary to Forecast.db database to save for main window listbox entries
        :return: none
        """
        self.cur = self.conn.cursor()
        self.cur.execute('''INSERT INTO Forecast
                           (productID, forecastRun, period, expirationDate, quantity, accuracy)
                            VALUES (?, ?, ?, ?, ?, ?)''', (self.choice,
                                                           str(datetime.date.today()),
                                                           self.durationChoice[:-9],
                                                           str(datetime.date.today() + relativedelta(months=+1)),
                                                           self.y[-1][0],
                                                           self.visualObj.getMae()*100))


    def _save(self):
        """
        Override 'X' button to:
         - save plot variables to pickle file to be able to view the plot again in a different session.
         - write plot summary entry to Forecast.db.
         - save the forecast plot for the product in view to a .csv file to a location of the user's choice.
        :return: None
        """
        if self.x is not None and self.y is not None:
            self.writeToDB()
            self.writeToPickle()

            if tkmb.askokcancel("Save", "Where would you like to save the forecast results for product {}?".format(self.choice), parent=self):
                directory = tk.filedialog.askdirectory(initialdir=".")
                if directory:
                    outputFilename = "forecast_{}_{}.csv".format(str(self.choice),datetime.date.today())
                    with open(os.path.join(directory, outputFilename), 'w') as fh:
                        fh.write("x,y\n") # header
                        for line in range(len(self.x)):
                            fh.write(str(*self.x[line]) + "," + str(*self.y[line]) + "\n")
                    tkmb.showinfo("Save", "File " + outputFilename + " will be saved in " + directory, parent=self)


    def writeToPickle(self):
        """
        Save plot variables to pickle file to be able to view the plot again in a different session.
        :return: none
        """
        l = [self.x, self.y, self.choice, self.m, self.listX, self.listY, self.newlabel, self.newpos]
        pickle.dump(l, open("{}_{}.bin".format(self.choice, str(datetime.date.today())), "wb"))

    def _close(self):
        """
        invalidates user's radio button choice, commits the database entries, closes the DB connection, and closes the current window.
        :return: None
        """
        self._controlVar.set("")
        self.conn.commit()
        self.conn.close()
        self.destroy()


class DialogWin3(tk.Toplevel):
    """ a dialog window which lets the user choose a product from the 'Select Product' window.
    """
    def __init__(self, master, productList):
        """
        create a dialog window which is a top level window from the main window.
        :param master - a main window object.
        :param choiceList - an iterable that contains choice categories
        """
        super().__init__(master)
        self._master = master
        self.title("Select Product")
        self._controlVar = tk.StringVar()
        self._controlVar.set(productList[0])

        # scroll bar for listbox
        self.F1 = tk.Frame(self)
        S = tk.Scrollbar(self.F1)

        # Search bar with listbox filter
        # search bar reference: http://code.activestate.com/recipes/578860-setting-up-a-listbox-filter-in-tkinterpython-27/
        self.productList = productList
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self.update_list())
        self.entry = tk.Entry(self, textvariable=self.search_var,width=13)

        # product listbox
        self.LB = tk.Listbox(self.F1, yscrollcommand=S.set)
        self.LB.insert(tk.END, *productList)

        S.config(command=self.LB.yview)
        self.entry.grid(row=0, column=0, padx=10, pady=3)
        self.LB.grid(row=1, column=0)
        self.F1.grid()
        S.grid(row=1, column=1, sticky='ns')

        self.F2 = tk.Frame(self)
        self.F2.grid(row=2)
        tk.Button(self.F2, text="OK", width=10, command=self._close).grid(padx=10, pady=10)

        self.update_list()

        self.grab_set()
        self.focus_set()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.transient(master)

    def update_list(self):
        """
        Updates product listbox with search box match results
        :return: none
        """
        search_term = self.search_var.get()

        # clear listbox
        self.LB.delete(0, tk.END)

        # fill listbox with matching search results
        for item in self.productList:
            if search_term.lower() in str(item).lower():
                self.LB.insert(tk.END, item)

    def getChoice(self):
        """
        returns the user choice when one clicks the ok button.
        :return: a string of the user choice on the radio buttons.
        """
        return self.LB.get(self.LB.curselection()[0])

    def _close(self):
        """
        invalidates user's radio button choice and closes the current window.
        :return: None
        """
        if len(self.LB.curselection()):
            self._master.choice = self.LB.get(self.LB.curselection()[0])
        self._controlVar.set("")
        self.destroy()


def main():
    """ create a main window and it runs until the X is clicked on the main window.
    """
    app = MainWin()
    app.mainloop()

main()