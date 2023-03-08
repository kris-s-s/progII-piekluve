import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sqlite3
from datetime import datetime
import re


# return a money string from cent integer
def format_from_cents(cents):
    if not cents:
        return '0.00'
    euros = cents // 100
    cents = cents % 100
    return f'{euros:,}.{cents:02d}'


# return cents from money string
def convert_to_cents(money_str):
    if not money_str.replace(",", ".").replace(".", "", 1).isdigit():
        return None
    money_str = money_str.replace(",", ".")
    euro, cents = money_str.split(".")
    euro = int(euro)
    cents = int(cents)
    total_cents = euro * 100 + cents
    return total_cents


# checks if the string is in format like 232.00
def validate_decimal(input_str):
    pattern = r'^\d+(\.|,)\d{2}$'
    return bool(re.match(pattern, input_str))


class financeTracker(tk.Frame):
    view_mode = 'expenses'
    database = 'f.db'
    selected_record = None

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        # create the database tables, if they don't already exist
        self.create_tables()

        self.parent = parent
        self.parent.resizable(False, False)
        self.parent.title('Finanšu sekotājs')

        # create an ui element for holding the records
        self.tree = ttk.Treeview(parent, columns=('id', 'name', 'money', 'date'), show='headings')
        self.tree.heading('id', text='ID')
        self.tree.heading('name', text='Nosaukums')
        self.tree.heading('money', text='Nauda')
        self.tree.heading('date', text='Datums')
        # add scrolling to the element
        self.tree_scroll = ttk.Scrollbar(parent, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scroll.set)
        # listen for clicking on the records to select them
        self.tree.bind("<ButtonRelease-1>", self.select_record)

        # create a field for entering a name for the record
        self.name_label = ttk.Label(parent, text='Nosaukums:')
        self.name_entry = ttk.Entry(parent)
        # create a field for entering a money amount for the record
        self.money_label = ttk.Label(parent, text='Nauda:')
        self.money_entry = ttk.Entry(parent, validate="focusout")
        self.money_entry.bind("<FocusOut>", self.on_validate_money_entry)

        # add buttons for various functionality
        self.record_submit = tk.Button(parent, text='Saglabāt', background='#94fc8d', command=self.add_record)
        self.record_delete = tk.Button(parent, text='Izdzēst izvēlēto', background='#fc928d',
                                       command=self.delete_record)
        self.mode_to_earnings_switch = tk.Button(parent, text='Rādīt ienākumus', background='#f8fc8d',
                                                 command=self.switch_view_state)
        self.mode_to_expenses_switch = tk.Button(parent, text='Rādīt izdevumus', background='#919d9e',
                                                 state=tk.DISABLED,
                                                 command=self.switch_view_state)
        # add a label for the total amount of money in the table
        self.money_total = ttk.Label(parent)

        # put all the elements in a grid
        self.tree.grid(row=0, column=0, columnspan=5, sticky='nwse')
        self.tree_scroll.grid(row=0, column=5, sticky='nwse')

        self.name_label.grid(row=1, column=1, sticky='nwse')
        self.name_entry.grid(row=1, column=2, sticky='nwse')

        self.money_label.grid(row=2, column=1, sticky='nwse')
        self.money_entry.grid(row=2, column=2, sticky='nwse')
        self.money_entry.insert(0, '1.23')  # to show an example to the user

        self.mode_to_expenses_switch.grid(row=1, column=0, sticky='nswe')
        self.mode_to_earnings_switch.grid(row=2, column=0, sticky='nswe')
        self.money_total.grid(row=3, column=0, sticky='w')

        self.record_submit.grid(row=3, column=1, columnspan=2, sticky='nwse')
        self.record_delete.grid(row=1, column=4, columnspan=2, sticky='nwse')

        # display any existing records
        self.refresh_view()

    # go from viewing or adding to the expenses table to earnings or vice versa
    def switch_view_state(self):
        self.selected_record = None
        if self.view_mode == 'expenses':
            self.view_mode = 'earnings'

            self.mode_to_expenses_switch['state'] = 'normal'
            self.mode_to_earnings_switch['state'] = 'disabled'

            self.mode_to_expenses_switch['background'] = '#f8fc8d'
            self.mode_to_earnings_switch['background'] = '#676d75'

        elif self.view_mode == 'earnings':
            self.view_mode = 'expenses'
            self.mode_to_expenses_switch['state'] = 'disabled'
            self.mode_to_earnings_switch['state'] = 'normal'

            self.mode_to_expenses_switch['background'] = '#676d75'
            self.mode_to_earnings_switch['background'] = '#f8fc8d'

        # display the change
        self.refresh_view()

    # sets the last selected record entry
    def select_record(self, a):
        focused_item = self.tree.focus()
        try:
            self.selected_record = self.tree.item(focused_item)['values'][0]
        except IndexError:
            print(self.tree.item(focused_item))

    # deletes a record that was selected
    def delete_record(self):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()

        cursor.execute(f'DELETE FROM {self.view_mode} WHERE id = {self.selected_record}')

        conn.commit()
        conn.close()

        self.refresh_view()

    # adds a record from the information in input fields
    def add_record(self):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()

        name = self.name_entry.get()
        money = convert_to_cents(self.money_entry.get())
        date = datetime.today().strftime('%Y-%m-%d')
        query = f'INSERT INTO {self.view_mode} (name, money, date) VALUES (?, ?, ?)'

        cursor.execute(query, (name, money, date))

        conn.commit()
        conn.close()

        self.refresh_view()

    # makes sure the latest information is shown
    def refresh_view(self):

        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        # get the relevant records
        cursor.execute(f'SELECT * FROM {self.view_mode}')
        rows = cursor.fetchall()
        # calculate their sum
        cursor.execute(f'SELECT SUM(money) FROM {self.view_mode};')
        total = cursor.fetchone()[0]
        # display the total
        self.money_total['text'] = f'Kopā: {format_from_cents(total)}'
        # clear the tree element from old values, then fill with new
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            row_id, name, money, date = row
            self.tree.insert('', 'end', values=(row_id, name, format_from_cents(money), date))

        conn.commit()
        conn.close()

    # makes sure the database tables exist
    def create_tables(self):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS expenses
                     (id INTEGER PRIMARY KEY, name TEXT, money INTEGER, date TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS earnings
                     (id INTEGER PRIMARY KEY, name TEXT, money INTEGER, date TEXT)''')

        conn.commit()
        conn.close()

    # makes sure the user entered money correctly or displays error message
    def on_validate_money_entry(self, event=None):
        input_str = self.money_entry.get()
        if not validate_decimal(input_str):
            messagebox.showerror('Kļūda', 'Naudai jābūt ievadītai šādā formātā: "11.11" vai "11,11"')
            self.money_entry.delete(0, 'end')
            return False
        return True


# starts the program loop
if __name__ == "__main__":
    root = tk.Tk()
    financeTracker(root)
    root.mainloop()
