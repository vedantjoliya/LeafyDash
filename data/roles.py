ROLES = {
    1: {"id": 1, "title": "Junior Frontend Engineer", "department": "Engineering", "salary": 60000, "next_role": 2},
    2: {"id": 2, "title": "Mid Frontend Engineer", "department": "Engineering", "salary": 90000, "next_role": 3},
    3: {"id": 3, "title": "Senior Frontend Engineer", "department": "Engineering", "salary": 130000, "next_role": 22},
    
    4: {"id": 4, "title": "Junior Backend Engineer", "department": "Engineering", "salary": 65000, "next_role": 5},
    5: {"id": 5, "title": "Mid Backend Engineer", "department": "Engineering", "salary": 95000, "next_role": 6},
    6: {"id": 6, "title": "Senior Backend Engineer", "department": "Engineering", "salary": 140000, "next_role": 22},
    
    7: {"id": 7, "title": "Junior QA Engineer", "department": "Engineering", "salary": 55000, "next_role": 8},
    8: {"id": 8, "title": "Mid QA Engineer", "department": "Engineering", "salary": 80000, "next_role": 9},
    9: {"id": 9, "title": "Senior QA Engineer", "department": "Engineering", "salary": 110000, "next_role": 22},
    
    10: {"id": 10, "title": "Junior DevOps Engineer", "department": "Infrastructure", "salary": 70000, "next_role": 11},
    11: {"id": 11, "title": "Mid DevOps Engineer", "department": "Infrastructure", "salary": 100000, "next_role": 12},
    12: {"id": 12, "title": "Senior DevOps Engineer", "department": "Infrastructure", "salary": 150000, "next_role": 22},
    
    13: {"id": 13, "title": "Junior Data Scientist", "department": "Data", "salary": 75000, "next_role": 14},
    14: {"id": 14, "title": "Mid Data Scientist", "department": "Data", "salary": 110000, "next_role": 15},
    15: {"id": 15, "title": "Senior Data Scientist", "department": "Data", "salary": 160000, "next_role": 22},
    
    16: {"id": 16, "title": "Junior Product Manager", "department": "Product", "salary": 70000, "next_role": 17},
    17: {"id": 17, "title": "Mid Product Manager", "department": "Product", "salary": 105000, "next_role": 18},
    18: {"id": 18, "title": "Senior Product Manager", "department": "Product", "salary": 145000, "next_role": 23},
    
    19: {"id": 19, "title": "Junior Designer", "department": "Design", "salary": 60000, "next_role": 20},
    20: {"id": 20, "title": "Mid Designer", "department": "Design", "salary": 90000, "next_role": 21},
    21: {"id": 21, "title": "Senior Designer", "department": "Design", "salary": 125000, "next_role": 23},
    
    22: {"id": 22, "title": "Chief Technology Officer (CTO)", "department": "Leadership", "salary": 250000, "next_role": 24},
    23: {"id": 23, "title": "Chief Product Officer (CPO)", "department": "Leadership", "salary": 240000, "next_role": 24},
    24: {"id": 24, "title": "Chief Executive Officer (CEO)", "department": "Leadership", "salary": 400000, "next_role": None},
}

def get_role(role_id):
    return ROLES.get(int(role_id))

def get_all_roles():
    return list(ROLES.values())

def get_starting_roles():
    
    return [r for r in ROLES.values() if "Junior" in r['title']]
