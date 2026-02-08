#1.  ip 🔵🔴 seperate fun 
#2. port & timeout & intervals 🔴 constant in seperate file 
#3. parameters <as it is > 🔴 get from user + 🔴 seperate fun to define parameters + #🔴 call it 
#4. connet
#5. FV 🔵 will be part of general send+resieve     🟢 1
#6. DS 🔵 will be part of general send+resieve     🟢 1
#7. initial setup                                  🟢 1
#8. AQ 🔵 will be part of general send+resieve     🟢 1
#9. BD 🔵 will be part of general send+resieve     
#10. Save to csv 🔵 is this part will replacement with database ?
#11. ASK user  🔵 is this part will replacement with UI ?
#12. input_timeout  #🔴 seperate fun



#🔵
#🟢
#🔴

##--------- 1 commands
#🔴 ip fun
#🔴 fun of excute commands  (ex. )send line + receive line + print verify / response + 🔴 if (one of important) --> check or raise 
#🔴🔵 fun if (one of parameters) (pa.)--> loop <the previous one > for line + call the previous fun line + sleep line 🔵 اقرا المانيوال تبعت كذا واحدة 
##---------

##-------- 2 constants
#🔴🔵 port line + timeout + reader + writer
#🔴 ask for parameters fun  ( ask from user lines + call fun of define )
# fun of define parameters as it is 

##-------- 3
#🔴 csv fun


##--------4
#🔴 take a decision fun (call input with timeout fun line  + if c --> call ask for parameters fun line  , elif user input --> call ex. line )


##------- 5 input with fun 

##-------- 0 
#🔴  call constents fun line + call ip fun  line  +  call ask for patameters fun line + 🔵try (call conect fun line + ......
#🔴  call fun of ex. for FV line + DS line  + pa. line + 🔵🔵while (call ex. for AQ  line + for  BD line + call csv fun line +....)
#🔴  call fun of take a decision line + sleep intervals line in the end of while )🔵🔵 + except and finally of that try

#🔴🔵csv + input with t0 + connect + recive //samples // above samples

#🔴 1. BD --> complete the recieve function