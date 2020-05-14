#!/usr/bin/env python3

# ----------------------------------------------------------------------------
# Basic parameters - change as needed 
# ----------------------------------------------------------------------------

#change this to choose which personnel get loaded based on personnel types
#in mekhq
#https://github.com/MegaMek/mekhq/blob/master/MekHQ/src/mekhq/campaign/personnel/Person.java#L75
roles = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,20,22,23,24,25]

#role names for ALL roles in MekHQ by index number. You can change names, but 
#do not remove values, even if you do not use the role above
role_names = ["Mechwarrior", "Aerospace Pilot", "Vehicle Driver", "Naval Vessel Driver", "VTOL Pilot", "Vehicle Gunner", "Battle Armor Pilot", "Conventional Infantry", "Protomech Pilot", "Conventional Fighter Pilot", "Space Vessel Pilot", "Space Vessel Crew", "Space Vessel Gunner", "Hyperspace Navigator", "Mech Tech", "Mechanic", "Aero Tech", "Battle Armor Tech", "Astech", "Doctor", "Medic", "Admin/Command", "Admin/Logistical", "Admin/Transport", "Admin/HR", "LAM Pilot", "Vehicle Crew"]

#relative or absolute path to your mekhq directory including trailing /
mekhq_path = "../Programs/mekhq-0.47.5/"

#the name of your campaign file within the campaigns directory of your 
#mekhq directory
campaign_file = 'The Free Company of Oriente30571215.cpnx'

#beginning of portait paths, only change if default image changes
portrait_paths = {
    "default.gif": "default.gif"
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


# ----------------------------------------------------------------------------
# custom functions
# ----------------------------------------------------------------------------

#clean out punctuation and replace spaces with - for url links and slugs
def urlify(s):
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
        return datetime.datetime.strptime(ele.text, '%Y-%m-%d %H:%M:%S')
    else:
        return None
    
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
            if(parent_name is ''):
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
            if(parent_name is ''):
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

def find_rank(rank_level, role, rank_list):
    if(role==2 or role==10):
        rank = rank_list[1][rank_level]
    elif((role>=3 and role<=6) or role==27):
        rank = rank_list[2][rank_level]
    elif(role>=11 and role <=14):
        rank = rank_list[3][rank_level]
    elif(role>=7 and role <=8):
        rank = rank_list[4][rank_level]
    elif(role>=15 and role <=19):
        rank = rank_list[5][rank_level]
    else:
        rank = rank_list[0][rank_level]
    rank = check_rank(rank, rank_level, rank_list)
    if(rank == '-'):
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

tree = ET.parse(mekhq_path + 'campaigns/' + campaign_file)
campaign = tree.getroot()

#stuff we need 
campaign_info = campaign.find('info')
date = datetime.datetime.strptime(campaign_info.find('calendar').text, '%Y-%m-%d %H:%M:%S')
rank_system = campaign_info.find('rankSystem')
personnel = campaign.find('personnel')
missions = campaign.find('missions')
kills = campaign.find('kills')
forces = campaign.find('forces')
units = campaign.find('units')

# ----------------------------------------------------------------------------
# Process the xml and output results to campaign directory
# ----------------------------------------------------------------------------

# process forces
process_forces(forces, None, None)

#process ranks. Currently, I think this will only work for custom rank
#systems.
#0 - mechwarriors
#1 - ASF pilots
#2 - Vehicle crew
#3 - Naval
#4 - Infantry
#5 - Tech
rank_mw    = []
rank_asf   = []
rank_vee   = []
rank_naval = []
rank_inf   = []
rank_tech  = []
for rank in rank_system.findall("rank"):
    rank_names = get_xml_text(rank.find('rankNames')).split(",")
    rank_mw.append(rank_names[0])
    rank_asf.append(rank_names[1])
    rank_vee.append(rank_names[2])
    rank_naval.append(rank_names[3])
    rank_inf.append(rank_names[4])
    rank_tech.append(rank_names[5])
rank_list = [rank_mw, rank_asf, rank_vee, rank_naval, rank_inf, rank_tech]

#loop through personnel and print out markdown file for each one
#currently limiting it to mechwarriors for test purposes
for person in personnel.findall('person'):
    uuid  = person.find('id').text
    primary_role = int(person.find('primaryRole').text)
    role_name = role_names[primary_role-1]
    first = get_xml_text(person.find('givenName'))
    surname = get_xml_text(person.find('surname'))
    birthdate = get_xml_date(person.find('birthday'))
    deathdate = get_xml_date(person.find('deathday'))
    rank_number = get_xml_text(person.find('rank'))
    if(rank_number is not None):
        rank_name = find_rank(int(rank_number), primary_role, rank_list)
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
    if primary_role in roles and first is not '':
        name = first
        if(surname is not ''):
            name = name + ' ' + surname
        title = name
        if(rank_name is not None):
            title = rank_name + ' ' + name
        bio = get_xml_text(person.find('biography'))
        portrait_file = get_xml_text(person.find('portraitFile'))
        portrait_path = get_xml_text(person.find('portraitCategory'))+portrait_file
        callsign = get_xml_text(person.find('callsign'))
        f = open('campaign/_personnel/' + urlify(name) + '.md', 'w')
        f.write('---\n')
        f.write('layout: bio\n')
        f.write('title: ' + title + '\n')
        f.write('name: ' + name + '\n')
        f.write('role: ' + str(primary_role) + '\n')
        f.write('role-name: ' + role_name + '\n')
        if(callsign is not ''):
            f.write('callsign: ' + callsign + '\n')
        f.write('kills: ' + str(count_kills(uuid, kills)) + '\n')
        f.write('age: ' + str(age) + '\n')
        if(rank_number is not None):
            f.write('rank-number: ' + rank_number + '\n')
        if(rank_name is not None):
            f.write('rank-name: ' + rank_name + '\n')
        if(unit_name is not None):
            f.write('unit: ' + unit_name + '\n')
        if(force_name is not None):
            f.write('force: ' + force_name + '\n')
            f.write('force-slug: ' + urlify(force_name) + '\n')
        f.write('dead: ' + str(dead) + '\n')
        if(portrait_path is not '' and portrait_file is not ''):
            portrait_paths[portrait_file] = portrait_path
            f.write('portrait: ' + portrait_file + '\n')
        f.write('---\n\n')
        f.write(unescape(bio))
        f.close()
  
#loop through missions and scenarios. Use slugs to link scenarios
#to mission, but actually linking will be done by liquid
for mission in missions.findall('mission'):
    mission_name = mission.find('name').text
    mission_type = get_xml_text(mission.find('type'))
    mission_desc = get_xml_text(mission.find('desc'))
    f = open('campaign/_missions/' + urlify(mission_name) + '.md', 'w')
    f.write('---\n')
    f.write('layout: mission\n')
    f.write('title: ' + mission_name + '\n')
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
            f = open('campaign/_scenarios/' + urlify(mission_name + ' ' + scenario_name) + '.md', 'w')
            f.write('---\n')
            f.write('layout: mission\n')
            f.write('title: ' + scenario_name + '\n')
            if(scenario_date is not None):
                f.write('date: ' + scenario_date.strftime('%Y-%m-%d') + '\n')
            f.write('mission: ' + mission_name + '\n')
            f.write('mission-slug: ' + urlify(mission_name) + '\n')
            f.write('---\n\n')
            f.write(scenario_desc + '\n')
            if(scenario_aar is not ''):
                f.write('#### After-Action Report\n\n')
                f.write(scenario_aar)
            f.close()

# ----------------------------------------------------------------------------
# Copy over data from MekHQ
# ----------------------------------------------------------------------------

#copy over images
for portrait_name in portrait_paths:
    portrait_path = portrait_paths[portrait_name]
    copyfile(mekhq_path + 'data/images/portraits/' + portrait_path, 'assets/images/portraits/' + portrait_name)

    
#copyfile(mekhq_path + "data/images/portraits/default.gif", "assets/images/portraits/default.gif")
