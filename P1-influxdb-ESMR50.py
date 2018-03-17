#!/usr/bin/env python
# ESMR 5.0 P1 uitlezer

import sys
import serial
import time
import ConfigParser
import io
import os
import json
from influxdb import InfluxDBClient
from influxdb.client import InfluxDBClientError

with open("/home/odroid/config.ini") as f:
        sample_config = f.read()
config = ConfigParser.RawConfigParser(allow_no_value=True)
config.readfp(io.BytesIO(sample_config))

###########################
# Variables
listen_address = config.get('DEFAULT', 'listen_address') # What address to list$
listen_port = int(config.get('DEFAULT', 'listen_port')) # Port to listen on
client_id = config.get('MQTT', 'client_id') # MQTT Client ID
mqtt_server = config.get('MQTT', 'mqtt_server') # MQTT Address
mqtt_port = int(config.get('MQTT', 'mqtt_port')) # MQTT Port
influx_server = config.get('INFLUXDB', 'influxdb_server') # Ifluxdb server adre$
influx_port = int(config.get('INFLUXDB', 'influxdb_port')) # Influxdb port
influx_db = config.get('INFLUXDB', 'influxdb_databasename') # influxdb name
influx_user = config.get('INFLUXDB', 'influxdb_user') # influxdb gebruikersnaam
influx_passwd = config.get('INFLUXDB', 'influxdb_password') # influxdb login



################
#Error display #
################
def show_error():
    ft = sys.exc_info()[0]
    fv = sys.exc_info()[1]
    print("Fout type: %s" % ft )
    print("Fout waarde: %s" % fv )
    return

def daily():
   if Gas != 0:
	E = str(meter)
	dailyE = open("dayelek.txt","w")
	dailyE.write(E)
	dailyE.close()

	G = str(Gas)
	dailyG = open("daygas.txt","w")
	dailyG.write(G)
	dailyG.close()

def influx():
	DataJson = [{"measurement":"Meter",
		"tags":{"Serienummer":Serienr},
		"fields": {
			"Dal teller":T1afgenomen,
			"Dal retour":T1terug,
			"Piek teller":T2afgenomen,
			"Piek retour":T2terug,
			"Verbruik":meter,
			"Dag verbruik":PowerToday,
			"Afgenomen vermogen":Afgenomenvermogen,
			"Geleverd vermogen":Teruggeleverdvermogen,
			"Rendement":Totaalvermogen,
			"Tarief":Tarief,
			"Gas":Gas,
			"Gas vandaag":GasToday
			  }
		}
	]
	# print DataJson
	if influx_db:
	     client = InfluxDBClient(influx_server,influx_port, influx_user , influx_passwd , influx_db)
             client.create_database (influx_db)
             client.write_points (DataJson,protocol='json')


################################################################################################################################################
#Main program
################################################################################################################################################

#Set COM port config
ser = serial.Serial()
ser.baudrate = 115200
ser.bytesize=serial.EIGHTBITS
ser.parity=serial.PARITY_NONE
ser.stopbits=serial.STOPBITS_ONE
ser.xonxoff=0
ser.rtscts=0
ser.timeout=20
ser.port="/dev/ttyUSB0"

#Open COM port
try:
    ser.open()
except:
    sys.exit ("Fout bij het openen van %s. Programma afgebroken."  % ser.name)      


#Initialize
# stack is mijn list met de 26 regeltjes.
p1_teller=0
stack=[]

while p1_teller < 26:
    p1_line=''
#Read 1 line
    try:
        p1_raw = ser.readline()
    except:
        sys.exit ("Seriele poort %s kan niet gelezen worden. Programma afgebroken." % ser.name )      
    p1_str=str(p1_raw)
    #p1_str=str(p1_raw, "utf-8")
    p1_line=p1_str.strip()
    stack.append(p1_line)
# als je alles wil zien moet je de volgende line uncommenten
    # print (p1_line)
    p1_teller = p1_teller +1

#Initialize
# stack_teller is mijn tellertje voor de 26 weer door te lopen. Waarschijnlijk mag ik die p1_teller ook gebruiken
stack_teller=0
meter=0

while stack_teller < 26:
   if stack[stack_teller][0:9] == "1-0:1.8.1":
	T1afgenomen = float(stack[stack_teller][10:16])
	meter = meter + T1afgenomen
   elif stack[stack_teller][0:9] == "1-0:1.8.2":
	T2afgenomen = float(stack[stack_teller][10:16])
	meter = meter + T2afgenomen
# Daltarief, teruggeleverd vermogen 1-0:2.8.1
   elif stack[stack_teller][0:9] == "1-0:2.8.1":
	T1terug = float(stack[stack_teller][10:16])
	meter = meter - T1terug
# Piek tarief, teruggeleverd vermogen 1-0:2.8.2
   elif stack[stack_teller][0:9] == "1-0:2.8.2":
	T2terug = float(stack[stack_teller][10:16])
        meter = meter - T2terug
# Huidige stroomafname: 1-0:1.7.0
   elif stack[stack_teller][0:9] == "1-0:1.7.0":
	Afgenomenvermogen = float(stack[stack_teller][10:16])
# Huidig teruggeleverd vermogen: 1-0:1.7.0
   elif stack[stack_teller][0:9] == "1-0:2.7.0":
	Teruggeleverdvermogen = float(stack[stack_teller][10:16])
	Totaalvermogen = Afgenomenvermogen - Teruggeleverdvermogen
# Tarief (0-0:96.14.0(0001) 1 = daltarief)
   elif stack[stack_teller][0:9] == "0-0:96.14":
	Tarief = int(stack[stack_teller][12:16])
# Gasmeter: 0-1:24.3.0
   elif stack[stack_teller][0:10] == "0-1:24.2.1":
	Gas = float(stack[stack_teller][26:35])
# Serie nummer: 0-0:96.1.1
   elif stack[stack_teller][0:10] == "0-0:96.1.1":
        Serienr = (stack[stack_teller][11:45])
   else:
	pass
   stack_teller = stack_teller +1

# Dag verbruik bepalen
if os.path.exists("dayelek.txt"):
   ElekToday = open("dayelek.txt","r")
   PowerToday = float(meter) - float(ElekToday.readline())
   ElekToday.close()

   GasT = open("daygas.txt","r")
   GasToday = round(float(Gas) - float(GasT.readline()),3)
   GasT.close()
else:
   print ("no file")
   daily()



#Close port and show status
try:
    ser.close()
except:
    sys.exit ("Oops %s. Programma afgebroken." % ser.name )

if Gas != 0:
	# Database vullen
	#uur = int(time.strftime("%H",time.localtime(time.time())))
	#min = int(time.strftime("%M",time.localtime(time.time())))
	#sec = int(time.strftime("%S",time.localtime(time.time())))
	if int(time.strftime("%H",time.localtime(time.time()))) == 0 and int(time.strftime("%M",time.localtime(time.time()))) <= 2:
	    daily()

	influx()
