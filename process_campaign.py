#!/usr/bin/env python3

import xml.etree.ElementTree as ET
from html import unescape
import re

def urlify(s):
    # Remove all non-word characters (everything except numbers and letters)
    s = re.sub(r"[^\w\s]", '', s)
    # Replace all runs of whitespace with a single dash
    s = re.sub(r"\s+", '-', s)
    return s.lower()
    
def count_kills(uuid, kills):
  nkills = 0
  for kill in kills.findall('kill'):
    kill_id = kill.find('pilotId')
    if(kill_id is not None and kill_id.text is not None):
      if(uuid == kill_id.text):
       nkills = nkills + 1
  return nkills


tree = ET.parse('Flaming Devil Monkeys30740902.cpnx')
campaign = tree.getroot()

personnel = campaign.find('personnel')
toe = campaign.find('forces').find('force')
missions = campaign.find('missions')
kills = campaign.find('kills')

for person in personnel.findall('person'):
  uuid = person.find('id').text
  primary_role = int(person.find('primaryRole').text)
  first = person.find('givenName')
  surname = person.find('surname')
  if primary_role == 1 and first is not None and first.text is not None:
    name = first.text
    if surname is not None and surname.text is not None:
      name = name + ' ' + surname.text
    bio = person.find('biography')
    portrait_path = person.find('portraitCategory')
    portrait_file = person.find('portraitFile')
    callsign = person.find('callsign')
    f = open('campaign/personnel/' + urlify(name) + '.md', 'w')
    f.write('---\n')
    f.write('layout: bio\n')
    f.write('title: ' + name + '\n')
    if(callsign is not None and callsign.text is not None):
      f.write('callsign: ' + callsign.text + '\n')
    f.write('kills: ' + str(count_kills(uuid, kills)) + '\n')
    if(portrait_path is not None and portrait_path.text is not None and portrait_file is not None and portrait_file.text is not None):
      f.write('portrait: ' + portrait_path.text + portrait_file.text + '\n')
    f.write('---\n\n')
    if bio is not None:
      f.write(unescape(bio.text))
    f.close()
  

#for mission in missions.findall('mission'):
#  mission_name = mission.find('name').text
#  print mission_name
#  scenarios = mission.find('scenarios')
#  for scenario in scenarios.findall('scenario'):
#    print '\t'+scenario.find('name').text

