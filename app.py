from flask import Flask, request, render_template, flash, get_flashed_messages, redirect, url_for, jsonify
from tables import Call_log, Create_Problem_Form, Specialist_Assigned, Solution
import pymysql

connection = pymysql.connect(host='localhost',
                             user='root',
                             password='suprim00',
                             database='it_helpdesk'
                             )

app = Flask(__name__)

app.config['SECRET_KEY'] = "super secret key"

@app.route('/')
def index(): 
    return render_template('index.html')  # Create an HTML template for the user interface


#a route to log calls in
@app.route('/log_calls', methods=["GET", "POST"])
def log_calls():
    form = Call_log()
    if form.validate_on_submit():
        cur = connection.cursor()   # Create a connection to mysql
        # receives data from form
        operator = form.operator.data
        caller = form.caller.data

        #checks if the names matches the name in the database
        cur.execute("SELECT full_name FROM personnel WHERE full_name LIKE %s OR full_name LIKE %s", 
                    (operator, caller))
        rows = cur.fetchall()
        if len(rows) != 2:
            flash("The names of operator or caller doesnot match", "danger")
            return redirect(url_for("log_calls"))
        
        call_time = form.call_time.data
        serial_number = form.serial_number.data

        cur.execute("SELECT serial_number FROM equipments WHERE serial_number LIKE %s",
                    (serial_number))
        rows = cur.fetchall()
        if len(rows) != 1:
            flash("This equipment isnot available in database","danger")
            return redirect(url_for("log_calls"))
        
        call_note = form.call_note.data
       
        #Inserts the data into database
        cur.execute(
            """INSERT INTO call_logs (operator, caller, call_time, serial_number, call_note) 
                    VALUES (%s, %s, %s, %s, %s)""",
                    (operator, caller, call_time, serial_number, call_note) 
                    )
        connection.commit()

        return redirect(url_for("create_problems"))
    return render_template('log_calls.html', form=form)

#a route to create problems
@app.route('/create_problems', methods=["GET", "POST"])
def create_problems():
    form = Create_Problem_Form()
    
    cur = connection.cursor()
    cur.execute("SELECT * FROM problem_type")
    rows = cur.fetchall()

    problem_types = []

    for row in rows:
        problem_types.append(row)

    #give the choices based on the data from the database.
    form.problem_type.choices = problem_types

    if request.method == "POST" and form.validate_on_submit():
        flash("Problem saved", "success")
        # receives data from form
        problem_title = form.problem_title.data
        description = form.description.data
        problem_type_id = form.problem_type.data
        caller = form.caller.data
        
        cur.execute(
            """INSERT INTO problem (problem_title, description, problem_type_id, caller_name) 
                    VALUES (%s, %s, %s, %s)""",
                    (problem_title, description, problem_type_id, caller) 
                    )
        # Get the value of the inserted primary key
        last_inserted_id = cur.lastrowid
        connection.commit()

        return redirect(url_for("assign_specialist", problem_type_id=problem_type_id, problem_id=last_inserted_id))
    return render_template('create_problem.html', form=form)

@app.route('/assign_specialist/<int:problem_type_id>/<int:problem_id>', methods=['GET', 'POST'])
def assign_specialist(problem_type_id,problem_id):
    form = Specialist_Assigned()

    cur = connection.cursor()
    cur.execute("SELECT * FROM problem WHERE problem_id = %s", (problem_id))
    problem = cur.fetchall
    if problem:
        cur.execute("""SELECT S_ID, name
                    FROM specialist
                    JOIN specialist_problem ON specialist.S_ID = specialist_problem.specialist_id
                    JOIN problem_type ON specialist_problem.problemtype_id = problem_type.P_ID
                    WHERE problem_type.P_ID = %s;""", (problem_type_id,))

        rows = cur.fetchall()
        specialists = []
        for row in rows:
            specialists.append(row)
        
        form.specialist.choices = specialists
        
        if request.method == "POST" and form.validate_on_submit():
            flash("Specialist assigned", "success")
            # receives data from form
            assigned_to = form.specialist.data
            print(assigned_to)
            assigned_time = form.assigned_time.data
            
            cur.execute(
                """UPDATE problem
                    SET assigned_to = %s, assigned_time =%s 
                    WHERE problem_id = %s;""",
                        (assigned_to, assigned_time, problem_id)
                        )
            #change state to currently working
            cur.execute(
                """UPDATE specialist
                    SET currently_working = true
                    WHERE S_ID = %s;""",
                        (assigned_to)
            )
            connection.commit()

            return redirect(url_for("resolve_problem",problem_id=problem_id, assigned_to=assigned_to))
        return render_template('assign_specialist.html', form=form)
    else:
        return "Problem not found"

@app.route('/resolve_problem/<int:problem_id>/<int:assigned_to>', methods=['GET','POST'])
def resolve_problem(problem_id,assigned_to):
    form = Solution()
    cur = connection.cursor()

    if request.method == "POST" and form.validate_on_submit():
        flash("Solution saved", "success")
        is_solved = form.is_solved.data
        solution = form.solution.data
        finished_time = form.finished_time.data

        cur.execute(
            """UPDATE problem
                SET is_solved = %s, solution = %s, finished_time =%s 
                WHERE problem_id = %s;""",
                    (is_solved, solution, finished_time, problem_id)
                    )
        cur.execute(
            """UPDATE specialist
                SET currently_working = 0
                WHERE S_ID = %s;""",
                    (assigned_to)
        )
        connection.commit()
        redirect(url_for("home"))    
    else:
        return render_template("resolve_problem.html",form=form)

#a route that shows list of problems
@app.route('/problem_list')
def problem_list():
    cur = connection.cursor()
    cur.execute("""SELECT problem.problem_id,problem.problem_title, problem_type.problem_type_name,specialist.name 
                FROM it_helpdesk.problem
                JOIN problem_type ON problem.problem_type_id = problem_type.P_ID
                JOIN specialist ON problem.assigned_to= specialist.S_ID;""")
    rows = cur.fetchall()
    #creates an empty list to store problem type lists
    problems = []
    for row in rows:
        problemObj = {}
        problemObj['problem_id'] = row[0]
        problemObj['problem_title'] = row[1]
        problemObj['problem_type_name'] = row[2]
        problemObj['specialist'] = row[3]
        problems.append(problemObj)
    print(problems)
    return render_template("problem_list.html", problems=problems)

@app.route('/view_problem/<int:problem_id>')
def view_problem(problem_id):
    cur = connection.cursor()
    cur.execute("""SELECT problem.problem_id,problem.problem_title,problem.description,
                problem_type.P_ID, problem_type.problem_type_name,specialist.name, problem.is_solved, problem.solution, problem.caller_name
                FROM it_helpdesk.problem
                JOIN problem_type ON problem.problem_type_id = problem_type.P_ID
                JOIN specialist ON problem.assigned_to= specialist.S_ID
                WHERE problem.problem_id = %s;""", (problem_id))
    rows = cur.fetchall()
    problems = []
    for row in rows:
        problemObj = {}
        problemObj['problem_id'] = row[0]
        problemObj['problem_title'] = row[1]
        problemObj['description'] = row[2]
        problemObj['P_ID'] = row[3]
        problemObj['problem_type'] = row[4]
        problemObj['specialist'] = row[5]
        problemObj['is_solved'] = row[6]
        problemObj['solution'] = row[7]
        problemObj['caller_name'] = row[8]
        problems.append(problemObj)
    if problems:    
        return render_template('problem.html', problems=problems)
    else:
        return "Problem not found!"

#a route that shows the problem types
@app.route('/problem_type')
def problem_type():
    cur = connection.cursor()
    cur.execute("SELECT problem_type_name FROM problem_type")
    rows = cur.fetchall()
    #creates an empty list to store problem type lists
    problem_types = []
    for row in rows:
        problem_types.append(row[0])
    return render_template("problem_type.html", problem_types=problem_types)

#a route that shows equipments
@app.route('/equipments')
def equipments():
    cur = connection.cursor()
    cur.execute("""SELECT equipments.serial_number,equipments.equipment_type, software.software_name,department.department_name 
                FROM it_helpdesk.equipments
                JOIN software ON equipments.S_ID = software.S_ID
                JOIN department ON equipments.department_id= department.D_ID;""")
    rows = cur.fetchall()
    #creates an empty list to store equipment lists
    equipments = []
    for row in rows:
        equipmentObj = {}
        equipmentObj['serial_number'] = row[0]
        equipmentObj['equipment_type'] = row[1]
        equipmentObj['software_name'] = row[2]
        equipmentObj['department_name'] = row[3]
        equipments.append(equipmentObj)
    return render_template("equipments.html", equipments=equipments)

#route to show personnel details
@app.route('/personnels')
def personnels():
    cur = connection.cursor()
    cur.execute("""SELECT personnel.ID,personnel.full_name, personnel.address, 
                personnel.phone, personnel.job_title, department.department_name 
                FROM it_helpdesk.personnel
                JOIN department ON personnel.department_id= department.D_ID;""")
    rows = cur.fetchall()
    #creates an empty list to store equipment lists
    personnels = []
    for row in rows:
        personnelObj = {}
        personnelObj['ID'] = row[0]
        personnelObj['full_name'] = row[1]
        personnelObj['address'] = row[2]
        personnelObj['phone'] = row[3]
        personnelObj['job_title'] = row[4]
        personnelObj['department_name'] = row[5]
        personnels.append(personnelObj)
    return render_template("personnels.html", personnels=personnels)

if __name__ == '__main__':
    # session cookies for protection against cookie data tampering.
    app.secret_key = 'super secret key'
    # It will store in the hard drive
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config ['DEBUG'] = True 
    app.run(debug=True)
