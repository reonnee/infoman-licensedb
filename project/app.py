import os
from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
import string
import random
from datetime import date

app = Flask(__name__)
app.secret_key = "license_portal_secret_key"

# tidb
license = mysql.connector.connect(
    host=os.environ.get("DB_HOST"),
    port=int(os.environ.get("DB_PORT")),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
    database=os.environ.get("DB_NAME"),
    ssl_verify_cert=True
)
cursor = license.cursor(dictionary=True, buffered=True)

FIELDS = [
  {
    "section": "Applicant Information",
    "fields": [
      ("applicant_id", "varchar(30)"),
      ("Full Name", "varchar(80)"),
      ("Address", "varchar(100)"),
      ("Nationality", "varchar(15)"),
      ("Sex", "char(1)"),
      ("Contact Number", "varchar(15)"),
      ("Birthdate", "date"),
      ("Birthplace", "varchar(20)"),
      ("TIN", "varchar(11)"),
      ("Civil Status", "char(9)"),
      ("Father's Name", "varchar(80)"),
      ("Mother's Name", "varchar(80)"),
      ("Spouse's Name", "varchar(80)"),
      ("License Number", "varchar(14)"),
      ("Highest Educational Attainment (HEA)", "int"),
      ("Height", "decimal(10,0)"),
      ("Weight", "decimal(10,0)"),
      ("Blood Type", "varchar(3)"),
      ("Organ Donor", "tinyint"),
      ("Eye Color", "varchar(15)"),
      ("Agency Code", "varchar(5)"),
      ("License Classification Applied For (LCA)", "int"),
      ("Condition", "int"),
      ("dsa_code", "varchar(10)"),
      ("employer_id", "varchar(10)"),
      ("emergency_id", "varchar(10)")
    ]
  },
  {
    "section": "Application Details",
    "fields": [
      ("application_id", "varchar(30)"),
      ("applicant_id", "varchar(30)"),
      ("Type of Application (TOA)", "varchar(7)"),
     # ("Issue Date", "date"),
     # ("Expiry Date", "date")
    ]
  },
  {
    "section": "Work Details",
    "fields": [
      ("employer_id", "varchar(10)"),
      ("Employer/Business Name", "varchar(80)"),
      ("Employer/Business Contact", "varchar(15)"),
      ("Employer/Business Address", "varchar(100)")
    ]
  },
  {
    "section": "Emergency Information",
    "fields": [
      ("emergency_id", "varchar(10)"),
      ("Emergency Contact Person", "varchar(80)"),
      ("Emergency Contact No.", "varchar(15)"),
      ("Emergency Contact Address", "varchar(100)"),
      ("applicant_id", "varchar(30)")
    ]
  },
  {
    "section": "Organ Information",
    "fields": [
      ("applicant_id", "varchar(30)"),
      ("Organ Details", "char(8)")
    ]
  },
  {
    "section": "DSA Details",
    "fields": [
      ("dsa_code", "varchar(10)"),
      ("Driving Skills Acquired From (DSA)", "varchar(80)")
    ]
  },
]

CATEGORIES = [
    ("A-L1", "Two wheels with a speed not exceeding 50 kph"),
    ("A-L2", "Three wheels with a speed not exceeding 50 kph"),
    ("A-L3", "Two wheels with a speed exceeding 50 kph"),
    ("A1-L4", "Motorcycle with side cars with a speed exceeding 50 kph"),
    ("A1-L5", "Three wheels symmetrically arranged with a speed exceeding 50 kph"),
    ("A1-L6", "Four wheels whose mass is less than 350kg with a speed not exceeding 45 kph"),
    ("A1-L7", "Four wheels whose mass is less than 550kg with a speed not exceeding 45 kph"),
    ("B-M1", "Vehicles used for the carriage of passengers, comprising not more than 8 seats with a GVW up to 5000kgs."),
    ("B1-M2", "Vehicles used for the carriage of passengers, comprising more than 8 seats with a GVW up to 5000kgs."),
    ("B2-N1", "Vehicles used for the carriage of goods and having a GVW up to 3500kgs."),
    ("C-N2", "Vehicles used for the carriage of goods and must have a minimum 3500kgs GVW but not exceeding 12000kgs"),
    ("C-N3", "Vehicles used for the carriage of goods and having a maximum GVW exceeding 12000kgs."),
    ("D-M3", "Vehicles used for the carriage of passengers, comprising more than 8 seats with having a maximum GVW exceeding 5000kgs."),
    ("BE-O1", "Trailers with a maximum GVW not exceeding 750kgs."),
    ("BE-O2", "Trailers with a minimum GVW exceeding 750kgs, but not exceeding 3500kgs."),
    ("CE-O3", "Trailers with a minimum GVW exceeding 3500kgs, but not exceeding 10000kgs."),
    ("CE-O4", "Trailers with a maximum GVW exceeding 10000kgs.")
]

def generate_id(table, column, prefix):
    cursor.execute(f"""
        SELECT {column}
        FROM {table}
        ORDER BY {column} DESC
        LIMIT 1
    """)
    result = cursor.fetchone()
    
    # result is a dictionary, e.g., {"applicant_id": "APL001"}
    if result and result[column]: 
        try:
            last_num = int(result[column][len(prefix):])
            return f"{prefix}{last_num + 1:03d}"
        except (ValueError, KeyError):
            pass
    return f"{prefix}001"

#generate a license number if LCA=1
def generate_lto_license_number():
    region_letter = random.choice(['N', 'E', 'D', 'C', 'R']) 
    region_digits = f"{random.randint(1, 16):02d}"
    region = f"{region_letter}{region_digits}"
    year = f"{date.today().year % 100:02d}"
    serial = ''.join(random.choices(string.digits, k=6))
    return f"{region}-{year}-{serial}"

# HOMEPAGE
@app.route('/')
def home():
    return render_template('dashboard.html')

@app.route('/apply')
def apply():
    return render_template('apply.html', sections=FIELDS, categories=CATEGORIES)


def clean_field(val, is_numeric=False):
    if val is None or str(val).strip() == "":
        return None
    return int(val) if is_numeric and str(val).isdigit() else val
# SUBMITTING THE FORM
  
@app.route('/submit', methods=['POST'])
def submit():
  
  # Generate random IDs for applicant, application, employer, and emergency contact
  application_id = generate_id("application", "application_id", "A")
  emergency_id = generate_id("emergency", "emergency_id", "#EMG")
  dsa_code = generate_id("dsa_details", "dsa_code", "DSA")
    
  #DATE
  issue_date = date.today()
  expiry_date = date(
    issue_date.year + 4,
    issue_date.month, 
    issue_date.day
  )
    
  # User input
  form_data = request.form.to_dict()

  #retrieve work details
  emp_name = form_data.get("Employer/Business Name")
  emp_contact = form_data.get("Employer/Business Contact")
  emp_address = form_data.get("Employer/Business Address")
  full_name = form_data.get("Full Name")
  father = form_data.get("Father's Name")
  mother = form_data.get("Mother's Name")
  selected_organs = request.form.getlist("Organ Details")

  #data cleaning
  weight = clean_field(form_data.get("Weight"), is_numeric=True)
  height = clean_field(form_data.get("Height"), is_numeric=True)
  condition = clean_field(form_data.get("Condition"), is_numeric=True)
  lca = clean_field(form_data.get("License Classification Applied For (LCA)"), is_numeric=True)
  organ_donor = 1 if form_data.get("Organ Donor") == "1" else 0


  try:
      
    #titingnan if existing na xia
    cursor.execute("""
        SELECT employer_id
        FROM work
        WHERE empBName = %s AND empBAddress = %s
    """, (emp_name, emp_address))

    existing_employer = cursor.fetchone()

    #reuse na lang if existing na
    if existing_employer:
        employer_id = existing_employer['employer_id']
    else:  # Insert data into the Employer table
         employer_id = generate_id("work", "employer_id", "#EMP")
         cursor.execute("""
          INSERT INTO work (
            employer_id,
            empBName,
            empBContact,
            empBAddress
          ) VALUES (%s, %s, %s, %s)
        """, 
          (
          employer_id, 
          form_data.get("Employer/Business Name"), 
          form_data.get("Employer/Business Contact"), 
          form_data.get("Employer/Business Address")
          )
        )
  #check if LCA = 1
    if lca == 1:
        license_num = generate_lto_license_number()
    else:
        license_num = form_data.get("License Number")
  # Insert data into the DSA table
    cursor.execute("""
      INSERT INTO dsa_details (
        dsa_code,
        dsa_details
      ) VALUES (%s, %s)
    """,
      (
        dsa_code,
        form_data.get("Driving Skills Acquired From (DSA)")
      )
    )

 # applicant table
    cursor.execute("""
        SELECT applicant_id 
        FROM applicant
        WHERE aplname = %s AND father_name = %s AND mother_name = %s
        LIMIT 1
    """, (full_name, father, mother))
      
    existing_applicant = cursor.fetchone()

    if existing_applicant:
        applicant_id = existing_applicant['applicant_id']
    else:
        applicant_id = generate_id("applicant", "applicant_id", "APL")
      # Insert data into the Applicant table
        cursor.execute("""
          INSERT INTO applicant (
            applicant_id,
            aplname, 
            aplAddress, 
            aplNationality, 
            aplSex, 
            aplContact,
            aplBirthdate,
            aplBirthplace,
            TIN,
            civil_status,
            father_name,
            mother_name,
            spouse_name,
            license_num,
            hea,
            aplHeight,
            aplWeight,
            aplBloodType,
            isOrganDonor,
            aplEyeColor,
            agency_code,
            LCA,
            medical_condition,
            dsa_code,
            employer_id
          ) VALUES (%s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s)
          """,
          (
          applicant_id,
          form_data.get("Full Name"), 
          form_data.get("Address"), 
          form_data.get("Nationality"), 
          form_data.get("Sex"),
          form_data.get("Contact Number"),
          form_data.get("Birthdate"),
          form_data.get("Birthplace"),
          form_data.get("TIN"),
          form_data.get("Civil Status"),
          form_data.get("Father's Name"),
          form_data.get("Mother's Name"),
          form_data.get("Spouse's Name"),
          license_num,
          form_data.get("Highest Educational Attainment (HEA)"),
          height,
          weight,
          form_data.get("Blood Type"),
          organ_donor,
          form_data.get("Eye Color"),
          form_data.get("Agency Code"),
          lca,
          condition,
          dsa_code,
          employer_id,
          )
        )  
  
  # Insert data into the Emergency table
    cursor.execute(""" 
      INSERT INTO emergency (
        emergency_id,
        emergencyName,
        emergencyContact,
        emergencyAddress,
        applicant_id
      ) VALUES (%s, %s, %s, %s, %s)
    """,
      (
      emergency_id, 
      form_data.get("Emergency Contact Person"), 
      form_data.get("Emergency Contact No."), 
      form_data.get("Emergency Contact Address"),
      applicant_id
      )
    )
    
  # Inset data into the Organ table
    for organ in selected_organs:
        
      cursor.execute("""
          INSERT INTO organ (
            applicant_id,
            organ_details
          ) VALUES (%s, %s)
          """,
          (
          applicant_id,
          organ
          )
        )
      
  # Insert data into the Application table
    cursor.execute("""
      INSERT INTO application (
        application_id,
        applicant_id,
        toa,
        issue_date,
        expiry_date
      ) VALUES (%s, %s, %s, %s, %s)
      """,
      (
      application_id, 
      applicant_id, 
      form_data.get("Type of Application (TOA)"), 
      issue_date, 
      expiry_date
      )
    )
      
    for code, description in CATEGORIES:

      status = request.form.get(f"status_{code}")
      sv = request.form.get(f"sv_{code}")
      license_category = request.form.get(f"category_{code}")
      clutch_type = request.form.get(f"clutch_{code}")

      if status or license_category or clutch_type:
        if not license_category or not clutch_type or not status:
          license.rollback()
          return f"Error: Please select, Status, License Category and Clutch Type for {code}.", 400
      
      # Insert data into the DLVC table
        cursor.execute("""
          INSERT INTO dl_details (
            application_id,
            dlvc_code,
            status,
            clutch_type,
            sv,
            license_category
          ) VALUES (%s, %s, %s, %s, %s, %s)          
          """,
          (
          application_id,
          code,
          status,
          clutch_type,
          1 if sv else 0,
          license_category
          )
        )
    
    license.commit()
    return redirect(url_for('success', application_id=application_id))

  except Exception as e:
    license.rollback()
    print(f"Error inserting data: {e}")
    return f"An error occurred while saving your application: {e}", 500
      
@app.route('/debug-view')
def debug_view():
    # Fetch all applicants
    cursor.execute("SELECT applicant_id, aplname, aplAddress FROM applicant")
    applicants = cursor.fetchall()
    
    # Format them cleanly as HTML
    html = "<h1>Database Records</h1>"
    html += "<table border='1'><tr><th>ID</th><th>Name</th><th>Address</th></tr>"
    for app_id, name, address in applicants:
        html += f"<tr><td>{app_id}</td><td>{name}</td><td>{address}</td></tr>"
    html += "</table>"
    return html

# function to get all data  
def retrieve_all(application_id=None):
    # Base Query
    query = """
        SELECT
            a.application_id, a.toa, a.issue_date, a.expiry_date,
            p.applicant_id, p.aplname, p.aplAddress, p.aplNationality, p.aplSex, p.aplContact,
            p.aplBirthdate, p.aplBirthplace, p.TIN, p.civil_status, p.father_name, p.mother_name,
            p.spouse_name, p.license_num, p.hea, p.aplHeight, p.aplWeight, p.aplBloodType,
            p.isOrganDonor, p.aplEyeColor, p.agency_code, p.LCA, p.medical_condition,
            w.employer_id, w.empBName, w.empBContact, w.empBAddress,
            e.emergency_id, e.emergencyName, e.emergencyContact, e.emergencyAddress,
            o.organ_details,
            d.dsa_code, d.dsa_details
        FROM application a
        LEFT JOIN applicant p ON a.applicant_id = p.applicant_id
        LEFT JOIN work w ON p.employer_id = w.employer_id
        LEFT JOIN emergency e ON p.applicant_id = e.applicant_id
        LEFT JOIN organ o ON p.applicant_id = o.applicant_id
        LEFT JOIN dsa_details d ON p.dsa_code = d.dsa_code
    """
    
    if application_id:
        query += " WHERE a.application_id = %s"
        cursor.execute(query, (application_id,))
        profile = cursor.fetchone() 
        
        if profile:
            cursor.execute("""
                SELECT dlvc_code, status, clutch_type, sv, license_category 
                FROM dl_details WHERE application_id = %s
            """, (application_id,))
            profile['matrix_details'] = cursor.fetchall()
        return profile
    else:
        query += " ORDER BY a.application_id DESC"
        cursor.execute(query)
        all_profile = cursor.fetchall() 
        
        for row in all_profile:
            cursor.execute("""
                SELECT dlvc_code, status, clutch_type, sv, license_category 
                FROM dl_details WHERE application_id = %s
            """, (row['application_id'],))
            row['matrix_details'] = cursor.fetchall()
        return all_profile
        
@app.route('/records')
def view_records():
    query = """
        SELECT 
            a.application_id,
            p.applicant_id,
            p.aplname AS full_name,
            a.toa AS type_of_app,
            p.license_num,
            a.expiry_date
        FROM application a
        JOIN applicant p ON a.applicant_id = p.applicant_id
        ORDER BY a.application_id DESC
    """
    cursor.execute(query)
    records = cursor.fetchall()
    return render_template('records.html', records=records)
  
@app.route('/success')
def success():
  app_id = request.args.get('application_id')
  profile_data = retrieve_all(application_id=app_id)
    
  if not profile_data:
    return "Profile data initialization structural failure.", 404
  return render_template('success.html', profile=profile_data)

@app.route('/summary/<app_id>')
def summary(app_id):
    profile_data = retrieve_all(application_id=app_id)
    
    if not profile_data:
        return "Profile data initialization structural failure.", 404
        
    return render_template('summary.html', profile=profile_data)

@app.route('/delete/<app_id>', methods=['POST'])
def delete_record(app_id):
    try:
        cursor.execute("SELECT applicant_id FROM application WHERE application_id = %s", (app_id,))
        record = cursor.fetchone()
        
        if record:
            tgt_applicant = record['applicant_id'] if isinstance(record, dict) else record[0]

            cursor.execute("SELECT COUNT(*) FROM application WHERE applicant_id = %s", (applicant_id,))
            count_result = cursor.fetchone()
            app_count = count_result['COUNT(*)'] if isinstance(count_result, dict) else count_result[0]

            if app_count == 1:
                # pag 1 application na lang yung associated sa kanya, saka na lang madedelete si applicant as a whole
                cursor.execute("DELETE FROM dl_details WHERE application_id = %s", (app_id,))
                cursor.execute("DELETE FROM application WHERE application_id = %s", (app_id,))
                cursor.execute("DELETE FROM emergency WHERE applicant_id = %s", (tgt_applicant,))
                cursor.execute("DELETE FROM organ WHERE applicant_id = %s", (tgt_applicant,))
                cursor.execute("DELETE FROM applicant WHERE applicant_id = %s", (tgt_applicant,))
                
                print("Both the application and the final applicant record were deleted.")
            else:
                cursor.execute("DELETE FROM application WHERE application_id = %s", (app_id,))
                cursor.execute("DELETE FROM dl_details WHERE application_id = %s", (app_id,))
                print(f"Application deleted. Applicant kept because they have {app_count - 1} other application(s).")
            
            license.commit()
            flash("Record deletion executed successfully.", "success")
            
        else:
            flash("Target Application Reference ID record profile was not found.", "danger")
    except Exception as e:
        license.rollback()
        flash(f"Deletion transaction aborted: {e}", "danger")
        
    return redirect(url_for('view_records'))
      
if __name__ == "__main__":
    # Render requires the app to listen on 0.0.0.0 and a dynamic port environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
      
      


