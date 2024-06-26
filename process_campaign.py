#!/usr/bin/env python3

# ----------------------------------------------------------------------------
# Basic parameters - change as needed 
# ----------------------------------------------------------------------------

#relative or absolute path to your mekhq directory including trailing /
mekhq_path = "../Programs/mekhq-0.49.19/"

#path to user data for getting portraits
user_data_path = "../Programs/megamek_data/"

#the name of your campaign file within the campaigns directory of your 
#mekhq directory
campaign_file = 'Ronin Cat Avengers31441111.cpnx.gz'

#change this to choose which personnel get loaded based on personnel types
#in mekhq
#https://github.com/MegaMek/mekhq/blob/master/MekHQ/src/mekhq/campaign/personnel/Person.java#L75
roles = ["MECHWARRIOR","LAM_PILOT","GROUND_VEHICLE_DRIVER",
         "NAVAL_VEHICLE_DRIVER","VTOL_PILOT","VEHICLE_GUNNER",
         "VEHICLE_CREW","AEROSPACE_PILOT","CONVENTIONAL_AIRCRAFT_PILOT",
         "PROTOMECH_PILOT","BATTLE_ARMOUR","SOLDIER","VESSEL_PILOT",
         "VESSEL_GUNNER","VESSEL_CREW","VESSEL_NAVIGATOR","MECH_TECH",
         "MECHANIC","AERO_TECH","BA_TECH","DOCTOR",
         "ADMINISTRATOR_COMMAND","ADMINISTRATOR_LOGISTICS",
         "ADMINISTRATOR_TRANSPORT","ADMINISTRATOR_HR"]

roles_dict = {
    "MECHWARRIOR" : "Mechwarrior",
    "LAM_PILOT" : "LAM Pilot",
    "GROUND_VEHICLE_DRIVER" : "Vehicle Driver",
    "NAVAL_VEHICLE_DRIVER" : "Naval Vessel Driver",
    "VTOL_PILOT" : "VTOL Pilot",
    "VEHICLE_GUNNER" : "Vehicle Gunner",
    "VEHICLE_CREW" : "Vehicle Crew",
    "AEROSPACE_PILOT" : "Aerospace Pilot",
    "CONVENTIONAL_AIRCRAFT_PILOT" : "Conventional Fighter Pilot",
    "PROTOMECH_PILOT" : "Protomech Pilot",
    "BATTLE_ARMOUR" : "Battle Armor Soldier",
    "SOLDIER" : "Soldier",
    "VESSEL_PILOT" : "Space Vessel Pilot",
    "VESSEL_GUNNER" : "Space Vessel Gunner",
    "VESSEL_CREW" : "Space Vessel Crew",
    "VESSEL_NAVIGATOR" : "Hyperspace Navigator",
    "MECH_TECH" : "Mech Tech",
    "MECHANIC" : "Mechanic",
    "AERO_TECH" : "Aero Tech",
    "BA_TECH" : "Battle Armor Tech",
    "ASTECH" : "Astech",
    "DOCTOR" : "Doctor",
    "MEDIC" : "Medic",
    "ADMINISTRATOR_COMMAND" : "Admin/Command",
    "ADMINISTRATOR_LOGISTICS" : "Admin/Logistical",
    "ADMINISTRATOR_TRANSPORT" : "Admin/Transport",
    "ADMINISTRATOR_HR" : "Admin/HR",
    "DEPENDENT" : "Dependent",
    "NONE" : "None"
}

#mission, scenario, and personnel status names
mission_status_dict = {
    "ACTIVE" : "Active",
    "SUCCESS" : "Success",
    "FAILED" : "Failed",
    "BREACHED" : "Breached"
}
scenario_status_dict = {
    "CURRENT" : "Current",
    "DECISIVE_VICTORY" : "Decisive Victory",
    "VICTORY" : "Victory",
    "MARGINAL_VICTORY" : "Marginal Victory",
    "PYRRHIC_VICTORY" : "Pyrrhic Victory",
    "DRAW" : "Draw",
    "MARGINAL_DEFEAT" : "Marginal Defeat",
    "DEFEAT" : "Defeat",
    "DECISIVE_DEFEAT" : "Decisive Defeat"
}
personnel_status_names = ['Active','Retired','Killed in Action','Missing in Action']
personnel_status_dict = {
    "ACTIVE" : "Active",
    "RETIRED" : "Retired",
    "KIA": "Killed in Action",
    "MIA": "Missing in Action"
}

#skill level names
skill_level_names = ["Ultra-Green","Green","Regular","Veteran","Elite"]

#beginning of portait paths, only change if default image changes
portrait_paths = {
    "default.gif": "default.gif"
}

#skill type dictionary
skill_dict = {
}

# ----------------------------------------------------------------------------
# imports
# ----------------------------------------------------------------------------

import xml.etree.ElementTree as ET
import re
import datetime
from dateutil import relativedelta
from html import unescape
import os
import glob
from shutil import copyfile
import gzip


# ----------------------------------------------------------------------------
# custom functions
# ----------------------------------------------------------------------------

#clean out punctuation and replace spaces with - for url links and slugs
def urlify(s):
    # strip leading and trailing whitespace
    s = s.strip()
    # Remove all non-word characters (everything except numbers and letters)
    s = re.sub(r"[^\w\s]", '', s)
    # Replace all runs of whitespace with a single dash
    s = re.sub(r"\s+", '-', s)
    #slugs have trouble with numbers as the first letter, so add 
    #a letter if this is the case
    if(s[0].isdigit()):
        s = "n" + s
    return s.lower()

#takes an xml element and returns either the text of element if it exists
#or an empty string otherwise
def get_xml_text(ele):
    if(ele is not None and ele.text is not None):
        return ele.text
    else:
        return ''

#take an xml element with a date in it and convert to date object
def get_xml_date(ele):
    if(ele is not None and ele.text is not None):
        date  = ele.text.split(" ")[0]
        return datetime.datetime.strptime(date, '%Y-%m-%d')
    else:
        return None

#read portrait pathway. Need to check for special cases
def get_portrait_path(ele):
    path = get_xml_text(ele)
    if(path == '-- General --'):
        return '';
    else:
        return path

#read portrait file. Need to check for special cases
def get_portrait_file(ele):
    file_name = get_xml_text(ele)
    if(file_name == 'None'):
        return '';
    else:
        return file_name

def replace_portrait_name(portrait_file, slug):
    suffix = portrait_file.split('.')[1]
    return slug + '.' + suffix

#they switched over from int to enum for status
#so need to consider both ways
def get_person_status(status):
    if(status.isdigit()):
        return personnel_status_names[int(status)]
    else:
        return personnel_status_dict[status]
    
def get_person_role(role):
    return roles_dict[role]

#loop through kills and count ones belonging to this uuid
def count_kills(uuid, kills):
  nkills = 0
  for kill in kills.findall('kill'):
    kill_id = kill.find('pilotId')
    if(kill_id is not None and kill_id.text is not None):
      if(uuid == kill_id.text):
       nkills = nkills + 1
  return nkills

# get the name of the unit assigned to person uuid
def get_unit_name(uuid, units):
    for unit in units.findall('unit'):
        if(unit.attrib['id'] == uuid):
            entity = unit.find('entity')
            if(entity is None):
                return ''
            else:
                return entity.attrib['chassis'] + ' ' + entity.attrib['model']
    return None
  
#loop through units and find the one assigned to a person by uuid
def find_unit(uuid, units):
    for unit in units.findall('unit'):
        for current_id in unit.findall('driverId'):
            if(current_id is not None and current_id.text is not None and current_id.text == uuid):
                return unit.attrib['id']
        for current_id in unit.findall('pilotId'):
            if(current_id is not None and current_id.text is not None and current_id.text == uuid):
                return unit.attrib['id']
        for current_id in unit.findall('gunnerId'):
            if(current_id is not None and current_id.text is not None and current_id.text == uuid):
                return unit.attrib['id']
        for current_id in unit.findall('vesselCrewId'):
            if(current_id is not None and current_id.text is not None and current_id.text == uuid):
                return unit.attrib['id']
    return None

#loop through all the forces identified in element list and output them to
#markdown files. At the end it calls itself to iteratively process the tree
def process_forces(forces_ele, parent_name, parent_slug):
    for force in forces_ele.findall('force'):
        short_force_name = force.find('name').text
        if(parent_name is not None):
            if(parent_name == ''):
                full_force_name = short_force_name
            else:
                full_force_name = parent_name + ', ' + short_force_name
            slug = urlify(full_force_name)
        else:
            #top level force so special things
            full_force_name = ''
            slug = urlify(short_force_name)
        force_desc = get_xml_text(force.find('desc'))
        f = open('campaign/_forces/' + slug + '.md', 'w')
        f.write('---\n')
        f.write('layout: force\n')
        f.write('title: ' + short_force_name + '\n')
        f.write('order: ' + force.attrib['id'] + '\n')
        f.write('slug: ' + slug + '\n')
        if(parent_name is not None):
            f.write('parent-name: ' + parent_name + '\n')
            f.write('parent-slug: ' + parent_slug + '\n')
        f.write('---\n\n')
        f.write(unescape(force_desc))
        f.close()
        subforces = force.find('subforces')
        if(subforces is not None):
            process_forces(subforces, full_force_name, slug)

#loop through forces and find the force that the unit uuid is a member of, 
#iteratively recursing through the subforces
def find_force(uuid, forces_ele, parent_name, parent_slug):
    for force in forces_ele.findall('force'):
        short_force_name = force.find('name').text
        if(parent_name is not None):
            if(parent_name == ''):
                full_force_name = short_force_name
            else:
                full_force_name = parent_name + ', ' + short_force_name
            slug = urlify(full_force_name)
        else:
            #top level force so special things
            full_force_name = ''
            slug = urlify(short_force_name)
        units = force.find('units')
        if(units is not None):
            for unit in units.findall('unit'):
                if(unit.attrib['id'] == uuid):
                    return full_force_name
        subforces = force.find('subforces')
        if(subforces is not None):
            found_name = find_force(uuid, subforces, full_force_name, slug)
            if(found_name is not None):
                return found_name
    return None

def find_rank(rank_level, rank_system, role):
    if(role in ["AEROSPACE_PILOT","CONVENTIONAL_AIRCRAFT_PILOT"]):
        rank = all_rank_lists[rank_system][1][rank_level]
    elif(role in ["GROUND_VEHICLE_DRIVER", "NAVAL_VEHICLE_DRIVER", "VTOL_PILOT", "VEHICLE_GUNNER","VEHICLE_CREW"]):
        rank = all_rank_lists[rank_system][2][rank_level]
    elif(role in [ "VESSEL_PILOT", "VESSEL_CREW", "VESSEL_GUNNER", "VESSEL_NAVIGATOR"]):
        rank = all_rank_lists[rank_system][3][rank_level]
    elif(role in ["BATTLE_ARMOUR","SOLDIER"]):
        rank = all_rank_lists[rank_system][4][rank_level]
    elif(role in ["MECH_TECH", "MECHANIC", "AERO_TECH", "BA_TECH", "ASTECH"]):
        rank = all_rank_lists[rank_system][5][rank_level]
    else:
        rank = all_rank_lists[rank_system][0][rank_level]
    rank = check_rank(rank, rank_level, all_rank_lists[rank_system])
    if(rank == '-' or rank == "None"):
        return None
    else:
        return rank
    
def check_rank(rank, rank_level, rank_list):
    if(rank == '--MW'):
        rank = rank_list[0][rank_level]
    elif(rank == '--ASF'):
        rank = rank_list[1][rank_level]
    elif(rank == '--VEE'):
        rank = rank_list[2][rank_level]
    elif(rank == '--NAVAL'):
        rank = rank_list[3][rank_level]
    elif(rank == '--INF'):
        rank = rank_list[4][rank_level]
    elif(rank == '--TECH'):
        rank = rank_list[5][rank_level]
    else:
        return rank
    return check_rank(rank, rank_level, rank_list)

def process_rank_system(rsystem):
    rank_mw    = []
    rank_asf   = []
    rank_vee   = []
    rank_naval = []
    rank_inf   = []
    rank_tech  = []    
    for rank in rsystem.findall("rank"):
        rank_names = get_xml_text(rank.find('rankNames')).split(",")
        rank_mw.append(rank_names[0])
        rank_asf.append(rank_names[1])
        rank_vee.append(rank_names[2])
        rank_naval.append(rank_names[3])
        rank_inf.append(rank_names[4])
        rank_tech.append(rank_names[5])
    return [rank_mw, rank_asf, rank_vee, rank_naval, rank_inf, rank_tech]

#custom class for skill type
class SkillType:
    def __init__(self, name, target, count_up, green, reg, vet, elite):
        self.name = name
        self.target = target
        self.count_up = count_up
        self.green = green
        self.reg = reg
        self.vet = vet
        self.elite = elite
    
    def get_target_desc(self, skill):
        if(self.count_up):
            value = self.target + skill.level + skill.bonus
            return '+' + str(value)
        else:
            value = self.target - (skill.level  + skill.bonus)
            return str(value) + '+'
    
    def get_skill_level(self, level):
        if(level >= self.elite):
            return 4
        elif(level >= self.vet):
            return 3
        elif(level >= self.reg):
            return 2
        elif(level >= self.green):
            return 1
        else:
            return 0
            
class Skill:
    def __init__(self, name, level, bonus):
        self.name = name
        self.level = level
        self.bonus = bonus

def get_skill_desc(sk1, sk2):
    if(sk1 is None):
        return None
    lvl = skill_dict[sk1.name].get_skill_level(sk1.level)
    tgt_desc = skill_dict[sk1.name].get_target_desc(sk1)
    if(sk2 is not None):
        lvl2 = skill_dict[sk2.name].get_skill_level(sk2.level)
        lvl = int((lvl+lvl2)/2)
        tgt_desc = tgt_desc + "/" + skill_dict[sk2.name].get_target_desc(sk2)
        tgt_desc = re.sub(r"\+", '', tgt_desc)
    return [skill_level_names[lvl], tgt_desc]
    
def get_skill_report(person):
    role = person.find('primaryRole').text
    skills = {}
    for skill in person.findall('skill'):
        sk_name = get_xml_text(skill.find('type'))
        sk_lvl = int(get_xml_text(skill.find('level')))
        sk_bns = int(get_xml_text(skill.find('bonus')))
        skills[sk_name] = Skill(sk_name, sk_lvl, sk_bns)
    sk1 = None
    sk2 = None
    if(role == "MECHWARRIOR"):
        if('Gunnery/Mech' in skills):
            sk1 = skills['Gunnery/Mech']
        if('Piloting/Mech' in skills):
            sk2 = skills['Piloting/Mech']
    elif(role == "AEROSPACE_PILOT"):
        if('Gunnery/Aerospace' in skills):
            sk1 = skills['Gunnery/Aerospace']
        if('Piloting/Aerospace' in skills):
            sk2 = skills['Piloting/Aerospace']
    elif(role == "GROUND_VEHICLE_DRIVER"):
        if('Piloting/Ground Vehicle' in skills):
            sk1 = skills['Piloting/Ground Vehicle']
    elif(role == "NAVAL_VEHICLE_DRIVER"):
        if('Piloting/Naval' in skills):
            sk1 = skills['Piloting/Naval']
    elif(role == "VTOL_PILOT"):
        if('Piloting/VTOL' in skills):
            sk1 = skills['Piloting/VTOL']
    elif(role == "VEHICLE_GUNNER"):
        if('Gunnery/Vehicle' in skills):
            sk1 = skills['Gunnery/Vehicle']
    elif(role == "BATTLE_ARMOUR"):
        if('Gunnery/Battlesuit' in skills):
            sk1 = skills['Gunnery/Battlesuit']
        if('Anti-Mech' in skills):
            sk2 = skills['Anti-Mech']
    elif(role == "SOLDIER"):
        if('Small Arms' in skills):
            sk1 = skills['Small Arms']
    elif(role == "PROTOMECH_PILOT"):
        if('Gunnery/Protomech' in skills):
            sk1 = skills['Gunnery/Protomech']
    elif(role == "CONVENTIONAL_AIRCRAFT_PILOT"):
        if('Gunnery/Aircraft' in skills):
            sk1 = skills['Gunnery/Aircraft']
        if('Piloting/Jet' in skills):
            sk2 = skills['Piloting/Jet']
    elif(role == "VESSEL_PILOT"):
        if('Piloting/Aircraft' in skills):
            sk1 = skills['Piloting/Spacecraft']
    elif(role == "VESSEL_CREW"):
        if('Tech/Vessel' in skills):
            sk1 = skills['Tech/Vessel']
    elif(role == "VESSEL_GUNNER"):
        if('Gunnery/Spacecraft' in skills):
            sk1 = skills['Gunnery/Spacecraft']
    elif(role == "VESSEL_NAVIGATOR"):
        if('Hyperspace Navigator' in skills):
            sk1 = skills['Hyperspace Navigation']
    elif(role == "MECH_TECH"):
        if('Tech/Mech' in skills):
            sk1 = skills['Tech/Mech']
    elif(role == "MECHANIC"):
        if('Tech/Mechanic' in skills):
            sk1 = skills['Tech/Mechanic']
    elif(role == "AERO_TECH"):
        if('Tech/Aero' in skills):
            sk1 = skills['Tech/Aero']
    elif(role == "BA_TECH"):
        if('Tech/BA' in skills):
            sk1 = skills['Tech/BA']
    elif(role == "ASTECH"):
        if('Astech' in skills):
            sk1 = skills['Astech']
    elif(role == "DOCTOR"):
        if('Doctor' in skills):
            sk1 = skills['Doctor']
    elif(role == "MEDIC"):
        if('Medtech' in skills):
            sk1 = skills['Medtech']
    elif(role == "ADMINISTRATOR_COMMAND" or role == "ADMINISTRATOR_LOGISTICS" or role == "ADMINISTRATOR_TRANSPORT" or role == "ADMINISTRATOR_HR"):
        if('Administration' in skills):
            sk1 = skills['Administration']
    return get_skill_desc(sk1, sk2)

# ----------------------------------------------------------------------------
# Remove old files to start fresh
# ----------------------------------------------------------------------------

files = glob.glob('campaign/_forces/*')
for f in files:
    os.remove(f)
    
files = glob.glob('campaign/_missions/*')
for f in files:
    os.remove(f)
    
files = glob.glob('campaign/_personnel/*')
for f in files:
    os.remove(f)
    
files = glob.glob('campaign/_scenarios/*')
for f in files:
    os.remove(f)
    
files = glob.glob('assets/images/portraits/*')
for f in files:
    os.remove(f)

# ----------------------------------------------------------------------------
# Load the file and top-level information
# ----------------------------------------------------------------------------

if campaign_file.endswith("gz"):
    gzipper = gzip.GzipFile(mekhq_path + 'campaigns/' + campaign_file)
    data = gzipper.read()
    campaign = ET.fromstring(data)
else:
    tree = ET.parse(mekhq_path + 'campaigns/' + campaign_file)
    campaign = tree.getroot()

#stuff we need 
campaign_info = campaign.find('info')
date = datetime.datetime.strptime(campaign_info.find('calendar').text, '%Y-%m-%d')
kills = campaign.find('kills')
skill_types = campaign.find('skillTypes')
personnel = campaign.find('personnel')
missions = campaign.find('missions')
forces = campaign.find('forces')
units = campaign.find('units')

# ----------------------------------------------------------------------------
# Process default and custom rank structure and skill types for later use
# ----------------------------------------------------------------------------

rank_tree = ET.parse(mekhq_path + 'data/universe/ranks.xml')
rank_systems = rank_tree.getroot()
all_rank_lists = {}
for rank_system in rank_systems.findall('rankSystem'):
    code = get_xml_text(rank_system.find('code'))   
    all_rank_lists[code] = process_rank_system(rank_system)

#now check for a custom rank system to append
rank_system = campaign_info.find('rankSystem')
all_rank_lists['CUSTOM'] = process_rank_system(rank_system)
if(get_xml_text(rank_system.find("system")) == ''):
    rank_system_default = 'CUSTOM'
else:
    rank_system_default = get_xml_text(rank_system.find("system"))



#process skill types
for skill_type in skill_types.findall("skillType"):
    skill_name = get_xml_text(skill_type.find('name'))
    skill_target = int(get_xml_text(skill_type.find('target')))
    skill_count_up = get_xml_text(skill_type.find('countUp')) == 'true'
    skill_green = int(get_xml_text(skill_type.find('greenLvl')))
    skill_reg = int(get_xml_text(skill_type.find('regLvl')))
    skill_vet = int(get_xml_text(skill_type.find('vetLvl')))
    skill_elite = int(get_xml_text(skill_type.find('eliteLvl')))
    skill_dict[skill_name] = SkillType(skill_name, skill_target, skill_count_up, skill_green, skill_reg, skill_vet, skill_elite)

# ----------------------------------------------------------------------------
# Process the xml and output results to campaign directory
# ----------------------------------------------------------------------------

# process forces
process_forces(forces, None, None)

#loop through personnel and print out markdown file for each one
for person in personnel.findall('person'):
    uuid  = person.find('id').text
    primary_role = person.find('primaryRole').text
    role_name = get_person_role(primary_role)
    first = get_xml_text(person.find('givenName'))
    surname = get_xml_text(person.find('surname'))
    bloodname = get_xml_text(person.find('bloodname'))
    name = get_xml_text(person.find('name'))
    if(name == ''):
        name = first
        if(surname != ''):
            name = name + ' ' + surname
    if(bloodname != '' and surname == ''):
        name = name + ' ' + bloodname
    status = get_person_status(get_xml_text(person.find('status')))
    birthdate = get_xml_date(person.find('birthday'))
    deathdate = get_xml_date(person.find('deathday'))
    clan = get_xml_text(person.find('clan')) == 'true'
    phenotype = get_xml_text(person.find('phenotype'))
    if(clan):
        if(phenotype == '0' or phenotype == ''):
            phenotype = 'Freeborn Clan'
        else:
            phenotype = 'Trueborn Clan'
    else:
        phenotype = ''
    rank_number = get_xml_text(person.find('rank'))
    person_rank_system = get_xml_text(person.find('rankSystem'))
    if(person_rank_system == '' or person_rank_system == '-1'):
        person_rank_system = rank_system_default
    if(rank_number is not None):
        rank_name = find_rank(int(rank_number), person_rank_system, primary_role)
    unit_id = find_unit(uuid, units)
    unit_name = None
    force_name = None
    if(unit_id is not None):
        unit_name = get_unit_name(unit_id, units)
        force_name = find_force(unit_id, forces, None, None)
    dead = deathdate is not None
    if(dead):
        age = relativedelta.relativedelta(deathdate, birthdate).years
    else:
        age = relativedelta.relativedelta(date, birthdate).years
    if primary_role in roles and name != '':
        title = name
        if(rank_name is not None):
            title = rank_name + ' ' + name
        bio = get_xml_text(person.find('biography'))
        skill_desc = get_skill_report(person)
        kill_count = count_kills(uuid, kills)
        portrait = person.find('portrait')
        if(portrait is None):
            portrait_file = ''
            portrait_path = ''
        else:
            portrait_file = get_portrait_file(portrait.find('filename'))
            portrait_path = get_portrait_path(portrait.find('category'))+portrait_file
        callsign = get_xml_text(person.find('callsign'))
        f = open('campaign/_personnel/' + urlify(name) + '.md', 'w')
        f.write('---\n')
        f.write('layout: bio\n')
        f.write('title: ' + title + '\n')
        f.write('name: ' + name + '\n')
        f.write('status: ' + status + '\n')
        if(phenotype != ''):
            f.write('phenotype: ' + phenotype + '\n')
        f.write('role: ' + str(primary_role) + '\n')
        f.write('role-name: ' + role_name + '\n')
        if(skill_desc is not None):
            f.write('skill-level: ' + skill_desc[0] + '\n')
            f.write('skill-detail: ' + skill_desc[1] + '\n')
        if(callsign != ''):
            f.write('callsign: ' + callsign + '\n')
        if(kill_count>0):
            f.write('kills: ' + str(kill_count) + '\n')
        f.write('age: ' + str(age) + '\n')
        if(rank_number is not None):
            f.write('rank-number: ' + rank_number + '\n')
        if(rank_name is not None):
            f.write('rank-name: ' + rank_name + '\n')
        if(unit_name is not None):
            f.write('unit: ' + unit_name + '\n')
            f.write('unit-id: ' + unit_id + '\n')
            f.write('unit-slug: ' + urlify(unit_name) + '\n')
        f.write('slug: ' + urlify(name) + '\n')
        if(force_name is not None):
            f.write('force: ' + force_name + '\n')
            f.write('force-slug: ' + urlify(force_name) + '\n')
        if(portrait_path != '' and portrait_file != ''):
            new_portrait_file = replace_portrait_name(portrait_file, urlify(name))
            portrait_paths[new_portrait_file] = portrait_path
            f.write('portrait: ' + new_portrait_file + '\n')
        f.write('---\n\n')
        f.write(unescape(bio))
        f.close()
  
#loop through missions and scenarios. Use slugs to link scenarios
#to mission, but actually linking will be done by liquid
for mission in missions.findall('mission'):
    mission_name = mission.find('name').text
    mission_type = get_xml_text(mission.find('type'))
    mission_desc = get_xml_text(mission.find('desc'))
    mission_id = int(mission.attrib['id'])*10
    mission_start = get_xml_date(mission.find('startDate'))
    mission_end = get_xml_date(mission.find('endDate'))
    mission_employer = get_xml_text(mission.find('employer'))
    mission_location = get_xml_text(mission.find('systemId'))
    mission_status = get_xml_text(mission.find('status'))
    f = open('campaign/_missions/' + urlify(mission_name) + '.md', 'w')
    f.write('---\n')
    f.write('layout: mission\n')
    f.write('title: ' + mission_name + '\n')
    if(mission_start is not None):
        f.write('start-date: ' + mission_start.strftime('%Y-%m-%d') + '\n')
    if(mission_end is not None):
        f.write('end-date: ' + mission_end.strftime('%Y-%m-%d') + '\n')
    if(mission_type != ''):
        f.write('type: ' + mission_type + '\n')
    if(mission_employer != ''):
        f.write('employer: ' + mission_employer + '\n')
    if(mission_location != ''):
        f.write('location: ' + mission_location + '\n')
    if(mission_status != ''):
        f.write('status: ' + mission_status_dict[mission_status] + '\n')
    f.write('mission-order: ' + str(mission_id) + '\n')
    f.write('slug: ' + urlify(mission_name) + '\n')
    f.write('---\n\n')
    f.write(unescape(mission_desc))
    f.close()
    scenarios = mission.find('scenarios')
    if(scenarios is not None):
        for scenario in scenarios.findall('scenario'):
            scenario_name = scenario.find('name').text
            scenario_desc = get_xml_text(scenario.find('desc'))
            scenario_aar = get_xml_text(scenario.find('report'))
            scenario_date = get_xml_date(scenario.find('date'))
            scenario_status = get_xml_text(scenario.find('status'))
            f = open('campaign/_scenarios/' + urlify(mission_name + ' ' + scenario_name) + '.md', 'w')
            f.write('---\n')
            f.write('layout: mission\n')
            f.write('title: ' + scenario_name + '\n')
            if(scenario_date is not None):
                f.write('date: ' + scenario_date.strftime('%Y-%m-%d') + '\n')
            if(scenario_status != ''):
                f.write('status: ' + scenario_status_dict[scenario_status] + '\n')
            f.write('mission: ' + mission_name + '\n')
            f.write('mission-slug: ' + urlify(mission_name) + '\n')
            f.write('---\n\n')
            f.write(scenario_desc + '\n')
            if(scenario_aar != ''):
                f.write('\n##### After-Action Report\n\n')
                f.write(scenario_aar)
            f.close()

# ----------------------------------------------------------------------------
# Copy over data from MekHQ
# ----------------------------------------------------------------------------

#copy over images
for portrait_name in portrait_paths:
    portrait_path = portrait_paths[portrait_name]
    try:
        copyfile(mekhq_path + 'data/images/portraits/' + portrait_path, 'assets/images/portraits/' + portrait_name)
    except:
        try:
          copyfile(user_data_path + 'data/images/portraits/' + portrait_path, 'assets/images/portraits/' + portrait_name)
        except:
          pass
          
          
