#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import re
import datetime
from dateutil import relativedelta
from html import unescape

#clean out punctuation and replace spaces with - for url links
def urlify(s):
    # Remove all non-word characters (everything except numbers and letters)
    s = re.sub(r"[^\w\s]", '', s)
    # Replace all runs of whitespace with a single dash
    s = re.sub(r"\s+", '-', s)
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
  
#loop through all the forces identified in element list and output them to
#markdown files. At the end it calls itself to iteratively process the tree
def process_forces(forces_ele, parent_slug):
    for force in forces_ele.findall('force'):
        force_name = force.find('name').text
        force_desc = get_xml_text(force.find('desc'))
        f = open('campaign/_forces/' + urlify(force_name) + '.md', 'w')
        f.write('---\n')
        f.write('layout: forces\n')
        f.write('title: ' + force_name + '\n')
        f.write('slug: ' + urlify(force_name) + '\n')
        if(parent_slug is not None):
            f.write('parent-slug: ' + parent_slug + '\n')
        f.write('---\n\n')
        f.write(unescape(force_desc))
        f.close()
        subforces = force.find('subforces')
        if(subforces is not None):
            process_forces(subforces, urlify(force_name))

tree = ET.parse('Flaming Devil Monkeys30740902.cpnx')
campaign = tree.getroot()
campaign_info = campaign.find('info')

#when are we?
date = datetime.datetime.strptime(campaign_info.find('calendar').text, '%Y-%m-%d %H:%M:%S')
  
#some stuff we need
personnel = campaign.find('personnel')
missions = campaign.find('missions')
kills = campaign.find('kills')
forces = campaign.find('forces')

# process forces
process_forces(forces, None)

#loop through personnel and print out markdown file for each one
#currently limiting it to mechwarriors for test purposes
for person in personnel.findall('person'):
    uuid  = person.find('id').text
    primary_role = int(person.find('primaryRole').text)
    first = get_xml_text(person.find('givenName'))
    surname = get_xml_text(person.find('surname'))
    birthdate = get_xml_date(person.find('birthday'))
    deathdate = get_xml_date(person.find('deathday'))
    dead = deathdate is not None
    if(dead):
        age = relativedelta.relativedelta(deathdate, birthdate).years
    else:
        age = relativedelta.relativedelta(date, birthdate).years
    if primary_role == 1 and first is not '':
        name = first
        if(surname is not ''):
            name = name + ' ' + surname
        bio = get_xml_text(person.find('biography'))
        portrait_path = get_xml_text(person.find('portraitCategory'))+get_xml_text(person.find('portraitFile'))
        callsign = get_xml_text(person.find('callsign'))
        f = open('campaign/_personnel/' + urlify(name) + '.md', 'w')
        f.write('---\n')
        f.write('layout: bio\n')
        f.write('title: ' + name + '\n')
        if(callsign is not ''):
            f.write('callsign: ' + callsign + '\n')
        f.write('kills: ' + str(count_kills(uuid, kills)) + '\n')
        f.write('age: ' + str(age) + '\n')
        if(portrait_path is not ''):
            f.write('portrait: ' + portrait_path + '\n')
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
                f.write('date: ' + str(scenario_date) + '\n')
            f.write('mission: ' + mission_name + '\n')
            f.write('mission-slug: ' + urlify(mission_name) + '\n')
            f.write('---\n\n')
            f.write(scenario_desc + '\n')
            if(scenario_aar is not ''):
                f.write('#### After-Action Report\n\n')
                f.write(scenario_aar)
            f.close()
