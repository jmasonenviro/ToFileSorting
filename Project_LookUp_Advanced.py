"""
This is a plan for the more advanced project look up.
It will be carried out with the information given by the QuickBase API call.

"""

# pip install anthropic
 

import json 

import datetime 

 

#CONFIG 

 

NAMING_CONFIDENCE_THRESHOLD = 0.9 #higher threshold in the beginning to prevent accidentally filing documnents 

REQUIRED_NAMING_FIELDS = ["vendor_name", "document_number", "paid"] 
 
PROJECTS_DATABASE = [{"number": "1042", "address": "12 Oak Street", "folder": "folder_id_1042"}, 

                     {"number": "1055", "address": "88 Harbor Rd", "folder": "folder_id_1055"}, 

                     {"number": "2000", "address": "5 First Ave", "folder": "folder_id_2000a"}, 

                     {"number": "2000", "address": "5 First Ave Unit B", "folder": "folder_id_2000b"}] 

def extract_fields(document): 

    # Read the document
    # pdf_bytes = download_document(document["id"])
    
    # Call Claude with the document
    # response = client.messages.create(
        # model="claude-3-5-sonnet-20241022",
        # max_tokens=1024,
        # messages=[
            # {
                # "role": "user",
                # "content": [
                    # {"type": "image", "source": {...}},
                    # {"type": "text", "text": "Extract: signature, vendor, amount, project number, date, address, invoice number..."}
                # ]
            # }
        # ]
    # )

    # Parse the response (Claude will return JSON)
    # fields = json.loads(response.content[0].text)
    # For now, returning stub with expected field structure (will switch to returning fields)
    return {
        "signature": None,
        "date": None,
        "address": None,
        "project_number": None,
        "vendor_name": None
    } 
    

 

# Hardcode Renova's address into the code for future reference. 

COMPANY_ADDRESSES = [ 

    "3417 Sunset Ave, Ocean, NJ" 

    "3417 Sunset Ave, Ocean, NJ 07712" 

    "3417 Sunset Avenue, Ocean, NJ" 

    "3417 Sunset Avenue, Ocean, NJ 07712" 

] 

 

def _normalize(s): 

    return "".join(c for c in s.lower() if c.isalnum() or c == " ").split() 

 

def _is_company_address(addr): 

    a = " ".join(_normalize(addr)) 

    for company in COMPANY_ADDRESSES: 

        c = " ".join(_normalize(company)) 

        if c in a or a in c:                    # loose match, not exact 

            return True   

    return False 

 

def clean_project_address(fields): 

    addr = fields.get("project_address") 

    if addr and _is_company_address(addr): 

        fields["project_address"] = None        # it was RENOVA's address, not a project's 

    return fields 

 

def query_projects_by_address(project_address): 

    # QUICKBASE API CALL WOULD GO HERE 

    # where = "{7.CT." + address + "}"  

    # field 7 = address, CT = contains 

    # return quickbase_query(where, select_fields)  

    # POST /records/query 

     

    a = project_address.lower() 

     

    return [p for p in PROJECTS_DATABASE  

            if a in p["address"].lower() or p["address"].lower() in a] 

             

def query_projects_by_number(project_number):  

    # QUICKBASE API CALL WOULD GO HERE   

    # where = "{6.EX.'" + project_number + "'}"        

    # field 6 = project number  

    # return quickbase_query(where, select_fields)      

    # POST /records/query   

     

    return [p for p in PROJECTS_DATABASE if p["number"] == project_number] 

def find_project_number(address=None, project_number=None):
    """
    Try to determine project number from available fields.
    Returns project_number if found, None otherwise.
    """
    # If it already has project number, return it
    if project_number:
        return project_number
    
    # If it has address, try to find project by address
    if address:
      projects = query_projects_by_address(address)
      if len(projects) == 1:
          return projects[0]["number"]   # Return the only match as project address
      elif len(projects) > 1:
          return None    # Multiple matches, needs review
      
    return None # Can't determine project number
    


def query_projects_by_sig_and_date (project_number):  

    # QUICKBASE API CALL WOULD GO HERE   

    # where = "{6.EX.'" + project_number + "'}"        

    # field 6 = project number  

    # return quickbase_query(where, select_fields)      

    # POST /records/query   

     

     [p for p in PROJECTS_DATABASE if p["number"] == project_number] 

def move_and_rename(document, new_name, target_folder): 

    # MICROSOFT GRAPH WOULD GO HERE 

    # PATCH .../drive/items/{id} with {"name": new_name, "parentReference": {"id": target_folder}} 

     

    print(f" FILE -> '{new_name}' into {target_folder}") 

     
def verify_employee_on_project(employee_name=None, project_number=None, document_date=None):
    """
    Verify if an employee worked on the project during the document date.
    All fields are optional.
    """
    confidence = 0
    # Case 1: All three fields present
    if employee_name and project_number and document_date:
        # Search for tasks/comments by this person on this project
        tasks = "a" # quickbase_search(employee_name=employee_name, project_id=project_number)
        
        # Check if any task/comment is on document date
        for task in tasks:
            task_date = datetime.datetime.strptime(task["date"], "%Y-%m-%d")
            doc_date = datetime.datetime.strptime(document_date, "%Y-%m-%d")
            
            # If task is on document date, it matches
            if task_date == doc_date:
                return True
        return False
    

# THE REAL DECISION LOGIC (identical to full version) 

 

def passes_naming_gate(fields): 

    # Gate A: were the fields the filename is based on read confidently enough? 

     

    conf = fields.get("field_confidence", {}) 

    for name in REQUIRED_NAMING_FIELDS: 

        if conf.get(name, 0) < NAMING_CONFIDENCE_THRESHOLD: 

            return False, f"low confidence on '{name}'" 

    return True, "" 

 

def find_project(fields): 

    # Gate B: try to tie this document to exactly one project. 

     

    # 1. Prefer an exact match on a printed project number 

    if fields.get("project_number"): 

        rows = query_projects_by_number(fields["project_number"]) 

        if len(rows) == 1: 

            return {"status": "one", "project":rows[0]} 

        if len(rows) > 1: 

            return {"status": "many", "reason": f"project #{fields['project_number']} matched {len(rows)} records"} 

    # 2. Otherwise try to match on the job-site address 

    if fields.get("project_address"): 

        rows = query_projects_by_address(fields["project_address"]) 

        if len(rows) == 1: 

            return {"status": "one", "project":rows[0]} 

        if len(rows) > 1: 

            return {"status": "many", "reason": f"address '{fields['project_address']}' matched {len(rows)} projects"} 

         

    return {"status": "none", "reason": "no project number or address match"} 

 


     

 